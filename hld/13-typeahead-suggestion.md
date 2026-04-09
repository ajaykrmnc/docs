# HLD 13: Design a Typeahead / Autocomplete System

> **Cross-reference:** For the low-level class design, see [LLD: Search Autocomplete](/lld/14-search-autocomplete)

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Back-of-Envelope Estimation](#4-back-of-envelope-estimation)
5. [API Design](#5-api-design)
6. [Data Model](#6-data-model)
7. [High-Level Architecture](#7-high-level-architecture)
8. [Deep Dive](#8-deep-dive)
9. [Partitioning](#9-partitioning)
10. [Caching](#10-caching)
11. [Replication](#11-replication)
12. [Fault Tolerance](#12-fault-tolerance)
13. [Scalability](#13-scalability)
14. [Monitoring and Observability](#14-monitoring-and-observability)
15. [Trade-offs and Alternatives](#15-trade-offs-and-alternatives)
16. [Interview Questions](#16-interview-questions)

---

## 1. Problem Statement

Design a typeahead (autocomplete) system that provides real-time search suggestions as
a user types into a search box. The system must return top relevant suggestions with
**sub-100ms end-to-end latency** from keystroke to rendered dropdown.

**Why is this hard?**

- **Latency:** Users expect instant results; even 200ms feels sluggish.
- **Volume:** Every keystroke generates a request. 10B daily searches x 4 chars = 40B requests/day.
- **Freshness:** Trending topics must surface within minutes, not hours.
- **Personalization at scale:** Tailored suggestions for billions of users.
- **Multi-language:** CJK, RTL, and Indic scripts need special tokenization and segmentation.

**Real-World Examples:** Google Search autocomplete, YouTube suggestions, Amazon product
search, LinkedIn search, IDE code completion.

---

## 2. Functional Requirements

| ID   | Requirement                    | Description                                               |
|------|--------------------------------|-----------------------------------------------------------|
| FR-1 | Prefix-based suggestions       | Return top 5-10 suggestions matching the typed prefix     |
| FR-2 | Real-time response             | Update with every keystroke (debounced 50-100ms)          |
| FR-3 | Ranked results                 | Ordered by frequency, recency, popularity                 |
| FR-4 | Typo tolerance                 | Handle misspellings ("pythn" -> "python")                 |
| FR-5 | Personalized suggestions       | Blend user search history into rankings                   |
| FR-6 | Trending queries               | Surface trending queries within minutes                   |
| FR-7 | Multi-language support          | Latin, CJK, Cyrillic, Arabic, Indic scripts               |
| FR-8 | Offensive content filtering    | Filter profanity, hate speech, NSFW                       |
| FR-9 | Multi-word prefix matching     | "how to le" -> "how to learn python"                      |
| FR-10| Category-aware suggestions     | Scope by category (images, news, shopping)                |

**Out of Scope:** Full search results rendering, spell correction for submitted queries,
voice-based autocomplete, image/visual search.

---

## 3. Non-Functional Requirements

| Requirement      | Target                             | Rationale                                      |
|------------------|------------------------------------|-------------------------------------------------|
| Latency          | p50 < 50ms, p99 < 100ms           | Each keystroke triggers a call                  |
| Availability     | 99.99% (52 min downtime/year)      | Critical path of every search                   |
| Throughput       | 500K+ QPS sustained                | 40B requests/day                                |
| Consistency      | Eventual (seconds to minutes)      | Stale suggestions acceptable                    |
| Scalability      | Horizontal to 1M+ QPS             | Handle spikes (Super Bowl, elections)            |
| Data freshness   | Trending < 5 min, Batch < 1 hour  | Trending topics must surface quickly             |

---

## 4. Back-of-Envelope Estimation

```
Query Volume:
  Daily searches:              10 billion
  Avg chars typed/search:      4 (users select early)
  Typeahead requests/day:      40 billion
  QPS (sustained):             ~460,000
  Peak QPS (3x):               ~1.4 million

Storage:
  Unique queries (freq > 1):   ~5 billion
  Avg query length:            15 chars (~20 bytes UTF-8)
  Raw query storage:           100 GB
  Compressed trie + metadata:  300 - 700 GB
  Per shard (100 shards):      3 - 7 GB

Bandwidth:
  Avg response:  ~500 bytes (10 suggestions x 50 chars)
  Outbound:      460K QPS x 500B = ~1.8 Gbps
  After CDN:     ~370 Mbps from origin

Infrastructure:
  Trie servers:   100 shards x 3 replicas = 300 servers (16 GB RAM)
  Spark cluster:  50 nodes (offline aggregation)
  Kafka:          20 brokers (query log ingestion)
  Redis:          50 nodes (hot prefix cache)
```

---

## 5. API Design

### 5.1 Get Suggestions

```
GET /api/v1/suggestions?prefix={prefix}&user_id={user_id}&limit={limit}&lang={lang}&category={category}
```

| Parameter    | Type   | Required | Default | Description                          |
|--------------|--------|----------|---------|--------------------------------------|
| `prefix`     | string | Yes      | -       | Typed prefix (URL-encoded, UTF-8)    |
| `user_id`    | string | No       | -       | For personalized suggestions         |
| `limit`      | int    | No       | 10      | Number of suggestions (max 20)       |
| `lang`       | string | No       | "en"    | Language code (ISO 639-1)            |
| `category`   | string | No       | "all"   | Scope: all, news, images, shopping   |
| `lat`, `lon` | float  | No       | -       | For geo-aware suggestions            |

**Response (200 OK):**

```json
{
  "prefix": "how to le",
  "suggestions": [
    {
      "text": "how to learn python",
      "score": 0.95,
      "highlight": { "prefix": "how to le", "completion": "arn python" },
      "metadata": { "trending": false, "personalized": false }
    }
  ],
  "debug": { "latency_ms": 12, "shard": "prefix-h", "cache_hit": true }
}
```

**Headers:** `Cache-Control: public, max-age=300` (5 min for common prefixes).

### 5.2 Report Selection (Analytics)

```
POST /api/v1/suggestions/select
{ "prefix": "how to le", "selected": "how to learn python", "position": 0, "user_id": "u_12345" }
```

### 5.3 Client-Side Optimizations

- **Debounce:** Wait 50-100ms after last keystroke before sending
- **Cancel in-flight:** Cancel previous request on new keystroke
- **Local cache:** Cache recent prefix responses in localStorage
- **Min prefix length:** Use CDN-cached responses for 1-char prefixes

---

## 6. Data Model

### 6.1 Trie Node (In-Memory)

```
┌──────────────────────────────────────────────────────┐
│                   TrieNode                           │
├──────────────────────────────────────────────────────┤
│  char              : character                       │
│  children          : map<char, TrieNode*>            │
│  is_end_of_word    : bool                            │
│  frequency         : uint64                          │
│  top_k_suggestions : list<(query, score)> [size=10]  │
│  last_updated      : timestamp                       │
└──────────────────────────────────────────────────────┘
```

### 6.2 Query Log (Kafka Topic: `query-logs`)

```
┌──────────────────────────────────────────────────────┐
│                  QueryLogEvent                       │
├──────────────────────────────────────────────────────┤
│  query_id    : UUID          │  language  : string   │
│  query_text  : string        │  country   : string   │
│  user_id     : string (null) │  device    : enum     │
│  timestamp   : int64 (ms)    │  session_id: string   │
└──────────────────────────────────────────────────────┘
```

### 6.3 Aggregated Query Frequency (HDFS / S3)

```
┌──────────────────────────────────────────────────────┐
│              AggregatedQueryFrequency                │
├──────────────────────────────────────────────────────┤
│  query_text   : string (partition key)               │
│  time_window  : string (e.g., "2026-04-09")         │
│  raw_count    : uint64    │  decayed_score : float64 │
│  language     : string    │  is_filtered   : bool    │
└──────────────────────────────────────────────────────┘
```

### 6.4 User Search History (Cassandra)

```
Table: user_search_history
  Partition key:  user_id (text)
  Clustering key: timestamp DESC
  Columns:        query_text, category, clicked
  TTL:            90 days
```

### 6.5 Trending Queries (Redis Sorted Set)

```
Key:    trending:{lang}:{country}     Type: Sorted Set
Member: query_text                    Score: trending velocity
TTL:    1 hour (refreshed by streaming pipeline)
```

---

## 7. High-Level Architecture

### 7.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ONLINE SERVING PATH                          │
│                                                                        │
│  ┌──────────┐     ┌───────┐     ┌──────────────────┐                   │
│  │  Client   │────>│  CDN  │────>│  Load Balancer   │                   │
│  │(Browser/  │<────│(1-2   │     │  (L7 / Nginx)    │                   │
│  │ Mobile)   │     │ char) │     └────────┬─────────┘                   │
│  └──────────┘     └───────┘              │                              │
│                                          v                              │
│                              ┌───────────────────────┐                  │
│                              │  Suggestion Service    │                  │
│                              │  (Stateless, N nodes)  │                  │
│                              └─────┬───────┬─────────┘                  │
│                                    │       │                            │
│                     ┌──────────────┘       └──────────────┐             │
│                     v                                     v             │
│          ┌───────────────────┐                 ┌──────────────────┐     │
│          │   Redis Cache     │                 │  Personalization │     │
│          │  (Hot Prefixes)   │                 │  Service         │     │
│          └────────┬──────────┘                 └────────┬─────────┘     │
│                   │ miss                                │              │
│                   v                                     │              │
│          ┌────────────────────────────────────────┐     │              │
│          │        Distributed Trie Cluster        │     │              │
│          │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │     │              │
│          │  │ Shard 1 │ │ Shard 2 │ │ Shard N │  │     │              │
│          │  │ (a-c)   │ │ (d-f)   │ │ (x-z)   │  │     │              │
│          │  └─────────┘ └─────────┘ └─────────┘  │     │              │
│          │  Each shard: 3 replicas                │     │              │
│          └────────────────────────────────────────┘     │              │
│                                                         │              │
│          Cassandra (User Search History) <───────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         OFFLINE DATA PIPELINE                          │
│                                                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Search  │───>│  Kafka   │───>│  Spark       │───>│  Trie        │  │
│  │  Logs    │    │ (Query   │    │  Batch       │    │  Builder     │  │
│  │          │    │  Logs)   │    │  (Hourly)    │    │              │  │
│  └──────────┘    └────┬─────┘    └──────┬───────┘    └──────┬───────┘  │
│                       │                 │                    │          │
│                       │                 v                    v          │
│                       │          ┌──────────────┐    ┌──────────────┐  │
│                       v          │  HDFS / S3   │    │  Trie        │  │
│                ┌──────────────┐  │ (Aggregated) │    │  Snapshot    │  │
│                │  Flink       │  └──────────────┘    │  (S3 + Deploy│  │
│                │ (Trending    │                      │   Blue-Green)│  │
│                │  Detector)   │                      └──────────────┘  │
│                └──────┬───────┘                                        │
│                       v                                                │
│                  Redis (Trending Queries)                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Request Flow

```
User types "pyth" ->
  1. Client debounces (50ms), cancels previous in-flight request
  2. Check browser local cache -> miss
  3. GET /suggestions?prefix=pyth -> CDN miss -> LB -> Suggestion Service
  4. Check Redis cache for "pyth" -> miss
  5. Route to Trie Shard for prefix "p", lookup node p->y->t->h
  6. Return pre-computed top-10 from that node
  7. Fetch user history from Cassandra (parallel)
  8. Blend global + personal + trending scores
  9. Filter offensive content, apply diversity rules
  10. Cache in Redis (TTL 5 min), return to client

Latency budget:
  Network RTT:           20-30ms
  Service + Trie lookup:  5-15ms
  Personalization:        5-10ms
  Total:                 30-55ms (well under 100ms target)
```

---

## 8. Deep Dive

### 8.1 Trie Data Structure

**Standard Trie** -- one character per node:

```
                         ┌─────┐
                         │ root│
                         └──┬──┘
                ┌───────────┼───────────┐
                v           v           v
            ┌───┐       ┌───┐       ┌───┐
            │ b │       │ c │       │ p │
            └─┬─┘       └─┬─┘       └─┬─┘
              v           v           v
          ┌───┐       ┌───┐       ┌───┐
          │ e │       │ a │       │ y │
          └─┬─┘       └─┬─┘       └─┬─┘
            v           v           v
        ┌───┐       ┌───┐       ┌───┐
        │ e │       │ r │       │ t │
        └─┬─┘       └───┘       └─┬─┘
          v        (car:50)       v
      ┌───┐                   ┌───┐
      │ r │                   │ h -> o -> n │
      └───┘                   └─────────────┘
     (beer:30)               (python:100)
```

**Problem:** Finding top-K for prefix "py" requires traversing the entire subtree -- too slow.

**Compressed Trie (Radix Tree)** -- merges single-child chains:

```
                         ┌──────┐
                         │ root │
                         └──┬───┘
                ┌───────────┼───────────┐
                v           v           v
          ┌─────────┐ ┌─────────┐ ┌──────────┐
          │ "beer"  │ │ "car"   │ │ "pyth"   │
          │ freq:30 │ │ freq:50 │ └─────┬────┘
          └─────────┘ └─────────┘       │
                                  ┌─────┴─────┐
                                  v           v
                            ┌─────────┐ ┌─────────┐
                            │ "on"    │ │ "onic"  │
                            │ freq:100│ │ freq:20 │
                            └─────────┘ └─────────┘
```

Memory: Standard trie ~3 TB vs Compressed ~900 GB for 5B queries.

**Key optimization: Pre-computed Top-K at each node.** Store top-10 suggestions at
every node, converting subtree traversal into a single O(L) node lookup.

```
               ┌───────────────────────┐
               │  "py"                 │
               │  top_k:               │
               │   ("python", 100K)    │
               │   ("python tutorial", │
               │     60K)              │
               │   ("pygame", 30K)     │
               │   ("pytorch", 28K)    │
               └───────────────────────┘
```

Store query IDs (4 bytes) instead of strings at each node:
10 IDs x 4 bytes x 15B nodes = 600 GB + 100 GB string table = ~700 GB total.
With 100 shards: ~7 GB per shard.

**Build-time:** Top-K is computed bottom-up. At each node, merge children's top-K lists
and keep only top K using a min-heap: O(C * K * log K) per node.

**Trie Serialization Format (binary, for fast deployment):**

```
┌──────────────────────────────────────────────────────┐
│              Trie Binary Format                      │
├──────────────────────────────────────────────────────┤
│  Header:                                             │
│    magic ("TRIE"), version, node_count,              │
│    query_count, build_timestamp, checksum (MD5)      │
├──────────────────────────────────────────────────────┤
│  Query String Table:                                 │
│    [query_id -> (offset, length)] index              │
│    [concatenated query strings]                      │
├──────────────────────────────────────────────────────┤
│  Node Array (BFS order, cache-friendly):             │
│    label_offset(4B), label_len(1B),                  │
│    child_offset(4B), child_count(1B),                │
│    is_terminal(1bit), frequency(4B),                 │
│    top_k_offset(4B), top_k_count(1B)                 │
├──────────────────────────────────────────────────────┤
│  Top-K Lists:                                        │
│    [query_id(4B), score(4B)] x K per node            │
└──────────────────────────────────────────────────────┘
```

BFS-ordered node layout ensures sequential memory access patterns for better
CPU cache performance compared to pointer-chasing in a heap-allocated trie.

### 8.2 Data Collection Pipeline

```
┌───────────────────────────────────────────────────────────┐
│  Search Logs ──> Kafka (128 partitions, 7-day retention)  │
│       │                                                    │
│       ├──> Flink Streaming ──> Redis (Trending Queries)    │
│       │                                                    │
│       └──> Spark Batch (Hourly) ──> HDFS (Aggregated)     │
│                                       │                    │
│                                       v                    │
│                               Trie Builder ──> S3 Snapshot │
│                                       │                    │
│                               Blue-Green Deploy to Cluster │
└───────────────────────────────────────────────────────────┘
```

**Sampling:** At 460K QPS, we sample: 1/1000 for 1-char prefixes, 1/100 for 2-3 char,
1/10 for 4+, and 100% for completed queries and click-throughs. Effective: ~50K events/sec.

**Aggregation (Spark):**
1. Map: `(query, lang, country) -> 1`
2. Reduce: Sum counts per key
3. Decay: `new_score = old_score * exp(-lambda * dt) + new_count` (half-life = 1 week)
4. Filter: Remove score < threshold, offensive content, garbage queries
5. Output: Parquet files to S3, partitioned by date/lang/country

**Update modes:**
- Full rebuild: 30-60 min, daily or on schema changes
- Incremental: 1-5 min, hourly frequency updates
- Real-time patch: Seconds, trending queries only (via Redis, not trie mutation)

### 8.3 Ranking and Scoring

```
final_score = w1 * global_frequency     (0.30)
            + w2 * recency              (0.25)
            + w3 * trending             (0.15)
            + w4 * personalization      (0.15)
            + w5 * contextual           (0.10)
            + w6 * quality              (0.05)
```

**Global frequency:** `log10(1 + decayed_count) / log10(1 + max_count)` normalized to [0,1].

**Personalization blend example:**

```
  User types "ja", has history: [javascript tutorial x5, java spring boot x3]

  Global top-5:              Blended result:
   1. java (100K)             1. javascript (boosted by history)
   2. japan travel (80K)      2. java (global + history)
   3. javascript (75K)        3. java spring boot (personal)
   4. jake paul (60K)         4. japan travel (global)
   5. james bond (55K)        5. jake paul (global)
```

**Trending detection:** `velocity = (count_last_hour - avg_7d_hourly) / (avg_7d_hourly + epsilon)`.
If velocity > 3x, mark as trending and boost.

**Diversity:** Use Maximal Marginal Relevance (MMR) -- max 3 suggestions with same first
2 words, at least 1 trending if available, at least 1 personalized if logged in.

**Offensive filtering pipeline:**

```
┌─────────────────────────────────────────────────────────┐
│  Query candidate                                        │
│       │                                                 │
│       v                                                 │
│  ┌──────────────────┐   Maybe                           │
│  │ Bloom filter     │──────> Exact hash set check       │
│  │ (fast, O(1))     │        ┌─> Match: BLOCK           │
│  └────────┬─────────┘        └─> No match: PASS         │
│           │ Definitely not                              │
│           v                                             │
│       PASS (serve)                                      │
│                                                         │
│  Applied at:                                            │
│    1. Build time (remove from top-K lists entirely)     │
│    2. Serve time (runtime check for edge cases)         │
│    3. ML classifier (<5ms) for creative misspellings    │
└─────────────────────────────────────────────────────────┘
```

### 8.4 Trie Sharding

**Prefix range partitioning** with load-balanced boundaries:

```
  Shard 0: "a"            (~10% traffic)
  Shard 1: "b" - "c"      (~10%)
  Shard 2: "d" - "f"      (~10%)
  ...
  Shard 7: "t"             (~10%)  -- "the", "to" are very common
  Shard 9: "x"-"z", 0-9   (~10%)
  Shard 10: CJK characters (separate scheme)
```

Boundaries are NOT uniform -- weighted by query volume so each shard handles roughly
equal QPS. Re-balanced weekly. Hot shards (e.g., "s") can be further split by 2nd character.

**Replication:** 3 replicas per shard, spread across availability zones. All replicas
serve reads (load balanced). Updates pushed during trie deployment.

**Routing:**

```
┌──────────────────────────────────────────────────────────┐
│  Suggestion Service receives prefix "python"             │
│                                                          │
│  1. Normalize: lowercase, trim whitespace                │
│  2. Extract routing key: first_char = 'p'                │
│  3. Lookup shard map (cached from ZooKeeper): 'p' -> S5  │
│  4. Select replica: round-robin among healthy Shard 5    │
│     replicas, prefer same-region                         │
│  5. Send gRPC request to selected replica                │
│  6. On failure: retry on different replica               │
│     (max 1 retry, timeout = 50ms)                        │
└──────────────────────────────────────────────────────────┘
```

---

## 9. Partitioning

| Data Store         | Partition Strategy                                                  |
|--------------------|---------------------------------------------------------------------|
| **Trie**           | Prefix range (first 1-2 chars), 50-100 shards, load-balanced       |
| **Kafka logs**     | 128 partitions, keyed by `hash(query_text)`, 7-day retention       |
| **HDFS/S3**        | Date + language + country partitions, Parquet format, 90-day retain |
| **Cassandra**      | `user_id` (Murmur3 hash), clustering by `timestamp DESC`, RF=3     |

For HDFS/S3: `s3://typeahead/aggregated/dt=2026-04-09/lang=en/country=US/part-*.parquet`

Cassandra: Write CL=ONE, Read CL=ONE (low latency). Max 1000 queries/user. TTL 90 days.
TimeWindowCompactionStrategy.

---

## 10. Caching

### Multi-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Browser Cache                                     │
│    Cache-Control max-age=300, localStorage for recent prefix│
│    Hit rate: ~35%    Cost: Zero                             │
│                         │ miss                              │
│  Layer 2: CDN (CloudFront/Akamai)                           │
│    Cache 1-2 char prefix responses (only ~676 combos)      │
│    TTL: 1 hour, key: prefix+lang+country                   │
│    Hit rate: ~55% of remaining                             │
│                         │ miss                              │
│  Layer 3: Redis (Application)                               │
│    Hot 3+ char prefixes, key: "sugg:{lang}:{prefix}"       │
│    TTL: 5 min, LFU eviction, 50 nodes / 128 GB             │
│    Hit rate: ~75% of remaining                             │
│                         │ miss                              │
│  Layer 4: Trie In-Memory (Source of Truth)                  │
│    Pre-computed top-K, O(L) lookup, always available        │
└─────────────────────────────────────────────────────────────┘

Net effect: 460K QPS total -> only ~34K QPS reach the trie (93% reduction)
```

**Personalized caching:** Cache global top-20 at CDN/Redis. Personalization computed as
a server-side re-ranking overlay -- keeps CDN effective while still personalizing.

**Invalidation:** TTL-based natural expiry. Trending detection triggers surgical Redis
purge for affected prefixes. Offensive content addition triggers immediate purge. Top-1000
prefixes proactively refreshed before TTL expires (background refresh at 80% TTL).

**Thundering herd mitigation:** Staggered TTLs (5 min +/- 30s jitter), lock-based
deduplication (Redis SETNX), stale-while-revalidate for async refresh.

---

## 11. Replication

### Trie Replication Model

```
┌──────────────┐     Snapshot to S3
│ Trie Builder │──────────────────────┐
│ (Writer)     │                      v
└──────────────┘               ┌──────────────┐
                               │   S3 Bucket  │
                               └──────┬───────┘
                        ┌─────────────┼──────────┐
                        v             v          v
                  ┌──────────┐ ┌──────────┐ ┌──────┐
                  │ Replica A│ │ Replica B│ │ ...  │
                  │ (US-E)   │ │ (US-W)   │ │      │
                  └──────────┘ └──────────┘ └──────┘
```

Each replica polls S3 (or receives SNS push) for new snapshots, loads in background
alongside current trie, performs atomic pointer swap, frees old memory.

**Consistency:** Eventually consistent, minutes lag acceptable. All replicas converge
within 1 rebuild cycle (~1 hour). Trending queries served from Redis (not trie) for
near-real-time freshness. Version IDs tracked; alert if skew > 2.

**Blue-Green Deployment:** Canary replica gets new version first, serves 5% traffic for
10 min. If healthy: rolling update 10% -> 25% -> 50% -> 100% over 30 min. Previous
snapshot retained in S3 for instant rollback (pointer swap, < 1 min).

---

## 12. Fault Tolerance

| Failure Mode               | Mitigation                                              |
|----------------------------|---------------------------------------------------------|
| Single trie replica crash  | Route to other replicas (3x replication), <5s detection |
| Entire shard offline       | Serve stale cache; fallback to popular queries list     |
| Redis cache down           | Bypass cache, serve from trie (auto-scale for load)     |
| CDN outage                 | Clients fall through to origin; auto-scaling kicks in   |
| Trie build failure         | Continue serving previous version; alert and retry      |
| Kafka broker failure       | RF=3 handles broker loss; some log loss acceptable      |
| Cassandra node down        | RF=3, CL=ONE transparent; degrade to global-only        |
| Network partition          | Each region operates independently with local tries     |

**Graceful Degradation Hierarchy:**

```
Level 0: Full service (global + personalized + trending + filtered)
Level 1: No personalization (Cassandra down)
Level 2: No trending (Redis down)
Level 3: Cached only (trie cluster unreachable)
Level 4: Static fallback (top-100 popular queries per language, pre-computed)
Level 5: Empty suggestions (catastrophic failure, client hides dropdown)
```

**Circuit breakers** on all backends: open at >50% failure rate in 10s window, half-open
after 30s trial at 10% traffic, close when success rate > 90%.

---

## 13. Scalability

```
┌─────────────────────────────────────────────────────────────┐
│  1. Trie Sharding:        Add shards as data grows          │
│     100 -> 1000+ shards, split hot shards by 2nd char      │
│                                                             │
│  2. Read Replicas:        Add replicas per shard            │
│     3 -> 10+ for hot shards                                │
│                                                             │
│  3. CDN Offloading:       Absorbs 80%+ traffic              │
│     Add PoPs in new regions as user base grows              │
│                                                             │
│  4. Suggestion Service:   Stateless, auto-scale             │
│     K8s HPA: 60% CPU target, 50 -> 500 pods in minutes     │
│                                                             │
│  5. Redis Cache:          Redis Cluster with hash slots     │
│     Add nodes for more memory/throughput                    │
└─────────────────────────────────────────────────────────────┘
```

**Traffic spikes (e.g., Super Bowl at 10x normal):** CDN absorbs most; Redis handles
warm prefixes; auto-scaling for compute; pre-warm caches for predicted events; rate limit
at 20 req/sec per user; degrade gracefully (disable personalization, increase TTLs,
reduce suggestions from 10 to 5).

**Multi-region:** Full trie copy in each region (US-East, US-West, EU, APAC). Central
pipeline in US-East builds snapshots replicated to all regions via S3. DNS routes users
to nearest region. Each region serves independently.

---

## 14. Monitoring and Observability

### Key Metrics

```
┌────────────────────────────────────────────────────────────┐
│  LATENCY          │  p50: 12ms  p95: 38ms  p99: 72ms      │
│  THROUGHPUT       │  462K QPS total, 21K to trie (5%)      │
│  CACHE HIT RATES  │  CDN: 82%  Redis: 76%  Client: 35%    │
│  TRIE HEALTH      │  Version: v2847, 14.2B nodes, 6.2 GB  │
│                   │  Last rebuild: 32 min ago (18 min dur) │
│  QUALITY          │  CTR: 42%  MRR: 0.68  Diversity: 0.72 │
│  PIPELINE         │  Kafka lag: 12s  Spark: SUCCESS        │
└────────────────────────────────────────────────────────────┘
```

### Alerting Rules

| Alert                   | Condition               | Severity |
|-------------------------|-------------------------|----------|
| High latency            | p99 > 200ms for 2 min   | P1       |
| Low CDN hit rate        | < 60% for 10 min        | P2       |
| Trie version skew       | > 2 versions for 30 min | P2       |
| Trie rebuild failure    | 2 consecutive failures  | P1       |
| Shard replicas < 2      | Any shard               | P1       |
| Error rate              | > 0.1% 5xx for 2 min    | P1       |
| CTR drop                | > 20% vs 7-day avg      | P2       |
| Offensive content spike | > 5x normal filtered    | P1       |

Distributed tracing (Jaeger) across LB -> Service -> Cache -> Trie -> Personalization.
Sample rate 0.1%. Structured JSON logs for every request with request_id, shard, cache_layer,
latency_ms, trie_version.

---

## 15. Trade-offs and Alternatives

### 15.1 Trie vs Inverted Index

| Aspect             | Trie                     | Inverted Index              |
|--------------------|--------------------------|-----------------------------|
| Prefix lookup      | O(L) -- excellent        | O(log N) with sorted lists  |
| Pre-computed top-K | Natural fit at each node | Requires separate index     |
| Fuzzy matching     | Needs edit-distance walk | Better (n-gram based)       |
| Multi-word         | Full query as key        | Per-word + intersection     |
| Best for           | Exact prefix, real-time  | Fuzzy, multi-field search   |

**Verdict:** Trie is standard for typeahead. Use inverted index as complement for fuzzy matching.

### 15.2 Prefix Match vs Fuzzy Match

Prefix match: O(L), high precision, simple. Fuzzy match: O(L * edit_dist), handles typos,
more false positives.

**Hybrid:** Always do prefix first. If < 5 results, trigger fuzzy match (n-gram index,
edit distance 1-2, BK-tree or SymSpell). Merge results, prefix preferred. Fuzzy only for
prefixes > 3 chars.

### 15.3 Real-Time vs Batch Updates

| Aspect      | Real-Time              | Batch                     |
|-------------|------------------------|---------------------------|
| Freshness   | Seconds                | Minutes to hours          |
| Complexity  | High (concurrent R/W)  | Low (rebuild and swap)    |
| Risk        | Memory fragmentation   | Stale data between builds |

**Hybrid:** Batch rebuild hourly (99% of data) + streaming for trending only (1%, via Redis).
Avoids real-time trie mutation complexity while keeping trending fresh.

### 15.4 Caching Strategy

| Strategy            | Pro                        | Con                             |
|---------------------|----------------------------|---------------------------------|
| Aggressive (long TTL)| 95%+ hit rate, low load   | Stale suggestions               |
| Conservative (short)| Fresh results              | Higher trie load                |
| Per-user caching    | Personalized + cached      | Huge cache, low per-user hits   |
| Two-tier (recommended)| CDN for global, compute personal overlay | Slightly more logic |

---

## 16. Interview Questions

**Q1: How do you handle multi-word prefix matching?**
The trie stores full query strings including spaces. "how to le" is a path h-o-w-' '-t-o-' '-l-e. The top-K at node "e" contains "how to learn python". Multi-word and single-word queries are handled identically from the trie's perspective. Compressed tries mitigate the cost of common chains like "how to".

**Q2: How do you handle real-time trending updates without full trie rebuild?**
Two-tier approach: main trie rebuilt hourly (Spark batch). Flink streaming detects queries with velocity > 3x their 7-day average and writes them to Redis sorted sets. At serving time, the Suggestion Service merges trie results with Redis trending results. This avoids the complexity of mutating a distributed in-memory trie.

**Q3: How do you support CJK languages?**
(1) Use word segmenters (Jieba for Chinese, MeCab for Japanese) before trie lookup. (2) Maintain character-level CJK trie for character-by-character input. (3) Support pinyin/romaji input ("beijing" -> "北京"). (4) Dedicate separate shards for CJK (Unicode U+4E00-U+9FFF, ~20K chars). (5) More aggressive debounce (200ms) due to IME buffering.

**Q4: How do you filter offensive suggestions?**
Multi-layer: (1) Build-time blocklist + regex removal from trie. (2) Serving-time Bloom filter pre-check (O(1), 0.1% FPR). (3) Exact hash set verification on Bloom "maybe" results. (4) Lightweight ML classifier (<5ms) for creative misspellings. (5) Human review queue for borderline cases. (6) Monitor for spikes indicating coordinated abuse.

**Q5: How do you handle cold start for new users?**
Default to global popularity. Use demographic signals (language, country, device, time-of-day). Track session context -- if user searched "python tutorial", bias toward programming. Boost trending weight (w3: 0.15 -> 0.25) for new users. After 5-10 searches, begin basic personalization with short half-life.

**Q6: How do you handle thundering herd on cache expiry?**
(1) Staggered TTLs (5 min +/- 30s jitter). (2) Background refresh for top-1000 prefixes at 80% TTL. (3) Lock-based dedup via Redis SETNX (only 1 request refills, others wait). (4) Stale-while-revalidate -- serve expired value while async refresh.

**Q7: What if a trie shard exceeds single-machine memory?**
Split by next character: shard "s" becomes sub-shards "sa-sf", "sg-sm", "sn-ss", "st-sz". Update shard map in ZooKeeper. Routing uses first 2 characters instead of 1. Transparent to clients. Can split on 3+ characters in extreme cases.

**Q8: How do you measure suggestion quality?**
CTR (target >35%), MRR (target >0.6, higher = clicked suggestion ranks higher), Keystroke Savings Rate (target >50%), abandonment rate, time to selection. Every ranking change A/B tested before full rollout.

**Q9: How do you handle prefix "a" matching billions of queries?**
CDN-cached with 1-hour TTL (only 36 possible 1-char prefixes). Pre-computed static top-10 lists baked at build time. O(1) lookup from pre-computed top-K at the "a" node. For logged-in users, personalization overlay computed server-side.

**Q10: How do you handle multiple languages?**
Separate tries per language (recommended at scale). Routing key: `lang + prefix[0]` determines shard. Each language has different character distributions and query patterns, making separate tries more efficient. Multilingual users get suggestions from their configured language's trie.

**Q11: How do you prevent the trie from growing indefinitely?**
(1) Frequency threshold: only include score > 5. (2) Recency cutoff: drop queries unsearched for 90 days. (3) Hard cap at 5B unique queries; evict lowest-scoring. (4) Length limit: 100 chars. (5) Normalize (lowercase, trim, collapse spaces). (6) Weekly full rebuild prunes and compacts.

**Q12: How do you bootstrap with no query history?**
Seed with Wikipedia titles, Common Crawl page titles, product catalogs, place names. Integrate Twitter/Google Trends. Manual curation for first weeks. Short half-life (1 day vs 1 week) for aggressive early learning. Gradually increase half-life as corpus grows.

**Q13: How do you implement "did you mean" alongside typeahead?**
Separate systems: typeahead (before submission) vs "did you mean" (after submission). For typeahead fuzzy matching: maintain bigram/trigram index alongside trie. When prefix yields < 5 exact results, query n-gram index for edit distance 1-2 matches using SymSpell. Mark fuzzy results distinctly in UI. Only for prefixes > 3 chars.

**Q14: How do you address privacy concerns?**
90-day TTL on user history. Opt-out deletes all data. On-device personalization option (client-side re-ranking). Anonymize query logs after session. Differential privacy for aggregate frequencies. GDPR/CCPA deletion within 72 hours. Never surface one user's private searches to another.

**Q15: How would e-commerce typeahead differ?**

```
┌──────────────────────────────────────────────────────────┐
│  E-Commerce Typeahead Differences                        │
├──────────────────────────────────────────────────────────┤
│  1. Catalog-aware:    Only suggest existing products     │
│  2. Category suggest: "sho" -> "shoes" (category)        │
│  3. Attribute-based:  "iphone 15 pro max 256gb" (SKU)    │
│  4. Inventory-aware:  Deprioritize out-of-stock items    │
│  5. Revenue-weighted: Score by conversion rate x AOV     │
│  6. Rich results:     Thumbnails, prices, ratings        │
│  7. Seasonal boost:   "halloween costume" in October     │
│  8. Aggressive fuzzy: "adiddas" -> "adidas" (brand       │
│     misspelling directly impacts revenue)                │
└──────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    KEY DESIGN DECISIONS                     │
├─────────────────────────────────────────────────────────────┤
│  1. Compressed trie + pre-computed top-K -> O(L) lookup     │
│  2. Multi-layer caching (client+CDN+Redis) -> 93% offload  │
│  3. Batch rebuild (hourly) + streaming trending (seconds)   │
│  4. Prefix-range sharding, load-balanced boundaries         │
│  5. Blue-green deployment with canary rollout               │
│  6. 5-level graceful degradation hierarchy                  │
│  7. Two-tier personalization (cache global, blend at serve)  │
│  8. Offensive filtering at build + serve time               │
└─────────────────────────────────────────────────────────────┘
```
