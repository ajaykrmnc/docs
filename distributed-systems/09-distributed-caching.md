# Distributed Caching

## Table of Contents
1. [Introduction to Caching](#introduction-to-caching)
2. [Caching Strategies](#caching-strategies)
3. [Cache Invalidation](#cache-invalidation)
4. [Distributed Cache Architectures](#distributed-cache-architectures)
5. [Redis Deep Dive](#redis-deep-dive)
6. [Memcached](#memcached)
7. [Cache Consistency](#cache-consistency)
8. [Interview Questions](#interview-questions)

---

## Introduction to Caching

### Why Caching?

```
┌─────────────────────────────────────────────────────────────────┐
│              WHY CACHING?                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Without Cache:                                                │
│  ──────────────                                                │
│  Client ───► App Server ───► Database                          │
│                              (100ms)                           │
│                                                                 │
│  With Cache:                                                   │
│  ────────────                                                  │
│  Client ───► App Server ───► Cache (HIT) ───► Response        │
│                              (1ms)                             │
│                         │                                       │
│                         └───► Database (MISS)                  │
│                              (100ms)                           │
│                                                                 │
│  Benefits:                                                     │
│  • Reduced latency (100x faster)                              │
│  • Reduced database load                                       │
│  • Improved throughput                                         │
│  • Cost savings (fewer DB instances)                          │
│                                                                 │
│  Latency comparison:                                           │
│  • L1 cache:     ~1 ns                                        │
│  • L2 cache:     ~4 ns                                        │
│  • RAM:          ~100 ns                                      │
│  • SSD:          ~100 μs                                      │
│  • Network:      ~1-100 ms                                    │
│  • Database:     ~10-100 ms                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cache Hit Ratio

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE HIT RATIO                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hit Ratio = Cache Hits / (Cache Hits + Cache Misses)         │
│                                                                 │
│  Example:                                                      │
│  • 90 hits, 10 misses → 90% hit ratio                        │
│                                                                 │
│  Impact on latency:                                            │
│  ─────────────────────                                         │
│  Cache latency: 1ms                                            │
│  DB latency: 100ms                                             │
│                                                                 │
│  │ Hit Ratio │ Avg Latency │ Speedup │                        │
│  │───────────│─────────────│─────────│                        │
│  │    50%    │   50.5ms    │   2x    │                        │
│  │    80%    │   20.8ms    │   5x    │                        │
│  │    90%    │   10.9ms    │   9x    │                        │
│  │    95%    │    5.95ms   │   17x   │                        │
│  │    99%    │    1.99ms   │   50x   │                        │
│                                                                 │
│  Even small improvements in hit ratio have big impact!        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Caching Strategies

### Read Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE-ASIDE (Lazy Loading)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Application manages cache:                                    │
│                                                                 │
│  1. App checks cache                                           │
│  2. If HIT: return cached data                                │
│  3. If MISS: read from DB, write to cache, return             │
│                                                                 │
│  ┌─────────┐    1. Get    ┌─────────┐                         │
│  │   App   │─────────────►│  Cache  │                         │
│  └────┬────┘◄─────────────└─────────┘                         │
│       │         2. Miss                                        │
│       │                                                        │
│       │ 3. Get  ┌─────────┐                                   │
│       └────────►│   DB    │                                   │
│       ◄─────────└─────────┘                                   │
│       │         4. Data                                        │
│       │                                                        │
│       │ 5. Set  ┌─────────┐                                   │
│       └────────►│  Cache  │                                   │
│                 └─────────┘                                   │
│                                                                 │
│  Pros: Only requested data cached, cache failure = DB fallback│
│  Cons: Cache miss penalty, potential stale data               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│              READ-THROUGH                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Cache manages data loading:                                   │
│                                                                 │
│  ┌─────────┐    1. Get    ┌─────────┐    2. Get   ┌─────────┐│
│  │   App   │─────────────►│  Cache  │────────────►│   DB    ││
│  └─────────┘◄─────────────└─────────┘◄────────────└─────────┘│
│                 3. Data                  (on miss)            │
│                                                                 │
│  Cache automatically loads from DB on miss                    │
│                                                                 │
│  Pros: Simpler app code, consistent loading logic             │
│  Cons: First request always slow, cache library dependency    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Write Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              WRITE STRATEGIES                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. WRITE-THROUGH                                              │
│  ─────────────────                                             │
│  Write to cache AND DB synchronously                          │


---

## Cache Invalidation

### The Hard Problem

> "There are only two hard things in Computer Science: cache invalidation and naming things." - Phil Karlton

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE INVALIDATION STRATEGIES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TIME-TO-LIVE (TTL)                                         │
│  ─────────────────────                                         │
│  Data expires after fixed time                                 │
│                                                                 │
│  SET key value EX 300  (expires in 5 minutes)                 │
│                                                                 │
│  Pros: Simple, automatic cleanup                              │
│  Cons: Stale data until expiry, thundering herd on expiry    │
│                                                                 │
│  2. EVENT-BASED INVALIDATION                                   │
│  ───────────────────────────                                   │
│  Invalidate on data change                                    │
│                                                                 │
│  DB Update ───► Publish Event ───► Cache Delete               │
│                                                                 │
│  Pros: Immediate consistency                                  │
│  Cons: Complex, event delivery issues                         │
│                                                                 │
│  3. VERSION-BASED                                              │
│  ────────────────                                              │
│  Include version in cache key                                 │
│                                                                 │
│  Key: user:123:v5                                             │
│  On update: increment version, old key naturally expires      │
│                                                                 │
│  Pros: No explicit invalidation needed                        │
│  Cons: Storage overhead, version management                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cache Stampede Prevention

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE STAMPEDE (Thundering Herd)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Problem: Many requests hit expired key simultaneously        │
│                                                                 │
│  Time ─────────────────────────────────────────────────►       │
│                                                                 │
│  Cache: [data] ─────────────────────────────── EXPIRED!       │
│                                                                 │
│  Requests:  ─────────────────────────────────┬─┬─┬─┬─┬─       │
│                                              │ │ │ │ │        │
│                                              ▼ ▼ ▼ ▼ ▼        │
│  Database:                                   💥 OVERLOAD      │
│                                                                 │
│  SOLUTIONS:                                                    │
│  ───────────                                                   │
│  1. LOCKING                                                    │
│     First request acquires lock, others wait                  │
│     Only one DB query, others get cached result               │
│                                                                 │
│  2. PROBABILISTIC EARLY EXPIRATION                            │
│     Refresh before actual expiry (random jitter)              │
│     TTL = actual_ttl - random(0, buffer)                      │
│                                                                 │
│  3. BACKGROUND REFRESH                                         │
│     Separate process refreshes before expiry                  │
│     Cache never actually expires                              │
│                                                                 │
│  4. STALE-WHILE-REVALIDATE                                    │
│     Return stale data, refresh in background                  │
│     User gets fast response, data refreshed async             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Distributed Cache Architectures

### Partitioning Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE PARTITIONING                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. MODULO HASHING                                             │
│  ─────────────────                                             │
│  server = hash(key) % num_servers                             │
│                                                                 │
│  Problem: Adding/removing server redistributes ALL keys       │
│                                                                 │
│  Before (3 servers):  hash(key) % 3 = 1 → Server B           │
│  After (4 servers):   hash(key) % 4 = 2 → Server C           │
│                                                                 │
│  2. CONSISTENT HASHING                                         │
│  ─────────────────────                                         │
│  Servers and keys on hash ring                                │
│                                                                 │
│                    Server A                                    │
│                       ●                                         │
│                   ╱       ╲                                     │
│                 ╱     ○ key1 ╲                                 │
│               ╱               ╲                                 │
│  Server D   ●       ○ key2     ●  Server B                    │
│               ╲               ╱                                 │
│                 ╲   ○ key3  ╱                                  │
│                   ╲       ╱                                     │
│                       ●                                         │
│                    Server C                                    │
│                                                                 │
│  Adding server: only adjacent keys move                       │
│  Virtual nodes: better distribution                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Replication Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE REPLICATION                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. NO REPLICATION                                             │
│     • Single copy per key                                     │
│     • Node failure = data loss                                │
│     • Simplest, highest capacity                              │
│                                                                 │
│  2. PRIMARY-REPLICA                                            │
│     • Primary handles writes                                  │
│     • Replicas handle reads                                   │
│     • Async replication (eventual consistency)                │
│                                                                 │
│     ┌─────────┐                                               │
│     │ Primary │◄─── Writes                                    │
│     └────┬────┘                                               │
│          │ async                                               │
│     ┌────┴────┐                                               │
│     ▼         ▼                                               │
│  ┌─────┐  ┌─────┐                                             │
│  │Rep 1│  │Rep 2│◄─── Reads                                   │
│  └─────┘  └─────┘                                             │
│                                                                 │
│  3. MULTI-PRIMARY                                              │
│     • Any node handles writes                                 │
│     • Conflict resolution needed                              │
│     • Higher availability                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Redis Deep Dive

### Redis Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              REDIS ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Single-threaded event loop (mostly):                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    REDIS SERVER                          │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │              Event Loop (single thread)          │    │  │
│  │  │                                                   │    │  │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │    │  │
│  │  │  │ Network │  │ Command │  │  Timer  │         │    │  │
│  │  │  │  I/O    │  │ Process │  │ Events  │         │    │  │
│  │  │  └─────────┘  └─────────┘  └─────────┘         │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │              In-Memory Data                      │    │  │
│  │  │  Strings, Lists, Sets, Hashes, Sorted Sets...  │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │                                                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Why single-threaded?                                         │
│  • No locks needed                                            │
│  • Simpler code                                               │
│  • Memory access is bottleneck, not CPU                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Redis Data Structures

```
┌─────────────────────────────────────────────────────────────────┐
│              REDIS DATA STRUCTURES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STRING: Simple key-value                                      │
│  SET user:123 "John"                                          │
│  GET user:123 → "John"                                        │
│  INCR counter → atomic increment                              │
│                                                                 │
│  LIST: Ordered collection                                      │
│  LPUSH queue task1 task2                                      │
│  RPOP queue → task1                                           │
│  Use: Message queues, activity feeds                          │
│                                                                 │
│  SET: Unique unordered collection                             │
│  SADD tags:post1 redis cache database                        │
│  SMEMBERS tags:post1 → {redis, cache, database}              │
│  Use: Tags, unique visitors                                   │
│                                                                 │
│  HASH: Field-value pairs                                      │
│  HSET user:123 name "John" age 30                            │
│  HGET user:123 name → "John"                                 │
│  Use: Objects, user profiles                                  │
│                                                                 │
│  SORTED SET: Scored unique members                            │
│  ZADD leaderboard 100 "player1" 200 "player2"                │
│  ZRANGE leaderboard 0 -1 → [player1, player2]                │
│  Use: Leaderboards, rate limiting                             │
│                                                                 │
│  STREAM: Append-only log (Kafka-like)                         │
│  XADD stream * field value                                    │
│  XREAD STREAMS stream 0                                       │
│  Use: Event sourcing, message queues                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Redis Cluster

```
┌─────────────────────────────────────────────────────────────────┐
│              REDIS CLUSTER                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  16384 hash slots distributed across nodes:                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    REDIS CLUSTER                         │  │
│  │                                                           │  │
│  │  Node A              Node B              Node C          │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │  │
│  │  │ Slots 0-5460 │   │Slots 5461-   │   │Slots 10923-  │ │  │
│  │  │              │   │    10922     │   │    16383     │ │  │
│  │  │  ┌────────┐  │   │  ┌────────┐  │   │  ┌────────┐  │ │  │
│  │  │  │Primary │  │   │  │Primary │  │   │  │Primary │  │ │  │
│  │  │  └────────┘  │   │  └────────┘  │   │  └────────┘  │ │  │
│  │  │  ┌────────┐  │   │  ┌────────┐  │   │  ┌────────┐  │ │  │
│  │  │  │Replica │  │   │  │Replica │  │   │  │Replica │  │ │  │
│  │  │  └────────┘  │   │  └────────┘  │   │  └────────┘  │ │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘ │  │
│  │                                                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Key routing: slot = CRC16(key) % 16384                       │
│  MOVED redirect if key on different node                      │
│                                                                 │
│  Limitations:                                                  │
│  • Multi-key ops only if same slot (use hash tags)           │
│  • No strong consistency (async replication)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Memcached

### Memcached vs Redis

| Feature | Memcached | Redis |
|---------|-----------|-------|
| **Data Types** | Strings only | Rich (lists, sets, etc.) |
| **Persistence** | No | Yes (RDB, AOF) |
| **Replication** | No | Yes |
| **Clustering** | Client-side | Built-in |
| **Memory** | Multi-threaded | Single-threaded |
| **Use Case** | Simple caching | Caching + data structures |

### When to Use Memcached

- Simple key-value caching
- Multi-threaded performance needed
- No persistence required
- Horizontal scaling with client-side sharding

---

## Cache Consistency

### Consistency Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│              CACHE CONSISTENCY PATTERNS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CACHE-ASIDE + TTL                                          │
│     • Eventual consistency                                     │
│     • Stale data possible for TTL duration                    │
│     • Simple to implement                                      │
│                                                                 │
│  2. WRITE-THROUGH                                              │
│     • Strong consistency                                       │
│     • Higher write latency                                     │
│     • Cache always up-to-date                                 │
│                                                                 │
│  3. INVALIDATE ON WRITE                                        │
│     • Delete cache on DB write                                │
│     • Next read populates cache                               │
│     • Race condition possible                                  │
│                                                                 │
│  Race condition example:                                       │
│  ─────────────────────────                                     │
│  T1: Read DB (old value)                                      │
│  T2: Write DB (new value)                                     │
│  T2: Delete cache                                             │
│  T1: Write cache (old value!) ← STALE!                       │
│                                                                 │
│  Solution: Use versioning or delayed double-delete            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: What's the difference between cache-aside and read-through?**

| Aspect | Cache-Aside | Read-Through |
|--------|-------------|--------------|
| Who loads data | Application | Cache library |
| Code complexity | Higher | Lower |
| Cache miss handling | App queries DB | Cache queries DB |
| Flexibility | More control | Less control |

**Q2: How do you handle cache stampede?**

1. **Locking**: First request acquires lock, others wait
2. **Early expiration**: Refresh before TTL with jitter
3. **Background refresh**: Never let cache expire
4. **Stale-while-revalidate**: Return stale, refresh async

**Q3: Explain consistent hashing.**

- Servers and keys mapped to hash ring
- Key routes to next server clockwise
- Adding/removing server only affects adjacent keys
- Virtual nodes improve distribution

### Design Questions

**Q4: Design a distributed cache for a social media feed.**

```
Architecture:
├── Cache layer (Redis Cluster)
│   ├── User feed cache (sorted set by timestamp)
│   ├── Post cache (hash)
│   └── User profile cache (hash)
├── Invalidation
│   ├── New post → fan-out to follower caches
│   ├── TTL for older posts
│   └── Event-driven for profile updates
├── Consistency
│   ├── Write-through for critical data
│   └── Cache-aside with TTL for feeds
└── Scaling
    ├── Consistent hashing for distribution
    └── Read replicas for hot users
```

**Q5: How would you implement rate limiting with Redis?**

```
Sliding window with sorted set:

ZADD user:123:requests <timestamp> <request_id>
ZREMRANGEBYSCORE user:123:requests 0 <timestamp - window>
ZCARD user:123:requests

If count > limit → reject
Else → allow

Or use token bucket with INCR + EXPIRE
```

---

## Summary

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         CACHING CHEAT SHEET                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  READ STRATEGIES:                                              │
│  • Cache-aside: App manages cache                             │
│  • Read-through: Cache manages loading                        │
│                                                                 │
│  WRITE STRATEGIES:                                             │
│  • Write-through: Sync write to cache + DB                    │
│  • Write-behind: Async write to DB                            │
│  • Write-around: Write to DB only                             │
│                                                                 │
│  INVALIDATION:                                                 │
│  • TTL: Time-based expiration                                 │
│  • Event-based: Invalidate on change                          │
│  • Version-based: New version = new key                       │
│                                                                 │
│  CACHE STAMPEDE PREVENTION:                                    │
│  • Locking                                                     │
│  • Early expiration with jitter                               │
│  • Background refresh                                          │
│  • Stale-while-revalidate                                     │
│                                                                 │
│  REDIS DATA STRUCTURES:                                        │
│  • String: Simple KV, counters                                │
│  • List: Queues, feeds                                        │
│  • Set: Tags, unique items                                    │
│  • Hash: Objects                                               │
│  • Sorted Set: Leaderboards, rate limiting                   │
│                                                                 │
│  PARTITIONING:                                                 │
│  • Modulo: Simple but poor scaling                            │
│  • Consistent hashing: Minimal redistribution                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

