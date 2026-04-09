# Design a Distributed Cache (Redis / Memcached)

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Back-of-Envelope Estimation](#4-back-of-envelope-estimation)
5. [API Design](#5-api-design)
6. [Data Model](#6-data-model)
7. [High-Level Architecture](#7-high-level-architecture)
8. [Deep Dive](#8-deep-dive)
   - 8.1 [Hash Slot Architecture](#81-hash-slot-architecture)
   - 8.2 [Eviction Policies](#82-eviction-policies)
   - 8.3 [Replication](#83-replication)
   - 8.4 [Cache Patterns](#84-cache-patterns)
9. [Data Partitioning](#9-data-partitioning)
10. [Caching Strategy](#10-caching-strategy)
11. [Replication and Consistency](#11-replication-and-consistency)
12. [Fault Tolerance](#12-fault-tolerance)
13. [Scalability](#13-scalability)
14. [Monitoring](#14-monitoring)
15. [Trade-offs](#15-trade-offs)
16. [Interview Questions](#16-interview-questions)

---

## 1. Problem Statement

Modern web applications rely heavily on databases to store and retrieve data. As traffic
scales, databases become bottlenecks -- disk I/O, query parsing, and index lookups all add
latency. A distributed cache sits between the application and the database, storing
frequently accessed data in memory to deliver sub-millisecond responses while shielding the
database from excessive load.

**Core challenge**: Design a distributed, in-memory key-value store that provides
sub-millisecond reads, supports millions of operations per second, handles node failures
gracefully, and scales horizontally across a cluster of machines.

**Real-world systems**: Redis, Memcached, Amazon ElastiCache, Azure Cache for Redis,
Google Memorystore.

**Why this matters**:
- Database queries typically take 5-50ms; cache hits return in <1ms (50-100x speedup).
- A single cache node can serve 100K+ operations/sec vs ~5K queries/sec for a database.
- Caching reduces database load by 80-95% for read-heavy workloads.
- Without caching, scaling to millions of users requires proportionally more database
  capacity, which is expensive and complex.

---

## 2. Functional Requirements

### Core Operations

| Operation   | Description                                          |
|-------------|------------------------------------------------------|
| `GET`       | Retrieve value by key                                |
| `SET`       | Store key-value pair with optional TTL               |
| `DELETE`    | Remove key-value pair                                |
| `EXISTS`    | Check if key exists without fetching value           |
| `EXPIRE`    | Set or update TTL on existing key                    |
| `TTL`       | Query remaining time-to-live for a key               |
| `INCR/DECR` | Atomic increment/decrement of integer values        |
| `MGET/MSET` | Batch get/set for multiple keys                     |

### Eviction Policies

- **LRU (Least Recently Used)**: Evict keys that have not been accessed recently.
- **LFU (Least Frequently Used)**: Evict keys with the lowest access frequency.
- **Random**: Evict a randomly selected key.
- **TTL-based**: Evict keys closest to expiration.
- **No eviction**: Return errors when memory is full (useful for critical data).

### Data Structures (Redis-style)

| Structure     | Operations                        | Use Case                          |
|---------------|-----------------------------------|-----------------------------------|
| String        | GET, SET, INCR, APPEND            | Counters, simple caching          |
| Hash          | HGET, HSET, HMGET, HGETALL       | Object storage, user profiles     |
| List          | LPUSH, RPUSH, LPOP, RPOP, LRANGE | Message queues, activity feeds    |
| Set           | SADD, SREM, SMEMBERS, SINTER     | Tags, unique visitors             |
| Sorted Set    | ZADD, ZRANGE, ZRANGEBYSCORE      | Leaderboards, rate limiters       |
| HyperLogLog   | PFADD, PFCOUNT, PFMERGE          | Cardinality estimation            |
| Bitmap        | SETBIT, GETBIT, BITCOUNT         | Feature flags, daily active users |
| Stream        | XADD, XREAD, XRANGE              | Event sourcing, message streams   |

### Pub/Sub

- **SUBSCRIBE/PUBLISH**: Real-time message broadcasting to channels.
- **Pattern subscribe**: Subscribe using glob-style patterns (`news.*`).
- **Key-space notifications**: Get notified when keys are modified or expired.

### Atomic Operations

- **Transactions (MULTI/EXEC)**: Group commands for atomic execution.
- **Lua scripting**: Execute server-side scripts atomically.
- **Optimistic locking (WATCH)**: Detect concurrent modifications.

### Persistence Options

| Mode   | Mechanism                                | Pros                         | Cons                         |
|--------|------------------------------------------|------------------------------|------------------------------|
| RDB    | Point-in-time snapshots to disk          | Compact, fast recovery       | Data loss between snapshots  |
| AOF    | Append every write command to log        | Minimal data loss            | Larger files, slower restart |
| Hybrid | RDB snapshot + AOF tail                  | Best of both worlds          | More complex management      |
| None   | Pure in-memory, no persistence           | Maximum performance          | All data lost on restart     |

### Cluster Mode

- **Automatic sharding**: Data distributed across multiple nodes.
- **Hash slots**: 16384 slots mapped to nodes for deterministic routing.
- **Online resharding**: Migrate slots between nodes without downtime.
- **Automatic failover**: Promote replicas when masters fail.

---

## 3. Non-Functional Requirements

| Requirement        | Target                                               |
|--------------------|------------------------------------------------------|
| Latency (p50)      | < 0.5 ms for GET/SET operations                      |
| Latency (p99)      | < 1 ms for GET/SET operations                        |
| Throughput          | 100,000+ operations/sec per node                     |
| Availability       | 99.99% uptime (< 52.6 minutes downtime/year)         |
| Durability          | Configurable: from none to fsync-every-write         |
| Data size per key  | Up to 512 MB (Redis), typically 1 KB - 1 MB          |
| Max keys per node  | Hundreds of millions (limited by RAM)                |
| Cluster size       | Up to 1000 nodes                                     |
| Failover time      | < 15 seconds for automatic failover                  |
| Network            | Support for 10 Gbps+ network interfaces              |
| Replication lag    | < 1 ms under normal conditions                       |
| Memory efficiency  | < 20% overhead vs raw data size                      |

---

## 4. Back-of-Envelope Estimation

### Traffic Estimation

```
Total operations/sec:      10,000,000 (10M ops/sec)
Read:Write ratio:          80:20
Read operations/sec:       8,000,000
Write operations/sec:      2,000,000

Peak multiplier:           3x
Peak operations/sec:       30,000,000
```

### Storage Estimation

```
Average key size:          64 bytes
Average value size:        1 KB (1,024 bytes)
Total entry size:          ~1.1 KB (key + value + metadata)

Total unique keys:         10 billion (10B)
Raw data:                  10B x 1.1 KB = 11 TB
Memory overhead (20%):     11 TB x 1.2 = ~13.2 TB
Per-node memory:           128 GB RAM
Nodes needed (data):       13.2 TB / 128 GB = ~104 nodes
Rounded up:                110 nodes (with headroom)
```

### Node Calculation

```
Per-node throughput:       100,000 ops/sec
Total ops/sec needed:      10,000,000
Nodes needed (throughput): 10M / 100K = 100 nodes
Peak nodes needed:         30M / 100K = 300 nodes

Decision: 110 nodes for storage, ~300 for peak throughput
  -> Use 110 primary nodes + 220 replicas (2 replicas each)
  -> Replicas absorb read traffic, handling peak load
  -> Total cluster: 330 nodes
```

### Network Estimation

```
Per operation bandwidth:   1.1 KB (avg)
Total bandwidth:           10M x 1.1 KB = 11 GB/sec = 88 Gbps
Per node (110 nodes):      88 Gbps / 110 = ~0.8 Gbps per node
With replication (2x):     ~1.6 Gbps per node for writes
Network interface needed:  10 Gbps (sufficient)
```

### Memory Breakdown Per Node (128 GB)

```
User data:                 100 GB (78%)
Hash table overhead:       10 GB (8%)
Eviction metadata (LRU):   3 GB (2%)
Replication buffers:        5 GB (4%)
Client output buffers:      5 GB (4%)
OS and process overhead:    5 GB (4%)
Total:                     128 GB (100%)
```

---

## 5. API Design

### Data Operations

```
# String operations
SET key value [EX seconds] [PX milliseconds] [NX|XX]
GET key
DEL key [key ...]
MSET key value [key value ...]
MGET key [key ...]
INCR key
INCRBY key increment
DECR key
DECRBY key decrement
APPEND key value
SETNX key value              # SET if Not eXists (atomic)

# Expiration
EXPIRE key seconds
PEXPIRE key milliseconds
TTL key                      # Remaining TTL in seconds
PTTL key                     # Remaining TTL in milliseconds
PERSIST key                  # Remove TTL

# Hash operations
HSET key field value [field value ...]
HGET key field
HMGET key field [field ...]
HGETALL key
HDEL key field [field ...]
HINCRBY key field increment

# List operations
LPUSH key element [element ...]
RPUSH key element [element ...]
LPOP key [count]
RPOP key [count]
LRANGE key start stop
LLEN key
BLPOP key [key ...] timeout  # Blocking pop

# Set operations
SADD key member [member ...]
SREM key member [member ...]
SMEMBERS key
SISMEMBER key member
SINTER key [key ...]
SUNION key [key ...]
SCARD key

# Sorted Set operations
ZADD key [NX|XX] [GT|LT] score member [score member ...]
ZRANGE key min max [BYSCORE|BYLEX] [REV] [LIMIT offset count]
ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count]
ZRANK key member
ZSCORE key member
ZREM key member [member ...]
ZCARD key

# Stream operations
XADD key [MAXLEN|MINID] ID field value [field value ...]
XREAD [COUNT count] [BLOCK milliseconds] STREAMS key [key ...] ID [ID ...]
XRANGE key start end [COUNT count]
XLEN key
```

### Cluster Management

```
CLUSTER INFO                 # Show cluster state
CLUSTER NODES                # List all nodes in cluster
CLUSTER MEET ip port         # Add node to cluster
CLUSTER ADDSLOTS slot [slot ...]
CLUSTER DELSLOTS slot [slot ...]
CLUSTER SETSLOT slot MIGRATING node-id
CLUSTER SETSLOT slot IMPORTING node-id
CLUSTER SETSLOT slot NODE node-id
CLUSTER REPLICATE node-id    # Make current node replica of given master
CLUSTER FAILOVER [FORCE|TAKEOVER]
CLUSTER RESET [HARD|SOFT]
CLUSTER SLOTS                # Slot-to-node mapping
CLUSTER KEYSLOT key          # Which slot a key maps to
```

### Pub/Sub

```
SUBSCRIBE channel [channel ...]
UNSUBSCRIBE [channel [channel ...]]
PUBLISH channel message
PSUBSCRIBE pattern [pattern ...]   # Pattern subscribe
PUNSUBSCRIBE [pattern [pattern ...]]
```

### Transactions and Scripting

```
MULTI                        # Start transaction
EXEC                         # Execute transaction
DISCARD                      # Abort transaction
WATCH key [key ...]          # Optimistic lock

EVAL script numkeys [key ...] [arg ...]     # Run Lua script
EVALSHA sha1 numkeys [key ...] [arg ...]    # Run cached script
SCRIPT LOAD script
SCRIPT EXISTS sha1 [sha1 ...]
```

### Administrative

```
INFO [section]               # Server info and stats
CONFIG GET parameter
CONFIG SET parameter value
DBSIZE                       # Number of keys
FLUSHDB [ASYNC]              # Delete all keys in current DB
SLOWLOG GET [count]          # Slow query log
CLIENT LIST                  # Connected clients
MEMORY USAGE key             # Memory used by key
DEBUG SLEEP seconds          # (development only)
```

---

## 6. Data Model

### Core Data Structures (Internal Implementation)

#### Hash Table (Primary Index)

The main key-space is a hash table using chained hashing with incremental rehashing.

```
┌─────────────────────────────────────────────────────────────────┐
│                      HASH TABLE (dict)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ht[0] (current)              ht[1] (rehash target)            │
│  ┌──────────┐                 ┌──────────┐                     │
│  │ bucket 0 │─→ entry─→ NULL  │ bucket 0 │─→ NULL              │
│  │ bucket 1 │─→ NULL          │ bucket 1 │─→ entry ─→ NULL     │
│  │ bucket 2 │─→ entry─→entry  │ bucket 2 │─→ NULL              │
│  │ bucket 3 │─→ entry─→ NULL  │ ...      │                     │
│  │ ...      │                 │ bucket N │─→ NULL              │
│  │ bucket N │─→ NULL          └──────────┘                     │
│  └──────────┘                                                   │
│                                                                 │
│  Rehashing: Incremental, 1 bucket per operation                │
│  Load factor trigger: > 1.0 (or > 5.0 during BGSAVE)          │
│  Hash function: SipHash (secure against hash flooding)          │
│                                                                 │
│  Each entry:                                                    │
│  ┌─────────────────────────────────────────┐                   │
│  │ key (SDS string)                        │                   │
│  │ value (robj: string/list/set/zset/hash) │                   │
│  │ next pointer                            │                   │
│  │ metadata (TTL, LRU clock, etc.)         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Doubly Linked List (LRU Eviction)

Redis uses an approximate LRU instead of a true LRU linked list to save memory.
Each key stores a 24-bit LRU clock (last access time in seconds, wrapping ~194 days).

```
┌─────────────────────────────────────────────────────────────────┐
│                  APPROXIMATE LRU MECHANISM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Each key stores: lru_clock (24 bits)                          │
│                                                                 │
│  When eviction is needed:                                      │
│  1. Sample N random keys (default N=5)                         │
│  2. Compute idle time = current_clock - key.lru_clock          │
│  3. Evict the key with the highest idle time                   │
│                                                                 │
│  Eviction pool (optimization in Redis 3.0+):                   │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│  │ k1│ k2│ k3│ k4│ k5│ k6│ k7│ k8│ k9│k10│k11│k12│k13│k14│k15│k16│
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
│    ^                                                         ^  │
│    │ least idle                                  most idle   │  │
│                                                                 │
│  Sorted by idle time; best eviction candidate at the right.    │
│  Pool size: 16 entries; filled across multiple eviction cycles. │
│                                                                 │
│  True LRU vs Approximate LRU:                                  │
│  - True LRU:   O(1) eviction but needs doubly-linked list      │
│                 + hash map = ~80 bytes overhead per key         │
│  - Approx LRU: 24 bits (3 bytes) per key, very close to true  │
│                 LRU with sample size >= 10                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Skip List (Sorted Sets)

```
┌─────────────────────────────────────────────────────────────────┐
│                     SKIP LIST (zskiplist)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 4:  HEAD ─────────────────────────────────→ 90 ─→ NULL  │
│  Level 3:  HEAD ──────────→ 30 ─────────────────→ 90 ─→ NULL  │
│  Level 2:  HEAD ──────────→ 30 ────→ 50 ────────→ 90 ─→ NULL  │
│  Level 1:  HEAD ─→ 10 ───→ 30 ─→ 40→ 50 ─→ 70 ─→ 90 ─→ NULL │
│                                                                 │
│  Max levels: 32 (Redis uses max 64)                            │
│  Probability: p = 0.25 (each level has 25% chance of next)     │
│  Average space: O(n), Average search: O(log n)                 │
│                                                                 │
│  Each node:                                                     │
│  ┌──────────────────────────┐                                  │
│  │ member (SDS string)      │                                  │
│  │ score (double)           │                                  │
│  │ backward pointer         │                                  │
│  │ level[]:                 │                                  │
│  │   forward pointer        │                                  │
│  │   span (distance)        │                                  │
│  └──────────────────────────┘                                  │
│                                                                 │
│  Span: Enables O(log n) ZRANK by summing spans along path.    │
│                                                                 │
│  Encoding optimization:                                        │
│  - Small sorted sets (<128 elements, <64 byte values):         │
│    → Use ziplist (now listpack) for memory efficiency          │
│  - Large sorted sets: → Use skip list + hash table             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Persistence Data Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE OPTIONS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RDB (Redis Database) Snapshot:                                │
│  ┌────────┬──────────┬───────┬───────┬─────┬──────────┬──────┐ │
│  │ REDIS  │ RDB Ver  │ Aux   │ DB    │ Key │ Key-Value│ EOF  │ │
│  │ Magic  │ Number   │ Fields│Select │Count│ Pairs    │ CRC  │ │
│  └────────┴──────────┴───────┴───────┴─────┴──────────┴──────┘ │
│                                                                 │
│  AOF (Append Only File) Log:                                   │
│  ┌───────────────────────────────────────────────────┐         │
│  │ *3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n    │ SET foo bar
│  │ *3\r\n$3\r\nSET\r\n$3\r\nbaz\r\n$5\r\nhello\r\n  │ SET baz hello
│  │ *2\r\n$3\r\nDEL\r\n$3\r\nfoo\r\n                 │ DEL foo
│  │ ...                                               │         │
│  └───────────────────────────────────────────────────┘         │
│                                                                 │
│  AOF fsync policies:                                           │
│  - always:    fsync after every write  (safest, slowest)       │
│  - everysec:  fsync once per second    (balanced, default)     │
│  - no:        let OS decide            (fastest, risky)        │
│                                                                 │
│  Hybrid (Redis 4.0+):                                          │
│  ┌──────────────────────┬───────────────────────┐              │
│  │   RDB Snapshot       │  AOF Tail (recent)    │              │
│  │   (compact binary)   │  (RESP commands)      │              │
│  └──────────────────────┴───────────────────────┘              │
│  Fast reload from RDB + minimal data loss from AOF tail.       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### SDS (Simple Dynamic String)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDS STRING ENCODING                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Standard layout:                                              │
│  ┌──────┬──────┬───────┬─────────────────────────┬────┐        │
│  │ len  │ alloc│ flags │ buf[] (actual string)    │ \0 │        │
│  │(used)│(cap) │(type) │                          │    │        │
│  └──────┴──────┴───────┴─────────────────────────┴────┘        │
│                  ^                                              │
│                  │ SDS pointer points here                     │
│                                                                 │
│  Types (based on string length):                               │
│  - sdshdr5:   unused (too small for header optimization)       │
│  - sdshdr8:   len < 256           (1 byte header fields)       │
│  - sdshdr16:  len < 65536         (2 byte header fields)       │
│  - sdshdr32:  len < 4294967296    (4 byte header fields)       │
│  - sdshdr64:  larger strings      (8 byte header fields)       │
│                                                                 │
│  Benefits over C strings:                                      │
│  - O(1) length retrieval (stored, not computed)                │
│  - Binary safe (no null-terminator issues)                     │
│  - Reduced reallocation via pre-allocation strategy            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. High-Level Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                       │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ App Srv 1│  │ App Srv 2│  │ App Srv 3│  │ App Srv N│  │  Worker  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │              │          │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐    │
│  │  Smart   │  │  Smart   │  │  Smart   │  │  Smart   │  │  Smart   │    │
│  │  Client  │  │  Client  │  │  Client  │  │  Client  │  │  Client  │    │
│  │(Jedis/   │  │(Lettuce/ │  │(redis-py)│  │(ioredis) │  │(go-redis)│    │
│  │ Redisson)│  │ Redisson)│  │          │  │          │  │          │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │              │          │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────┘
        │              │              │              │              │
        │     Smart clients maintain slot-to-node mapping           │
        │     CRC16(key) mod 16384 → slot → node                  │
        │              │              │              │              │
┌───────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────┐
│       ▼              ▼              ▼              ▼              ▼          │
│                      CACHE CLUSTER (Hash Slot Ring)                          │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     HASH SLOT DISTRIBUTION                            │  │
│  │  Slots 0-5460          Slots 5461-10922        Slots 10923-16383     │  │
│  │  ┌──────────────┐      ┌──────────────┐        ┌──────────────┐      │  │
│  │  │  Master A     │      │  Master B     │        │  Master C     │      │  │
│  │  │  (node-1)     │      │  (node-2)     │        │  (node-3)     │      │  │
│  │  │  128 GB RAM   │      │  128 GB RAM   │        │  128 GB RAM   │      │  │
│  │  └──┬───────┬───┘      └──┬───────┬───┘        └──┬───────┬───┘      │  │
│  │     │       │              │       │                │       │          │  │
│  │     ▼       ▼              ▼       ▼                ▼       ▼          │  │
│  │  ┌──────┐┌──────┐      ┌──────┐┌──────┐        ┌──────┐┌──────┐      │  │
│  │  │Rep A1││Rep A2│      │Rep B1││Rep B2│        │Rep C1││Rep C2│      │  │
│  │  │(AZ-2)││(AZ-3)│      │(AZ-1)││(AZ-3)│        │(AZ-1)││(AZ-2)│      │  │
│  │  └──────┘└──────┘      └──────┘└──────┘        └──────┘└──────┘      │  │
│  │                                                                       │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │               GOSSIP PROTOCOL (Cluster Bus)           │                   │
│  │                                                       │                   │
│  │  Port: data_port + 10000 (e.g., 6379 → 16379)       │                   │
│  │  Protocol: Binary, custom Redis Cluster Bus           │                   │
│  │  Messages: PING, PONG, MEET, FAIL, PUBLISH           │                   │
│  │  Frequency: Every node pings 1 random node/sec       │                   │
│  │  Failure detection: pfail → fail (quorum based)      │                   │
│  │                                                       │                   │
│  │  Node A ←──PING/PONG──→ Node B                       │                   │
│  │  Node B ←──PING/PONG──→ Node C                       │                   │
│  │  Node C ←──PING/PONG──→ Node A                       │                   │
│  │                                                       │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                      REQUEST LIFECYCLE                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client sends: SET user:1001 '{"name":"Alice"}' EX 3600      │
│                                                                  │
│  2. Smart Client:                                                │
│     slot = CRC16("user:1001") mod 16384 = 7438                  │
│     node = slot_map[7438] → Master B (node-2)                   │
│                                                                  │
│  3. Connection to Master B (multiplexed TCP):                    │
│     Client ──RESP3──→ Master B                                  │
│                                                                  │
│  4. Master B processes command:                                  │
│     a. Parse RESP protocol                                      │
│     b. Look up command table → SET handler                      │
│     c. Check memory limit (maxmemory)                           │
│     d. If over limit → run eviction policy                      │
│     e. Insert into hash table                                   │
│     f. Set TTL in expires dict                                  │
│     g. Append to AOF buffer (if enabled)                        │
│     h. Propagate to replicas (replication stream)               │
│     i. Return "+OK\r\n" to client                              │
│                                                                  │
│  5. If MOVED (wrong node):                                      │
│     Master B → "-MOVED 7438 192.168.1.2:6379"                  │
│     Client updates slot map                                     │
│     Client retries to correct node                              │
│                                                                  │
│  6. If ASK (slot migrating):                                    │
│     Master B → "-ASK 7438 192.168.1.3:6379"                    │
│     Client sends ASKING + command to target node                │
│     (does NOT update slot map permanently)                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Single Node Internal Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    SINGLE NODE INTERNALS                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   EVENT LOOP (ae.c)                       │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │ File Events  │  │ Time Events │  │ Before/After    │  │   │
│  │  │ (I/O)       │  │ (cron jobs) │  │ Sleep Hooks     │  │   │
│  │  │             │  │             │  │                  │  │   │
│  │  │ - accept()  │  │ - Eviction  │  │ - Cluster cron  │  │   │
│  │  │ - read()    │  │ - Lazy free │  │ - Replication   │  │   │
│  │  │ - write()   │  │ - AOF fsync │  │ - Key expiry    │  │   │
│  │  │ - replicas  │  │ - RDB save  │  │ - Stats update  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │   │
│  │                                                           │   │
│  │  I/O Multiplexing: epoll (Linux), kqueue (BSD/macOS)     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐      │
│  │ Main Thread │  │ I/O Threads  │  │ Background Threads│      │
│  │ (commands)  │  │ (Redis 6.0+) │  │                   │      │
│  │             │  │              │  │ - bio_close_file  │      │
│  │ Single-     │  │ Read/parse   │  │ - bio_aof_fsync   │      │
│  │ threaded    │  │ and write    │  │ - bio_lazy_free    │      │
│  │ command     │  │ responses    │  │                   │      │
│  │ execution   │  │ in parallel  │  │ Handles slow I/O  │      │
│  │             │  │              │  │ without blocking  │      │
│  └─────────────┘  └──────────────┘  └───────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MEMORY LAYOUT                          │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │   │
│  │  │ Dict     │  │ Expires  │  │ Blocking │  │ Watched │  │   │
│  │  │ (keyspace│  │ Dict     │  │ Keys     │  │ Keys    │  │   │
│  │  │  db[0])  │  │ (TTLs)  │  │ (BLPOP)  │  │ (WATCH) │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │   │
│  │                                                           │   │
│  │  Memory allocator: jemalloc (default)                    │   │
│  │  Fragmentation ratio target: < 1.5                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Deep Dive

### 8.1 Hash Slot Architecture

Redis Cluster divides the keyspace into **16384 hash slots**. Each key is mapped to a
slot using `CRC16(key) mod 16384`. Slots are then assigned to master nodes.

#### Why 16384 Slots?

- Gossip messages include a bitmap of all slots (16384 bits = 2 KB per message).
- 65536 slots would require 8 KB per gossip message -- too much bandwidth.
- 16384 is enough for up to ~1000 nodes (16 slots per node minimum).
- Power of 2 enables fast modulo via bitwise AND.

#### Slot Distribution

```
┌────────────────────────────────────────────────────────────────────┐
│                    HASH SLOT ASSIGNMENT                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  3-node cluster:                                                  │
│  ┌────────────────┬────────────────┬────────────────┐             │
│  │   Node A        │   Node B        │   Node C        │             │
│  │   Slots 0-5460  │   Slots 5461-   │   Slots 10923- │             │
│  │   (5461 slots)  │   10922         │   16383        │             │
│  │                 │   (5462 slots)  │   (5461 slots) │             │
│  └────────────────┴────────────────┴────────────────┘             │
│                                                                    │
│  Key mapping example:                                             │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  Key: "user:1001"                                    │         │
│  │  CRC16("user:1001") = 0x1D12 = 7442                 │         │
│  │  7442 mod 16384 = 7442                               │         │
│  │  Slot 7442 → Node B (5461-10922)                    │         │
│  │                                                      │         │
│  │  Key: "session:abc123"                               │         │
│  │  CRC16("session:abc123") = 0x2FA7 = 12199           │         │
│  │  12199 mod 16384 = 12199                             │         │
│  │  Slot 12199 → Node C (10923-16383)                  │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Slot Migration (Online Resharding)

When adding a node or rebalancing, slots are migrated live without downtime:

```
┌────────────────────────────────────────────────────────────────────┐
│                     SLOT MIGRATION PROCESS                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Moving slot 7438 from Node B (source) to Node D (target):       │
│                                                                    │
│  Step 1: Mark slot as migrating/importing                         │
│  ┌──────────────────┐          ┌──────────────────┐               │
│  │  Node B (source) │          │  Node D (target) │               │
│  │  MIGRATING 7438  │          │  IMPORTING 7438  │               │
│  └──────────────────┘          └──────────────────┘               │
│                                                                    │
│  Step 2: Migrate keys one by one (MIGRATE command)                │
│  ┌──────────────────┐  DUMP+RESTORE  ┌──────────────────┐        │
│  │  Node B           │──────────────→│  Node D           │        │
│  │  key1 ──→ (moved) │               │  key1 (received)  │        │
│  │  key2 ──→ (moved) │               │  key2 (received)  │        │
│  │  key3 (pending)   │               │                   │        │
│  └──────────────────┘               └──────────────────┘        │
│                                                                    │
│  Step 3: During migration, requests handled as:                   │
│  - Key exists on source → serve from source                      │
│  - Key NOT on source → reply ASK → client asks target            │
│  - New writes to migrated keys → go to target (after ASKING)     │
│                                                                    │
│  Step 4: All keys migrated → update slot ownership                │
│  ┌──────────────────┐          ┌──────────────────┐               │
│  │  Node B           │          │  Node D           │               │
│  │  (no slot 7438)   │          │  OWNS slot 7438  │               │
│  └──────────────────┘          └──────────────────┘               │
│                                                                    │
│  Step 5: Cluster gossip propagates new mapping to all nodes.      │
│  Clients update slot map via CLUSTER SLOTS or MOVED redirect.    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 8.2 Eviction Policies

#### Approximate LRU

Redis does NOT maintain a true LRU list. Instead, it uses a sampling-based approach:

```
┌────────────────────────────────────────────────────────────────────┐
│                   APPROXIMATE LRU ALGORITHM                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Configuration: maxmemory-policy allkeys-lru                      │
│                 maxmemory-samples 5 (default, can increase to 10) │
│                                                                    │
│  Algorithm:                                                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. Memory usage exceeds maxmemory                            │ │
│  │ 2. Randomly sample 5 keys from keyspace                     │ │
│  │ 3. Compute idle_time = now - lru_clock for each             │ │
│  │ 4. Insert into eviction pool (sorted by idle_time)          │ │
│  │ 5. Evict key with highest idle_time from pool               │ │
│  │ 6. Repeat until enough memory is freed                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Accuracy comparison (% of true LRU evicted correctly):           │
│  ┌─────────────────────────────────────────────────────┐         │
│  │  Sample Size │ Accuracy │ Notes                      │         │
│  │─────────────│──────────│────────────────────────────│         │
│  │  5 (default) │ ~90%     │ Good enough for most cases │         │
│  │  10          │ ~97%     │ Near-perfect LRU behavior  │         │
│  │  20          │ ~99%     │ Diminishing returns        │         │
│  └─────────────────────────────────────────────────────┘         │
│                                                                    │
│  Eviction pool visualization:                                     │
│                                                                    │
│  Idle time →   low                              high              │
│  ┌─────────────────────────────────────────────────────┐         │
│  │ k12 │ k45 │ k78 │ k3  │ k91 │ k22 │ ... │ k67    │         │
│  │ 2s  │ 5s  │ 12s │ 30s │ 45s │ 60s │     │ 300s   │         │
│  └─────────────────────────────────────────────────────┘         │
│                                         Evict this one ──→ ^^^   │
│                                                                    │
│  Policies available:                                              │
│  - volatile-lru:   LRU among keys WITH expiry set                │
│  - allkeys-lru:    LRU among ALL keys                            │
│  - volatile-random: Random among keys with expiry                │
│  - allkeys-random:  Random among all keys                        │
│  - volatile-ttl:    Evict keys closest to expiring               │
│  - noeviction:      Return OOM error on writes                   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### LFU (Least Frequently Used) with Decay

Redis 4.0+ introduced LFU, which tracks access frequency with a logarithmic counter
and applies time-based decay to prevent stale popular keys from never being evicted.

```
┌────────────────────────────────────────────────────────────────────┐
│                     LFU WITH DECAY ALGORITHM                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Each key stores 24 bits of LFU data:                             │
│  ┌──────────────────────────────────────┐                         │
│  │  16 bits: last decrement time (min)  │                         │
│  │   8 bits: logarithmic counter (0-255)│                         │
│  └──────────────────────────────────────┘                         │
│                                                                    │
│  Logarithmic counter increment:                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ counter = current_counter                                    │ │
│  │ p = 1.0 / (counter * lfu_log_factor + 1)                    │ │
│  │ if random() < p:                                             │ │
│  │     counter = min(counter + 1, 255)                          │ │
│  │                                                              │ │
│  │ With lfu_log_factor=10 (default):                            │ │
│  │ ┌───────────────────────────────────┐                        │ │
│  │ │ Accesses │ Counter │ Note         │                        │ │
│  │ │       1  │    1    │              │                        │ │
│  │ │      10  │    2    │              │                        │ │
│  │ │     100  │    8    │              │                        │ │
│  │ │   1,000  │   18    │              │                        │ │
│  │ │  10,000  │   38    │              │                        │ │
│  │ │ 100,000  │  107    │              │                        │ │
│  │ │   1M+    │  255    │ Saturated    │                        │ │
│  │ └───────────────────────────────────┘                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Decay mechanism (halving over time):                             │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ elapsed_minutes = now - last_decrement_time                  │ │
│  │ decay = elapsed_minutes / lfu_decay_time                     │ │
│  │ counter = max(counter - decay, 0)                            │ │
│  │                                                              │ │
│  │ With lfu_decay_time=1 (default):                             │ │
│  │   Counter loses 1 for every minute without access.          │ │
│  │   A key with counter=100 unused for 100 min → counter=0    │ │
│  │                                                              │ │
│  │ Example: Flash sale item                                    │ │
│  │ T=0:     Massive traffic → counter = 200                   │ │
│  │ T=30min: Sale ends, no access → counter = 170              │ │
│  │ T=100min: → counter = 100                                  │ │
│  │ T=200min: → counter = 0 → eligible for eviction            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  When to use LFU over LRU:                                        │
│  - Workloads with varying key popularity over time               │
│  - When recently accessed != frequently accessed                 │
│  - Scan-resistant: a full key scan won't pollute the cache       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 8.3 Replication

#### Master-Replica Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    REPLICATION ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                     MASTER NODE                            │    │
│  │                                                            │    │
│  │  ┌──────────────────────────────────────────────────────┐ │    │
│  │  │ Replication Backlog (circular buffer, 1 MB default)  │ │    │
│  │  │ ┌──────────────────────────────────────────────────┐ │ │    │
│  │  │ │ offset 100 │ offset 200 │ ... │ offset 5000     │ │ │    │
│  │  │ │ SET a 1    │ DEL b      │     │ INCR counter    │ │ │    │
│  │  │ └──────────────────────────────────────────────────┘ │ │    │
│  │  │ master_repl_offset: 5000                             │ │    │
│  │  └──────────────────────────────────────────────────────┘ │    │
│  │                                                            │    │
│  │  Writes propagated to replicas in real-time:              │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐                      │    │
│  │  │ SET a 1│→ │ DEL b  │→ │ INCR c │→ (replication stream)│    │
│  │  └────────┘  └────────┘  └────────┘                      │    │
│  └───────────────┬────────────────┬──────────────────────────┘    │
│                  │ async          │ async                          │
│                  ▼                ▼                                │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │   REPLICA 1       │  │   REPLICA 2       │                      │
│  │                   │  │                   │                      │
│  │  Applies commands │  │  Applies commands │                      │
│  │  in order.        │  │  in order.        │                      │
│  │                   │  │                   │                      │
│  │  replica_offset:  │  │  replica_offset:  │                      │
│  │  4800 (200 behind)│  │  4950 (50 behind) │                      │
│  │                   │  │                   │                      │
│  │  Read-only by     │  │  Read-only by     │                      │
│  │  default          │  │  default          │                      │
│  └──────────────────┘  └──────────────────┘                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Synchronization Modes

```
┌────────────────────────────────────────────────────────────────────┐
│                   SYNCHRONIZATION MODES                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  FULL SYNCHRONIZATION (initial sync or backlog overflow):         │
│  ┌─────────────┐                        ┌────────────────┐        │
│  │   Master     │                        │    Replica      │        │
│  │             │ ──1. PSYNC ? -1──────→ │ (new replica)  │        │
│  │             │ ←── FULLRESYNC id off─ │               │        │
│  │ BGSAVE      │                        │               │        │
│  │ (fork)      │                        │               │        │
│  │   ↓         │ ──2. Send RDB file───→ │ Load RDB      │        │
│  │             │                        │               │        │
│  │ Buffered    │ ──3. Send buffer──────→ │ Apply buffer  │        │
│  │ writes      │                        │               │        │
│  │             │ ──4. Stream ongoing───→ │ Apply stream  │        │
│  └─────────────┘                        └────────────────┘        │
│                                                                    │
│  PARTIAL RESYNCHRONIZATION (after brief disconnect):              │
│  ┌─────────────┐                        ┌────────────────┐        │
│  │   Master     │                        │    Replica      │        │
│  │             │ ←── PSYNC id offset── │ (reconnecting) │        │
│  │             │                        │               │        │
│  │  Check: is  │                        │               │        │
│  │  offset in  │ ── CONTINUE ────────→ │               │        │
│  │  backlog?   │ ── Send missing ────→ │ Apply delta   │        │
│  │             │     commands           │               │        │
│  └─────────────┘                        └────────────────┘        │
│                                                                    │
│  If offset is NOT in backlog → falls back to FULL SYNC.          │
│  Tuning: repl-backlog-size (increase for unreliable networks).   │
│                                                                    │
│  WAIT COMMAND (semi-synchronous replication):                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ WAIT numreplicas timeout                                     │ │
│  │                                                              │ │
│  │ Example: WAIT 2 100                                          │ │
│  │ → Block until 2 replicas have ACK'd the latest write        │ │
│  │ → Or timeout after 100ms                                    │ │
│  │ → Returns number of replicas that ACK'd                     │ │
│  │                                                              │ │
│  │ Use case: When you need stronger (not full) consistency     │ │
│  │ Caveat: Does NOT guarantee consistency during failover      │ │
│  │         (replica may lose ACK'd writes if promoted before   │ │
│  │          persisting to disk)                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 8.4 Cache Patterns

#### Cache-Aside (Lazy Loading)

The application manages the cache explicitly. Most common pattern.

```
┌────────────────────────────────────────────────────────────────────┐
│                    CACHE-ASIDE PATTERN                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  READ PATH (Cache Hit):                                           │
│  ┌──────────┐   1. GET key    ┌───────────┐                      │
│  │          │ ───────────────→│           │                      │
│  │  App     │   2. Return val │   Cache   │                      │
│  │  Server  │ ←───────────────│           │                      │
│  │          │                 └───────────┘                      │
│  └──────────┘                                                     │
│                                                                    │
│  READ PATH (Cache Miss):                                          │
│  ┌──────────┐   1. GET key    ┌───────────┐                      │
│  │          │ ───────────────→│           │                      │
│  │          │   2. MISS       │   Cache   │                      │
│  │  App     │ ←───────────────│           │                      │
│  │  Server  │                 └───────────┘                      │
│  │          │   3. SELECT ... ┌───────────┐                      │
│  │          │ ───────────────→│           │                      │
│  │          │   4. Return row │ Database  │                      │
│  │          │ ←───────────────│           │                      │
│  │          │                 └───────────┘                      │
│  │          │   5. SET key val┌───────────┐                      │
│  │          │ ───────────────→│           │                      │
│  │          │                 │   Cache   │                      │
│  └──────────┘                 └───────────┘                      │
│                                                                    │
│  WRITE PATH:                                                      │
│  ┌──────────┐   1. UPDATE ... ┌───────────┐                      │
│  │  App     │ ───────────────→│ Database  │                      │
│  │  Server  │ ←───────────────│           │                      │
│  │          │   2. DEL key    ┌───────────┐                      │
│  │          │ ───────────────→│   Cache   │  (invalidate)        │
│  └──────────┘                 └───────────┘                      │
│                                                                    │
│  Pros: Only caches data that is actually requested.              │
│  Cons: Cache miss = 3 round trips. Stale data possible.         │
│  Note: DELETE on write is safer than SET (avoids race).          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Write-Through

Every write goes to both cache and database synchronously.

```
┌────────────────────────────────────────────────────────────────────┐
│                   WRITE-THROUGH PATTERN                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  WRITE PATH:                                                      │
│  ┌──────────┐   1. Write      ┌───────────┐   2. Write           │
│  │  App     │ ───────────────→│  Cache     │ ───────────────→     │
│  │  Server  │                 │  (write-   │   ┌───────────┐     │
│  │          │                 │  through   │   │ Database  │     │
│  │          │   4. ACK        │  proxy)    │   │           │     │
│  │          │ ←───────────────│           │ ←─┤  3. ACK   │     │
│  └──────────┘                 └───────────┘   └───────────┘     │
│                                                                    │
│  The cache layer is responsible for persisting to the DB.         │
│  ACK to client only after both cache and DB are written.         │
│                                                                    │
│  Pros: Cache is always consistent with DB. No stale reads.       │
│  Cons: Higher write latency (cache + DB on every write).         │
│        Writes to infrequently-read keys waste cache space.       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Write-Behind (Write-Back)

Writes go to cache immediately; database is updated asynchronously.

```
┌────────────────────────────────────────────────────────────────────┐
│                   WRITE-BEHIND PATTERN                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  WRITE PATH:                                                      │
│  ┌──────────┐   1. Write      ┌───────────┐                      │
│  │  App     │ ───────────────→│   Cache    │                      │
│  │  Server  │   2. ACK (fast) │           │                      │
│  │          │ ←───────────────│           │                      │
│  └──────────┘                 └─────┬─────┘                      │
│                                     │                              │
│                                     │ 3. Async batch write        │
│                                     │    (after delay or batch)   │
│                                     ▼                              │
│                               ┌───────────┐                      │
│                               │ Database  │                      │
│                               │           │                      │
│                               └───────────┘                      │
│                                                                    │
│  Write queue (in cache or separate):                              │
│  ┌──────┬──────┬──────┬──────┬──────┐                            │
│  │ w1   │ w2   │ w3   │ w4   │ w5   │ → batch INSERT/UPDATE     │
│  │ t=0s │ t=1s │ t=2s │ t=3s │ t=4s │   every 5 seconds         │
│  └──────┴──────┴──────┴──────┴──────┘                            │
│                                                                    │
│  Coalescing: Multiple writes to same key → only last value       │
│  written to DB. Reduces DB write amplification.                  │
│                                                                    │
│  Pros: Very fast writes. Reduces DB load via batching.           │
│  Cons: Risk of data loss if cache crashes before DB write.       │
│        Complex failure handling. Inconsistency window.           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Read-Through

Cache is responsible for loading data from the database on misses.

```
┌────────────────────────────────────────────────────────────────────┐
│                   READ-THROUGH PATTERN                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────┐   1. GET key    ┌───────────┐                      │
│  │  App     │ ───────────────→│   Cache    │                      │
│  │  Server  │                 │ (has data  │                      │
│  │          │   2. Return     │  loader)   │                      │
│  │          │ ←───────────────│           │                      │
│  └──────────┘                 └───────────┘                      │
│                                  HIT ↑                            │
│                                                                    │
│  On cache MISS:                                                   │
│  ┌──────────┐   1. GET key    ┌───────────┐   2. Load from DB    │
│  │  App     │ ───────────────→│   Cache    │ ───────────────→     │
│  │  Server  │                 │           │   ┌───────────┐     │
│  │          │                 │  3. Store  │   │ Database  │     │
│  │          │   4. Return     │  in cache  │ ←─┤  Return   │     │
│  │          │ ←───────────────│           │   └───────────┘     │
│  └──────────┘                 └───────────┘                      │
│                                                                    │
│  The app only talks to the cache, never directly to the DB.      │
│  Cache has a "data loader" function configured for each type.    │
│                                                                    │
│  Pros: Simpler application code. Cache handles all loading.      │
│  Cons: First request always slow. Cache library must support.    │
│  Examples: Caffeine (Java), Guava Cache, NCache (read-through).  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### Cache Stampede Prevention

```
┌────────────────────────────────────────────────────────────────────┐
│                 CACHE STAMPEDE PREVENTION                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Problem: Hot key expires → 1000 concurrent requests → 1000     │
│  simultaneous database queries for the same data.                │
│                                                                    │
│  ┌─────────┐ GET "hot_key"  ┌───────┐  MISS!  ┌──────────┐     │
│  │ Req 1   │───────────────→│ Cache │─────────→│ Database │     │
│  │ Req 2   │───────────────→│       │─────────→│ (1000    │     │
│  │ Req 3   │───────────────→│       │─────────→│ queries!)│     │
│  │ ...     │───────────────→│       │─────────→│          │     │
│  │ Req 1000│───────────────→│       │─────────→│          │     │
│  └─────────┘                └───────┘          └──────────┘     │
│                                                                    │
│  Solution 1: Locking (Mutex)                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. Cache miss → try SETNX "lock:hot_key" "1" EX 5          │ │
│  │ 2. If lock acquired:                                        │ │
│  │    → Load from DB, SET in cache, release lock               │ │
│  │ 3. If lock NOT acquired:                                    │ │
│  │    → Sleep 50ms, retry GET from cache                       │ │
│  │    → If still miss after retries, fall through to DB        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Solution 2: Probabilistic Early Expiration (PER)                 │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ On each cache hit, with probability that increases as TTL   │ │
│  │ approaches 0:                                               │ │
│  │                                                              │ │
│  │   should_refresh = (now - fetch_time) * beta >= TTL         │ │
│  │     where beta = random(0, 1) * log(random())              │ │
│  │                                                              │ │
│  │ Refresh in background before actual expiry. Only one        │ │
│  │ thread statistically wins the "lottery" to refresh.         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Solution 3: Background refresh                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ - Set TTL to 2x the desired refresh interval               │ │
│  │ - Background job refreshes at 1x interval                  │ │
│  │ - Cache is never truly empty for hot keys                  │ │
│  │ - Trade-off: may cache data nobody reads                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Partitioning

### Hash Slot Partitioning (Redis Cluster)

```
┌────────────────────────────────────────────────────────────────────┐
│                    PARTITIONING STRATEGIES                          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Strategy 1: HASH SLOTS (Redis Cluster - recommended)             │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ slot = CRC16(key) mod 16384                                  │ │
│  │                                                              │ │
│  │ Advantages:                                                  │ │
│  │ - Deterministic: any client can compute the target node     │ │
│  │ - Fine-grained: 16384 slots can be individually migrated    │ │
│  │ - No single point of failure (no external coordinator)      │ │
│  │ - Online resharding: move slots without downtime            │ │
│  │                                                              │ │
│  │ Disadvantages:                                              │ │
│  │ - Multi-key operations only work within same slot           │ │
│  │ - 16384 slots limits practical cluster to ~1000 nodes       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Strategy 2: CONSISTENT HASHING (Memcached / client-side)         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                                                              │ │
│  │          Node A (v1, v2, v3)                                 │ │
│  │             ╱                                                │ │
│  │           ╱        Ring (0 to 2^32)                          │ │
│  │      ┌──╱────────────────────────┐                          │ │
│  │      │ A-v1        A-v2          │                          │ │
│  │      │       B-v1       C-v2     │                          │ │
│  │      │  C-v1       A-v3          │                          │ │
│  │      │       B-v2       B-v3     │                          │ │
│  │      │            C-v3           │                          │ │
│  │      └───────────────────────────┘                          │ │
│  │                                                              │ │
│  │ Each physical node has multiple virtual nodes (vnodes)       │ │
│  │ on the ring for better distribution.                        │ │
│  │                                                              │ │
│  │ Key hashed → walk clockwise → first node = owner.           │ │
│  │ Adding/removing a node only affects adjacent keys.          │ │
│  │                                                              │ │
│  │ Advantages:                                                  │ │
│  │ - Minimal key movement when adding/removing nodes           │ │
│  │ - No centralized slot map needed                            │ │
│  │                                                              │ │
│  │ Disadvantages:                                              │ │
│  │ - Harder to rebalance precisely                             │ │
│  │ - Virtual nodes add complexity                              │ │
│  │ - No native support in Redis Cluster                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  HASH TAGS (forcing keys to same slot):                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ If key contains {...}, only the text inside {} is hashed.   │ │
│  │                                                              │ │
│  │ Examples:                                                    │ │
│  │   "user:{1001}:profile" → CRC16("1001") → slot X           │ │
│  │   "user:{1001}:sessions" → CRC16("1001") → slot X          │ │
│  │   "user:{1001}:cart" → CRC16("1001") → slot X              │ │
│  │                                                              │ │
│  │ All three keys land on the same slot → same node.           │ │
│  │ Enables multi-key operations (MGET, Lua scripts, pipeline). │ │
│  │                                                              │ │
│  │ Caveat: Overuse creates hot spots if one hash tag has       │ │
│  │ disproportionately many keys.                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 10. Caching Strategy

### Client-Side Caching (Redis 6.0+ Tracking)

```
┌────────────────────────────────────────────────────────────────────┐
│                  CLIENT-SIDE CACHING                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Redis 6.0+ supports server-assisted client-side caching:        │
│                                                                    │
│  ┌──────────────┐                         ┌─────────────────┐    │
│  │ App Server   │                         │  Redis Server    │    │
│  │              │                         │                  │    │
│  │ ┌──────────┐ │   1. CLIENT TRACKING ON │                  │    │
│  │ │ L1 Cache │ │ ───────────────────────→│ Tracking table:  │    │
│  │ │ (local   │ │                         │ key → [client1,  │    │
│  │ │  memory) │ │   2. GET user:1001      │        client2]  │    │
│  │ │          │ │ ───────────────────────→│                  │    │
│  │ │ user:1001│ │   3. "Alice"            │                  │    │
│  │ │ = "Alice"│ │ ←───────────────────────│                  │    │
│  │ └──────────┘ │                         │                  │    │
│  │              │                         │ (another client  │    │
│  │              │   4. INVALIDATE         │  modifies key)   │    │
│  │              │      ["user:1001"]      │                  │    │
│  │              │ ←───────────────────────│ SET user:1001    │    │
│  │ ┌──────────┐ │                         │ "Bob"            │    │
│  │ │ L1 Cache │ │                         │                  │    │
│  │ │ (evict   │ │                         │                  │    │
│  │ │ user:1001│ │                         │                  │    │
│  │ └──────────┘ │                         │                  │    │
│  └──────────────┘                         └─────────────────┘    │
│                                                                    │
│  Modes:                                                           │
│  - Default mode: Server tracks exact keys per client.            │
│  - Broadcasting mode: BCAST prefix; server broadcasts            │
│    invalidations for all keys matching prefix to all clients.    │
│                                                                    │
│  Benefits:                                                        │
│  - Near-zero latency for cached keys (local memory access).      │
│  - Reduces Redis traffic and network round-trips.                │
│  - Server-assisted invalidation keeps local cache fresh.         │
│                                                                    │
│  Caveats:                                                         │
│  - Server memory overhead for tracking table.                    │
│  - Invalidation messages consume bandwidth.                      │
│  - Client must handle RESP3 push notifications.                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Two-Tier L1/L2 Caching

```
┌────────────────────────────────────────────────────────────────────┐
│                   TWO-TIER L1/L2 CACHE                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  L1: In-Process Cache (per app instance)                  │     │
│  │  Technology: Caffeine (Java), lru-cache (Node), dict (Py) │     │
│  │  Size: 100 MB - 1 GB (limited by JVM/process heap)       │     │
│  │  Latency: ~100 ns (nanoseconds)                          │     │
│  │  Hit rate target: 50-80% of requests                     │     │
│  │  TTL: Short (30s-5min) to limit staleness                │     │
│  └────────────────────────────┬─────────────────────────────┘     │
│                               │ L1 MISS                           │
│                               ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  L2: Distributed Cache (Redis Cluster)                    │     │
│  │  Technology: Redis, Memcached                             │     │
│  │  Size: 100 GB - 10 TB (across cluster)                   │     │
│  │  Latency: ~500 us (microseconds) including network       │     │
│  │  Hit rate target: 90-99% of L1 misses                    │     │
│  │  TTL: Longer (5min - 24hr)                               │     │
│  └────────────────────────────┬─────────────────────────────┘     │
│                               │ L2 MISS                           │
│                               ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Database (PostgreSQL, MySQL, etc.)                       │     │
│  │  Latency: 5-50 ms                                        │     │
│  │  Populate both L2 and L1 on DB read                      │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                    │
│  Effective hit rate calculation:                                  │
│  L1 hit: 70%, L2 hit (of L1 misses): 95%                        │
│  Overall hit rate: 70% + (30% * 95%) = 70% + 28.5% = 98.5%     │
│  DB queries: only 1.5% of total requests                         │
│                                                                    │
│  Invalidation strategy:                                           │
│  - On DB write: DELETE from L2 (Redis)                           │
│  - L2 invalidation → Redis pub/sub to all app instances          │
│  - Each app instance evicts from L1 on notification              │
│  - Or use Redis 6.0+ client-side caching with TRACKING           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 11. Replication and Consistency

### Asynchronous Replication (Default)

```
┌────────────────────────────────────────────────────────────────────┐
│                CONSISTENCY MODEL                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Redis provides EVENTUAL CONSISTENCY by default.                  │
│                                                                    │
│  Timeline of a write:                                             │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ T=0ms: Client sends SET key value to Master                  │ │
│  │ T=0.1ms: Master writes to memory, returns OK to client       │ │
│  │ T=0.3ms: Master streams command to Replica 1                 │ │
│  │ T=0.5ms: Replica 1 applies command                           │ │
│  │ T=0.8ms: Master streams command to Replica 2                 │ │
│  │ T=1.0ms: Replica 2 applies command                           │ │
│  │                                                              │ │
│  │ Window of inconsistency: 0.1ms - 1.0ms (during this window  │ │
│  │ a read from a replica may return stale data)                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Read-your-writes guarantee:                                      │
│  - Read from same master → always consistent                     │
│  - Read from replica → may be stale                              │
│  - Use WAIT for stronger guarantees (still not linearizable)     │
│                                                                    │
│  WAIT for stronger consistency:                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ SET user:1001 "Alice"                                        │ │
│  │ WAIT 1 100  # Wait for at least 1 replica, timeout 100ms    │ │
│  │ → Returns 1 (one replica confirmed)                          │ │
│  │                                                              │ │
│  │ Note: WAIT blocks the client but not the server.            │ │
│  │ Other clients can still execute commands during WAIT.        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Split-Brain Scenario

```
┌────────────────────────────────────────────────────────────────────┐
│                    SPLIT-BRAIN PROBLEM                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Network partition splits cluster:                                │
│                                                                    │
│  Partition A:                    │  Partition B:                   │
│  ┌───────────────────┐          │  ┌───────────────────┐          │
│  │ Master (isolated) │          │  │ Replica 1          │          │
│  │                   │  ──X──   │  │ (promoted to       │          │
│  │ Client C1 writes  │          │  │  new master)       │          │
│  │ to old master     │          │  │                   │          │
│  │                   │          │  │ Client C2 writes  │          │
│  │ SET key "A"       │          │  │ SET key "B"       │          │
│  └───────────────────┘          │  └───────────────────┘          │
│                                 │                                  │
│  After partition heals:                                           │
│  - Old master discovers new master exists.                        │
│  - Old master demotes itself to replica.                          │
│  - Old master's writes during partition are LOST.                │
│  - key = "B" (new master's value wins).                          │
│                                                                    │
│  Mitigation: min-replicas-to-write                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ min-replicas-to-write 1                                      │ │
│  │ min-replicas-max-lag 10                                      │ │
│  │                                                              │ │
│  │ Master refuses writes if fewer than 1 replica is reachable  │ │
│  │ and replica lag > 10 seconds.                                │ │
│  │                                                              │ │
│  │ Effect: Isolated master stops accepting writes → fewer      │ │
│  │ lost writes. Client gets error instead of silent data loss. │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  NODE_TIMEOUT and its impact:                                     │
│  - cluster-node-timeout 15000 (15 seconds default)               │
│  - If a master is unreachable for > NODE_TIMEOUT by majority:    │
│    → Marked as FAIL                                              │
│    → Replica initiates failover election                         │
│  - Longer timeout = fewer false failovers but longer downtime.   │
│  - Shorter timeout = faster failover but risk of flapping.       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 12. Fault Tolerance

### Automatic Failover

```
┌────────────────────────────────────────────────────────────────────┐
│                   AUTOMATIC FAILOVER PROCESS                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Step 1: Failure Detection                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Node B pings Master A → no response                          │ │
│  │ Node B marks Master A as PFAIL (probable failure)            │ │
│  │                                                              │ │
│  │ Node B gossips PFAIL to Nodes C, D, E                       │ │
│  │ When majority (quorum) of masters agree:                    │ │
│  │   PFAIL → FAIL (confirmed failure)                          │ │
│  │                                                              │ │
│  │ Quorum = N/2 + 1 masters must agree.                        │ │
│  │ With 5 masters: need 3 PFAIL reports.                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Step 2: Replica Election                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Eligible replicas of failed master request votes:            │ │
│  │                                                              │ │
│  │ Replica A1: "I have offset 4950, vote for me!"              │ │
│  │ Replica A2: "I have offset 4800, vote for me!"              │ │
│  │                                                              │ │
│  │ Priority: replica with highest replication offset wins       │ │
│  │ (least data loss). Ties broken by run ID.                   │ │
│  │                                                              │ │
│  │ Each master votes for at most 1 replica per epoch.          │ │
│  │ Replica needs majority of master votes to be promoted.      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Step 3: Promotion                                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Winning replica (A1):                                        │ │
│  │ 1. Stops replicating from old master                        │ │
│  │ 2. Promotes itself: REPLICAOF NO ONE                        │ │
│  │ 3. Claims old master's hash slots                           │ │
│  │ 4. Broadcasts new config epoch via gossip                   │ │
│  │ 5. Starts accepting writes                                  │ │
│  │                                                              │ │
│  │ Other nodes:                                                 │ │
│  │ - Update slot mapping to point to new master                │ │
│  │ - Redirect clients via MOVED responses                      │ │
│  │ - Remaining replicas replicate from new master              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Step 4: Old Master Recovery                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ When old Master A comes back online:                         │ │
│  │ - Discovers it has been replaced (lower config epoch)       │ │
│  │ - Automatically becomes a replica of new Master A1          │ │
│  │ - Syncs missing data from new master                        │ │
│  │ - Cluster returns to desired replica count                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Total failover time:                                             │
│  - Detection: cluster-node-timeout (default 15s)                 │
│  - Election: 1-2 seconds                                         │
│  - Promotion: < 1 second                                         │
│  - Total: ~15-20 seconds (adjustable)                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Retry and Recovery Strategies

```
┌────────────────────────────────────────────────────────────────────┐
│                  CLIENT RETRY STRATEGIES                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  On connection failure:                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Retry with exponential backoff + jitter:                     │ │
│  │                                                              │ │
│  │   delay = min(base * 2^attempt + random(0, jitter), max)    │ │
│  │                                                              │ │
│  │   Attempt 1: 100ms + rand(0, 50ms)                          │ │
│  │   Attempt 2: 200ms + rand(0, 50ms)                          │ │
│  │   Attempt 3: 400ms + rand(0, 50ms)                          │ │
│  │   Attempt 4: 800ms + rand(0, 50ms)                          │ │
│  │   Attempt 5: 1600ms + rand(0, 50ms) → give up or circuit   │ │
│  │                                         breaker opens        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  On MOVED redirect:                                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. Update local slot map for the redirected slot             │ │
│  │ 2. Retry immediately to the correct node                    │ │
│  │ 3. After several MOVEDs, refresh entire slot map            │ │
│  │    via CLUSTER SLOTS                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  On ASK redirect (during migration):                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. Send ASKING command to target node                        │ │
│  │ 2. Immediately send original command to target node          │ │
│  │ 3. Do NOT update local slot map (migration is temporary)    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Circuit breaker pattern:                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ CLOSED → (failures > threshold) → OPEN                      │ │
│  │                                     │                        │ │
│  │ ┌──────────────────────────────────┘                        │ │
│  │ │ (timeout expires)                                          │ │
│  │ ▼                                                            │ │
│  │ HALF-OPEN → (success) → CLOSED                              │ │
│  │     │                                                        │ │
│  │     └─── (failure) → OPEN                                   │ │
│  │                                                              │ │
│  │ When OPEN: return fallback (stale cache, default, error)    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 13. Scalability

### Horizontal Scaling (Adding Nodes + Migrating Slots)

```
┌────────────────────────────────────────────────────────────────────┐
│                   HORIZONTAL SCALING                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Before: 3 masters, uneven load on Node B                        │
│  ┌──────────────┬──────────────┬──────────────┐                  │
│  │ Node A       │ Node B       │ Node C       │                  │
│  │ 5461 slots   │ 5462 slots   │ 5461 slots   │                  │
│  │ CPU: 40%     │ CPU: 85%     │ CPU: 45%     │                  │
│  │ MEM: 50 GB   │ MEM: 110 GB  │ MEM: 55 GB   │                  │
│  └──────────────┴──────────────┴──────────────┘                  │
│                                                                    │
│  After: Add Node D, rebalance                                     │
│  ┌────────────┬────────────┬────────────┬────────────┐           │
│  │ Node A     │ Node B     │ Node C     │ Node D     │           │
│  │ 4096 slots │ 4096 slots │ 4096 slots │ 4096 slots │           │
│  │ CPU: 30%   │ CPU: 55%   │ CPU: 35%   │ CPU: 40%   │           │
│  │ MEM: 40 GB │ MEM: 70 GB │ MEM: 42 GB │ MEM: 50 GB │           │
│  └────────────┴────────────┴────────────┴────────────┘           │
│                                                                    │
│  Process:                                                         │
│  1. redis-cli --cluster add-node new_host:6379 existing:6379     │
│  2. redis-cli --cluster rebalance existing:6379                  │
│  3. Tool calculates optimal slot distribution                    │
│  4. Migrates slots in background (MIGRATE with pipeline)         │
│  5. Updates slot ownership via gossip                            │
│                                                                    │
│  Migration speed:                                                 │
│  - ~1000-5000 keys/sec per migration stream                     │
│  - Parallelizable across slots                                   │
│  - Can be throttled to reduce impact on live traffic             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Read Replicas for Read Scaling

```
┌────────────────────────────────────────────────────────────────────┐
│                  READ REPLICA SCALING                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Read-heavy workload (95% reads):                                 │
│                                                                    │
│  ┌──────────────┐                                                 │
│  │   Master      │ ←── Writes (5%)                                │
│  │   (node-1)    │                                                 │
│  └──┬───────┬───┘                                                 │
│     │       │                                                      │
│     ▼       ▼                                                      │
│  ┌──────┐┌──────┐┌──────┐                                        │
│  │Rep 1 ││Rep 2 ││Rep 3 │ ←── Reads (95%) distributed            │
│  │(AZ-2)││(AZ-3)││(AZ-1)│     across replicas                    │
│  └──────┘└──────┘└──────┘                                        │
│                                                                    │
│  Client configuration:                                            │
│  READONLY                   # Allow reads from replicas           │
│  READWRITE                  # Revert to master-only reads         │
│                                                                    │
│  Smart client routing:                                            │
│  - Writes → always to master                                     │
│  - Reads → round-robin across replicas (or latency-based)        │
│                                                                    │
│  Trade-off: Replicas may serve slightly stale data                │
│  (typically < 1ms lag in same datacenter).                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Pipelining for Throughput

```
┌────────────────────────────────────────────────────────────────────┐
│                     PIPELINING                                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Without pipeline (sequential):                                   │
│  ┌────────┐          ┌────────┐                                   │
│  │ Client │          │ Server │                                   │
│  │        │─ SET a ─→│        │                                   │
│  │        │←─ OK ────│        │  RTT: 0.5ms each                 │
│  │        │─ SET b ─→│        │                                   │
│  │        │←─ OK ────│        │  Total: 4 x 0.5ms = 2ms          │
│  │        │─ SET c ─→│        │  for 4 commands                   │
│  │        │←─ OK ────│        │                                   │
│  │        │─ SET d ─→│        │                                   │
│  │        │←─ OK ────│        │                                   │
│  └────────┘          └────────┘                                   │
│                                                                    │
│  With pipeline (batched):                                         │
│  ┌────────┐          ┌────────┐                                   │
│  │ Client │          │ Server │                                   │
│  │        │─ SET a ─→│        │                                   │
│  │        │─ SET b ─→│        │  Only 1 RTT for all 4 commands   │
│  │        │─ SET c ─→│        │                                   │
│  │        │─ SET d ─→│        │  Total: 0.5ms + 4 x 0.01ms      │
│  │        │←─ OK ────│        │       = ~0.54ms                   │
│  │        │←─ OK ────│        │                                   │
│  │        │←─ OK ────│        │  ~4x faster (more with bigger    │
│  │        │←─ OK ────│        │  batches)                         │
│  └────────┘          └────────┘                                   │
│                                                                    │
│  Optimal pipeline size: 100-1000 commands per batch              │
│  Diminishing returns beyond ~1000 (memory and latency trade-off) │
│                                                                    │
│  Cluster-aware pipelining:                                        │
│  - Group commands by target node (based on slot)                 │
│  - Send pipeline to each node in parallel                        │
│  - Merge responses in original order                             │
│                                                                    │
│  Throughput improvement:                                          │
│  Without pipeline: ~50,000 ops/sec (RTT-bound)                   │
│  With pipeline:    ~500,000 ops/sec (CPU-bound)                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 14. Monitoring

### Key Metrics

```
┌────────────────────────────────────────────────────────────────────┐
│                   MONITORING METRICS                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  CACHE EFFECTIVENESS                                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Metric             │ Formula / Command        │ Target       │ │
│  │────────────────────│──────────────────────────│─────────────│ │
│  │ Hit Ratio           │ hits / (hits + misses)   │ > 95%       │ │
│  │ Miss Ratio          │ misses / (hits + misses) │ < 5%        │ │
│  │ Eviction Rate       │ evicted_keys/sec         │ Low/stable  │ │
│  │ Expired Keys Rate   │ expired_keys/sec         │ Stable      │ │
│  │ Keys Count          │ DBSIZE / INFO keyspace   │ Predictable │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  PERFORMANCE                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Metric             │ Source                   │ Target       │ │
│  │────────────────────│──────────────────────────│─────────────│ │
│  │ Ops/sec             │ INFO stats               │ > 100K      │ │
│  │ Latency (p50)       │ redis-cli --latency      │ < 0.5ms    │ │
│  │ Latency (p99)       │ LATENCY HISTORY          │ < 1ms      │ │
│  │ Slow queries        │ SLOWLOG GET              │ 0          │ │
│  │ Connected clients   │ INFO clients             │ < max      │ │
│  │ Blocked clients     │ INFO clients             │ ~0         │ │
│  │ Command rate        │ INFO commandstats        │ -          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  MEMORY                                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Metric             │ Source                   │ Target       │ │
│  │────────────────────│──────────────────────────│─────────────│ │
│  │ Used memory         │ INFO memory              │ < maxmemory │ │
│  │ Memory fragmentation│ mem_fragmentation_ratio  │ 1.0 - 1.5  │ │
│  │ RSS (Resident Set)  │ used_memory_rss          │ < physical  │ │
│  │ Peak memory         │ used_memory_peak         │ < maxmemory │ │
│  │ Eviction count      │ evicted_keys             │ Low         │ │
│  │ Object encoding     │ OBJECT ENCODING key      │ Optimal     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  REPLICATION                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Metric             │ Source                   │ Target       │ │
│  │────────────────────│──────────────────────────│─────────────│ │
│  │ Replication offset  │ INFO replication         │ Close match │ │
│  │ Replication lag     │ master_offset - slave_   │ < 1 second  │ │
│  │                    │ offset                    │             │ │
│  │ Connected replicas  │ connected_slaves         │ = expected  │ │
│  │ Sync status         │ master_sync_in_progress │ 0 (idle)    │ │
│  │ Repl backlog active │ repl_backlog_active     │ 1           │ │
│  │ Repl backlog size   │ repl_backlog_size       │ Adequate    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  CLUSTER                                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Metric             │ Source                   │ Target       │ │
│  │────────────────────│──────────────────────────│─────────────│ │
│  │ Cluster state       │ CLUSTER INFO             │ ok          │ │
│  │ Slots assigned      │ cluster_slots_assigned   │ 16384       │ │
│  │ Slots OK            │ cluster_slots_ok         │ 16384       │ │
│  │ Known nodes         │ cluster_known_nodes      │ = expected  │ │
│  │ Messages sent/recv  │ cluster_stats_messages_* │ Stable      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Alerting Thresholds:                                             │
│  - Hit ratio < 90%: WARNING (investigate cold keys or eviction)  │
│  - Memory > 85% maxmemory: WARNING                               │
│  - Memory > 95% maxmemory: CRITICAL                              │
│  - Eviction rate spike: WARNING (may cause latency)              │
│  - Replication lag > 5 sec: WARNING                              │
│  - Replication lag > 30 sec: CRITICAL                            │
│  - Connected replicas < expected: CRITICAL                       │
│  - Cluster state != ok: CRITICAL                                 │
│  - Fragmentation ratio > 1.5: WARNING (run MEMORY PURGE)        │
│  - p99 latency > 5ms: WARNING (check slow log)                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 15. Trade-offs

### Redis vs Memcached

```
┌────────────────────────────────────────────────────────────────────┐
│                   REDIS vs MEMCACHED                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┬───────────────────┬────────────────────┐    │
│  │ Feature           │ Redis              │ Memcached           │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Data structures   │ Strings, Hashes,   │ Strings only       │    │
│  │                  │ Lists, Sets, Sorted│                    │    │
│  │                  │ Sets, Streams,     │                    │    │
│  │                  │ HyperLogLog, etc.  │                    │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Threading model   │ Single-threaded    │ Multi-threaded     │    │
│  │                  │ (I/O threads in    │ (better multi-core │    │
│  │                  │ 6.0+)              │ utilization)       │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Persistence       │ RDB, AOF, Hybrid   │ None (pure cache)  │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Replication       │ Master-replica     │ None (built-in)    │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Clustering        │ Redis Cluster      │ Client-side        │    │
│  │                  │ (hash slots)       │ consistent hashing │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Max value size    │ 512 MB             │ 1 MB (default)     │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Eviction          │ LRU, LFU, Random,  │ LRU only           │    │
│  │                  │ TTL, noeviction    │                    │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Pub/Sub           │ Yes                │ No                 │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Lua scripting     │ Yes                │ No                 │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Transactions      │ MULTI/EXEC         │ CAS (compare-and- │    │
│  │                  │                   │ swap)              │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Memory efficiency │ Higher overhead    │ Slab allocator,    │    │
│  │                  │ per key            │ more efficient for │    │
│  │                  │                   │ uniform sizes      │    │
│  │──────────────────│───────────────────│────────────────────│    │
│  │ Ecosystem         │ Rich (Sentinel,    │ Simple, focused    │    │
│  │                  │ Cluster, Modules)  │                    │    │
│  └──────────────────┴───────────────────┴────────────────────┘    │
│                                                                    │
│  When to choose Redis:                                            │
│  - Need rich data structures beyond simple key-value             │
│  - Need persistence (even if cache, for faster restart)          │
│  - Need pub/sub, streams, or Lua scripting                       │
│  - Need built-in replication and clustering                      │
│  - Need atomic operations on complex data types                  │
│                                                                    │
│  When to choose Memcached:                                        │
│  - Simple key-value caching with known access patterns           │
│  - Need multi-threaded performance on single node                │
│  - Memory efficiency is critical with uniform value sizes        │
│  - Already have external service discovery / consistent hashing  │
│  - Operational simplicity (fewer knobs to tune)                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Persistence vs Pure In-Memory

```
┌────────────────────────────────────────────────────────────────────┐
│                PERSISTENCE TRADE-OFFS                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│                 No Persistence         With Persistence            │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Performance  │ Highest (no disk I/O) │ Slight overhead      │  │
│  │              │                       │ (fork, fsync)        │  │
│  │──────────────│───────────────────────│─────────────────────│  │
│  │ Restart time │ Cold start (empty)    │ Warm start (load    │  │
│  │              │ Must repopulate from  │ from RDB/AOF)       │  │
│  │              │ database              │ Seconds to minutes  │  │
│  │──────────────│───────────────────────│─────────────────────│  │
│  │ Data safety  │ All lost on crash     │ Configurable loss   │  │
│  │              │                       │ window (0 to 1 sec) │  │
│  │──────────────│───────────────────────│─────────────────────│  │
│  │ Memory usage │ 100% for data         │ ~2x during BGSAVE   │  │
│  │              │                       │ (fork COW overhead) │  │
│  │──────────────│───────────────────────│─────────────────────│  │
│  │ Use case     │ True cache (rebuild-  │ Session store,      │  │
│  │              │ able from source)     │ job queues, primary │  │
│  │              │                       │ data store          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  RDB fork() considerations:                                       │
│  - fork() creates a child process with copy-on-write pages       │
│  - During BGSAVE, writes cause page copies (COW overhead)        │
│  - Rule: reserve 50% more RAM than data size for BGSAVE          │
│  - On 128 GB node with 100 GB data: need ~150 GB virtual memory  │
│  - Alternative: AOF with no-rewrite avoids fork entirely         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Single-Threaded vs Multi-Threaded

```
┌────────────────────────────────────────────────────────────────────┐
│             SINGLE-THREADED vs MULTI-THREADED                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Redis (single-threaded command execution):                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Advantages:                                                  │ │
│  │ - No locks, no race conditions, no context switching         │ │
│  │ - Predictable latency (no lock contention spikes)           │ │
│  │ - Simpler code, fewer bugs                                  │ │
│  │ - Atomicity for free (each command runs to completion)      │ │
│  │                                                              │ │
│  │ Disadvantages:                                              │ │
│  │ - Single core bottleneck (~100K-250K ops/sec)               │ │
│  │ - Slow commands (KEYS *, large SORT) block everything       │ │
│  │ - Cannot leverage multiple CPU cores for computation        │ │
│  │                                                              │ │
│  │ Mitigation (Redis 6.0+):                                    │ │
│  │ - I/O threads: read requests and write responses in         │ │
│  │   parallel across threads                                   │ │
│  │ - Command execution remains single-threaded                 │ │
│  │ - Result: ~2x throughput improvement                        │ │
│  │                                                              │ │
│  │ Scale-out: Run multiple Redis instances per server          │ │
│  │ (1 per CPU core) instead of multi-threading                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Memcached (multi-threaded):                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Advantages:                                                  │ │
│  │ - Leverages all CPU cores on a single machine               │ │
│  │ - Higher throughput on a single instance                    │ │
│  │                                                              │ │
│  │ Disadvantages:                                              │ │
│  │ - Global cache lock (slab lock per class)                   │ │
│  │ - Lock contention under high concurrency                    │ │
│  │ - More complex code, harder to extend                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  Emerging: Redis 8+ / KeyDB / Dragonfly                           │
│  - Multi-threaded shared-nothing architectures                   │
│  - Each thread owns a subset of the keyspace                     │
│  - No cross-thread locking needed                                │
│  - Dragonfly claims ~25x Redis throughput on single node         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 16. Interview Questions

### Q1: How does Redis achieve sub-millisecond latency?

**Answer:**

1. **In-memory storage**: All data resides in RAM. Memory access is ~100ns vs ~10ms for disk.
2. **Single-threaded execution**: No lock contention, no context switching. Each command
   runs atomically without synchronization overhead.
3. **Efficient data structures**: Hash tables with O(1) lookups, skip lists with O(log n)
   for sorted operations, pre-allocated SDS strings to avoid repeated allocations.
4. **I/O multiplexing**: Uses epoll/kqueue to handle thousands of connections in a single
   thread without blocking.
5. **RESP protocol**: Simple, binary-safe protocol with minimal parsing overhead.
6. **Zero-copy where possible**: Shared objects for small integers (0-9999), avoiding
   memory allocation for common values.
7. **Pipelining**: Amortizes network RTT across multiple commands, keeping the CPU fed.

---

### Q2: How does Redis Cluster handle resharding without downtime?

**Answer:**

1. **Mark slots**: Source node marks slot as MIGRATING, target marks it as IMPORTING.
2. **Key-by-key migration**: Each key is atomically moved using DUMP (serialize) on source
   and RESTORE (deserialize) on target, then deleted from source.
3. **During migration**:
   - If the key exists on source: serve normally from source.
   - If the key does NOT exist on source: reply with `-ASK target_node`. Client sends
     `ASKING` + command to the target.
   - New keys for the migrating slot can be created on either node (source if not yet
     migrated, target after ASKING).
4. **Completion**: After all keys are moved, slot ownership is updated in the cluster
   config. All nodes learn via gossip. Clients get `MOVED` responses and update slot maps.
5. **No data loss**: Each key is atomically present on exactly one node at any time.

---

### Q3: Explain the differences between cache avalanche, cache stampede, and cache penetration.

**Answer:**

| Problem | Definition | Cause | Solution |
|---------|-----------|-------|----------|
| **Avalanche** | Large number of keys expire simultaneously, overwhelming the database | TTLs set to same value (e.g., midnight expiry) | Add random jitter to TTL: `TTL = base + random(0, spread)` |
| **Stampede** | Single hot key expires, many concurrent requests hit DB | Popular key expiration | Mutex lock (SETNX), probabilistic early refresh, background pre-warming |
| **Penetration** | Requests for keys that will NEVER exist in cache or DB | Attacker queries non-existent IDs | Bloom filter to check existence, cache null results with short TTL, input validation |

**Avalanche** is about volume (many keys at once), **stampede** is about concurrency (many
requests for one key), and **penetration** is about non-existent data bypassing cache.

---

### Q4: How can Redis be single-threaded yet handle 100K+ ops/sec?

**Answer:**

The bottleneck for most network services is NOT CPU but network I/O and system calls. Redis
operates entirely in memory, so each command takes only a few microseconds of CPU time:

- `GET`: Hash lookup = ~0.5 microseconds
- `SET`: Hash insert = ~1 microsecond
- At 1 microsecond per command, a single core can handle ~1M commands/second theoretically

In practice, network I/O and protocol parsing reduce this to ~100K-250K ops/sec. Redis 6.0+
introduces I/O threads to parallelize read/write I/O while keeping command execution
single-threaded, pushing throughput to ~500K+ ops/sec.

The real comparison: a database doing 1 command at 5ms (disk + parse + index) gets 200 ops/sec
per core. Redis at 1 microsecond gets 1,000,000 ops/sec per core. The 5000x difference is
purely because of in-memory access vs disk access.

---

### Q5: How do you handle hot keys in a distributed cache?

**Answer:**

A "hot key" is a key receiving disproportionately high traffic (e.g., trending topic, flash
sale item), creating a bottleneck on the single node that owns the key's slot.

**Solutions:**

1. **Read replicas with READONLY**: Spread read traffic across replicas. For a key on
   a master with 3 replicas, you get 4x read capacity.

2. **Local (L1) caching**: Cache hot keys in application memory (Caffeine, in-process
   HashMap with short TTL). Reduces Redis traffic by 50-80%.

3. **Key replication / fan-out**: Create N copies of the key with suffix:
   `hot_key:1`, `hot_key:2`, ..., `hot_key:N`. Client randomly selects one.
   Distributes load across N different slots/nodes.

4. **Client-side caching (Redis 6.0+)**: Use `CLIENT TRACKING` to cache the key locally
   with server-assisted invalidation.

5. **Rate limiting + coalescing**: When cache misses, use a single-flight pattern -- only
   one goroutine/thread fetches from DB, others wait for the result.

---

### Q6: Explain Redis persistence options and when to use each.

**Answer:**

- **No persistence**: Pure cache. Data is expendable and can be rebuilt from source of truth.
  Use when: session caching, computed results, CDN edge cache.

- **RDB only**: Point-in-time snapshots every N seconds (after M changes). Compact binary
  format, fast loading. Data loss = changes since last snapshot (up to minutes).
  Use when: Backup/disaster recovery, cache warm-up after restart.

- **AOF only (everysec)**: Logs every write command, fsync every second. At most 1 second
  of data loss. Larger files, slower restart (must replay all commands).
  Use when: Session stores, leaderboards, moderate durability needs.

- **AOF (always)**: fsync after every write. Zero data loss. Significant performance hit.
  Use when: Financial data, critical counters (but consider a real database instead).

- **Hybrid (RDB + AOF)**: RDB for fast loading, AOF tail for recent changes. Best of both.
  Use when: Production systems needing both fast restart and minimal data loss.
  This is the recommended default for Redis 4.0+.

---

### Q7: How does the Redis eviction pool work?

**Answer:**

Before Redis 3.0, eviction sampled N random keys and evicted the one with the highest idle
time. This was repeated every time memory was needed. The problem: each eviction cycle was
independent; a good eviction candidate found in one cycle but not the worst might be lost.

Redis 3.0+ introduced the **eviction pool** (size 16):

1. When eviction is needed, sample `maxmemory-samples` random keys (default 5).
2. For each sampled key, compute its idle time (LRU) or frequency (LFU).
3. Insert the key into the eviction pool, which is sorted by eviction priority.
4. The pool accumulates candidates across multiple eviction cycles.
5. Evict the key with the highest priority (most idle / least frequent) from the pool.
6. This "best effort" accumulation across cycles closely approximates true LRU/LFU.

With pool + sample size of 10, Redis achieves ~97% accuracy compared to true LRU, while
using only 24 bits per key instead of ~80 bytes for a linked list entry.

---

### Q8: What happens during a Redis Cluster failover?

**Answer:**

1. **Detection**: Each node pings random peers every second. If a node doesn't respond
   within `cluster-node-timeout` (default 15s), the pinging node marks it as PFAIL.
2. **Gossip**: PFAIL state is gossiped. When a majority of masters agree a node is PFAIL,
   it's promoted to FAIL (hard failure).
3. **Election**: Replicas of the failed master wait a random delay (based on replication
   offset -- the most up-to-date replica waits the shortest). Each replica requests votes
   from all masters. A replica needs a majority of master votes.
4. **Promotion**: The winning replica executes `REPLICAOF NO ONE`, claims the failed
   master's slots, increments the config epoch, and broadcasts the new configuration.
5. **Convergence**: All nodes update their slot map. Clients receive `MOVED` redirections
   and update their cached slot map.
6. **Recovery**: When the old master comes back, it detects it's been replaced (lower
   config epoch) and automatically becomes a replica of the new master.

Total time: ~15-20 seconds (dominated by `cluster-node-timeout`).

---

### Q9: How would you implement a distributed rate limiter using Redis?

**Answer:**

**Sliding window with sorted set:**
```
-- Lua script for atomic rate limiting
local key = KEYS[1]
local window = tonumber(ARGV[1])  -- window size in seconds
local limit = tonumber(ARGV[2])    -- max requests
local now = tonumber(ARGV[3])      -- current timestamp (ms)

-- Remove entries outside the window
redis.call('ZREMRANGEBYSCORE', key, 0, now - window * 1000)

-- Count requests in current window
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, now .. ':' .. math.random())
    redis.call('EXPIRE', key, window)
    return 1  -- allowed
else
    return 0  -- rate limited
end
```

**Token bucket with INCR + TTL:**
```
-- Simple fixed-window rate limiter
local key = "ratelimit:" .. KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
if current > limit then
    return 0  -- rate limited
end
return 1  -- allowed
```

The Lua script approach is preferred because the entire operation is atomic on the server,
avoiding race conditions that would occur with multiple round trips.

---

### Q10: How do you handle cache warming after a Redis restart?

**Answer:**

1. **RDB/AOF persistence**: If enabled, Redis reloads data from disk on restart. This is
   the simplest approach -- data survives restart automatically.

2. **Pre-warming script**: On startup, query the database for the top N most accessed keys
   and populate the cache before serving traffic. Use pipelining for speed.

3. **Gradual warm-up behind load balancer**: Add the restarted node to the cluster but route
   only a fraction of traffic to it initially. As its cache fills, increase the traffic
   share. This prevents cache miss storms.

4. **RDB transfer from replica**: Before restarting a master, take an RDB snapshot from a
   replica. After restart, load that RDB. Avoids cold-start entirely.

5. **Shadow traffic**: Replay production read traffic to the new node without serving
   responses. The cache fills with real access patterns.

6. **Avoid thundering herd**: Add random jitter to TTLs when pre-warming to prevent all
   keys from expiring at the same time later.

---

### Q11: What is the difference between MOVED and ASK redirections?

**Answer:**

| Aspect | MOVED | ASK |
|--------|-------|-----|
| Meaning | "Slot X permanently lives on Node Y" | "Slot X is being migrated; try Node Y for this key" |
| Client action | Update slot map permanently, retry to Node Y | Send ASKING + command to Node Y, do NOT update slot map |
| When seen | After resharding is complete, or client has stale map | During active slot migration |
| Frequency | Should be rare after initial discovery | Temporary, only during migration |

**ASK flow**: Client sends command to source node. Source node doesn't have the key (already
migrated). Source replies `-ASK slot target`. Client sends `ASKING` to target (tells target
"I know this slot isn't fully mine yet, but serve this key anyway"), then sends the command.
This is a one-time redirect -- the next command for the same slot goes back to source first.

---

### Q12: How would you design cache invalidation for a microservices architecture?

**Answer:**

1. **Event-driven invalidation**: When a service updates its database, it publishes an event
   (via Kafka, RabbitMQ, or Redis Streams). Consuming services that cache that data
   subscribe and invalidate/update their cache entries.

2. **CDC (Change Data Capture)**: Use Debezium or similar to capture database changes and
   stream them to a cache invalidation service. Guarantees no missed invalidations (even
   if the application crashes after DB write but before publishing event).

3. **TTL-based eventual consistency**: Set short TTLs (30s-5min) on all cache entries.
   Accept that data may be stale for up to TTL duration. Simplest approach when slight
   staleness is acceptable.

4. **Write-through with cache service**: All writes go through a centralized cache service
   that updates both cache and database. Ensures consistency but adds latency and a single
   point of failure.

5. **Version-based invalidation**: Each cache entry includes a version number. On read,
   check if the cached version matches the current version (stored in a lightweight
   version store). Stale versions trigger a cache refresh.

---

### Q13: Explain Redis Cluster's gossip protocol.

**Answer:**

Redis Cluster uses a gossip protocol for decentralized cluster state management:

1. **Cluster bus**: Each node opens a second port (data port + 10000, e.g., 16379) for
   node-to-node binary communication.

2. **PING/PONG**: Every second, each node sends a PING to a randomly selected node. The
   PING contains:
   - The sender's node ID, IP, port, cluster bus port
   - The sender's current config epoch
   - A bitmap of slots the sender is responsible for
   - Flags (master/replica, PFAIL/FAIL status)
   - Information about a few other random nodes (gossip section)

3. **Failure detection**: If a node doesn't respond to PING within `cluster-node-timeout`,
   it's marked PFAIL. The PFAIL state is gossiped. When >50% of masters mark a node as
   PFAIL, it's promoted to FAIL (a definitive failure that triggers failover).

4. **Configuration propagation**: When a node's configuration changes (e.g., new slot
   assignment), it increments its config epoch. During gossip, nodes compare epochs --
   higher epoch wins. This ensures convergence to the latest configuration.

5. **Scalability**: O(N) messages per node per second (N = cluster size). For a 100-node
   cluster, each node sends/receives ~100 gossip messages/second -- manageable bandwidth.

---

### Q14: How do you prevent cache penetration attacks?

**Answer:**

Cache penetration occurs when attackers query keys that don't exist in cache OR database,
bypassing the cache entirely and hitting the database with every request.

**Solutions:**

1. **Bloom filter**: Maintain a Bloom filter of all valid keys. Before querying cache/DB,
   check the filter. If the key is definitely not in the set, return 404 immediately.
   False positive rate of ~1% is acceptable (those few requests hit DB and find nothing).

2. **Cache null results**: When a DB query returns no result, cache a null/empty value with
   a short TTL (30-60 seconds). Subsequent requests for the same non-existent key get
   the cached null without hitting DB. Caveat: if millions of unique non-existent keys are
   queried, this can fill up cache memory.

3. **Input validation**: Validate key format before querying. If your user IDs are UUIDs,
   reject anything that's not a valid UUID. If IDs are sequential integers, reject negative
   or impossibly large values.

4. **Rate limiting**: Limit requests per IP/user. Attackers generating unique non-existent
   keys are throttled before they can overwhelm the database.

5. **Request coalescing**: Use singleflight/dedup to ensure only one DB query is in-flight
   for a given key, even if 1000 concurrent requests arrive for it.

---

### Q15: Design a leaderboard system using Redis sorted sets.

**Answer:**

```
# Add/update player score
ZADD leaderboard 1500 "player:alice"
ZADD leaderboard 2300 "player:bob"
ZADD leaderboard 1800 "player:charlie"

# Increment score atomically
ZINCRBY leaderboard 100 "player:alice"  # Alice now has 1600

# Get top 10 players (descending)
ZREVRANGE leaderboard 0 9 WITHSCORES
# Returns: bob(2300), charlie(1800), alice(1600)

# Get player's rank (0-indexed, descending)
ZREVRANK leaderboard "player:alice"  # Returns 2 (3rd place)

# Get player's score
ZSCORE leaderboard "player:alice"  # Returns 1600

# Get players ranked 50-60 (pagination)
ZREVRANGE leaderboard 49 59 WITHSCORES

# Get players with scores between 1000-2000
ZRANGEBYSCORE leaderboard 1000 2000 WITHSCORES

# Count players with score > 1000
ZCOUNT leaderboard 1000 +inf

# Remove inactive player
ZREM leaderboard "player:charlie"
```

**At scale (millions of players):**
- Single sorted set handles millions of members efficiently (O(log N) operations).
- For sharding: use hash tags `{game:1}:leaderboard` to keep related data on same node.
- For time-based leaderboards (daily/weekly): use separate keys per period, delete old ones.
- For real-time updates: Redis handles ~100K ZINCRBY/sec per node, sufficient for most games.
- For very large leaderboards with approximate ranking: use HyperLogLog for count and
  approximate percentile-based ranking.

---

## Summary

A distributed cache is a critical infrastructure component that sits between applications and
databases, dramatically reducing latency and database load. The key design decisions are:

| Decision | Recommendation |
|----------|---------------|
| Architecture | Hash slot partitioning (16384 slots) with master-replica topology |
| Eviction | Approximate LRU with eviction pool (or LFU for frequency-based workloads) |
| Persistence | Hybrid RDB+AOF for production; none for pure cache |
| Replication | Async replication with WAIT for critical writes |
| Cache pattern | Cache-aside with stampede prevention (mutex or early refresh) |
| Scaling reads | Read replicas + client-side caching (L1/L2) |
| Scaling writes | Add masters + rebalance slots |
| Fault tolerance | Automatic failover with gossip-based failure detection |
| Monitoring | Hit ratio, eviction rate, memory utilization, replication lag |

The system achieves sub-millisecond latency through in-memory storage, single-threaded
execution (avoiding lock contention), and efficient I/O multiplexing. It scales horizontally
by distributing hash slots across nodes and vertically through read replicas and pipelining.
