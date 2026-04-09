# Design a Web Search Engine (Google Search)

**Difficulty:** Hard | **Category:** Information Retrieval, Distributed Systems  
**Companies:** Google, Microsoft (Bing), Amazon (A9), Apple (Spotlight/Siri), Yandex, Baidu, DuckDuckGo

---

## 1. Problem Statement and Scope

Design a web-scale search engine that continuously crawls billions of web pages,
builds and maintains a searchable index, and returns highly relevant ranked results
for arbitrary user queries with sub-second latency.

### In Scope

- **Web Crawling:** Discover, fetch, and store web pages at scale
- **Indexing:** Build and maintain an inverted index over crawled content
- **Query Processing:** Parse, understand, and execute user queries
- **Ranking:** Return results ordered by relevance (BM25 + PageRank + ML)
- **Autocomplete / Query Suggestions:** Real-time prefix-based suggestions
- **Spell Correction:** "Did you mean..." functionality
- **Snippet Generation:** Extract and highlight relevant text fragments
- **Pagination:** Serve results across multiple pages
- **Knowledge Panels:** Structured information cards for entities
- **Image and Video Search:** Multimedia result types

### Out of Scope

- Ads auction system (separate design)
- Google Maps / local search integration details
- Full NLP / conversational AI (e.g., featured snippets via LLMs)
- Browser or client-side implementation
- Content moderation / safe search filtering (mentioned briefly)

---

## 2. Functional Requirements

| # | Requirement | Description |
|---|-------------|-------------|
| F1 | Web Crawling | Continuously discover and fetch web pages respecting robots.txt |
| F2 | Content Parsing | Extract text, links, metadata, and structured data from HTML |
| F3 | Index Building | Build and maintain an inverted index for full-text search |
| F4 | Query Processing | Parse user queries, handle multi-word, phrases, operators |
| F5 | Ranked Results | Return top-K results ordered by relevance |
| F6 | Autocomplete | Suggest query completions as the user types |
| F7 | Spell Correction | Detect and correct misspelled queries |
| F8 | Snippet Generation | Show relevant text excerpts with query terms highlighted |
| F9 | Pagination | Return paginated results (10 per page, up to ~30 pages) |
| F10 | Image/Video Search | Index and retrieve multimedia content |
| F11 | Knowledge Panels | Display structured entity information |
| F12 | Freshness | Prioritize re-crawling time-sensitive content (news) |

---

## 3. Non-Functional Requirements

| # | Requirement | Target |
|---|-------------|--------|
| NF1 | Query Latency | p50 < 200ms, p99 < 500ms end-to-end |
| NF2 | Availability | 99.99% uptime (< 52 min downtime/year) |
| NF3 | Index Size | 100B+ web pages indexed |
| NF4 | Crawl Freshness | News: < 1 hour, Popular: < 1 day, Long-tail: < 30 days |
| NF5 | Throughput | 115K+ queries per second globally |
| NF6 | Cost Efficiency | < $0.001 per query served |
| NF7 | Scalability | Horizontal scaling for crawl, index, and query tiers |
| NF8 | Fault Tolerance | No single point of failure; graceful degradation |
| NF9 | Consistency | Index eventually consistent (stale by minutes, not hours) |
| NF10 | Crawl Politeness | Respect robots.txt, rate-limit per domain |

---

## 4. Back-of-the-Envelope Estimation

### 4.1 Query Traffic

```
Daily queries:          10 billion
Seconds per day:        86,400
Average QPS:            10B / 86,400 = ~115,740 QPS
Peak QPS (3x avg):      ~350,000 QPS
Queries per year:       ~3.65 trillion

Avg query length:       ~3.5 words = ~25 bytes
Query traffic:          115K * 25 bytes = ~2.9 MB/s (negligible)
```

### 4.2 Web Scale

```
Total web pages:            ~100 billion (indexed)
Avg raw HTML size:          ~100 KB (compressed)
Avg extracted text size:    ~10 KB per page
Total raw content:          100B * 100KB = 10 PB (compressed HTML)
Total extracted text:       100B * 10KB  = 1 PB

Pages discovered but not indexed: ~500 billion (deep web, duplicates)
Unique domains:             ~350 million
```

### 4.3 Inverted Index Size

```
Unique terms:               ~10 billion (after stemming, normalization)
Avg posting list length:    ~1,000 documents per term (power-law distribution)
Avg posting entry:          ~12 bytes (doc_id: 5B, tf: 2B, positions: 5B)

Posting lists total:        10B terms * 1K docs * 12 bytes = ~120 TB
Term dictionary:            10B terms * 20 bytes avg = ~200 GB
Total inverted index:       ~150-200 TB (with compression ~50-80 TB)
```

### 4.4 Crawler Throughput

```
Pages to re-crawl per day:  ~1 billion (priority-based)
Avg page fetch time:        ~500ms (including DNS + download)
Pages per crawler worker:   ~170K/day (with parallelism per worker)
Crawler workers needed:     1B / 170K = ~6,000 workers
Bandwidth:                  1B * 100KB / 86400 = ~1.2 TB/s download
```

### 4.5 Storage Summary

```
Component              Size          Storage Type
─────────────────────────────────────────────────
Raw HTML store         10 PB         Distributed FS (GFS/Colossus)
Extracted text         1 PB          Column store (BigTable)
Inverted index         80 TB         Custom in-memory + SSD
PageRank scores        800 GB        Pre-computed, in-memory
URL frontier           50 GB         Distributed priority queue
Link graph             2 TB          Graph store
Query logs             500 TB/year   Append-only log store
```

### 4.6 Serving Infrastructure

```
Index shards:           ~10,000 shards (each ~8 TB of index)
Replicas per shard:     3 (for availability + load distribution)
Total index servers:    ~30,000 machines
Query frontend servers: ~5,000 (behind load balancers)
Data centers:           ~20 globally (serve from nearest)
```

---

## 5. API Design

### 5.1 Web Search

```
GET /api/v1/search

Query Parameters:
  q        (required)   Search query string, max 2048 chars
  page     (optional)   Page number, default 1, max 30
  count    (optional)   Results per page, default 10, max 50
  lang     (optional)   Language filter (ISO 639-1), e.g., "en"
  region   (optional)   Region filter (ISO 3166-1), e.g., "US"
  safe     (optional)   Safe search: "off", "moderate", "strict"
  type     (optional)   Result type: "web", "image", "video", "news"
  freshness(optional)   Time filter: "day", "week", "month", "year"

Response (200 OK):
{
  "query": "distributed systems consensus",
  "corrected_query": null,
  "total_results": 48200000,
  "search_time_ms": 187,
  "results": [
    {
      "rank": 1,
      "url": "https://example.com/raft-consensus",
      "title": "Understanding Raft Consensus Algorithm",
      "snippet": "...a <b>distributed</b> <b>consensus</b> algorithm...",
      "domain": "example.com",
      "last_crawled": "2026-04-08T14:22:00Z",
      "content_type": "web",
      "sitelinks": [...]
    },
    ...
  ],
  "knowledge_panel": { ... },
  "related_searches": ["paxos vs raft", "distributed consensus explained"],
  "pagination": {
    "current_page": 1,
    "total_pages": 30,
    "next": "/api/v1/search?q=distributed+systems+consensus&page=2"
  }
}
```

### 5.2 Autocomplete / Suggestions

```
GET /api/v1/suggest

Query Parameters:
  q        (required)   Partial query prefix
  lang     (optional)   Language, default "en"
  count    (optional)   Number of suggestions, default 8

Response (200 OK):
{
  "prefix": "how to des",
  "suggestions": [
    { "text": "how to design a search engine",     "score": 0.95 },
    { "text": "how to design a database",           "score": 0.89 },
    { "text": "how to design distributed systems",  "score": 0.84 },
    ...
  ]
}

Latency requirement: < 50ms (must feel instant while typing)
```

### 5.3 Spell Correction

```
GET /api/v1/spell

Query Parameters:
  q        (required)   Query to check

Response (200 OK):
{
  "original": "distribted systms",
  "corrected": "distributed systems",
  "confidence": 0.97,
  "alternatives": [
    "distributed systems",
    "distributed streams"
  ]
}
```

---

## 6. Data Model and Database Selection

### 6.1 Core Data Structures

#### Inverted Index Entry

```
Term Dictionary Entry:
┌──────────────────────────────────────────────────┐
│  term: "consensus"                               │
│  document_frequency: 2,340,000                   │
│  posting_list_offset: 0x7FA3B200                 │
│  posting_list_length: 28,080,000 bytes           │
│  collection_frequency: 5,120,000                 │
└──────────────────────────────────────────────────┘

Posting List (for term "consensus"):
┌─────────────────────────────────────────────────────────────┐
│  doc_id   │  term_freq  │  positions        │  field_flags  │
├───────────┼─────────────┼───────────────────┼───────────────┤
│  1003842  │     7       │  [12, 45, 89,     │  title=1      │
│           │             │   134, 201, 267,  │  body=1       │
│           │             │   312]            │  anchor=0     │
├───────────┼─────────────┼───────────────────┼───────────────┤
│  1003901  │     3       │  [5, 78, 156]     │  title=1      │
│           │             │                   │  body=1       │
│           │             │                   │  anchor=1     │
├───────────┼─────────────┼───────────────────┼───────────────┤
│  1004217  │     1       │  [42]             │  title=0      │
│           │             │                   │  body=1       │
│           │             │                   │  anchor=0     │
└───────────┴─────────────┴───────────────────┴───────────────┘

Sorted by doc_id for efficient intersection and delta encoding.
```

#### Document Metadata Store

```
Document Record:
┌──────────────────────────────────────────────────────┐
│  doc_id:          uint64                             │
│  url:             string (max 2048)                  │
│  canonical_url:   string                             │
│  title:           string (max 512)                   │
│  content_hash:    uint64 (SimHash for near-dedup)    │
│  language:        enum (ISO 639-1)                   │
│  last_crawled:    timestamp                          │
│  last_modified:   timestamp                          │
│  content_length:  uint32                             │
│  pagerank:        float32                            │
│  spam_score:      float32                            │
│  domain_id:       uint32                             │
│  outlink_count:   uint16                             │
│  inlink_count:    uint32                             │
└──────────────────────────────────────────────────────┘
```

#### URL Frontier Entry

```
URL Frontier Record:
┌──────────────────────────────────────────────────┐
│  url:             string                         │
│  priority:        float32 (based on PageRank)    │
│  domain:          string (for politeness)        │
│  last_crawled:    timestamp                      │
│  crawl_interval:  duration (adaptive)            │
│  retry_count:     uint8                          │
│  status:          enum (PENDING, IN_PROGRESS,    │
│                         DONE, FAILED)            │
└──────────────────────────────────────────────────┘
```

### 6.2 Database Selection

```
┌─────────────────────────┬──────────────────────────────────────────┐
│  Data                   │  Storage System                          │
├─────────────────────────┼──────────────────────────────────────────┤
│  Inverted Index         │  Custom distributed store (SSTable-like) │
│                         │  In-memory term dict + SSD posting lists │
├─────────────────────────┼──────────────────────────────────────────┤
│  Raw HTML / Content     │  Distributed FS (GFS / Colossus / HDFS) │
├─────────────────────────┼──────────────────────────────────────────┤
│  Document Metadata      │  BigTable / HBase (wide-column store)    │
├─────────────────────────┼──────────────────────────────────────────┤
│  URL Frontier           │  Distributed priority queue              │
│                         │  (Redis sorted sets + persistent backing)│
├─────────────────────────┼──────────────────────────────────────────┤
│  Link Graph             │  Graph store (custom adjacency lists)    │
├─────────────────────────┼──────────────────────────────────────────┤
│  PageRank Scores        │  Pre-computed, stored in doc metadata    │
├─────────────────────────┼──────────────────────────────────────────┤
│  Query Logs             │  Append-only distributed log (Kafka)     │
├─────────────────────────┼──────────────────────────────────────────┤
│  Autocomplete Trie      │  In-memory trie / prefix tree            │
│                         │  (replicated across query servers)       │
├─────────────────────────┼──────────────────────────────────────────┤
│  Spell Correction Dict  │  In-memory (BK-tree / SymSpell)          │
└─────────────────────────┴──────────────────────────────────────────┘
```

### 6.3 Why Not a Traditional RDBMS?

- **Scale:** 100B documents with 10B unique terms cannot fit in a single relational database
- **Access patterns:** Search requires posting list lookups (sequential scan of sorted lists), not row-by-row queries
- **Custom compression:** Inverted indexes use domain-specific compression (delta encoding, variable-byte) that relational stores don't support
- **Latency:** We need sub-millisecond posting list lookups, which requires memory-mapped custom data structures

---

## 7. High-Level Architecture

### 7.1 System Overview - Three Major Pipelines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WEB SEARCH ENGINE - OVERVIEW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    1. CRAWL PIPELINE (Offline)                      │   │
│   │                                                                     │   │
│   │   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────────┐  │   │
│   │   │   URL    │──>│ Crawler  │──>│  Content  │──>│   URL        │  │   │
│   │   │ Frontier │   │ Workers  │   │   Store   │   │  Extractor   │  │   │
│   │   └──────────┘   └──────────┘   └───────────┘   └──────┬───────┘  │   │
│   │        ^              │                                  │         │   │
│   │        │              v                                  │         │   │
│   │        │         ┌──────────┐                            │         │   │
│   │        │         │   DNS    │                            │         │   │
│   │        │         │ Resolver │                            │         │   │
│   │        │         └──────────┘                            │         │   │
│   │        │                                                 │         │   │
│   │        └───────────── Dedup ◄────────────────────────────┘         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    v                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    2. INDEX PIPELINE (Batch/Stream)                 │   │
│   │                                                                     │   │
│   │   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────────┐  │   │
│   │   │ Content  │──>│  HTML    │──>│Tokenizer/ │──>│   Inverted   │  │   │
│   │   │  Store   │   │ Parser   │   │ Analyzer  │   │ Index Builder│  │   │
│   │   └──────────┘   └──────────┘   └───────────┘   └──────┬───────┘  │   │
│   │                                                         │          │   │
│   │                        ┌──────────────┐                 │          │   │
│   │                        │   PageRank   │                 │          │   │
│   │                        │ Computation  │                 │          │   │
│   │                        └──────┬───────┘                 │          │   │
│   │                               │                         v          │   │
│   │                               │              ┌──────────────────┐  │   │
│   │                               └─────────────>│  Index Shards   │  │   │
│   │                                              │  (distributed)  │  │   │
│   │                                              └──────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    v                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    3. QUERY PIPELINE (Online)                       │   │
│   │                                                                     │   │
│   │   ┌──────┐  ┌───────┐  ┌────────┐  ┌─────────┐  ┌──────────────┐  │   │
│   │   │ User │─>│  LB / │─>│ Query  │─>│  Index  │─>│   Ranker /   │  │   │
│   │   │      │  │  CDN  │  │ Parser │  │ Servers │  │  Re-Ranker   │  │   │
│   │   └──────┘  └───────┘  └────────┘  └─────────┘  └──────┬───────┘  │   │
│   │      ^                                                   │         │   │
│   │      │         ┌────────────┐    ┌──────────────┐        │         │   │
│   │      │         │  Snippet   │◄───│   Result     │◄───────┘         │   │
│   │      │         │ Generator  │    │  Compiler    │                  │   │
│   │      │         └─────┬──────┘    └──────────────┘                  │   │
│   │      │               │                                             │   │
│   │      └───────────────┘                                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Query Pipeline - Detailed Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      QUERY PROCESSING PIPELINE                          │
│                                                                          │
│  User Query: "best distributed consensus algorithms"                     │
│                                                                          │
│  ┌──────────────┐                                                        │
│  │  1. Query    │  - Tokenize: ["best", "distributed", "consensus",     │
│  │     Parser   │               "algorithms"]                            │
│  │              │  - Remove stop words: ["distributed", "consensus",     │
│  │              │                        "algorithms"]                    │
│  │              │  - Stem: ["distribut", "consensus", "algorithm"]        │
│  │              │  - Spell check: OK                                      │
│  └──────┬───────┘                                                        │
│         │                                                                │
│         v                                                                │
│  ┌──────────────┐                                                        │
│  │  2. Query    │  - Check query cache (exact match)                     │
│  │     Cache    │  - Cache hit? Return cached results                    │
│  │              │  - Cache miss? Proceed to index lookup                 │
│  └──────┬───────┘                                                        │
│         │ (cache miss)                                                   │
│         v                                                                │
│  ┌──────────────┐     ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │  3. Scatter  │────>│ Shard 0 │ │ Shard 1 │ │Shard N-1│              │
│  │   (Fan-Out)  │────>│         │ │         │ │         │              │
│  │              │────>│ top-K   │ │ top-K   │ │ top-K   │              │
│  └──────────────┘     └────┬────┘ └────┬────┘ └────┬────┘              │
│                            │           │           │                    │
│                            v           v           v                    │
│                       ┌────────────────────────────────┐                │
│                       │  4. Gather (Merge top-K lists) │                │
│                       │     Global top-K by BM25 score │                │
│                       └──────────────┬─────────────────┘                │
│                                      │                                  │
│                                      v                                  │
│                       ┌────────────────────────────────┐                │
│                       │  5. Re-Ranker (ML Model)       │                │
│                       │     - Apply PageRank boost     │                │
│                       │     - Freshness signal         │                │
│                       │     - User context / locale    │                │
│                       │     - Click-through model      │                │
│                       └──────────────┬─────────────────┘                │
│                                      │                                  │
│                                      v                                  │
│                       ┌────────────────────────────────┐                │
│                       │  6. Result Compiler            │                │
│                       │     - Fetch doc metadata       │                │
│                       │     - Generate snippets        │                │
│                       │     - Build knowledge panel    │                │
│                       │     - Attach related searches  │                │
│                       └──────────────┬─────────────────┘                │
│                                      │                                  │
│                                      v                                  │
│                              ┌──────────────┐                           │
│                              │   Response   │                           │
│                              │   to User    │                           │
│                              │  (~200ms)    │                           │
│                              └──────────────┘                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Component Breakdown

| Component | Responsibility | Scale |
|-----------|---------------|-------|
| Load Balancer / CDN | Route queries to nearest DC, cache static assets | Global, 20+ DCs |
| Query Parser | Tokenize, normalize, spell-check, classify intent | Stateless, ~5K instances |
| Query Cache | Cache frequent query results (LRU) | ~100 TB distributed cache |
| Index Servers | Store index shards, execute BM25 retrieval | ~30K machines |
| Ranker / Re-ranker | ML-based relevance scoring | Co-located with index or separate tier |
| Snippet Generator | Extract relevant text from stored documents | Stateless workers |
| Result Compiler | Assemble final response (results + panels + suggestions) | Stateless workers |
| Autocomplete Service | Trie-based prefix matching on query logs | In-memory, replicated |
| Spell Correction | Edit-distance computation, language models | In-memory, replicated |

---

## 8. Deep Dive: Core Components

### 8.1 Web Crawler

The web crawler is the data ingestion layer of the search engine. It continuously
discovers and fetches web pages, feeding content into the indexing pipeline.

#### 8.1.1 Crawler Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          WEB CRAWLER SYSTEM                           │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     URL FRONTIER                                │   │
│  │                                                                 │   │
│  │  ┌───────────────┐    ┌───────────────┐    ┌────────────────┐  │   │
│  │  │  Priority     │    │  Politeness   │    │  Seen URL      │  │   │
│  │  │  Queues       │    │  Queues       │    │  Filter        │  │   │
│  │  │               │    │               │    │  (Bloom Filter)│  │   │
│  │  │  High: news   │    │  Per-domain   │    │                │  │   │
│  │  │  Med:  popular│    │  rate limits  │    │  ~50B URLs     │  │   │
│  │  │  Low:  long   │    │  last_access  │    │  FPR: 0.01%   │  │   │
│  │  │       tail    │    │  timestamps   │    │  ~60GB memory  │  │   │
│  │  └───────┬───────┘    └───────┬───────┘    └────────────────┘  │   │
│  │          │                    │                                  │   │
│  │          └────────┬───────────┘                                  │   │
│  └───────────────────┼─────────────────────────────────────────────┘   │
│                      │                                                  │
│                      v                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CRAWLER WORKERS (6,000+)                     │   │
│  │                                                                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │Worker N  │       │   │
│  │  │          │  │          │  │          │  │          │       │   │
│  │  │ Fetch    │  │ Fetch    │  │ Fetch    │  │ Fetch    │       │   │
│  │  │ Parse    │  │ Parse    │  │ Parse    │  │ Parse    │       │   │
│  │  │ Extract  │  │ Extract  │  │ Extract  │  │ Extract  │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────┬───────────────────────────────────────┘   │
│                            │                                           │
│           ┌────────────────┼────────────────┐                          │
│           v                v                v                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  DNS Cache   │  │   Content    │  │  Extracted   │                 │
│  │  (resolved   │  │   Store      │  │  URLs        │                 │
│  │   IPs)       │  │  (raw HTML)  │  │  (new links) │                 │
│  └──────────────┘  └──────────────┘  └──────┬───────┘                 │
│                                              │                         │
│                    ┌─────────────────────────┘                         │
│                    v                                                    │
│           ┌──────────────┐                                             │
│           │  Dedup /     │  - URL normalization                        │
│           │  Content     │  - SimHash for near-duplicate detection     │
│           │  Filter      │  - Canonical URL resolution                 │
│           └──────┬───────┘                                             │
│                  │                                                      │
│                  v                                                      │
│           ┌──────────────┐                                             │
│           │  Back to     │                                             │
│           │  URL Frontier│                                             │
│           └──────────────┘                                             │
└────────────────────────────────────────────────────────────────────────┘
```

#### 8.1.2 URL Frontier Design

The URL frontier is the most critical data structure in the crawler. It determines
**what** to crawl and **when** to crawl it.

**Two-level queue architecture:**

1. **Front queues (Priority):** Multiple queues ordered by priority
   - Priority 1: Breaking news sites, frequently updated pages
   - Priority 2: Popular sites (top 1M by PageRank)
   - Priority 3: Regular content
   - Priority 4: Deep web, rarely changing pages

2. **Back queues (Politeness):** One queue per domain
   - Ensures at most one outstanding request per domain
   - Enforces minimum delay between requests (typically 1-10 seconds)
   - Respects `Crawl-delay` directive from robots.txt

```
Front Queues (Priority)              Back Queues (Politeness)
┌────────────────────┐               ┌────────────────────┐
│ Priority 1 (News)  │──┐            │ example.com queue  │
│  cnn.com/breaking  │  │            │  /page1            │
│  bbc.co.uk/news    │  │            │  /page2            │
└────────────────────┘  │            │  last_access: T-5s │
┌────────────────────┐  │   Router   └────────────────────┘
│ Priority 2 (Pop.)  │──┼──────────> ┌────────────────────┐
│  github.com/...    │  │   (maps    │ github.com queue   │
│  stackoverflow.com │  │    URL to  │  /repo1            │
└────────────────────┘  │    domain  │  /repo2            │
┌────────────────────┐  │    queue)  │  last_access: T-2s │
│ Priority 3 (Reg.)  │──┤            └────────────────────┘
│  blog.example.com  │  │            ┌────────────────────┐
│  docs.foo.org      │  │            │ wikipedia.org queue│
└────────────────────┘  │            │  /article1         │
┌────────────────────┐  │            │  /article2         │
│ Priority 4 (Long)  │──┘            │  last_access: T-8s │
│  archive.org/...   │               └────────────────────┘
└────────────────────┘
```

#### 8.1.3 Politeness and Ethics

```
Robots.txt Handling:
  1. Fetch and cache robots.txt for each domain (TTL: 24 hours)
  2. Parse Allow/Disallow directives
  3. Respect Crawl-delay (default: 1 second between requests)
  4. Honor noindex, nofollow meta tags

Rate Limiting per Domain:
  - Max 1 concurrent request per domain
  - Minimum 1-second gap between requests to same domain
  - Back off exponentially on 429 / 503 responses
  - Track domain health score; reduce crawl rate for slow domains

Ethical Crawling:
  - Identify crawler via User-Agent header
  - Provide contact info for webmasters
  - Support robots.txt "Sitemap:" directive
  - Handle HTTP 304 Not Modified (If-Modified-Since)
```

#### 8.1.4 Handling Dynamic Content

Modern web pages rely heavily on JavaScript. A search engine must render
JavaScript to see the full page content.

```
Approach: Two-Phase Crawling

Phase 1 - Static HTML Fetch:
  - Fast, low-cost HTTP GET
  - Extracts links, basic text, metadata
  - Sufficient for ~60% of web pages

Phase 2 - JavaScript Rendering:
  - Headless browser (Chromium-based)
  - Wait for page load + dynamic content
  - Much more expensive (~10x cost of static fetch)
  - Used for pages detected as JS-heavy

Decision Logic:
  if page has <script> tags AND extracted text is minimal:
      queue for Phase 2 rendering
  else:
      use Phase 1 content
```

#### 8.1.5 Duplicate and Near-Duplicate Detection

```
URL-level Dedup:
  - Normalize URLs (lowercase host, remove fragments, sort params)
  - Bloom filter with 50B entries, 0.01% FPR
  - Memory: ~60 GB for 50B URLs

Content-level Dedup (SimHash / MinHash):
  - Compute SimHash (64-bit fingerprint) of page content
  - Two documents are near-duplicates if Hamming distance <= 3
  - Store fingerprints in a lookup table
  - O(1) lookup for exact duplicates
  - For near-duplicates: use multi-probe approach (flip k bits)

  SimHash Algorithm:
    1. Tokenize document into shingles (3-grams)
    2. Hash each shingle to 64-bit value
    3. For each bit position: sum weights (+1 for 1, -1 for 0)
    4. Final hash: 1 if sum > 0, else 0 for each position
    5. Compare: Hamming distance = number of differing bits
```

---

### 8.2 Inverted Index

The inverted index is the heart of the search engine. It maps every term to the
list of documents containing that term, enabling efficient full-text search.

#### 8.2.1 Inverted Index Structure

```
┌────────────────────────────────────────────────────────────────────┐
│                      INVERTED INDEX STRUCTURE                      │
│                                                                    │
│  TERM DICTIONARY (in-memory hash table or B-tree)                  │
│  ┌──────────────┬──────────┬───────────┬────────────┐             │
│  │    Term      │   DF     │  Offset   │   Length   │             │
│  ├──────────────┼──────────┼───────────┼────────────┤             │
│  │  "algorithm" │  5.2M    │  0x00A0   │  62.4 MB   │             │
│  │  "consensus" │  2.3M    │  0x3BA0   │  27.6 MB   │             │
│  │  "database"  │  12.1M   │  0x7200   │  145.2 MB  │             │
│  │  "distribut" │  8.7M    │  0xC100   │  104.4 MB  │             │
│  │     ...      │   ...    │   ...     │    ...     │             │
│  └──────────────┴──────────┴───────────┴────────────┘             │
│                                  │                                 │
│                                  │ (pointer to SSD/memory)        │
│                                  v                                 │
│  POSTING LISTS (on SSD, hot terms cached in memory)                │
│                                                                    │
│  Posting list for "consensus":                                     │
│  ┌────────┬────┬──────────────────┐                               │
│  │ DocID  │ TF │ Positions        │  (delta-encoded, var-byte)    │
│  ├────────┼────┼──────────────────┤                               │
│  │  1001  │  5 │ [12,45,89,134,   │                               │
│  │        │    │  201]            │                               │
│  ├────────┼────┼──────────────────┤                               │
│  │ +47    │  3 │ [5,78,156]       │  <-- delta from prev doc_id   │
│  │(=1048) │    │                  │                               │
│  ├────────┼────┼──────────────────┤                               │
│  │ +102   │  1 │ [42]             │                               │
│  │(=1150) │    │                  │                               │
│  ├────────┼────┼──────────────────┤                               │
│  │  ...   │... │ ...              │                               │
│  └────────┴────┴──────────────────┘                               │
│                                                                    │
│  Skip Pointers (every sqrt(N) entries):                            │
│  ┌──────────────────────────────────────────────────┐             │
│  │  DocID 1001 ──> offset 0                         │             │
│  │  DocID 5230 ──> offset 4096                      │             │
│  │  DocID 12040 ─> offset 8192                      │             │
│  │  DocID 24500 ─> offset 12288                     │             │
│  └──────────────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────────────┘
```

#### 8.2.2 Index Compression

Compression is critical because the raw inverted index is ~150 TB. Good
compression reduces this to ~50-80 TB while maintaining fast decompression.

```
Technique 1: Delta Encoding (for doc_ids)
  Original:     [1001, 1048, 1150, 1302, 1510, 1998]
  Deltas:       [1001, 47,   102,  152,  208,  488]
  Observation:  Deltas are much smaller numbers, fewer bits needed

Technique 2: Variable-Byte (VByte) Encoding
  - Use 7 bits per byte for data, 1 bit as continuation flag
  - Small numbers (< 128) = 1 byte
  - Medium numbers (< 16384) = 2 bytes
  - Large numbers (< 2M) = 3 bytes

  Example: encoding delta 47
    47 < 128, so: [0|0101111] = 1 byte
  Example: encoding delta 488
    488 >= 128, so: [1|0000011] [0|1101000] = 2 bytes

Technique 3: PForDelta (Patched Frame-of-Reference)
  - Encode blocks of 128 doc_id deltas at a time
  - Find the minimum bits needed for most values (e.g., 90th percentile)
  - Encode most values with that bit width
  - "Patch" exceptions (outliers) with a separate list
  - Very SIMD-friendly for fast decompression

Compression Ratios:
  ┌──────────────────┬──────────────┬────────────────┐
  │  Technique       │  Ratio       │  Decode Speed  │
  ├──────────────────┼──────────────┼────────────────┤
  │  Uncompressed    │  1.0x        │  Baseline      │
  │  VByte           │  3-4x        │  ~1 GB/s       │
  │  PForDelta       │  5-8x        │  ~2 GB/s       │
  │  Simple-9/16     │  4-6x        │  ~1.5 GB/s     │
  │  Roaring Bitmap  │  10-100x     │  ~3 GB/s       │
  └──────────────────┴──────────────┴────────────────┘
```

#### 8.2.3 Index Construction (MapReduce)

```
┌────────────────────────────────────────────────────────────────────┐
│                    INDEX CONSTRUCTION PIPELINE                     │
│                                                                    │
│  Phase 1: MAP                                                      │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Input: (doc_id, raw_content) pairs                      │     │
│  │                                                          │     │
│  │  For each document:                                      │     │
│  │    1. Parse HTML, extract text                           │     │
│  │    2. Tokenize: split into terms                         │     │
│  │    3. Normalize: lowercase, remove accents               │     │
│  │    4. Stem: "running" -> "run", "algorithms" -> "algorithm"│   │
│  │    5. Emit: (term, doc_id, term_frequency, [positions])  │     │
│  │                                                          │     │
│  │  Example:                                                │     │
│  │    Doc 1001: "Raft is a consensus algorithm"             │     │
│  │    Emits:                                                │     │
│  │      ("raft",      1001, 1, [0])                         │     │
│  │      ("consensus", 1001, 1, [3])                         │     │
│  │      ("algorithm", 1001, 1, [4])                         │     │
│  └──────────────────────────────────────────────────────────┘     │
│                              │                                     │
│                              v                                     │
│  Phase 2: SHUFFLE (Group by term)                                  │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Sort and group all (term, doc_id, tf, positions)        │     │
│  │  by term, then by doc_id within each term                │     │
│  │                                                          │     │
│  │  "algorithm" -> [(1001, 1, [4]), (1048, 3, [1,5,12]),   │     │
│  │                  (1150, 2, [0,7]), ...]                   │     │
│  │  "consensus" -> [(1001, 1, [3]), (1048, 2, [0,6]), ...] │     │
│  └──────────────────────────────────────────────────────────┘     │
│                              │                                     │
│                              v                                     │
│  Phase 3: REDUCE (Build posting lists)                             │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  For each term:                                          │     │
│  │    1. Sort postings by doc_id                            │     │
│  │    2. Delta-encode doc_ids                               │     │
│  │    3. Compress with VByte/PForDelta                      │     │
│  │    4. Build skip pointers                                │     │
│  │    5. Write to index shard                               │     │
│  │    6. Record term -> (offset, length) in dictionary      │     │
│  └──────────────────────────────────────────────────────────┘     │
│                              │                                     │
│                              v                                     │
│  Output: Index Shards + Term Dictionary                            │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Shard 0: documents 0 - 9,999,999                       │     │
│  │  Shard 1: documents 10,000,000 - 19,999,999             │     │
│  │  ...                                                     │     │
│  │  Shard 9999: documents 99,990,000,000 - 99,999,999,999  │     │
│  └──────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

#### 8.2.4 Index Partitioning Strategies

```
Strategy 1: Document-Partitioned (Used by Google, most search engines)

  Each shard contains ALL terms for a SUBSET of documents.

  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │  Shard 0    │  │  Shard 1    │  │  Shard 2    │
  │             │  │             │  │             │
  │ Docs 0-10M │  │ Docs 10M-20M│  │ Docs 20M-30M│
  │             │  │             │  │             │
  │ All terms   │  │ All terms   │  │ All terms   │
  │ for these   │  │ for these   │  │ for these   │
  │ docs        │  │ docs        │  │ docs        │
  └─────────────┘  └─────────────┘  └─────────────┘

  Query execution: Scatter query to ALL shards, gather top-K from each

  Pros:
    + Each shard is self-contained (can compute local BM25 scores)
    + Easy to add/remove documents (affect only one shard)
    + Shard failure only loses a fraction of documents
    + Load naturally balanced for most queries

  Cons:
    - Every query must hit ALL shards (high fan-out)
    - N shards = N network round trips per query

Strategy 2: Term-Partitioned

  Each shard contains ALL documents for a SUBSET of terms.

  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │  Shard 0    │  │  Shard 1    │  │  Shard 2    │
  │             │  │             │  │             │
  │ Terms A-F   │  │ Terms G-M   │  │ Terms N-Z   │
  │             │  │             │  │             │
  │ All docs    │  │ All docs    │  │ All docs    │
  │ for these   │  │ for these   │  │ for these   │
  │ terms       │  │ terms       │  │ terms       │
  └─────────────┘  └─────────────┘  └─────────────┘

  Query execution: Route each query term to its shard, intersect results

  Pros:
    + Single-term queries hit only ONE shard
    + Less fan-out for simple queries

  Cons:
    - Multi-term queries require cross-shard intersection
    - Hot terms (e.g., "the") create hot shards
    - Adding documents requires updating EVERY shard
    - Harder to compute document-level scores (BM25)

  Verdict: Document-partitioned wins for web search at scale.
```

---

### 8.3 Query Processing and Ranking

#### 8.3.1 Query Processing Pipeline

```
Input: "Best distributed consensus algorithms 2026"
                    │
                    v
┌──────────────────────────────────────────────┐
│  Step 1: TOKENIZATION                        │
│  ["Best", "distributed", "consensus",        │
│   "algorithms", "2026"]                      │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│  Step 2: LOWERCASING                         │
│  ["best", "distributed", "consensus",        │
│   "algorithms", "2026"]                      │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│  Step 3: STOP WORD REMOVAL (optional)        │
│  Remove: "best" (sometimes kept for ranking) │
│  ["distributed", "consensus",                │
│   "algorithms", "2026"]                      │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│  Step 4: STEMMING / LEMMATIZATION            │
│  "distributed" -> "distribut"                │
│  "algorithms"  -> "algorithm"                │
│  ["distribut", "consensus", "algorithm",     │
│   "2026"]                                    │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│  Step 5: QUERY EXPANSION (optional)          │
│  Add synonyms: "consensus" + "agreement"     │
│  Add related: "raft", "paxos"                │
│  (Controlled expansion to avoid topic drift) │
└──────────────────────┬───────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────┐
│  Step 6: INTENT CLASSIFICATION               │
│  Informational query (not navigational or    │
│  transactional)                              │
│  -> Use standard web results ranking         │
└──────────────────────────────────────────────┘
```

#### 8.3.2 Scoring: From Boolean to BM25

```
Evolution of Scoring Models:

1. Boolean Retrieval (1960s)
   Query: "distributed AND consensus"
   Returns: All documents containing BOTH terms (unranked)
   Problem: No ranking, returns too many or too few results

2. TF-IDF (1970s)
   score(q, d) = SUM over terms t in q:
       tf(t, d) * idf(t)

   where:
     tf(t, d) = frequency of term t in document d
     idf(t)   = log(N / df(t))
               = inverse document frequency (rare terms score higher)

   Problem: No term frequency saturation (repeating a term
            100 times shouldn't be 100x better than once)

3. BM25 (1990s, Okapi BM25) - INDUSTRY STANDARD
   score(q, d) = SUM over terms t in q:
       idf(t) * (tf(t,d) * (k1 + 1)) / (tf(t,d) + k1 * (1 - b + b * |d|/avgdl))

   where:
     k1 = 1.2  (term frequency saturation parameter)
     b  = 0.75 (document length normalization parameter)
     |d| = document length
     avgdl = average document length in collection

   Key properties:
     - tf saturation: diminishing returns for high term frequency
     - Length normalization: longer documents don't get unfair advantage
     - IDF weighting: rare terms are more important

   Example Calculation:
     Query: "consensus algorithm"
     Document d (length 500 words, avgdl = 1000):
       tf("consensus", d) = 5
       tf("algorithm", d) = 3
       df("consensus") = 2.3M out of 100B docs
       df("algorithm") = 5.2M out of 100B docs

     idf("consensus") = log((100B - 2.3M + 0.5) / (2.3M + 0.5)) = 10.67
     idf("algorithm") = log((100B - 5.2M + 0.5) / (5.2M + 0.5)) = 9.85

     BM25("consensus"):
       10.67 * (5 * 2.2) / (5 + 1.2 * (1 - 0.75 + 0.75 * 500/1000))
       = 10.67 * 11 / (5 + 1.2 * 0.625)
       = 10.67 * 11 / 5.75
       = 20.40

     BM25("algorithm"):
       9.85 * (3 * 2.2) / (3 + 1.2 * 0.625)
       = 9.85 * 6.6 / 3.75
       = 17.34

     Total BM25 score = 20.40 + 17.34 = 37.74
```

#### 8.3.3 Two-Phase Ranking

```
┌────────────────────────────────────────────────────────────────────┐
│                     TWO-PHASE RANKING ARCHITECTURE                 │
│                                                                    │
│  Phase 1: FAST RETRIEVAL (BM25)                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  - Applied on ALL index shards in parallel               │     │
│  │  - Uses BM25 scoring (cheap, CPU-efficient)              │     │
│  │  - Each shard returns top-K candidates (K = 100-1000)    │     │
│  │  - Merge results from all shards -> global top-K         │     │
│  │  - Latency budget: ~50ms                                 │     │
│  │  - Candidates: ~100B docs -> ~10,000 candidates          │     │
│  └──────────────────────────────────────────────────────────┘     │
│                              │                                     │
│                              v                                     │
│  Phase 2: RE-RANKING (ML Model)                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Applied on top ~1,000-10,000 candidates from Phase 1    │     │
│  │                                                          │     │
│  │  Features used by the ML re-ranker:                      │     │
│  │  ┌─────────────────────────────────────────────────┐     │     │
│  │  │  Query-Document Features:                       │     │     │
│  │  │    - BM25 score (from Phase 1)                  │     │     │
│  │  │    - Term overlap in title, body, anchor text   │     │     │
│  │  │    - Phrase match score                         │     │     │
│  │  │    - Query term proximity in document           │     │     │
│  │  ├─────────────────────────────────────────────────┤     │     │
│  │  │  Document Features:                             │     │     │
│  │  │    - PageRank score                             │     │     │
│  │  │    - Document freshness (age since last update) │     │     │
│  │  │    - Domain authority                           │     │     │
│  │  │    - Spam score (probability of spam)           │     │     │
│  │  │    - Content quality score                      │     │     │
│  │  │    - Mobile-friendliness                        │     │     │
│  │  │    - Page load speed (Core Web Vitals)          │     │     │
│  │  ├─────────────────────────────────────────────────┤     │     │
│  │  │  User/Context Features:                         │     │     │
│  │  │    - User language and locale                   │     │     │
│  │  │    - Historical click-through rate for this URL │     │     │
│  │  │    - Query intent classification                │     │     │
│  │  │    - Device type (mobile vs desktop)            │     │     │
│  │  └─────────────────────────────────────────────────┘     │     │
│  │                                                          │     │
│  │  Model: LambdaMART or Deep Neural Network (BERT-based)   │     │
│  │  Latency budget: ~100ms for re-ranking 1000 candidates   │     │
│  └──────────────────────────────────────────────────────────┘     │
│                              │                                     │
│                              v                                     │
│  Output: Top 10 results for page 1 (top 300 for pagination)       │
└────────────────────────────────────────────────────────────────────┘
```

#### 8.3.4 Scatter-Gather Execution

```
┌───────────────────────────────────────────────────────────────────────┐
│                    SCATTER-GATHER QUERY EXECUTION                     │
│                                                                       │
│  Query: "distributed consensus"                                       │
│                                                                       │
│  ┌─────────────────┐                                                  │
│  │  Query Frontend │                                                  │
│  │  (Coordinator)  │                                                  │
│  └────────┬────────┘                                                  │
│           │                                                           │
│           │  SCATTER: Send query to all N shards                      │
│           │  (parallel, async fan-out)                                 │
│           │                                                           │
│    ┌──────┼──────┬──────┬──────┬──────┬──────┐                        │
│    v      v      v      v      v      v      v                        │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│  │ S0 │ │ S1 │ │ S2 │ │ S3 │ │... │ │S9998│ │S9999│                  │
│  │    │ │    │ │    │ │    │ │    │ │    │ │    │                   │
│  │top │ │top │ │top │ │top │ │    │ │top │ │top │                   │
│  │100 │ │100 │ │100 │ │100 │ │    │ │100 │ │100 │                   │
│  └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘                   │
│     │      │      │      │      │      │      │                       │
│     └──────┴──────┴──────┴──────┴──────┴──────┘                       │
│                           │                                            │
│                           v                                            │
│                    GATHER: Merge top-100 from each shard               │
│                    ┌──────────────────────────┐                        │
│                    │  Priority queue merge    │                        │
│                    │  10,000 shards * 100     │                        │
│                    │  = 1M candidates         │                        │
│                    │  -> Global top 1,000     │                        │
│                    └──────────────────────────┘                        │
│                                                                       │
│  Optimization: Tiered Index                                           │
│  ┌────────────────────────────────────────────────────────────┐       │
│  │  Tier 1: Top 1B documents (by PageRank) - checked first   │       │
│  │  Tier 2: Next 9B documents - checked if Tier 1 insufficient│      │
│  │  Tier 3: Remaining 90B documents - rarely needed           │       │
│  │                                                            │       │
│  │  ~95% of queries are answered by Tier 1 alone              │       │
│  │  Reduces effective fan-out by 100x                         │       │
│  └────────────────────────────────────────────────────────────┘       │
│                                                                       │
│  Timeout Handling:                                                     │
│  - Set deadline of 200ms for shard responses                          │
│  - If 95% of shards respond within deadline, proceed with             │
│    partial results (graceful degradation)                              │
│  - Slow/failed shards are noted for health monitoring                 │
└───────────────────────────────────────────────────────────────────────┘
```

---

### 8.4 PageRank Algorithm

PageRank is a link-analysis algorithm that assigns an importance score to every
web page based on the link structure of the web.

#### 8.4.1 Core Concept

```
Intuition: A page is important if it is linked to by other important pages.

Formula:
  PR(A) = (1 - d) / N + d * SUM over pages B linking to A:
              PR(B) / L(B)

  where:
    d = damping factor (typically 0.85)
    N = total number of pages
    L(B) = number of outgoing links from page B

Example Web Graph:
                ┌───┐
         ┌─────│ A │─────┐
         │     └───┘     │
         v       ^       v
       ┌───┐     │     ┌───┐
       │ B │─────┘     │ C │
       └─┬─┘           └─┬─┘
         │               │
         v               v
       ┌───┐           ┌───┐
       │ D │◄──────────│ E │
       └───┘           └───┘

  Iteration 0 (initial): PR(A)=PR(B)=PR(C)=PR(D)=PR(E) = 0.20

  Iteration 1:
    PR(A) = 0.15/5 + 0.85 * PR(B)/2     = 0.03 + 0.85 * 0.10  = 0.115
    PR(B) = 0.15/5 + 0.85 * PR(A)/2     = 0.03 + 0.85 * 0.10  = 0.115
    PR(C) = 0.15/5 + 0.85 * PR(A)/2     = 0.03 + 0.85 * 0.10  = 0.115
    PR(D) = 0.15/5 + 0.85 * (PR(B)/2 + PR(E)/1) = 0.03 + 0.85*(0.10+0.20) = 0.285
    PR(E) = 0.15/5 + 0.85 * PR(C)/1     = 0.03 + 0.85 * 0.20  = 0.200

  ... converges after ~50-100 iterations
```

#### 8.4.2 Handling Edge Cases

```
Problem 1: Dead Ends (Dangling Nodes)
  Pages with no outgoing links absorb PageRank and never distribute it.

  Solution: Redistribute dangling node PageRank equally to all pages.
    For each dangling node D:
      PR_redistributed = PR(D) / N  (added to every page)

Problem 2: Spider Traps
  A group of pages that only link to each other, accumulating all PageRank.

  Solution: The damping factor d = 0.85 ensures that with probability
  (1 - d) = 0.15, a random surfer jumps to a random page, breaking
  out of the trap.

Problem 3: Scale (100B pages)
  The PageRank vector has 100B entries. A single iteration requires
  reading the entire link graph.

  Solution: MapReduce implementation (see below).
```

#### 8.4.3 PageRank at Scale with MapReduce

```
┌─────────────────────────────────────────────────────────────────────┐
│              PAGERANK COMPUTATION VIA MAPREDUCE                     │
│                                                                     │
│  Input: Link graph G and current PR vector                          │
│                                                                     │
│  Per Iteration:                                                     │
│                                                                     │
│  MAP Phase:                                                         │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │  For each page P with outlinks [L1, L2, ..., Lk]:        │      │
│  │    contribution = PR(P) / k                               │      │
│  │    For each Li:                                           │      │
│  │      emit (Li, contribution)                              │      │
│  │    emit (P, outlink_list)   // preserve graph structure   │      │
│  └───────────────────────────────────────────────────────────┘      │
│                                                                     │
│  REDUCE Phase:                                                      │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │  For each page P:                                         │      │
│  │    new_PR(P) = (1-d)/N + d * SUM(all contributions to P) │      │
│  │    emit (P, new_PR(P), outlink_list)                      │      │
│  └───────────────────────────────────────────────────────────┘      │
│                                                                     │
│  Repeat for 50-100 iterations until convergence                     │
│  (|PR_new - PR_old| < epsilon for all pages)                        │
│                                                                     │
│  At Google's Scale:                                                  │
│  - Link graph: ~2 TB (100B pages, avg 20 outlinks each)             │
│  - PR vector: ~800 GB (100B * 8 bytes)                              │
│  - Each iteration: ~3 TB read + write                               │
│  - 50 iterations: ~150 TB of I/O                                    │
│  - Time per iteration: ~30 minutes on 10K machines                  │
│  - Total: ~25 hours for full recomputation                          │
│  - Schedule: recomputed weekly or incrementally updated              │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 8.5 Autocomplete and Query Suggestions

```
┌────────────────────────────────────────────────────────────────────┐
│                    AUTOCOMPLETE SYSTEM                             │
│                                                                    │
│  Data Source: Query logs (billions of past queries + frequencies)   │
│                                                                    │
│  Data Structure: Trie with Top-K Caching                           │
│                                                                    │
│  Example Trie:                                                     │
│                  (root)                                             │
│                 /      \                                            │
│               d          h                                         │
│              /            \                                        │
│            di              ho                                      │
│           /                  \                                     │
│         dis                  how                                   │
│        /                    /   \                                   │
│      dist                 how_t  how_d                             │
│     /                    /         \                                │
│   distr                how_to     how_do                           │
│  /                    /     \                                      │
│ distrib         how_to_d  how_to_l                                 │
│                    /          \                                     │
│           how_to_des    how_to_lea                                 │
│              /                  \                                   │
│     how_to_design        how_to_learn                              │
│                                                                    │
│  Each node stores: top-8 completions by popularity                 │
│                                                                    │
│  Node "how_to_des":                                                │
│    top_completions = [                                              │
│      ("how to design a database",           freq: 50K/month),      │
│      ("how to design a search engine",      freq: 12K/month),      │
│      ("how to design distributed systems",  freq: 8K/month),       │
│      ...                                                           │
│    ]                                                               │
│                                                                    │
│  Size: ~50M unique query prefixes * ~200 bytes = ~10 GB            │
│  Fits entirely in memory on each query server                      │
│                                                                    │
│  Updates: Rebuild trie every few hours from query log aggregation   │
│  Personalization: Boost suggestions based on user history (optional)│
│                                                                    │
│  Latency: < 10ms (in-memory trie lookup)                           │
└────────────────────────────────────────────────────────────────────┘
```

### 8.6 Spell Correction

```
┌────────────────────────────────────────────────────────────────────┐
│                     SPELL CORRECTION SYSTEM                        │
│                                                                    │
│  Approach 1: Edit Distance (Norvig's method)                       │
│    - Generate all words within edit distance 1-2 of query term     │
│    - Check which candidates exist in the dictionary                │
│    - Rank by: P(correction | misspelling) ~ P(misspelling |        │
│               correction) * P(correction)                          │
│    - P(correction) from query log frequencies                      │
│                                                                    │
│  Approach 2: SymSpell (faster, pre-computed)                       │
│    - Pre-compute all delete-only edits for dictionary words        │
│    - At query time: generate deletes of query, look up in table    │
│    - O(1) lookup instead of generating all edit combinations       │
│    - 1M dictionary words, max edit distance 2:                     │
│      Pre-computed entries: ~25M (fits in ~2 GB)                    │
│                                                                    │
│  Approach 3: Noisy Channel Model (production systems)              │
│    - Train on (misspelling, correction) pairs from query logs      │
│    - Error model: P("teh" | "the") from observed typo patterns     │
│    - Language model: P("the cat") from n-gram frequencies          │
│    - Combined: argmax_c P(c) * P(query | c)                       │
│                                                                    │
│  Example:                                                          │
│    Input:  "distribted systms"                                     │
│    Candidates for "distribted":                                    │
│      "distributed" (edit dist 1, freq: very high) -> winner        │
│      "distribute"  (edit dist 2, freq: high)                       │
│    Candidates for "systms":                                        │
│      "systems"     (edit dist 1, freq: very high) -> winner        │
│      "stems"       (edit dist 2, freq: medium)                     │
│    Output: "distributed systems" (confidence: 0.97)                │
│                                                                    │
│  Context-Aware Correction:                                         │
│    "distributed systems" is far more likely as a phrase than       │
│    "distribute stems", so the bigram/trigram language model         │
│    heavily favors the correct interpretation.                      │
└────────────────────────────────────────────────────────────────────┘
```

### 8.7 Snippet Generation

```
┌────────────────────────────────────────────────────────────────────┐
│                    SNIPPET GENERATION                              │
│                                                                    │
│  Goal: Extract 1-2 sentence fragment from the document that best   │
│  matches the query, with query terms highlighted in <b> tags.      │
│                                                                    │
│  Algorithm:                                                        │
│    1. Retrieve stored document text (from content store)           │
│    2. Split into sentences                                         │
│    3. Score each sentence:                                         │
│       - Count of query terms present                               │
│       - Proximity of query terms to each other                     │
│       - Position in document (earlier = slightly better)           │
│       - Term density (query terms / total words in sentence)       │
│    4. Select top 1-2 sentences                                     │
│    5. Truncate to ~160 characters                                  │
│    6. Wrap query terms in <b>...</b> tags                          │
│                                                                    │
│  Example:                                                          │
│    Query: "distributed consensus algorithms"                       │
│    Document: (long article about Raft)                              │
│    Best sentence: "Raft is a distributed consensus algorithm        │
│      designed to be more understandable than Paxos."               │
│    Snippet: "Raft is a <b>distributed consensus algorithm</b>      │
│      designed to be more understandable than Paxos."               │
│                                                                    │
│  Performance:                                                      │
│    - Must generate snippets for top-10 results per query           │
│    - Latency budget: ~20ms (done in parallel with re-ranking)      │
│    - Pre-stored sentence boundaries in document metadata help      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### 9.1 Index Sharding Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                    INDEX SHARDING ARCHITECTURE                        │
│                                                                        │
│  Strategy: Document-Partitioned with Tiered Index                      │
│                                                                        │
│  100B documents divided into:                                          │
│    Tier 1 (Hot):  Top 1B docs by PageRank   = 100 shards * 3 replicas │
│    Tier 2 (Warm): Next 9B docs              = 900 shards * 3 replicas │
│    Tier 3 (Cold): Remaining 90B docs        = 9000 shards * 2 replicas│
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  TIER 1 (searched for every query)                           │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐         ┌──────┐               │     │
│  │  │ S0   │ │ S1   │ │ S2   │  ...    │ S99  │               │     │
│  │  │ R0   │ │ R0   │ │ R0   │         │ R0   │  100 shards   │     │
│  │  │ R1   │ │ R1   │ │ R1   │         │ R1   │  x 3 replicas │     │
│  │  │ R2   │ │ R2   │ │ R2   │         │ R2   │  = 300 servers│     │
│  │  └──────┘ └──────┘ └──────┘         └──────┘               │     │
│  │  10M docs per shard, ~8 GB index each                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  TIER 2 (searched if Tier 1 results insufficient)            │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐         ┌──────┐               │     │
│  │  │ S100 │ │ S101 │ │ S102 │  ...    │ S999 │  900 shards   │     │
│  │  │ x3   │ │ x3   │ │ x3   │         │ x3   │  = 2700 srv   │     │
│  │  └──────┘ └──────┘ └──────┘         └──────┘               │     │
│  │  10M docs per shard, ~8 GB index each                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  TIER 3 (searched for rare / long-tail queries)              │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐         ┌──────┐               │     │
│  │  │S1000 │ │S1001 │ │S1002 │  ...    │S9999 │  9000 shards  │     │
│  │  │ x2   │ │ x2   │ │ x2   │         │ x2   │  = 18000 srv  │     │
│  │  └──────┘ └──────┘ └──────┘         └──────┘               │     │
│  │  10M docs per shard, ~8 GB index each                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  Total: ~21,000 index servers (+ query frontends, etc.)                │
│                                                                        │
│  Shard Assignment:                                                     │
│    doc_id -> shard_id = hash(doc_id) % num_shards_in_tier             │
│    Or: range-partitioned by doc_id for easier maintenance              │
└────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Crawler Data Partitioning

```
URL Frontier Partitioning:
  - Partition by domain hash: URLs for the same domain go to the same
    partition (required for per-domain rate limiting)
  - 1000 frontier partitions, each handling ~350K domains

Content Store Partitioning:
  - Partition by content hash (for dedup efficiency)
  - Or by URL hash (for retrieval efficiency)
  - Replicated 3x across data centers
```

---

## 10. Caching Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CACHING LAYERS                                │
│                                                                        │
│  Layer 1: CDN / Edge Cache                                             │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  - Cache static assets (CSS, JS, images for SERP UI)         │     │
│  │  - Geographic distribution for low latency                   │     │
│  │  - TTL: 1 hour for static, no caching for search results     │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  Layer 2: Query Result Cache                                           │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Key:    normalized_query + lang + region + page_number       │     │
│  │  Value:  serialized search results (top-K + snippets)         │     │
│  │  TTL:    5-60 minutes (shorter for news-related queries)      │     │
│  │                                                               │     │
│  │  Cache hit rate: ~30-40% (query distribution follows Zipf)    │     │
│  │  Size: ~50 TB distributed across query frontend servers       │     │
│  │  Eviction: LRU with frequency-based admission (TinyLFU)      │     │
│  │                                                               │     │
│  │  Impact: 30% cache hit = 30% fewer scatter-gather operations  │     │
│  │  = massive cost savings                                       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  Layer 3: Posting List Cache (per Index Server)                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Key:    term_id                                              │     │
│  │  Value:  decompressed posting list (or hot prefix of it)      │     │
│  │                                                               │     │
│  │  Hot terms like "the", "how", "what" are always cached        │     │
│  │  Top 1M terms cover ~80% of query traffic                    │     │
│  │  Size: ~500 GB per index server (in RAM)                     │     │
│  │  Eviction: LFU (frequency-based, terms don't change often)   │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  Layer 4: Document Metadata Cache                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Key:    doc_id                                               │     │
│  │  Value:  title, URL, snippet-ready text, PageRank score       │     │
│  │                                                               │     │
│  │  Cache top 100M most-accessed documents                       │     │
│  │  Size: ~1 TB (100M * 10KB per doc metadata)                   │     │
│  │  Used during result compilation and snippet generation        │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  Layer 5: DNS Cache (for Crawler)                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Key:    domain                                               │     │
│  │  Value:  IP address(es)                                       │     │
│  │  TTL:    follows DNS TTL (typically 5-60 minutes)             │     │
│  │  Size:   350M domains * 50 bytes = ~17 GB                    │     │
│  │  Avoids DNS lookup bottleneck during crawling                 │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  Cache Invalidation:                                                   │
│  - Query result cache: TTL-based (no explicit invalidation)            │
│  - Posting list cache: Refreshed when index shards are rebuilt         │
│  - Document cache: Invalidated on re-crawl                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Replication and Consistency

### 11.1 Index Replication

```
┌────────────────────────────────────────────────────────────────────────┐
│                       INDEX REPLICATION MODEL                         │
│                                                                        │
│  Consistency Model: Eventually Consistent (acceptable for search)      │
│                                                                        │
│  Index Rebuild Process:                                                │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  1. Index pipeline builds new index shards (batch, ~hours)     │   │
│  │  2. New shard replicas are copied to serving machines          │   │
│  │  3. Atomic swap: old shard -> new shard (via symlink or       │   │
│  │     load balancer reroute)                                    │   │
│  │  4. Old shard kept for rollback (24-hour retention)           │   │
│  │                                                               │   │
│  │  During swap, some replicas serve old index, some new:        │   │
│  │  User may see slightly different results for ~minutes.        │   │
│  │  This is acceptable for search.                               │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  Replication Topology:                                                 │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                                                                │   │
│  │  Data Center A          Data Center B         Data Center C    │   │
│  │  ┌──────────────┐       ┌──────────────┐      ┌────────────┐  │   │
│  │  │ Shard 0, R0  │       │ Shard 0, R1  │      │ Shard 0, R2│  │   │
│  │  │ Shard 1, R0  │       │ Shard 1, R1  │      │ Shard 1, R2│  │   │
│  │  │ ...          │       │ ...          │      │ ...        │  │   │
│  │  └──────────────┘       └──────────────┘      └────────────┘  │   │
│  │                                                                │   │
│  │  Each DC has a full copy of the index for local query serving  │   │
│  │  Cross-DC replication is async (index built centrally,         │   │
│  │  distributed to all DCs)                                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  No strong consistency needed because:                                 │
│  - Users don't notice minor ranking differences between DCs            │
│  - Index is rebuilt periodically (not real-time updated)                │
│  - Freshness is handled by a separate real-time index overlay          │
└────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Real-Time Index for Freshness

```
┌────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME INDEX OVERLAY                             │
│                                                                        │
│  Problem: The main index is rebuilt every few hours. Breaking news     │
│  needs to appear within minutes.                                       │
│                                                                        │
│  Solution: Small in-memory real-time index that is merged with         │
│  main index results at query time.                                     │
│                                                                        │
│  ┌──────────────────┐   ┌───────────────────┐                         │
│  │  Main Index      │   │  Real-Time Index   │                        │
│  │  (100B docs,     │   │  (~10M docs,       │                        │
│  │   rebuilt every   │   │   updated within   │                        │
│  │   few hours)     │   │   minutes)         │                        │
│  └────────┬─────────┘   └─────────┬─────────┘                         │
│           │                       │                                    │
│           └───────────┬───────────┘                                    │
│                       v                                                │
│              ┌─────────────────┐                                       │
│              │  Merge Results  │                                       │
│              │  (interleave by │                                       │
│              │   final score)  │                                       │
│              └─────────────────┘                                       │
│                                                                        │
│  Real-Time Index Properties:                                           │
│  - Size: ~10M recently crawled/updated pages                           │
│  - Storage: Entirely in-memory (small enough)                          │
│  - Update latency: < 5 minutes from crawl to searchable               │
│  - Merged into main index on next full rebuild                         │
│  - Covers: breaking news, trending topics, live events                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Fault Tolerance and Failure Handling

```
┌────────────────────────────────────────────────────────────────────────┐
│                    FAILURE SCENARIOS AND HANDLING                      │
│                                                                        │
│  ┌──────────────────┬──────────────────────────────────────────────┐  │
│  │  Failure Mode    │  Handling Strategy                           │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  Index server    │  - Route queries to replica of same shard   │  │
│  │  crash           │  - 3 replicas per shard: survives 2 failures│  │
│  │                  │  - Health checker detects within 10 seconds  │  │
│  │                  │  - Auto-restart on same or new machine       │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  Slow index      │  - Query coordinator sets 200ms deadline    │  │
│  │  shard response  │  - If shard misses deadline, use results    │  │
│  │                  │    from responded shards (partial results)   │  │
│  │                  │  - User sees slightly fewer results (ok)    │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  Crawler worker  │  - URLs in-progress are re-queued after     │  │
│  │  failure         │    timeout (5 minutes)                      │  │
│  │                  │  - Idempotent: re-crawling a URL is safe    │  │
│  │                  │  - Worker auto-replaced by orchestrator     │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  URL frontier    │  - Persistent backing store (not just       │  │
│  │  node failure    │    in-memory)                               │  │
│  │                  │  - Frontier partitioned; loss of one        │  │
│  │                  │    partition = temporary gap in crawling    │  │
│  │                  │  - Rebuild from checkpoint + re-discovery   │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  Data center     │  - DNS-based failover to next nearest DC   │  │
│  │  outage          │  - Each DC has full index replica           │  │
│  │                  │  - Users redirected within ~30 seconds      │  │
│  │                  │  - Capacity planning: each DC can handle   │  │
│  │                  │    1.5x normal load (N+1 redundancy)       │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  Index build     │  - Continue serving old index               │  │
│  │  pipeline fails  │  - Alert, retry build                       │  │
│  │                  │  - Stale index is better than no index      │  │
│  │                  │  - Canary: deploy new index to 1% of       │  │
│  │                  │    traffic first, check quality metrics     │  │
│  ├──────────────────┼──────────────────────────────────────────────┤  │
│  │  Query cache     │  - Cache is a performance optimization,    │  │
│  │  failure         │    not a correctness requirement            │  │
│  │                  │  - Cache miss -> query goes to index       │  │
│  │                  │  - Higher latency, but correct results     │  │
│  │                  │  - Auto-repopulate as queries flow in      │  │
│  └──────────────────┴──────────────────────────────────────────────┘  │
│                                                                        │
│  Graceful Degradation Priority:                                        │
│    1. Always return SOME results (even if partial)                      │
│    2. Prefer fast + slightly incomplete over slow + complete            │
│    3. Show cached results if live pipeline is degraded                  │
│    4. Disable expensive features first (knowledge panels, ML re-rank)  │
│    5. Last resort: static "service unavailable" with retry             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Scalability

### 13.1 Scaling Each Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                       SCALABILITY STRATEGIES                          │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  CRAWL PIPELINE SCALING                                        │   │
│  │                                                                │   │
│  │  Bottleneck: Network I/O and DNS resolution                    │   │
│  │                                                                │   │
│  │  Horizontal: Add more crawler workers                          │   │
│  │    - Each worker handles ~170K pages/day                       │   │
│  │    - 1B pages/day -> ~6,000 workers                            │   │
│  │    - 10B pages/day -> ~60,000 workers                          │   │
│  │                                                                │   │
│  │  Vertical: More concurrent connections per worker              │   │
│  │    - Async I/O (epoll/kqueue) for 1000s of connections         │   │
│  │    - Connection pooling per domain                             │   │
│  │                                                                │   │
│  │  DNS: Run local DNS caching resolvers                          │   │
│  │    - Pre-resolve domains before crawl                          │   │
│  │    - Cache 350M domain resolutions                             │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  INDEX PIPELINE SCALING                                        │   │
│  │                                                                │   │
│  │  Bottleneck: Sorting and merging posting lists                 │   │
│  │                                                                │   │
│  │  Horizontal: Partition MapReduce across thousands of workers   │   │
│  │    - Map: embarrassingly parallel (one doc = one map task)     │   │
│  │    - Shuffle: partition by term hash                           │   │
│  │    - Reduce: one reducer per index shard                       │   │
│  │                                                                │   │
│  │  Incremental: Don't rebuild full index every time              │   │
│  │    - Merge new/updated documents into existing index           │   │
│  │    - Full rebuild weekly; incremental updates every hour       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  QUERY PIPELINE SCALING                                        │   │
│  │                                                                │   │
│  │  Bottleneck: Fan-out to index shards, ML re-ranking            │   │
│  │                                                                │   │
│  │  Read Replicas: More replicas per shard = more query capacity  │   │
│  │    - 3 replicas -> 3x throughput per shard                     │   │
│  │    - During peak: spin up additional replicas                  │   │
│  │                                                                │   │
│  │  Caching: 30-40% cache hit rate offloads index servers         │   │
│  │                                                                │   │
│  │  Tiered Index: Only search Tier 1 for most queries             │   │
│  │    - 100 shards instead of 10,000 for 95% of queries           │   │
│  │                                                                │   │
│  │  Geographic: 20+ data centers, serve from nearest              │   │
│  │    - User in Tokyo -> Tokyo DC (RTT < 10ms)                    │   │
│  │    - User in Berlin -> Frankfurt DC (RTT < 20ms)               │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Scaling Numbers

```
Scale Milestones:

  1M pages indexed (startup search)
    - 1 index server, no sharding needed
    - Single-machine crawler
    - In-memory inverted index (~1 GB)

  1B pages (medium-scale, e.g., DuckDuckGo)
    - 100 index shards, 300 servers
    - 500 crawler workers
    - Index size: ~1 TB

  100B pages (Google-scale)
    - 10,000 index shards, 30,000 servers
    - 6,000+ crawler workers
    - Index size: ~80 TB (compressed)
    - 20+ data centers globally
    - 115K QPS sustained

  Growth Handling:
    - Web grows ~10% per year
    - Add index shards proportionally
    - Re-partition annually or when shards exceed target size
    - Linear cost scaling: 2x pages = ~2x infrastructure
```

---

## 14. Monitoring and Observability

```
┌────────────────────────────────────────────────────────────────────────┐
│                    MONITORING DASHBOARD                                │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  QUERY SERVING METRICS                                           │ │
│  │                                                                  │ │
│  │  Latency:                                                        │ │
│  │    p50:  180ms  [============================            ] target: 200ms │
│  │    p95:  350ms  [=====================================   ] target: 400ms │
│  │    p99:  480ms  [========================================] target: 500ms │
│  │                                                                  │ │
│  │  Throughput:                                                      │ │
│  │    Current QPS:      125,000                                      │ │
│  │    Peak (24h):       340,000                                      │ │
│  │    Capacity:         500,000                                      │ │
│  │                                                                  │ │
│  │  Cache:                                                          │ │
│  │    Query cache hit rate:    35.2%                                 │ │
│  │    Posting list cache hit:  78.4%                                 │ │
│  │    Doc metadata cache hit:  91.3%                                 │ │
│  │                                                                  │ │
│  │  Errors:                                                         │ │
│  │    5xx rate:     0.001%                                          │ │
│  │    Timeout rate: 0.05%                                           │ │
│  │    Empty results: 2.3% (expected for nonsense queries)           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  CRAWL PIPELINE METRICS                                          │ │
│  │                                                                  │ │
│  │  Crawl rate:         1.02 billion pages/day                      │ │
│  │  Active workers:     5,847 / 6,000                               │ │
│  │  DNS resolution p99: 15ms                                        │ │
│  │  Fetch success rate: 94.2%                                       │ │
│  │  robots.txt blocks:  8.1%                                        │ │
│  │  Duplicate rate:     23.4%                                       │ │
│  │  JS render queue:    142K pages pending                          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  INDEX HEALTH METRICS                                            │ │
│  │                                                                  │ │
│  │  Index freshness:                                                │ │
│  │    Median document age:    3.2 days                              │ │
│  │    News document age:      47 minutes                            │ │
│  │    Real-time index size:   8.7M documents                        │ │
│  │                                                                  │ │
│  │  Index size:               82.4 TB (compressed)                  │ │
│  │  Total documents:          101.2 billion                         │ │
│  │  Unique terms:             9.8 billion                           │ │
│  │  Last full rebuild:        6 hours ago                           │ │
│  │  Shard health:             9,997 / 10,000 healthy                │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  QUALITY METRICS                                                 │ │
│  │                                                                  │ │
│  │  Click-through rate (CTR) on result #1:  31.2%                   │ │
│  │  Mean Reciprocal Rank (MRR):             0.68                    │ │
│  │  NDCG@10:                                0.74                    │ │
│  │  Query abandonment rate:                 12.1%                   │ │
│  │  Spell correction trigger rate:          8.3%                    │ │
│  │  Autocomplete acceptance rate:           42.7%                   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Alerting Thresholds:                                                  │
│    CRITICAL: p99 latency > 1s, error rate > 0.1%, shard down > 5      │
│    WARNING:  p99 latency > 500ms, cache hit < 25%, crawl rate < 800M  │
│    INFO:     Index rebuild started/completed, new shard deployed       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Key Design Decisions

```
┌────────────────────────┬──────────────────────┬──────────────────────┐
│  Decision              │  Option A (Chosen)   │  Option B            │
├────────────────────────┼──────────────────────┼──────────────────────┤
│  Index Partitioning    │  Document-partitioned │  Term-partitioned    │
│                        │  + Uniform load       │  + Lower fan-out for │
│                        │  + Easy doc updates   │    single-term query │
│                        │  - High fan-out       │  - Hot term shards   │
│                        │                      │  - Cross-shard joins │
├────────────────────────┼──────────────────────┼──────────────────────┤
│  First-Pass Ranking    │  BM25                │  TF-IDF              │
│                        │  + TF saturation      │  + Simpler            │
│                        │  + Length norm         │  - No saturation     │
│                        │  + Proven at scale    │  - Length bias        │
├────────────────────────┼──────────────────────┼──────────────────────┤
│  Re-Ranking Model      │  LambdaMART / GBDT   │  Deep Neural Net     │
│                        │  + Fast inference     │  + Better accuracy   │
│                        │  + Interpretable      │  - Slower inference  │
│                        │  - Feature engineering│  - Black box         │
│                        │  (Trend: DNNs winning)│  + End-to-end        │
├────────────────────────┼──────────────────────┼──────────────────────┤
│  Crawl Strategy        │  BFS with priority   │  DFS                 │
│                        │  + Broad coverage     │  + Deep site coverage│
│                        │  + Finds important    │  - Misses breadth    │
│                        │    pages first        │  - Can get trapped   │
├────────────────────────┼──────────────────────┼──────────────────────┤
│  Index Update          │  Periodic rebuild +   │  Real-time indexing  │
│                        │  real-time overlay    │  (fully incremental) │
│                        │  + Simpler, cheaper   │  + Always fresh      │
│                        │  + Optimized layout   │  - Complex           │
│                        │  - Slight staleness   │  - Index fragmentation│
├────────────────────────┼──────────────────────┼──────────────────────┤
│  Content Store         │  Distributed FS      │  Object Store (S3)   │
│                        │  + Low latency reads  │  + Cheaper storage   │
│                        │  + High throughput    │  + Simpler ops       │
│                        │  - Operational cost   │  - Higher latency    │
├────────────────────────┼──────────────────────┼──────────────────────┤
│  Posting Compression   │  PForDelta            │  VByte               │
│                        │  + Better compression │  + Simpler code      │
│                        │  + SIMD-friendly      │  + Decent compression│
│                        │  - More complex       │  - Slower for dense  │
│                        │  - Block-based        │    posting lists     │
└────────────────────────┴──────────────────────┴──────────────────────┘
```

### 15.2 Freshness vs Completeness Trade-off

```
The fundamental tension: we cannot crawl 100B pages in real-time.

Solution: Priority-based crawl scheduling

  ┌──────────────────────────────────────────────────────────────┐
  │  Page Category         │  Re-crawl Interval  │  % of Crawl  │
  ├────────────────────────┼─────────────────────┼──────────────┤
  │  Breaking news sites   │  Every 5-15 minutes │     5%       │
  │  Major news portals    │  Every 1-2 hours    │    10%       │
  │  Popular sites (top 1M)│  Every 1-3 days     │    25%       │
  │  Regular content       │  Every 1-4 weeks    │    40%       │
  │  Long-tail / archive   │  Every 1-6 months   │    20%       │
  └────────────────────────┴─────────────────────┴──────────────┘

  Adaptive re-crawl: Track how often a page changes.
    If change_rate is high -> increase crawl frequency
    If page hasn't changed in 3 crawls -> decrease frequency
```

### 15.3 Relevance vs Speed Trade-off

```
More accurate ranking requires more computation:

  Fast path (~50ms):
    BM25 only, Tier 1 index, top-100 results
    Quality: Good for popular queries

  Standard path (~200ms):
    BM25 + ML re-ranking, Tier 1+2, top-1000 candidates
    Quality: Good for most queries

  Deep path (~500ms):
    BM25 + ML re-ranking, all tiers, query expansion
    Quality: Best, for rare/ambiguous queries

  Decision: Route based on query characteristics
    - Common queries (seen before) -> fast path + cache
    - Normal queries -> standard path
    - Rare / long queries -> deep path
```

---

## 16. Interview Deep-Dive Questions

### Q1: How does PageRank work and how do you compute it at scale?

**Answer:** PageRank models a "random surfer" who follows links randomly. The
probability of the surfer landing on a page is its PageRank. The formula is
iterative: PR(A) = (1-d)/N + d * SUM(PR(B)/L(B)) for all pages B linking to A,
where d=0.85 is the damping factor.

At scale (100B pages), we use MapReduce. Each mapper reads a page and its
outlinks, distributing the page's PageRank equally among its outlinks. Each
reducer sums contributions for a target page and applies the damping formula.
This requires ~50-100 iterations to converge, with each iteration processing
~3 TB of data. On 10K machines, one iteration takes ~30 minutes, so full
computation takes ~25 hours. We recompute weekly and store results in the
document metadata.

Dead ends (pages with no outlinks) are handled by redistributing their PageRank
mass equally across all pages. Spider traps are handled by the damping factor,
which ensures 15% probability of jumping to a random page.

---

### Q2: How do you handle duplicate or near-duplicate content?

**Answer:** We use a multi-layered approach:

1. **URL-level dedup:** Normalize URLs (lowercase, remove fragments, sort
   parameters) and check against a Bloom filter (50B entries, 0.01% FPR, ~60
   GB memory).

2. **Content-level exact dedup:** Compute a hash (e.g., MD5 or SHA-256) of the
   extracted text. Store hashes in a lookup table. Identical hashes = duplicate.

3. **Near-duplicate detection (SimHash):** Compute a 64-bit SimHash fingerprint.
   Two documents with Hamming distance <= 3 are near-duplicates. This catches
   pages that differ only in headers/footers/ads.

4. **Canonical URL resolution:** Respect the `<link rel="canonical">` tag,
   which tells us the preferred URL for duplicate content.

When duplicates are found, we keep only the canonical (highest PageRank) version
in the index and merge link signals from all copies.

---

### Q3: How do you keep the index fresh?

**Answer:** We use a two-tier approach:

1. **Main index:** Rebuilt every few hours via batch MapReduce pipeline. Contains
   100B documents. Optimized for query performance (sorted, compressed, skip
   pointers).

2. **Real-time index overlay:** A small in-memory index (~10M documents) that
   is updated within minutes of crawl. When a query is processed, results from
   both indexes are merged by the query coordinator.

The crawler uses adaptive scheduling: pages that change frequently (detected via
HTTP Last-Modified or content hash comparison) are crawled more often. News sites
are crawled every 5-15 minutes, while static content may only be crawled monthly.

We also support push-based indexing via sitemaps (sitemap.xml) and the
IndexNow protocol, where publishers notify us of changes.

---

### Q4: How do you handle multi-word queries and phrase matching?

**Answer:** Multi-word queries require intersecting posting lists:

1. **AND semantics:** For "distributed consensus", fetch posting lists for both
   terms and intersect them (documents containing both). We use skip pointers
   for efficient intersection of sorted posting lists.

2. **Phrase matching:** For "distributed consensus" in quotes, we need the terms
   to appear adjacent. We store term positions in the posting list. After
   intersecting doc_ids, we check if position(consensus) = position(distributed) + 1.

3. **Proximity scoring:** Even without quotes, terms appearing closer together
   in a document score higher. The position data enables this.

4. **Optimization:** We process the rarest term first (smallest posting list)
   to minimize the number of documents we need to check for the other terms.

---

### Q5: How do you prevent search result manipulation (SEO spam)?

**Answer:** Multiple defensive layers:

1. **Link spam detection:** Detect link farms (clusters of low-quality sites
   linking to each other). Use graph analysis to identify unnatural link
   patterns. Discount links from known spam domains.

2. **Content quality signals:** ML models trained on human-rated examples to
   score content quality. Features include: text-to-HTML ratio, keyword stuffing
   density, grammar quality, E-E-A-T signals (experience, expertise,
   authoritativeness, trustworthiness).

3. **Cloaking detection:** Crawl pages from different IPs and User-Agents. If
   the content served to the crawler differs from what users see, penalize the
   page.

4. **Click signal analysis:** If users consistently bounce back quickly from a
   result (pogo-sticking), it's a signal of low quality. Incorporate dwell time
   and click-through patterns into ranking.

5. **Manual actions:** A team of quality raters reviews flagged sites. Severe
   spam gets manually demoted or removed from the index.

---

### Q6: How do you scale the scatter-gather query architecture?

**Answer:** Key strategies:

1. **Tiered index:** Only search the top-tier (1B most important pages = 100
   shards) for most queries. This reduces fan-out from 10,000 to 100 shards.
   95% of queries are satisfied by Tier 1 alone.

2. **Replication:** Each shard has 3+ replicas. Query coordinator randomly picks
   a replica, distributing load. During peak, temporarily add more replicas.

3. **Caching:** 30-40% of queries are cache hits, completely bypassing the
   scatter-gather. Posting list caching on index servers reduces SSD reads.

4. **Deadline propagation:** Each query has a 200ms deadline. If a shard is
   slow, its results are excluded. The coordinator returns results from the
   shards that responded in time.

5. **Request hedging:** For tail latency, send the same request to 2 replicas
   and use whichever responds first. This converts p99 latency to roughly p99^2.

---

### Q7: How would you design the autocomplete system?

**Answer:** The autocomplete system needs < 50ms latency (feels instant).

**Data:** Aggregate query logs to find the most popular queries and their
frequencies. Update every few hours.

**Data structure:** Build a trie where each node stores the top-8 completions
by popularity. Size: ~10 GB, fits entirely in memory.

**Lookup:** User types "how to des" -> traverse trie to "how_to_des" node ->
return pre-computed top-8 completions.

**Personalization:** Boost suggestions from user's recent search history (stored
in session/cookie). Mix personal suggestions with global popular ones.

**Freshness:** For trending topics, merge a small "trending trie" (updated every
15 minutes from real-time query stream) with the main trie.

**Sharding:** Shard by first 2 characters of query prefix. "ho*" queries go to
one server, "di*" to another. Each shard is replicated.

---

### Q8: How do you handle different languages and internationalization?

**Answer:** Each language requires its own processing pipeline:

1. **Language detection:** Classify document language using n-gram models (e.g.,
   CLD2). Multi-language pages are indexed under the primary language.

2. **Language-specific tokenization:** Chinese/Japanese need word segmentation
   (no spaces). Arabic/Hebrew are right-to-left. German has compound words that
   need decompounding.

3. **Language-specific stemming:** English uses Porter stemmer, other languages
   use language-specific stemmers (e.g., Snowball stemmers).

4. **Index per language:** Maintain separate index shards per language or language
   group. Query routing uses the user's language preference.

5. **Cross-language search:** Optionally translate queries or use multilingual
   embeddings to find results in other languages.

---

### Q9: What is the role of the link graph in ranking?

**Answer:** The link graph serves multiple purposes beyond PageRank:

1. **PageRank:** Global authority score based on incoming link count and quality.
2. **Anchor text:** The text of links pointing to a page describes what the page
   is about. "Click here for Raft paper" tells us the target is about Raft.
3. **Domain authority:** Aggregate PageRank of all pages on a domain.
4. **Spam detection:** Unnatural link patterns indicate manipulation.
5. **Topic-sensitive PageRank:** Compute PageRank biased toward specific topic
   categories, giving different authority scores for different query intents.

The link graph is stored as an adjacency list (source -> [targets]) and reversed
adjacency list (target -> [sources]). Total size: ~2 TB for 100B pages with
~20 average outlinks each.

---

### Q10: How do you handle query intent classification?

**Answer:** Queries are classified into three main intents:

1. **Navigational:** User wants a specific site. E.g., "facebook login" ->
   return facebook.com as top result. Detected by brand name matching and
   high click-through on a single result.

2. **Informational:** User wants to learn something. E.g., "how does TCP work"
   -> return educational articles, knowledge panels. Most common type (~60%).

3. **Transactional:** User wants to do something. E.g., "buy laptop" -> return
   shopping results, product listings.

Classification uses an ML model (gradient-boosted trees or neural network)
trained on labeled query-intent pairs. Features include: query length, presence
of action verbs, entity detection, and historical click patterns.

Intent affects ranking: navigational queries boost the target domain,
informational queries boost authoritative educational content, and transactional
queries boost product pages with high ratings.

---

### Q11: How do you build knowledge panels?

**Answer:** Knowledge panels display structured information for entity queries
(e.g., "Albert Einstein", "Python programming language").

1. **Entity recognition:** Identify if the query matches a known entity in a
   knowledge base (e.g., Wikidata, Freebase). Use entity linking to
   disambiguate (e.g., "Python" -> programming language vs. snake).

2. **Structured data:** Extract facts from the knowledge base (birth date,
   occupation, related entities). Also ingest schema.org structured data from
   web pages.

3. **Panel assembly:** Template-based rendering: person template shows photo,
   birth date, occupation; company template shows CEO, stock price, headquarters.

4. **Freshness:** Some facts (stock price, weather) need real-time feeds.
   Others (birth date) are static and cached.

---

### Q12: How do you handle image and video search?

**Answer:** Multimedia search adds two main subsystems:

1. **Image indexing:** Extract images from crawled pages. Index by: surrounding
   text, alt text, filename, page title. Also compute visual features using CNNs
   (ResNet/CLIP) for visual similarity search. Store thumbnails in a CDN.

2. **Video indexing:** Crawl video platforms (YouTube, Vimeo). Index by: title,
   description, captions/transcripts (ASR-generated), tags. Extract key frames
   for visual matching.

3. **Blended results:** For queries with multimedia intent (e.g., "cat photos"),
   the result compiler inserts image/video carousels into web search results.

4. **Reverse image search:** Given an image, find visually similar images. Uses
   perceptual hashing (pHash) for exact matches and deep embeddings (CLIP) for
   semantic similarity. Index embeddings in an approximate nearest neighbor (ANN)
   structure like HNSW or ScaNN.

---

### Q13: What is the index serving data path for a single query?

**Answer:** Detailed timing breakdown for a query "distributed consensus":

```
Time (ms)  Action
────────────────────────────────────────────────────────
  0        User sends query
  5        DNS + TCP + TLS to nearest DC
 10        Load balancer routes to query frontend
 15        Query parser: tokenize, stem, spell-check
 20        Check query result cache -> MISS
 25        Scatter: send to 100 Tier-1 index shards
 30-80     Each shard: lookup posting lists, intersect, compute BM25
           Return local top-100 to coordinator
 85        Gather: merge 100 * 100 = 10K candidates -> global top-1000
 90-140    ML re-ranker scores top-1000 candidates
145        Select top-10 for page 1
150-170    Parallel: fetch doc metadata + generate snippets
175        Build knowledge panel (if entity detected)
180        Assemble final response JSON
185        Send response to user
190        User receives results
```

Total: ~190ms end-to-end (well within 200ms p50 target).

---

### Q14: How do you handle index compaction and garbage collection?

**Answer:** Over time, the index accumulates deleted/updated documents that
waste space and slow queries.

1. **Tombstones:** When a document is removed or updated, mark the old doc_id
   as deleted (bitmap of deleted doc_ids per shard). During query processing,
   filter out deleted doc_ids from results.

2. **Periodic compaction:** During full index rebuild (every few hours), deleted
   documents are physically removed. Posting lists are re-sorted and
   re-compressed without gaps.

3. **Segment merging:** Similar to Lucene's merge policy. Small index segments
   (from recent updates) are periodically merged into larger segments for
   better query performance (fewer segments to search).

4. **Cost:** Compaction is done during off-peak hours and uses separate I/O
   bandwidth from query serving to avoid latency impact.

---

### Q15: How would you design the system differently for a vertical search engine (e.g., e-commerce)?

**Answer:** Key differences for e-commerce search (like Amazon's A9):

1. **Structured data:** Products have structured attributes (price, brand,
   category, ratings). Use faceted search (filter by price range, brand, etc.)
   in addition to full-text search.

2. **Ranking signals:** Replace PageRank with conversion rate, sales velocity,
   seller reputation, profit margin. Freshness matters less; availability
   and pricing matter more.

3. **Real-time inventory:** Unlike web search, product availability changes in
   real-time. The index must support near-real-time updates (seconds, not hours).

4. **Smaller scale:** Millions of products (not billions of pages). Single-tier
   index fits on fewer machines. Can afford more expensive per-document
   processing.

5. **Personalization:** E-commerce search is heavily personalized. User purchase
   history, browsing behavior, and demographic features significantly affect
   ranking. Web search is less personalized.

6. **Merchandising:** Business rules override pure relevance ranking (e.g.,
   boost sponsored products, new arrivals, clearance items). Web search tries
   to avoid this.

---

## 17. Summary: Key Takeaways for Interviews

```
┌────────────────────────────────────────────────────────────────────────┐
│                       INTERVIEW CHEAT SHEET                           │
│                                                                        │
│  Three Pipelines:                                                      │
│    1. Crawl:  URL Frontier -> Crawlers -> Content Store                │
│    2. Index:  Content -> Parse -> Tokenize -> Inverted Index           │
│    3. Query:  Parse -> Scatter-Gather -> Rank -> Compile Results       │
│                                                                        │
│  Key Numbers:                                                          │
│    - 100B pages, 10B unique terms, 80 TB compressed index              │
│    - 115K QPS, < 200ms p50, < 500ms p99                                │
│    - 10,000 index shards, 30,000 index servers                         │
│    - 1B pages crawled per day, 6,000 crawler workers                   │
│                                                                        │
│  Core Data Structures:                                                 │
│    - Inverted index with posting lists (delta-encoded, compressed)     │
│    - Trie for autocomplete                                             │
│    - Bloom filter for URL dedup                                        │
│    - SimHash for content dedup                                         │
│    - Priority queue for URL frontier                                   │
│                                                                        │
│  Key Algorithms:                                                       │
│    - BM25 for first-pass ranking                                       │
│    - PageRank for authority scoring                                     │
│    - LambdaMART/DNN for re-ranking                                     │
│    - MapReduce for index construction and PageRank computation         │
│                                                                        │
│  Architecture Patterns:                                                │
│    - Document-partitioned index (not term-partitioned)                 │
│    - Scatter-gather query execution                                    │
│    - Tiered index (hot/warm/cold)                                      │
│    - Real-time index overlay for freshness                             │
│    - Two-phase ranking (fast retrieval + ML re-ranking)                │
│                                                                        │
│  Stand-Out Points for Senior Engineers:                                │
│    - Discuss index compression trade-offs (VByte vs PForDelta)         │
│    - Explain BM25 formula and why it beats TF-IDF                      │
│    - Describe tiered index optimization (95% queries on Tier 1)        │
│    - Mention request hedging for tail latency                          │
│    - Discuss freshness vs completeness trade-off                       │
│    - Explain how real-time overlay index enables news search           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## References and Further Reading

- Brin, S. & Page, L. (1998). "The Anatomy of a Large-Scale Hypertextual Web Search Engine" (original Google paper)
- Robertson, S. & Zaragoza, H. (2009). "The Probabilistic Relevance Framework: BM25 and Beyond"
- Dean, J. & Ghemawat, S. (2004). "MapReduce: Simplified Data Processing on Large Clusters"
- Ghemawat, S. et al. (2003). "The Google File System"
- Chang, F. et al. (2006). "Bigtable: A Distributed Storage System for Structured Data"
- Manning, C. et al. (2008). "Introduction to Information Retrieval" (Stanford NLP textbook)
- Zobel, J. & Moffat, A. (2006). "Inverted Files for Text Search Engines" (ACM Computing Surveys)
- Barroso, L. et al. (2013). "The Datacenter as a Computer" (warehouse-scale computing)
