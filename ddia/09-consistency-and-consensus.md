# Chapter 9: Consistency and Consensus

## Table of Contents

1. [Consistency Guarantees](#consistency-guarantees)
2. [Linearizability](#linearizability)
3. [Ordering Guarantees](#ordering-guarantees)
4. [Distributed Transactions and Consensus](#distributed-transactions-and-consensus)
5. [Consensus Algorithms](#consensus-algorithms)
6. [Interview Questions](#interview-questions)

---

## Consistency Guarantees

Different databases offer different consistency guarantees, from weak (eventual consistency) to strong (linearizability).

```
┌──────────────────────────────────────────────────────────────────┐
│              CONSISTENCY SPECTRUM                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WEAK ◄──────────────────────────────────────────────── STRONG  │
│                                                                  │
│  Eventual        Causal         Sequential      Linearizable    │
│  Consistency     Consistency    Consistency      (Strongest)     │
│                                                                  │
│  "If you stop    "Causally      "All nodes      "Behaves as     │
│   writing, all    related        see ops in      if there's      │
│   replicas will   events seen    the SAME        only ONE copy   │
│   eventually      in correct     order"          of the data,    │
│   converge"       order"                         and all ops     │
│                                                   are atomic"    │
│                                                                  │
│  ✓ Best avail.  ✓ Good perf.   ✓ Predictable   ✗ Worst perf.  │
│  ✗ Confusing    ✓ No coord.                     ✗ Worst avail. │
│    for users      across DCs                    ✓ Easiest to   │
│                                                   reason about  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Linearizability

The strongest single-object consistency model. Also called **atomic consistency**, **strong consistency**, or **external consistency**.

### What Linearizability Means

```
┌──────────────────────────────────────────────────────────────────┐
│              LINEARIZABILITY DEFINITION                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  The system behaves AS IF there is only ONE copy of the data,   │
│  and EVERY operation takes effect atomically at some point       │
│  between its start and end.                                     │
│                                                                  │
│  Client A:  ──[  write(x=1)  ]──────────────────────────►      │
│  Client B:  ────────[  read(x)  ]───────────────────────►      │
│  Client C:  ──────────────────[  read(x)  ]─────────────►      │
│                                                                  │
│  Linearizable: Once ANY read returns x=1, ALL subsequent        │
│  reads must also return x=1 (or a later value).                 │
│                                                                  │
│  NOT linearizable:                                               │
│  Client B reads x=1, then Client C reads x=0 (old value)       │
│  → violates linearizability (went "back in time")              │
│                                                                  │
│  KEY PROPERTY: RECENCY GUARANTEE                                │
│  A read always returns the value of the most recently           │
│  completed write (or a concurrent write).                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### When is Linearizability Required?

```
┌──────────────────────────────────────────────────────────────────┐
│  USE CASES REQUIRING LINEARIZABILITY:                            │
│                                                                  │
│  1. LEADER ELECTION (e.g., ZooKeeper lock)                      │
│     All nodes must agree on who the leader is.                  │
│     If the lock is not linearizable, two nodes may both         │
│     believe they are the leader → split brain!                  │
│                                                                  │
│  2. UNIQUE CONSTRAINTS (usernames, file names)                  │
│     Two users registering the same username concurrently.        │
│     Must ensure exactly one succeeds.                           │
│     Requires an atomic compare-and-set.                         │
│                                                                  │
│  3. CROSS-CHANNEL COORDINATION                                   │
│     File storage + message queue: "I uploaded image,             │
│     now resize it." If message arrives before image is          │
│     visible → error. Linearizability prevents this.             │
│                                                                  │
│  4. BANK ACCOUNT BALANCE                                         │
│     After a debit, the balance must immediately reflect          │
│     the change to prevent overdrafts.                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### The CAP Theorem

```
┌──────────────────────────────────────────────────────────────────┐
│              CAP THEOREM (revisited)                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  During a NETWORK PARTITION, you must choose:                   │
│                                                                  │
│  CONSISTENT (Linearizable)        AVAILABLE                     │
│  ─────────────────────            ─────────                     │
│  Some replicas won't respond      All replicas respond          │
│  (they can't confirm they have    (but may return STALE data)   │
│  the latest data)                                                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Datacenter 1         Network        Datacenter 2       │     │
│  │ ┌────────┐          Partition       ┌────────┐         │     │
│  │ │Leader  │     ═══════╳═══════      │Follower│         │     │
│  │ │ x = 2  │                          │ x = 1  │         │     │
│  │ └────────┘                          └────────┘         │     │
│  │                                                        │     │
│  │ CP: Follower refuses reads (unavailable but consistent)│     │
│  │ AP: Follower serves x=1 (available but inconsistent)   │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  MORE PRECISELY: CAP is really about the trade-off between      │
│  linearizability and availability during network partitions.    │
│                                                                  │
│  CP systems: ZooKeeper, HBase, etcd, MongoDB (with majority)   │
│  AP systems: Cassandra, DynamoDB (eventual), CouchDB, Riak     │
│                                                                  │
│  When the network is working fine, you get BOTH C and A.        │
│  The choice only matters during partitions.                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Linearizability and Performance

```
┌──────────────────────────────────────────────────────────────────┐
│  Even WITHOUT network partitions, many systems choose NOT to    │
│  be linearizable — for PERFORMANCE reasons.                     │
│                                                                  │
│  Multi-leader replication: Not linearizable (by design).        │
│  Leaderless replication: Usually not linearizable               │
│    (even with quorums — due to sloppy quorums, read repair).   │
│                                                                  │
│  The performance penalty of linearizability:                    │
│  Every read must contact the leader or do a quorum read.        │
│  Cross-datacenter linearizable reads have high latency.         │
│                                                                  │
│  Many applications don't need linearizability and work          │
│  correctly with weaker guarantees (causal consistency).         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Ordering Guarantees

### Causal Consistency

```
┌──────────────────────────────────────────────────────────────────┐
│              CAUSAL CONSISTENCY                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CAUSALLY RELATED events must be seen in the correct order.     │
│  CONCURRENT events (no causal relationship) can be in any       │
│  order.                                                          │
│                                                                  │
│  Examples of causal dependencies:                                │
│  • Question before answer                                        │
│  • Create before update                                          │
│  • Insert before foreign key reference                           │
│                                                                  │
│  Causal consistency is WEAKER than linearizability:             │
│  • Linearizable: total order (all events ordered)               │
│  • Causal: partial order (only causally related events ordered) │
│                                                                  │
│  Causal consistency is the STRONGEST consistency model that     │
│  doesn't sacrifice availability (unlike linearizability).       │
│                                                                  │
│  Implementation: Track causal dependencies using VERSION        │
│  VECTORS or LAMPORT TIMESTAMPS.                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Total Order Broadcast

```
┌──────────────────────────────────────────────────────────────────┐
│              TOTAL ORDER BROADCAST                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A protocol for exchanging messages between nodes with           │
│  TWO guarantees:                                                 │
│                                                                  │
│  1. RELIABLE DELIVERY: If a message is delivered to one node,  │
│     it is delivered to ALL nodes (no message loss)              │
│                                                                  │
│  2. TOTALLY ORDERED: All nodes see messages in the SAME order  │
│                                                                  │
│  Node A sees: [msg1, msg2, msg3, msg4]                          │
│  Node B sees: [msg1, msg2, msg3, msg4]  ← Same order!         │
│  Node C sees: [msg1, msg2, msg3, msg4]  ← Same order!         │
│                                                                  │
│  If you have total order broadcast, you can build:              │
│  • Linearizable storage (use it as a write-ahead log)           │
│  • Database replication (each message = a write)                │
│  • Serializable transactions                                    │
│  • Lock services                                                 │
│  • Unique ID generation                                          │
│                                                                  │
│  EQUIVALENT to consensus: if you can solve total order          │
│  broadcast, you can solve consensus, and vice versa.            │
│                                                                  │
│  Implemented by: ZooKeeper (Zab), etcd (Raft), Kafka            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Distributed Transactions and Consensus

### Two-Phase Commit (2PC)

```
┌──────────────────────────────────────────────────────────────────┐
│              TWO-PHASE COMMIT (2PC)                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1: PREPARE                                                │
│  ┌──────────────┐                                                │
│  │ Coordinator  │──── "Can you commit?" ───► Node A  → "YES"   │
│  │              │──── "Can you commit?" ───► Node B  → "YES"   │
│  │              │──── "Can you commit?" ───► Node C  → "YES"   │
│  └──────┬───────┘                                                │
│         │  All said YES → proceed to Phase 2                    │
│         │  Any said NO  → abort all                              │
│         ▼                                                        │
│  PHASE 2: COMMIT (or ABORT)                                     │
│  ┌──────────────┐                                                │
│  │ Coordinator  │──── "COMMIT!" ───► Node A  → committed       │
│  │              │──── "COMMIT!" ───► Node B  → committed       │
│  │              │──── "COMMIT!" ───► Node C  → committed       │
│  └──────────────┘                                                │
│                                                                  │
│  KEY RULE: Once a participant votes "YES" in Phase 1,           │
│  it MUST commit if the coordinator says commit.                 │
│  It has surrendered the right to abort unilaterally.            │
│                                                                  │
│  The coordinator's COMMIT/ABORT decision is the                 │
│  "point of no return." It must write this decision              │
│  to its own WAL (transaction log) BEFORE sending               │
│  to participants.                                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### The Coordinator Failure Problem

```
┌──────────────────────────────────────────────────────────────────┐
│              COORDINATOR FAILURE — IN DOUBT                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  What if the coordinator crashes AFTER Phase 1 but              │
│  BEFORE sending Phase 2 messages?                               │
│                                                                  │
│  Participants voted "YES" and are now WAITING.                  │
│  They cannot commit (don't know if all voted yes).              │
│  They cannot abort (coordinator might have decided commit).     │
│  They are IN DOUBT / UNCERTAIN.                                 │
│                                                                  │
│  They MUST WAIT for the coordinator to recover.                 │
│  This can take minutes, hours, or even days!                    │
│                                                                  │
│  During this time, participants HOLD LOCKS on the               │
│  affected rows → other transactions are BLOCKED.               │
│                                                                  │
│  ┌──────────────┐                                                │
│  │ Coordinator  │  CRASHED!                                     │
│  │   (down)     │                                                │
│  └──────────────┘                                                │
│        ╱    ╲                                                    │
│       ╱      ╲                                                   │
│  ┌────────┐ ┌────────┐                                          │
│  │ Node A │ │ Node B │  Both: "I voted YES... now what?"       │
│  │WAITING │ │WAITING │  Can't commit, can't abort, can't       │
│  │(locks  │ │(locks  │  release locks. STUCK.                   │
│  │ held!) │ │ held!) │                                          │
│  └────────┘ └────────┘                                          │
│                                                                  │
│  This is a FUNDAMENTAL problem with 2PC — the coordinator      │
│  is a single point of failure that can block the whole system.  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Consensus Algorithms

Consensus means getting several nodes to **agree on something** (leader election, transaction commit, total order of events). The formal properties:

```
┌──────────────────────────────────────────────────────────────────┐
│              CONSENSUS PROPERTIES                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. UNIFORM AGREEMENT:  All nodes decide the same value         │
│  2. INTEGRITY:          No node decides twice                    │
│  3. VALIDITY:           The decided value was proposed by some  │
│                          node (not made up)                      │
│  4. TERMINATION:        Every non-crashed node eventually        │
│                          decides (liveness/progress)             │
│                                                                  │
│  FLP IMPOSSIBILITY THEOREM (1985):                              │
│  In an asynchronous system where nodes can crash,               │
│  it is IMPOSSIBLE to guarantee consensus will be reached.       │
│                                                                  │
│  Practical algorithms (Paxos, Raft, Zab) work around FLP       │
│  by using timeouts (assuming partial synchrony) — they may      │
│  not terminate during network partitions, but they NEVER        │
│  violate safety (agreement, integrity, validity).               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Raft Consensus Algorithm

```
┌──────────────────────────────────────────────────────────────────┐
│              RAFT CONSENSUS (simplified)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Three roles:                                                    │
│  • LEADER:    Handles all client requests, replicates log       │
│  • FOLLOWER:  Passive, replicates leader's log                  │
│  • CANDIDATE: Trying to become leader                           │
│                                                                  │
│  LEADER ELECTION:                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. Follower hasn't heard from leader (timeout)           │    │
│  │ 2. Becomes CANDIDATE, increments TERM, votes for itself  │    │
│  │ 3. Sends RequestVote to all other nodes                   │    │
│  │ 4. If majority votes YES → becomes LEADER                │    │
│  │ 5. If another leader discovered → steps down              │    │
│  │ 6. If election timeout → starts new election             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LOG REPLICATION:                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. Client sends write to LEADER                          │    │
│  │ 2. Leader appends to its log                              │    │
│  │ 3. Leader sends AppendEntries RPC to all followers       │    │
│  │ 4. Once MAJORITY have replicated → entry is COMMITTED   │    │
│  │ 5. Leader responds to client                              │    │
│  │ 6. Followers apply committed entries to state machine    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TERM: A logical clock period. Each term has at most            │
│  one leader. If a node sees a higher term → steps down.        │
│                                                                  │
│  Key invariant: If two logs contain an entry with the same     │
│  index and term, all preceding entries are identical.           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Comparison of Consensus Approaches

| Aspect | 2PC | Paxos | Raft | Zab (ZooKeeper) |
|--------|-----|-------|------|-----------------|
| **Type** | Distributed transaction | Consensus | Consensus | Total order broadcast |
| **Coordinator** | Single (SPOF) | No fixed leader | Elected leader | Elected leader |
| **Fault tolerance** | Blocks if coordinator fails | Tolerates f of 2f+1 failures | Tolerates f of 2f+1 | Tolerates f of 2f+1 |
| **Safety** | Always safe | Always safe | Always safe | Always safe |
| **Liveness** | Can block indefinitely | Eventually (partial sync) | Eventually (partial sync) | Eventually (partial sync) |
| **Complexity** | Simple | Very complex | Simpler than Paxos | Moderate |
| **Used by** | XA transactions | Google Chubby | etcd, CockroachDB | Apache ZooKeeper |

### What Consensus Gives You (via ZooKeeper)

```
┌──────────────────────────────────────────────────────────────────┐
│              ZOOKEEPER — CONSENSUS AS A SERVICE                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Instead of implementing Paxos/Raft yourself, use ZooKeeper:   │
│                                                                  │
│  1. LEADER ELECTION                                              │
│     Nodes compete for a ZooKeeper lock.                          │
│     Winner = leader. Others watch for leader failure.           │
│                                                                  │
│  2. DISTRIBUTED LOCKS                                            │
│     Acquire lock via ZooKeeper node (ephemeral znode).          │
│     Lock auto-released if holder crashes (session timeout).     │
│                                                                  │
│  3. SERVICE DISCOVERY                                            │
│     Services register in ZooKeeper.                              │
│     Clients watch for changes → notified when services          │
│     come/go.                                                    │
│                                                                  │
│  4. CONFIGURATION MANAGEMENT                                    │
│     Store config in ZooKeeper.                                   │
│     All nodes watch → notified on change → reload.             │
│                                                                  │
│  5. PARTITION ASSIGNMENT                                        │
│     Which node owns which partition (e.g., Kafka uses ZK       │
│     to track partition→broker mapping).                         │
│                                                                  │
│  Alternatives to ZooKeeper: etcd (Raft), Consul (Raft)         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: What is linearizability and how is it different from serializability?

**Linearizability** is a recency guarantee on a single object: all operations appear to take effect atomically at some point between their invocation and response, and once a read returns a value, all subsequent reads return that value or a later one. **Serializability** is an isolation property of transactions: transactions appear to execute in some serial order. They are different dimensions — linearizability is about single-object recency; serializability is about multi-object transaction ordering. A system can be serializable but not linearizable (e.g., snapshot isolation), or linearizable but not serializable. "Strict serializability" provides both.

### Q2: Explain the CAP theorem.

The CAP theorem states that during a **network partition**, a distributed system must choose between **Consistency** (linearizability) and **Availability**. A CP system returns errors or timeouts from partitioned replicas rather than serve stale data. An AP system responds from all replicas even if they have stale data. When the network is healthy, you can have both. CAP is often misunderstood — it's specifically about linearizability during partitions, not a general "pick two of three" choice.

### Q3: What is two-phase commit and what is its main weakness?

2PC coordinates a distributed transaction across multiple nodes. In Phase 1 (Prepare), the coordinator asks each participant "can you commit?" In Phase 2 (Commit), if all said yes, the coordinator tells everyone to commit; if any said no, abort. The **main weakness**: if the coordinator crashes between Phase 1 and Phase 2, participants that voted YES are stuck in an "in doubt" state — they can't commit or abort unilaterally and must hold locks until the coordinator recovers. This can block the system for an unbounded time.

### Q4: Compare Paxos and Raft.

Both are consensus algorithms tolerating f failures among 2f+1 nodes. **Paxos** (Lamport, 1998) is the foundational algorithm — mathematically elegant but notoriously difficult to understand and implement correctly. It separates leader election and log replication, making it flexible but complex. **Raft** (Ongaro & Ousterhout, 2014) was designed specifically for understandability — it bundles leader election, log replication, and safety into a single coherent protocol with strong leader semantics. Raft is more widely implemented in practice (etcd, CockroachDB).

### Q5: What is total order broadcast and why is it equivalent to consensus?

Total order broadcast guarantees that all nodes deliver the same messages in the same order, reliably. It's equivalent to consensus because: (1) if you have consensus, you can implement total order broadcast (use consensus to agree on the next message to deliver), and (2) if you have total order broadcast, you can implement consensus (broadcast a proposal, first one delivered wins). This equivalence means solutions to one problem directly solve the other.

### Q6: Why can't consensus be guaranteed in an asynchronous system?

The **FLP impossibility theorem** (Fischer, Lynch, Paterson, 1985) proves that in a purely asynchronous system where even one node can crash, no deterministic consensus algorithm can guarantee termination. This is because you can't distinguish a crashed node from a slow one without timeouts. Practical algorithms like Raft and Paxos work around this by assuming partial synchrony — they use timeouts and may fail to make progress during network issues, but they **never** violate safety (they won't make contradictory decisions).

---

*Based on Chapter 9 of "Designing Data-Intensive Applications" by Martin Kleppmann*
