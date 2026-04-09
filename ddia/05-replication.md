# Chapter 5: Replication

## Table of Contents

1. [Why Replicate?](#why-replicate)
2. [Leaders and Followers](#leaders-and-followers)
3. [Synchronous vs Asynchronous Replication](#synchronous-vs-asynchronous-replication)
4. [Setting Up New Followers](#setting-up-new-followers)
5. [Handling Node Outages](#handling-node-outages)
6. [Problems with Replication Lag](#problems-with-replication-lag)
7. [Multi-Leader Replication](#multi-leader-replication)
8. [Leaderless Replication](#leaderless-replication)
9. [Interview Questions](#interview-questions)

---

## Why Replicate?

**Replication** means keeping a copy of the same data on multiple machines connected via a network.

```
┌─────────────────────────────────────────────────────────────────┐
│              REASONS TO REPLICATE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. LATENCY:    Keep data geographically close to users         │
│                 (read from nearest datacenter)                  │
│                                                                 │
│  2. AVAILABILITY: System continues working even if some         │
│                   machines (or entire datacenters) go down      │
│                                                                 │
│  3. READ THROUGHPUT: Scale out read queries across               │
│                      multiple replicas                          │
│                                                                 │
│  The DIFFICULTY: Handling CHANGES to replicated data.           │
│  If data never changed, replication would be trivial.           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Three popular algorithms: **single-leader**, **multi-leader**, **leaderless**.

---

## Leaders and Followers

The most common approach: **leader-based replication** (also: master-slave, active-passive).

```
┌─────────────────────────────────────────────────────────────────┐
│              LEADER-BASED REPLICATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client writes ────► ┌────────────┐                             │
│                       │   LEADER   │ (master / primary)         │
│                       │  (read +   │                             │
│                       │   write)   │                             │
│                       └──┬────┬───┘                             │
│                          │    │                                  │
│           Replication    │    │    Replication                   │
│           Stream         │    │    Stream                        │
│                          ▼    ▼                                  │
│                    ┌──────┐  ┌──────┐                           │
│  Client reads ───► │FOLLOW│  │FOLLOW│  (slaves / secondaries)  │
│                    │ER 1  │  │ER 2  │  (read-only)             │
│                    └──────┘  └──────┘                           │
│                                                                 │
│  Used by: PostgreSQL, MySQL, Oracle, SQL Server, MongoDB,       │
│           RabbitMQ, Kafka, RethinkDB                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. One replica is designated the **leader**. All writes go to the leader.
2. The leader writes new data to its local storage.
3. The leader sends data changes to all **followers** via a **replication log** (or change stream).
4. Each follower applies the changes in the same order the leader processed them.
5. Clients can read from any replica (leader or follower), but writes go only to the leader.

---

## Synchronous vs Asynchronous Replication

```
┌─────────────────────────────────────────────────────────────────┐
│              SYNCHRONOUS REPLICATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client ──Write──► Leader ──Replicate──► Follower               │
│                       │                      │                  │
│                       │    ◄── ACK ──────────┘                  │
│                       │                                         │
│  Client ◄── OK ──────┘  (only after follower confirms)         │
│                                                                 │
│  ✓ Follower guaranteed to have up-to-date copy                 │
│  ✗ If follower is slow/dead, leader BLOCKS all writes          │
│  ✗ Any one slow node halts the entire system                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│              ASYNCHRONOUS REPLICATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client ──Write──► Leader ──Replicate──► Follower               │
│                       │                  (eventually)           │
│  Client ◄── OK ──────┘  (immediately, doesn't wait)            │
│                                                                 │
│  ✓ Leader doesn't block on slow followers                      │
│  ✓ Much faster writes                                           │
│  ✗ If leader fails, unreplicated writes are LOST               │
│  ✗ Followers may serve STALE data                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│              SEMI-SYNCHRONOUS (Practical Approach)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ONE follower is synchronous (guaranteed up-to-date backup)    │
│  ALL other followers are asynchronous                           │
│                                                                 │
│  If the synchronous follower becomes slow → promote another    │
│  follower to be the new synchronous one.                        │
│                                                                 │
│  Guarantees: at least 2 nodes have every write (leader +       │
│  one sync follower) while keeping the system responsive.        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setting Up New Followers

You can't just copy data files — the data is constantly changing. You can't lock the database (violates availability goals). The standard process:

```
┌─────────────────────────────────────────────────────────────────┐
│              SETTING UP A NEW FOLLOWER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Take a consistent SNAPSHOT of the leader's database    │
│          (without locking if possible, e.g., innodb backup)     │
│                                                                 │
│  Step 2: Copy the snapshot to the new follower node             │
│                                                                 │
│  Step 3: Follower connects to leader and requests all changes   │
│          that happened SINCE the snapshot                        │
│          (using the snapshot's position in the replication log)  │
│                                                                 │
│  Step 4: Follower processes the backlog of changes ("caught up")│
│          and then continues processing new changes in real time │
│                                                                 │
│  The snapshot's position is called:                             │
│  • PostgreSQL: log sequence number (LSN)                        │
│  • MySQL: binlog coordinates                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Handling Node Outages

### Follower Failure: Catch-Up Recovery

Each follower keeps a log of changes received from the leader. On restart, the follower knows the last transaction it processed, connects to the leader, and requests all changes since that point.

### Leader Failure: Failover

**Failover** is the process of promoting a follower to be the new leader:

```
┌─────────────────────────────────────────────────────────────────┐
│              LEADER FAILOVER PROCESS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DETECT leader failure                                       │
│     → Typically using a timeout (no heartbeat for 30 seconds)   │
│                                                                 │
│  2. CHOOSE a new leader                                         │
│     → Election (consensus) or appointed by controller node      │
│     → Best candidate: follower with most up-to-date data        │
│                                                                 │
│  3. RECONFIGURE the system                                      │
│     → Clients redirected to new leader                          │
│     → Other followers start replicating from new leader         │
│     → Old leader (when it comes back) must become a follower   │
│                                                                 │
│  THINGS THAT CAN GO WRONG:                                      │
│  ─────────────────────────                                      │
│  • Async replication → new leader may be MISSING some writes   │
│    from old leader (data loss!)                                 │
│                                                                 │
│  • Split brain: TWO nodes both believe they are the leader      │
│    → Both accept writes → DATA DIVERGENCE / CORRUPTION         │
│    → Must have a mechanism to shut down one leader              │
│                                                                 │
│  • Timeout too short → unnecessary failovers (flapping)         │
│    Timeout too long → longer recovery time                      │
│                                                                 │
│  GitHub incident (2012): MySQL failover, new leader had         │
│  out-of-date auto-increment counter, issued duplicate primary   │
│  keys, which were also used as Redis keys → data leak from     │
│  wrong user accounts. Fixed by shutting down MySQL.             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Problems with Replication Lag

With asynchronous replication, followers can be behind. This **replication lag** causes various anomalies:

### 1. Reading Your Own Writes

```
┌─────────────────────────────────────────────────────────────────┐
│              READ-AFTER-WRITE CONSISTENCY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User writes profile ──► Leader (write succeeds)                │
│                                                                 │
│  User reads profile  ──► Follower (stale! hasn't replicated)   │
│                          "Where did my update go?!"             │
│                                                                 │
│  Timeline:                                                      │
│  ──────────────────────────────────────────────►  time          │
│       ▲ write                  ▲ read (stale!)                  │
│       │                        │                                │
│    Leader                   Follower                            │
│    sees update              hasn't received it yet              │
│                                                                 │
│  SOLUTIONS:                                                     │
│  • Read your own data from LEADER (e.g., own profile)           │
│  • Track time of last write; for 1 minute after, read from     │
│    leader only                                                  │
│  • Client remembers timestamp of last write; replica must       │
│    be at least that up-to-date before serving the read          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Monotonic Reads

```
┌─────────────────────────────────────────────────────────────────┐
│              MONOTONIC READS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User reads from Follower 1 → sees comment by User X            │
│  User reads from Follower 2 → comment GONE (hasn't replicated) │
│  "The comment appeared and then disappeared — time travel!"     │
│                                                                 │
│  Follower 1 (more up-to-date):    Follower 2 (lagging):        │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │ Comment: "Hello!"    │         │ (no comment yet)     │     │
│  └──────────────────────┘         └──────────────────────┘     │
│                                                                 │
│  SOLUTION:                                                      │
│  Each user always reads from the SAME replica                   │
│  (e.g., pick replica based on hash of user ID).                │
│  Guarantees: if you saw data once, you'll never see             │
│  an older state on subsequent reads.                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Consistent Prefix Reads

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSISTENT PREFIX READS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A conversation between Mr. Poons and Mrs. Cake:                │
│                                                                 │
│  Actual order:                                                  │
│    Mr. Poons:  "How far into the future can you see?"           │
│    Mrs. Cake:  "About ten seconds usually."                     │
│                                                                 │
│  But a third-party observer may see:                            │
│    Mrs. Cake:  "About ten seconds usually."                     │
│    Mr. Poons:  "How far into the future can you see?"           │
│                                                                 │
│  This happens when different partitions replicate at             │
│  different speeds — causally related writes arrive              │
│  out of order!                                                  │
│                                                                 │
│  SOLUTION:                                                      │
│  Ensure causally related writes are sent to the same            │
│  partition, or use causal ordering mechanisms.                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Multi-Leader Replication

```
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-LEADER (ACTIVE/ACTIVE) REPLICATION            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Datacenter A               Datacenter B                       │
│  ┌──────────────┐           ┌──────────────┐                   │
│  │   Leader A   │◄─────────►│   Leader B   │                   │
│  │  (accepts    │  async     │  (accepts    │                   │
│  │   writes)    │ replication│   writes)    │                   │
│  └──┬───────┬───┘           └──┬───────┬───┘                   │
│     │       │                  │       │                        │
│  ┌──┴──┐ ┌──┴──┐           ┌──┴──┐ ┌──┴──┐                   │
│  │Foll.│ │Foll.│           │Foll.│ │Foll.│                    │
│  └─────┘ └─────┘           └─────┘ └─────┘                    │
│                                                                 │
│  USE CASES:                                                     │
│  • Multi-datacenter operation (each DC has a leader)            │
│  • Clients with offline operation (each device is a "leader")  │
│  • Collaborative editing (Google Docs — each user is a "leader")│
│                                                                 │
│  BIGGEST PROBLEM: Write conflicts                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Handling Write Conflicts

```
┌─────────────────────────────────────────────────────────────────┐
│              WRITE CONFLICT EXAMPLE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User 1 (via Leader A):  UPDATE title = "B"                     │
│  User 2 (via Leader B):  UPDATE title = "C"                     │
│                                                                 │
│  Both succeed locally. When replicated → CONFLICT!              │
│                                                                 │
│  Leader A: title was A → B    Leader B: title was A → C         │
│  Leader A receives B → C      Leader B receives A → B           │
│  Now what?! Both have conflicting changes.                      │
│                                                                 │
│  CONFLICT RESOLUTION STRATEGIES:                                │
│  ──────────────────────────────                                 │
│  1. Last Write Wins (LWW):                                     │
│     Attach a timestamp; highest timestamp wins.                 │
│     Simple but LOSSY — silently drops conflicting writes.       │
│     Used by Cassandra, some DynamoDB configs.                   │
│                                                                 │
│  2. Merge values:                                               │
│     Concatenate: "B/C" or store both versions (siblings).       │
│     Application resolves later (e.g., show both to user).      │
│                                                                 │
│  3. Custom conflict resolution logic:                           │
│     Application provides a handler:                             │
│     • On write: handler called when conflict detected           │
│     • On read: all versions stored; handler called at read     │
│       time to merge (CouchDB approach)                         │
│                                                                 │
│  4. CRDTs (Conflict-free Replicated Data Types):               │
│     Data structures that can be merged automatically            │
│     (e.g., G-Counter, OR-Set). Used by Riak.                   │
│                                                                 │
│  5. Operational Transformation (Google Docs):                   │
│     Transform concurrent edits to converge.                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Leaderless Replication

No leader at all. Clients send writes to **several replicas directly** (or via a coordinator node that doesn't enforce ordering).

```
┌─────────────────────────────────────────────────────────────────┐
│              LEADERLESS REPLICATION (Dynamo-style)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client write ──► Replica 1  ✓ (success)                       │
│              ──► Replica 2  ✓ (success)                        │
│              ──► Replica 3  ✗ (down — missed write)            │
│                                                                 │
│  Write succeeds if 2 out of 3 replicas confirm (w=2)           │
│                                                                 │
│  Client read  ──► Replica 1  → value v2 (up-to-date)          │
│              ──► Replica 2  → value v2 (up-to-date)            │
│              ──► Replica 3  → value v1 (STALE!)                │
│                                                                 │
│  Read succeeds if 2 out of 3 replicas respond (r=2)            │
│  Client sees both v1 and v2, picks the newer one (v2)          │
│                                                                 │
│  Used by: Amazon DynamoDB, Riak, Cassandra, Voldemort           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Quorum Condition

```
┌─────────────────────────────────────────────────────────────────┐
│              QUORUM: w + r > n                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  n = total replicas                                             │
│  w = write quorum (number of nodes that must confirm write)     │
│  r = read quorum (number of nodes that must respond to read)    │
│                                                                 │
│  If w + r > n, at least ONE node in the read set will           │
│  have the latest write.                                         │
│                                                                 │
│  Typical: n=3, w=2, r=2  →  2+2=4 > 3  ✓                     │
│                                                                 │
│  n=3 replicas:  ┌───┐  ┌───┐  ┌───┐                           │
│                  │ 1 │  │ 2 │  │ 3 │                           │
│                  └───┘  └───┘  └───┘                           │
│  Write w=2:      ✓       ✓      ✗                              │
│  Read r=2:       ✓       ✗      ✓                              │
│                  ▲                                               │
│                  └── Node 1 was in both sets → has latest value │
│                                                                 │
│  TRADE-OFFS:                                                    │
│  • Larger w → slower writes, but more durable                  │
│  • Larger r → slower reads, but more likely to get latest      │
│  • w=1, r=n → fast writes, slow reads                          │
│  • w=n, r=1 → slow writes, fast reads                          │
│                                                                 │
│  WARNING: Even with w+r>n, edge cases can return stale reads:  │
│  • Sloppy quorums                                               │
│  • Concurrent writes (which "wins"?)                           │
│  • Concurrent read and write                                    │
│  • Failed write on some replicas (not rolled back)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Anti-Entropy and Read Repair

```
┌─────────────────────────────────────────────────────────────────┐
│  How stale replicas catch up:                                   │
│                                                                 │
│  READ REPAIR:                                                   │
│  Client reads from multiple replicas, detects stale value,      │
│  writes the newer value back to the stale replica.              │
│  Works well for frequently-read data.                           │
│                                                                 │
│  ANTI-ENTROPY PROCESS:                                          │
│  Background process compares data between replicas and          │
│  copies missing data. Doesn't preserve ordering.                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Version Vectors

To detect concurrent writes vs. causally-ordered writes, leaderless systems use **version vectors** (generalization of version clocks):

```
┌─────────────────────────────────────────────────────────────────┐
│              VERSION VECTORS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Each replica maintains a version number per key.               │
│  A version vector = collection of version numbers from          │
│  all replicas.                                                  │
│                                                                 │
│  Example with 3 replicas (A, B, C):                             │
│                                                                 │
│  Write 1 (to A): version vector = {A:1, B:0, C:0}              │
│  Write 2 (to B): version vector = {A:1, B:1, C:0}              │
│                                                                 │
│  Are these concurrent? Compare element-wise:                    │
│  {A:1, B:0, C:0} vs {A:1, B:1, C:0}                           │
│   A: 1 ≤ 1  ✓                                                  │
│   B: 0 < 1  → First happened before second                     │
│   Write 1 HAPPENED BEFORE Write 2 (not concurrent)             │
│                                                                 │
│  Write 3 (to A): {A:2, B:0, C:0}                               │
│  Write 4 (to B): {A:1, B:1, C:0}                               │
│  Neither dominates → CONCURRENT → need conflict resolution     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: Compare single-leader, multi-leader, and leaderless replication.

**Single-leader**: All writes go to one leader, replicated to followers. Simple, no write conflicts, but leader is a bottleneck and single point of failure. **Multi-leader**: Multiple nodes accept writes; changes replicated between leaders. Better for multi-datacenter setups but introduces write conflicts that must be resolved. **Leaderless**: No leader; clients write to multiple replicas using quorums (w + r > n). High availability, no failover needed, but complex conflict resolution and weaker consistency guarantees.

### Q2: What is the quorum condition and why is it important?

The quorum condition is **w + r > n**, where n = total replicas, w = write quorum, r = read quorum. It ensures that the set of nodes read from and the set of nodes written to **overlap** — at least one node in every read has the latest write. This provides a probabilistic guarantee of reading up-to-date data without requiring a leader. However, it's not foolproof: sloppy quorums, concurrent writes, and network partitions can still cause stale reads.

### Q3: Explain three problems caused by replication lag.

1. **Read-after-write**: User writes data, then reads from a stale follower and doesn't see their own write. Fix: read own data from leader.
2. **Non-monotonic reads**: User reads from a fresh follower, then a stale one, and sees data "go back in time." Fix: always read from the same replica.
3. **Consistent prefix reads**: Causally related writes appear in wrong order because different partitions replicate at different speeds. Fix: ensure causal writes go to the same partition.

### Q4: How does leader failover work, and what can go wrong?

Failover detects leader failure (via timeout), elects a follower as the new leader, and reconfigures clients and other followers. Problems: (1) **Data loss**: async replication means the new leader may be missing some writes. (2) **Split brain**: two nodes both believe they're leader, both accept writes → data corruption. (3) **Wrong timeout**: too short causes unnecessary failovers; too long means longer downtime. GitHub's 2012 incident showed how stale auto-increment counters after failover caused duplicate primary keys and data leaks.

### Q5: What are CRDTs and when are they useful?

**Conflict-free Replicated Data Types** are data structures designed to be merged automatically without conflicts. Examples: G-Counter (grow-only counter), PN-Counter (increment/decrement), G-Set (grow-only set), OR-Set (observed-remove set). They're useful in multi-leader and leaderless systems where concurrent writes to the same data are common. CRDTs guarantee eventual convergence regardless of the order in which updates are applied. Used by Riak for distributed counters and sets.

---

*Based on Chapter 5 of "Designing Data-Intensive Applications" by Martin Kleppmann*
