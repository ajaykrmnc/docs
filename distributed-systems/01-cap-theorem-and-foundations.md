# CAP Theorem and Distributed Systems Foundations

## Table of Contents
1. [Introduction to Distributed Systems](#introduction-to-distributed-systems)
2. [CAP Theorem Deep Dive](#cap-theorem-deep-dive)
3. [PACELC Theorem](#pacelc-theorem)
4. [Consistency Models](#consistency-models)
5. [Real-World Trade-offs](#real-world-trade-offs)
6. [Interview Questions](#interview-questions)

---

## Introduction to Distributed Systems

### What is a Distributed System?

A **distributed system** is a collection of independent computers that appears to its users as a single coherent system. These computers communicate and coordinate their actions by passing messages over a network.

### Key Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ Node A  │◄──►│ Node B  │◄──►│ Node C  │◄──►│ Node D  │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│       ▲              ▲              ▲              ▲           │
│       │              │              │              │           │
│       └──────────────┴──────────────┴──────────────┘           │
│                    Network Communication                        │
└─────────────────────────────────────────────────────────────────┘
```

### Fundamental Characteristics

| Characteristic | Description |
|---------------|-------------|
| **Concurrency** | Multiple components execute simultaneously |
| **No Global Clock** | No single global notion of time |
| **Independent Failures** | Components can fail independently |
| **Heterogeneity** | Different hardware, OS, networks |
| **Scalability** | System can grow to accommodate load |
| **Transparency** | Hide complexity from users |

### Why Distributed Systems?

1. **Scalability**: Handle more load by adding machines
2. **Reliability**: No single point of failure
3. **Performance**: Parallel processing and geographic distribution
4. **Cost**: Commodity hardware vs. expensive mainframes
5. **Geographic Distribution**: Serve users globally with low latency

### The Eight Fallacies of Distributed Computing

These are false assumptions programmers new to distributed systems often make:

```
┌────────────────────────────────────────────────────────────────┐
│              FALLACIES OF DISTRIBUTED COMPUTING                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. The network is reliable          ──► Packets get lost     │
│  2. Latency is zero                  ──► Network has delay    │
│  3. Bandwidth is infinite            ──► Limited throughput   │
│  4. The network is secure            ──► Security threats     │
│  5. Topology doesn't change          ──► Nodes join/leave     │
│  6. There is one administrator       ──► Multiple admins      │
│  7. Transport cost is zero           ──► Data transfer costs  │
│  8. The network is homogeneous       ──► Different networks   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## CAP Theorem Deep Dive

### What is CAP Theorem?

The **CAP Theorem**, proposed by Eric Brewer in 2000 and proven by Seth Gilbert and Nancy Lynch in 2002, states that a distributed data store can only provide **two out of three** guarantees simultaneously:

- **C**onsistency
- **A**vailability
- **P**artition Tolerance

### The Three Properties Explained

```
                         CONSISTENCY (C)
                              ▲
                             /│\
                            / │ \
                           /  │  \
                          /   │   \
                         /    │    \
                        /     │     \
                       /      │      \
                      /   CP  │  CA   \
                     /  Systems│Systems \
                    /         │         \
                   ▼──────────┴──────────▼
        PARTITION                    AVAILABILITY (A)
        TOLERANCE (P)
                         AP Systems
```

#### Consistency (C)

**Definition**: Every read receives the most recent write or an error.

All nodes see the same data at the same time. When a write is acknowledged, all subsequent reads must return that value.

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRONG CONSISTENCY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client writes X=5 to Node A                                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────┐    Sync    ┌─────────┐    Sync    ┌─────────┐    │
│  │ Node A  │───────────►│ Node B  │───────────►│ Node C  │    │
│  │  X=5    │            │  X=5    │            │  X=5    │    │
│  └─────────┘            └─────────┘            └─────────┘    │
│                                                                 │
│  ANY read from ANY node returns X=5                            │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Challenges**:
- Requires coordination between all nodes
- Increases latency (must wait for acknowledgments)
- Reduces availability during network partitions

#### Availability (A)

**Definition**: Every request receives a (non-error) response, without guarantee that it contains the most recent write.

The system remains operational 100% of the time. Every request gets a response, regardless of the state of any individual node.

```
┌─────────────────────────────────────────────────────────────────┐
│                    HIGH AVAILABILITY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                  │
│  │ Node A  │     │ Node B  │     │ Node C  │                  │
│  │  (UP)   │     │ (DOWN)  │     │  (UP)   │                  │
│  └────┬────┘     └─────────┘     └────┬────┘                  │
│       │                               │                        │
│       ▼                               ▼                        │
│  Still accepts              Still accepts                      │
│  requests!                  requests!                          │
│                                                                 │
│  System remains available even with node failures              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points**:
- No request should wait indefinitely
- System always provides a response
- May return stale data during partitions

#### Partition Tolerance (P)

**Definition**: The system continues to operate despite network partitions (messages being dropped or delayed between nodes).

```
┌─────────────────────────────────────────────────────────────────┐
│                    NETWORK PARTITION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐                          ┌─────────┐              │
│  │ Node A  │          XXXXXX          │ Node B  │              │
│  │         │◄────────X BREAK X───────►│         │              │
│  └─────────┘          XXXXXX          └─────────┘              │
│       │                                    │                    │
│       │    Network                         │                    │
│       │    Partition                       │                    │
│       ▼                                    ▼                    │
│  ┌─────────┐                          ┌─────────┐              │
│  │ Node C  │                          │ Node D  │              │
│  └─────────┘                          └─────────┘              │
│                                                                 │
│  Partition 1: A, C          Partition 2: B, D                  │
└─────────────────────────────────────────────────────────────────┘
```

**Reality**: In any distributed system, network partitions WILL happen. Therefore, **P is not optional** - you must choose between C and A during a partition.

### The CAP Trade-off in Practice

Since partitions are inevitable in distributed systems, the real choice is between:
- **CP (Consistency + Partition Tolerance)**: Sacrifice availability
- **AP (Availability + Partition Tolerance)**: Sacrifice consistency

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAP SYSTEM CLASSIFICATION                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐           │
│  │    CP SYSTEMS       │    │    AP SYSTEMS       │           │
│  ├─────────────────────┤    ├─────────────────────┤           │
│  │ • MongoDB           │    │ • Cassandra         │           │
│  │ • HBase             │    │ • DynamoDB          │           │
│  │ • Redis (cluster)   │    │ • CouchDB           │           │
│  │ • Zookeeper         │    │ • Riak              │           │
│  │ • etcd              │    │ • Voldemort         │           │
│  │ • Consul            │    │                     │           │
│  ├─────────────────────┤    ├─────────────────────┤           │
│  │ During partition:   │    │ During partition:   │           │
│  │ - Reject writes     │    │ - Accept writes     │           │
│  │ - Return errors     │    │ - May return stale  │           │
│  │ - Wait for recovery │    │ - Resolve conflicts │           │
│  └─────────────────────┘    └─────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What About CA Systems?

**CA (Consistency + Availability)** systems can only exist when there are no network partitions - essentially single-node systems or systems on a perfectly reliable network.

Examples of "CA" systems (single-node or pre-partition):
- Traditional RDBMS (PostgreSQL, MySQL on single node)
- Single-node Redis

**Important**: Once you distribute data across multiple nodes, you MUST handle partitions.


---

## PACELC Theorem

### Beyond CAP: The PACELC Extension

PACELC extends CAP by addressing what happens when there is NO partition:

**P**artition → **A**vailability vs **C**onsistency
**E**lse → **L**atency vs **C**onsistency

```
┌─────────────────────────────────────────────────────────────────┐
│                    PACELC THEOREM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IF (Network Partition)                                        │
│  │                                                              │
│  ├── Choose: Availability (A) OR Consistency (C)               │
│  │                                                              │
│  ELSE (Normal Operation)                                       │
│  │                                                              │
│  └── Choose: Latency (L) OR Consistency (C)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### PACELC Classifications

| System | Partition (P) | Else (E) | Classification |
|--------|--------------|----------|----------------|
| DynamoDB | A | L | PA/EL |
| Cassandra | A | L | PA/EL |
| Riak | A | L | PA/EL |
| MongoDB | C | C | PC/EC |
| HBase | C | C | PC/EC |
| PostgreSQL | C | C | PC/EC |
| PNUTS | C | L | PC/EL |
| VoltDB | C | C | PC/EC |

### Why PACELC Matters

```
┌─────────────────────────────────────────────────────────────────┐
│                    LATENCY vs CONSISTENCY                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Write Request                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────┐                                                   │
│  │ Primary │                                                   │
│  └────┬────┘                                                   │
│       │                                                         │
│  ┌────┴────────────────────────┐                               │
│  │                             │                                │
│  ▼                             ▼                                │
│  LOW LATENCY                   HIGH CONSISTENCY                 │
│  (Async Replication)          (Sync Replication)               │
│                                                                 │
│  • Return immediately          • Wait for replicas             │
│  • May lose data               • Guaranteed durability         │
│  • Higher throughput           • Lower throughput              │
│  • Risk of stale reads         • Always current data           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Consistency Models

### Spectrum of Consistency

```
STRONGER ◄────────────────────────────────────────────► WEAKER

┌──────────────┬──────────────┬──────────────┬──────────────┐
│   STRICT     │  SEQUENTIAL  │   CAUSAL     │  EVENTUAL    │
│ CONSISTENCY  │ CONSISTENCY  │ CONSISTENCY  │ CONSISTENCY  │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ All ops in   │ All ops in   │ Causally     │ Eventually   │
│ real-time    │ some total   │ related ops  │ all replicas │
│ order        │ order        │ ordered      │ converge     │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ Impossible   │ Linearizable │ Good for     │ Highly       │
│ in practice  │ systems      │ social apps  │ available    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 1. Strong/Linearizable Consistency

The strongest practical consistency model. Operations appear to execute atomically at some point between invocation and response.

```
┌─────────────────────────────────────────────────────────────────┐
│                LINEARIZABLE CONSISTENCY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Time ─────────────────────────────────────────────────►       │
│                                                                 │
│  Client A:  ───[Write X=1]───────────────────────────          │
│                      │                                          │
│                      ▼ (linearization point)                   │
│  Client B:  ──────────────[Read X]─── returns 1                │
│                                                                 │
│  After write completes, ALL reads see the new value            │
└─────────────────────────────────────────────────────────────────┘
```

**Properties**:
- Total order of operations
- Real-time ordering preserved
- Read always returns most recent write

**Use Cases**: Bank transactions, inventory systems, leader election

### 2. Sequential Consistency

Operations from all processes executed in some sequential order, respecting program order within each process.

```
┌─────────────────────────────────────────────────────────────────┐
│                SEQUENTIAL CONSISTENCY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Process P1:  Write(X, 1) ──► Write(X, 2)                      │
│  Process P2:  Read(X) ──► Read(X)                              │
│                                                                 │
│  Valid Execution:                                               │
│  • P2 reads: 1, 2  ✓                                           │
│  • P2 reads: 1, 1  ✓ (both reads before Write(X,2))           │
│  • P2 reads: 2, 1  ✗ (violates P1's program order)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Causal Consistency

Operations that are causally related must be seen in the same order by all nodes.

```
┌─────────────────────────────────────────────────────────────────┐
│                  CAUSAL CONSISTENCY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Alice posts: "Hello!"           (Event A)                     │
│       │                                                         │
│       ▼ (causes)                                               │
│  Bob replies: "Hi Alice!"        (Event B)                     │
│                                                                 │
│  ALL nodes must see A before B (causally related)              │
│                                                                 │
│  Carol posts: "Nice weather!"    (Event C - concurrent)        │
│                                                                 │
│  C can appear before or after A and B (not causally related)  │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**: Vector clocks, version vectors

### 4. Eventual Consistency

If no new updates are made, all replicas will eventually converge to the same value.

```
┌─────────────────────────────────────────────────────────────────┐
│                EVENTUAL CONSISTENCY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Time ─────────────────────────────────────────────────►       │
│                                                                 │
│  Node A:  X=1 ───────────────────────────────► X=3             │
│  Node B:  X=1 ─────────► X=2 ────────────────► X=3             │
│  Node C:  X=1 ─────────────────────► X=2 ────► X=3             │
│                                                                 │
│           │                           │        │                │
│           │    Inconsistency Window   │        │                │
│           ◄───────────────────────────►        │                │
│                                                 │                │
│                                      Eventually consistent     │
└─────────────────────────────────────────────────────────────────┘
```

**Variants**:
- **Read-your-writes**: Client always sees its own writes
- **Monotonic reads**: Once a value is seen, older values won't be returned
- **Monotonic writes**: Writes from a client are applied in order

---

## Real-World Trade-offs

### Choosing the Right Consistency Model

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSISTENCY MODEL DECISION TREE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Is data loss/inconsistency catastrophic?                      │
│       │                                                         │
│       ├── YES ──► Strong Consistency (CP)                      │
│       │           Examples: Banking, Inventory                 │
│       │                                                         │
│       └── NO ──► Can you tolerate stale reads?                 │
│                       │                                         │
│                       ├── YES ──► Eventual Consistency (AP)    │
│                       │           Examples: Social media feeds │
│                       │                                         │
│                       └── SOMETIMES ──► Causal Consistency     │
│                                         Examples: Comments     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```


### Real System Examples

| System | CAP Choice | Consistency Model | Use Case |
|--------|------------|-------------------|----------|
| **Google Spanner** | CP | External consistency | Global transactions |
| **Amazon DynamoDB** | AP | Eventual (configurable) | Shopping carts |
| **Apache Cassandra** | AP | Tunable consistency | Time-series data |
| **MongoDB** | CP | Strong (by default) | Document storage |
| **Redis Cluster** | CP | Strong | Caching, sessions |
| **CockroachDB** | CP | Serializable | OLTP workloads |
| **Apache Kafka** | CP | Strong ordering | Event streaming |
| **Amazon S3** | AP | Eventual | Object storage |

---

## Interview Questions

### Conceptual Questions

**Q1: Can you build a system that is both consistent and available during a partition?**

No. The CAP theorem proves this is impossible. During a network partition:
- If you choose consistency, you must reject some requests (sacrifice availability)
- If you choose availability, different partitions may accept conflicting writes (sacrifice consistency)

**Q2: Why is partition tolerance not optional?**

In any distributed system, network partitions WILL happen due to:
- Network failures
- Hardware issues
- Software bugs
- Data center problems

You cannot "prevent" partitions in production, so you must design for them.

**Q3: What's the difference between strong consistency and eventual consistency?**

| Aspect | Strong Consistency | Eventual Consistency |
|--------|-------------------|---------------------|
| Read guarantee | Always latest write | May return stale data |
| Latency | Higher (coordination) | Lower (no waiting) |
| Availability | Lower during partitions | Higher |
| Use cases | Financial, inventory | Social media, DNS |

**Q4: How does a system like DynamoDB provide "tunable consistency"?**

DynamoDB allows per-request consistency settings:
- **Eventually consistent reads**: Lower latency, may return stale data
- **Strongly consistent reads**: Higher latency, returns latest data

This is possible because the consistency is tunable per-operation, not a system-wide setting.

### Design Questions

**Q5: Design a shopping cart system. Which consistency model would you choose?**

**Answer**: Eventually consistent (AP system)

**Reasoning**:
- High availability is crucial (lost sales = lost revenue)
- Temporary inconsistency is acceptable (items may briefly appear/disappear)
- Conflicts can be resolved by merging carts
- Users typically operate on their own cart (low conflict rate)

```
Cart Merge Strategy:
Cart A: {item1, item2}
Cart B: {item1, item3}
Merged: {item1, item2, item3}  (union of all items)
```

**Q6: Design a banking system. Which consistency model would you choose?**

**Answer**: Strong consistency (CP system)

**Reasoning**:
- Correctness is paramount (can't lose money)
- Double-spending must be prevented
- Regulatory requirements demand accuracy
- Users expect transactions to be immediately visible

```
Account Balance Transfer:
1. Lock both accounts
2. Debit source account
3. Credit destination account
4. Release locks
5. Return success only after all replicas confirm
```

---

## Summary

### Key Takeaways

1. **CAP Theorem**: In a distributed system, you can only guarantee 2 of 3: Consistency, Availability, Partition Tolerance

2. **Partition tolerance is mandatory**: Networks WILL fail; the real choice is between C and A

3. **PACELC extends CAP**: Even without partitions, you must choose between latency and consistency

4. **Consistency is a spectrum**: From strong (expensive) to eventual (cheap)

5. **Choose based on requirements**:
   - Financial/critical: Strong consistency
   - Social/non-critical: Eventual consistency
   - Mixed: Tunable/causal consistency

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│              DISTRIBUTED SYSTEMS CHEAT SHEET                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Need strong consistency? ──► CP systems (MongoDB, HBase)      │
│  Need high availability?  ──► AP systems (Cassandra, DynamoDB) │
│  Need both?               ──► Impossible! Make trade-offs      │
│                                                                 │
│  Consistency Models (Strong → Weak):                           │
│  Linearizable → Sequential → Causal → Eventual                 │
│                                                                 │
│  Remember:                                                      │
│  • Partitions are inevitable                                   │
│  • Trade-offs are unavoidable                                  │
│  • Choose based on business requirements                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
