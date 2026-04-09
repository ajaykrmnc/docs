# Design a Distributed Key-Value Store (Dynamo-Style)

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
9. [Data Partitioning](#9-data-partitioning)
10. [Caching](#10-caching)
11. [Replication and Consistency](#11-replication-and-consistency)
12. [Fault Tolerance](#12-fault-tolerance)
13. [Scalability](#13-scalability)
14. [Monitoring](#14-monitoring)
15. [Trade-offs](#15-trade-offs)
16. [Interview Questions](#16-interview-questions)

---

## 1. Problem Statement

Design a highly available, partition-tolerant distributed key-value store inspired by
Amazon's Dynamo. The system must:

- Provide **always-on write availability** -- writes must never be rejected, even during
  partial failures or network partitions.
- Offer **tunable consistency** so applications can choose their own trade-off between
  consistency and latency on a per-request basis.
- Scale **linearly** by adding commodity hardware -- no special nodes, no single points
  of failure.
- Support **multi-datacenter replication** with eventual convergence.

Real-world systems that follow this architecture: Amazon DynamoDB, Apache Cassandra,
Riak, Voldemort, ScyllaDB.

**Why Dynamo-style?** Traditional RDBMS systems sacrifice availability during partitions
(CP). Dynamo chooses AP: it remains available and writable even when nodes are
unreachable, resolving conflicts after the partition heals.

```
  ┌──────────────────────────────────────────────────────────┐
  │                    CAP Theorem                           │
  │                                                          │
  │              Consistency (C)                             │
  │                   /\                                     │
  │                  /  \                                    │
  │                 /    \                                   │
  │                / CP   \                                  │
  │               / (HBase,\                                 │
  │              / MongoDB) \                                │
  │             /────────────\                               │
  │            /              \                              │
  │           /    CA (RDBMS)  \                             │
  │          /   (impossible    \                            │
  │         /   in distributed)  \                           │
  │        /──────────────────────\                          │
  │  Availability (A)          Partition                     │
  │  AP: Dynamo, Cassandra     Tolerance (P)                │
  └──────────────────────────────────────────────────────────┘
```

---

## 2. Functional Requirements

### Core Operations

| Operation  | Description                                                    |
|------------|----------------------------------------------------------------|
| `put`      | Store a key-value pair with optional metadata (TTL, context)   |
| `get`      | Retrieve value(s) for a key; may return multiple versions      |
| `delete`   | Tombstone a key (soft delete with propagation)                 |

### Consistency Levels (per-request tunable)

| Level      | Behavior                                                       |
|------------|----------------------------------------------------------------|
| `ONE`      | Respond after 1 replica acknowledges. Lowest latency.          |
| `QUORUM`   | Respond after majority (W or R) replicas acknowledge.          |
| `ALL`      | Respond after all N replicas acknowledge. Strongest guarantee. |

### Additional Features

- **TTL (Time-To-Live):** Keys can have an expiration time. Expired keys are purged
  during compaction and filtered on reads.
- **Versioning:** Every write is tagged with a vector clock (or timestamp). Multiple
  concurrent versions may coexist until resolved.
- **Range Queries:** Not a primary feature (this is a hash-based store), but secondary
  indexes can be layered on top.
- **Batch Operations:** Multi-key get/put for throughput optimization.
- **Conditional Writes:** Compare-and-swap using the context (vector clock) returned
  from a prior `get`.

---

## 3. Non-Functional Requirements

| Requirement          | Target                                                  |
|----------------------|---------------------------------------------------------|
| **Availability**     | 99.99% (< 52.6 minutes downtime / year)                |
| **Read Latency**     | p50 < 1ms, p99 < 10ms                                  |
| **Write Latency**    | p50 < 2ms, p99 < 10ms                                  |
| **Scalability**      | Linear throughput scaling with added nodes              |
| **Durability**       | No data loss once acknowledged (WAL + replication)      |
| **Partition Tol.**   | System remains read/write available during partitions   |
| **Data Size**        | Support petabytes of data across the cluster            |
| **Key Size**         | Up to 256 bytes                                         |
| **Value Size**       | Up to 1 MB (typical: 1-10 KB)                           |

### SLA Targets

- 99.9th percentile latency (not averages) -- tail latency matters.
- Zero single points of failure.
- Automated failure detection and recovery within seconds.

---

## 4. Back-of-Envelope Estimation

### Traffic

```
Read throughput:   100,000 requests/sec
Write throughput:   50,000 requests/sec
Total:             150,000 requests/sec
```

### Storage

```
Average value size:          10 KB
Writes per day:              50,000 * 86,400 = 4.32 billion
Raw data per day:            4.32B * 10 KB   = 43.2 TB / day
With 3x replication:         43.2 * 3        = 129.6 TB / day
With 2x compaction overhead: 129.6 * 2       = 259.2 TB / day (peak)
```

### Bandwidth

```
Read bandwidth:   100,000 * 10 KB = 1 GB/s inbound
Write bandwidth:   50,000 * 10 KB = 500 MB/s inbound
Replication:       500 MB/s * 2 (for 2 additional replicas) = 1 GB/s inter-node
Total network:     ~2.5 GB/s = ~20 Gbps
```

### Node Count

```
Per node storage capacity:    4 TB usable (8 TB disks, 50% utilization)
Data per day (replicated):    129.6 TB
30-day retention:             129.6 * 30 = 3,888 TB
Nodes needed (storage):       3,888 / 4 = 972 nodes
Round up for headroom:        ~1,000 nodes

Per node throughput:          ~500 ops/sec (conservative for 10KB values)
Nodes needed (throughput):    150,000 / 500 = 300 nodes
```

### Memory

```
Per node RAM:                  64 GB
MemTable size:                 256 MB (flushed at threshold)
Key cache:                     ~10 GB (hot keys in LRU cache)
Bloom filters:                 ~2 GB (10 bits/key, millions of keys)
OS page cache:                 ~40 GB (SSTable reads)
Overhead:                      ~12 GB
```

---

## 5. API Design

### Put (Write)

```
PUT /v1/kv/{key}

Headers:
  Content-Type: application/octet-stream
  X-Consistency: QUORUM              # ONE | QUORUM | ALL
  X-TTL: 86400                       # optional, seconds
  X-Context: <base64-vector-clock>   # from prior GET, enables conflict detection

Body: <raw value bytes>

Response 200 OK:
{
  "key": "user:12345",
  "version": "vclock:a1b2c3...",
  "timestamp": 1712678400000,
  "replicas_acked": 2
}
```

### Get (Read)

```
GET /v1/kv/{key}

Headers:
  X-Consistency: QUORUM              # ONE | QUORUM | ALL

Response 200 OK:
{
  "key": "user:12345",
  "values": [
    {
      "value": "<base64-encoded>",
      "context": "vclock:a1b2c3...",
      "timestamp": 1712678400000
    }
  ],
  "replicas_read": 2
}
```

When there are conflicting versions (sibling values), the `values` array contains
multiple entries. The client must resolve the conflict and write back with the merged
context.

### Delete

```
DELETE /v1/kv/{key}

Headers:
  X-Consistency: QUORUM
  X-Context: <base64-vector-clock>

Response 200 OK:
{
  "key": "user:12345",
  "tombstone": true,
  "gc_grace_seconds": 864000
}
```

Deletes are **tombstones** -- a special marker that propagates to all replicas. The
tombstone is retained for `gc_grace_seconds` (default 10 days) to ensure all replicas
learn about the deletion, then purged during compaction.

### Internal RPC API (Node-to-Node)

```
// Coordinator -> Replica
rpc ReplicaWrite(key, value, vector_clock, ttl) -> (ack, updated_clock)
rpc ReplicaRead(key)                            -> (value, vector_clock, timestamp)
rpc ReplicaDelete(key, vector_clock)             -> (ack)

// Anti-entropy
rpc MerkleTreeExchange(range, tree_root)         -> (diff_ranges)
rpc StreamRepair(range, missing_keys)            -> (stream of key-value pairs)

// Gossip
rpc GossipDigest(node_states[])                  -> (node_states[])

// Hinted Handoff
rpc DeliverHint(target_node, key, value, clock)  -> (ack)
```

---

## 6. Data Model

### 6.1 LSM Tree (Log-Structured Merge Tree)

The LSM tree is the core on-disk data structure for Dynamo-style stores. It optimizes
for **write throughput** at the cost of slightly more expensive reads.

```
  ┌─────────────────────────────────────────────────────────────┐
  │                     LSM Tree Architecture                   │
  │                                                             │
  │  ┌──────────────┐                                           │
  │  │   MemTable   │  ← In-memory sorted structure (Red-Black  │
  │  │  (Red-Black  │    tree or skip list). All writes go here │
  │  │    Tree)     │    first. Sorted by key.                  │
  │  │  ~256 MB     │                                           │
  │  └──────┬───────┘                                           │
  │         │ flush when full                                   │
  │         v                                                   │
  │  ┌──────────────┐                                           │
  │  │  Immutable   │  ← Previous MemTable being flushed to     │
  │  │  MemTable    │    disk. New writes go to a fresh          │
  │  │              │    MemTable.                               │
  │  └──────┬───────┘                                           │
  │         │ write to disk                                     │
  │         v                                                   │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
  │  │  SSTable L0  │  │  SSTable L0  │  │  SSTable L0  │      │
  │  │  (newest)    │  │              │  │  (oldest)    │      │
  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
  │         │                 │                 │               │
  │         └────────┬────────┘─────────────────┘               │
  │                  │ compaction (merge-sort)                   │
  │                  v                                           │
  │  ┌──────────────────────────────────────────┐               │
  │  │            SSTable Level 1               │               │
  │  │   (non-overlapping key ranges)           │               │
  │  └──────────────────┬───────────────────────┘               │
  │                     │ compaction                             │
  │                     v                                        │
  │  ┌──────────────────────────────────────────┐               │
  │  │            SSTable Level 2               │               │
  │  │   (10x larger than Level 1)              │               │
  │  └──────────────────────────────────────────┘               │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

**Why LSM?**

| Property       | LSM Tree           | B-Tree              |
|----------------|--------------------|----------------------|
| Write speed    | O(1) amortized     | O(log N) random I/O  |
| Read speed     | O(L) levels checked| O(log N)             |
| Write amp.     | 10-30x             | 2-3x                 |
| Space amp.     | Low (compaction)   | ~50% page fill       |
| Concurrency    | Lock-free writes   | Page-level locks     |

### 6.2 Storage Engine

The complete write and read paths through the storage engine:

#### Write Path

```
  Client Write Request
         │
         v
  ┌──────────────┐
  │  Write-Ahead  │  Step 1: Append to WAL (sequential I/O, fsync)
  │  Log (WAL)    │          Guarantees durability before ack.
  │  (append-only)│          WAL is segmented, old segments deleted
  └──────┬───────┘          after MemTable flush.
         │
         v
  ┌──────────────┐
  │   MemTable    │  Step 2: Insert into in-memory sorted structure.
  │  (skip list)  │          O(log N) insert. Serves reads immediately.
  │   256 MB      │
  └──────┬───────┘
         │ when MemTable reaches threshold
         v
  ┌──────────────┐
  │   Immutable   │  Step 3: Freeze current MemTable. Create new one
  │   MemTable    │          for incoming writes. Background thread
  │               │          begins flush.
  └──────┬───────┘
         │ background flush
         v
  ┌──────────────┐
  │   SSTable     │  Step 4: Write sorted key-value pairs to disk.
  │  (Sorted      │          Each SSTable includes:
  │   String      │          - Data blocks (sorted KV pairs)
  │   Table)      │          - Index block (key -> block offset)
  │               │          - Bloom filter (probabilistic membership)
  │               │          - Compression (LZ4 / Snappy / Zstd)
  └──────┬───────┘
         │
         v
  ┌──────────────┐
  │  Compaction   │  Step 5: Periodically merge SSTables:
  │  (background) │          - Remove tombstoned/expired keys
  │               │          - Merge duplicate keys (keep latest)
  │               │          - Reduce read amplification
  └──────────────┘
```

#### Read Path

```
  Client Read Request for key K
         │
         v
  ┌──────────────┐
  │   MemTable    │  Step 1: Check current MemTable. O(log N).
  │               │          If found, return immediately.
  └──────┬───────┘
         │ miss
         v
  ┌──────────────┐
  │  Immutable    │  Step 2: Check immutable MemTable(s), if any.
  │  MemTable(s)  │
  └──────┬───────┘
         │ miss
         v
  ┌──────────────┐
  │  Bloom Filter │  Step 3: For each SSTable (newest first),
  │   Check       │          check Bloom filter.
  │  (~1% FP)     │          If "definitely not present", skip.
  └──────┬───────┘          If "possibly present", proceed.
         │ possibly present
         v
  ┌──────────────┐
  │  Key Cache /  │  Step 4: Check partition key cache for the
  │  Index Cache  │          SSTable offset. Avoids index lookup.
  └──────┬───────┘
         │ miss
         v
  ┌──────────────┐
  │  SSTable      │  Step 5: Binary search the SSTable index block
  │  Index Lookup │          to find the data block containing K.
  └──────┬───────┘
         │
         v
  ┌──────────────┐
  │  Data Block   │  Step 6: Read and decompress the data block.
  │  Read         │          Scan for key K within the block.
  └──────────────┘
```

#### Bloom Filters

A Bloom filter is a space-efficient probabilistic data structure that tests whether an
element is a member of a set. It can have false positives but never false negatives.

```
  Key "user:12345"
       │
       ├── hash1(key) = bit 3    ──┐
       ├── hash2(key) = bit 7    ──┤
       └── hash3(key) = bit 12   ──┤
                                    │
  Bit Array:                        v
  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
  │0│0│0│1│0│0│0│1│0│0│0│0│1│0│0│0│
  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
   0 1 2 3 4 5 6 7 8 9 ...  12

  Lookup: All 3 bits are set → "possibly present"
  If ANY bit is 0 → "definitely not present"
```

**Configuration:**
- 10 bits per key, 3 hash functions: ~1% false positive rate
- 15 bits per key, 4 hash functions: ~0.1% false positive rate
- Memory: ~1.2 GB for 1 billion keys at 10 bits/key

#### Compaction Strategies

**Size-Tiered Compaction (STCS):**
- Group SSTables of similar size into tiers.
- When a tier has enough SSTables (e.g., 4), merge them into one larger SSTable.
- Pros: Good write throughput, simple.
- Cons: High space amplification (up to 2x), wide key-range overlap.

```
  Tier 0:  [S1] [S2] [S3] [S4]     ← 4 small SSTables
                    │
                    v merge
  Tier 1:  [    S1-4 merged    ]    ← 1 larger SSTable
```

**Leveled Compaction (LCS):**
- SSTables organized into levels (L0, L1, L2, ...).
- Each level is 10x the size of the previous.
- L1+ has non-overlapping key ranges.
- When L(n) is full, pick an SSTable from L(n) and merge it with overlapping SSTables
  in L(n+1).
- Pros: Low space amplification, bounded read amplification.
- Cons: Higher write amplification (10-30x).

```
  L0:  [a-z] [a-z] [a-z]           ← Overlapping ranges (from MemTable flushes)
            │
            v compact into L1
  L1:  [a-f] [g-l] [m-r] [s-z]     ← Non-overlapping, sorted ranges
            │
            v compact into L2
  L2:  [a-c][d-f][g-i][j-l][m-o][p-r][s-u][v-z]  ← 10x more SSTables
```

**Time-Window Compaction (TWCS):**
- Groups SSTables by time window (e.g., 1 hour).
- Only compacts SSTables within the same window.
- Ideal for time-series data with TTL -- entire windows can be dropped.

---

## 7. High-Level Architecture

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        Client Application                              │
  │                  (any node can serve as entry point)                    │
  └────────────┬───────────────────────────────────────┬────────────────────┘
               │                                       │
               v                                       v
  ┌────────────────────┐                  ┌────────────────────┐
  │  Load Balancer /   │                  │  Client Library    │
  │  DNS Round Robin   │                  │  (token-aware      │
  │                    │                  │   routing)          │
  └────────┬───────────┘                  └────────┬───────────┘
           │                                       │
           v                                       v
  ┌────────────────────────────────────────────────────────────────────────┐
  │                                                                        │
  │                        Coordinator Node                                │
  │   (any node can be coordinator -- no special role)                     │
  │                                                                        │
  │   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐                 │
  │   │  Request     │  │  Consistency │  │  Failure      │                │
  │   │  Router      │  │  Manager     │  │  Detector     │                │
  │   │  (hash ring  │  │  (W/R/N      │  │  (phi-accrual │                │
  │   │   lookup)    │  │   tracking)  │  │   gossip)     │                │
  │   └──────┬──────┘  └──────┬───────┘  └──────┬───────┘                 │
  │          │                │                  │                          │
  └──────────┼────────────────┼──────────────────┼─────────────────────────┘
             │                │                  │
             v                v                  v
  ┌──────────────────────────────────────────────────────────────────────┐
  │                       Consistent Hash Ring                           │
  │                                                                      │
  │    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐         │
  │    │Node A│    │Node B│    │Node C│    │Node D│    │Node E│         │
  │    │VN:150│    │VN:150│    │VN:150│    │VN:150│    │VN:150│         │
  │    └──┬───┘    └──┬───┘    └──┬───┘    └──┬───┘    └──┬───┘         │
  │       │           │           │           │           │              │
  │  ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐       │
  │  │Storage  │ │Storage  │ │Storage  │ │Storage  │ │Storage  │       │
  │  │Engine   │ │Engine   │ │Engine   │ │Engine   │ │Engine   │       │
  │  │┌──────┐│ │┌──────┐│ │┌──────┐│ │┌──────┐│ │┌──────┐│       │
  │  ││ WAL  ││ ││ WAL  ││ ││ WAL  ││ ││ WAL  ││ ││ WAL  ││       │
  │  │├──────┤│ │├──────┤│ │├──────┤│ │├──────┤│ │├──────┤│       │
  │  ││ Mem  ││ ││ Mem  ││ ││ Mem  ││ ││ Mem  ││ ││ Mem  ││       │
  │  ││Table ││ ││Table ││ ││Table ││ ││Table ││ ││Table ││       │
  │  │├──────┤│ │├──────┤│ │├──────┤│ │├──────┤│ │├──────┤│       │
  │  ││SSTab-││ ││SSTab-││ ││SSTab-││ ││SSTab-││ ││SSTab-││       │
  │  ││les   ││ ││les   ││ ││les   ││ ││les   ││ ││les   ││       │
  │  │└──────┘│ │└──────┘│ │└──────┘│ │└──────┘│ │└──────┘│       │
  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
  │                                                                      │
  │  ┌───────────────────────────────────────────────────────────┐       │
  │  │  Background Services (per node):                          │       │
  │  │  - Gossip Protocol (membership, failure detection)        │       │
  │  │  - Hinted Handoff (deliver pending hints)                 │       │
  │  │  - Anti-Entropy (Merkle tree comparison & repair)         │       │
  │  │  - Compaction (merge SSTables)                            │       │
  │  │  - Read Repair (fix stale replicas on read)               │       │
  │  └───────────────────────────────────────────────────────────┘       │
  └──────────────────────────────────────────────────────────────────────┘
```

### Request Flow (Write)

```
  Client                Coordinator           Node B         Node C         Node D
    │                       │                    │              │              │
    │── PUT(key, val) ─────>│                    │              │              │
    │                       │                    │              │              │
    │                       │── hash(key) ──>  determines preference list:    │
    │                       │                  [B (primary), C, D]            │
    │                       │                    │              │              │
    │                       │── write(k,v) ─────>│              │              │
    │                       │── write(k,v) ──────┼─────────────>│              │
    │                       │── write(k,v) ──────┼──────────────┼─────────────>│
    │                       │                    │              │              │
    │                       │<── ack ────────────│              │              │
    │                       │<── ack ────────────┼──────────────│              │
    │                       │                    │              │     (slow)   │
    │                       │                    │              │              │
    │    (QUORUM: 2 of 3)   │                    │              │              │
    │<── 200 OK ────────────│                    │              │              │
    │                       │                    │              │              │
    │                       │<── ack (late) ─────┼──────────────┼──────────────│
```

---

## 8. Deep Dive

### 8.1 Consistent Hashing with Virtual Nodes

#### The Problem with Naive Hashing

With `node = hash(key) % N`, adding or removing a node changes the modulo, causing
almost all keys to be remapped. This is catastrophic for a distributed store.

#### Consistent Hash Ring

Map both keys and nodes onto the same hash ring (0 to 2^128 - 1). A key is assigned
to the first node encountered clockwise on the ring.

```
                          0 / 2^128
                            │
                        ....│....
                    ...     │     ...
                 ..    Node A (token 15)
               .         ╱  │         .
             .          ╱   │          .
            .      ────╱    │           .
           .      ╱         │            .
          . Node E         │             .
          . (token 230)     │      Node B  .
          .  \              │     (token 60).
           .  \             │       ╱      .
            .  \            │      ╱      .
             .  ─────       │  ───╱      .
               .        \   │  ╱       .
                 ..      \  │╱      ..
                    ...  Node C  ...
                        (token 120)
                    ........│........
                            │
                       Node D
                     (token 170)

  Key hash = 45 → walks clockwise → lands on Node B (token 60)
  Key hash = 130 → walks clockwise → lands on Node D (token 170)
  Key hash = 200 → walks clockwise → lands on Node E (token 230)
```

#### Virtual Nodes (VNodes)

A single physical node owns **multiple tokens** (virtual nodes) on the ring. This
provides:

1. **Even load distribution** -- prevents hotspots from uneven token spacing.
2. **Smooth rebalancing** -- adding a node steals small ranges from many nodes
   instead of one large range from one node.
3. **Heterogeneous hardware** -- powerful nodes get more vnodes.

```
  Physical Node A has vnodes: A1(15), A2(85), A3(195)
  Physical Node B has vnodes: B1(45), B2(120), B3(240)
  Physical Node C has vnodes: C1(60), C2(150), C3(210)

  Ring with vnodes:
  ┌────────────────────────────────────────────────────────┐
  │  0 ──> A1(15) ──> B1(45) ──> C1(60) ──> A2(85) ──>   │
  │  B2(120) ──> C2(150) ──> A3(195) ──> C3(210) ──>     │
  │  B3(240) ──> 0                                         │
  └────────────────────────────────────────────────────────┘

  Recommended: 150-200 vnodes per physical node.
  More vnodes = smoother distribution but more memory for ring metadata.
```

#### Token Assignment and Rebalancing

When a new node joins:

```
  Before (3 nodes, 3 vnodes each = 9 tokens):
  ┌──────────────────────────────────────────┐
  │  [A1]──[B1]──[C1]──[A2]──[B2]──[C2]──   │
  │  [A3]──[B3]──[C3]                        │
  └──────────────────────────────────────────┘

  Node D joins with 3 vnodes:
  ┌──────────────────────────────────────────┐
  │  [A1]──[D1]──[B1]──[C1]──[A2]──[D2]──   │
  │  [B2]──[C2]──[A3]──[D3]──[B3]──[C3]     │
  └──────────────────────────────────────────┘

  D1 steals a portion of B1's range
  D2 steals a portion of B2's range
  D3 steals a portion of B3's range

  Only ~1/N of the data is moved (where N is the number of nodes).
  Data streams from existing owners to D in the background.
```

### 8.2 Quorum Consensus

#### N, W, R Parameters

```
  N = Number of replicas (typically 3)
  W = Write quorum (replicas that must ack a write)
  R = Read quorum (replicas that must respond to a read)

  Strong consistency guarantee: R + W > N
```

**Common configurations:**

| Config         | W | R | Guarantees                     | Use Case           |
|----------------|---|---|--------------------------------|---------------------|
| Strong read    | 1 | 3 | Latest value guaranteed on read | Read-heavy, stale OK on write |
| Strong write   | 3 | 1 | All replicas have latest       | Write-heavy         |
| Balanced       | 2 | 2 | Overlap guarantees freshness   | General purpose     |
| Weak (fast)    | 1 | 1 | No consistency guarantee       | Metrics, logs       |

```
  Example: N=3, W=2, R=2

  Write to key K:
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ Replica 1│    │ Replica 2│    │ Replica 3│
  │  (ack)   │    │  (ack)   │    │ (slow)   │
  └─────────┘    └─────────┘    └─────────┘
       │              │
       └──────┬───────┘
              │
        W=2 satisfied → respond to client

  Read of key K:
  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ Replica 1│    │ Replica 2│    │ Replica 3│
  │  v=5     │    │  v=5     │    │  v=4     │
  │  (fast)  │    │  (fast)  │    │ (slow)   │
  └─────────┘    └─────────┘    └─────────┘
       │              │
       └──────┬───────┘
              │
        R=2 satisfied → return v=5 (latest among responses)
        Trigger read repair for Replica 3 (v=4 is stale)
```

#### Sloppy Quorum and Hinted Handoff

When a node is down, strict quorum would reduce availability. **Sloppy quorum** allows
the coordinator to use the next healthy node on the ring as a temporary stand-in.

```
  Preference list for key K: [B, C, D]
  Node C is DOWN.

  Strict quorum: Only B and D can participate → must wait for both.
  Sloppy quorum: Use E as a stand-in for C.

  ┌─────────┐    ┌─────────┐    ┌─────────┐
  │ Node B   │    │ Node E   │    │ Node D   │
  │ (primary)│    │ (hint    │    │ (primary)│
  │          │    │  for C)  │    │          │
  └─────────┘    └─────────┘    └─────────┘

  Node E stores the value with a "hint" metadata:
  {
    "intended_recipient": "C",
    "key": "K",
    "value": "...",
    "vector_clock": "..."
  }

  When C comes back online:
  1. E detects C is up (via gossip)
  2. E ships all hinted data to C
  3. E deletes the hints
```

### 8.3 Conflict Resolution

#### Vector Clocks

A vector clock is a list of (node, counter) pairs. Every time a node updates a key, it
increments its own counter. Vector clocks establish a **partial ordering** of events.

```
  Initial state: key K does not exist.

  Step 1: Client writes to Node A
  ┌─────────────────────────────────┐
  │  K = "value1"                   │
  │  VC = { A: 1 }                  │
  └─────────────────────────────────┘

  Step 2: Client reads from A, gets VC={A:1}, then writes to Node A
  ┌─────────────────────────────────┐
  │  K = "value2"                   │
  │  VC = { A: 2 }                  │ ← A:1 happened-before A:2
  └─────────────────────────────────┘   (no conflict, A:2 supersedes)

  Step 3: Network partition! Two clients write concurrently:

  Client X writes to Node A:        Client Y writes to Node B:
  (based on VC={A:2})                (based on VC={A:2})
  ┌──────────────────────┐           ┌──────────────────────┐
  │  K = "value3a"       │           │  K = "value3b"       │
  │  VC = { A: 3 }       │           │  VC = { A: 2, B: 1 } │
  └──────────────────────┘           └──────────────────────┘

  Neither version dominates the other:
  - {A:3} vs {A:2, B:1}: A is higher in first, B is higher in second.
  - These are CONCURRENT → CONFLICT!

  Step 4: Client reads key K, receives BOTH versions (siblings):
  ┌───────────────────────────────────────────────┐
  │  values: ["value3a", "value3b"]               │
  │  contexts: [{A:3}, {A:2, B:1}]               │
  └───────────────────────────────────────────────┘

  Step 5: Client resolves conflict (application-specific merge):
  Writes merged value with combined context:
  ┌──────────────────────────────────────────┐
  │  K = "merged_value"                      │
  │  VC = { A: 3, B: 1 }  ← merge of both   │
  │  (written via Node A → { A: 4, B: 1 })  │
  └──────────────────────────────────────────┘
```

**Comparing Vector Clocks:**

```
  VC1 = {A:2, B:3, C:1}
  VC2 = {A:2, B:2, C:1}

  For each node:
    A: 2 >= 2 ✓
    B: 3 >= 2 ✓
    C: 1 >= 1 ✓
  VC1 dominates VC2 → VC2 is stale, discard it.

  VC1 = {A:3, B:1}
  VC2 = {A:2, B:2}

  A: 3 > 2 (VC1 wins)
  B: 1 < 2 (VC2 wins)
  Neither dominates → CONCURRENT → conflict!
```

#### Last-Write-Wins (LWW)

A simpler alternative: attach a physical timestamp to each write. The write with the
highest timestamp wins. Used by Cassandra by default.

```
  Write 1: K = "foo", timestamp = 1712678400000
  Write 2: K = "bar", timestamp = 1712678400001   ← wins (higher timestamp)

  Pros: Simple, no sibling explosion, no client-side resolution needed.
  Cons: Clock skew can cause data loss. Write 1 may have been the "correct"
        value but loses due to clock difference.
```

#### Application-Level Resolution

For use cases like shopping carts, the application performs a **semantic merge**:

```
  Cart version A: {item1, item2, item3}     (user added item3)
  Cart version B: {item1, item2, item4}     (user added item4)

  Application merge: {item1, item2, item3, item4}  (union)
```

### 8.4 Failure Detection

#### Gossip Protocol

Every node periodically exchanges state information with random peers. This
decentralized approach has no single point of failure.

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    Gossip Protocol                               │
  │                                                                  │
  │  Every 1 second, each node:                                      │
  │  1. Picks 1-3 random nodes                                      │
  │  2. Sends a digest: [(nodeID, heartbeat, generation), ...]       │
  │  3. Receiver compares with its own state                         │
  │  4. Exchanges updates for stale entries                          │
  │                                                                  │
  │  Node A                    Node B                    Node C      │
  │  ┌──────────────┐         ┌──────────────┐         ┌────────┐   │
  │  │ A: hb=100    │         │ A: hb=98     │         │ A: hb=99│  │
  │  │ B: hb=95     │──dig──> │ B: hb=97     │──dig──> │ B: hb=97│  │
  │  │ C: hb=88     │ <──ack──│ C: hb=90     │ <──ack──│ C: hb=91│  │
  │  │ D: hb=102    │         │ D: hb=100    │         │ D: hb=102│  │
  │  └──────────────┘         └──────────────┘         └────────┘   │
  │                                                                  │
  │  After exchange, all nodes converge toward the latest state.     │
  │  Convergence time: O(log N) gossip rounds for N nodes.           │
  └─────────────────────────────────────────────────────────────────┘
```

#### Phi-Accrual Failure Detector

Instead of a binary "up/down" decision, the phi-accrual detector outputs a **suspicion
level** (phi) based on the statistical distribution of heartbeat inter-arrival times.

```
  phi(t) = -log10(1 - F(t_now - t_last))

  Where F is the CDF of the normal distribution fitted to historical
  inter-arrival times.

  phi < 1:   Normal heartbeat pattern. Node is definitely alive.
  phi = 1-5: Getting suspicious. Heartbeat is late.
  phi > 8:   Very likely down (convict threshold, configurable).
  phi > 12:  Almost certainly down.

  ┌─────────────────────────────────────────────────┐
  │  Suspicion Level (phi) Over Time                │
  │                                                  │
  │  phi                                             │
  │  12 │                              xxxxxxxx      │
  │  10 │                          xxxx              │
  │   8 │─────────────────────xxxxx──── (threshold)  │
  │   6 │                  xxx                       │
  │   4 │               xxx                         │
  │   2 │           xxxx                             │
  │   0 │xxxxxxxxxx                                  │
  │     └──────────────────────────────────── time   │
  │           ↑                                      │
  │     last heartbeat                               │
  └─────────────────────────────────────────────────┘
```

#### Merkle Trees for Anti-Entropy

Each node maintains a **Merkle tree** (hash tree) per key range. By comparing root
hashes, two nodes can quickly identify which key ranges have diverged, then
synchronize only the differing ranges.

```
  Merkle Tree for key range [0, 1000]:

              ┌──────────┐
              │ Root Hash│
              │  H(AB)   │
              └────┬─────┘
                   │
          ┌────────┴────────┐
          │                 │
     ┌────┴────┐       ┌────┴────┐
     │ Hash A  │       │ Hash B  │
     │ H(1,2)  │       │ H(3,4)  │
     └────┬────┘       └────┬────┘
          │                  │
     ┌────┴────┐        ┌────┴────┐
     │         │        │         │
  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐
  │Hash1│  │Hash2│  │Hash3│  │Hash4│
  │[0-  │  │[250-│  │[500-│  │[750-│
  │ 249]│  │ 499]│  │ 749]│  │1000]│
  └─────┘  └─────┘  └─────┘  └─────┘

  Node X's tree:              Node Y's tree:
  Root: abc123                Root: abc789    ← DIFFERENT!
    ├── A: def456               ├── A: def456   ← same
    │   ├── 1: aaa                │   ├── 1: aaa
    │   └── 2: bbb                │   └── 2: bbb
    └── B: ghi012               └── B: ghi345   ← DIFFERENT!
        ├── 3: ccc                  ├── 3: ccc     ← same
        └── 4: ddd                  └── 4: eee     ← DIFFERENT!

  Only range [750-1000] needs synchronization!
  Compared O(log N) hashes instead of scanning all keys.
```

#### Hinted Handoff (Detailed)

```
  Timeline of hinted handoff:

  t=0:   Node C goes down.
  t=0+:  Coordinator detects C is unresponsive (via gossip / phi detector).
  t=0+:  Writes destined for C are sent to Node E instead (sloppy quorum).
  t=0+:  E stores hints in a local hints directory:
         /hints/node_c/key1.hint
         /hints/node_c/key2.hint

  t=30m: Node C comes back online.
  t=30m: Gossip propagates C's liveness to all nodes.
  t=31m: E detects C is alive, begins shipping hints:
         - Reads each hint file
         - Sends (key, value, vector_clock) to C
         - Deletes hint file after C acknowledges

  Hint structure:
  ┌──────────────────────────────┐
  │ target_node: C               │
  │ key: "user:12345"            │
  │ value: <bytes>               │
  │ vector_clock: {A:3, B:1}    │
  │ timestamp: 1712678400000     │
  │ ttl_remaining: 85400         │
  └──────────────────────────────┘

  Hints are expired after a configurable window (e.g., 3 hours).
  If C is down longer, anti-entropy (Merkle trees) handles repair.
```

---

## 9. Data Partitioning

### Consistent Hash Ring with Token Ranges

The entire key space is divided into **token ranges** assigned to virtual nodes.

```
  Hash ring with tokens 0 to 360 (simplified):

  Token:    0    60    120    180    240    300    360/0
            │     │      │      │      │      │      │
  Range:    ├─A1──├──B1──├──C1──├──A2──├──B2──├──C2──┤
            │     │      │      │      │      │      │
  Owner:    A     B      C      A      B      C

  Key "user:12345" → hash = 145 → falls in range [120, 180) → owned by A2 (Node A)
  Replicated to next 2 nodes on ring: B2 (Node B), C2 (Node C)
  Preference list: [A, B, C]
```

### Virtual Node Configuration

```
  Recommended: 150-200 vnodes per physical node.

  Node Capacity    VNodes    Rationale
  ─────────────    ──────    ──────────────────────────
  Small  (4 CPU)     100    Proportional to capacity
  Medium (8 CPU)     150    Standard configuration
  Large  (16 CPU)    200    More tokens = more data

  Total tokens in cluster:  N_nodes * vnodes_per_node
  Example: 100 nodes * 150 vnodes = 15,000 tokens

  Memory per node for ring metadata:
  15,000 tokens * 32 bytes (token + node ID) = ~480 KB (negligible)
```

### Range Ownership and Rebalancing

When a node is added or removed:

```
  Before: 3 nodes, each owns ~33% of the ring.

  ┌─────────────────────────────────────────┐
  │  Node A: 33%  │  Node B: 33%  │  Node C: 33%  │
  └─────────────────────────────────────────┘

  After adding Node D: each node owns ~25%.

  ┌──────────────────────────────────────────────────────┐
  │  Node A: 25% │ Node B: 25% │ Node C: 25% │ Node D: 25% │
  └──────────────────────────────────────────────────────┘

  Node D's vnodes are interleaved, so it takes ~8% from each of A, B, C.
  Data streams in the background. Reads/writes continue during rebalancing.

  Rebalancing strategy:
  1. New node announces itself via gossip.
  2. Cluster assigns tokens to the new node.
  3. Existing nodes stream data for the new node's token ranges.
  4. Once streaming completes, the new node starts serving reads.
  5. Old replicas for transferred ranges are eventually garbage collected.
```

---

## 10. Caching

### Multi-Layer Caching Architecture

```
  ┌────────────────────────────────────────────────────┐
  │                  Read Request                       │
  │                      │                              │
  │                      v                              │
  │  ┌──────────────────────────────────┐              │
  │  │          Row Cache               │              │
  │  │  (full row data, LRU eviction)   │              │
  │  │  Hit rate: ~30-50% for hot data  │              │
  │  │  Memory: ~10 GB per node         │              │
  │  └──────────────┬───────────────────┘              │
  │                 │ miss                              │
  │                 v                                   │
  │  ┌──────────────────────────────────┐              │
  │  │          Key Cache               │              │
  │  │  (key → SSTable offset mapping)  │              │
  │  │  Avoids index scan entirely      │              │
  │  │  Memory: ~5 GB per node          │              │
  │  │  Hit rate: ~80-90%               │              │
  │  └──────────────┬───────────────────┘              │
  │                 │ miss                              │
  │                 v                                   │
  │  ┌──────────────────────────────────┐              │
  │  │        Bloom Filter              │              │
  │  │  (per-SSTable membership test)   │              │
  │  │  Eliminates unnecessary disk I/O │              │
  │  │  FP rate: ~1% at 10 bits/key     │              │
  │  │  Memory: ~2 GB for all SSTables  │              │
  │  └──────────────┬───────────────────┘              │
  │                 │ possibly present                  │
  │                 v                                   │
  │  ┌──────────────────────────────────┐              │
  │  │     OS Page Cache (mmap)         │              │
  │  │  SSTable data blocks cached by OS│              │
  │  │  Memory: remaining free RAM      │              │
  │  └──────────────┬───────────────────┘              │
  │                 │ miss                              │
  │                 v                                   │
  │  ┌──────────────────────────────────┐              │
  │  │        Disk I/O                  │              │
  │  │  (SSD: ~100us, HDD: ~10ms)      │              │
  │  └──────────────────────────────────┘              │
  └────────────────────────────────────────────────────┘
```

### Row Cache

- Stores deserialized row data in memory.
- Best for **read-heavy, small, hot** datasets (e.g., user sessions).
- Invalidated on writes to the same key.
- NOT recommended for write-heavy workloads (frequent invalidation).

### Key Cache

- Maps partition key to SSTable file + byte offset.
- Allows direct seeks, bypassing the SSTable index block entirely.
- Very high hit rate because key access patterns are often skewed (Zipfian).
- Populated on reads, saved to disk on graceful shutdown for warm restarts.

### Bloom Filter Tuning

```
  Bits per key    Hash functions    FP Rate     Memory / 1M keys
  ───────────     ──────────────    ────────    ─────────────────
       5               3            ~10%           625 KB
      10               7            ~1%           1.25 MB
      15              10            ~0.1%         1.87 MB
      20              14            ~0.01%        2.50 MB

  Recommendation: 10 bits/key (1% FP) is the sweet spot.
  At 1% FP rate with 100 SSTables, expected false disk reads per query: 1.
```

---

## 11. Replication and Consistency

### Replication Strategy

```
  Replication Factor (N) = 3

  For key K with primary token on Node B:

  ┌────────────────────────────────────────────────────┐
  │                 Consistent Hash Ring                │
  │                                                     │
  │     ...── Node A ── Node B ── Node C ── Node D ──...│
  │                      │         │         │         │
  │                      │ primary │ replica  │ replica │
  │                      │  (R1)   │  (R2)    │  (R3)  │
  │                      ▼         ▼          ▼        │
  │                    ┌────┐    ┌────┐     ┌────┐     │
  │                    │ K  │    │ K  │     │ K  │     │
  │                    │=val│    │=val│     │=val│     │
  │                    └────┘    └────┘     └────┘     │
  └────────────────────────────────────────────────────┘

  The "preference list" for K is [B, C, D].
  Skips duplicate physical nodes (if B and C are vnodes on the same machine,
  skip to the next distinct physical node).
```

### Tunable Consistency Levels

```
  ┌──────────────────────────────────────────────────────────────┐
  │                Consistency Level Spectrum                     │
  │                                                              │
  │  Weaker                                          Stronger    │
  │  (faster)                                       (slower)     │
  │                                                              │
  │  ◄──────────────────────────────────────────────────────►    │
  │  ONE        QUORUM              ALL                          │
  │  W=1,R=1    W=2,R=2 (N=3)      W=3,R=3 (N=3)              │
  │                                                              │
  │  - Fastest          - Balanced         - Linearizable        │
  │  - May read stale   - R+W > N          - Slowest (wait all) │
  │  - Best for metrics - Good default     - Any failure = error │
  │  - Always available - Tolerates 1      - Used for locks      │
  │                       failure                                │
  └──────────────────────────────────────────────────────────────┘
```

### Read Repair

When a coordinator reads from R replicas and detects version mismatches, it
asynchronously updates the stale replicas.

```
  Coordinator reads key K from replicas B, C, D:

  Node B: K = "v3", vc={A:3}         ← latest
  Node C: K = "v3", vc={A:3}         ← latest
  Node D: K = "v2", vc={A:2}         ← STALE

  Coordinator returns "v3" to client.
  Asynchronously sends repair to Node D:
    "Hey D, update K to v3 with vc={A:3}"

  Read repair is probabilistic (e.g., 10% of reads trigger a repair check)
  to avoid overwhelming the cluster with repair traffic.
```

### Anti-Entropy (Background Repair)

Complements read repair for keys that are rarely or never read.

```
  Anti-entropy process (runs every 1-24 hours):

  1. Node B builds Merkle tree for range [100, 200]
  2. Node B sends tree root hash to Node C (a replica for that range)
  3. Compare root hashes:
     - Same → entire range is in sync, done.
     - Different → descend into child hashes to find divergent leaf ranges.
  4. For each divergent leaf range, stream missing/outdated keys.
  5. Repeat for all ranges and all replica pairs.

  Cost: O(log N) hash comparisons + streaming only changed data.
  Much cheaper than a full key-by-key comparison.
```

---

## 12. Fault Tolerance

### Failure Scenarios and Recovery Mechanisms

```
  ┌──────────────────────────────────────────────────────────────────┐
  │              Failure Type → Recovery Mechanism                    │
  │                                                                  │
  │  ┌─────────────────┐    ┌────────────────────────────────────┐  │
  │  │ Single node      │───>│ Hinted handoff + read repair       │  │
  │  │ temporary failure│    │ (seconds to recover)                │  │
  │  └─────────────────┘    └────────────────────────────────────┘  │
  │                                                                  │
  │  ┌─────────────────┐    ┌────────────────────────────────────┐  │
  │  │ Single node      │───>│ Re-replication to new node         │  │
  │  │ permanent failure│    │ + Merkle tree repair                │  │
  │  │                  │    │ (minutes to hours)                  │  │
  │  └─────────────────┘    └────────────────────────────────────┘  │
  │                                                                  │
  │  ┌─────────────────┐    ┌────────────────────────────────────┐  │
  │  │ Network partition│───>│ Sloppy quorum + vector clock       │  │
  │  │                  │    │ conflict resolution on heal         │  │
  │  └─────────────────┘    └────────────────────────────────────┘  │
  │                                                                  │
  │  ┌─────────────────┐    ┌────────────────────────────────────┐  │
  │  │ Datacenter       │───>│ Cross-DC replication + local       │  │
  │  │ failure          │    │ quorum + async replication          │  │
  │  └─────────────────┘    └────────────────────────────────────┘  │
  │                                                                  │
  │  ┌─────────────────┐    ┌────────────────────────────────────┐  │
  │  │ Disk failure     │───>│ WAL replay + SSTable recovery      │  │
  │  │                  │    │ from replicas                       │  │
  │  └─────────────────┘    └────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────────────────┘
```

### Hinted Handoff (Recovery Flow)

```
  Normal state:          Write for key K → [B, C, D]

  Node C fails:          Write for key K → [B, E(hint for C), D]

  C recovers:            E detects C alive → ships hints → C catches up
                         Hint TTL = 3 hours (configurable)

  If C is down > 3h:     Hints expire. Anti-entropy (Merkle trees) handles
                         the remaining drift when C comes back.
```

### Read Repair (Consistency Recovery)

```
  Read repair runs during normal read operations:

  Step 1: Coordinator reads from R replicas.
  Step 2: Compare versions from all R responses.
  Step 3: If any replica is behind:
          - Return the latest version to the client.
          - Asynchronously send the latest version to stale replicas.
  Step 4: Stale replicas update their local storage.

  Read repair probability: 10% (configurable).
  This means 1 in 10 reads will trigger a version comparison across
  ALL N replicas (not just R). This is called "full read repair."
```

### Merkle Tree Synchronization (Anti-Entropy)

```
  ┌─────────────────────────────────────────────────────────┐
  │         Merkle Tree Sync Between Two Replicas            │
  │                                                          │
  │  Node B                              Node C              │
  │  ┌──────────┐                       ┌──────────┐        │
  │  │ Root: X  │ ───compare───────────>│ Root: Y  │        │
  │  └────┬─────┘       (different!)    └────┬─────┘        │
  │       │                                  │               │
  │  ┌────┴────┐                        ┌────┴────┐         │
  │  │L:a │R:b │ ───compare L──────────>│L:a │R:c │         │
  │  └──┬──┬───┘      (L same, R diff!) └──┬──┬───┘        │
  │     │  │                                │  │             │
  │     │  └──compare R──>                  │  └──>          │
  │     │                                   │                │
  │  Only sync the keys in range R (right subtree).          │
  │  Skip the entire L range (left subtree is identical).    │
  └─────────────────────────────────────────────────────────┘
```

### Re-Replication on Permanent Failure

```
  Node C is declared permanently dead (after N hours of being down).

  Before:
    Key K replicas: [B, C, D]

  Action:
  1. Gossip marks C as permanently removed.
  2. Token ranges owned by C are redistributed to other nodes.
  3. For each range formerly on C:
     - The remaining replicas (B, D) stream data to the new owner (e.g., E).
  4. Once streaming completes, E assumes responsibility for C's ranges.

  After:
    Key K replicas: [B, E, D]    (E replaces C)
```

---

## 13. Scalability

### Linear Scaling

```
  ┌──────────────────────────────────────────────────────────┐
  │          Throughput vs. Cluster Size                      │
  │                                                          │
  │  Throughput                                               │
  │  (ops/s)                                                  │
  │  600K │                                      x            │
  │       │                                   x               │
  │  500K │                                x                  │
  │       │                             x                     │
  │  400K │                          x       ideal linear     │
  │       │                       x     ─────────────────     │
  │  300K │                    x            actual             │
  │       │                 x          ─ ─ ─ ─ ─ ─ ─ ─ ─     │
  │  200K │              x                                    │
  │       │           x                                       │
  │  100K │        x                                          │
  │       │     x                                             │
  │     0 │──x────────────────────────────────────────        │
  │       0   2   4   6   8  10  12  14  16  18  20           │
  │                   Number of Nodes                         │
  └──────────────────────────────────────────────────────────┘

  Near-linear scaling because:
  - No central coordinator or master node.
  - Each node handles its own token ranges independently.
  - Cross-node communication is limited to:
    * Coordinator → replica (per-request, O(N_replicas) = O(3))
    * Gossip (O(log N) convergence)
    * Anti-entropy (background, per-range)
```

### Auto Rebalancing

```
  Adding a node:
  ┌─────────────────────────────────────────────────────┐
  │  1. Bootstrap: New node contacts a seed node.        │
  │  2. Token Assignment: New node claims tokens.        │
  │  3. Data Streaming: Existing nodes stream data       │
  │     for the new node's ranges.                       │
  │  4. Join: New node starts serving requests.           │
  │  5. Cleanup: Source nodes remove migrated data.       │
  │                                                      │
  │  During streaming:                                    │
  │  - Reads:  Served by old owners until streaming done. │
  │  - Writes: Dual-written to old + new owner.           │
  │  - Zero downtime. No manual intervention.             │
  └─────────────────────────────────────────────────────┘

  Removing a node:
  ┌─────────────────────────────────────────────────────┐
  │  1. Decommission: Node announces departure via       │
  │     gossip.                                          │
  │  2. Streaming: Departing node streams all its data   │
  │     to the new owners for each range.                │
  │  3. Token Release: Tokens are released and           │
  │     redistributed.                                   │
  │  4. Departure: Node leaves the cluster cleanly.       │
  └─────────────────────────────────────────────────────┘
```

### Cross-Datacenter Replication

```
  ┌──────────────────────┐          ┌──────────────────────┐
  │   Datacenter US-EAST │          │   Datacenter EU-WEST │
  │                      │          │                      │
  │  ┌───┐ ┌───┐ ┌───┐  │  async   │  ┌───┐ ┌───┐ ┌───┐  │
  │  │ A │ │ B │ │ C │  │◄────────►│  │ D │ │ E │ │ F │  │
  │  └───┘ └───┘ └───┘  │ repl.    │  └───┘ └───┘ └───┘  │
  │                      │          │                      │
  │  Local quorum: W=2   │          │  Local quorum: W=2   │
  │  within this DC      │          │  within this DC      │
  └──────────────────────┘          └──────────────────────┘

  Strategy: LOCAL_QUORUM + async cross-DC replication
  - Writes ack after local quorum (fast, <10ms).
  - Async replication to remote DC (50-200ms).
  - Conflicts resolved via vector clocks or LWW.
  - Each DC can serve reads independently (low latency).
  - DC failure: other DC takes over with slight staleness.
```

---

## 14. Monitoring

### Key Metrics Dashboard

```
  ┌────────────────────────────────────────────────────────────────────┐
  │                    KV Store Monitoring Dashboard                    │
  │                                                                    │
  │  ┌─────────────────────────┐    ┌─────────────────────────┐       │
  │  │  Read Latency           │    │  Write Latency          │       │
  │  │  p50:  0.5ms            │    │  p50:  1.2ms            │       │
  │  │  p95:  3.2ms            │    │  p95:  4.1ms            │       │
  │  │  p99:  8.7ms  ✓ (<10ms) │    │  p99:  7.3ms  ✓ (<10ms)│       │
  │  │  p999: 23ms             │    │  p999: 18ms             │       │
  │  └─────────────────────────┘    └─────────────────────────┘       │
  │                                                                    │
  │  ┌─────────────────────────┐    ┌─────────────────────────┐       │
  │  │  Compaction             │    │  SSTable Count          │       │
  │  │  Pending tasks: 3       │    │  L0: 4    (target: <8)  │       │
  │  │  Backlog (bytes): 2.1GB │    │  L1: 10                 │       │
  │  │  Rate: 50 MB/s          │    │  L2: 45                 │       │
  │  │  Status: NORMAL         │    │  Total: 59              │       │
  │  └─────────────────────────┘    └─────────────────────────┘       │
  │                                                                    │
  │  ┌─────────────────────────┐    ┌─────────────────────────┐       │
  │  │  Bloom Filter           │    │  Cluster Health         │       │
  │  │  FP rate: 0.8%          │    │  Nodes: 100/100 UP      │       │
  │  │  Memory: 1.8 GB         │    │  Gossip: converged      │       │
  │  │  Saves/sec: 45,200      │    │  Hints pending: 0       │       │
  │  │  (disk reads avoided)   │    │  Repairs: 0 running     │       │
  │  └─────────────────────────┘    └─────────────────────────┘       │
  │                                                                    │
  │  ┌─────────────────────────┐    ┌─────────────────────────┐       │
  │  │  MemTable               │    │  Throughput             │       │
  │  │  Size: 180 MB / 256 MB  │    │  Reads:  98,500 ops/s   │       │
  │  │  Flush count: 12/hour   │    │  Writes: 49,200 ops/s   │       │
  │  │  WAL size: 200 MB       │    │  Replications: 98K/s    │       │
  │  └─────────────────────────┘    └─────────────────────────┘       │
  └────────────────────────────────────────────────────────────────────┘
```

### Critical Alerts

| Metric                  | Warning Threshold      | Critical Threshold      |
|-------------------------|------------------------|--------------------------|
| Read p99 latency        | > 10ms                 | > 50ms                   |
| Write p99 latency       | > 10ms                 | > 50ms                   |
| Compaction backlog      | > 10 GB                | > 50 GB                  |
| L0 SSTable count        | > 8                    | > 32 (stall writes)      |
| Bloom filter FP rate    | > 5%                   | > 10%                    |
| Hints pending           | > 10,000               | > 100,000                |
| Node down duration      | > 5 minutes            | > 30 minutes             |
| Disk utilization        | > 70%                  | > 85%                    |
| MemTable flush latency  | > 5 seconds            | > 30 seconds             |
| Tombstone ratio         | > 20% of reads         | > 50% of reads           |

### Operational Runbooks

**High L0 SSTable Count:**
1. Check compaction throughput -- is it keeping up?
2. Increase compaction threads or I/O priority.
3. If sustained, consider throttling writes temporarily.
4. Check for wide partitions causing slow compaction.

**High Bloom Filter FP Rate:**
1. Check bits-per-key setting (should be >= 10).
2. Rebuild Bloom filters during next compaction.
3. Consider if dataset characteristics have changed.

**Growing Hints Queue:**
1. Identify the target node -- is it truly down or just slow?
2. If down, monitor for auto-recovery.
3. If hint TTL is approaching, prepare for anti-entropy repair.

---

## 15. Trade-offs

### AP vs CP

```
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │  AP (Dynamo-style):                                          │
  │  ┌──────────────────────────────────────────┐               │
  │  │ + Always writable, even during partitions │               │
  │  │ + Lower latency (no distributed consensus)│               │
  │  │ + Better availability                     │               │
  │  │ - May return stale data                   │               │
  │  │ - Conflict resolution complexity          │               │
  │  │ - Harder to reason about correctness      │               │
  │  │ Use: Shopping carts, session stores,       │               │
  │  │      user preferences, metrics            │               │
  │  └──────────────────────────────────────────┘               │
  │                                                              │
  │  CP (Raft/Paxos-based):                                     │
  │  ┌──────────────────────────────────────────┐               │
  │  │ + Strong consistency (linearizable)       │               │
  │  │ + No conflicts to resolve                 │               │
  │  │ + Easier to program against               │               │
  │  │ - Unavailable during partitions           │               │
  │  │ - Higher latency (consensus rounds)       │               │
  │  │ - Leader bottleneck                       │               │
  │  │ Use: Financial transactions, inventory,    │               │
  │  │      coordination, distributed locks       │               │
  │  └──────────────────────────────────────────┘               │
  └──────────────────────────────────────────────────────────────┘
```

### Vector Clocks vs Last-Write-Wins (LWW)

| Aspect              | Vector Clocks                    | LWW                          |
|---------------------|----------------------------------|-------------------------------|
| Data loss           | None (preserves all versions)    | Possible (clock skew)         |
| Client complexity   | High (must resolve siblings)     | None                          |
| Storage overhead    | VC metadata per key (grows)      | Single timestamp              |
| Correctness         | Causally correct                 | Depends on clock accuracy     |
| Sibling explosion   | Possible (mitigated by pruning)  | N/A                           |
| Clock dependency    | Logical (no physical clocks)     | Physical clocks (NTP)         |
| Used by             | Riak, original Dynamo            | Cassandra, ScyllaDB           |

**Vector Clock Pruning:** To prevent unbounded growth, prune entries older than a
threshold (e.g., remove entries for nodes not seen in 7 days). Trades correctness
for bounded metadata size.

### LSM Tree vs B-Tree

| Aspect                | LSM Tree                        | B-Tree                         |
|-----------------------|---------------------------------|---------------------------------|
| Write throughput      | Very high (sequential I/O)      | Lower (random I/O)             |
| Read throughput       | Lower (check multiple levels)   | Higher (single lookup path)    |
| Write amplification   | Higher (10-30x from compaction) | Lower (2-3x)                   |
| Space amplification   | Lower (after compaction)        | Higher (~50% page utilization) |
| Predictable latency   | No (compaction spikes)          | Yes (consistent performance)  |
| Range scans           | Good (sorted SSTables)          | Excellent (sorted leaves)     |
| Concurrency           | Good (lock-free memtable)       | Complex (page-level locks)    |
| Recovery              | WAL replay                      | WAL + partial page repair     |
| Used by               | Cassandra, RocksDB, LevelDB     | PostgreSQL, MySQL InnoDB      |

**When to choose LSM:** Write-heavy workloads (>50% writes), append-heavy patterns,
time-series data. The Dynamo-style KV store favors LSM because it prioritizes write
availability and throughput.

**When to choose B-Tree:** Read-heavy workloads, range scans, need for predictable
latency, transactional workloads with MVCC.

### Compaction Strategies Comparison

| Strategy       | Write Amp. | Space Amp. | Read Amp. | Best For                |
|----------------|-----------|------------|-----------|-------------------------|
| Size-Tiered    | Low       | High (2x)  | High      | Write-heavy workloads   |
| Leveled        | High      | Low (1.1x) | Low       | Read-heavy workloads    |
| Time-Window    | Low       | Low        | Low       | Time-series with TTL    |
| FIFO           | None      | None       | Low       | Cache-like workloads    |

---

## 16. Interview Questions

### Q1: How do you handle hotspot keys?

**A:** Hotspot keys (e.g., a viral post's like counter) overwhelm a single partition.
Solutions:
1. **Key salting / bucketing:** Append a random suffix (e.g., `hot_key_0` through
   `hot_key_99`) to distribute across 100 partitions. Reads must fan out to all 100
   and aggregate.
2. **Local aggregation:** Buffer writes in the coordinator and flush periodically.
3. **Dedicated cache tier:** Put hot keys in a Redis/Memcached layer in front of the
   KV store.
4. **Read replicas:** For read-hot keys, add more read-only replicas for that
   partition.

### Q2: What happens during a network partition?

**A:** With sloppy quorum, both sides of the partition continue serving reads and
writes. Writes on each side use hinted handoff or local replicas. When the partition
heals:
1. Gossip reconnects the two halves.
2. Anti-entropy (Merkle trees) identifies divergent keys.
3. Vector clocks determine causal ordering.
4. Concurrent writes (neither dominates) create siblings that the application must
   resolve, or LWW picks the highest timestamp.

### Q3: Explain vector clocks and when they produce conflicts.

**A:** A vector clock is a list of `(node, counter)` pairs. On every write, the
writing node increments its counter. Two vector clocks are compared element-wise:
- If VC1 dominates VC2 (every component >= and at least one >), VC2 is an ancestor --
  discard VC2.
- If neither dominates, the writes are concurrent -- they represent a conflict (sibling
  values).

Conflicts happen when two clients write to different replicas without seeing each
other's writes (e.g., during a partition or race condition).

### Q4: How does read repair work? When is it insufficient?

**A:** On a read, the coordinator compares versions from R replicas. If a replica has
a stale version, the coordinator asynchronously sends the latest version. Read repair
is insufficient for:
- Keys that are **never read** (cold data) -- use anti-entropy for these.
- **High-write, low-read** workloads -- divergence accumulates faster than reads repair it.
- **Tombstone propagation** -- a delete may not reach all replicas via read repair alone.

### Q5: How does LSM differ from B-Tree for this use case?

**A:** LSM converts random writes to sequential I/O (write to MemTable, flush to
sorted SSTables). This is ideal for a Dynamo-style store because:
- Writes are the critical path (always-on availability).
- Sequential I/O is 100x faster than random I/O on HDDs, 5x on SSDs.
- Trade-off: reads may need to check multiple SSTables, mitigated by Bloom filters
  and caching.

B-Trees update in-place (random I/O), which is better for read-heavy workloads with
predictable latency requirements (e.g., OLTP databases).

### Q6: How do you handle deletes in a distributed KV store?

**A:** Deletes are tombstones (a marker with a timestamp/vector clock). The tombstone
must propagate to all replicas before being garbage collected. `gc_grace_seconds`
(default: 10 days) defines how long tombstones are kept. If a node is down longer
than gc_grace_seconds, it may resurrect deleted data when it comes back -- this is
the **zombie data** problem. Mitigation: run anti-entropy repair before rejoining a
long-absent node.

### Q7: What is the impact of compaction on latency?

**A:** Compaction is I/O intensive and can cause latency spikes:
- **Read latency:** During compaction, disk bandwidth is shared, increasing read times.
- **Write stalls:** If L0 SSTable count exceeds a threshold (e.g., 32), writes are
  throttled or stalled until compaction catches up.

Mitigations:
- Rate-limit compaction I/O.
- Use separate disks for compaction output.
- Prioritize L0 compaction (most impact on read performance).
- Use leveled compaction for read-heavy workloads (fewer SSTables to check).

### Q8: How do you tune N, W, R for different use cases?

**A:**
- **Session store (availability > consistency):** N=3, W=1, R=1. Fastest, but may
  read stale sessions.
- **User profiles (balanced):** N=3, W=2, R=2. Strong consistency (R+W=4 > N=3),
  tolerates 1 failure.
- **Financial ledger (strong consistency):** N=3, W=3, R=1 or W=2, R=2. No stale
  reads, but any node failure blocks writes (W=3) or reduces availability.
- **Analytics/metrics (high write throughput):** N=3, W=1, R=1. Eventual consistency
  is fine for aggregated metrics.

### Q9: How does consistent hashing handle heterogeneous hardware?

**A:** Assign more virtual nodes to more powerful machines. A node with 2x the CPU
and storage gets 2x the vnodes, and thus owns 2x the token ranges. This is more
flexible than fixed partitioning because:
- Adding a large node automatically takes proportionally more load.
- Rebalancing is granular (moves vnodes, not entire ranges).

### Q10: What is a sloppy quorum and why is it important?

**A:** A strict quorum requires exactly the nodes in the preference list to respond.
A sloppy quorum allows the coordinator to use any N healthy nodes (not just the
designated replicas) to meet the W or R requirement. This is critical for availability:
without sloppy quorum, a single node failure could make a partition unavailable even
though other healthy nodes exist. The trade-off is temporary inconsistency (the
hint-holding node is not the designated replica).

### Q11: How do Merkle trees help with anti-entropy?

**A:** Merkle trees are hash trees where leaf nodes hash individual keys or key ranges
and internal nodes hash their children. Two replicas compare root hashes:
- Same root = entire range is in sync (O(1) check).
- Different root = descend into children to find divergent subtrees.
- Only the differing leaf ranges need key-by-key comparison and repair.

This reduces the amount of data transferred from O(N) to O(D * log N), where D is
the number of differences and N is the total number of keys.

### Q12: How do you handle cross-datacenter replication?

**A:** Use `LOCAL_QUORUM` for writes (ack after quorum within the local DC) plus
asynchronous replication to remote DCs. This ensures:
- Low write latency (no cross-DC round trip in the critical path).
- Each DC can serve reads independently.
- Conflict resolution via vector clocks or LWW when DCs reconnect.
- DC failure: the other DC has a slightly stale but complete copy.

For stronger consistency across DCs, use `EACH_QUORUM` (quorum in every DC), but
latency increases to cross-DC RTT (~50-200ms).

### Q13: What is the difference between hinted handoff and anti-entropy?

**A:**

| Aspect           | Hinted Handoff                  | Anti-Entropy                  |
|------------------|---------------------------------|-------------------------------|
| Trigger          | Node failure detected           | Periodic (scheduled)          |
| Scope            | Recent writes only              | Entire key ranges             |
| Granularity      | Individual keys                 | Range-level (Merkle tree)     |
| Time window      | Short (hours)                   | Unlimited                     |
| Overhead         | Low (just pending writes)       | Higher (tree computation)     |
| Speed            | Fast (immediate on recovery)    | Slow (background process)     |
| Coverage         | Incomplete (misses reads)       | Complete                      |

They are complementary: hinted handoff handles short outages quickly, anti-entropy
handles long outages and data drift comprehensively.

### Q14: How do you prevent tombstone accumulation?

**A:** Tombstone accumulation degrades read performance (reads must scan past
tombstones). Prevention strategies:
1. **gc_grace_seconds:** Tombstones are garbage collected after this period during
   compaction. Set to slightly longer than your longest acceptable node downtime.
2. **Compaction:** Ensure compaction runs regularly and is not backlogged.
3. **TTL instead of delete:** Use TTL for data that naturally expires (e.g., sessions).
   TTL expiration produces fewer tombstones because the data and tombstone are in the
   same SSTable (time-window compaction).
4. **Avoid range deletes:** Deleting 1 million keys in a range creates 1 million
   tombstones. Instead, use TTL or partition-level drops.

### Q15: How would you migrate from a single-node KV store to this distributed design?

**A:** Migration strategy:
1. **Dual-write phase:** Write to both old and new systems. Read from old.
2. **Backfill:** Scan the old store and write all existing data to the new cluster.
   Use background streaming to avoid overloading the new cluster.
3. **Validation:** Compare random samples between old and new stores. Use checksums
   for full validation.
4. **Shadow read phase:** Read from both systems, compare results, log discrepancies.
   Serve from old system.
5. **Cutover:** Switch reads to the new system. Keep the old system as fallback.
6. **Decommission:** After a confidence period (1-2 weeks), decommission the old
   store.

Key considerations:
- Handle schema differences (add vector clocks, partition keys).
- Set initial replication factor and consistency levels.
- Pre-split tokens based on existing key distribution to avoid hotspots.
- Monitor latency and error rates during each phase.

---

## Summary

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                  Dynamo-Style KV Store Summary                    │
  │                                                                  │
  │  Core Principles:                                                │
  │  ├── AP over CP (always writable)                                │
  │  ├── Consistent hashing + virtual nodes (data distribution)      │
  │  ├── Tunable consistency (ONE / QUORUM / ALL)                    │
  │  ├── LSM tree storage (write-optimized)                          │
  │  └── Decentralized (no master, gossip protocol)                  │
  │                                                                  │
  │  Key Mechanisms:                                                  │
  │  ├── Quorum (N/W/R) for consistency control                      │
  │  ├── Vector clocks / LWW for conflict resolution                 │
  │  ├── Gossip + phi-accrual for failure detection                  │
  │  ├── Hinted handoff for short-term failure recovery              │
  │  ├── Merkle trees for anti-entropy repair                        │
  │  ├── Read repair for passive consistency convergence             │
  │  ├── Bloom filters for read optimization                         │
  │  └── Compaction for space reclamation                            │
  │                                                                  │
  │  Scale:                                                          │
  │  ├── 150K ops/sec (100K reads + 50K writes)                      │
  │  ├── ~1000 nodes                                                 │
  │  ├── Petabytes of storage                                        │
  │  ├── < 10ms p99 latency                                          │
  │  └── 99.99% availability                                        │
  └──────────────────────────────────────────────────────────────────┘
```

---

*References: Amazon Dynamo (DeCandia et al., 2007), Apache Cassandra Architecture,
Google Bigtable, Facebook's RocksDB, LevelDB documentation.*
