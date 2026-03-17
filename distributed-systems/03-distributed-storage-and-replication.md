# Distributed Storage Systems: Replication and Partitioning

## Table of Contents
1. [Introduction to Distributed Storage](#introduction-to-distributed-storage)
2. [Data Replication](#data-replication)
3. [Data Partitioning (Sharding)](#data-partitioning-sharding)
4. [Consistent Hashing](#consistent-hashing)
5. [Replication Strategies](#replication-strategies)
6. [Conflict Resolution](#conflict-resolution)
7. [Real-World Systems](#real-world-systems)
8. [Interview Questions](#interview-questions)

---

## Introduction to Distributed Storage

### Why Distribute Data?

```
┌─────────────────────────────────────────────────────────────────┐
│            WHY DISTRIBUTED STORAGE?                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐        ┌─────────────────────────────────┐│
│  │ SINGLE SERVER   │        │    DISTRIBUTED SYSTEM          ││
│  ├─────────────────┤        ├─────────────────────────────────┤│
│  │                 │        │                                 ││
│  │ • Limited       │        │ • Horizontal scaling           ││
│  │   capacity      │   ──►  │ • High availability            ││
│  │ • Single point  │        │ • Geographic distribution      ││
│  │   of failure    │        │ • Fault tolerance              ││
│  │ • Limited       │        │ • Lower latency (data closer)  ││
│  │   throughput    │        │ • Higher throughput            ││
│  │                 │        │                                 ││
│  └─────────────────┘        └─────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

| Concept | Definition |
|---------|------------|
| **Replication** | Storing copies of data on multiple nodes |
| **Partitioning** | Splitting data across multiple nodes |
| **Sharding** | Horizontal partitioning of data |
| **Replica** | A copy of data on a different node |
| **Primary/Leader** | The authoritative copy that handles writes |
| **Secondary/Follower** | Copies that replicate from the primary |

### Data Distribution Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│           DATA DISTRIBUTION STRATEGIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. REPLICATION ONLY                                           │
│     ┌────────┐   ┌────────┐   ┌────────┐                      │
│     │ Data A │   │ Data A │   │ Data A │  (Same data)         │
│     │ Data B │   │ Data B │   │ Data B │                      │
│     │ Data C │   │ Data C │   │ Data C │                      │
│     └────────┘   └────────┘   └────────┘                      │
│      Node 1       Node 2       Node 3                          │
│                                                                 │
│  2. PARTITIONING ONLY                                          │
│     ┌────────┐   ┌────────┐   ┌────────┐                      │
│     │ Data A │   │ Data D │   │ Data G │  (Different data)    │
│     │ Data B │   │ Data E │   │ Data H │                      │
│     │ Data C │   │ Data F │   │ Data I │                      │
│     └────────┘   └────────┘   └────────┘                      │
│      Node 1       Node 2       Node 3                          │
│                                                                 │
│  3. PARTITIONING + REPLICATION (Most common)                   │
│     ┌────────┐   ┌────────┐   ┌────────┐                      │
│     │ A (P)  │   │ B (P)  │   │ C (P)  │  P = Primary         │
│     │ B (R)  │   │ C (R)  │   │ A (R)  │  R = Replica         │
│     │ C (R)  │   │ A (R)  │   │ B (R)  │                      │
│     └────────┘   └────────┘   └────────┘                      │
│      Node 1       Node 2       Node 3                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Replication

### Why Replicate?

1. **High Availability**: System survives node failures
2. **Reduced Latency**: Serve from geographically closer replicas
3. **Read Scalability**: Distribute read load across replicas
4. **Disaster Recovery**: Protect against data center failures

### Replication Topologies

```
┌─────────────────────────────────────────────────────────────────┐
│              REPLICATION TOPOLOGIES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. SINGLE-LEADER (Primary-Secondary)                          │
│                                                                 │
│        Writes                                                   │
│           │                                                     │
│           ▼                                                     │
│     ┌──────────┐                                               │
│     │  LEADER  │                                               │
│     └────┬─────┘                                               │
│          │ Replication                                         │
│     ┌────┴────────────┐                                        │
│     ▼         ▼       ▼                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐                                   │
│  │Follow│ │Follow│ │Follow│  ◄── Reads                        │
│  └──────┘ └──────┘ └──────┘                                   │
│                                                                 │
│  2. MULTI-LEADER                                               │
│                                                                 │
│     ┌──────────┐     ┌──────────┐                             │
│     │ Leader 1 │◄───►│ Leader 2 │    Both accept writes       │
│     └────┬─────┘     └────┬─────┘                             │
│          │                │                                    │
│     ┌────┴────┐      ┌────┴────┐                              │
│     ▼         ▼      ▼         ▼                              │
│  Followers    Followers                                        │
│                                                                 │
│  3. LEADERLESS (Peer-to-Peer)                                  │
│                                                                 │
│     ┌──────┐◄──────►┌──────┐                                  │
│     │Node 1│        │Node 2│     All nodes equal              │
│     └──┬───┘        └───┬──┘                                  │
│        │       ┌────────┘                                      │
│        │       │                                               │
│        ▼       ▼                                               │
│       ┌──────┐                                                 │
│       │Node 3│                                                 │
│       └──────┘                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Synchronous vs Asynchronous Replication

```
┌─────────────────────────────────────────────────────────────────┐
│         SYNC vs ASYNC REPLICATION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SYNCHRONOUS:                                                  │


---

## Data Partitioning (Sharding)

### Why Partition?

When data grows beyond what a single node can handle:
- **Storage capacity**: Data too large for one machine
- **Throughput**: More concurrent requests than one machine can serve
- **Memory**: Working set doesn't fit in RAM

### Partitioning Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              PARTITIONING STRATEGIES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RANGE PARTITIONING                                         │
│                                                                 │
│     Partition by key ranges:                                   │
│     ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐│
│     │ Users A-H       │ │ Users I-P       │ │ Users Q-Z      ││
│     │ (Shard 1)       │ │ (Shard 2)       │ │ (Shard 3)      ││
│     └─────────────────┘ └─────────────────┘ └────────────────┘│
│                                                                 │
│     ✓ Efficient range queries                                  │
│     ✗ Hot spots if keys not uniformly distributed             │
│                                                                 │
│  2. HASH PARTITIONING                                          │
│                                                                 │
│     hash(key) % num_partitions                                 │
│     ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐│
│     │ hash=0,3,6...   │ │ hash=1,4,7...   │ │ hash=2,5,8...  ││
│     │ (Shard 1)       │ │ (Shard 2)       │ │ (Shard 3)      ││
│     └─────────────────┘ └─────────────────┘ └────────────────┘│
│                                                                 │
│     ✓ Uniform distribution                                     │
│     ✗ Range queries hit all partitions                        │
│                                                                 │
│  3. DIRECTORY-BASED (Lookup Table)                             │
│                                                                 │
│     ┌────────────────────────────────────────────────┐        │
│     │          DIRECTORY SERVICE                      │        │
│     │    Key A → Shard 2                             │        │
│     │    Key B → Shard 1                             │        │
│     │    Key C → Shard 3                             │        │
│     └────────────────────────────────────────────────┘        │
│                                                                 │
│     ✓ Flexible placement                                       │
│     ✗ Directory is single point of failure                    │
│     ✗ Additional lookup latency                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Partition Rebalancing

When nodes are added or removed, data must be redistributed:

```
┌─────────────────────────────────────────────────────────────────┐
│              REBALANCING STRATEGIES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FIXED NUMBER OF PARTITIONS (Pre-splitting)                    │
│  ──────────────────────────────────────────                    │
│                                                                 │
│  Create many more partitions than nodes:                       │
│  • 1000 partitions across 10 nodes = 100 partitions/node      │
│  • Add node → steal some partitions from existing nodes       │
│  • Remove node → distribute its partitions to others          │
│                                                                 │
│  Before: Node A [1-250], Node B [251-500], ...                │
│  After:  Node A [1-200], Node B [251-450], Node E [201-250]...│
│                                                                 │
│  DYNAMIC PARTITIONING                                          │
│  ────────────────────                                          │
│                                                                 │
│  Split partitions when they get too large:                     │
│  • Partition grows → split into two                           │
│  • Two small partitions → merge into one                      │
│                                                                 │
│  Used by: HBase, RethinkDB, MongoDB                           │
│                                                                 │
│  PARTITIONING BY NODE COUNT                                    │
│  ───────────────────────────                                   │
│                                                                 │
│  Fixed number of partitions per node:                          │
│  • Add node → split random existing partitions                │
│  • Keeps partition sizes roughly equal                        │
│                                                                 │
│  Used by: Cassandra, Ketama                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Consistent Hashing

### The Problem with Simple Hashing

```
┌─────────────────────────────────────────────────────────────────┐
│         PROBLEM: ADDING/REMOVING NODES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Simple hash: partition = hash(key) % num_nodes                │
│                                                                 │
│  With 3 nodes:                                                 │
│  hash("user123") % 3 = 1 → Node 1                             │
│                                                                 │
│  Add a 4th node:                                               │
│  hash("user123") % 4 = 3 → Node 3  ← DIFFERENT!               │
│                                                                 │
│  Problem: Almost ALL keys need to be remapped!                 │
│  This causes massive data movement.                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Consistent Hashing Solution

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSISTENT HASHING                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hash both keys AND nodes onto a ring:                         │
│                                                                 │
│                    Node A                                      │
│                      ○                                         │
│                  ╱       ╲                                     │
│             key1●         ●key2                                │
│            ╱                   ╲                                │
│        Node D○                   ○Node B                       │
│            ╲                   ╱                                │
│             key4●         ●key3                                │
│                  ╲       ╱                                     │
│                      ○                                         │
│                    Node C                                      │
│                                                                 │
│  Rule: Key is stored on the FIRST node clockwise               │
│  • key1 → Node A                                               │
│  • key2 → Node B                                               │
│  • key3 → Node C                                               │
│  • key4 → Node D                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Adding/Removing Nodes

```
┌─────────────────────────────────────────────────────────────────┐
│         CONSISTENT HASHING: NODE CHANGES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ADDING NODE E (between C and D):                              │
│                                                                 │
│                    Node A                                      │
│                      ○                                         │
│                  ╱       ╲                                     │
│             key1●                                              │
│            ╱                                                   │
│        Node D○          ○Node B                                │
│            ╲          ╱                                        │
│        ●key4    ○Node E  (NEW)                                │
│                    ╲                                           │
│                      ○                                         │
│                    Node C                                      │
│                                                                 │
│  Only keys between C and E need to move!                       │
│  (key4 moves from D to E)                                      │
│                                                                 │
│  Benefit: Only K/N keys move on average                        │
│  (K = total keys, N = number of nodes)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Virtual Nodes (VNodes)

```
┌─────────────────────────────────────────────────────────────────┐
│              VIRTUAL NODES                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Problem: With few nodes, distribution can be uneven           │
│                                                                 │
│  Solution: Each physical node has multiple virtual nodes       │
│                                                                 │
│                 A1      A2                                     │
│                  ○       ○                                     │
│              ╱               ╲                                 │
│          B1○                   ○B2                             │
│            │                   │                                │
│          A3○                   ○B3                             │
│              ╲               ╱                                 │
│                  ○       ○                                     │
│                 B4      A4                                     │
│                                                                 │
│  Node A has vnodes: A1, A2, A3, A4                            │
│  Node B has vnodes: B1, B2, B3, B4                            │
│                                                                 │
│  Benefits:                                                     │
│  • More uniform distribution                                   │
│  • Heterogeneous hardware (more vnodes for powerful nodes)    │
│  • Smoother rebalancing                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Replication Strategies

### Single-Leader Replication

```
┌─────────────────────────────────────────────────────────────────┐
│           SINGLE-LEADER REPLICATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                                                        │
│    │                                                           │
│    │ Write (X=5)                                               │
│    ▼                                                           │
│  ┌──────────────┐                                              │
│  │    LEADER    │                                              │
│  │    X = 5     │                                              │
│  └──────┬───────┘                                              │
│         │                                                       │
│         │ Replication Log                                      │
│         │                                                       │
│    ┌────┴────────────┬────────────────┐                        │
│    ▼                 ▼                ▼                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ FOLLOWER │  │ FOLLOWER │  │ FOLLOWER │                     │
│  │  X = 5   │  │  X = 5   │  │  X = 5   │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│                                                                 │
│  Advantages:                                                   │
│  • Simple to understand and implement                         │
│  • No write conflicts                                          │
│  • Strong consistency possible                                 │
│                                                                 │
│  Disadvantages:                                                │
│  • Leader is write bottleneck                                 │
│  • Leader failure requires failover                           │
│  • Cross-region latency for writes                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Leader Replication

```
┌─────────────────────────────────────────────────────────────────┐
│           MULTI-LEADER REPLICATION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DC 1 (US)              DC 2 (Europe)          DC 3 (Asia)     │
│  ┌──────────┐           ┌──────────┐           ┌──────────┐    │
│  │ Leader 1 │◄─────────►│ Leader 2 │◄─────────►│ Leader 3 │    │
│  └────┬─────┘           └────┬─────┘           └────┬─────┘    │
│       │                      │                      │          │
│  ┌────┴────┐            ┌────┴────┐            ┌────┴────┐     │
│  │Followers│            │Followers│            │Followers│     │
│  └─────────┘            └─────────┘            └─────────┘     │
│                                                                 │
│  Use Cases:                                                    │
│  • Multi-datacenter deployments                                │
│  • Offline-capable applications                                │
│  • Real-time collaborative editing                             │
│                                                                 │
│  Challenges:                                                   │
│  • Write conflicts between leaders                             │
│  • Requires conflict resolution strategy                       │
│  • Complexity in maintaining consistency                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Leaderless Replication

```
┌─────────────────────────────────────────────────────────────────┐
│           LEADERLESS REPLICATION                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client writes to MULTIPLE nodes simultaneously:               │
│                                                                 │
│           Client                                               │
│             │                                                   │
│    ┌────────┼────────┐                                         │
│    ▼        ▼        ▼                                         │
│  ┌────┐  ┌────┐  ┌────┐                                       │
│  │ N1 │  │ N2 │  │ N3 │   Write to all (or quorum)           │
│  │ ✓  │  │ ✓  │  │ ✗  │   N3 temporarily unavailable         │
│  └────┘  └────┘  └────┘                                       │
│                                                                 │
│  Quorum Rules:                                                 │
│  • W = write quorum (min nodes for successful write)          │
│  • R = read quorum (min nodes for successful read)            │
│  • N = total replicas                                          │
│                                                                 │
│  For consistency: W + R > N                                    │
│                                                                 │
│  Example (N=3):                                                │
│  • W=2, R=2 → Always overlap (strong consistency)             │
│  • W=1, R=1 → May miss updates (eventual consistency)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Quorum Configurations

| Configuration | W | R | Guarantee |
|--------------|---|---|-----------|
| Strong consistency | 2 | 2 | Always read latest (for N=3) |
| Write-heavy | 1 | 3 | Fast writes, slower reads |
| Read-heavy | 3 | 1 | Slower writes, fast reads |
| Eventual | 1 | 1 | No consistency guarantee |

---

## Conflict Resolution

### Why Conflicts Happen

In multi-leader or leaderless systems, concurrent writes to the same key can cause conflicts:

```
┌─────────────────────────────────────────────────────────────────┐
│              WRITE CONFLICT EXAMPLE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Time ───────────────────────────────────────────►             │
│                                                                 │
│  Leader 1:  X=A ─────────► X=B                                 │
│                   │                                             │
│                   │ (concurrent)                                │
│                   │                                             │
│  Leader 2:  X=A ─────────► X=C                                 │
│                                                                 │
│  Conflict: Leader 1 has X=B, Leader 2 has X=C                  │
│  Question: What should X be after replication?                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Conflict Resolution Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│         CONFLICT RESOLUTION STRATEGIES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. LAST-WRITE-WINS (LWW)                                      │
│  ────────────────────────                                      │
│  • Attach timestamp to each write                              │
│  • Latest timestamp wins                                       │
│  • Simple but can lose data                                    │
│                                                                 │
│  X=B (t=100) vs X=C (t=105) → X=C wins                        │
│                                                                 │
│  2. MERGE VALUES                                               │
│  ───────────────                                               │
│  • Combine conflicting values                                  │
│  • Application-specific logic                                  │
│                                                                 │
│  Shopping cart: {item1} + {item2} = {item1, item2}            │
│                                                                 │
│  3. VERSION VECTORS / VECTOR CLOCKS                            │
│  ──────────────────────────────────                            │
│  • Track causal history                                        │
│  • Detect concurrent vs sequential                             │
│  • Pass conflicts to application                               │
│                                                                 │
│  4. CRDTs (Conflict-free Replicated Data Types)               │
│  ──────────────────────────────────────────────                │
│  • Data structures designed to merge                          │
│  • No conflicts by design                                      │
│  • Examples: G-Counter, OR-Set                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Version Vectors

```
┌─────────────────────────────────────────────────────────────────┐
│              VERSION VECTORS                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Track version per node:                                       │
│                                                                 │
│  Node A writes X=1:  [A:1, B:0, C:0]                          │
│  Node B writes X=2:  [A:1, B:1, C:0]                          │
│  Node A writes X=3:  [A:2, B:1, C:0]                          │
│                                                                 │
│  Comparing versions:                                           │
│                                                                 │
│  [A:2, B:1] vs [A:1, B:2]                                     │
│                                                                 │
│  Neither dominates! → CONFLICT (concurrent writes)            │
│                                                                 │
│  [A:2, B:1] vs [A:1, B:0]                                     │
│                                                                 │
│  First dominates → No conflict (sequential)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```


---

## Real-World Systems

### System Comparison

| System | Partitioning | Replication | Consistency |
|--------|-------------|-------------|-------------|
| **Cassandra** | Consistent hashing | Leaderless, quorum | Tunable |
| **DynamoDB** | Hash + range | Multi-leader | Eventual/Strong |
| **MongoDB** | Range-based | Single-leader | Strong |
| **CockroachDB** | Range-based | Raft consensus | Serializable |
| **Redis Cluster** | Hash slots | Single-leader | Strong |
| **Kafka** | Topic partitions | Single-leader | Strong ordering |

### Amazon DynamoDB Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              DYNAMODB ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    REQUEST ROUTER                        │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐        │
│  │ Partition  │     │ Partition  │     │ Partition  │        │
│  │     A      │     │     B      │     │     C      │        │
│  │            │     │            │     │            │        │
│  │  ┌──────┐  │     │  ┌──────┐  │     │  ┌──────┐  │        │
│  │  │Leader│  │     │  │Leader│  │     │  │Leader│  │        │
│  │  └──────┘  │     │  └──────┘  │     │  └──────┘  │        │
│  │  ┌──────┐  │     │  ┌──────┐  │     │  ┌──────┐  │        │
│  │  │Replica│ │     │  │Replica│ │     │  │Replica│ │        │
│  │  └──────┘  │     │  └──────┘  │     │  └──────┘  │        │
│  │  ┌──────┐  │     │  ┌──────┐  │     │  ┌──────┐  │        │
│  │  │Replica│ │     │  │Replica│ │     │  │Replica│ │        │
│  │  └──────┘  │     │  └──────┘  │     │  └──────┘  │        │
│  └────────────┘     └────────────┘     └────────────┘        │
│                                                                 │
│  Key Features:                                                 │
│  • Automatic partitioning                                      │
│  • Multi-AZ replication                                        │
│  • Tunable consistency per request                            │
│  • Global tables for multi-region                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Apache Cassandra Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              CASSANDRA ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client writes to ANY node (coordinator):                      │
│                                                                 │
│     Client                                                     │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────┐    Gossip     ┌─────────┐                        │
│  │ Node A  │◄─────────────►│ Node B  │                        │
│  │(coord)  │               │         │                        │
│  └────┬────┘               └─────────┘                        │
│       │                          ▲                             │
│       │ Write to replicas        │ Gossip                     │
│       │                          │                             │
│       ▼                          │                             │
│  ┌─────────┐               ┌─────────┐                        │
│  │ Node C  │◄─────────────►│ Node D  │                        │
│  │(replica)│    Gossip     │(replica)│                        │
│  └─────────┘               └─────────┘                        │
│                                                                 │
│  Key Features:                                                 │
│  • Consistent hashing with vnodes                             │
│  • Gossip protocol for membership                             │
│  • Tunable consistency (ONE, QUORUM, ALL)                     │
│  • No single point of failure                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: Explain the difference between replication and partitioning.**

| Aspect | Replication | Partitioning |
|--------|-------------|--------------|
| Purpose | Fault tolerance, read scaling | Capacity, write scaling |
| Data | Same data on multiple nodes | Different data on each node |
| Failure impact | Can serve from other replicas | Partition data unavailable |
| Complexity | Consistency challenges | Routing, cross-partition queries |

**Q2: How does consistent hashing minimize data movement when nodes change?**

In consistent hashing:
- Keys and nodes are mapped to the same hash ring
- Each key is stored on the next node clockwise
- When a node is added/removed, only keys between it and its predecessor are affected
- On average, only `K/N` keys move (K=total keys, N=nodes)

**Q3: What's the difference between synchronous and asynchronous replication?**

| Sync | Async |
|------|-------|
| Wait for all replicas | Return immediately |
| Strong consistency | Eventual consistency |
| Higher latency | Lower latency |
| Lower availability | Higher availability |
| Data durability guaranteed | Risk of data loss |

**Q4: Explain the CAP theorem trade-offs in partitioning.**

During a network partition:
- **CP**: Reject writes to maintain consistency (some partitions unavailable)
- **AP**: Accept writes everywhere, merge conflicts later

### Design Questions

**Q5: Design a URL shortener with high availability.**

```
Architecture:
├── Write Path
│   ├── Generate short code (hash or counter)
│   ├── Write to primary
│   └── Async replicate to secondaries
├── Read Path
│   ├── Consistent hash to find partition
│   └── Read from any replica (eventual consistency OK)
├── Partitioning
│   └── Hash(short_code) % num_partitions
└── Replication
    └── 3 replicas per partition (1 leader, 2 followers)
```

**Q6: How would you handle hot partitions?**

Solutions:
1. **Add jitter**: Append random suffix to keys
2. **Virtual partitioning**: Split hot partition
3. **Caching**: Cache hot keys at application layer
4. **Adaptive partitioning**: Auto-split based on load

---

## Summary

### Key Takeaways

1. **Replication** provides fault tolerance and read scalability; **partitioning** provides write scalability and storage capacity

2. **Consistent hashing** minimizes data movement when cluster size changes

3. **Replication strategies**:
   - Single-leader: Simple, no write conflicts
   - Multi-leader: Multi-region, but conflicts
   - Leaderless: Highly available, quorum-based

4. **Quorum formula**: `W + R > N` for strong consistency

5. **Conflict resolution** is essential for multi-leader and leaderless systems

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         DISTRIBUTED STORAGE CHEAT SHEET                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Partitioning:                                                 │
│  • Range: Good for range queries, risk of hotspots            │
│  • Hash: Uniform distribution, no range queries               │
│  • Consistent hash: Minimal data movement                     │
│                                                                 │
│  Replication:                                                  │
│  • Single-leader: Simple, no conflicts                        │
│  • Multi-leader: Multi-DC, conflicts                          │
│  • Leaderless: Quorum, eventual consistency                   │
│                                                                 │
│  Quorum (N replicas):                                          │
│  • Strong consistency: W + R > N                               │
│  • Common: W=2, R=2 for N=3                                   │
│                                                                 │
│  Conflict Resolution:                                          │
│  • LWW: Simple, data loss possible                            │
│  • Version vectors: Detect conflicts                          │
│  • CRDTs: Conflict-free by design                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

