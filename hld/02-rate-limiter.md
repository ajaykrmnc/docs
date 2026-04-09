# Design a Distributed Rate Limiter
**Difficulty:** Medium-Hard | **Companies:** Google, Amazon, Cloudflare, Stripe, Netflix

> For the low-level class design, see [LLD: Rate Limiter](/lld/01-rate-limiter)

---

## 1. Problem Statement and Scope

### What is Rate Limiting?

Rate limiting is a technique to control the rate of requests a client can make to a
server within a given time window. It protects services from abuse, prevents resource
starvation, manages costs, and ensures fair usage across tenants.

### Problem

Design a **distributed rate limiting system** that can:
- Throttle API requests across hundreds of application servers
- Support multiple rate limiting algorithms (token bucket, sliding window, etc.)
- Handle multi-tenant workloads with per-tenant, per-endpoint, and per-user limits
- Process millions of requests per second with sub-millisecond overhead
- Remain consistent (or gracefully degrade) during partial failures

### Scope

```
┌─────────────────────────────────────────────────────────────────────┐
│                          IN SCOPE                                   │
├─────────────────────────────────────────────────────────────────────┤
│  - API request rate limiting (HTTP, gRPC)                           │
│  - Multiple algorithms (token bucket, sliding window, etc.)         │
│  - Multi-tenant support with per-tenant configuration               │
│  - Distributed counters across server fleet                         │
│  - Rate limit rule management (CRUD)                                │
│  - Rate limit response headers (X-RateLimit-*)                      │
│  - Allow/deny lists for bypass or hard block                        │
│  - Monitoring and observability dashboard                           │
├─────────────────────────────────────────────────────────────────────┤
│                         OUT OF SCOPE                                │
├─────────────────────────────────────────────────────────────────────┤
│  - DDoS protection (layer 3/4 network-level filtering)              │
│  - Request queuing / throttling with retries (that's a queue)       │
│  - Cost-based billing or metering                                   │
│  - Authentication / authorization (assumed handled upstream)        │
└─────────────────────────────────────────────────────────────────────┘
```

### Real-World Examples

| Company     | Use Case                                      | Scale                    |
|-------------|-----------------------------------------------|--------------------------|
| Cloudflare  | Edge rate limiting for 25M+ internet properties | Billions of req/sec     |
| Stripe      | API rate limiting per merchant                | Millions of API calls/day |
| Google      | Cloud API quotas per project                  | Millions of projects     |
| Netflix     | Zuul gateway rate limiting                    | 100B+ requests/day       |
| Amazon      | API Gateway throttling per API key            | Millions of APIs         |

---

## 2. Functional Requirements

### Core Requirements

| ID  | Requirement                            | Description                                                                                |
|-----|----------------------------------------|--------------------------------------------------------------------------------------------|
| FR1 | Rate limit by identity                 | Limit by user ID, API key, IP address, or any combination                                  |
| FR2 | Multiple time windows                  | Per-second, per-minute, per-hour, per-day limits simultaneously                            |
| FR3 | Per-endpoint configuration             | Different limits for `/api/search` (100/min) vs `/api/upload` (10/min)                     |
| FR4 | Rate limit headers                     | Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` in every response |
| FR5 | Allow/deny lists                       | Bypass rate limiting for trusted partners; hard-block known abusers                        |
| FR6 | Multi-tenant support                   | Each tenant (SaaS customer) has independent rate limit configurations                      |
| FR7 | Rule management                        | CRUD operations on rate limit rules with hot-reload (no restart)                           |
| FR8 | Usage dashboard                        | Real-time view of rate limit counters, hit rates, and rejected requests                    |
| FR9 | Graceful rejection                     | Return HTTP 429 with `Retry-After` header when limit exceeded                              |
| FR10| Multiple algorithms                    | Support token bucket, sliding window counter, fixed window, leaky bucket                   |

### Request Flow

```
  Client Request
       │
       ▼
  ┌──────────┐    ┌───────────────────────────────────────────────────┐
  │  Extract  │    │  Rate Limit Decision                              │
  │  Identity ├───►│                                                   │
  │  (key)    │    │  1. Check deny list    → BLOCK (403)              │
  └──────────┘    │  2. Check allow list   → ALLOW (bypass)           │
                  │  3. Load matching rule                             │
                  │  4. Check counter      → ALLOW or BLOCK (429)     │
                  │  5. Increment counter                              │
                  │  6. Set response headers                           │
                  └───────────────────────────────────────────────────┘
```

---

## 3. Non-Functional Requirements

| Requirement        | Target                    | Rationale                                                |
|--------------------|---------------------------|----------------------------------------------------------|
| Latency overhead   | < 1ms p99                 | Rate limiter sits in the hot path of every request       |
| Throughput         | 10M+ decisions/sec        | Aggregated across all servers in the fleet               |
| Availability       | 99.99% (52 min/year)      | Downtime means either all traffic blocked or all allowed |
| Consistency        | Near-exact (< 1% drift)   | Slight over-counting acceptable; under-counting is not   |
| Scalability        | Horizontal                | Add more Redis nodes / servers linearly                  |
| Fault tolerance    | Configurable fail mode    | Fail-open (allow) or fail-closed (deny) per rule         |
| Durability         | Rules durable, counters ephemeral | Counters naturally expire; rules must survive restarts |

### Fail-Open vs Fail-Closed

```
┌────────────────────────────────────────────────────────────────┐
│                     FAIL-OPEN (Default)                        │
├────────────────────────────────────────────────────────────────┤
│  Redis down → allow all requests → risk of overload           │
│  Use for: non-critical APIs, internal services                │
│  Rationale: availability > protection                         │
├────────────────────────────────────────────────────────────────┤
│                     FAIL-CLOSED                                │
├────────────────────────────────────────────────────────────────┤
│  Redis down → deny all requests → service appears down        │
│  Use for: payment APIs, security-sensitive endpoints          │
│  Rationale: protection > availability                         │
├────────────────────────────────────────────────────────────────┤
│                  FAIL-LOCAL (Hybrid)                           │
├────────────────────────────────────────────────────────────────┤
│  Redis down → fall back to local in-memory counters           │
│  Use for: balanced approach, most production systems          │
│  Rationale: approximate limiting > no limiting                │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Back-of-Envelope Estimation

### Traffic Assumptions

```
Tenants:              1,000 (SaaS customers)
API endpoints/tenant: 50
Users/tenant:         100,000
Total users:          100M
Peak requests/sec:    10M (across all tenants)
Avg request size:     ~1 KB
```

### Counter Storage

```
Unique rate limit keys:
  = users * endpoints * time_windows
  = 100M * 1 (most active endpoint) * 3 (sec/min/hour windows)
  = 300M keys (worst case)
  = ~100M keys (realistic active set at any time)

Per-key storage:
  Key:   ~80 bytes (e.g., "tenant42:api/search:min:user12345678")
  Value: ~16 bytes (counter + TTL metadata)
  Total: ~100 bytes/key

Total memory:
  = 100M keys * 100 bytes
  = 10 GB

  This fits comfortably in a Redis cluster with 3-5 nodes
  (each node: 4-8 GB, with replication overhead)
```

### Redis Operations

```
  Requests/sec:     10M
  Redis ops/request: 2 (GET counter + INCR counter, or 1 Lua script)
  Total Redis ops:   10-20M ops/sec

  Single Redis node: ~100K-300K ops/sec (depending on operation)
  Nodes needed:      10M / 200K = 50 shards (conservative)

  With Redis Cluster: 50 primary + 50 replica = 100 nodes
  Or with Lua scripts: 10M / 200K = 50 shards
```

### Network Bandwidth

```
  Rate limit check payload: ~200 bytes/request
  10M req/sec * 200 bytes = 2 GB/sec between app servers and Redis
  Distributed across 50 shards = ~40 MB/sec per shard (manageable)
```

### Rule Storage

```
  Rules:  1,000 tenants * 50 endpoints * 3 windows = 150,000 rules
  Size:   150K * 500 bytes = 75 MB
  Fits easily in any relational DB + local cache
```

---

## 5. API Design

### 5.1 Rate Limit Check (Internal Middleware API)

This is the hot-path API called on every incoming request. It is not exposed externally
but invoked by the API gateway or service mesh sidecar.

```
checkRateLimit(request: RateLimitRequest) -> RateLimitResponse

RateLimitRequest {
    client_id:    string       // user ID, API key, or IP
    tenant_id:    string       // SaaS customer identifier
    endpoint:     string       // e.g., "POST /api/orders"
    http_method:  string       // GET, POST, PUT, DELETE
    timestamp:    int64        // Unix timestamp in millis
    cost:         int          // weight of this request (default 1)
}

RateLimitResponse {
    allowed:      bool         // true = proceed, false = reject
    limit:        int          // max requests in window
    remaining:    int          // requests remaining
    reset_at:     int64        // Unix timestamp when window resets
    retry_after:  int          // seconds to wait (if denied)
    rule_id:      string       // which rule triggered the decision
}
```

### 5.2 Admin API (External, for Rule Management)

```
# Create or update a rate limit rule
PUT /v1/rules/{rule_id}
{
    "tenant_id":         "tenant-42",
    "endpoint_pattern":  "POST /api/orders",
    "identifier_type":   "API_KEY",          // USER | API_KEY | IP | GLOBAL
    "algorithm":         "TOKEN_BUCKET",     // TOKEN_BUCKET | SLIDING_WINDOW | FIXED_WINDOW | LEAKY_BUCKET
    "limit":             1000,
    "window_seconds":    60,
    "burst_capacity":    50,                 // for token bucket
    "fail_mode":         "OPEN",             // OPEN | CLOSED | LOCAL
    "priority":          10,
    "enabled":           true
}
Response: 200 OK { "rule_id": "rule-123", "version": 5 }

# Get a specific rule
GET /v1/rules/{rule_id}
Response: 200 OK { ...rule object... }

# List rules for a tenant
GET /v1/rules?tenant_id=tenant-42&page=1&size=50
Response: 200 OK { "rules": [...], "total": 150 }

# Delete a rule
DELETE /v1/rules/{rule_id}
Response: 204 No Content

# Get usage statistics for a client
GET /v1/usage/{client_id}?tenant_id=tenant-42&endpoint=POST+/api/orders&window=60
Response: 200 OK {
    "client_id":  "user-789",
    "endpoint":   "POST /api/orders",
    "limit":      1000,
    "used":       423,
    "remaining":  577,
    "reset_at":   1680000060,
    "window":     60
}
```

### 5.3 Rate Limit Response Headers

Every API response includes these headers, regardless of whether the request was allowed:

```
HTTP/1.1 200 OK                              HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000                      X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 577                   X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1680000060                X-RateLimit-Reset: 1680000060
                                             Retry-After: 37
```

---

## 6. Data Model and Database Selection

### 6.1 Database Selection Rationale

```
┌─────────────────────────┬──────────────────┬──────────────────────────────┐
│       Data Type         │    Storage       │        Rationale             │
├─────────────────────────┼──────────────────┼──────────────────────────────┤
│ Rate limit rules        │ PostgreSQL       │ ACID, relational, durable   │
│ Rate limit counters     │ Redis Cluster    │ In-memory, atomic, TTL      │
│ Allow/deny lists        │ Redis + Postgres │ Redis for fast lookup,      │
│                         │                  │ Postgres for persistence     │
│ Usage analytics         │ ClickHouse/Kafka │ Time-series, high write     │
│ Audit log (rule changes)│ PostgreSQL       │ Append-only, queryable      │
└─────────────────────────┴──────────────────┴──────────────────────────────┘
```

### 6.2 Rules Schema (PostgreSQL)

```sql
CREATE TABLE rate_limit_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(64)   NOT NULL,
    endpoint_pattern VARCHAR(256) NOT NULL,     -- e.g., "POST /api/orders" or "/api/*"
    identifier_type VARCHAR(32)   NOT NULL,     -- USER, API_KEY, IP, GLOBAL
    algorithm       VARCHAR(32)   NOT NULL,     -- TOKEN_BUCKET, SLIDING_WINDOW, etc.
    max_requests    INT           NOT NULL,
    window_seconds  INT           NOT NULL,
    burst_capacity  INT           DEFAULT 0,    -- for token bucket
    fail_mode       VARCHAR(16)   DEFAULT 'OPEN',
    priority        INT           DEFAULT 0,    -- higher = checked first
    enabled         BOOLEAN       DEFAULT TRUE,
    version         INT           DEFAULT 1,
    created_at      TIMESTAMP     DEFAULT NOW(),
    updated_at      TIMESTAMP     DEFAULT NOW(),

    UNIQUE (tenant_id, endpoint_pattern, identifier_type)
);

CREATE INDEX idx_rules_tenant ON rate_limit_rules(tenant_id, enabled);
CREATE INDEX idx_rules_lookup ON rate_limit_rules(tenant_id, endpoint_pattern, enabled);
```

### 6.3 Allow/Deny List Schema

```sql
CREATE TABLE access_lists (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   VARCHAR(64) NOT NULL,
    identifier  VARCHAR(256) NOT NULL,        -- IP, user ID, API key
    list_type   VARCHAR(8) NOT NULL,          -- ALLOW or DENY
    reason      TEXT,
    expires_at  TIMESTAMP,                    -- NULL = permanent
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_access_list ON access_lists(tenant_id, identifier, list_type);
```

### 6.4 Redis Counter Key Design

```
Key format:
  rl:{tenant_id}:{endpoint_hash}:{window}:{identifier}

Examples:
  rl:tenant42:a1b2c3:60:user-789          # 60-second window for user
  rl:tenant42:a1b2c3:3600:user-789         # 1-hour window for user
  rl:tenant42:a1b2c3:60:ip-192.168.1.1     # 60-second window for IP

Token bucket keys:
  tb:{tenant_id}:{endpoint_hash}:{identifier}:tokens    # current token count
  tb:{tenant_id}:{endpoint_hash}:{identifier}:ts         # last refill timestamp

Sliding window log keys:
  swl:{tenant_id}:{endpoint_hash}:{identifier}           # sorted set of timestamps

TTL:
  Each key gets TTL = window_seconds + buffer (e.g., window + 10s)
  Redis automatically evicts expired keys
```

### 6.5 Entity Relationship

```
┌──────────────────┐       ┌───────────────────┐       ┌──────────────────┐
│     Tenant       │       │  RateLimitRule     │       │   AccessList     │
├──────────────────┤       ├───────────────────┤       ├──────────────────┤
│ id           PK  │───┐   │ id            PK  │       │ id           PK  │
│ name             │   │   │ tenant_id     FK  │   ┌───│ tenant_id    FK  │
│ plan_tier        │   ├──►│ endpoint_pattern  │   │   │ identifier       │
│ created_at       │   │   │ identifier_type   │   │   │ list_type        │
└──────────────────┘   │   │ algorithm         │   │   │ reason           │
                       │   │ max_requests      │   │   │ expires_at       │
                       │   │ window_seconds    │   │   └──────────────────┘
                       │   │ burst_capacity    │   │
                       │   │ fail_mode         │   │
                       │   │ priority          │   │
                       │   │ enabled           │   │
                       │   └───────────────────┘   │
                       │                           │
                       └───────────────────────────┘
```

---

## 7. High-Level Architecture

### 7.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                            │
│              (Mobile Apps, Web Apps, Third-Party Integrations)                   │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         EDGE / CDN LAYER                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ CDN PoP #1  │  │ CDN PoP #2  │  │ CDN PoP #3  │  │ CDN PoP #N  │           │
│  │ (coarse     │  │ (coarse     │  │ (coarse     │  │ (coarse     │           │
│  │  limiting)  │  │  limiting)  │  │  limiting)  │  │  limiting)  │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────────┘
          │                │                │                │
          └───────────┬────┴────────────────┴────┬───────────┘
                      │                          │
                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       LOAD BALANCER (L7)                                        │
│              (AWS ALB / Nginx / Envoy / HAProxy)                                │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  App Server #1   │  │  App Server #2   │  │  App Server #N   │
│ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────────┐ │
│ │  Rate Limit  │ │  │ │  Rate Limit  │ │  │ │  Rate Limit  │ │
│ │  Middleware  │ │  │ │  Middleware  │ │  │ │  Middleware  │ │
│ │ ┌──────────┐ │ │  │ │ ┌──────────┐ │ │  │ │ ┌──────────┐ │ │
│ │ │Local Rule│ │ │  │ │ │Local Rule│ │ │  │ │ │Local Rule│ │ │
│ │ │  Cache   │ │ │  │ │ │  Cache   │ │ │  │ │ │  Cache   │ │ │
│ │ └──────────┘ │ │  │ │ └──────────┘ │ │  │ │ └──────────┘ │ │
│ └──────┬───────┘ │  │ └──────┬───────┘ │  │ └──────┬───────┘ │
│        │         │  │        │         │  │        │         │
│  ┌─────┴─────┐   │  │  ┌─────┴─────┐   │  │  ┌─────┴─────┐   │
│  │ App Logic │   │  │  │ App Logic │   │  │  │ App Logic │   │
│  └───────────┘   │  │  └───────────┘   │  │  └───────────┘   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         REDIS CLUSTER (Counters)                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │  Shard #1  │  │  Shard #2  │  │  Shard #3  │  │  Shard #N  │               │
│  │ (primary)  │  │ (primary)  │  │ (primary)  │  │ (primary)  │               │
│  │   ┌────┐   │  │   ┌────┐   │  │   ┌────┐   │  │   ┌────┐   │               │
│  │   │ R  │   │  │   │ R  │   │  │   │ R  │   │  │   │ R  │   │               │
│  │   └────┘   │  │   └────┘   │  │   └────┘   │  │   └────┘   │               │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘               │
│         R = Replica                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │  Rules Service   │  │  Admin Dashboard │  │  Analytics       │              │
│  │  (CRUD + sync)   │  │  (React UI)      │  │  (ClickHouse)   │              │
│  └────────┬─────────┘  └──────────────────┘  └──────────────────┘              │
│           │                                                                     │
│           ▼                                                                     │
│  ┌──────────────────┐                                                          │
│  │  PostgreSQL      │                                                          │
│  │  (Rules Store)   │                                                          │
│  └──────────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Centralized vs Distributed Rate Limiting

```
┌──────────────────────────────────┬───────────────────────────────────┐
│      CENTRALIZED (via Redis)     │     DISTRIBUTED (local only)      │
├──────────────────────────────────┼───────────────────────────────────┤
│                                  │                                   │
│  Server A ──┐                    │  Server A                         │
│             │                    │  ┌─────────────┐                  │
│  Server B ──┼──► Redis ──► count │  │ Local count │  (limit/N per   │
│             │    (single source  │  └─────────────┘   server)        │
│  Server C ──┘     of truth)      │                                   │
│                                  │  Server B                         │
│  Pros:                           │  ┌─────────────┐                  │
│  + Exact global count            │  │ Local count │                  │
│  + Simple mental model           │  └─────────────┘                  │
│                                  │                                   │
│  Cons:                           │  Pros:                            │
│  - Redis is SPOF                 │  + No network hop                 │
│  - Network latency per request   │  + No SPOF                        │
│  - Redis scaling challenges      │  + Ultra-low latency              │
│                                  │                                   │
│  Best for:                       │  Cons:                            │
│  Exact limits, financial APIs    │  - Inaccurate if traffic uneven   │
│                                  │  - Scaling changes break limits   │
│                                  │                                   │
│                                  │  Best for:                        │
│                                  │  Approximate limits, high volume  │
└──────────────────────────────────┴───────────────────────────────────┘
```

### 7.3 Component Breakdown

| Component              | Responsibility                                                | Tech Choice        |
|------------------------|---------------------------------------------------------------|---------------------|
| Rate Limit Middleware  | Intercepts every request, calls rate limit logic              | In-process library  |
| Rule Cache             | Local in-memory cache of rate limit rules                     | Caffeine / Guava    |
| Rate Limit Service     | Core logic: algorithm execution, counter management           | Java / Go library   |
| Redis Cluster          | Distributed counter storage with atomic operations            | Redis 7+ Cluster    |
| Rules Service          | CRUD API for rate limit rules, pushes updates                 | REST microservice   |
| Rules Database         | Persistent storage for rate limit configurations              | PostgreSQL          |
| Admin Dashboard        | UI for managing rules, viewing usage, analytics               | React + REST        |
| Analytics Pipeline     | Collects rate limit events for monitoring and reporting       | Kafka + ClickHouse  |

---

## 8. Deep Dive: Core Components

### 8.1 Rate Limiting Algorithms

#### 8.1.1 Token Bucket

The token bucket is the most commonly used algorithm (used by AWS API Gateway, Stripe).
Tokens are added to a bucket at a fixed rate. Each request consumes a token. If the
bucket is empty, the request is rejected.

**Parameters:**
- `capacity` (bucket size): maximum burst size
- `refill_rate`: tokens added per second

```
Token Bucket Visualization (capacity=5, refill_rate=1/sec)

Time 0s: Bucket full                Time 3s: 3 requests consumed
┌─────────────┐                     ┌─────────────┐
│ ● ● ● ● ●  │ 5/5 tokens          │ ● ●         │ 2/5 tokens
└─────────────┘                     └─────────────┘

Time 5s: Refilled +2 tokens         Time 6s: Burst of 4 requests
┌─────────────┐                     ┌─────────────┐
│ ● ● ● ●    │ 4/5 tokens          │             │ 0/5 tokens
└─────────────┘                     └─────────────┘

Time 7s: Request DENIED!             Time 8s: 1 token refilled
┌─────────────┐                     ┌─────────────┐
│      X      │ 0/5 → REJECTED      │ ●           │ 1/5 token
└─────────────┘                     └─────────────┘
```

**Redis Implementation (Lua Script):**

```lua
-- Token Bucket via Redis Lua script (atomic)
-- KEYS[1] = bucket key
-- ARGV[1] = capacity, ARGV[2] = refill_rate, ARGV[3] = now (ms), ARGV[4] = cost

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens
local elapsed = (now - last_refill) / 1000.0
local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

-- Try to consume
if new_tokens >= cost then
    new_tokens = new_tokens - cost
    redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
    redis.call('PEXPIRE', key, capacity / refill_rate * 1000 + 1000)
    return {1, math.floor(new_tokens)}  -- allowed, remaining
else
    redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
    redis.call('PEXPIRE', key, capacity / refill_rate * 1000 + 1000)
    local wait_time = math.ceil((cost - new_tokens) / refill_rate)
    return {0, 0, wait_time}            -- denied, remaining=0, retry_after
end
```

**Pros:** Allows bursts up to bucket capacity, smooth rate limiting, memory efficient.
**Cons:** Two parameters to tune, harder to reason about exact window counts.

---

#### 8.1.2 Leaky Bucket

The leaky bucket processes requests at a constant rate. Incoming requests are queued,
and the bucket "leaks" (processes) at a fixed rate. If the queue is full, new requests
are dropped.

```
Leaky Bucket (queue_size=5, leak_rate=1/sec)

  Incoming requests (variable rate)
       │ │ │
       ▼ ▼ ▼
  ┌───────────────┐
  │ ┌───┐ ┌───┐  │  Queue (max 5)
  │ │ R3│ │ R2│  │  Requests wait here
  │ └───┘ └───┘  │
  │    ┌───┐     │
  │    │ R1│     │
  │    └───┘     │
  └───────┬──────┘
          │
          ▼  (constant leak rate: 1 req/sec)
     ┌─────────┐
     │ Process │
     │ Request │
     └─────────┘

  State transitions:

  t=0  [R1, R2, R3, R4, R5]   Queue full → R6 DROPPED
  t=1  [R2, R3, R4, R5]       R1 processed, space for 1 more
  t=2  [R3, R4, R5, R6]       R2 processed, R6 now accepted
  t=3  [R4, R5, R6]           R3 processed
```

**Pros:** Constant output rate, prevents bursts entirely.
**Cons:** Slow processing during burst traffic, stale requests if queue is old, not
commonly used for API rate limiting (more common in network traffic shaping).

---

#### 8.1.3 Fixed Window Counter

Divide time into fixed windows (e.g., 60-second intervals). Count requests in the
current window. Reject when count exceeds the limit.

```
Fixed Window (limit=5 per 60s)

 Requests: |||  ||   |    ||||  ||     |||||||
           ─────────────────────────────────────────── time
           │  Window 1  │  Window 2  │  Window 3  │
           │  count: 5  │  count: 6  │  count: 7  │
           │  OK (=5)   │  DENIED(>5)│  DENIED    │
           12:00  12:01   12:01 12:02  12:02 12:03

BOUNDARY BURST PROBLEM:

  Window 1: 12:00-12:01       Window 2: 12:01-12:02
  ┌────────────────────────┐  ┌────────────────────────┐
  │                   |||||│  │|||||                    │
  │            5 req at end│  │5 req at start           │
  └────────────────────────┘  └────────────────────────┘
                         │      │
                         └──┬───┘
                            │
                    10 requests in 2-second
                    span around boundary!
                    (double the intended limit)
```

**Redis Implementation:**

```lua
-- Fixed Window via Redis (simple INCR + EXPIRE)
-- KEYS[1] = base key
-- ARGV[1] = window_seconds, ARGV[2] = limit, ARGV[3] = now

local window = math.floor(tonumber(ARGV[3]) / tonumber(ARGV[1]))
local key = KEYS[1] .. ':' .. window
local count = redis.call('INCR', key)

if count == 1 then
    redis.call('EXPIRE', key, tonumber(ARGV[1]) + 1)
end

if count > tonumber(ARGV[2]) then
    return {0, 0}      -- denied
else
    return {1, tonumber(ARGV[2]) - count}  -- allowed, remaining
end
```

**Pros:** Simple, memory efficient (one counter per window), O(1) operations.
**Cons:** Boundary burst problem allows 2x limit at window edges.

---

#### 8.1.4 Sliding Window Log

Track every request timestamp in a sorted set. For each new request, remove timestamps
outside the window and count remaining entries.

```
Sliding Window Log (limit=5, window=60s)

Current time: 12:01:30

  Sorted Set of timestamps:
  ┌────────────────────────────────────────────────────┐
  │  12:00:45  12:01:02  12:01:15  12:01:22  12:01:28 │  count=5
  └────────────────────────────────────────────────────┘

  Window: [12:00:30, 12:01:30]
         (now - 60s)   (now)

  New request at 12:01:30:
  1. Remove entries before 12:00:30     → none removed
  2. Count entries in window            → 5
  3. 5 >= limit(5)                      → DENIED

  At 12:01:46 (12:00:45 falls out of window):
  1. Remove entries before 12:00:46     → remove 12:00:45
  2. Count entries in window            → 4
  3. 4 < limit(5)                       → ALLOWED, add 12:01:46
```

**Redis Implementation:**

```lua
-- Sliding Window Log via Redis Sorted Set
-- KEYS[1] = key, ARGV[1] = now_ms, ARGV[2] = window_ms, ARGV[3] = limit

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current entries
local count = redis.call('ZCARD', key)

if count < limit then
    -- Add new entry with timestamp as score and unique member
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
    redis.call('PEXPIRE', key, window + 1000)
    return {1, limit - count - 1}  -- allowed, remaining
else
    redis.call('PEXPIRE', key, window + 1000)
    return {0, 0}                  -- denied
end
```

**Pros:** Exact counting, no boundary problems.
**Cons:** High memory usage (stores every timestamp), O(N) cleanup per request.

---

#### 8.1.5 Sliding Window Counter (Recommended)

A hybrid approach that combines the simplicity of fixed windows with the accuracy of
sliding windows. Uses weighted counters from the current and previous windows.

```
Sliding Window Counter (limit=10, window=60s)

  Previous Window          Current Window
  (12:00:00 - 12:01:00)    (12:01:00 - 12:02:00)
  ┌──────────────────────┐  ┌──────────────────────┐
  │  count_prev = 8      │  │  count_curr = 3      │
  └──────────────────────┘  └──────────────────────┘
                                     ▲
                                     │ current time: 12:01:20
                                     │ (20s into 60s window)

  Weighted count formula:
  ─────────────────────────────────────────────────
  weighted = count_prev * (1 - elapsed/window) + count_curr
           = 8 * (1 - 20/60) + 3
           = 8 * 0.667 + 3
           = 5.33 + 3
           = 8.33

  8.33 < limit(10) → ALLOWED

  Visual of the sliding window:
         ◄──── 60 seconds ────►
  ──────┬───────────────────────┬──────
        │/////////////////////  │
        │  40s of prev window   │ 20s of curr window
        │  weight = 40/60       │ weight = 1.0
        │  = 0.667              │
  ──────┴───────────────────────┴──────
     12:00:20              12:01:20 (now)
```

**Redis Implementation:**

```lua
-- Sliding Window Counter
-- KEYS[1] = base key
-- ARGV[1] = window_sec, ARGV[2] = limit, ARGV[3] = now_sec

local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local curr_window = math.floor(now / window) * window
local prev_window = curr_window - window
local elapsed = now - curr_window

local curr_key = KEYS[1] .. ':' .. curr_window
local prev_key = KEYS[1] .. ':' .. prev_window

local curr_count = tonumber(redis.call('GET', curr_key) or '0')
local prev_count = tonumber(redis.call('GET', prev_key) or '0')

local weight = 1 - (elapsed / window)
local weighted = prev_count * weight + curr_count

if weighted < limit then
    redis.call('INCR', curr_key)
    redis.call('EXPIRE', curr_key, window * 2 + 1)
    return {1, math.floor(limit - weighted - 1)}
else
    return {0, 0}
end
```

**Pros:** Memory efficient (2 counters), O(1) operations, no boundary burst problem, good accuracy.
**Cons:** Approximation (not exact), assumes uniform request distribution in previous window.

---

#### 8.1.6 Algorithm Comparison

```
┌──────────────────┬───────────┬──────────┬──────────┬────────────┬───────────────┐
│    Algorithm     │  Memory   │ Accuracy │ Burst    │ Complexity │ Best For      │
│                  │  per key  │          │ Handling │            │               │
├──────────────────┼───────────┼──────────┼──────────┼────────────┼───────────────┤
│ Token Bucket     │  O(1)     │ Good     │ Allows   │ Medium     │ API gateways  │
│                  │  ~32 B    │          │ bursts   │            │ (AWS, Stripe) │
├──────────────────┼───────────┼──────────┼──────────┼────────────┼───────────────┤
│ Leaky Bucket     │  O(N)     │ Exact    │ Smooths  │ Medium     │ Traffic       │
│                  │  ~queue   │          │ output   │            │ shaping       │
├──────────────────┼───────────┼──────────┼──────────┼────────────┼───────────────┤
│ Fixed Window     │  O(1)     │ Poor     │ 2x at    │ Simple     │ Simple use    │
│                  │  ~16 B    │          │ boundary │            │ cases         │
├──────────────────┼───────────┼──────────┼──────────┼────────────┼───────────────┤
│ Sliding Window   │  O(N)     │ Exact    │ None     │ High       │ When exact    │
│ Log              │  ~req*16B │          │          │            │ count needed  │
├──────────────────┼───────────┼──────────┼──────────┼────────────┼───────────────┤
│ Sliding Window   │  O(1)     │ ~99.7%   │ Minimal  │ Simple     │ Best default  │
│ Counter          │  ~32 B    │          │          │            │ choice        │
└──────────────────┴───────────┴──────────┴──────────┴────────────┴───────────────┘

Recommendation: Use Sliding Window Counter as default, Token Bucket when burst
control is needed, Sliding Window Log only for financial/compliance use cases.
```

---

### 8.2 Distributed Counter Management

#### 8.2.1 Atomic Operations with Redis

All counter operations must be atomic to avoid race conditions. Redis provides two
mechanisms: single atomic commands and Lua scripts.

```
Race Condition WITHOUT atomicity:

  Server A                    Redis                    Server B
     │                          │                          │
     │── GET counter ──────────►│                          │
     │◄── return 99 ───────────│                          │
     │                          │◄── GET counter ──────────│
     │                          │── return 99 ────────────►│
     │                          │                          │
     │   99 < 100 → ALLOW      │                          │  99 < 100 → ALLOW
     │                          │                          │
     │── INCR counter ────────►│                          │
     │◄── return 100 ──────────│                          │
     │                          │◄── INCR counter ────────│
     │                          │── return 101 ───────────►│
     │                          │                          │
     Result: counter = 101, but limit was 100!
             One request should have been denied.

  SOLUTION: Lua script runs atomically on Redis

  Server A                    Redis (Lua)              Server B
     │                          │                          │
     │── EVAL lua_script ─────►│                          │
     │                          │ GET → 99                 │
     │                          │ 99 < 100 → ALLOW        │
     │                          │ INCR → 100               │
     │◄── return ALLOWED ──────│                          │
     │                          │◄── EVAL lua_script ──────│
     │                          │ GET → 100                │
     │                          │ 100 >= 100 → DENY        │
     │                          │── return DENIED ────────►│
     │                          │                          │
     Result: Correct! Exactly 100 requests allowed.
```

#### 8.2.2 Pipeline Optimization

For multiple rate limit checks (e.g., per-second AND per-minute), use Redis pipelines:

```
Without pipeline (3 round trips):        With pipeline (1 round trip):
┌──────────┐      ┌───────┐              ┌──────────┐      ┌───────┐
│  Server  │      │ Redis │              │  Server  │      │ Redis │
└────┬─────┘      └───┬───┘              └────┬─────┘      └───┬───┘
     │ check /sec     │                       │ PIPELINE       │
     │───────────────►│                       │───────────────►│
     │◄───────────────│                       │  check /sec    │
     │ check /min     │                       │  check /min    │
     │───────────────►│                       │  check /hour   │
     │◄───────────────│                       │◄───────────────│
     │ check /hour    │                       │ 3 results      │
     │───────────────►│                       │                │
     │◄───────────────│               Total: 1 round trip
     │                │               Latency: ~0.3ms
Total: 3 round trips
Latency: ~0.9ms
```

#### 8.2.3 Clock Synchronization

In a distributed system, servers have slightly different clocks. This matters for
window-based algorithms.

```
Problem: Clock skew between servers

  Server A (clock: 12:01:00.000)    Server B (clock: 12:00:59.950)
  ┌─────────────────────────────┐   ┌─────────────────────────────┐
  │ Window 2 starts at 12:01:00 │   │ Still in Window 1           │
  │ curr_count = 0              │   │ curr_count = 99             │
  │ NEW request → count = 1    │   │ NEW request → count = 100  │
  └─────────────────────────────┘   └─────────────────────────────┘

  Server A thinks it's a new window (count=1)
  Server B thinks it's the same window (count=100)
  Both write to different Redis keys!

Solutions:
  1. Use Redis server time: EVAL with redis.call('TIME')
     → All decisions use the same clock
  2. Use NTP: Keep servers within 10ms of each other
     → Acceptable for most rate limiting use cases
  3. Use sequence numbers instead of timestamps
     → Eliminates clock dependency entirely
```

**Recommended approach:** Use Redis server time via Lua scripts. This ensures all
rate limit decisions reference the same clock, regardless of app server clock skew.

---

### 8.3 Rule Engine

#### 8.3.1 Rule Matching

When a request arrives, the rule engine must find the most specific matching rule.

```
Rule Priority Matching:

  Request: POST /api/v2/orders from user-789, tenant-42

  Rule evaluation order (highest priority first):

  Priority 100: tenant-42 + POST /api/v2/orders + user-789    ← EXACT match
  Priority  80: tenant-42 + POST /api/v2/orders + *           ← endpoint match
  Priority  60: tenant-42 + POST /api/v2/*       + *           ← wildcard path
  Priority  40: tenant-42 + POST /api/**          + *           ← glob pattern
  Priority  20: tenant-42 + *                     + *           ← tenant default
  Priority   0: *          + *                     + *           ← global default

  First matching rule wins.
```

#### 8.3.2 Rule Cache and Hot Reload

Rules are stored in PostgreSQL but cached locally for performance. Changes are
propagated in near real-time.

```
Rule Update Flow:

  Admin Dashboard                Rules Service             App Servers
       │                              │                         │
       │── PUT /v1/rules/123 ────────►│                         │
       │                              │── Write to Postgres ───►│
       │                              │                         │
       │                              │── Publish to Redis ────►│
       │                              │   Pub/Sub channel       │
       │                              │   "rules:updated"       │
       │                              │                         │
       │                              │           ┌─────────────┤
       │                              │           │ Subscriber  │
       │                              │           │ receives    │
       │                              │           │ notification│
       │                              │           │             │
       │                              │           │ Invalidate  │
       │                              │           │ local cache │
       │                              │           │             │
       │                              │           │ Fetch new   │
       │                              │           │ rules from  │
       │                              │           │ Postgres    │
       │                              │           └─────────────┤
       │                              │                         │
       │◄── 200 OK ──────────────────│                         │

  Propagation time: < 1 second (Pub/Sub) + cache TTL fallback (30s)
```

#### 8.3.3 Rule Conflict Resolution

```
When multiple rules match, apply these resolution rules:

  1. Most specific endpoint wins over wildcard
     POST /api/v2/orders  >  POST /api/v2/*  >  POST /**  >  *

  2. Most specific identifier wins
     user:user-789  >  apikey:key-456  >  ip:10.0.0.1  >  global

  3. Higher priority number wins (explicit admin override)
     priority: 100  >  priority: 50

  4. Shortest window wins (if same priority)
     10 req/sec  evaluated before  1000 req/min

  5. Most restrictive limit applies when ambiguous
     If two rules match with same priority, the lower limit wins
```

---

### 8.4 Edge Rate Limiting vs Centralized

#### 8.4.1 Edge Rate Limiting

Rate limiting at the CDN/load balancer layer, before traffic reaches application servers.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      EDGE RATE LIMITING                             │
│                                                                     │
│  Client ──► CDN PoP (edge rate limiter) ──► Origin Server           │
│                  │                                                  │
│                  ├─ Local counter per PoP                            │
│                  ├─ No external dependency (no Redis call)           │
│                  ├─ Limit = global_limit / num_pops (approximate)    │
│                  └─ Decision in < 0.1ms                              │
│                                                                     │
│  Example: Cloudflare Rate Limiting                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│  │ PoP NYC    │  │ PoP London │  │ PoP Tokyo  │                    │
│  │ limit: 33  │  │ limit: 33  │  │ limit: 34  │   Total: 100/min  │
│  │ count: 20  │  │ count: 15  │  │ count: 5   │   Used:  40/min   │
│  └────────────┘  └────────────┘  └────────────┘                    │
│                                                                     │
│  Problem: User sending from NYC uses up NYC's quota but             │
│  Tokyo's quota is unused → total effective limit varies             │
└─────────────────────────────────────────────────────────────────────┘
```

#### 8.4.2 Centralized Rate Limiting

Rate limiting at the application layer, using a shared counter store (Redis).

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CENTRALIZED RATE LIMITING                         │
│                                                                     │
│  Client ──► LB ──► App Server ──► Redis ──► Decision                │
│                         │            │                               │
│                         │            ├─ Single source of truth       │
│                         │            ├─ Exact global count           │
│                         │            └─ Adds ~0.5ms latency          │
│                         │                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│  │ App Srv 1  │  │ App Srv 2  │  │ App Srv 3  │                    │
│  │            │  │            │  │            │                    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                    │
│        │               │               │                            │
│        └───────────────┼───────────────┘                            │
│                        │                                             │
│                        ▼                                             │
│                 ┌────────────┐                                      │
│                 │   Redis    │  count: 40/100                       │
│                 │  (global)  │  EXACT count                         │
│                 └────────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 8.4.3 Hybrid Approach (Recommended)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HYBRID RATE LIMITING                              │
│                                                                     │
│  Layer 1 (Edge): Coarse-grained, approximate                       │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  CDN/LB: IP-based rate limiting                        │        │
│  │  - 10,000 req/min per IP (DDoS protection)             │        │
│  │  - Local counters, no external call                    │        │
│  │  - Catches 90% of abuse                                │        │
│  └────────────────────────┬───────────────────────────────┘        │
│                           │ passes ~10% of edge-limited traffic    │
│                           ▼                                         │
│  Layer 2 (App): Fine-grained, exact                                │
│  ┌────────────────────────────────────────────────────────┐        │
│  │  App Server: User/API-key rate limiting via Redis      │        │
│  │  - 100 req/min per user per endpoint                   │        │
│  │  - Exact counting via Redis Lua scripts                │        │
│  │  - Handles multi-tenant, per-endpoint rules            │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
│  Benefits:                                                          │
│  - Edge catches bulk abuse (no Redis load)                         │
│  - App layer handles precise per-user limiting                      │
│  - Redis only sees "good" traffic (reduced load by 90%)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning and Sharding

### 9.1 Redis Cluster Sharding

Redis Cluster automatically partitions data across shards using hash slots (16,384 slots).

```
Redis Cluster Topology (6 nodes: 3 primary + 3 replica)

  ┌─────────────────────────────────────────────────────────────┐
  │                    Redis Cluster                             │
  │                                                             │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
  │  │  Primary #1  │  │  Primary #2  │  │  Primary #3  │      │
  │  │ Slots: 0-    │  │ Slots: 5462- │  │ Slots: 10923-│      │
  │  │        5461  │  │        10922 │  │        16383 │      │
  │  │              │  │              │  │              │      │
  │  │ Keys:        │  │ Keys:        │  │ Keys:        │      │
  │  │ tenant1:*    │  │ tenant2:*    │  │ tenant3:*    │      │
  │  │ tenantA:*    │  │ tenantB:*    │  │ tenantC:*    │      │
  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
  │         │                 │                 │               │
  │         ▼                 ▼                 ▼               │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
  │  │  Replica #1  │  │  Replica #2  │  │  Replica #3  │      │
  │  │ (of Prim #1) │  │ (of Prim #2) │  │ (of Prim #3) │      │
  │  └──────────────┘  └──────────────┘  └──────────────┘      │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘

Key distribution using hash tags:
  rl:{tenant42}:endpoint:window:user  → hash("tenant42") → slot 8234 → Primary #2

  Hash tags {tenant42} ensure all keys for the same tenant land on the
  same shard, enabling Lua scripts to operate on multiple keys atomically.
```

### 9.2 Sharding Strategy

```
┌───────────────────────────────────────────────────────────────────┐
│                    SHARDING STRATEGIES                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Strategy 1: Shard by client_id (Recommended)                     │
│  ─────────────────────────────────────────────                    │
│  Key: rl:{client_id_hash}:endpoint:window                         │
│  Pros: All limits for one client on same shard                    │
│  Cons: Hot clients create hot shards                              │
│                                                                   │
│  Strategy 2: Shard by tenant_id                                   │
│  ───────────────────────────────                                  │
│  Key: rl:{tenant_id}:endpoint:window:client                       │
│  Pros: Tenant isolation, Lua scripts work                         │
│  Cons: Large tenants = hot shards                                 │
│                                                                   │
│  Strategy 3: Shard by composite key                               │
│  ──────────────────────────────────                               │
│  Key: rl:{tenant_id:endpoint_hash}:window:client                  │
│  Pros: Better distribution, avoids mega-tenant hotspots           │
│  Cons: Multi-key Lua scripts won't work across hash tags          │
│                                                                   │
│  Recommendation: Strategy 2 for multi-tenant SaaS (tenant         │
│  isolation + Lua compatibility), Strategy 1 for single-tenant.    │
└───────────────────────────────────────────────────────────────────┘
```

### 9.3 Handling Hot Shards

```
Problem: A viral API key generates 1M req/sec, overwhelming one shard.

  Solution 1: Local rate limiting for hot keys
  ┌────────────────────────────────────────────┐
  │  App Server detects hot key (>1K req/sec)  │
  │  → Switch to local counter                 │
  │  → Sync with Redis every 100ms             │
  │  → Accept ~N% over-counting (N = servers)  │
  └────────────────────────────────────────────┘

  Solution 2: Key splitting
  ┌────────────────────────────────────────────┐
  │  Instead of 1 key for a hot client:        │
  │  rl:{tenant}:endpoint:window:user          │
  │                                            │
  │  Split into K sub-keys:                    │
  │  rl:{tenant}:endpoint:window:user:0        │
  │  rl:{tenant}:endpoint:window:user:1        │
  │  rl:{tenant}:endpoint:window:user:2        │
  │  ...                                       │
  │  rl:{tenant}:endpoint:window:user:K-1      │
  │                                            │
  │  Server picks sub-key = hash(server_id)%K  │
  │  Limit per sub-key = global_limit / K      │
  │  Keys distribute across K different shards │
  └────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

### 10.1 Rule Caching

```
┌─────────────────────────────────────────────────────────────────────┐
│                       RULE CACHE HIERARCHY                          │
│                                                                     │
│  Level 1: In-Process Cache (Caffeine/Guava)                        │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │  Capacity: 10,000 rules                                   │      │
│  │  TTL: 30 seconds                                          │      │
│  │  Lookup: O(1) hash map, ~10ns                              │      │
│  │  Invalidation: Pub/Sub notification + TTL expiry           │      │
│  │                                                           │      │
│  │  Cache key: (tenant_id, endpoint, identifier_type)        │      │
│  │  Cache value: RateLimitRule object                         │      │
│  └───────────────────────────────┬───────────────────────────┘      │
│                                  │ MISS                              │
│                                  ▼                                   │
│  Level 2: Redis (shared cache)                                      │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │  All rules replicated to Redis for fast cross-server      │      │
│  │  access. TTL: 5 minutes.                                  │      │
│  │  Lookup: ~0.3ms network round trip                         │      │
│  └───────────────────────────────┬───────────────────────────┘      │
│                                  │ MISS                              │
│                                  ▼                                   │
│  Level 3: PostgreSQL (source of truth)                              │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │  Full rules table. Lookup: ~2-5ms.                        │      │
│  │  Only hit on cold start or cache miss cascade.            │      │
│  └───────────────────────────────────────────────────────────┘      │
│                                                                     │
│  Hit rates (expected):                                              │
│  L1: 99.5%  │  L2: 0.4%  │  L3: 0.1%                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 Counter Approximation with Local Caching

For extremely high throughput, avoid calling Redis on every request by batching
counter updates locally.

```
Local Counter Batching:

  ┌──────────────────────────────────────────┐
  │  App Server (in-memory)                   │
  │                                           │
  │  local_count = 0                          │
  │  last_sync_count = 850  (from Redis)      │
  │  limit = 1000                             │
  │                                           │
  │  On request:                              │
  │    local_count++                           │
  │    estimated_total = last_sync_count       │
  │                    + local_count            │
  │    if estimated_total > limit → DENY       │
  │                                           │
  │  Every 100ms or 50 local requests:        │
  │    sync with Redis:                        │
  │    redis_count = INCRBY key local_count   │
  │    last_sync_count = redis_count           │
  │    local_count = 0                         │
  └──────────────────────────────────────────┘

  Trade-off:
  - Reduces Redis calls by 50x (batch of 50)
  - Introduces counting error of up to:
    num_servers * batch_size = 20 * 50 = 1000 extra requests
  - Acceptable for high-limit rules (10,000/min)
  - NOT acceptable for low-limit rules (10/min)
```

### 10.3 Cache Warm-Up

```
On server startup:

  1. Fetch all active rules from PostgreSQL
     SELECT * FROM rate_limit_rules WHERE enabled = true;
     → ~150K rules, takes ~500ms

  2. Populate local cache (Caffeine)
     → All rules available immediately, no cold-start misses

  3. Subscribe to Redis Pub/Sub for rule updates
     → Receive real-time invalidations

  4. Start accepting traffic
     → First requests don't need to hit Postgres

  Startup time: ~1 second (acceptable for rolling deploys)
```

---

## 11. Replication and Consistency

### 11.1 Counter Consistency Model

Rate limiting uses **eventual consistency** for counters. This is an intentional design
decision: strong consistency would require distributed locks, adding unacceptable latency.

```
┌─────────────────────────────────────────────────────────────────────┐
│              CONSISTENCY SPECTRUM FOR RATE LIMITING                  │
│                                                                     │
│  Strong                                              Eventual       │
│  Consistency                                         Consistency    │
│  ◄─────────────────────────────────────────────────────────────►    │
│  │                                                           │      │
│  │  Distributed                 Redis        Sliding Window  │      │
│  │  Lock per       Single      Async         Counter with    │      │
│  │  counter        Redis       Replication   local batching  │      │
│  │                 (no                                       │      │
│  │  +5ms latency   replication) +0.5ms      +0ms overhead   │      │
│  │  per request                 latency      (best effort)  │      │
│  │                                                          │      │
│  │  Never          ~exact      <0.1%         ~1-5%          │      │
│  │  over-count     counting    over-count    over-count     │      │
│  │                                                          │      │
│  │  Financial      Most prod   Multi-DC     Very high       │      │
│  │  APIs           systems     setups       throughput      │      │
│  │                                                          │      │
│  │                    ▲                                      │      │
│  │                    │ RECOMMENDED                          │      │
│  │                    │ for most use cases                   │      │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 Multi-Data-Center Consistency

```
Multi-DC Rate Limiting Options:

  Option A: Shared global counter (high latency)
  ┌──────────┐         ┌──────────┐
  │  DC-East │         │  DC-West │
  │  App Svr ├────────►│  Redis   │   Cross-DC latency: 30-80ms
  │          │         │  (primary)│   Too slow for rate limiting
  └──────────┘         └──────────┘

  Option B: Independent counters (inaccurate)
  ┌──────────┐         ┌──────────┐
  │  DC-East │         │  DC-West │
  │  App Svr │         │  App Svr │
  │  Redis   │         │  Redis   │   Each DC: limit/2
  │  limit:50│         │  limit:50│   Problem: user in one DC
  └──────────┘         └──────────┘   wastes other DC's quota

  Option C: Async sync with local counters (RECOMMENDED)
  ┌──────────────────┐         ┌──────────────────┐
  │     DC-East      │         │     DC-West      │
  │  ┌────────────┐  │         │  ┌────────────┐  │
  │  │ Local Redis│◄─┼────────►│─►│ Local Redis│  │
  │  │ limit: 100 │  │  async  │  │ limit: 100 │  │
  │  │            │  │  sync   │  │            │  │
  │  │ count: 40  │  │ (1-5s)  │  │ count: 30  │  │
  │  └────────────┘  │         │  └────────────┘  │
  │                  │         │                  │
  │  Effective count:│         │                  │
  │  local + remote  │         │                  │
  │  = 40 + 30 = 70  │         │                  │
  └──────────────────┘         └──────────────────┘

  Sync mechanism:
  - Every 1-5 seconds, each DC publishes its local delta
  - Other DCs adjust their view of the global count
  - Worst-case over-count: num_DCs * sync_interval * request_rate
  - Example: 3 DCs * 5s * 100 req/s = 1500 extra requests (1.5% of 100K limit)
```

### 11.3 Rule Consistency

```
Rules propagation (eventually consistent):

  Admin updates rule ──► PostgreSQL ──► Change event
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                        App Server 1    App Server 2    App Server 3
                        (sees update    (sees update    (sees update
                         at t+200ms)     at t+500ms)     at t+800ms)

  During the propagation window (up to ~1 second):
  - Some servers use old rule, others use new rule
  - This is acceptable: rule changes are rare and not latency-sensitive
  - Safety measure: version number on rules prevents reverting to older versions
```

---

## 12. Fault Tolerance and Failure Handling

### 12.1 Failure Scenarios

```
┌─────────────────────────┬─────────────────────────────────────────────────┐
│     Failure Scenario    │              Handling Strategy                  │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Redis primary down      │ Automatic failover to replica (Redis Sentinel  │
│                         │ or Cluster). Failover time: 5-30 seconds.      │
│                         │ During failover: use fail mode (open/closed).  │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Redis cluster partially │ Keys on failed shard unavailable. Other shards │
│ down (1 shard)          │ still work. Affected keys use fail mode.       │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Network partition       │ App servers can't reach Redis. Fall back to    │
│ (app ↔ Redis)          │ local in-memory counters with reduced limits.  │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ PostgreSQL down         │ Rules already cached locally. No impact on     │
│                         │ rate limiting. Rule updates queued until back.  │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ App server crash        │ Stateless middleware. New server picks up      │
│                         │ traffic immediately. Counters in Redis.        │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Clock drift             │ Use Redis server time in Lua scripts.          │
│                         │ App server clocks irrelevant for counting.     │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Counter data loss       │ Counters are ephemeral (TTL-based). Loss       │
│ (Redis restart)         │ means some requests bypass limits temporarily. │
│                         │ Counters rebuild within one window period.     │
└─────────────────────────┴─────────────────────────────────────────────────┘
```

### 12.2 Circuit Breaker for Redis

```
Circuit Breaker State Machine:

  ┌──────────┐      failure_threshold       ┌──────────┐
  │          │      exceeded (5 failures    │          │
  │  CLOSED  ├─────────in 10 seconds)──────►│   OPEN   │
  │ (normal) │                              │ (bypass  │
  │          │◄─────────────────────────────┤  Redis)  │
  └──────┬───┘      success in              └────┬─────┘
         │          half-open                    │
         │                                       │  after timeout
         │          ┌──────────┐                 │  (30 seconds)
         │          │          │                 │
         └──────────┤HALF-OPEN │◄────────────────┘
                    │ (probe   │
                    │  Redis)  │
                    └──────────┘

  CLOSED:    Normal operation, all requests go to Redis
  OPEN:      Redis calls skipped, use fail mode (open/closed/local)
  HALF-OPEN: Send 1 probe request to Redis every 5 seconds
             If success → CLOSED, if failure → OPEN

  Implementation:
  ┌─────────────────────────────────────────────────────────────┐
  │  class RateLimiterWithCircuitBreaker {                       │
  │      CircuitBreaker cb = new CircuitBreaker(                 │
  │          failureThreshold: 5,                                │
  │          timeout: 30s,                                       │
  │          halfOpenProbes: 1                                   │
  │      );                                                      │
  │                                                             │
  │      RateLimitResponse check(request) {                      │
  │          if (cb.isOpen()) {                                  │
  │              return applyFailMode(request.rule.failMode);    │
  │          }                                                   │
  │          try {                                               │
  │              result = redis.eval(luaScript, ...);            │
  │              cb.recordSuccess();                              │
  │              return result;                                   │
  │          } catch (RedisException e) {                        │
  │              cb.recordFailure();                              │
  │              return applyFailMode(request.rule.failMode);    │
  │          }                                                   │
  │      }                                                       │
  │  }                                                           │
  └─────────────────────────────────────────────────────────────┘
```

### 12.3 Local Fallback Counters

```
When Redis is unavailable, fall back to local in-memory counters:

  Normal operation:
  ┌──────────────┐      ┌──────────────┐
  │  App Server  ├─────►│    Redis     │  Global count
  └──────────────┘      └──────────────┘

  Redis down (circuit breaker OPEN):
  ┌──────────────────────────────────────────────────┐
  │  App Server                                       │
  │  ┌──────────────────────────────────────────────┐ │
  │  │  Local ConcurrentHashMap                      │ │
  │  │  Key: "tenant42:orders:60:user789"           │ │
  │  │  Value: AtomicLong(count) + expiry            │ │
  │  │                                               │ │
  │  │  Adjusted limit = global_limit / num_servers  │ │
  │  │  Example: 1000/min / 20 servers = 50/min     │ │
  │  │                                               │ │
  │  │  Problem: Traffic may not be evenly distributed│ │
  │  │  across servers, so limits are approximate.   │ │
  │  └──────────────────────────────────────────────┘ │
  │                                                   │
  │  When Redis recovers:                              │
  │  1. Circuit breaker moves to HALF-OPEN             │
  │  2. Probe succeeds → CLOSED                        │
  │  3. Local counters discarded                       │
  │  4. Fresh Redis counters used                      │
  └──────────────────────────────────────────────────┘
```

---

## 13. Scalability

### 13.1 Horizontal Scaling

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SCALING DIMENSIONS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  App Server Tier (stateless - scale freely)                        │
│  ┌──────┐ ┌──────┐ ┌──────┐        ┌──────┐ ┌──────┐ ┌──────┐    │
│  │ AS-1 │ │ AS-2 │ │ AS-3 │  ────► │ AS-1 │ │ AS-2 │ │ AS-3 │    │
│  └──────┘ └──────┘ └──────┘        │ AS-4 │ │ AS-5 │ │ AS-6 │    │
│                                     └──────┘ └──────┘ └──────┘    │
│  3 servers, 1M req/sec              6 servers, 2M req/sec          │
│                                                                     │
│  Redis Tier (add shards for more throughput)                       │
│  ┌──────────┐ ┌──────────┐         ┌──────────┐ ┌──────────┐      │
│  │ Shard 1  │ │ Shard 2  │  ────►  │ Shard 1  │ │ Shard 2  │      │
│  │ 200K/sec │ │ 200K/sec │         │ Shard 3  │ │ Shard 4  │      │
│  └──────────┘ └──────────┘         └──────────┘ └──────────┘      │
│  400K ops/sec total                 800K ops/sec total              │
│                                                                     │
│  Rule Database (rarely the bottleneck)                             │
│  ┌──────────┐                      ┌──────────┐ ┌──────────┐      │
│  │ Primary  │            ────►     │ Primary  │ │ Read     │      │
│  └──────────┘                      └──────────┘ │ Replicas │      │
│  150K rules, 10 QPS                             └──────────┘      │
│                                     150K rules, 100 QPS            │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.2 Performance Characteristics

```
Operation Complexity:

  ┌──────────────────────────────┬──────────┬────────────┐
  │        Operation             │ Time     │ Space      │
  ├──────────────────────────────┼──────────┼────────────┤
  │ Rule lookup (local cache)    │ O(1)     │ O(R)       │
  │ Rule lookup (Redis)          │ O(1)     │ O(R)       │
  │ Token bucket check           │ O(1)     │ O(1)/key   │
  │ Fixed window check           │ O(1)     │ O(1)/key   │
  │ Sliding window counter       │ O(1)     │ O(1)/key   │
  │ Sliding window log           │ O(N)     │ O(N)/key   │
  │ Allow/deny list check        │ O(1)     │ O(L)       │
  │ Redis Lua script             │ O(1)*    │ O(1)       │
  └──────────────────────────────┴──────────┴────────────┘
  R = number of rules, L = list size, N = requests in window
  * O(1) assuming constant-time Redis operations

Latency Breakdown (p99):
  ┌──────────────────────────────────────────────────────┐
  │  Rule cache lookup:          0.01 ms                 │
  │  Allow/deny list check:      0.01 ms                 │
  │  Network to Redis:           0.20 ms                 │
  │  Redis Lua script exec:      0.05 ms                 │
  │  Network from Redis:         0.20 ms                 │
  │  Response header injection:  0.01 ms                 │
  │  ─────────────────────────────────────               │
  │  Total overhead:             0.48 ms (< 1ms target)  │
  └──────────────────────────────────────────────────────┘
```

### 13.3 Scaling Bottlenecks and Mitigations

```
┌─────────────────────┬──────────────────────┬───────────────────────────┐
│ Bottleneck          │ Symptom              │ Mitigation                │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ Redis throughput    │ High latency on      │ Add more shards, use      │
│                     │ Redis ops            │ local batching            │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ Redis memory        │ OOM errors           │ Shorter TTLs, fewer       │
│                     │                      │ windows, eviction policy  │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ Network (app↔Redis)│ Increased latency    │ Pipeline, connection pool │
│                     │                      │ colocate Redis with app   │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ Hot keys (viral     │ One shard overloaded │ Key splitting, local      │
│ user/endpoint)      │                      │ counter for hot keys      │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ Rule evaluation     │ High CPU on app      │ Precompile patterns,      │
│ (regex matching)    │ servers              │ use hash lookup           │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ Pub/Sub fan-out     │ Slow rule updates    │ Batch updates, use        │
│ (many subscribers)  │                      │ polling with ETag         │
└─────────────────────┴──────────────────────┴───────────────────────────┘
```

---

## 14. Monitoring and Observability

### 14.1 Key Metrics

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MONITORING DASHBOARD                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  REQUEST METRICS                                                    │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Total requests checked:     10,234,567 / sec           │       │
│  │  Requests allowed:            9,876,543 / sec (96.5%)   │       │
│  │  Requests denied (429):         358,024 / sec (3.5%)    │       │
│  │  Requests bypassed (allow list):  12,345 / sec          │       │
│  │  Requests blocked (deny list):     1,234 / sec          │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  LATENCY METRICS                                                    │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Rate limit check p50:        0.15 ms                   │       │
│  │  Rate limit check p99:        0.48 ms                   │       │
│  │  Rate limit check p999:       1.20 ms                   │       │
│  │  Redis round trip p50:        0.12 ms                   │       │
│  │  Redis round trip p99:        0.35 ms                   │       │
│  │  Rule cache hit rate:         99.7%                     │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  REDIS CLUSTER METRICS                                              │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Total ops/sec:               8,234,567                 │       │
│  │  Memory usage:                6.2 GB / 10 GB (62%)      │       │
│  │  Connected clients:           1,200                     │       │
│  │  Key count:                   45,678,901                │       │
│  │  Evicted keys:                0 / sec                   │       │
│  │  Cluster health:              OK (all slots covered)    │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  ACCURACY METRICS                                                   │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Counter accuracy drift:      0.3% (target < 1%)       │       │
│  │  False allows (over-count):   ~12 / million requests    │       │
│  │  False denies (under-count):  ~3 / million requests     │       │
│  │  Clock skew (max):            8ms across fleet          │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  ALERTING THRESHOLDS                                                │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  WARN:  Denial rate > 5%  (potential abuse or bad rule) │       │
│  │  WARN:  Redis p99 > 1ms   (network/capacity issue)     │       │
│  │  CRIT:  Redis unavailable (circuit breaker triggered)   │       │
│  │  CRIT:  Rule cache hit rate < 95%                       │       │
│  │  WARN:  Counter drift > 2%                              │       │
│  └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.2 Logging Strategy

```
Log levels for rate limiting events:

  DEBUG: Every rate limit check (only in dev/staging)
         {"level":"DEBUG","client":"user-789","endpoint":"POST /orders",
          "count":45,"limit":100,"remaining":55,"allowed":true}

  INFO:  Rate limit rule changes
         {"level":"INFO","action":"RULE_UPDATED","rule_id":"rule-123",
          "old_limit":100,"new_limit":200,"updated_by":"admin@co.com"}

  WARN:  Client approaching limit (> 80% used)
         {"level":"WARN","client":"user-789","endpoint":"POST /orders",
          "count":85,"limit":100,"pct_used":85}

  ERROR: Redis connection failures, circuit breaker state changes
         {"level":"ERROR","event":"CIRCUIT_BREAKER_OPEN",
          "redis_shard":"shard-3","fail_mode":"OPEN","duration":"30s"}

  Sampling: In production, log 1% of checks (DEBUG), 100% of denials (INFO)
```

### 14.3 Distributed Tracing Integration

```
  Request trace with rate limiting span:

  ┌─ Request: POST /api/orders ────────────────────────────────────────────┐
  │                                                                        │
  │  ┌─ span: http.request ──────────────────────────────────────────────┐ │
  │  │                                                                    │ │
  │  │  ┌─ span: ratelimit.check (0.45ms) ─────────────────────────────┐ │ │
  │  │  │  tags:                                                        │ │ │
  │  │  │    ratelimit.key = "tenant42:orders:60:user789"               │ │ │
  │  │  │    ratelimit.algorithm = "SLIDING_WINDOW_COUNTER"            │ │ │
  │  │  │    ratelimit.limit = 100                                      │ │ │
  │  │  │    ratelimit.remaining = 55                                   │ │ │
  │  │  │    ratelimit.allowed = true                                   │ │ │
  │  │  │    ratelimit.rule_id = "rule-123"                             │ │ │
  │  │  │                                                               │ │ │
  │  │  │  ┌─ span: redis.eval (0.30ms) ─────────────┐                │ │ │
  │  │  │  │  tags: redis.shard = "shard-2"           │                │ │ │
  │  │  │  └──────────────────────────────────────────┘                │ │ │
  │  │  └──────────────────────────────────────────────────────────────┘ │ │
  │  │                                                                    │ │
  │  │  ┌─ span: app.handle_request (25ms) ────────────────────────────┐ │ │
  │  │  │  ...                                                          │ │ │
  │  │  └──────────────────────────────────────────────────────────────┘ │ │
  │  └────────────────────────────────────────────────────────────────────┘ │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs and Design Decisions

### 15.1 Key Trade-offs

```
┌──────────────────────────────────────────────────────────────────────────┐
│  TRADE-OFF 1: Token Bucket vs Sliding Window Counter                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Token Bucket                          Sliding Window Counter            │
│  ─────────────                         ────────────────────              │
│  + Natural burst handling              + Simpler mental model            │
│  + Industry standard (AWS, Stripe)     + Easy to explain limits          │
│  + Two knobs (capacity + rate)         + One knob (count/window)         │
│  - Harder to reason about              - No built-in burst control       │
│  - "100 req/min" doesn't mean          - "100 req/min" means exactly     │
│    exactly 100 in any minute             that in any sliding minute      │
│                                                                          │
│  Decision: Use Sliding Window Counter as default for simplicity.         │
│  Offer Token Bucket as option for APIs that need burst control.          │
├──────────────────────────────────────────────────────────────────────────┤
│  TRADE-OFF 2: Centralized (Redis) vs Distributed (Local)                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Centralized (Redis)                   Distributed (Local)               │
│  ──────────────────                    ──────────────────                │
│  + Exact counts                        + No SPOF                         │
│  + Works with any server count         + Zero network latency            │
│  - Redis is a dependency               - Inaccurate with uneven traffic  │
│  - Network hop per request             - Scaling changes break limits    │
│                                                                          │
│  Decision: Centralized with local fallback (circuit breaker).            │
│  Redis for accuracy; local counters only during Redis outages.           │
├──────────────────────────────────────────────────────────────────────────┤
│  TRADE-OFF 3: Accuracy vs Performance                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  High Accuracy                         High Performance                  │
│  ──────────────                        ────────────────                  │
│  + Exact enforcement                   + Lower latency                   │
│  + No over/under counting              + Less Redis load                 │
│  - Redis call per request              - Up to N% over-counting          │
│  - Higher latency                      - Batched syncs                   │
│                                                                          │
│  Decision: Per-request Redis check for low-limit rules (< 100/min).     │
│  Local batching for high-limit rules (> 1000/min) where 1-5%            │
│  over-counting is acceptable.                                            │
├──────────────────────────────────────────────────────────────────────────┤
│  TRADE-OFF 4: Fail-Open vs Fail-Closed                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Fail-Open                             Fail-Closed                       │
│  ─────────                             ───────────                       │
│  + Service stays available             + Protects downstream systems     │
│  + Better user experience              + Security-safe                   │
│  - Abuse possible during outage        - Service appears down            │
│  - Downstream overload risk            - Customer impact                 │
│                                                                          │
│  Decision: Configurable per rule. Default fail-open for most APIs.       │
│  Fail-closed for payment and security-sensitive endpoints.               │
│  Fail-local (in-memory fallback) as middle ground.                       │
└──────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Technology Choices Rationale

```
┌───────────────────┬──────────────────┬───────────────────────────────────┐
│   Decision        │   Choice         │   Why Not Alternatives            │
├───────────────────┼──────────────────┼───────────────────────────────────┤
│ Counter store     │ Redis Cluster    │ Memcached: no Lua scripts, no    │
│                   │                  │   cluster mode, no persistence    │
│                   │                  │ DynamoDB: too slow (5-10ms),     │
│                   │                  │   expensive at 10M ops/sec       │
│                   │                  │ In-memory only: not distributed  │
├───────────────────┼──────────────────┼───────────────────────────────────┤
│ Rule store        │ PostgreSQL       │ MySQL: less feature-rich for      │
│                   │                  │   JSON rules / pattern matching  │
│                   │                  │ Redis: not durable enough        │
│                   │                  │   for configuration data          │
├───────────────────┼──────────────────┼───────────────────────────────────┤
│ Rule propagation  │ Redis Pub/Sub    │ Kafka: overkill for config       │
│                   │                  │   changes (low volume)           │
│                   │                  │ Polling: higher latency          │
│                   │                  │   (acceptable as fallback)       │
├───────────────────┼──────────────────┼───────────────────────────────────┤
│ Local cache       │ Caffeine         │ Guava Cache: slower, less        │
│                   │                  │   memory efficient               │
│                   │                  │ EhCache: heavier, disk-based     │
├───────────────────┼──────────────────┼───────────────────────────────────┤
│ Analytics         │ Kafka +          │ Direct DB writes: too slow       │
│                   │ ClickHouse       │ Prometheus only: no drill-down   │
│                   │                  │ Elasticsearch: expensive at      │
│                   │                  │   10M events/sec                 │
└───────────────────┴──────────────────┴───────────────────────────────────┘
```

---

## 16. Interview Deep-Dive Questions

### Q1: How do you rate limit across multiple data centers?

**Answer:** Use a hybrid approach with local Redis clusters per data center and
asynchronous cross-DC counter synchronization.

Each DC maintains its own Redis cluster with full rate limit counters. Periodically
(every 1-5 seconds), each DC publishes its counter deltas to other DCs via a
cross-DC message bus (e.g., Kafka with cross-region replication, or a purpose-built
gossip protocol).

Each DC calculates the effective count as:
`effective = local_count + sum(remote_dc_counts)`

This means the system is eventually consistent across DCs with a sync delay of
1-5 seconds. The worst-case over-count is:
`num_DCs * sync_interval * request_rate_per_DC`

For most use cases, this is acceptable. For strict global limits (e.g., financial
transaction caps), you would need a single global Redis cluster, accepting the
cross-DC latency penalty (30-80ms).

---

### Q2: What happens during a Redis failover?

**Answer:** Redis Sentinel or Redis Cluster handles automatic failover. The timeline:

1. **Detection** (5-15s): Sentinel detects primary is down via heartbeats.
2. **Election** (1-5s): Sentinels vote on a new primary from replicas.
3. **Promotion** (1-2s): Replica promoted, clients redirected.

During this 10-30 second window, the rate limiter circuit breaker opens, and the
configured fail mode activates. With fail-open, all requests are allowed temporarily.
With fail-local, in-memory counters enforce approximate limits.

**Data loss:** Redis async replication means the promoted replica may be a few
seconds behind. Some counter increments from the old primary are lost. This means
the system slightly under-counts after failover. For rate limiting, this is
preferable to over-counting (which would wrongly block users).

---

### Q3: How do you handle the fixed window boundary burst problem?

**Answer:** The boundary burst problem occurs when a client sends their full quota
at the end of one window and the beginning of the next, effectively getting 2x
the limit in a short burst.

**Solution: Sliding Window Counter.** Instead of a single counter per window, maintain
counters for both the current and previous windows. The effective count is:

```
weighted_count = prev_count * (1 - elapsed/window) + curr_count
```

This creates a virtual sliding window by interpolating between the two fixed windows.
The approximation assumes uniform distribution within the previous window, which
introduces ~0.3% error in practice -- far better than the 100% burst error of pure
fixed windows.

---

### Q4: How do you rate limit WebSocket connections vs HTTP requests?

**Answer:** WebSocket rate limiting has two dimensions:

1. **Connection rate limiting:** Limit how many WebSocket connections a client can
   establish per time window (e.g., 10 connections/minute). This uses the same
   mechanisms as HTTP rate limiting, triggered on the `Upgrade` handshake.

2. **Message rate limiting:** Once connected, limit the number of messages a client
   can send per time window (e.g., 100 messages/second). This requires the WebSocket
   handler to call the rate limiter on each incoming frame.

Key difference: HTTP rate limiting is stateless (each request independent), while
WebSocket message limiting is stateful (tied to a long-lived connection). For
WebSocket messages, a **token bucket** is ideal because it allows message bursts
(e.g., rapid typing) while enforcing an average rate.

Implementation: Maintain a per-connection token bucket in local memory (no need
for Redis since the connection is pinned to one server). Only use Redis for
connection establishment rate limiting.

---

### Q5: How would you implement a "leaky bucket" at global scale?

**Answer:** A true leaky bucket queues requests and processes them at a constant
rate. At global scale, this requires a distributed queue.

**Architecture:**
- Incoming requests are pushed to a partitioned queue (e.g., Kafka topic, partitioned
  by client_id)
- Consumer group processes messages at a fixed drain rate (e.g., 100 msg/sec per client)
- If the queue for a client is full (configurable depth), new messages are rejected (429)

**Challenges at scale:**
- Each client needs its own logical queue partition -- millions of partitions
- Constant drain rate requires a timer per client -- use a priority queue ordered
  by next-allowed-time
- Memory overhead: storing queued requests is expensive vs just counting them

**Recommendation:** For API rate limiting, the token bucket achieves similar smoothing
with far less complexity. The leaky bucket is better suited for network traffic
shaping where actual packet queuing is needed.

---

### Q6: How do you prevent a single hot tenant from affecting other tenants?

**Answer:** Multi-tenant isolation requires multiple strategies:

1. **Separate Redis key namespaces:** Each tenant's counters use `{tenant_id}` as
   a Redis hash tag, ensuring they land on predictable shards.

2. **Per-tenant Redis connection pools:** Prevent one tenant's traffic from
   exhausting another tenant's Redis connections.

3. **Hot tenant detection:** Monitor per-tenant request rates. When a tenant
   exceeds a threshold (e.g., 10x their limit), trigger local rate limiting
   for that tenant (skip Redis entirely, use in-memory counters).

4. **Shard isolation for premium tenants:** Large enterprise tenants get dedicated
   Redis shards, ensuring their counter operations never compete with other tenants.

5. **Admission control:** At the load balancer level, apply coarse per-tenant
   limits before traffic reaches the app layer.

---

### Q7: What is the cost of this system at scale?

**Answer:** For 10M requests/second:

```
Redis Cluster:
  50 shards * 2 (primary + replica) = 100 nodes
  r6g.xlarge (4 vCPU, 26 GB RAM): ~$0.25/hr per node
  Monthly: 100 * $0.25 * 730 = ~$18,250/month

App Server overhead:
  Rate limiting adds ~0.5ms per request
  20 app servers, rate limiting uses ~5% CPU
  Marginal cost: ~$500/month

PostgreSQL (rules):
  Single db.r6g.large: ~$300/month

Kafka + ClickHouse (analytics):
  ~$2,000/month

Total: ~$21,000/month for 10M req/sec rate limiting
Per request: ~$0.000000068 (essentially free per request)
```

---

### Q8: How do you handle rate limit key collision?

**Answer:** Key collisions happen when different clients map to the same Redis key
(e.g., hash collision in key generation).

**Prevention:**
- Use full identifiers in keys (not hashes): `rl:{tenant}:{endpoint}:{window}:{user_id}`
- If key length is a concern, use SHA-256 hash with collision probability ~1/2^128
- Include the identifier type in the key to prevent cross-type collisions

**Detection:**
- Monitor anomalies where a client's actual request count differs significantly
  from the counter value
- Log the full key on every 429 response for debugging

In practice, using full identifiers (not hashes) in Redis keys eliminates this
problem entirely. Redis supports keys up to 512MB, so a 200-byte key is fine.

---

### Q9: How would you implement tiered rate limiting (free/pro/enterprise)?

**Answer:** Map tier to rate limit rules:

```
Tier        | /api/search  | /api/upload  | /api/export
------------|-------------|-------------|-------------
Free        | 10/min      | 5/hour       | 1/day
Pro         | 100/min     | 50/hour      | 10/day
Enterprise  | 10,000/min  | 1,000/hour   | unlimited
```

**Implementation:**
1. Each tenant has a `plan_tier` field in the tenant table.
2. Rate limit rules have a `tier` field: `WHERE tier = tenant.plan_tier`.
3. On tier upgrade, update the tenant's tier and invalidate their cached rules.
4. Rules engine resolves: tier-specific rule > default rule.

**Edge case:** When a user upgrades mid-window, should the new limit apply
immediately or at the next window? Recommendation: apply immediately by resetting
the counter for that window. This provides a better user experience and incentivizes
upgrades.

---

### Q10: How do you test a rate limiter in production?

**Answer:**

1. **Shadow mode:** Run the rate limiter in observe-only mode, logging decisions
   without enforcing them. Compare shadow decisions against expected behavior.

2. **Canary deployment:** Enable enforcement on 1% of traffic first. Monitor 429
   rates and customer complaints.

3. **Load testing:** Use tools like Locust or k6 to simulate burst traffic patterns.
   Verify counters are accurate and latency stays under 1ms.

4. **Chaos testing:**
   - Kill Redis shards and verify circuit breaker activates
   - Inject network latency between app servers and Redis
   - Simulate clock skew between servers

5. **Accuracy verification:** Periodically compare Redis counter values against
   actual request counts from access logs. Alert if drift exceeds 1%.

---

### Q11: Should rate limiting be implemented as a library or a service?

**Answer:**

```
┌──────────────────┬─────────────────┬──────────────────────────────────┐
│                  │ Library (SDK)   │ Service (sidecar or standalone)  │
├──────────────────┼─────────────────┼──────────────────────────────────┤
│ Latency          │ Lower (in-proc) │ Higher (network hop)             │
│ Language support │ Per-language SDK │ Language-agnostic (HTTP/gRPC)    │
│ Deployment       │ Per-app upgrade  │ Independent deployment           │
│ Consistency      │ Rule sync needed │ Centralized rules                │
│ Complexity       │ Simpler          │ More infrastructure              │
├──────────────────┼─────────────────┼──────────────────────────────────┤
│ Best for         │ Homogeneous      │ Polyglot microservices           │
│                  │ stack (all Java) │ or service mesh (Envoy, Istio)   │
└──────────────────┴─────────────────┴──────────────────────────────────┘
```

**Recommendation for most teams:** Start with a library (lower complexity), move to
a sidecar if you have multiple languages or need centralized control. Envoy proxy
with its rate limiting filter is a good middle ground.

---

### Q12: How do you handle rate limiting for distributed transactions?

**Answer:** When a single user action triggers multiple API calls (e.g., placing an
order calls inventory, payment, and notification services), you must decide: does
each internal call count toward the limit, or only the user-facing request?

**Approach:** Use a **request cost** model. The user-facing request has `cost=1`.
Internal service-to-service calls carry a context header (`X-RateLimit-Internal: true`)
and are either excluded from rate limiting or counted with `cost=0`.

Alternatively, rate limit only at the **edge** (API gateway). Internal calls bypass
the rate limiter entirely since they are already bounded by the edge limit.

---

### Q13: How do you handle sudden traffic spikes (flash crowds)?

**Answer:**

1. **Token bucket with burst capacity:** Set bucket capacity higher than the sustained
   rate. E.g., limit=100/min, burst=50 means 50 requests can arrive instantly, then
   100/min sustained.

2. **Adaptive rate limiting:** Monitor backend health (CPU, latency, error rate). When
   backends are stressed, dynamically lower rate limits. When healthy, restore them.

   ```
   if backend_error_rate > 5%:
       dynamic_limit = base_limit * 0.5
   elif backend_p99_latency > 500ms:
       dynamic_limit = base_limit * 0.75
   else:
       dynamic_limit = base_limit
   ```

3. **Prioritized rate limiting:** Under load, tier limits differently.
   Enterprise customers keep their full limits, while free-tier limits are reduced.
   This is effectively quality-of-service (QoS) based rate limiting.

---

### Q14: What is the difference between rate limiting and throttling?

**Answer:**

- **Rate limiting:** Binary decision. Request is either allowed or rejected (429).
  The client must retry later. Protects the server.

- **Throttling:** Delays the request rather than rejecting it. The request is queued
  and processed when capacity is available. Better for batch/async workloads.

- **Backpressure:** Server signals the client to slow down (e.g., via flow control
  in gRPC or TCP window size). Client cooperatively reduces its rate.

In practice, API rate limiting uses rejection (429 + Retry-After), while internal
service-to-service communication may use throttling or backpressure to avoid
cascading failures.

---

### Q15: How would you migrate from a local rate limiter to a distributed one?

**Answer:** Phased migration:

1. **Phase 1 - Dual write:** Deploy Redis-based rate limiter alongside existing
   local limiter. Both make decisions, but only the local limiter's decision is
   enforced. Log discrepancies.

2. **Phase 2 - Shadow enforcement:** Switch enforcement to the distributed limiter
   for 5% of traffic. Monitor for correctness and latency impact.

3. **Phase 3 - Gradual rollout:** Increase to 25%, 50%, 100% over 2 weeks.
   Keep local limiter as fallback (circuit breaker).

4. **Phase 4 - Cleanup:** Remove local limiter code once distributed limiter has
   been stable for 30 days.

**Key concern:** During migration, both limiters run simultaneously. A request
that passes the local limiter but fails the distributed one (or vice versa) reveals
a discrepancy. Track these as a metric and investigate before increasing rollout.

---

## Appendix A: Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE REQUEST FLOW                                    │
│                                                                             │
│  Client                                                                     │
│    │                                                                        │
│    │ POST /api/orders                                                       │
│    │ X-API-Key: key-456                                                     │
│    ▼                                                                        │
│  Load Balancer                                                              │
│    │                                                                        │
│    │ (optional: edge rate limit by IP)                                       │
│    ▼                                                                        │
│  App Server                                                                 │
│    │                                                                        │
│    ├─► 1. Extract identity                                                  │
│    │      client_id = "key-456"                                             │
│    │      tenant_id = lookupTenant("key-456") → "tenant-42"                │
│    │                                                                        │
│    ├─► 2. Check deny list (local cache / Redis SET)                        │
│    │      SISMEMBER deny:tenant-42 "key-456" → false                       │
│    │                                                                        │
│    ├─► 3. Check allow list (local cache / Redis SET)                       │
│    │      SISMEMBER allow:tenant-42 "key-456" → false                      │
│    │                                                                        │
│    ├─► 4. Load matching rule (local Caffeine cache)                        │
│    │      rule = cache.get("tenant-42:POST /api/orders:API_KEY")           │
│    │      → {limit: 100, window: 60, algorithm: SLIDING_WINDOW_COUNTER}   │
│    │                                                                        │
│    ├─► 5. Execute rate limit check (Redis Lua script)                      │
│    │      EVAL sliding_window_counter.lua                                   │
│    │        KEY = "rl:{tenant-42}:a1b2c3:60:key-456"                       │
│    │        → {allowed: true, remaining: 55}                                │
│    │                                                                        │
│    ├─► 6. Set response headers                                             │
│    │      X-RateLimit-Limit: 100                                            │
│    │      X-RateLimit-Remaining: 55                                         │
│    │      X-RateLimit-Reset: 1680000060                                     │
│    │                                                                        │
│    ├─► 7. Emit analytics event (async, non-blocking)                       │
│    │      kafka.send("rate-limit-events", {tenant, client, allowed, ...})  │
│    │                                                                        │
│    └─► 8. Forward to application handler                                    │
│           → process order                                                   │
│           → return 201 Created + rate limit headers                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Production Configuration Example

```yaml
# rate-limiter-config.yaml
rate_limiter:
  # Global settings
  default_algorithm: SLIDING_WINDOW_COUNTER
  default_fail_mode: OPEN
  local_cache_ttl_seconds: 30
  local_cache_max_size: 10000

  # Redis connection
  redis:
    cluster_nodes:
      - redis-shard-1.internal:6379
      - redis-shard-2.internal:6379
      - redis-shard-3.internal:6379
    connection_pool_size: 50
    connection_timeout_ms: 100
    read_timeout_ms: 50
    write_timeout_ms: 50
    max_retries: 2

  # Circuit breaker
  circuit_breaker:
    failure_threshold: 5
    failure_window_seconds: 10
    open_duration_seconds: 30
    half_open_probes: 1

  # Local fallback (when Redis is down)
  local_fallback:
    enabled: true
    server_count: 20  # used to divide global limit
    cleanup_interval_seconds: 60

  # Analytics
  analytics:
    enabled: true
    kafka_topic: rate-limit-events
    sampling_rate: 0.01  # 1% of allowed requests
    denied_sampling_rate: 1.0  # 100% of denied requests

  # Default rules (overridden by tenant-specific rules)
  default_rules:
    - endpoint: "*"
      identifier_type: IP
      limit: 10000
      window_seconds: 60
      algorithm: FIXED_WINDOW
      fail_mode: OPEN

    - endpoint: "POST /api/auth/login"
      identifier_type: IP
      limit: 5
      window_seconds: 60
      algorithm: SLIDING_WINDOW_COUNTER
      fail_mode: CLOSED  # security: fail-closed for login
```

---

## Appendix C: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│            RATE LIMITER DESIGN - QUICK REFERENCE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DEFAULT ALGORITHM:     Sliding Window Counter                  │
│  COUNTER STORE:         Redis Cluster (50+ shards for 10M rps) │
│  RULE STORE:            PostgreSQL + local Caffeine cache       │
│  FAIL MODE:             Fail-open (default), configurable       │
│  LATENCY:               < 1ms p99 overhead per request          │
│  ACCURACY:              ~99.7% (sliding window approximation)   │
│  MULTI-DC:              Local Redis + async cross-DC sync       │
│  HOT KEY HANDLING:      Local counter + periodic Redis sync     │
│                                                                 │
│  KEY FORMULA:           rl:{tenant}:{ep_hash}:{window}:{client} │
│  TTL:                   window_seconds + 10s buffer             │
│  RULE PROPAGATION:      Redis Pub/Sub + 30s cache TTL fallback  │
│                                                                 │
│  CRITICAL DECISIONS:                                            │
│  1. Sliding window counter over token bucket (simpler)          │
│  2. Redis over local-only (accuracy over latency)               │
│  3. Fail-open over fail-closed (availability over safety)       │
│  4. Async analytics over sync logging (performance)             │
│  5. Lua scripts over multi-command (atomicity)                  │
└─────────────────────────────────────────────────────────────────┘
```
