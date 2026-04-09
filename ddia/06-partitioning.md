# Chapter 6: Partitioning

## Table of Contents

1. [Why Partition?](#why-partition)
2. [Partitioning of Key-Value Data](#partitioning-of-key-value-data)
3. [Partitioning and Secondary Indexes](#partitioning-and-secondary-indexes)
4. [Rebalancing Partitions](#rebalancing-partitions)
5. [Request Routing](#request-routing)
6. [Interview Questions](#interview-questions)

---

## Why Partition?

**Partitioning** (also called **sharding**) splits a large dataset across multiple nodes so that each node stores a subset of the data.

```
┌─────────────────────────────────────────────────────────────────┐
│              PARTITIONING MOTIVATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Without partitioning:           With partitioning:             │
│  ┌──────────────────────┐       ┌───────┐ ┌───────┐ ┌───────┐│
│  │                      │       │Shard 1│ │Shard 2│ │Shard 3││
│  │    ALL DATA on       │       │ A-H   │ │ I-P   │ │ Q-Z   ││
│  │    ONE machine       │       └───────┘ └───────┘ └───────┘│ │
│  │                      │       Each node processes only its  │
│  │  100 TB, 100K QPS    │       share of queries → throughput │
│  │  → one node can't    │       scales linearly with nodes    │
│  │    handle it         │                                     │
│  └──────────────────────┘                                     │
│                                                                 │
│  GOAL: Spread data and query load EVENLY across nodes.         │
│  If uneven → "hot spot" — one node does all the work while     │
│  others sit idle. Defeats the purpose of partitioning.         │
│                                                                 │
│  Terminology:                                                   │
│  MongoDB, Elasticsearch, SolrCloud: shard                       │
│  HBase: region                                                  │
│  Bigtable: tablet                                               │
│  Cassandra, Riak: vnode                                         │
│  Couchbase: vBucket                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Partitioning is usually combined with replication** — each partition is replicated on multiple nodes for fault tolerance.

---

## Partitioning of Key-Value Data

### Key Range Partitioning

```
┌─────────────────────────────────────────────────────────────────┐
│              KEY RANGE PARTITIONING                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Assign a continuous range of keys to each partition:           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Partition 1  │  │ Partition 2  │  │ Partition 3  │         │
│  │  A - G       │  │  H - N       │  │  O - Z       │         │
│  │              │  │              │  │              │          │
│  │ Keys sorted  │  │ Keys sorted  │  │ Keys sorted  │         │
│  │ within part. │  │ within part. │  │ within part. │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ✓ Efficient range queries (scan from start key to end key)    │
│  ✓ Keys sorted within partition → efficient range scans        │
│  ✗ Risk of HOT SPOTS if access pattern is skewed               │
│                                                                 │
│  Example hot spot:                                              │
│  Sensor data partitioned by timestamp (YYYY-MM-DD)             │
│  All writes for TODAY go to the same partition!                 │
│  Fix: Prefix key with sensor_id → sensor42/2024-03-15          │
│                                                                 │
│  Used by: HBase, Bigtable, RethinkDB, MongoDB (before 2.4)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Hash Partitioning

```
┌─────────────────────────────────────────────────────────────────┐
│              HASH PARTITIONING                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  partition = hash(key) mod num_partitions                       │
│                                                                 │
│  Key "user123" ──► hash("user123") = 0x7A3F...                │
│                 ──► 0x7A3F... mod 4 = partition 2               │
│                                                                 │
│  Hash function distributes keys uniformly:                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Part. 0  │  │ Part. 1  │  │ Part. 2  │  │ Part. 3  │      │
│  │ hash     │  │ hash     │  │ hash     │  │ hash     │      │
│  │ 0x00-3F  │  │ 0x40-7F  │  │ 0x80-BF  │  │ 0xC0-FF  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  ✓ Evenly distributes keys → no hot spots (usually)            │
│  ✗ Loses ability to do efficient range queries                  │
│    (adjacent keys scattered across different partitions)       │
│                                                                 │
│  IMPORTANT: Use a good hash function (MD5, Murmur3),           │
│  NOT language built-in hash (Java's hashCode() is not          │
│  consistent across processes!)                                  │
│                                                                 │
│  Used by: Cassandra, DynamoDB, MongoDB, Riak, Voldemort         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Compound Key (Cassandra's Approach)

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPOUND KEY STRATEGY (Cassandra)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Primary key: (user_id, timestamp)                              │
│                                                                 │
│  • FIRST part (user_id): hashed → determines partition          │
│  • REMAINING parts (timestamp): sorted WITHIN the partition    │
│                                                                 │
│  Partition (user_id = 42):                                      │
│  ┌────────────────────────────────────────┐                    │
│  │ (42, 2024-03-01): data1               │                    │
│  │ (42, 2024-03-02): data2               │ Sorted by timestamp│
│  │ (42, 2024-03-03): data3               │ within partition   │
│  │ (42, 2024-03-04): data4               │                    │
│  └────────────────────────────────────────┘                    │
│                                                                 │
│  ✓ Range query on timestamp for a single user = fast           │
│  ✗ Range query across ALL users = scatter to all partitions    │
│                                                                 │
│  Best of both: hash-based partition assignment +                │
│  range-based sorting within partitions.                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Dealing with Hot Spots

Even with hashing, a single hot key (e.g., a celebrity's user ID) causes all requests to hit one partition.

```
┌─────────────────────────────────────────────────────────────────┐
│  HOT KEY MITIGATION:                                            │
│                                                                 │
│  Append a random number (0-99) to the hot key:                 │
│  "celebrity_123" → "celebrity_123_42"                           │
│                                                                 │
│  Spreads writes across 100 keys → 100 partitions.              │
│  But reads must query ALL 100 keys and merge results.          │
│                                                                 │
│  Trade-off: write spread vs. read amplification.               │
│  Only apply to known hot keys, not all keys.                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Partitioning and Secondary Indexes

Secondary indexes don't map neatly to partitions. Two approaches:

### Document-Partitioned Index (Local Index)

```
┌─────────────────────────────────────────────────────────────────┐
│              LOCAL INDEX (Document-Partitioned)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Each partition maintains its OWN secondary index               │
│  covering only the documents in that partition.                 │
│                                                                 │
│  Partition 0:                    Partition 1:                    │
│  ┌──────────────────────┐       ┌──────────────────────┐       │
│  │ Docs: car191 (red),  │       │ Docs: car389 (yellow)│       │
│  │       car392 (blue)  │       │       car556 (red)   │       │
│  │                      │       │                      │       │
│  │ Index:               │       │ Index:               │       │
│  │  color:red → [191]   │       │  color:red → [556]   │       │
│  │  color:blue → [392]  │       │  color:yellow→ [389] │       │
│  └──────────────────────┘       └──────────────────────┘       │
│                                                                 │
│  Query "color=red" must hit ALL partitions (scatter/gather):   │
│  → Partition 0: finds car191                                    │
│  → Partition 1: finds car556                                    │
│  → Merge results                                               │
│                                                                 │
│  ✓ Writes are local (update one partition's index)             │
│  ✗ Reads are expensive (scatter/gather across all partitions)  │
│                                                                 │
│  Used by: MongoDB, Riak, Cassandra, Elasticsearch, VoltDB      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Term-Partitioned Index (Global Index)

```
┌─────────────────────────────────────────────────────────────────┐
│              GLOBAL INDEX (Term-Partitioned)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Index itself is partitioned separately from the data.          │
│                                                                 │
│  Index Partition 0 (a-m):       Index Partition 1 (n-z):       │
│  ┌──────────────────────┐       ┌──────────────────────┐       │
│  │ color:blue → [392]   │       │ color:red → [191,556]│       │
│  │                      │       │ color:yellow→ [389]  │       │
│  └──────────────────────┘       └──────────────────────┘       │
│                                                                 │
│  Query "color=red" → go to index partition 1 only.             │
│                                                                 │
│  ✓ Reads are efficient (query one index partition)             │
│  ✗ Writes are slow and complex (may need to update index       │
│    partitions on DIFFERENT nodes → distributed transaction)    │
│  ✗ Index updates are often ASYNCHRONOUS                        │
│                                                                 │
│  Used by: DynamoDB (global secondary indexes, async update)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Rebalancing Partitions

When adding/removing nodes, partitions need to be redistributed.

### Strategies

```
┌──────────────────────────────────────────────────────────────────┐
│              REBALANCING STRATEGIES                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✗ DON'T: hash mod N                                            │
│    If N (number of nodes) changes, MOST keys move.              │
│    Adding one node = rehash everything = terrible.              │
│                                                                  │
│  ✓ FIXED NUMBER OF PARTITIONS:                                  │
│    Create many more partitions than nodes (e.g., 1000           │
│    partitions on 10 nodes = 100 per node).                      │
│    Adding a node → steal a few partitions from each node.       │
│    Partition count never changes; only assignment changes.       │
│                                                                  │
│    ┌──────────────────────────────────────────────────────┐     │
│    │ Before: 3 nodes, 12 partitions (4 each)              │     │
│    │ Node A: [P1, P2, P3, P4]                             │     │
│    │ Node B: [P5, P6, P7, P8]                             │     │
│    │ Node C: [P9, P10, P11, P12]                          │     │
│    │                                                       │     │
│    │ After adding Node D:                                  │     │
│    │ Node A: [P1, P2, P3]                                  │     │
│    │ Node B: [P5, P6, P7]                                  │     │
│    │ Node C: [P9, P10, P11]                                │     │
│    │ Node D: [P4, P8, P12]  ← stole one from each        │     │
│    └──────────────────────────────────────────────────────┘     │
│    Used by: Riak, Elasticsearch, Couchbase, Voldemort           │
│                                                                  │
│  ✓ DYNAMIC PARTITIONING:                                        │
│    Partition splits when it exceeds a size threshold.            │
│    Partition merges when it shrinks below a threshold.           │
│    Number of partitions adapts to data volume.                   │
│    Used by: HBase, RethinkDB, MongoDB                           │
│                                                                  │
│  ✓ CONSISTENT HASHING (Virtual Nodes):                          │
│    Each node gets multiple positions on a hash ring.             │
│    Adding a node → it takes over part of the ring.              │
│    Only K/N keys move on average (K=keys, N=nodes).            │
│    Used by: Cassandra, DynamoDB                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Request Routing

How does a client know which node to connect to for a given key?

```
┌──────────────────────────────────────────────────────────────────┐
│              REQUEST ROUTING APPROACHES                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  APPROACH 1: Contact any node; it forwards if needed.           │
│  ┌────────┐    ┌────────┐                                       │
│  │ Client │───►│ Node 1 │──forward──► Node 3 (has the data)    │
│  └────────┘    └────────┘                                       │
│                                                                  │
│  APPROACH 2: Routing tier (partition-aware load balancer).       │
│  ┌────────┐    ┌──────────────┐    ┌────────┐                  │
│  │ Client │───►│ Routing Tier │───►│ Node 3 │                  │
│  └────────┘    └──────────────┘    └────────┘                  │
│                                                                  │
│  APPROACH 3: Client is partition-aware (knows the mapping).     │
│  ┌────────┐────────────────────────► Node 3                     │
│  │ Client │  (client knows key→node mapping)                    │
│  └────────┘                                                     │
│                                                                  │
│  HOW TO KEEP ROUTING INFO UP-TO-DATE?                           │
│  ─────────────────────────────────────                          │
│  Use a coordination service like ZooKeeper:                     │
│                                                                  │
│  ┌────────────────┐                                             │
│  │   ZooKeeper    │  Maintains authoritative mapping of         │
│  │                │  partitions → nodes.                        │
│  └───┬───────┬────┘                                             │
│      │       │  Notifies routing tier / nodes                   │
│      ▼       ▼  when mapping changes                            │
│  ┌──────┐ ┌────────────────┐                                    │
│  │Nodes │ │Routing Tier or │                                    │
│  │      │ │Client Library  │                                    │
│  └──────┘ └────────────────┘                                    │
│                                                                  │
│  HBase, SolrCloud, Kafka: use ZooKeeper                         │
│  Cassandra, Riak: gossip protocol (no external service)         │
│  MongoDB: has its own config server (mongos routers)            │
│  Couchbase: moxi router                                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: What is the difference between key range and hash partitioning?

**Key range**: Each partition owns a contiguous range of keys (A-G, H-N, O-Z). Supports efficient range queries but risks hot spots if access is skewed (e.g., all writes for today's date go to one partition). **Hash partitioning**: Keys are hashed and partitions own hash ranges. Distributes keys evenly (no hot spots) but loses the ability to do range queries since adjacent keys are scattered. Cassandra's compound keys combine both: hash the first part for partition assignment, sort the remaining parts within each partition.

### Q2: Explain scatter/gather and why it's a problem.

In a **document-partitioned (local) secondary index**, each partition maintains its own index covering only its local documents. A query on the secondary index (e.g., "find all red cars") must be sent to **every partition** (scatter), and results must be merged (gather). This is expensive and adds tail latency — the response is only as fast as the slowest partition. The alternative is a **global (term-partitioned) index** which is efficient for reads but makes writes slower and more complex.

### Q3: Why shouldn't you use hash mod N for partitioning?

If N (number of nodes) changes by even one, `hash(key) mod N` changes for almost every key, requiring nearly all data to be moved between nodes. This is catastrophically expensive. Instead, use **fixed number of partitions** (more partitions than nodes, reassign whole partitions), **dynamic partitioning** (split/merge partitions based on size), or **consistent hashing** (only K/N keys move when a node is added/removed).

### Q4: How does request routing work in partitioned databases?

Three approaches: (1) **Any node**: client contacts any node, which forwards the request to the correct partition owner. (2) **Routing tier**: a partition-aware proxy/load balancer routes requests to the correct node. (3) **Client awareness**: the client itself maintains the partition-to-node mapping. The mapping is kept up-to-date via a coordination service like ZooKeeper (used by HBase, Kafka) or a gossip protocol (used by Cassandra, Riak).

### Q5: What is consistent hashing and how does it help with rebalancing?

Consistent hashing maps both keys and nodes onto a circular hash ring. Each key is assigned to the nearest node clockwise on the ring. When a node is added, it takes over keys from the next node on the ring; when removed, its keys move to the next node. Only K/N keys move on average (where K = total keys, N = nodes), compared to nearly all keys with hash mod N. **Virtual nodes** (each physical node gets multiple positions on the ring) improve balance and ensure even distribution.

---

*Based on Chapter 6 of "Designing Data-Intensive Applications" by Martin Kleppmann*
