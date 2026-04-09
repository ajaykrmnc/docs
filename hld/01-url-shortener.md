# Design a URL Shortener (TinyURL / Bitly)

**Difficulty:** Medium-Hard | **Companies:** Google, Amazon, Microsoft, Meta, Uber

## Table of Contents
1. [Problem Statement and Scope](#1-problem-statement-and-scope)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Back-of-Envelope Estimation](#4-back-of-envelope-estimation)
5. [API Design](#5-api-design)
6. [Data Model and Database Selection](#6-data-model-and-database-selection)
7. [High-Level Architecture](#7-high-level-architecture)
8. [Deep Dive: Core Components](#8-deep-dive-core-components)
9. [Data Partitioning and Sharding](#9-data-partitioning-and-sharding)
10. [Caching Strategy](#10-caching-strategy)
11. [Replication and Consistency](#11-replication-and-consistency)
12. [Fault Tolerance and Failure Handling](#12-fault-tolerance-and-failure-handling)
13. [Scalability](#13-scalability)
14. [Monitoring and Observability](#14-monitoring-and-observability)
15. [Trade-offs and Design Decisions](#15-trade-offs-and-design-decisions)
16. [Interview Deep-Dive Questions](#16-interview-deep-dive-questions)

---

## 1. Problem Statement and Scope

### Problem Statement

Design a URL shortening service similar to TinyURL or Bitly that takes a long URL (e.g.,
`https://www.example.com/articles/2024/distributed-systems/cap-theorem?ref=newsletter&utm_source=twitter`)
and converts it to a short, unique alias (e.g., `https://short.ly/aB3x7Kq`) that redirects
to the original URL when accessed.

### Why is This Problem Important?

1. **Shareability**: Long URLs are unwieldy in tweets, text messages, and print media.
2. **Analytics**: Shortened links enable click tracking, geographic analysis, and A/B testing.
3. **Branding**: Custom short domains (e.g., `amzn.to`, `goo.gl`) reinforce brand identity.
4. **Link management**: Centralized control over redirects allows updating destination URLs without changing the shared link.

### Scope Definition

```
┌──────────────────────────────────────────────────────────────────────┐
│                         IN SCOPE                                     │
├──────────────────────────────────────────────────────────────────────┤
│  - Shorten a given URL to a unique short alias                       │
│  - Redirect short URL to the original long URL                       │
│  - Custom short aliases (user-chosen slugs)                          │
│  - Link expiration (TTL-based)                                       │
│  - Basic analytics (click count, referrer, geo)                      │
│  - Rate limiting to prevent abuse                                    │
│  - API-based access (RESTful)                                        │
├──────────────────────────────────────────────────────────────────────┤
│                        OUT OF SCOPE                                  │
├──────────────────────────────────────────────────────────────────────┤
│  - Full user management / OAuth / social login                       │
│  - Payment and subscription tiers                                    │
│  - Link-in-bio pages or landing page builders                        │
│  - QR code generation (mention as extension)                         │
│  - Deep link handling for mobile apps                                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Functional Requirements

| #  | Requirement                    | Description                                                                                          |
|----|--------------------------------|------------------------------------------------------------------------------------------------------|
| F1 | **Shorten URL**                | Given a long URL, generate a unique short URL (7-character key by default).                          |
| F2 | **Redirect**                   | When a user visits the short URL, redirect them (HTTP 301/302) to the original long URL.             |
| F3 | **Custom Aliases**             | Allow users to optionally specify a custom short key (e.g., `short.ly/my-brand`).                   |
| F4 | **Link Expiration**            | Support optional expiration time (TTL). Default lifetime: 5 years. Expired links return HTTP 410.    |
| F5 | **Link Deletion**              | Authenticated users can delete their own shortened URLs.                                             |
| F6 | **Analytics**                  | Track click count, timestamp, referrer, user-agent, geographic location per short URL.               |
| F7 | **Duplicate Detection**        | If the same long URL is submitted by the same user, return the existing short URL instead of creating a new one. |
| F8 | **Rate Limiting**              | Limit URL creation to prevent spam (e.g., 100 URLs/hour per API key, 1000 redirects/sec per IP).    |
| F9 | **API Key Authentication**     | All write operations require a valid API key. Read (redirect) is public.                             |
| F10| **Preview Mode**               | Appending `+` to a short URL (e.g., `short.ly/aB3x7Kq+`) shows a preview page instead of redirecting.|

---

## 3. Non-Functional Requirements

| Requirement         | Target                          | Rationale                                                                |
|---------------------|---------------------------------|--------------------------------------------------------------------------|
| **Latency**         | p50 < 5ms, p99 < 50ms redirect | Redirect must feel instant; any delay loses users.                       |
| **Throughput**       | 50K reads/sec, 500 writes/sec   | Read-heavy workload (100:1 read-to-write ratio).                        |
| **Availability**     | 99.99% (52 min downtime/year)  | Revenue-generating links must always resolve; use multi-region.          |
| **Consistency**      | Eventual consistency (reads)   | A newly created short URL may take ~1-2s to propagate to all replicas.   |
| **Durability**       | 99.999999999% (11 nines)       | Once a URL is stored, it must not be lost. Replicate across AZs/regions. |
| **Scalability**      | 100B+ URLs over 5 years        | Must handle internet-scale growth without re-architecture.               |
| **Security**         | No enumeration attacks         | Short keys must not be sequential/predictable.                           |

### Consistency vs. Availability Trade-off

For a URL shortener, **availability is more critical** than strong consistency. If a user
creates a short URL and it takes 1-2 seconds to propagate, that is acceptable. However, if
the redirect service is down, every shared link on the internet pointing to our service is
broken. This places us firmly in the **AP** side of the CAP theorem during network partitions.

---

## 4. Back-of-Envelope Estimation

### 4.1 Traffic Estimation

```
┌────────────────────────────────────────────────────────────────────┐
│                    TRAFFIC ASSUMPTIONS                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Daily Active Users (DAU):        10 million                       │
│  Monthly Active Users (MAU):      100 million                      │
│                                                                    │
│  URL shortenings per day:         100 million (10 per DAU avg)     │
│  But most users only read:        ~1M writes/day, 100M reads/day  │
│                                                                    │
│  Read:Write ratio:                100 : 1                          │
│                                                                    │
│  ┌─────────────── WRITE PATH ───────────────┐                      │
│  │ New URLs per day:    1,000,000            │                      │
│  │ Write QPS:           1M / 86400 ≈ 12 QPS  │                      │
│  │ Peak write QPS:      12 × 5 = ~60 QPS     │                      │
│  └───────────────────────────────────────────┘                      │
│                                                                    │
│  ┌─────────────── READ PATH ────────────────┐                      │
│  │ Redirects per day:   100,000,000          │                      │
│  │ Read QPS:            100M / 86400 ≈ 1200  │                      │
│  │ Peak read QPS:       1200 × 5 = ~6000     │                      │
│  └───────────────────────────────────────────┘                      │
│                                                                    │
│  (Bitly processes ~600M clicks/month ≈ 230 QPS average)           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Storage Estimation

```
┌────────────────────────────────────────────────────────────────────┐
│                    STORAGE ESTIMATION                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Per URL record:                                                   │
│  ┌──────────────────────────────────────────────┐                  │
│  │  short_key (7 chars)          :     7 bytes  │                  │
│  │  original_url (avg 200 chars) :   200 bytes  │                  │
│  │  user_id (UUID)               :    16 bytes  │                  │
│  │  created_at (timestamp)       :     8 bytes  │                  │
│  │  expires_at (timestamp)       :     8 bytes  │                  │
│  │  click_count (counter)        :     8 bytes  │                  │
│  │  metadata (JSON blob avg)     :   ~250 bytes │                  │
│  │  ─────────────────────────────────────────── │                  │
│  │  Total per record             :  ~500 bytes  │                  │
│  └──────────────────────────────────────────────┘                  │
│                                                                    │
│  New URLs per month:     1M/day × 30 = 30 million                  │
│  New URLs per year:      30M × 12 = 360 million                    │
│  Over 5 years:           360M × 5 = 1.8 billion URLs               │
│                                                                    │
│  Storage for URLs:       1.8B × 500 bytes = 900 GB ≈ ~1 TB        │
│  With replication (×3):  ~3 TB                                     │
│  With analytics data:    ~10-15 TB (click events are voluminous)   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Key insight**: 1 TB of URL data is modest. Even a single modern server with NVMe SSDs
can hold this. The challenge is not raw storage but **read throughput** and **latency at
the tail** (p99).

### 4.3 Bandwidth Estimation

```
┌────────────────────────────────────────────────────────────────────┐
│                   BANDWIDTH ESTIMATION                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Incoming (write):                                                 │
│    12 QPS × 500 bytes = 6 KB/s                                     │
│    (Negligible)                                                    │
│                                                                    │
│  Outgoing (read/redirect):                                         │
│    1200 QPS × 500 bytes = 600 KB/s ≈ ~5 Mbps                      │
│    (Redirect responses are just HTTP headers, ~200 bytes each)     │
│    Actual: 1200 × 200 bytes = 240 KB/s ≈ ~2 Mbps                  │
│                                                                    │
│  Peak outgoing:                                                    │
│    6000 QPS × 200 bytes = 1.2 MB/s ≈ ~10 Mbps                     │
│                                                                    │
│  Verdict: Bandwidth is NOT a bottleneck for this system.           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 4.4 Cache/Memory Estimation

```
┌────────────────────────────────────────────────────────────────────┐
│                     CACHE ESTIMATION                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Applying the 80-20 rule:                                          │
│    20% of URLs generate 80% of traffic.                            │
│                                                                    │
│  Total URLs to cache (hot set):                                    │
│    Daily unique URLs accessed: ~20M                                │
│    Hot 20%: 20M × 0.2 = 4 million URLs                            │
│                                                                    │
│  Memory needed:                                                    │
│    4M × 500 bytes = 2 GB                                           │
│                                                                    │
│  With overhead (hash table, pointers, metadata):                   │
│    ~4-5 GB per cache node                                          │
│                                                                    │
│  Recommendation:                                                   │
│    A single Redis instance (64 GB) can hold the entire hot set     │
│    with room to spare. Use 2-3 Redis replicas for HA.              │
│                                                                    │
│  Expected cache hit ratio: 85-95%                                  │
│  (Viral/popular URLs dominate traffic)                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 5. API Design

### RESTful API Endpoints

#### 5.1 Create Short URL

```
POST /api/v1/urls
Headers:
  Authorization: Bearer <api_key>
  Content-Type: application/json

Request Body:
{
  "long_url": "https://www.example.com/very/long/path?with=params",
  "custom_alias": "my-link",         // optional
  "expires_at": "2027-01-01T00:00:00Z", // optional, default 5 years
  "metadata": {                       // optional
    "campaign": "spring-sale",
    "source": "email"
  }
}

Response: 201 Created
{
  "short_url": "https://short.ly/my-link",
  "short_key": "my-link",
  "long_url": "https://www.example.com/very/long/path?with=params",
  "created_at": "2026-04-09T10:30:00Z",
  "expires_at": "2027-01-01T00:00:00Z",
  "user_id": "usr_abc123"
}

Error Responses:
  400 - Invalid URL format or custom alias contains invalid characters
  409 - Custom alias already taken
  429 - Rate limit exceeded
```

#### 5.2 Redirect (Get Original URL)

```
GET /{short_key}

Response: 301 Moved Permanently (or 302 Found)
  Location: https://www.example.com/very/long/path?with=params
  Cache-Control: private, max-age=3600

Error Responses:
  404 - Short URL not found
  410 - Short URL has expired
```

#### 5.3 Delete Short URL

```
DELETE /api/v1/urls/{short_key}
Headers:
  Authorization: Bearer <api_key>

Response: 204 No Content

Error Responses:
  401 - Unauthorized
  403 - Forbidden (not the owner)
  404 - Short URL not found
```

#### 5.4 Get Analytics

```
GET /api/v1/urls/{short_key}/analytics
Headers:
  Authorization: Bearer <api_key>

Query Parameters:
  ?from=2026-01-01&to=2026-04-01
  &granularity=day   // hour, day, week, month
  &group_by=country  // country, referrer, device, browser

Response: 200 OK
{
  "short_key": "aB3x7Kq",
  "total_clicks": 142857,
  "unique_visitors": 98234,
  "time_series": [
    { "date": "2026-04-01", "clicks": 1523, "unique": 1102 },
    { "date": "2026-04-02", "clicks": 1687, "unique": 1230 },
    ...
  ],
  "top_referrers": [
    { "referrer": "twitter.com", "clicks": 45023 },
    { "referrer": "facebook.com", "clicks": 32100 },
    ...
  ],
  "top_countries": [
    { "country": "US", "clicks": 62000 },
    { "country": "IN", "clicks": 28000 },
    ...
  ],
  "devices": {
    "mobile": 85000,
    "desktop": 52000,
    "tablet": 5857
  }
}
```

#### 5.5 Bulk Create (Batch API)

```
POST /api/v1/urls/batch
Headers:
  Authorization: Bearer <api_key>
  Content-Type: application/json

Request Body:
{
  "urls": [
    { "long_url": "https://example.com/page1" },
    { "long_url": "https://example.com/page2", "custom_alias": "pg2" },
    ...
  ]
}

Response: 200 OK (partial success possible)
{
  "results": [
    { "status": "created", "short_url": "https://short.ly/xK9mP2q", ... },
    { "status": "conflict", "error": "Alias 'pg2' already exists" },
    ...
  ]
}
```

### API Design Considerations

```
┌────────────────────────────────────────────────────────────────────┐
│                   API DESIGN PRINCIPLES                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Idempotency: POST with same long_url + user returns existing   │
│     short URL rather than creating a duplicate.                    │
│                                                                    │
│  2. Rate Limiting Headers:                                         │
│     X-RateLimit-Limit: 100                                         │
│     X-RateLimit-Remaining: 73                                      │
│     X-RateLimit-Reset: 1617235200                                  │
│                                                                    │
│  3. Versioning: /api/v1/ prefix for backward compatibility.        │
│                                                                    │
│  4. Pagination: Analytics endpoints use cursor-based pagination    │
│     (not offset-based) for consistency under concurrent writes.    │
│                                                                    │
│  5. The redirect endpoint (GET /{short_key}) is intentionally      │
│     separate from the API namespace (/api/v1/) to keep URLs as    │
│     short as possible.                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Model and Database Selection

### 6.1 Schema Design

#### URL Table (Primary)

```
┌──────────────────────────────────────────────────────────────────────┐
│                          urls                                        │
├──────────────┬──────────────┬────────────────────────────────────────┤
│ Column       │ Type         │ Notes                                  │
├──────────────┼──────────────┼────────────────────────────────────────┤
│ short_key    │ VARCHAR(16)  │ PRIMARY KEY, indexed                   │
│ original_url │ TEXT         │ The destination URL (max 2048 chars)   │
│ user_id      │ UUID         │ Foreign key to users table             │
│ created_at   │ TIMESTAMP    │ Immutable, set on creation             │
│ expires_at   │ TIMESTAMP    │ NULL = never expires                   │
│ is_active    │ BOOLEAN      │ Soft delete flag, default TRUE         │
│ click_count  │ BIGINT       │ Denormalized counter for fast reads    │
│ custom_alias │ BOOLEAN      │ Whether the key is user-chosen         │
│ metadata     │ JSONB        │ Campaign tags, source, etc.            │
├──────────────┴──────────────┴────────────────────────────────────────┤
│ INDEXES:                                                             │
│   - PRIMARY KEY (short_key)           -- O(1) lookups                │
│   - INDEX idx_user_urls (user_id, created_at DESC)                   │
│   - INDEX idx_expiry (expires_at) WHERE expires_at IS NOT NULL       │
│   - INDEX idx_original (user_id, original_url) -- duplicate detect   │
└──────────────────────────────────────────────────────────────────────┘
```

#### User Table

```
┌──────────────────────────────────────────────────────────────────────┐
│                          users                                       │
├──────────────┬──────────────┬────────────────────────────────────────┤
│ Column       │ Type         │ Notes                                  │
├──────────────┼──────────────┼────────────────────────────────────────┤
│ user_id      │ UUID         │ PRIMARY KEY                            │
│ api_key      │ VARCHAR(64)  │ UNIQUE, hashed                         │
│ email        │ VARCHAR(255) │ UNIQUE                                 │
│ tier         │ ENUM         │ free, pro, enterprise                  │
│ rate_limit   │ INT          │ URLs per hour (varies by tier)         │
│ created_at   │ TIMESTAMP    │                                        │
│ is_active    │ BOOLEAN      │ Account status                         │
├──────────────┴──────────────┴────────────────────────────────────────┤
│ INDEXES:                                                             │
│   - PRIMARY KEY (user_id)                                            │
│   - UNIQUE INDEX (api_key)                                           │
│   - UNIQUE INDEX (email)                                             │
└──────────────────────────────────────────────────────────────────────┘
```

#### Click Events Table (Analytics)

```
┌──────────────────────────────────────────────────────────────────────┐
│                      click_events                                    │
├──────────────┬──────────────┬────────────────────────────────────────┤
│ Column       │ Type         │ Notes                                  │
├──────────────┼──────────────┼────────────────────────────────────────┤
│ event_id     │ UUID / ULID  │ PRIMARY KEY (time-sortable)            │
│ short_key    │ VARCHAR(16)  │ Partition key                          │
│ clicked_at   │ TIMESTAMP    │ Event time (sort key in time-series)   │
│ ip_hash      │ VARCHAR(64)  │ SHA256 of IP (privacy-preserving)      │
│ country      │ CHAR(2)      │ ISO country code from GeoIP            │
│ city         │ VARCHAR(100) │ From GeoIP lookup                      │
│ referrer     │ TEXT         │ HTTP Referer header                    │
│ user_agent   │ TEXT         │ Browser/device info                    │
│ device_type  │ ENUM         │ mobile, desktop, tablet, bot           │
│ browser      │ VARCHAR(50)  │ Parsed from user-agent                 │
│ os           │ VARCHAR(50)  │ Parsed from user-agent                 │
├──────────────┴──────────────┴────────────────────────────────────────┤
│ PARTITION BY: RANGE (clicked_at) -- monthly partitions               │
│ INDEXES:                                                             │
│   - PRIMARY KEY (short_key, clicked_at, event_id)                    │
│   - INDEX (short_key, country)                                       │
│   - INDEX (short_key, referrer)                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Database Selection Rationale

```
┌────────────────────────────────────────────────────────────────────────┐
│                    DATABASE SELECTION MATRIX                           │
├──────────────┬──────────────┬──────────────┬──────────────────────────┤
│ Data Store   │ Use Case     │ Technology   │ Why                      │
├──────────────┼──────────────┼──────────────┼──────────────────────────┤
│ URL Mapping  │ Key-value    │ DynamoDB /   │ - Simple key→value lookup│
│ (Primary)    │ lookups      │ Cassandra    │ - Horizontally scalable  │
│              │              │              │ - Single-digit ms latency│
│              │              │              │ - No complex joins needed│
│              │              │              │ - Tunable consistency    │
├──────────────┼──────────────┼──────────────┼──────────────────────────┤
│ User Data    │ Relational   │ PostgreSQL   │ - ACID transactions      │
│              │ with joins   │ (RDS)        │ - Complex queries        │
│              │              │              │ - Small dataset (~1M)    │
│              │              │              │ - Strong consistency     │
├──────────────┼──────────────┼──────────────┼──────────────────────────┤
│ Click Events │ Time-series  │ ClickHouse / │ - Columnar storage       │
│ (Analytics)  │ append-only  │ Apache Druid │ - Fast aggregations      │
│              │              │ / TimescaleDB│ - Partition by time      │
│              │              │              │ - Billions of rows       │
├──────────────┼──────────────┼──────────────┼──────────────────────────┤
│ Cache        │ Hot URL      │ Redis        │ - Sub-millisecond reads  │
│              │ lookups      │ (Cluster)    │ - Built-in TTL support   │
│              │              │              │ - LRU eviction policy    │
├──────────────┼──────────────┼──────────────┼──────────────────────────┤
│ Message Queue│ Click event  │ Apache Kafka │ - Durable event stream   │
│              │ streaming    │              │ - High throughput        │
│              │              │              │ - Consumer groups        │
├──────────────┴──────────────┴──────────────┴──────────────────────────┤
│                                                                       │
│  Note on DynamoDB vs Cassandra:                                       │
│  - DynamoDB: Managed, auto-scaling, pay-per-request. Best for AWS.    │
│  - Cassandra: Multi-DC replication, tunable consistency, open source. │
│  - Both offer O(1) key lookups at scale with predictable latency.     │
│                                                                       │
└────────────────────────────────────────────────────────────────────────┘
```

#### Why Not a Traditional RDBMS for URL Storage?

1. **No complex queries**: URL lookup is a pure key-value operation. No joins, no
   aggregations, no WHERE clauses beyond the primary key.
2. **Scale ceiling**: A single PostgreSQL instance tops out at ~10K-50K QPS for
   simple reads. With 1.8B rows and 6K peak QPS, we would need multiple read
   replicas and the operational burden grows.
3. **Sharding complexity**: RDBMS sharding is operationally painful (schema changes,
   cross-shard queries). DynamoDB/Cassandra handle partitioning natively.

#### Why Keep PostgreSQL for Users?

The user table is small (~1M rows), requires ACID guarantees (e.g., API key rotation),
and benefits from relational queries (e.g., "find all URLs by user X with expiry before
date Y"). A single PostgreSQL instance handles this trivially.

---

## 7. High-Level Architecture

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENTS                                           │
│    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│    │ Browser  │   │ Mobile   │   │ cURL/API │   │ 3rd Party│              │
│    │  Users   │   │   Apps   │   │  Clients │   │  Integr. │              │
│    └─────┬────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘              │
│          │             │              │              │                      │
└──────────┼─────────────┼──────────────┼──────────────┼──────────────────────┘
           │             │              │              │
           ▼             ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CDN / EDGE LAYER                                    │
│                    (CloudFront / Cloudflare)                                │
│         Cache popular redirects at edge, DDoS protection                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LOAD BALANCER (L7)                                     │
│                    (AWS ALB / Nginx / HAProxy)                              │
│          ┌────────────────────┬────────────────────┐                        │
│          │   GET /{key}       │  POST/DELETE/GET    │                        │
│          │   (Redirect)       │  /api/v1/*          │                        │
│          └────────┬───────────┴────────┬────────────┘                        │
│                   │                    │                                     │
└───────────────────┼────────────────────┼────────────────────────────────────┘
                    │                    │
          ┌─────────▼──────┐   ┌────────▼───────┐
          │  REDIRECT      │   │  API SERVICE   │
          │  SERVICE       │   │  (Write Path)  │
          │  (Read Path)   │   │                │
          │  ┌──────────┐  │   │  ┌──────────┐  │
          │  │ Server 1 │  │   │  │ Server 1 │  │
          │  │ Server 2 │  │   │  │ Server 2 │  │
          │  │ Server 3 │  │   │  │ Server 3 │  │
          │  │   ...     │  │   │  │   ...     │  │
          │  └──────────┘  │   │  └──────────┘  │
          └───────┬────────┘   └───┬────────┬───┘
                  │                │        │
                  │                │        │       ┌──────────────────┐
                  │                │        └──────►│  KEY GENERATION  │
                  │                │               │  SERVICE (KGS)   │
                  ▼                ▼               │  ┌────────────┐  │
          ┌──────────────┐  ┌──────────────┐       │  │ Pre-gen    │  │
          │              │  │              │       │  │ Key Pool   │  │
          │    REDIS      │  │    REDIS      │       │  │ (ZooKeeper)│  │
          │    CACHE      │  │    CACHE      │       │  └────────────┘  │
          │   (Cluster)   │  │   (Cluster)   │       └──────────────────┘
          │              │  │              │
          └──────┬───────┘  └──────┬───────┘
                 │                 │
                 │    ┌────────────┘
                 ▼    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRIMARY DATA STORE                                    │
│                  (DynamoDB / Cassandra Cluster)                             │
│                                                                             │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│   │ Shard 1 │  │ Shard 2 │  │ Shard 3 │  │ Shard 4 │  │ Shard N │        │
│   │ (a-d)   │  │ (e-h)   │  │ (i-l)   │  │ (m-p)   │  │  ...    │        │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────┐
                    │    ANALYTICS PIPELINE         │
                    │                              │
  Click Events ───►│  Kafka ──► Flink/Spark ──►   │
                    │           Aggregator          │
                    │              │                │
                    │              ▼                │
                    │  ┌────────────────────────┐   │
                    │  │ ClickHouse / Druid     │   │
                    │  │ (Analytics OLAP Store) │   │
                    │  └────────────────────────┘   │
                    └──────────────────────────────┘
```

### 7.1 Component Breakdown

#### Read Path (Redirect) - Latency-Critical

```
┌────────────────────────────────────────────────────────────────────────┐
│                     REDIRECT FLOW (READ PATH)                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  User clicks short.ly/aB3x7Kq                                         │
│       │                                                                │
│       ▼                                                                │
│  ┌─────────┐  cache   ┌─────────┐  HIT   ┌──────────────────┐        │
│  │  CDN    │─────────►│  Edge   │───────►│ 301/302 Redirect │        │
│  │  Edge   │  miss    │  Cache  │        │ to original URL  │        │
│  └────┬────┘          └─────────┘        └──────────────────┘        │
│       │                                                                │
│       ▼ (cache miss)                                                   │
│  ┌──────────┐                                                          │
│  │   LB     │                                                          │
│  └────┬─────┘                                                          │
│       │                                                                │
│       ▼                                                                │
│  ┌──────────────┐  1. Check  ┌─────────┐                              │
│  │  Redirect    │──────────►│  Redis   │                              │
│  │  Server      │           │  Cache   │                              │
│  │              │◄──────────│          │                              │
│  │              │  2. HIT?  └─────────┘                              │
│  │              │     │                                                │
│  │              │     ├── YES ──► Return 301/302                       │
│  │              │     │                                                │
│  │              │     └── NO ──► Query DB                              │
│  │              │                  │                                    │
│  │              │◄─────────────────┘                                    │
│  │              │  3. Populate cache                                    │
│  │              │  4. Return 301/302                                    │
│  │              │  5. Async: emit click event to Kafka                  │
│  └──────────────┘                                                      │
│                                                                        │
│  Latency budget:                                                       │
│    CDN hit:       1-5ms                                                │
│    Redis hit:     1-2ms (network) + <1ms (lookup) = ~3ms              │
│    Redis miss:    3ms + 5-10ms (DynamoDB) + 1ms (cache write) = ~15ms │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Write Path (URL Creation)

```
┌────────────────────────────────────────────────────────────────────────┐
│                   URL CREATION FLOW (WRITE PATH)                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Client: POST /api/v1/urls { "long_url": "https://..." }              │
│       │                                                                │
│       ▼                                                                │
│  ┌──────────┐                                                          │
│  │   LB     │   (rate limit check via API key)                         │
│  └────┬─────┘                                                          │
│       │                                                                │
│       ▼                                                                │
│  ┌──────────────┐                                                      │
│  │  API Server  │                                                      │
│  │              │  1. Validate URL format (parse, check scheme)         │
│  │              │  2. Check for duplicate (same user + same URL)        │
│  │              │     └── If exists, return existing short URL          │
│  │              │  3. Get unique key:                                   │
│  │              │     ┌──────────────────────────────────┐              │
│  │              │     │ Option A: KGS (pre-generated)    │              │
│  │              │     │ Option B: Base62(counter)         │              │
│  │              │     │ Option C: Hash + collision check  │              │
│  │              │     └──────────────────────────────────┘              │
│  │              │  4. Write to DynamoDB (conditional put)               │
│  │              │  5. Write to Redis cache                              │
│  │              │  6. Return short URL to client                        │
│  └──────────────┘                                                      │
│                                                                        │
│  Latency budget:                                                       │
│    Validation:        <1ms                                             │
│    Duplicate check:   2-5ms (index lookup)                             │
│    Key generation:    1-2ms (KGS) or <1ms (counter)                   │
│    DB write:          5-10ms                                           │
│    Cache write:       1-2ms                                            │
│    Total:             ~15-25ms                                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Deep Dive: Core Components

### 8.1 URL Shortening Algorithm

The choice of shortening algorithm is the most critical design decision. Below are the
four main approaches, with trade-offs.

#### Key Space Analysis

```
┌────────────────────────────────────────────────────────────────────────┐
│                      KEY SPACE ANALYSIS                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Character set: [a-z, A-Z, 0-9] = 62 characters (Base62)              │
│                                                                        │
│  Key length vs. unique combinations:                                   │
│  ┌──────────┬──────────────────┬────────────────────────┐              │
│  │  Length   │  Combinations    │  Sufficient for        │              │
│  ├──────────┼──────────────────┼────────────────────────┤              │
│  │  5 chars  │  62^5 = 916M     │  ~1 year at 1M/day    │              │
│  │  6 chars  │  62^6 = 56.8B    │  ~155 years at 1M/day │              │
│  │  7 chars  │  62^7 = 3.5T     │  ~9600 years          │              │
│  │  8 chars  │  62^8 = 218T     │  ~600K years           │              │
│  └──────────┴──────────────────┴────────────────────────┘              │
│                                                                        │
│  Recommendation: 7 characters                                          │
│  - 3.5 trillion combinations is more than sufficient for 1.8B URLs     │
│  - Utilization: 1.8B / 3.5T = 0.05% (extremely sparse, low collision) │
│  - Short enough for readability and sharing                            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Approach 1: Base62 Encoding of Auto-Increment Counter

```
┌────────────────────────────────────────────────────────────────────────┐
│             BASE62 ENCODING OF COUNTER                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Algorithm:                                                            │
│    1. Maintain a global auto-incrementing counter.                     │
│    2. Convert counter value to Base62 string.                          │
│    3. Use the Base62 string as the short key.                          │
│                                                                        │
│  Example:                                                              │
│    Counter = 1000000                                                   │
│    Base62(1000000) = "4c92"                                            │
│                                                                        │
│    Base62 encoding:                                                    │
│    chars = "0123456789abcdef...ABCDEF...Z"                             │
│    while n > 0:                                                        │
│        remainder = n % 62                                              │
│        result = chars[remainder] + result                              │
│        n = n // 62                                                     │
│                                                                        │
│  Pros:                                                                 │
│    + Zero collisions (unique counter = unique key)                     │
│    + Simple and deterministic                                          │
│    + Keys grow gradually (short keys first)                            │
│                                                                        │
│  Cons:                                                                 │
│    - Sequential keys are predictable (security concern)                │
│    - Single point of failure (counter service)                         │
│    - Distributed counter coordination is hard                          │
│    - Competitors can estimate your volume                              │
│                                                                        │
│  Mitigation for predictability:                                        │
│    Shuffle bits or XOR with a secret before Base62 encoding.           │
│    e.g., key = Base62(counter XOR 0x5DEECE66D)                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Approach 2: MD5/SHA256 Hash + Truncation

```
┌────────────────────────────────────────────────────────────────────────┐
│             HASH-BASED APPROACH                                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Algorithm:                                                            │
│    1. Compute hash = MD5(long_url) or SHA256(long_url)                 │
│    2. Take first 43 bits of the hash (sufficient for 7 Base62 chars)   │
│    3. Encode those bits as Base62 → 7-character key                    │
│    4. Check for collision in DB:                                       │
│       - If key exists with DIFFERENT URL → append salt and rehash      │
│       - If key exists with SAME URL → return existing                  │
│       - If key doesn't exist → insert                                  │
│                                                                        │
│  Collision handling detail:                                             │
│    hash_input = long_url                                               │
│    while True:                                                         │
│        key = Base62(MD5(hash_input)[:7])                               │
│        if not exists_in_db(key):                                       │
│            insert(key, long_url)                                       │
│            break                                                       │
│        elif db_lookup(key).url == long_url:                            │
│            return key  // same URL, reuse                              │
│        else:                                                           │
│            hash_input = hash_input + str(attempt_number)  // rehash    │
│                                                                        │
│  Collision probability (Birthday Paradox):                             │
│    With 1.8B URLs and 3.5T keyspace:                                   │
│    P(collision) ≈ n^2 / (2 × keyspace)                                 │
│                 ≈ (1.8×10^9)^2 / (2 × 3.5×10^12)                      │
│                 ≈ 46% cumulative collision chance!                      │
│                                                                        │
│    This is TOO HIGH. Need collision detection + resolution.            │
│                                                                        │
│  Pros:                                                                 │
│    + No centralized counter needed                                     │
│    + Same URL always maps to same hash (dedup-friendly)                │
│    + Stateless computation                                             │
│                                                                        │
│  Cons:                                                                 │
│    - Collision handling adds latency and complexity                     │
│    - Requires DB read before write (check existence)                   │
│    - Hash computation cost (minor but nonzero)                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Approach 3: Counter with ZooKeeper Range Allocation

```
┌────────────────────────────────────────────────────────────────────────┐
│             ZOOKEEPER RANGE-BASED COUNTER                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Algorithm:                                                            │
│    1. ZooKeeper allocates counter ranges to each app server.           │
│    2. Each server independently increments within its range.           │
│    3. When a range is exhausted, server requests a new range.          │
│                                                                        │
│  ┌──────────────┐     ┌───────────────────────────────────────┐        │
│  │  ZooKeeper   │     │  Range Allocation                     │        │
│  │  Cluster     │     │                                       │        │
│  │              │     │  Server A: [1,      1,000,000]        │        │
│  │  ┌────────┐  │     │  Server B: [1,000,001, 2,000,000]    │        │
│  │  │ Leader │  │     │  Server C: [2,000,001, 3,000,000]    │        │
│  │  └────────┘  │     │  Server D: [3,000,001, 4,000,000]    │        │
│  │  ┌────────┐  │     │                                       │        │
│  │  │Follower│  │     │  Each range = 1 million IDs           │        │
│  │  └────────┘  │     │  At 60 QPS peak, lasts ~4.6 hours     │        │
│  │  ┌────────┐  │     │  ZK only contacted once per range     │        │
│  │  │Follower│  │     └───────────────────────────────────────┘        │
│  │  └────────┘  │                                                      │
│  └──────────────┘                                                      │
│                                                                        │
│  Pros:                                                                 │
│    + No collisions (guaranteed unique ranges)                          │
│    + Minimal coordination (only on range exhaustion)                   │
│    + Each server works independently within its range                  │
│    + Horizontally scalable                                             │
│                                                                        │
│  Cons:                                                                 │
│    - Gaps in sequence if server crashes mid-range (acceptable)         │
│    - ZooKeeper dependency (operational complexity)                     │
│    - Slightly predictable within a range                               │
│                                                                        │
│  Real-world: Twitter Snowflake uses a similar concept for tweet IDs.   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Approach 4: Snowflake ID

```
┌────────────────────────────────────────────────────────────────────────┐
│             SNOWFLAKE-STYLE ID GENERATION                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  64-bit ID structure:                                                  │
│  ┌───────────────────┬───────────┬──────────────┬─────────────┐       │
│  │ Timestamp (41 bit)│DC ID (5b) │Worker ID (5b)│Sequence(12b)│       │
│  │ ms since epoch    │ 32 DCs    │ 32 workers   │ 4096/ms     │       │
│  └───────────────────┴───────────┴──────────────┴─────────────┘       │
│                                                                        │
│  Total: 41 + 5 + 5 + 12 = 63 bits + 1 sign bit = 64 bits              │
│                                                                        │
│  Capacity:                                                             │
│    - 32 data centers × 32 workers × 4096 IDs/ms                       │
│    - = 4,194,304 IDs per millisecond                                   │
│    - = 4.19 billion IDs per second                                     │
│    - Timestamp lasts: 2^41 ms ≈ 69 years                              │
│                                                                        │
│  For URL shortener:                                                    │
│    Convert 64-bit Snowflake ID to Base62 → 11 characters              │
│    Truncate to 7 characters → still unique enough                     │
│    (discard high-order timestamp bits that rarely change)              │
│                                                                        │
│  Pros:                                                                 │
│    + Time-sortable (useful for analytics and debugging)                │
│    + No coordination needed (worker ID baked in)                       │
│    + Battle-tested at Twitter scale                                    │
│    + k-sortable: rough chronological ordering                          │
│                                                                        │
│  Cons:                                                                 │
│    - 11 Base62 chars is longer than 7 (can truncate with care)        │
│    - Clock skew across servers can cause issues                        │
│    - Worker ID management adds operational overhead                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Key Generation Service (KGS)

The **Key Generation Service** is the recommended approach for production systems. It
pre-generates unique keys offline and hands them out on demand, completely avoiding
runtime collision checks.

```
┌────────────────────────────────────────────────────────────────────────┐
│                  KEY GENERATION SERVICE (KGS)                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Architecture:                                                         │
│                                                                        │
│  ┌───────────────────────────────────────────────────────────┐         │
│  │                    KGS Database                            │         │
│  │                                                           │         │
│  │  ┌─────────────────────┐   ┌─────────────────────┐       │         │
│  │  │   UNUSED KEYS       │   │   USED KEYS          │       │         │
│  │  │                     │   │                      │       │         │
│  │  │  aB3x7Kq            │   │  mN2pR4s  (in use)  │       │         │
│  │  │  Zk9mW2p            │   │  xT5vQ1y  (in use)  │       │         │
│  │  │  hJ4nL8r            │   │  ...                 │       │         │
│  │  │  qW7tY3s            │   │                      │       │         │
│  │  │  ...                 │   │                      │       │         │
│  │  │  (millions of keys)  │   │                      │       │         │
│  │  └──────────┬──────────┘   └──────────────────────┘       │         │
│  │             │                                              │         │
│  └─────────────┼──────────────────────────────────────────────┘         │
│                │                                                        │
│       ┌────────▼────────┐                                              │
│       │  KGS Service    │  (2-3 replicas for HA)                       │
│       │                 │                                              │
│       │  - Loads batch  │                                              │
│       │    of 1000 keys │                                              │
│       │    into memory  │                                              │
│       │  - Marks them   │                                              │
│       │    as "assigned" │                                              │
│       │  - Serves keys  │                                              │
│       │    from memory  │                                              │
│       └────┬───────┬────┘                                              │
│            │       │                                                    │
│    ┌───────▼──┐ ┌──▼───────┐                                           │
│    │ API Srv 1│ │ API Srv 2│  Each API server gets a batch of keys     │
│    │ (local   │ │ (local   │  from KGS and uses them locally.          │
│    │  buffer  │ │  buffer  │  When the buffer runs low, fetch more.    │
│    │  ~1000)  │ │  ~1000)  │                                           │
│    └──────────┘ └──────────┘                                           │
│                                                                        │
│  Key generation (offline batch job):                                   │
│    - Generate random 7-char Base62 strings                             │
│    - Check uniqueness against existing keys                            │
│    - Insert into UNUSED_KEYS table                                     │
│    - Run periodically to maintain pool of ~10M unused keys             │
│                                                                        │
│  Failure handling:                                                     │
│    - If API server crashes, its buffer of ~1000 keys is lost.          │
│    - 1000 keys out of 3.5T keyspace is negligible waste.               │
│    - KGS marks keys as "assigned" atomically (no double-issue).        │
│                                                                        │
│  Concurrency control:                                                  │
│    - KGS uses SELECT ... FOR UPDATE or atomic batch operations         │
│    - Each key is moved from UNUSED → USED atomically                   │
│    - Two KGS replicas never issue the same key                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### KGS Sizing

```
Storage for pre-generated keys:
  Each key: 7 bytes
  10 million keys: 7 × 10M = 70 MB
  100 million keys: 700 MB

  This easily fits in a single database table.
  With an index on (status, key): ~1 GB total.

Throughput:
  At 60 QPS peak write rate, 1 million pre-generated keys
  last: 1,000,000 / 60 = ~16,666 seconds ≈ 4.6 hours.
  
  KGS can lazily generate in batches of 100K keys every few hours.
```

### 8.3 Redirection Service

#### 301 vs 302: A Critical Decision

```
┌────────────────────────────────────────────────────────────────────────┐
│                   301 vs 302 REDIRECT COMPARISON                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┬───────────────────┬──────────────────────────────┐   │
│  │              │ 301 Moved         │ 302 Found                    │   │
│  │              │ Permanently       │ (Temporary Redirect)         │   │
│  ├──────────────┼───────────────────┼──────────────────────────────┤   │
│  │ Browser      │ Caches redirect.  │ Does NOT cache.              │   │
│  │ behavior     │ Future visits go  │ Always hits our server       │   │
│  │              │ directly to dest. │ first.                       │   │
│  ├──────────────┼───────────────────┼──────────────────────────────┤   │
│  │ Server load  │ Lower (browser    │ Higher (every click hits     │   │
│  │              │ caches)           │ our servers)                 │   │
│  ├──────────────┼───────────────────┼──────────────────────────────┤   │
│  │ Analytics    │ Under-counts!     │ Accurate click counts.       │   │
│  │ accuracy     │ Repeat visits not │ Every visit is tracked.      │   │
│  │              │ tracked.          │                              │   │
│  ├──────────────┼───────────────────┼──────────────────────────────┤   │
│  │ SEO impact   │ Passes link juice │ Does not pass link juice     │   │
│  │              │ to destination    │ to destination               │   │
│  ├──────────────┼───────────────────┼──────────────────────────────┤   │
│  │ URL updates  │ Hard to change    │ Easy to change destination   │   │
│  │              │ destination later │ anytime                      │   │
│  └──────────────┴───────────────────┴──────────────────────────────┘   │
│                                                                        │
│  RECOMMENDATION: Use 302 (temporary redirect) by default.             │
│                                                                        │
│  Reasoning:                                                            │
│  1. Analytics is a core feature - we NEED every click to hit us.       │
│  2. We want the ability to update/expire links dynamically.            │
│  3. The additional server load is manageable with caching at our end.  │
│  4. Offer 301 as an opt-in for users who prioritize SEO.              │
│                                                                        │
│  Note: Bitly uses 301. TinyURL uses 301. Google's goo.gl used 301.   │
│  This is because they prioritize reducing server load at massive       │
│  scale. For a new service, start with 302 for better analytics.       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Redirect Response Headers

```
HTTP/1.1 302 Found
Location: https://www.example.com/original-very-long-url
Cache-Control: private, max-age=0, no-cache
X-Robots-Tag: noindex
Server: URLShortener/1.0

# For 301 (when user opts in):
HTTP/1.1 301 Moved Permanently
Location: https://www.example.com/original-very-long-url
Cache-Control: public, max-age=86400
```

#### Redirect Server Implementation (Pseudocode)

```
function handleRedirect(short_key):
    // 1. Check Redis cache
    long_url = redis.get("url:" + short_key)
    
    if long_url is null:
        // 2. Cache miss - check database
        record = db.get(short_key)
        
        if record is null:
            return HTTP 404 "Short URL not found"
        
        if record.expires_at < now():
            return HTTP 410 "This link has expired"
        
        if not record.is_active:
            return HTTP 410 "This link has been deleted"
        
        long_url = record.original_url
        
        // 3. Populate cache with TTL
        redis.setex("url:" + short_key, 3600, long_url)
    
    // 4. Async: emit click event (non-blocking)
    kafka.produce("click-events", {
        short_key: short_key,
        timestamp: now(),
        ip: request.remote_addr,
        referrer: request.headers["Referer"],
        user_agent: request.headers["User-Agent"]
    })
    
    // 5. Return redirect
    return HTTP 302, Location: long_url
```

### 8.4 Analytics Pipeline

Click tracking must be **asynchronous** to avoid adding latency to the redirect path.
Every millisecond of redirect latency is user-visible.

```
┌────────────────────────────────────────────────────────────────────────┐
│                     ANALYTICS PIPELINE                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐                                                      │
│  │  Redirect    │                                                      │
│  │  Server      │──── Fire-and-forget ────┐                            │
│  └──────────────┘                         │                            │
│                                           ▼                            │
│  ┌───────────────────────────────────────────────────────────┐         │
│  │                    APACHE KAFKA                            │         │
│  │                                                           │         │
│  │  Topic: click-events                                      │         │
│  │  Partitions: 16 (partitioned by short_key hash)           │         │
│  │  Retention: 7 days                                        │         │
│  │  Replication factor: 3                                    │         │
│  │                                                           │         │
│  │  Message format:                                          │         │
│  │  {                                                        │         │
│  │    "short_key": "aB3x7Kq",                               │         │
│  │    "timestamp": 1712678400000,                            │         │
│  │    "ip_hash": "a1b2c3...",                                │         │
│  │    "country": "US",                                       │         │
│  │    "referrer": "twitter.com",                             │         │
│  │    "user_agent": "Mozilla/5.0...",                        │         │
│  │    "device_type": "mobile"                                │         │
│  │  }                                                        │         │
│  └────────────┬──────────────────────────────┬───────────────┘         │
│               │                              │                         │
│               ▼                              ▼                         │
│  ┌────────────────────────┐    ┌────────────────────────────┐          │
│  │  STREAM PROCESSOR      │    │  STREAM PROCESSOR          │          │
│  │  (Flink / Kafka        │    │  (Batch Aggregator)        │          │
│  │   Streams)             │    │                            │          │
│  │                        │    │  - Hourly rollups           │          │
│  │  Real-time:            │    │  - Daily summaries          │          │
│  │  - Update click_count  │    │  - Top referrers            │          │
│  │    in Redis (INCR)     │    │  - Geographic breakdown     │          │
│  │  - GeoIP lookup        │    │  - Device/browser stats     │          │
│  │  - User-agent parsing  │    │                            │          │
│  │  - Fraud detection     │    │                            │          │
│  └───────────┬────────────┘    └──────────────┬─────────────┘          │
│              │                                │                        │
│              ▼                                ▼                        │
│  ┌────────────────────┐         ┌────────────────────────┐            │
│  │  Redis             │         │  ClickHouse / Druid    │            │
│  │  (Real-time        │         │  (OLAP Analytics DB)   │            │
│  │   counters)        │         │                        │            │
│  │                    │         │  - Columnar storage     │            │
│  │  url:aB3x7Kq:cnt  │         │  - Fast aggregations    │            │
│  │  = 142857          │         │  - Partitioned by time  │            │
│  └────────────────────┘         │  - Compressed (10:1)    │            │
│                                 └────────────────────────┘            │
│                                                                        │
│  Why Kafka?                                                            │
│  1. Decouples redirect latency from analytics processing.              │
│  2. Absorbs traffic spikes (producers are never blocked).              │
│  3. Supports multiple consumers (real-time + batch + fraud).           │
│  4. Durable: events are persisted even if downstream is down.          │
│  5. Replay: can reprocess historical events if aggregation is wrong.   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Click Count Consistency

```
The click_count field in the URL table is a denormalized counter for fast reads.
It is updated asynchronously via the analytics pipeline, so it may lag behind
the true count by a few seconds. This is acceptable for display purposes.

For exact counts, query the analytics OLAP store directly.

Redis counter update (real-time):
  INCR url:aB3x7Kq:clicks           → total clicks
  INCR url:aB3x7Kq:clicks:2026-04   → monthly clicks
  PFADD url:aB3x7Kq:uniq <ip_hash>  → HyperLogLog for unique visitors

Periodic flush to primary DB:
  Every 5 minutes, batch-update click_count in DynamoDB from Redis counters.
```

---

## 9. Data Partitioning and Sharding

### Sharding Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SHARDING STRATEGIES COMPARED                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Option 1: Hash-Based Partitioning on short_key (RECOMMENDED)         │
│  ─────────────────────────────────────────────────────────────         │
│  shard_id = hash(short_key) % num_shards                              │
│                                                                        │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐                      │
│  │Shard 0 │  │Shard 1 │  │Shard 2 │  │Shard 3 │                      │
│  │hash=0  │  │hash=1  │  │hash=2  │  │hash=3  │                      │
│  │ aB3... │  │ mK7... │  │ xP2... │  │ qR9... │                      │
│  │ zW1... │  │ hJ4... │  │ cN6... │  │ tY5... │                      │
│  └────────┘  └────────┘  └────────┘  └────────┘                      │
│                                                                        │
│  Pros: Uniform distribution, simple routing                            │
│  Cons: Adding shards requires data migration (mitigated by             │
│         consistent hashing)                                            │
│                                                                        │
│                                                                        │
│  Option 2: Range-Based Partitioning on short_key                      │
│  ───────────────────────────────────────────────                       │
│  shard_id based on first character of short_key                        │
│                                                                        │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐                      │
│  │Shard 0 │  │Shard 1 │  │Shard 2 │  │Shard 3 │                      │
│  │ a-f    │  │ g-n    │  │ o-v    │  │ w-Z,0-9│                      │
│  └────────┘  └────────┘  └────────┘  └────────┘                      │
│                                                                        │
│  Pros: Range queries possible, simple to understand                    │
│  Cons: Uneven distribution if keys aren't uniformly distributed        │
│         Hot spots if some ranges are more popular                      │
│                                                                        │
│                                                                        │
│  Option 3: Consistent Hashing (RECOMMENDED FOR PRODUCTION)            │
│  ─────────────────────────────────────────────────────────             │
│                                                                        │
│             ┌───── Node A ─────┐                                       │
│           ╱                     ╲                                      │
│         ╱   ┌─ VNode A1          ╲                                    │
│       ╱     │  ┌─ VNode A2        ╲                                   │
│      │      │  │                   │                                   │
│   Node D ───┤  │    Hash Ring      ├─── Node B                        │
│      │      │  │                   │                                   │
│       ╲     │  └─ VNode B1        ╱                                   │
│         ╲   └─ VNode D1          ╱                                    │
│           ╲                     ╱                                      │
│             └───── Node C ─────┘                                       │
│                                                                        │
│  Each physical node has 100-200 virtual nodes on the ring.             │
│  Adding/removing a node only affects adjacent keys (~1/N data).        │
│                                                                        │
│  When Node E is added:                                                 │
│    - Only keys between Node D and Node E migrate to Node E             │
│    - All other keys remain on their current nodes                      │
│    - Data movement: ~1/N of total data (not 1/2 as in mod hashing)    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### DynamoDB Partition Key Design

```
If using DynamoDB:
  - Partition key: short_key
  - No sort key needed (each item is a single URL record)
  - DynamoDB automatically distributes across partitions based on hash of partition key
  - With random short_keys, distribution is naturally uniform
  
  Throughput per partition: 3000 RCU + 1000 WCU
  For 6000 read QPS: need ~2 partitions minimum (DynamoDB auto-scales)
  
  DynamoDB handles sharding transparently - one of its key advantages.
```

### Cross-Shard Operations

```
Operations that touch multiple shards are rare:
  - Redirect lookup: single-key, single-shard ✓
  - URL creation: single-key, single-shard ✓
  - "List all URLs by user X": requires scatter-gather across shards
    → Use a secondary index (GSI in DynamoDB: user_id → short_keys)
    → Or maintain a separate user_urls table in PostgreSQL
  - Analytics: handled by separate OLAP store, not the URL store
```

---

## 10. Caching Strategy

### Multi-Layer Cache Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                    MULTI-LAYER CACHING                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Layer 1: CDN Edge Cache (CloudFront / Cloudflare)                    │
│  ────────────────────────────────────────────────                      │
│  - Caches 302 responses at edge locations worldwide                   │
│  - Cache key: short_key                                               │
│  - TTL: 5 minutes (short, to preserve analytics accuracy)             │
│  - Covers: viral links clicked millions of times                      │
│  - Hit ratio: 30-50% (only the most popular links)                    │
│                                                                        │
│  Layer 2: Application-Level Cache (Local in-process)                  │
│  ──────────────────────────────────────────────────                    │
│  - LRU cache in each redirect server (e.g., Caffeine/Guava)          │
│  - Size: 100K entries (~50 MB per server)                             │
│  - TTL: 60 seconds                                                    │
│  - Avoids Redis network round-trip for ultra-hot URLs                 │
│  - Hit ratio: 20-30%                                                  │
│                                                                        │
│  Layer 3: Distributed Cache (Redis Cluster)                           │
│  ──────────────────────────────────────────                            │
│  - Central cache shared across all redirect servers                   │
│  - Size: 4M entries (~5 GB) covering the hot 20%                     │
│  - TTL: 1 hour (refreshed on access)                                  │
│  - Pattern: Cache-aside (read-through with lazy population)           │
│  - Hit ratio: 85-95%                                                  │
│  - Eviction: allkeys-lru                                              │
│                                                                        │
│  Layer 4: Database                                                    │
│  ───────────────                                                       │
│  - Only reached on triple cache miss (~1-5% of requests)             │
│  - DynamoDB with DAX (DynamoDB Accelerator) for additional caching    │
│                                                                        │
│                                                                        │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐        │
│  │  CDN    │────►│ Local   │────►│  Redis  │────►│ DynamoDB │        │
│  │  Edge   │miss │ LRU     │miss │ Cluster │miss │          │        │
│  │  Cache  │     │ Cache   │     │         │     │          │        │
│  │ (30-50%)│     │(20-30%) │     │(85-95%) │     │ (source  │        │
│  │         │     │         │     │         │     │  of truth)│        │
│  └─────────┘     └─────────┘     └─────────┘     └──────────┘        │
│                                                                        │
│  Effective DB hit rate after all cache layers:                         │
│    ~1-3% of total requests reach the database.                        │
│    At 6000 QPS peak: only 60-180 QPS hit the DB. Easily handled.     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Cache-Aside Pattern (Implementation)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CACHE-ASIDE PATTERN                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  READ (Redirect):                                                      │
│    1. Look up key in Redis.                                            │
│    2. If HIT → return cached URL, done.                               │
│    3. If MISS → query database.                                       │
│    4. If found in DB → write to Redis with TTL, return URL.           │
│    5. If not in DB → cache "not found" sentinel for 60s               │
│       (prevents cache stampede on invalid URLs).                      │
│                                                                        │
│  WRITE (Create URL):                                                   │
│    1. Write to database first (source of truth).                       │
│    2. Then write to Redis cache.                                       │
│    3. If cache write fails, it's OK - next read will populate it.     │
│                                                                        │
│  DELETE:                                                               │
│    1. Delete from database.                                            │
│    2. Delete from Redis cache.                                         │
│    3. CDN cache will expire naturally (short TTL).                    │
│                                                                        │
│  Cache Invalidation:                                                   │
│    - URL updates (rare): delete from Redis, CDN purge API.            │
│    - Expiration: TTL-based eviction handles most cases.               │
│    - The mantra: "There are only two hard things in computer science: │
│      cache invalidation and naming things."                            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Cache Stampede Prevention

```
When a popular URL's cache entry expires, hundreds of simultaneous requests
may all miss the cache and hit the database concurrently. This is a
"thundering herd" or "cache stampede."

Mitigation strategies:
  1. Probabilistic early expiration (jittered TTL):
     actual_ttl = base_ttl + random(-60, +60) seconds
     
  2. Lock-based recomputation:
     Only one thread fetches from DB; others wait on the lock.
     Redis SETNX "lock:aB3x7Kq" with short expiry.
     
  3. Background refresh:
     Refresh cache entries proactively before they expire.
     If TTL < 10% remaining, trigger async refresh.
     
  4. Negative caching:
     Cache "not found" responses for 60 seconds to prevent
     repeated DB lookups for nonexistent keys (e.g., bots
     scanning random short URLs).
```

---

## 11. Replication and Consistency

### Consistency Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CONSISTENCY REQUIREMENTS                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  URL Shortener consistency needs are RELAXED:                          │
│                                                                        │
│  ┌──────────────────┬────────────────┬─────────────────────────────┐   │
│  │ Operation        │ Consistency    │ Rationale                   │   │
│  ├──────────────────┼────────────────┼─────────────────────────────┤   │
│  │ Create URL       │ Strong (write) │ Must not lose data.         │   │
│  │                  │                │ Use quorum write (W=2, N=3).│   │
│  ├──────────────────┼────────────────┼─────────────────────────────┤   │
│  │ Read/Redirect    │ Eventual       │ 1-2s propagation delay is   │   │
│  │                  │                │ acceptable. Read from any   │   │
│  │                  │                │ replica (R=1 for speed).    │   │
│  ├──────────────────┼────────────────┼─────────────────────────────┤   │
│  │ Delete URL       │ Eventual       │ Soft-delete; cache TTL      │   │
│  │                  │                │ handles propagation.        │   │
│  ├──────────────────┼────────────────┼─────────────────────────────┤   │
│  │ Analytics        │ Eventual       │ Aggregated async; exact     │   │
│  │                  │                │ real-time not required.     │   │
│  └──────────────────┴────────────────┴─────────────────────────────┘   │
│                                                                        │
│  Quorum configuration (Cassandra/DynamoDB):                            │
│    N = 3 (replication factor)                                          │
│    W = 2 (write to 2 of 3 replicas before acknowledging)               │
│    R = 1 (read from any 1 replica for lowest latency)                  │
│                                                                        │
│    W + R > N? → 2 + 1 = 3 > 3? NO, so NOT strongly consistent.       │
│    This is intentional: we trade consistency for read latency.         │
│                                                                        │
│    For strong consistency when needed: use R=2 (but adds latency).    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Replication Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MULTI-REGION REPLICATION                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌───────────────────────────┐    ┌───────────────────────────┐       │
│  │      US-EAST (Primary)    │    │      EU-WEST (Replica)    │       │
│  │                           │    │                           │       │
│  │  ┌─────┐ ┌─────┐ ┌─────┐│    │  ┌─────┐ ┌─────┐ ┌─────┐│       │
│  │  │ DB  │ │ DB  │ │ DB  ││    │  │ DB  │ │ DB  │ │ DB  ││       │
│  │  │Rep 1│ │Rep 2│ │Rep 3││    │  │Rep 1│ │Rep 2│ │Rep 3││       │
│  │  └──┬──┘ └──┬──┘ └──┬──┘│    │  └──┬──┘ └──┬──┘ └──┬──┘│       │
│  │     │       │       │    │    │     │       │       │    │       │
│  │     └───────┼───────┘    │    │     └───────┼───────┘    │       │
│  │             │            │    │             │            │       │
│  │      Local Replication   │    │      Local Replication   │       │
│  │      (sync, <5ms)        │    │      (sync, <5ms)        │       │
│  │                           │    │                           │       │
│  └─────────────┬─────────────┘    └──────────┬────────────────┘       │
│                │                              │                        │
│                └──────── Cross-Region ────────┘                        │
│                   Async Replication (~100-200ms)                       │
│                                                                        │
│  Write path:                                                           │
│    - Writes go to the nearest region.                                  │
│    - DynamoDB Global Tables or Cassandra multi-DC replication          │
│      handles cross-region sync automatically.                          │
│    - Conflict resolution: Last-Writer-Wins (LWW) is fine because      │
│      short_keys are unique and immutable once created.                 │
│                                                                        │
│  Read path:                                                            │
│    - Reads served from the nearest region (lowest latency).            │
│    - A URL created in US-EAST may not be readable in EU-WEST           │
│      for ~200ms. This is acceptable.                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Redis Replication

```
Redis cache is replicated independently per region:
  - Each region has its own Redis cluster (not cross-region replicated)
  - Cache misses in one region simply fall through to the local DB replica
  - This avoids cross-region cache synchronization complexity
  - Cache warm-up after deployment: pre-populate from DB scan of recent hot URLs
```

---

## 12. Fault Tolerance and Failure Handling

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FAILURE SCENARIOS AND HANDLING                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────┬──────────────────────────────────────────────┐   │
│  │ Failure          │ Handling Strategy                             │   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ App server crash │ LB detects via health check (every 5s).      │   │
│  │                  │ Routes traffic to healthy servers.            │   │
│  │                  │ Pre-fetched keys from KGS are lost (OK,      │   │
│  │                  │ ~1000 keys out of trillions).                 │   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ Redis cache down │ Redirect servers fall through to DB directly.│   │
│  │                  │ Latency increases from ~3ms to ~15ms.        │   │
│  │                  │ DB can handle the load temporarily.          │   │
│  │                  │ Circuit breaker: stop trying Redis after 3   │   │
│  │                  │ consecutive failures; retry every 30s.       │   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ Primary DB down  │ Failover to read replica (automatic with     │   │
│  │                  │ DynamoDB/Cassandra multi-node setup).         │   │
│  │                  │ Writes may be briefly unavailable (seconds).  │   │
│  │                  │ Reads continue from replicas + cache.        │   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ KGS down         │ API servers use their local key buffer.      │   │
│  │                  │ Buffer holds ~1000 keys → lasts ~16 minutes  │   │
│  │                  │ at 60 QPS. Fallback: generate keys inline    │   │
│  │                  │ using hash-based approach until KGS recovers.│   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ Kafka down       │ Click events are lost (acceptable trade-off).│   │
│  │                  │ Analytics may have gaps but redirects work.   │   │
│  │                  │ Alternative: buffer events locally on disk    │   │
│  │                  │ and replay when Kafka recovers.               │   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ Region outage    │ DNS failover to secondary region.            │   │
│  │                  │ Route53 health checks detect within 30s.     │   │
│  │                  │ All data is replicated to secondary region.  │   │
│  │                  │ RTO: ~60 seconds. RPO: ~200ms of writes.     │   │
│  ├──────────────────┼──────────────────────────────────────────────┤   │
│  │ CDN outage       │ LB receives traffic directly.               │   │
│  │                  │ Higher latency but functional.               │   │
│  │                  │ DNS TTL (60s) determines switchover speed.   │   │
│  └──────────────────┴──────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Rate Limiting

```
┌────────────────────────────────────────────────────────────────────────┐
│                       RATE LIMITING                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Algorithm: Token Bucket (implemented via Redis)                       │
│                                                                        │
│  Limits:                                                               │
│  ┌──────────────┬──────────────────┬──────────────────────────────┐    │
│  │ Tier         │ URL Creation     │ Redirect (per IP)            │    │
│  ├──────────────┼──────────────────┼──────────────────────────────┤    │
│  │ Free         │ 50/hour          │ 1000/min per short URL       │    │
│  │ Pro          │ 500/hour         │ 10,000/min per short URL     │    │
│  │ Enterprise   │ 10,000/hour      │ No limit                     │    │
│  └──────────────┴──────────────────┴──────────────────────────────┘    │
│                                                                        │
│  Implementation:                                                       │
│    Key: ratelimit:{api_key}:{window}                                   │
│    Redis: INCR + EXPIRE (sliding window counter)                       │
│                                                                        │
│  Anti-abuse for redirects:                                              │
│    - IP-based rate limiting on redirect endpoint                        │
│    - CAPTCHA challenge after threshold                                  │
│    - Block known bot user-agents                                       │
│    - Flag URLs with suspiciously high click rates for review           │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Graceful Degradation Strategy

```
Under extreme load, shed non-critical work in this priority order:

1. KEEP: Redirects (core functionality - always available)
2. KEEP: URL creation (primary write path)
3. SHED: Real-time analytics (buffer in Kafka, process later)
4. SHED: Analytics API (return cached/stale data, HTTP 503 if needed)
5. SHED: Custom alias validation (fall back to system-generated keys)
6. SHED: Duplicate URL detection (allow duplicates temporarily)

Circuit breaker states:
  CLOSED → Normal operation
  OPEN   → Skip the failing dependency, use fallback
  HALF-OPEN → Periodically test if dependency has recovered
```

---

## 13. Scalability

### Horizontal Scaling of Stateless Components

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SCALING STRATEGY                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                 STATELESS TIER (Easy to Scale)                │      │
│  │                                                              │      │
│  │  Redirect Servers:                                            │      │
│  │    Current: 6000 peak QPS                                    │      │
│  │    Per server capacity: ~2000 QPS (Go/Rust) or ~500 QPS (Java)│      │
│  │    Servers needed: 6000/2000 = 3 (with Go) + 3 for redundancy│      │
│  │    Total: 6 redirect servers                                  │      │
│  │    Auto-scale trigger: CPU > 60% or p99 latency > 30ms       │      │
│  │                                                              │      │
│  │  API Servers (Write Path):                                    │      │
│  │    Current: 60 peak QPS                                      │      │
│  │    2 servers are sufficient (with headroom)                   │      │
│  │    Auto-scale trigger: CPU > 70%                              │      │
│  │                                                              │      │
│  │  Scaling is trivial: add more containers behind the LB.      │      │
│  │  No session state, no sticky sessions needed.                 │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                 STATEFUL TIER (Harder to Scale)               │      │
│  │                                                              │      │
│  │  DynamoDB:                                                    │      │
│  │    Auto-scales transparently (on-demand mode).               │      │
│  │    Or provisioned: increase RCU/WCU as needed.               │      │
│  │    Global Tables for multi-region.                            │      │
│  │                                                              │      │
│  │  Cassandra:                                                   │      │
│  │    Add nodes to the ring → data rebalances automatically.    │      │
│  │    Linear scalability: 2× nodes ≈ 2× throughput.            │      │
│  │                                                              │      │
│  │  Redis:                                                       │      │
│  │    Redis Cluster: shard across 3-6 nodes.                    │      │
│  │    Each node: 64 GB RAM, handles ~100K ops/sec.              │      │
│  │    For 6000 QPS: a single Redis node is sufficient.          │      │
│  │    Cluster is for HA, not throughput.                         │      │
│  │                                                              │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Scaling to 10x and 100x

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SCALING PROJECTIONS                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Current design handles:    ~6K read QPS, ~60 write QPS               │
│                                                                        │
│  10× scale (60K read QPS):                                            │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │ - Add more redirect servers (30 instances)                 │        │
│  │ - Redis Cluster with 3 shards (20K QPS each)              │        │
│  │ - DynamoDB: increase RCU to 60K or use DAX                │        │
│  │ - CDN handles most of the increase for viral URLs         │        │
│  │ - Kafka: increase partitions to 64                        │        │
│  │ - No architectural changes needed                          │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                        │
│  100× scale (600K read QPS):                                          │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │ - Multi-region deployment (US, EU, APAC) - each region     │        │
│  │   handles local traffic independently                      │        │
│  │ - CDN becomes critical (cache hit ratio must be >80%)     │        │
│  │ - Redis Cluster: 10+ shards per region                    │        │
│  │ - Consider edge computing (Cloudflare Workers / Lambda@Edge)│       │
│  │   to resolve redirects at the edge without hitting origin  │        │
│  │ - DynamoDB Global Tables or Cassandra multi-DC             │        │
│  │ - Separate read and write services completely              │        │
│  │ - Analytics pipeline: dedicated Kafka cluster, Flink cluster│       │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                        │
│  Bitly scale reference:                                                │
│    ~600M clicks/month ≈ 230 QPS average                               │
│    Our 6K QPS design is already ~26× Bitly's average.                 │
│    With 100× scaling, we handle ~2600× Bitly.                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Read Replicas and CQRS

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CQRS PATTERN FOR URL SHORTENER                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│                     ┌──────────────────┐                               │
│                     │    CLIENTS       │                               │
│                     └────────┬─────────┘                               │
│                              │                                         │
│              ┌───────────────┼───────────────┐                         │
│              │               │               │                         │
│              ▼               │               ▼                         │
│  ┌───────────────────┐       │   ┌───────────────────┐                │
│  │   WRITE SERVICE   │       │   │   READ SERVICE    │                │
│  │   (URL Creation)  │       │   │   (Redirects)     │                │
│  │                   │       │   │                   │                │
│  │   POST /api/v1/   │       │   │   GET /{key}      │                │
│  │   DELETE /api/v1/ │       │   │                   │                │
│  └────────┬──────────┘       │   └────────┬──────────┘                │
│           │                  │            │                            │
│           ▼                  │            ▼                            │
│  ┌────────────────┐          │   ┌────────────────┐                   │
│  │  WRITE DB      │          │   │  READ REPLICAS │                   │
│  │  (Primary)     │──────────┘   │  (3-5 replicas)│                   │
│  │                │   async      │                │                   │
│  │                │──────────────►│                │                   │
│  └────────────────┘  replication └────────────────┘                   │
│                                                                        │
│  Benefits:                                                             │
│  - Read and write paths scale independently                           │
│  - Read replicas can be in different regions                          │
│  - Write path can have stronger consistency guarantees                │
│  - Read path optimized purely for latency                             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring and Observability

### Key Metrics Dashboard

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MONITORING METRICS                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─── LATENCY METRICS (Prometheus + Grafana) ───────────────────┐     │
│  │                                                               │     │
│  │  redirect_latency_ms{quantile="0.50"}: < 5ms                │     │
│  │  redirect_latency_ms{quantile="0.95"}: < 20ms               │     │
│  │  redirect_latency_ms{quantile="0.99"}: < 50ms               │     │
│  │  url_creation_latency_ms{quantile="0.99"}: < 100ms          │     │
│  │  db_query_latency_ms{quantile="0.99"}: < 15ms               │     │
│  │  redis_latency_ms{quantile="0.99"}: < 3ms                   │     │
│  │                                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌─── THROUGHPUT METRICS ────────────────────────────────────────┐     │
│  │                                                               │     │
│  │  redirect_requests_per_second: current QPS                   │     │
│  │  url_creation_requests_per_second: current write QPS         │     │
│  │  kafka_messages_per_second: click event throughput            │     │
│  │  rate_limit_rejections_per_second: abuse indicator            │     │
│  │                                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌─── ERROR METRICS ────────────────────────────────────────────┐     │
│  │                                                               │     │
│  │  http_errors{code="404"}: short URL not found rate           │     │
│  │  http_errors{code="410"}: expired URL rate                   │     │
│  │  http_errors{code="429"}: rate limit hit rate                │     │
│  │  http_errors{code="500"}: internal server errors             │     │
│  │  db_connection_errors: database connectivity issues          │     │
│  │  redis_connection_errors: cache connectivity issues          │     │
│  │                                                               │     │
│  │  SLO: error_rate < 0.01% (1 in 10,000 requests)             │     │
│  │                                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌─── CACHE METRICS ────────────────────────────────────────────┐     │
│  │                                                               │     │
│  │  redis_cache_hit_ratio: target > 90%                         │     │
│  │  redis_cache_evictions_per_second: should be low             │     │
│  │  redis_memory_usage_bytes: vs. max memory                    │     │
│  │  cdn_cache_hit_ratio: target > 40%                           │     │
│  │  local_cache_hit_ratio: target > 20%                         │     │
│  │                                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌─── STORAGE METRICS ──────────────────────────────────────────┐     │
│  │                                                               │     │
│  │  total_urls_count: total URLs in system                      │     │
│  │  urls_created_today: daily creation rate                     │     │
│  │  expired_urls_count: URLs past expiration                    │     │
│  │  db_storage_bytes: disk usage growth trend                   │     │
│  │  kgs_available_keys: must stay above threshold (>100K)       │     │
│  │                                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌─── BUSINESS METRICS ─────────────────────────────────────────┐     │
│  │                                                               │     │
│  │  daily_active_users: DAU trend                               │     │
│  │  urls_per_user: engagement metric                            │     │
│  │  clicks_per_url: viral coefficient                           │     │
│  │  top_domains_shortened: content analysis                     │     │
│  │                                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Alerting Rules

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ALERTING THRESHOLDS                              │
├──────────────────────┬────────────────┬───────────────────────────────┤
│ Alert                │ Threshold      │ Action                        │
├──────────────────────┼────────────────┼───────────────────────────────┤
│ Redirect p99 > 100ms│ CRITICAL       │ Page on-call, check DB/cache  │
│ Error rate > 1%      │ CRITICAL       │ Page on-call immediately      │
│ Cache hit < 70%      │ WARNING        │ Investigate cache evictions   │
│ KGS keys < 10K       │ WARNING        │ Trigger key generation job    │
│ KGS keys < 1K        │ CRITICAL       │ Page on-call, fallback to hash│
│ DB CPU > 80%         │ WARNING        │ Consider scaling/optimization │
│ Kafka consumer lag   │ WARNING        │ Scale consumers, check proc.  │
│   > 100K messages    │                │                               │
│ Redis memory > 80%   │ WARNING        │ Review eviction policy/sizing │
│ Disk usage > 80%     │ WARNING        │ Plan storage expansion        │
└──────────────────────┴────────────────┴───────────────────────────────┘
```

### Distributed Tracing

```
Each request gets a trace ID that flows through all components:

  Browser → CDN → LB → Redirect Server → Redis → DB → Kafka
           t=0   t=1ms  t=2ms            t=3ms   t=8ms  t=9ms

Tools: Jaeger / Zipkin / AWS X-Ray
Sampling rate: 1% for redirects (high volume), 100% for writes
```

---

## 15. Trade-offs and Design Decisions

### Algorithm Comparison

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    URL SHORTENING ALGORITHM COMPARISON                         │
├──────────────┬──────────────┬──────────────┬──────────────┬───────────────────┤
│ Criterion    │ Base62       │ Hash+Trunc   │ ZK Counter   │ KGS (Pre-gen)    │
│              │ Counter      │ (MD5/SHA)    │ Range        │                   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Collision    │ None         │ Possible     │ None         │ None              │
│              │              │ (needs check)│              │                   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Predictable  │ Yes (bad)    │ No           │ Within range │ No                │
│              │              │              │ (semi-bad)   │                   │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Latency      │ ~1ms         │ ~2-5ms       │ ~1ms         │ ~1ms              │
│              │              │ (with check) │              │ (from local buf)  │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Scalability  │ SPOF         │ Stateless    │ Good         │ Excellent         │
│              │ (counter)    │ (no coord)   │ (ZK needed)  │ (pre-computed)    │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Dedup        │ No           │ Natural      │ No           │ No                │
│ (same URL)   │ (new key)    │ (same hash)  │ (new key)    │ (new key)         │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Complexity   │ Low          │ Medium       │ Medium       │ Medium            │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Dependencies │ Counter DB   │ None         │ ZooKeeper    │ KGS DB + service  │
├──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ Recommended? │ For small    │ If dedup is  │ For large    │ BEST for          │
│              │ scale only   │ critical     │ distributed  │ production        │
│              │              │              │ systems      │                   │
└──────────────┴──────────────┴──────────────┴──────────────┴───────────────────┘

Winner: KGS (Key Generation Service)
  - Zero runtime collisions
  - O(1) key retrieval from local buffer
  - Unpredictable keys (security)
  - Decoupled from write path latency
  - Trade-off: operational overhead of running KGS
```

### Database Comparison

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                       DATABASE COMPARISON                                      │
├──────────────┬──────────────────┬──────────────────┬──────────────────────────┤
│ Criterion    │ DynamoDB         │ Cassandra        │ PostgreSQL               │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Ops overhead │ Fully managed    │ Self-managed     │ Managed (RDS) or self    │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Latency      │ <10ms single-    │ <10ms            │ <5ms (single node)       │
│              │ digit ms at any  │                  │ Degrades with scale      │
│              │ scale            │                  │                          │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Scalability  │ Infinite (auto)  │ Linear (add      │ Vertical + read replicas │
│              │                  │ nodes)           │ Sharding is painful      │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Multi-region │ Global Tables    │ Native multi-DC  │ Logical replication      │
│              │ (built-in)       │ (battle-tested)  │ (limited)                │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Cost         │ Pay-per-request  │ Infra + ops      │ Cheapest at low scale    │
│              │ or provisioned   │ team cost        │                          │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Consistency  │ Eventual or      │ Tunable          │ Strong (ACID)            │
│              │ strong (per-req) │ (per-query)      │                          │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Query        │ Key-value only   │ CQL (limited)    │ Full SQL, joins, etc.    │
│ flexibility  │ (GSI for others) │                  │                          │
├──────────────┼──────────────────┼──────────────────┼──────────────────────────┤
│ Best for     │ AWS-native,      │ Multi-cloud,     │ Small-medium scale,      │
│              │ variable traffic │ write-heavy      │ complex queries          │
└──────────────┴──────────────────┴──────────────────┴──────────────────────────┘

Recommendation:
  - DynamoDB if you're on AWS (simplest ops, auto-scaling)
  - Cassandra if multi-cloud or you need fine-grained control
  - PostgreSQL ONLY if your scale is <1M URLs and you value simplicity
```

### 301 vs 302 Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│                   REDIRECT STATUS CODE DECISION                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Use 302 when:                                                        │
│    ✓ Analytics accuracy is critical (track every click)               │
│    ✓ You need ability to change destination URL                       │
│    ✓ Link expiration is a feature                                     │
│    ✓ You're building a new service and want maximum flexibility        │
│                                                                        │
│  Use 301 when:                                                        │
│    ✓ Minimizing server load is the top priority                       │
│    ✓ SEO pass-through matters to your users                           │
│    ✓ You're at extreme scale and every request counts                 │
│    ✓ Analytics can tolerate undercounting                             │
│                                                                        │
│  Our choice: 302 by default, 301 as opt-in per URL                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### SQL vs NoSQL Decision Framework

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  "If your primary access pattern is key-value lookup                  │
│   and you need to scale beyond a single machine,                      │
│   use a purpose-built key-value or wide-column store."                │
│                                                                        │
│  URL shortener's primary access pattern:                              │
│    INPUT: short_key (string)                                          │
│    OUTPUT: original_url (string)                                      │
│                                                                        │
│  This is the textbook use case for a key-value store.                 │
│  No joins. No transactions across keys. No complex WHERE clauses.     │
│                                                                        │
│  SQL makes sense for:                                                 │
│    - User management (ACID, complex queries)                          │
│    - Billing and subscriptions                                        │
│    - Admin dashboards                                                  │
│                                                                        │
│  Polyglot persistence: use the right DB for each use case.            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you handle custom aliases?

**Answer:** Custom aliases follow the same write path but skip the key generation step.
The user-provided alias is validated (alphanumeric, hyphens, 3-30 characters, no profanity
filter hit) and then checked against the database with a conditional write (DynamoDB
`ConditionExpression: attribute_not_exists(short_key)` or Cassandra `IF NOT EXISTS`). If
the alias already exists, return HTTP 409 Conflict. Custom aliases are stored in the same
table as auto-generated keys; a `custom_alias` boolean flag distinguishes them. To prevent
custom aliases from colliding with future auto-generated keys, reserve a character pattern
(e.g., auto-generated keys always start with a lowercase letter, custom aliases can contain
hyphens which auto-generated keys never do). Alternatively, use separate key namespaces.

---

### Q2: How do you handle URL expiration?

**Answer:** Each URL record has an optional `expires_at` timestamp. Expiration is checked
in two places:

1. **At read time (lazy):** When a redirect is requested, check `expires_at < now()`. If
   expired, return HTTP 410 Gone and delete from cache.
2. **Background cleanup (eager):** A daily cron job scans for expired URLs using the
   `idx_expiry` index (`SELECT short_key FROM urls WHERE expires_at < now() AND is_active = true`).
   It soft-deletes them (`is_active = false`), removes them from cache, and moves the
   `short_key` back to the KGS unused pool for recycling. In DynamoDB, use TTL feature
   which automatically deletes expired items.

---

### Q3: What if two users submit the same long URL?

**Answer:** There are two valid approaches:

- **Per-user dedup:** Before generating a new key, query `(user_id, original_url)` index.
  If a match exists, return the existing short URL. Different users get different short
  URLs for the same long URL. This allows per-user analytics and independent expiration.
  This is the recommended approach.

- **Global dedup:** All users share the same short URL for the same long URL. Saves storage
  but makes deletion and expiration complex (who "owns" it?). Analytics become ambiguous.
  TinyURL uses this approach for simplicity. Not recommended for a Bitly-style service.

---

### Q4: How do you prevent abuse and spam?

**Answer:** Multiple layers of defense:

1. **Rate limiting:** Token bucket per API key (creation) and per IP (redirects). Implemented
   via Redis with sliding window counters.
2. **URL validation:** Check submitted URLs against Google Safe Browsing API or a local
   blocklist of known malware/phishing domains. Reject URLs pointing to our own domain
   (redirect loops).
3. **CAPTCHA:** Require CAPTCHA for anonymous URL creation (no API key).
4. **Link scanning:** Async job that follows created URLs and checks destination content.
   Flag suspicious content for human review. Auto-disable links with confirmed malware.
5. **Monitoring:** Alert on sudden spikes in URL creation from a single user or IP range.
6. **Cooldown:** After rate limit is hit, require exponential backoff before new requests.

---

### Q5: How do you generate globally unique keys in a distributed system?

**Answer:** The KGS approach avoids distributed coordination entirely. Pre-generate millions
of random keys offline and store them in a database. Each application server fetches a
batch of keys (e.g., 1000) into a local in-memory buffer. Key assignment uses an atomic
database operation (e.g., `DELETE FROM unused_keys LIMIT 1000 RETURNING short_key`). If two
KGS instances run simultaneously, they get different batches because the operation is atomic.
If an app server crashes and loses its buffer, those keys are simply never used -- wasting
1000 out of 3.5 trillion keys is negligible. No ZooKeeper, no distributed locks, no
coordination needed beyond a simple database.

---

### Q6: How do you handle hot URLs (viral links)?

**Answer:** A single URL going viral (millions of clicks per hour) creates a hot key problem:

1. **CDN caching:** Cache the redirect at the edge. With a 5-minute CDN TTL, a viral link
   with 1M clicks/hour generates only ~12 origin requests per edge location per hour.
2. **Local in-memory cache:** Each redirect server caches the top 100K URLs locally. A viral
   URL will be in every server's local cache after the first request.
3. **Redis read replicas:** If using Redis Cluster, the hot key lands on one shard. Add
   read replicas for that shard, or use client-side replication where the client randomly
   picks from multiple replicas.
4. **Request coalescing:** If multiple concurrent requests hit the same cache miss, only
   one request fetches from DB. Others wait on the result (singleflight pattern in Go).

---

### Q7: How do you handle the read/write ratio imbalance?

**Answer:** The 100:1 read-to-write ratio is a defining characteristic. The architecture
exploits this by:

- **Separating read and write services** (CQRS-lite): Redirect servers are scaled
  independently from API servers. Scale redirect servers 10-50x more than API servers.
- **Aggressive caching:** With 90%+ cache hit ratio, only 10% of reads hit the database.
  The effective DB read QPS is 600, not 6000.
- **Read replicas:** Database read replicas serve redirect queries; the primary handles writes.
- **CDN:** Offloads the most popular URLs entirely from origin infrastructure.

---

### Q8: What happens if the database is temporarily unavailable?

**Answer:** Defense in depth:

1. **Cache serves most reads:** With 90%+ hit ratio and 1-hour TTL, the cache can serve
   reads for up to an hour without the database. This covers most short outages.
2. **Circuit breaker on DB:** After 3 consecutive DB failures, open the circuit. Return
   cached results if available, or HTTP 503 with `Retry-After` header.
3. **Write path:** Queue write requests in a local buffer or SQS queue. Process them when
   DB recovers. Return HTTP 202 Accepted (the short URL will work once DB is back).
4. **Multi-AZ / multi-region:** DynamoDB multi-AZ or Cassandra multi-DC means a single AZ
   failure does not cause DB unavailability.

---

### Q9: How do you ensure short URLs are not predictable?

**Answer:** Predictability is a security concern because attackers could enumerate valid short
URLs and discover private/sensitive links. Solutions:

1. **KGS with random generation:** Keys are randomly generated Base62 strings, not sequential.
   Enumerating 62^7 = 3.5 trillion possibilities is infeasible.
2. **No sequential patterns:** Avoid auto-increment counters without obfuscation.
3. **Rate limiting on redirect:** Limit redirect requests per IP to prevent scanning.
4. **Private links:** For sensitive URLs, require authentication to access (token in query
   param or cookie). This is a premium feature.
5. **Monitoring:** Detect and block IPs making rapid sequential requests to different short URLs.

---

### Q10: How do you handle database schema migrations?

**Answer:** With a NoSQL store like DynamoDB or Cassandra:

- **Schema-less:** Adding new fields requires no migration. Just start writing the new field;
  old records will have it as null. Application code handles both old and new formats.
- **Backward compatibility:** Always make additive changes. Never remove or rename fields
  in-place. Deprecate fields by adding new ones alongside.
- **For PostgreSQL (user table):** Use online migration tools like `pg-osc` or `gh-ost` to
  apply schema changes without locking tables. Perform rolling migrations: add new column,
  backfill, deploy code that writes both old and new, deploy code that reads new, drop old.

---

### Q11: How would you implement A/B testing with short URLs?

**Answer:** Enable a single short URL to redirect to different destinations based on rules:

```
URL record:
{
  "short_key": "promo2026",
  "destinations": [
    { "url": "https://example.com/landing-v1", "weight": 50 },
    { "url": "https://example.com/landing-v2", "weight": 50 }
  ],
  "split_type": "weighted_random"  // or "cookie_based" for consistency
}
```

The redirect server picks a destination based on the weight distribution. For consistent
user experience, hash the user's IP or cookie to deterministically assign them to a variant.
Track which variant each click went to in the analytics pipeline for conversion analysis.

---

### Q12: How do you handle the "thundering herd" problem when a popular URL's cache expires?

**Answer:** When a cache entry for a viral URL expires, thousands of simultaneous requests
may all miss the cache and hit the database concurrently.

Solutions (in order of sophistication):
1. **Jittered TTL:** Add random jitter to TTL so entries expire at slightly different times.
   `TTL = base_ttl + random(0, 120)` seconds.
2. **Mutex/lock-based refresh:** First thread to detect a miss acquires a distributed lock
   (`SETNX lock:key 1 EX 5`), fetches from DB, and populates cache. Other threads wait
   briefly (50ms) and retry the cache. The `singleflight` pattern in Go is ideal.
3. **Proactive refresh:** A background process refreshes cache entries before they expire.
   If remaining TTL < 10%, trigger an async refresh. The stale value is served until the
   refresh completes.
4. **Two-tier TTL:** Soft TTL (1 hour) triggers background refresh. Hard TTL (2 hours) is
   when the entry is actually evicted. Between soft and hard, stale data is served while
   refresh happens async.

---

### Q13: What are the security considerations for a URL shortener?

**Answer:**

1. **Open redirect vulnerability:** Short URLs can be used to disguise malicious destinations.
   Mitigation: scan URLs against malware/phishing databases, show preview pages.
2. **Data exfiltration:** Attackers encode data in URL parameters to exfiltrate through the
   shortener (it bypasses DLP tools). Mitigation: log and monitor URL patterns.
3. **Denial of service:** Mass-creation of URLs to exhaust key space or storage.
   Mitigation: rate limiting, API key requirements, CAPTCHA.
4. **Information disclosure:** Short URLs in browser history, server logs, and Referer
   headers may leak sensitive information. Mitigation: offer "private" URLs that require
   authentication.
5. **Clickjacking:** Short URL landing page (preview mode) must include
   `X-Frame-Options: DENY` header.
6. **API key security:** Store API keys hashed (bcrypt/argon2), never in plaintext. Use
   HTTPS everywhere. Rotate keys periodically.

---

### Q14: How would you migrate from one database to another (e.g., PostgreSQL to DynamoDB)?

**Answer:** A phased migration approach:

1. **Dual-write phase:** Modify the write path to write to both old (PostgreSQL) and new
   (DynamoDB) databases simultaneously. The old DB remains the source of truth.
2. **Backfill:** Run a one-time migration job that copies all existing records from
   PostgreSQL to DynamoDB. Handle conflicts (dual-write may have already copied some).
3. **Shadow-read phase:** Read from both databases and compare results. Log any
   discrepancies. Fix inconsistencies. This runs for days/weeks until confidence is high.
4. **Cutover reads:** Switch the read path to DynamoDB. PostgreSQL is still receiving writes
   as a safety net.
5. **Cutover writes:** Stop writing to PostgreSQL. DynamoDB is now the sole data store.
6. **Decommission:** After a soak period (e.g., 2 weeks with no issues), shut down PostgreSQL.

Use feature flags to control each phase. Rollback at any step is trivial: flip the flag back.

---

### Q15: How would you design URL shortener for multi-tenancy (enterprise white-label)?

**Answer:** Enterprise customers want their own custom domains (e.g., `links.company.com`)
with isolated analytics:

1. **Custom domain mapping:** Add a `domain` field to the URL table. The redirect service
   checks the `Host` header and looks up `(domain, short_key)` as the composite key.
   Same short_key can exist under different domains without collision.

2. **DNS setup:** Customer creates a CNAME record: `links.company.com → shortener.ourservice.com`.
   Our load balancer accepts traffic for any configured custom domain. TLS certificates
   are provisioned via Let's Encrypt with DNS-01 challenge or AWS Certificate Manager.

3. **Tenant isolation:**
   - **Logical isolation:** Same database, partitioned by `tenant_id`. DynamoDB GSI on
     `(tenant_id, short_key)`. Cheaper but "noisy neighbor" risk.
   - **Physical isolation (enterprise):** Dedicated Redis instance and database partition
     per tenant. Higher cost but guaranteed SLAs.

4. **Analytics isolation:** Each tenant sees only their own click data. Analytics queries
   are always filtered by `tenant_id`. Use row-level security in the OLAP store.

5. **Rate limiting per tenant:** Each tenant has their own rate limit pool, not shared with
   others.

```
┌────────────────────────────────────────────────────────────────────────┐
│                  MULTI-TENANT ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │links.acme.com│  │go.beta.io    │  │short.ly      │                │
│  │ (Tenant A)   │  │ (Tenant B)   │  │ (Default)    │                │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
│         │                 │                 │                          │
│         └─────────────────┼─────────────────┘                          │
│                           │                                            │
│                           ▼                                            │
│               ┌───────────────────────┐                               │
│               │   LOAD BALANCER       │                               │
│               │   (SNI-based routing  │                               │
│               │    or Host header)    │                               │
│               └───────────┬───────────┘                               │
│                           │                                            │
│                           ▼                                            │
│               ┌───────────────────────┐                               │
│               │   REDIRECT SERVICE    │                               │
│               │                       │                               │
│               │  domain = Host header │                               │
│               │  key = path segment   │                               │
│               │  lookup(domain, key)  │                               │
│               └───────────────────────┘                               │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: System at a Glance

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM SUMMARY                                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Scale:       1.8B URLs over 5 years, 6K peak read QPS               │
│  Storage:     ~1 TB URLs + ~10 TB analytics                          │
│  Key algo:    KGS (pre-generated random Base62, 7 chars)             │
│  Database:    DynamoDB (URLs) + PostgreSQL (users) + ClickHouse (analytics) │
│  Cache:       Redis Cluster (5 GB, 90%+ hit ratio)                   │
│  Queue:       Kafka (click events, 16 partitions)                    │
│  Redirect:    302 by default (analytics-first)                       │
│  Consistency: Eventual for reads, quorum for writes                  │
│  Availability: 99.99% (multi-AZ, multi-region)                      │
│  Latency:     p50 < 5ms, p99 < 50ms                                 │
│                                                                        │
│  Key trade-offs made:                                                 │
│  1. Availability over consistency (AP in CAP)                        │
│  2. 302 over 301 (analytics accuracy over server load)               │
│  3. KGS over hash (no collisions, slight operational overhead)       │
│  4. NoSQL over SQL for URL store (scale over query flexibility)      │
│  5. Async analytics over sync (latency over real-time accuracy)      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```
