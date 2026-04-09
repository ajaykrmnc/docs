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

## Conflict Resolution Strategies

### The Problem: Conflicting Writes During Partitions

When a network partition occurs in an AP (Available + Partition Tolerant) system, different partitions can accept conflicting writes for the same data. When the partition heals, the system must resolve these conflicts.

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONFLICT SCENARIO                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Time: T0                Network Partition Occurs               │
│                                                                 │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │  Partition 1    │    XXXXXX    │  Partition 2    │          │
│  │                 │    XXXXXX    │                 │          │
│  │  Node A, Node B │              │  Node C, Node D │          │
│  └────────┬────────┘              └────────┬────────┘          │
│           │                                │                    │
│  Time: T1 │                                │                    │
│           ▼                                ▼                    │
│    Client writes X=5                Client writes X=7          │
│    (accepted by A,B)                (accepted by C,D)          │
│                                                                 │
│  Time: T2                Partition Heals                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │  CONFLICT: Which value should X have?            │          │
│  │  • Node A,B think X=5                            │          │
│  │  • Node C,D think X=7                            │          │
│  │  • Need conflict resolution strategy!           │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Strategy 1: Last Write Wins (LWW)

**Concept**: Use timestamps to determine which write is "newer" and discard older writes.

```
┌─────────────────────────────────────────────────────────────────┐
│                  LAST WRITE WINS (LWW)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Partition 1:                    Partition 2:                  │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │ Write X=5       │              │ Write X=7       │          │
│  │ Timestamp: 100  │              │ Timestamp: 105  │          │
│  └─────────────────┘              └─────────────────┘          │
│                                                                 │
│  After Partition Heals:                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Compare timestamps: 105 > 100                    │          │
│  │ Winner: X=7 (timestamp 105)                      │          │
│  │ Result: X=5 is DISCARDED                         │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
class LWWRegister:
    def __init__(self):
        self.value = None
        self.timestamp = 0

    def write(self, value, timestamp):
        if timestamp > self.timestamp:
            self.value = value
            self.timestamp = timestamp
            return True
        return False  # Reject older writes

    def merge(self, other_value, other_timestamp):
        """Merge with replica during partition healing"""
        if other_timestamp > self.timestamp:
            self.value = other_value
            self.timestamp = other_timestamp
```

**Pros**:
- Simple to implement
- Deterministic (all nodes converge to same value)
- Low overhead

**Cons**:
- **Data loss**: Earlier write is completely discarded
- **Clock synchronization**: Requires synchronized clocks (problematic in distributed systems)
- **Concurrent writes**: If timestamps are equal, need tie-breaker (e.g., node ID)

**Use Cases**:
- User profile updates (last update wins)
- Configuration settings
- Cache invalidation

**Real-World Example**: Cassandra (default), Riak with `allow_mult=false`

---

### Strategy 2: Version Vectors / Vector Clocks

**Concept**: Track causality between writes to detect concurrent (conflicting) updates vs. sequential updates.

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR CLOCKS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Initial State:                                                 │
│  Value: X=0, Vector: {A:0, B:0, C:0}                           │
│                                                                 │
│  Step 1: Node A writes X=5                                     │
│  Value: X=5, Vector: {A:1, B:0, C:0}                           │
│                                                                 │
│  Step 2: Partition occurs                                      │
│                                                                 │
│  Partition 1 (Node A):        Partition 2 (Node C):            │
│  Writes X=10                  Writes X=20                       │
│  Vector: {A:2, B:0, C:0}      Vector: {A:1, B:0, C:1}          │
│                                                                 │
│  Step 3: Partition heals - Detect conflict!                    │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Compare vectors:                                 │          │
│  │ {A:2, B:0, C:0} vs {A:1, B:0, C:1}              │          │
│  │                                                  │          │
│  │ Neither vector dominates the other:             │          │
│  │ • A:2 > A:1 (left wins on A)                    │          │
│  │ • C:1 > C:0 (right wins on C)                   │          │
│  │                                                  │          │
│  │ Result: CONCURRENT CONFLICT detected!           │          │
│  │ Both values must be kept: {X=10, X=20}          │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
class VectorClock:
    def __init__(self, node_id):
        self.node_id = node_id
        self.clock = {}  # {node_id: counter}

    def increment(self):
        """Increment this node's counter"""
        self.clock[self.node_id] = self.clock.get(self.node_id, 0) + 1

    def update(self, other_clock):
        """Update with received vector clock"""
        for node, count in other_clock.items():
            self.clock[node] = max(self.clock.get(node, 0), count)
        self.increment()

    def compare(self, other):
        """Compare two vector clocks"""
        # Check if self dominates other (self is newer)
        self_dominates = False
        other_dominates = False

        all_nodes = set(self.clock.keys()) | set(other.keys())

        for node in all_nodes:
            self_count = self.clock.get(node, 0)
            other_count = other.get(node, 0)

            if self_count > other_count:
                self_dominates = True
            elif other_count > self_count:
                other_dominates = True

        if self_dominates and not other_dominates:
            return "AFTER"  # self is newer
        elif other_dominates and not self_dominates:
            return "BEFORE"  # other is newer
        elif not self_dominates and not other_dominates:
            return "EQUAL"  # identical
        else:
            return "CONCURRENT"  # conflict!

class VersionedValue:
    def __init__(self, value, vector_clock):
        self.value = value
        self.vector_clock = vector_clock

    def merge(self, other):
        """Merge two versioned values"""
        comparison = self.vector_clock.compare(other.vector_clock)

        if comparison == "AFTER":
            return [self]  # Keep only self
        elif comparison == "BEFORE":
            return [other]  # Keep only other
        elif comparison == "EQUAL":
            return [self]  # Same version
        else:  # CONCURRENT
            return [self, other]  # Keep both - conflict!
```

**Pros**:
- Accurately detects causality
- No clock synchronization needed
- Can distinguish concurrent vs. sequential writes

**Cons**:
- Vector size grows with number of nodes
- More complex to implement
- Still need application-level resolution for conflicts

**Use Cases**:
- Distributed databases (Riak, Voldemort)
- Collaborative editing
- Shopping carts

**Real-World Example**: Riak with `allow_mult=true`, Amazon Dynamo

---

### Strategy 3: CRDTs (Conflict-free Replicated Data Types)

**Concept**: Use special data structures that are mathematically designed to merge automatically without conflicts.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRDT EXAMPLES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. G-Counter (Grow-only Counter)                              │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Partition 1:  {A:5, B:3, C:0} = Total: 8        │          │
│  │ Partition 2:  {A:5, B:3, C:2} = Total: 10       │          │
│  │                                                  │          │
│  │ Merge: Take MAX of each node's count            │          │
│  │ Result: {A:5, B:3, C:2} = Total: 10             │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  2. PN-Counter (Positive-Negative Counter)                     │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Partition 1: +{A:10, B:5} -{A:2, B:1} = 12      │          │
│  │ Partition 2: +{A:10, B:7} -{A:3, B:1} = 13      │          │
│  │                                                  │          │
│  │ Merge: MAX each component independently         │          │
│  │ Result: +{A:10, B:7} -{A:3, B:1} = 13           │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  3. OR-Set (Observed-Remove Set)                               │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Partition 1: Add "apple", Remove "banana"        │          │
│  │ Partition 2: Add "banana", Add "cherry"          │          │
│  │                                                  │          │
│  │ Merge: Union of adds, remove only if observed   │          │
│  │ Result: {"apple", "banana", "cherry"}            │          │
│  │ (banana re-added wins over remove)               │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Examples**:

```python
# G-Counter (Grow-only Counter)
class GCounter:
    def __init__(self, node_id):
        self.node_id = node_id
        self.counts = {}  # {node_id: count}

    def increment(self, amount=1):
        """Increment counter on this node"""
        self.counts[self.node_id] = self.counts.get(self.node_id, 0) + amount

    def value(self):
        """Get total count"""
        return sum(self.counts.values())

    def merge(self, other):
        """Merge with another G-Counter (conflict-free!)"""
        all_nodes = set(self.counts.keys()) | set(other.counts.keys())
        for node in all_nodes:
            self.counts[node] = max(
                self.counts.get(node, 0),
                other.counts.get(node, 0)
            )

# PN-Counter (Increment and Decrement)
class PNCounter:
    def __init__(self, node_id):
        self.node_id = node_id
        self.increments = GCounter(node_id)
        self.decrements = GCounter(node_id)

    def increment(self, amount=1):
        self.increments.increment(amount)

    def decrement(self, amount=1):
        self.decrements.increment(amount)

    def value(self):
        return self.increments.value() - self.decrements.value()

    def merge(self, other):
        self.increments.merge(other.increments)
        self.decrements.merge(other.decrements)

# LWW-Element-Set (Last-Write-Wins Set)
class LWWSet:
    def __init__(self):
        self.add_set = {}  # {element: timestamp}
        self.remove_set = {}  # {element: timestamp}

    def add(self, element, timestamp):
        self.add_set[element] = max(
            self.add_set.get(element, 0),
            timestamp
        )

    def remove(self, element, timestamp):
        self.remove_set[element] = max(
            self.remove_set.get(element, 0),
            timestamp
        )

    def contains(self, element):
        add_time = self.add_set.get(element, 0)
        remove_time = self.remove_set.get(element, 0)
        return add_time > remove_time  # Add wins on tie

    def elements(self):
        return {e for e in self.add_set if self.contains(e)}

    def merge(self, other):
        # Merge add sets
        for element, timestamp in other.add_set.items():
            self.add_set[element] = max(
                self.add_set.get(element, 0),
                timestamp
            )
        # Merge remove sets
        for element, timestamp in other.remove_set.items():
            self.remove_set[element] = max(
                self.remove_set.get(element, 0),
                timestamp
            )
```

**CRDT Types**:

| CRDT Type | Operations | Use Case |
|-----------|-----------|----------|
| **G-Counter** | Increment only | Page views, likes |
| **PN-Counter** | Increment, Decrement | Inventory, votes |
| **G-Set** | Add only | Append-only logs |
| **2P-Set** | Add, Remove (once) | Membership lists |
| **LWW-Set** | Add, Remove (LWW) | Shopping cart items |
| **OR-Set** | Add, Remove (observed) | Collaborative editing |
| **LWW-Register** | Set value (LWW) | User preferences |

**Pros**:
- **Automatic conflict resolution** - no application logic needed
- Mathematically proven to converge
- No coordination required
- Works well for AP systems

**Cons**:
- Limited to specific data types
- Can have higher memory overhead
- Some operations not supported (e.g., decrement below zero for G-Counter)
- Complexity in implementation

**Use Cases**:
- Collaborative applications (Google Docs, Figma)
- Distributed counters (analytics)
- Shopping carts
- Presence systems

**Real-World Examples**: Redis Enterprise, Riak, Akka Distributed Data, SoundCloud's Roshi

---

### Strategy 4: Application-Level Conflict Resolution

**Concept**: Return all conflicting versions to the application and let business logic decide how to merge.

```
┌─────────────────────────────────────────────────────────────────┐
│            APPLICATION-LEVEL RESOLUTION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Example: Shopping Cart Conflict                               │
│                                                                 │
│  Partition 1:                    Partition 2:                  │
│  Cart = ["Book", "Pen"]          Cart = ["Book", "Laptop"]     │
│                                                                 │
│  After Partition Heals:                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Database returns BOTH versions:                  │          │
│  │ Version 1: ["Book", "Pen"]                       │          │
│  │ Version 2: ["Book", "Laptop"]                    │          │
│  └──────────────────────────────────────────────────┘          │
│                    │                                            │
│                    ▼                                            │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Application Merge Logic:                         │          │
│  │ • Take UNION of all items                        │          │
│  │ • Remove duplicates                              │          │
│  │ • Result: ["Book", "Pen", "Laptop"]              │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:

```python
class ShoppingCart:
    def __init__(self, items=None, version_vector=None):
        self.items = items or []
        self.version_vector = version_vector or {}

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)

    @staticmethod
    def resolve_conflicts(carts):
        """
        Application-specific merge logic for shopping carts
        Strategy: Union of all items (add-wins semantics)
        """
        all_items = []
        for cart in carts:
            all_items.extend(cart.items)

        # Remove duplicates while preserving order
        seen = set()
        merged_items = []
        for item in all_items:
            if item not in seen:
                seen.add(item)
                merged_items.append(item)

        return ShoppingCart(items=merged_items)

# Example usage
cart1 = ShoppingCart(items=["Book", "Pen"])
cart2 = ShoppingCart(items=["Book", "Laptop"])

# Conflict detected - resolve at application level
merged_cart = ShoppingCart.resolve_conflicts([cart1, cart2])
print(merged_cart.items)  # ["Book", "Pen", "Laptop"]
```

**Common Merge Strategies**:

```python
# Strategy 1: Union (Add-wins)
def merge_union(values):
    """Combine all unique values"""
    return list(set().union(*[set(v) for v in values]))

# Strategy 2: Intersection (Conservative)
def merge_intersection(values):
    """Keep only common values"""
    return list(set.intersection(*[set(v) for v in values]))

# Strategy 3: Custom Business Logic
def merge_user_profile(profiles):
    """Merge user profiles with field-specific logic"""
    merged = {}

    # Email: Take most recent
    merged['email'] = max(profiles, key=lambda p: p['updated_at'])['email']

    # Friends: Union of all friends
    all_friends = set()
    for p in profiles:
        all_friends.update(p.get('friends', []))
    merged['friends'] = list(all_friends)

    # Settings: Prefer non-default values
    merged['settings'] = {}
    for p in profiles:
        for key, value in p.get('settings', {}).items():
            if value != 'default':
                merged['settings'][key] = value

    return merged

# Strategy 4: Prompt User
def merge_with_user_input(values):
    """Let user choose which version to keep"""
    print("Conflict detected! Choose a version:")
    for i, value in enumerate(values):
        print(f"{i+1}. {value}")
    choice = int(input("Enter choice: ")) - 1
    return values[choice]
```

**Pros**:
- Maximum flexibility
- Business logic can be arbitrarily complex
- Can involve user input when needed
- Domain-specific optimizations

**Cons**:
- Requires application code changes
- More complex client logic
- May need user intervention
- Harder to test

**Use Cases**:
- Shopping carts (Amazon)
- Document editing (Google Docs)
- Calendar events
- User profiles

**Real-World Example**: Amazon's Dynamo shopping cart, Riak with sibling resolution

---

### Strategy 5: Quorum-Based Resolution

**Concept**: Use read and write quorums to ensure overlap and detect conflicts early.

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUORUM CONSENSUS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Configuration: N=5 replicas, W=3 (write quorum), R=3 (read)  │
│                                                                 │
│  Write Operation:                                               │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client writes X=10                               │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ ┌────┴────┬────────┬────────┬────────┬────────┐ │          │
│  │ │ Node 1  │ Node 2 │ Node 3 │ Node 4 │ Node 5 │ │          │
│  │ │  X=10✓  │  X=10✓ │  X=10✓ │  X=5   │  X=5   │ │          │
│  │ └─────────┴────────┴────────┴────────┴────────┘ │          │
│  │                                                  │          │
│  │ W=3 nodes acknowledged → Write succeeds         │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  Read Operation:                                                │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client reads X                                   │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ Read from R=3 nodes:                             │          │
│  │ • Node 1: X=10 (version 2)                       │          │
│  │ • Node 2: X=10 (version 2)                       │          │
│  │ • Node 3: X=5  (version 1) ← Stale!              │          │
│  │                                                  │          │
│  │ Return: X=10 (majority/latest version)          │          │
│  │ Trigger: Read Repair on Node 3                  │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Quorum Rules**:

```
R + W > N  →  Strong Consistency
(Read and Write quorums overlap, guaranteeing latest value)

Examples with N=5:
• R=3, W=3 → Overlap=1 → Strong consistency
• R=2, W=4 → Overlap=1 → Strong consistency
• R=1, W=5 → Overlap=1 → Strong consistency (slow writes)
• R=5, W=1 → Overlap=1 → Strong consistency (slow reads)

R + W ≤ N  →  Eventual Consistency
(Quorums may not overlap, may read stale data)

• R=1, W=1 → Fast but may be inconsistent
• R=2, W=2 → Balanced but eventual consistency
```

**Implementation**:

```python
class QuorumStore:
    def __init__(self, nodes, N, R, W):
        self.nodes = nodes  # List of storage nodes
        self.N = N  # Total replicas
        self.R = R  # Read quorum
        self.W = W  # Write quorum

    def write(self, key, value):
        """Write to W nodes"""
        version = self._get_next_version(key)
        versioned_value = (value, version)

        successful_writes = 0
        for node in self.nodes:
            try:
                if node.write(key, versioned_value):
                    successful_writes += 1
                    if successful_writes >= self.W:
                        return True  # Quorum reached
            except Exception:
                continue

        return False  # Failed to reach quorum

    def read(self, key):
        """Read from R nodes and resolve conflicts"""
        responses = []

        for node in self.nodes:
            try:
                value = node.read(key)
                if value:
                    responses.append(value)
                    if len(responses) >= self.R:
                        break  # Quorum reached
            except Exception:
                continue

        if len(responses) < self.R:
            raise Exception("Failed to reach read quorum")

        # Resolve conflicts using version numbers
        latest = max(responses, key=lambda x: x[1])  # x[1] is version

        # Read repair: update stale replicas
        self._read_repair(key, latest, responses)

        return latest[0]  # Return value without version

    def _read_repair(self, key, latest_value, all_responses):
        """Update nodes with stale data"""
        for node in self.nodes:
            try:
                current = node.read(key)
                if current and current[1] < latest_value[1]:
                    node.write(key, latest_value)  # Update stale node
            except Exception:
                continue
```

**Tunable Consistency Levels** (Cassandra-style):

| Level | Description | Use Case |
|-------|-------------|----------|
| **ONE** | 1 node responds | Fastest, least consistent |
| **QUORUM** | Majority responds | Balanced |
| **ALL** | All nodes respond | Slowest, most consistent |
| **LOCAL_QUORUM** | Majority in local DC | Multi-DC deployments |
| **EACH_QUORUM** | Majority in each DC | Strong multi-DC consistency |

**Pros**:
- Tunable consistency per operation
- Can achieve strong consistency in AP system
- Read repair fixes inconsistencies automatically
- Flexible trade-offs

**Cons**:
- Higher latency (must wait for multiple nodes)
- More complex to implement
- Still need conflict resolution for concurrent writes
- Reduced availability if quorum can't be reached

**Use Cases**:
- Cassandra (tunable consistency)
- DynamoDB (configurable read/write consistency)
- Riak (N/R/W parameters)

**Real-World Example**: Apache Cassandra, Amazon DynamoDB

---

### Comparison of Conflict Resolution Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│           CONFLICT RESOLUTION STRATEGY COMPARISON               │
├──────────────┬──────────┬──────────┬──────────┬────────────────┤
│ Strategy     │ Data Loss│ Complexity│ Latency │ Use Case       │
├──────────────┼──────────┼──────────┼──────────┼────────────────┤
│ Last Write   │ High     │ Low      │ Low      │ Caching,       │
│ Wins (LWW)   │ ⚠️       │ ✓        │ ✓        │ profiles       │
├──────────────┼──────────┼──────────┼──────────┼────────────────┤
│ Vector       │ None     │ Medium   │ Low      │ Databases,     │
│ Clocks       │ ✓        │ ⚠️       │ ✓        │ carts          │
├──────────────┼──────────┼──────────┼──────────┼────────────────┤
│ CRDTs        │ None     │ High     │ Low      │ Collaborative  │
│              │ ✓        │ ✗        │ ✓        │ editing        │
├──────────────┼──────────┼──────────┼──────────┼────────────────┤
│ Application  │ None     │ High     │ Medium   │ Complex        │
│ Level        │ ✓        │ ✗        │ ⚠️       │ business logic │
├──────────────┼──────────┼──────────┼──────────┼────────────────┤
│ Quorum       │ Low      │ Medium   │ High     │ Tunable        │
│ Based        │ ✓        │ ⚠️       │ ✗        │ consistency    │
└──────────────┴──────────┴──────────┴──────────┴────────────────┘

Legend: ✓ Good  ⚠️ Medium  ✗ Poor
```

### Decision Tree: Choosing a Conflict Resolution Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│         CONFLICT RESOLUTION DECISION TREE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Can you tolerate data loss?                                   │
│       │                                                         │
│       ├── YES ──► Use Last Write Wins (LWW)                    │
│       │           Simple, fast, deterministic                  │
│       │                                                         │
│       └── NO ──► Is your data a well-known type?               │
│                       │                                         │
│                       ├── YES (Counter, Set, etc.)             │
│                       │   └──► Use CRDTs                        │
│                       │        Automatic, proven correct       │
│                       │                                         │
│                       └── NO ──► Need strong consistency?      │
│                                   │                             │
│                                   ├── YES                       │
│                                   │   └──► Use Quorum (R+W>N)  │
│                                   │        Tunable consistency │
│                                   │                             │
│                                   └── NO                        │
│                                       └──► Complex merge logic?│
│                                             │                   │
│                                             ├── YES             │
│                                             │   └──► App-Level │
│                                             │        Resolution │
│                                             │                   │
│                                             └── NO              │
│                                                 └──► Vector     │
│                                                      Clocks     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Understanding Consistency vs Availability Trade-offs

### What Does "Sacrificing Availability" Really Mean?

**Important**: Sacrificing availability does NOT necessarily mean your entire system goes down! It's more nuanced than that.

```
┌─────────────────────────────────────────────────────────────────┐
│         AVAILABILITY SACRIFICE: WHAT ACTUALLY HAPPENS           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MYTH: System goes completely offline ✗                        │
│                                                                 │
│  REALITY: System rejects SOME requests ✓                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │ During Network Partition:                        │          │
│  │                                                  │          │
│  │ CP System (Consistency Priority):               │          │
│  │ • Minority partition: REJECTS writes            │          │
│  │ • Majority partition: ACCEPTS writes            │          │
│  │ • Users in minority: Get errors (unavailable)   │          │
│  │ • Users in majority: System works normally      │          │
│  │                                                  │          │
│  │ AP System (Availability Priority):              │          │
│  │ • Both partitions: ACCEPT writes                │          │
│  │ • All users: System works (available)           │          │
│  │ • Trade-off: May read stale/conflicting data    │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Concrete Example: Banking System (CP - Consistency Priority)

```
┌─────────────────────────────────────────────────────────────────┐
│              BANKING SYSTEM DURING PARTITION                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Normal Operation (No Partition):                              │
│  ┌────────────────────────────────────────────────┐            │
│  │ Data Center 1 (3 nodes) ◄──────► Data Center 2 (2 nodes)   │
│  │ All 5 nodes in sync                            │            │
│  │ Account Balance: $1000                         │            │
│  │ ✓ All requests accepted                        │            │
│  └────────────────────────────────────────────────┘            │
│                                                                 │
│  Network Partition Occurs:                                     │
│  ┌────────────────────┐         XXXXX    ┌──────────────────┐ │
│  │ Data Center 1      │         XXXXX    │ Data Center 2    │ │
│  │ (3 nodes)          │    PARTITION     │ (2 nodes)        │ │
│  │ MAJORITY ✓         │         XXXXX    │ MINORITY ✗       │ │
│  └────────────────────┘                  └──────────────────┘ │
│           │                                       │            │
│           ▼                                       ▼            │
│  ┌────────────────────┐                  ┌──────────────────┐ │
│  │ User A tries to    │                  │ User B tries to  │ │
│  │ withdraw $100      │                  │ withdraw $50     │ │
│  │                    │                  │                  │ │
│  │ Response:          │                  │ Response:        │ │
│  │ ✓ SUCCESS          │                  │ ✗ ERROR 503      │ │
│  │ "Withdrawal done"  │                  │ "Service         │ │
│  │                    │                  │  temporarily     │ │
│  │ New balance: $900  │                  │  unavailable"    │ │
│  └────────────────────┘                  └──────────────────┘ │
│                                                                 │
│  User B experiences "unavailability" - but system is still     │
│  running! Just rejecting requests from minority partition.     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### How Long Does It Take to Maintain Consistency?

The time depends on the consistency model and operation type:

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSISTENCY OPERATION TIMELINES                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. SYNCHRONOUS REPLICATION (Strong Consistency)               │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client Write Request                             │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ [Primary Node] ──► [Replica 1] ──► [Replica 2]  │          │
│  │      │ Wait          │ Wait          │           │          │
│  │      │ for ACK       │ for ACK       │           │          │
│  │      ◄───────────────┴───────────────┘           │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ Return Success to Client                         │          │
│  │                                                  │          │
│  │ Time: Network RTT × Number of Replicas          │          │
│  │ Typical: 10-100ms (same datacenter)              │          │
│  │          100-500ms (cross-region)                │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  2. ASYNCHRONOUS REPLICATION (Eventual Consistency)            │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client Write Request                             │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ [Primary Node]                                   │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ Return Success to Client (IMMEDIATE)             │          │
│  │                                                  │          │
│  │ [Background] Primary ──► Replicas                │          │
│  │                                                  │          │
│  │ Client Time: 1-5ms (local write only)            │          │
│  │ Convergence Time: 100ms - several seconds        │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  3. QUORUM WRITES (Tunable Consistency)                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client Write Request (W=3 out of N=5)            │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ [Coordinator] ──► [Node 1] ✓                     │          │
│  │               ──► [Node 2] ✓                     │          │
│  │               ──► [Node 3] ✓ ← Quorum reached!   │          │
│  │               ──► [Node 4] (still waiting...)    │          │
│  │               ──► [Node 5] (still waiting...)    │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ Return Success (don't wait for 4 & 5)            │          │
│  │                                                  │          │
│  │ Time: RTT to W nodes (parallel)                  │          │
│  │ Typical: 10-50ms                                 │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Timing Breakdown

```python
# Example: Write latency comparison

# 1. Strong Consistency (Synchronous to all replicas)
class StrongConsistencyWrite:
    """
    Must wait for ALL replicas to acknowledge
    """
    def write(self, data):
        start = time.time()

        # Write to primary
        primary.write(data)  # 5ms

        # Wait for ALL replicas (sequential worst case)
        for replica in replicas:
            replica.write(data)  # 10ms each (network RTT)
            wait_for_ack()       # Must wait

        end = time.time()
        # Total: 5ms + (10ms × 3 replicas) = 35ms
        return end - start

# 2. Eventual Consistency (Async replication)
class EventualConsistencyWrite:
    """
    Return immediately, replicate in background
    """
    def write(self, data):
        start = time.time()

        # Write to primary only
        primary.write(data)  # 5ms

        # Trigger async replication (don't wait)
        async_replicate(data)

        end = time.time()
        # Total: 5ms (client sees this)
        # Background replication: 100ms - 2s (client doesn't wait)
        return end - start

# 3. Quorum Consistency (W=2, N=3)
class QuorumConsistencyWrite:
    """
    Wait for majority, not all
    """
    def write(self, data):
        start = time.time()

        # Write to all nodes in parallel
        futures = []
        for node in nodes:
            future = node.write_async(data)
            futures.append(future)

        # Wait for W=2 responses (majority)
        wait_for_count(futures, count=2)

        end = time.time()
        # Total: 10ms (parallel write to 2 nodes)
        # 3rd node still writing (don't wait)
        return end - start
```

### Typical Latency Numbers

| Operation | Strong Consistency | Quorum (W=2,N=3) | Eventual Consistency |
|-----------|-------------------|------------------|---------------------|
| **Same datacenter** | 20-50ms | 10-30ms | 1-5ms |
| **Cross-region** | 200-500ms | 100-300ms | 1-5ms (local write) |
| **Global (multi-continent)** | 500ms-2s | 200-800ms | 1-5ms (local write) |
| **Convergence time** | Immediate | Immediate | 100ms-10s |

### Data vs Process State: What Are We Replicating?

```
┌─────────────────────────────────────────────────────────────────┐
│           DATA REPLICATION vs PROCESS REPLICATION               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DATA REPLICATION (Most Common)                             │
│  ┌──────────────────────────────────────────────────┐          │
│  │ What: Database records, files, key-value pairs   │          │
│  │                                                  │          │
│  │ ┌─────────┐    ┌─────────┐    ┌─────────┐      │          │
│  │ │ Node A  │    │ Node B  │    │ Node C  │      │          │
│  │ │ ─────── │    │ ─────── │    │ ─────── │      │          │
│  │ │ User:   │    │ User:   │    │ User:   │      │          │
│  │ │  id=123 │◄──►│  id=123 │◄──►│  id=123 │      │          │
│  │ │  name=  │    │  name=  │    │  name=  │      │          │
│  │ │  "Alice"│    │  "Alice"│    │  "Alice"│      │          │
│  │ └─────────┘    └─────────┘    └─────────┘      │          │
│  │                                                  │          │
│  │ Same DATA replicated across nodes               │          │
│  │ Processes are independent                       │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  2. PROCESS STATE REPLICATION (Less Common)                    │
│  ┌──────────────────────────────────────────────────┐          │
│  │ What: Running process state, memory, variables   │          │
│  │                                                  │          │
│  │ ┌─────────┐    ┌─────────┐    ┌─────────┐      │          │
│  │ │Process A│    │Process B│    │Process C│      │          │
│  │ │ ─────── │    │ ─────── │    │ ─────── │      │          │
│  │ │ counter │    │ counter │    │ counter │      │          │
│  │ │  = 42   │◄──►│  = 42   │◄──►│  = 42   │      │          │
│  │ │ state=  │    │ state=  │    │ state=  │      │          │
│  │ │ "active"│    │ "active"│    │ "active"│      │          │
│  │ └─────────┘    └─────────┘    └─────────┘      │          │
│  │                                                  │          │
│  │ Same PROCESS STATE replicated                   │          │
│  │ Used in: Actor systems, stateful services       │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### CAP Theorem Applies to BOTH Data and Process State

```
┌─────────────────────────────────────────────────────────────────┐
│              WHAT CAP THEOREM COVERS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✓ DATA REPLICATION                                            │
│    • Database records (MySQL, PostgreSQL replication)          │
│    • Key-value stores (Redis, Memcached)                       │
│    • Document stores (MongoDB, CouchDB)                        │
│    • Object storage (S3, GCS)                                  │
│    • File systems (HDFS, GlusterFS)                            │
│                                                                 │
│  ✓ PROCESS STATE REPLICATION                                   │
│    • Actor systems (Akka Cluster, Orleans)                     │
│    • Stateful microservices (with state replication)           │
│    • Distributed caches (Hazelcast, Coherence)                 │
│    • Session stores (sticky sessions with replication)         │
│    • Workflow engines (Temporal, Cadence)                      │
│                                                                 │
│  ✓ HYBRID (Both Data + Process State)                          │
│    • Kubernetes StatefulSets (pods + persistent volumes)       │
│    • Distributed databases with stored procedures              │
│    • Event sourcing systems (state + events)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Data Replication (Database)

```
┌─────────────────────────────────────────────────────────────────┐
│         DATABASE REPLICATION - DATA ONLY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Scenario: PostgreSQL with 3 replicas                          │
│                                                                 │
│  ┌─────────────────┐                                           │
│  │ Primary DB      │                                           │
│  │ ─────────────── │                                           │
│  │ Process: PID    │  ← Different process IDs                  │
│  │   12345         │                                           │
│  │                 │                                           │
│  │ Data:           │  ← Same data replicated                   │
│  │   users table   │                                           │
│  │   orders table  │                                           │
│  └────────┬────────┘                                           │
│           │ Replication                                        │
│           ▼                                                     │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │ Replica 1       │    │ Replica 2       │                   │
│  │ ─────────────── │    │ ─────────────── │                   │
│  │ Process: PID    │    │ Process: PID    │                   │
│  │   67890         │    │   11111         │                   │
│  │                 │    │                 │                   │
│  │ Data:           │    │ Data:           │                   │
│  │   users table   │    │   users table   │                   │
│  │   orders table  │    │   orders table  │                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
│  • Each node runs DIFFERENT process (different PID)            │
│  • But they replicate the SAME DATA                            │
│  • CAP theorem applies to the DATA consistency                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Process State Replication (Actor System)

```
┌─────────────────────────────────────────────────────────────────┐
│         ACTOR SYSTEM - PROCESS STATE REPLICATION                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Scenario: Akka Cluster with replicated actors                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────┐           │
│  │ ShoppingCartActor (User 123)                    │           │
│  │                                                 │           │
│  │ Node A (Primary)      Node B (Replica)          │           │
│  │ ┌─────────────┐      ┌─────────────┐           │           │
│  │ │ Actor State │      │ Actor State │           │           │
│  │ │ ─────────── │◄────►│ ─────────── │           │           │
│  │ │ userId: 123 │      │ userId: 123 │           │           │
│  │ │ items: [    │      │ items: [    │           │           │
│  │ │   "book",   │      │   "book",   │           │           │
│  │ │   "pen"     │      │   "pen"     │           │           │
│  │ │ ]           │      │ ]           │           │           │
│  │ │ total: $25  │      │ total: $25  │           │           │
│  │ └─────────────┘      └─────────────┘           │           │
│  │                                                 │           │
│  │ • Same PROCESS STATE replicated                │           │
│  │ • If Node A fails, Node B takes over           │           │
│  │ • CAP theorem applies to STATE consistency     │           │
│  └─────────────────────────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Differences: Data vs Process State Replication

| Aspect | Data Replication | Process State Replication |
|--------|------------------|---------------------------|
| **What's replicated** | Database records, files | In-memory variables, state |
| **Persistence** | Usually persistent (disk) | Often in-memory (RAM) |
| **Recovery** | Read from disk | Rebuild from events/snapshots |
| **Examples** | MySQL replication | Akka Cluster, Orleans |
| **Consistency concern** | Data values | State variables |
| **Typical size** | GBs to TBs | MBs to GBs |
| **Replication speed** | Slower (disk I/O) | Faster (memory) |
| **Use case** | Long-term storage | Active computations |

### Most Systems Use Data Replication

```
┌─────────────────────────────────────────────────────────────────┐
│              TYPICAL ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │ APPLICATION TIER (Stateless)                     │          │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────┐        │          │
│  │ │ Server 1 │  │ Server 2 │  │ Server 3 │        │          │
│  │ │ (No state│  │ (No state│  │ (No state│        │          │
│  │ │  to sync)│  │  to sync)│  │  to sync)│        │          │
│  │ └────┬─────┘  └────┬─────┘  └────┬─────┘        │          │
│  └──────┼────────────┼─────────────┼───────────────┘          │
│         │            │             │                            │
│         └────────────┴─────────────┘                            │
│                      │                                          │
│                      ▼                                          │
│  ┌──────────────────────────────────────────────────┐          │
│  │ DATA TIER (Stateful - Replicated)                │          │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────┐        │          │
│  │ │Database 1│◄─┤Database 2│◄─┤Database 3│        │          │
│  │ │ (Primary)│  │(Replica) │  │(Replica) │        │          │
│  │ └──────────┘  └──────────┘  └──────────┘        │          │
│  │                                                  │          │
│  │ ← CAP theorem applies HERE (data layer)         │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  • Application servers: Stateless (no replication needed)      │
│  • Database: Stateful (data replication with CAP trade-offs)   │
│  • This is the most common pattern!                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Summary: Answering Your Questions

```
┌─────────────────────────────────────────────────────────────────┐
│                    KEY TAKEAWAYS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Q1: Does sacrificing availability mean downtime?              │
│  A1: NO! It means SOME requests get rejected (errors),         │
│      not that the entire system goes down.                     │
│      • Minority partition: Gets errors                         │
│      • Majority partition: Works normally                      │
│                                                                 │
│  Q2: How long does it take to maintain consistency?            │
│  A2: Depends on the model:                                     │
│      • Strong consistency: 10-500ms (wait for replicas)        │
│      • Eventual consistency: 1-5ms (client), 100ms-10s (sync)  │
│      • Quorum: 10-300ms (wait for majority)                    │
│                                                                 │
│  Q3: Are we talking about data or process state?               │
│  A3: BOTH! But mostly DATA replication:                        │
│      • Data replication: 90% of use cases (databases)          │
│      • Process state: 10% (actor systems, stateful services)   │
│      • Most apps: Stateless servers + Stateful database        │
│                                                                 │
│  Q4: Do processes get replicated across nodes?                 │
│  A4: Usually NO - processes are independent.                   │
│      Only the DATA they work with is replicated.               │
│      Exception: Actor systems, stateful microservices          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## How Database Replication Actually Works: Delta Tracking and Synchronization

### The Core Question: How Do Nodes Know What Changed?

Unlike Git (which tracks file-level changes) or rsync (which compares entire files), databases use specialized mechanisms to track and propagate changes efficiently.

```
┌─────────────────────────────────────────────────────────────────┐
│         REPLICATION MECHANISMS COMPARISON                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Git (Version Control):                                        │
│  • Tracks: File snapshots and diffs                            │
│  • Method: Commit-based, manual push/pull                      │
│  • Granularity: File level                                     │
│                                                                 │
│  Rsync/SCP (File Sync):                                        │
│  • Tracks: File timestamps and checksums                       │
│  • Method: Compare entire files, transfer differences          │
│  • Granularity: File/block level                               │
│                                                                 │
│  Database Replication:                                         │
│  • Tracks: Individual operations (INSERT, UPDATE, DELETE)      │
│  • Method: Continuous streaming of changes                     │
│  • Granularity: Row/document level (or even field level)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Method 1: Write-Ahead Log (WAL) Replication

**Most Common Method** - Used by PostgreSQL, MySQL, MongoDB, etc.

```
┌─────────────────────────────────────────────────────────────────┐
│              WRITE-AHEAD LOG (WAL) REPLICATION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIMARY NODE:                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │ 1. Client sends: UPDATE users SET name='Bob'     │          │
│  │                  WHERE id=123                    │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ 2. Write to WAL (Write-Ahead Log) FIRST          │          │
│  │    ┌─────────────────────────────────┐           │          │
│  │    │ WAL File (append-only log)      │           │          │
│  │    ├─────────────────────────────────┤           │          │
│  │    │ LSN: 1000 | INSERT user id=122  │           │          │
│  │    │ LSN: 1001 | UPDATE user id=123  │ ← New!    │          │
│  │    │ LSN: 1002 | ...                 │           │          │
│  │    └─────────────────────────────────┘           │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ 3. Apply to actual database                      │          │
│  │    ┌─────────────────────────────────┐           │          │
│  │    │ Users Table                     │           │          │
│  │    │ id=123, name='Bob' ✓            │           │          │
│  │    └─────────────────────────────────┘           │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ 4. Stream WAL to replicas                        │          │
│  └──────┼───────────────────────────────────────────┘          │
│         │                                                        │
│         ├──────────────────┬─────────────────────┐              │
│         ▼                  ▼                     ▼              │
│  ┌─────────────┐    ┌─────────────┐     ┌─────────────┐        │
│  │ REPLICA 1   │    │ REPLICA 2   │     │ REPLICA 3   │        │
│  │             │    │             │     │             │        │
│  │ 5. Receive  │    │ 5. Receive  │     │ 5. Receive  │        │
│  │    WAL      │    │    WAL      │     │    WAL      │        │
│  │    LSN:1001 │    │    LSN:1001 │     │    LSN:1001 │        │
│  │             │    │             │     │             │        │
│  │ 6. Apply    │    │ 6. Apply    │     │ 6. Apply    │        │
│  │    UPDATE   │    │    UPDATE   │     │    UPDATE   │        │
│  │             │    │             │     │             │        │
│  │ 7. Track    │    │ 7. Track    │     │ 7. Track    │        │
│  │    position │    │    position │     │    position │        │
│  │    LSN:1001 │    │    LSN:1001 │     │    LSN:1001 │        │
│  └─────────────┘    └─────────────┘     └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Concepts**:

1. **LSN (Log Sequence Number)**: Unique, monotonically increasing identifier for each change
2. **WAL**: Append-only log of ALL changes (like a journal)
3. **Streaming**: Continuous push of WAL entries to replicas
4. **Replay**: Replicas apply the same operations in the same order

**Implementation Example**:

```python
class WriteAheadLog:
    """
    Simplified WAL implementation
    """
    def __init__(self):
        self.log_file = "wal.log"
        self.current_lsn = 0
        self.replicas = []

    def write_operation(self, operation):
        """
        Write operation to WAL before applying to database
        """
        # 1. Assign LSN (Log Sequence Number)
        self.current_lsn += 1
        lsn = self.current_lsn

        # 2. Write to WAL (durable storage)
        wal_entry = {
            'lsn': lsn,
            'timestamp': time.time(),
            'operation': operation['type'],  # INSERT, UPDATE, DELETE
            'table': operation['table'],
            'data': operation['data'],
            'where': operation.get('where')
        }

        # Append to WAL file (fsync for durability)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(wal_entry) + '\n')
            os.fsync(f.fileno())  # Force write to disk

        # 3. Apply to local database
        self.apply_to_database(wal_entry)

        # 4. Stream to replicas (async)
        self.stream_to_replicas(wal_entry)

        return lsn

    def stream_to_replicas(self, wal_entry):
        """
        Send WAL entry to all replicas
        """
        for replica in self.replicas:
            try:
                # Send over network (TCP connection)
                replica.send_wal_entry(wal_entry)
            except Exception as e:
                # Replica will catch up later
                print(f"Failed to send to replica: {e}")

    def apply_to_database(self, wal_entry):
        """
        Apply the operation to the actual database
        """
        if wal_entry['operation'] == 'INSERT':
            db.insert(wal_entry['table'], wal_entry['data'])
        elif wal_entry['operation'] == 'UPDATE':
            db.update(wal_entry['table'], wal_entry['data'], wal_entry['where'])
        elif wal_entry['operation'] == 'DELETE':
            db.delete(wal_entry['table'], wal_entry['where'])


class Replica:
    """
    Replica that receives and applies WAL entries
    """
    def __init__(self, replica_id):
        self.replica_id = replica_id
        self.last_applied_lsn = 0  # Track position in WAL
        self.wal_buffer = []

    def receive_wal_entry(self, wal_entry):
        """
        Receive WAL entry from primary
        """
        # Check if this is the next expected entry
        if wal_entry['lsn'] == self.last_applied_lsn + 1:
            # Apply immediately
            self.apply_wal_entry(wal_entry)
            self.last_applied_lsn = wal_entry['lsn']

            # Check buffer for next entries
            self.process_buffer()
        else:
            # Out of order - buffer it
            self.wal_buffer.append(wal_entry)

    def apply_wal_entry(self, wal_entry):
        """
        Apply WAL entry to replica database
        """
        # Same logic as primary
        if wal_entry['operation'] == 'INSERT':
            db.insert(wal_entry['table'], wal_entry['data'])
        elif wal_entry['operation'] == 'UPDATE':
            db.update(wal_entry['table'], wal_entry['data'], wal_entry['where'])
        elif wal_entry['operation'] == 'DELETE':
            db.delete(wal_entry['table'], wal_entry['where'])

    def process_buffer(self):
        """
        Process buffered WAL entries in order
        """
        self.wal_buffer.sort(key=lambda x: x['lsn'])

        while self.wal_buffer:
            next_entry = self.wal_buffer[0]
            if next_entry['lsn'] == self.last_applied_lsn + 1:
                self.apply_wal_entry(next_entry)
                self.last_applied_lsn = next_entry['lsn']
                self.wal_buffer.pop(0)
            else:
                break  # Gap in sequence

    def catch_up(self, primary):
        """
        Catch up with primary if replica falls behind
        """
        # Request WAL entries from last_applied_lsn to current
        missing_entries = primary.get_wal_entries(
            start_lsn=self.last_applied_lsn + 1
        )

        for entry in missing_entries:
            self.apply_wal_entry(entry)
            self.last_applied_lsn = entry['lsn']
```

**Real-World Examples**:
- **PostgreSQL**: WAL streaming replication
- **MySQL**: Binary log (binlog) replication
- **MongoDB**: Oplog (operations log)

---

### Method 2: Statement-Based Replication

**Concept**: Replicate the actual SQL statements instead of the data changes.

```
┌─────────────────────────────────────────────────────────────────┐
│            STATEMENT-BASED REPLICATION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIMARY:                                                       │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client executes:                                 │          │
│  │ UPDATE users SET last_login=NOW()                │          │
│  │ WHERE country='USA'                              │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ Log the STATEMENT itself:                        │          │
│  │ "UPDATE users SET last_login=NOW()               │          │
│  │  WHERE country='USA'"                            │          │
│  └──────┼───────────────────────────────────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │ REPLICA:                                         │          │
│  │ Re-execute the SAME statement:                   │          │
│  │ UPDATE users SET last_login=NOW()                │          │
│  │ WHERE country='USA'                              │          │
│  │                                                  │          │
│  │ ⚠️  PROBLEM: NOW() gives different time!         │          │
│  │     Primary: 2024-01-01 10:00:00                │          │
│  │     Replica: 2024-01-01 10:00:05 ← Different!   │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pros**:
- Compact (just the SQL statement)
- Easy to understand

**Cons**:
- Non-deterministic functions (NOW(), RAND()) cause inconsistencies
- Different results if data differs
- Slower (must re-execute complex queries)

**Used by**: MySQL (older versions), some custom systems

---

### Method 3: Row-Based Replication

**Concept**: Replicate the actual data changes (before/after values).

```
┌─────────────────────────────────────────────────────────────────┐
│              ROW-BASED REPLICATION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIMARY:                                                       │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Client executes:                                 │          │
│  │ UPDATE users SET name='Alice' WHERE id=123       │          │
│  │      │                                            │          │
│  │      ▼                                            │          │
│  │ Log the ACTUAL DATA CHANGE:                      │          │
│  │ ┌────────────────────────────────────┐           │          │
│  │ │ Table: users                       │           │          │
│  │ │ Operation: UPDATE                  │           │          │
│  │ │ Row ID: 123                        │           │          │
│  │ │ Before: {id:123, name:'Bob'}       │           │          │
│  │ │ After:  {id:123, name:'Alice'}     │           │          │
│  │ └────────────────────────────────────┘           │          │
│  └──────┼───────────────────────────────────────────┘          │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │ REPLICA:                                         │          │
│  │ Apply the EXACT data change:                     │          │
│  │ • Find row with id=123                           │          │
│  │ • Change name from 'Bob' to 'Alice'              │          │
│  │                                                  │          │
│  │ ✓ Deterministic - always same result!           │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pros**:
- Deterministic (always same result)
- Handles non-deterministic functions
- Faster to apply (direct data change)

**Cons**:
- Larger log size (stores actual data)
- More bandwidth

**Used by**: MySQL (default in modern versions), PostgreSQL (logical replication)

---

### Method 4: Snapshot + Delta Replication

**Concept**: Periodic full snapshots + incremental changes (like Git commits + diffs).

```
┌─────────────────────────────────────────────────────────────────┐
│            SNAPSHOT + DELTA REPLICATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INITIAL SYNC:                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │ PRIMARY → REPLICA                                │          │
│  │                                                  │          │
│  │ 1. Take snapshot (full copy)                     │          │
│  │    ┌─────────────────────────┐                  │          │
│  │    │ Snapshot at LSN: 1000   │                  │          │
│  │    │ ─────────────────────── │                  │          │
│  │    │ users: 1M rows          │                  │          │
│  │    │ orders: 5M rows         │                  │          │
│  │    │ products: 10K rows      │                  │          │
│  │    └─────────────────────────┘                  │          │
│  │         │                                        │          │
│  │         ▼                                        │          │
│  │ 2. Transfer snapshot to replica (one-time)       │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  ONGOING SYNC:                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │ 3. Stream only CHANGES since snapshot            │          │
│  │    ┌─────────────────────────┐                  │          │
│  │    │ Delta (LSN: 1001-1100)  │                  │          │
│  │    │ ─────────────────────── │                  │          │
│  │    │ INSERT user id=500001   │                  │          │
│  │    │ UPDATE order id=123     │                  │          │
│  │    │ DELETE product id=999   │                  │          │
│  │    └─────────────────────────┘                  │          │
│  │         │                                        │          │
│  │         ▼                                        │          │
│  │ 4. Replica applies deltas incrementally          │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  PERIODIC RE-SNAPSHOT:                                          │
│  ┌──────────────────────────────────────────────────┐          │
│  │ 5. Every N hours/days, take new snapshot         │          │
│  │    • Prevents delta log from growing forever     │          │
│  │    • Allows new replicas to join quickly         │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:

```python
class SnapshotReplication:
    """
    Snapshot + Delta replication
    """
    def __init__(self):
        self.snapshot_interval = 3600  # 1 hour
        self.last_snapshot_lsn = 0
        self.current_lsn = 0

    def initial_sync(self, replica):
        """
        Initial synchronization with full snapshot
        """
        # 1. Create snapshot
        snapshot = self.create_snapshot()

        # 2. Transfer to replica
        replica.load_snapshot(snapshot)

        # 3. Replica tracks snapshot LSN
        replica.last_applied_lsn = snapshot['lsn']

    def create_snapshot(self):
        """
        Create full database snapshot
        """
        snapshot = {
            'lsn': self.current_lsn,
            'timestamp': time.time(),
            'data': {}
        }

        # Copy all tables
        for table in db.get_tables():
            snapshot['data'][table] = db.export_table(table)

        self.last_snapshot_lsn = self.current_lsn
        return snapshot

    def stream_delta(self, replica):
        """
        Stream changes since last snapshot
        """
        # Get all WAL entries since replica's last LSN
        deltas = self.get_wal_entries(
            start_lsn=replica.last_applied_lsn + 1,
            end_lsn=self.current_lsn
        )

        for delta in deltas:
            replica.apply_delta(delta)

    def should_snapshot(self):
        """
        Check if it's time for a new snapshot
        """
        time_since_snapshot = time.time() - self.last_snapshot_time
        return time_since_snapshot >= self.snapshot_interval
```

**Used by**: MongoDB (initial sync), MySQL (mysqldump + binlog), Cassandra (snapshot + hints)

---

### Method 5: Change Data Capture (CDC)

**Concept**: Capture changes from database transaction log and stream them.

```
┌─────────────────────────────────────────────────────────────────┐
│            CHANGE DATA CAPTURE (CDC)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │ DATABASE (Primary)                               │          │
│  │ ┌────────────────────────────────────┐           │          │
│  │ │ Transaction Log                    │           │          │
│  │ │ ────────────────────────────────── │           │          │
│  │ │ TXN 1: INSERT user id=123          │           │          │
│  │ │ TXN 2: UPDATE order id=456         │           │          │
│  │ │ TXN 3: DELETE product id=789       │           │          │
│  │ └────────────┬───────────────────────┘           │          │
│  └──────────────┼──────────────────────────────────┘          │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────┐          │
│  │ CDC Tool (Debezium, Maxwell, etc.)               │          │
│  │ • Reads transaction log                          │          │
│  │ • Converts to events                             │          │
│  │ • Publishes to message queue                     │          │
│  └──────────────┬───────────────────────────────────┘          │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Message Queue (Kafka, RabbitMQ)                  │          │
│  │ ┌────────────────────────────────────┐           │          │
│  │ │ Topic: database.users              │           │          │
│  │ │ Event: {op: "INSERT", id: 123}     │           │          │
│  │ └────────────────────────────────────┘           │          │
│  └──────────────┬───────────────────────────────────┘          │
│                 │                                               │
│                 ├──────────────┬────────────────┐               │
│                 ▼              ▼                ▼               │
│  ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Consumer 1      │  │ Consumer 2  │  │ Consumer 3  │        │
│  │ (Replica DB)    │  │ (Analytics) │  │ (Cache)     │        │
│  └─────────────────┘  └─────────────┘  └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Used by**: Debezium (Kafka Connect), AWS DMS, Google Datastream

---

### How Nodes Track State: Position Tracking

```
┌─────────────────────────────────────────────────────────────────┐
│              REPLICA POSITION TRACKING                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Each replica maintains:                                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Replica State File                               │          │
│  │ ────────────────────────────────────             │          │
│  │ primary_host: "db-primary.example.com"           │          │
│  │ primary_port: 5432                               │          │
│  │ last_applied_lsn: 1000567                        │          │
│  │ last_received_lsn: 1000570                       │          │
│  │ replication_lag: 3 entries                       │          │
│  │ last_sync_time: 2024-01-01 10:00:00              │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  Replica knows its position by:                                │
│  1. Tracking last applied LSN                                  │
│  2. Requesting entries from primary starting at LSN+1          │
│  3. Updating position after each successful apply              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison: Database Replication vs Git vs Rsync

```
┌─────────────────────────────────────────────────────────────────┐
│         DATABASE vs GIT vs RSYNC - DETAILED COMPARISON          │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│ Aspect       │ Database WAL │ Git          │ Rsync/Mutagen    │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Granularity  │ Row/Document │ File         │ File/Block       │
│              │ level        │ level        │ level            │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Tracking     │ LSN (Log Seq │ Commit SHA   │ Timestamp/       │
│ Mechanism    │ Number)      │ (hash)       │ Checksum         │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Change       │ Continuous   │ Manual       │ Periodic/        │
│ Detection    │ (real-time)  │ (on commit)  │ On-demand        │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Transfer     │ Streaming    │ Pull/Push    │ Compare &        │
│ Method       │ (push)       │ (on-demand)  │ Transfer         │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Ordering     │ Strict order │ DAG (branch) │ No ordering      │
│              │ (sequential) │              │                  │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Conflict     │ Automatic    │ Manual merge │ Last-write-wins  │
│ Resolution   │ (replays ops)│ required     │ or error         │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Latency      │ Milliseconds │ Seconds to   │ Seconds to       │
│              │              │ minutes      │ minutes          │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Bandwidth    │ Efficient    │ Efficient    │ Can be wasteful  │
│              │ (only ops)   │ (diffs)      │ (full files)     │
├──────────────┼──────────────┼──────────────┼──────────────────┤
│ Use Case     │ Live data    │ Code version │ File backup/     │
│              │ replication  │ control      │ sync             │
└──────────────┴──────────────┴──────────────┴──────────────────┘
```

### Visual Comparison: How Each System Tracks Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE WAL                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Time ──────────────────────────────────────────────►          │
│                                                                 │
│  LSN: 1000    1001      1002      1003      1004               │
│       │       │         │         │         │                  │
│       ▼       ▼         ▼         ▼         ▼                  │
│  [INSERT] [UPDATE] [DELETE] [INSERT] [UPDATE]                  │
│                                                                 │
│  • Continuous stream of operations                             │
│  • Each operation has unique LSN                               │
│  • Replicas track: "I've applied up to LSN 1002"               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         GIT                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Commit: abc123 ──► def456 ──► ghi789 ──► jkl012               │
│          │          │          │          │                     │
│          ▼          ▼          ▼          ▼                     │
│      [Snapshot] [Snapshot] [Snapshot] [Snapshot]               │
│      + diff     + diff     + diff     + diff                   │
│                                                                 │
│  • Discrete snapshots (commits)                                │
│  • Each commit has SHA hash                                    │
│  • Replicas track: "I'm at commit ghi789"                      │
│  • Manual pull/push required                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      RSYNC/MUTAGEN                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Sync 1        Sync 2        Sync 3        Sync 4              │
│  (manual)      (manual)      (manual)      (manual)            │
│     │            │            │            │                    │
│     ▼            ▼            ▼            ▼                    │
│  Compare ──► Compare ──► Compare ──► Compare                   │
│  all files   all files   all files   all files                 │
│                                                                 │
│  • No continuous tracking                                      │
│  • Compares file metadata (timestamp, size, checksum)          │
│  • Transfers entire changed files                              │
│  • No concept of "position" - just "in sync" or "out of sync"  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Databases Don't Use Git/Rsync Approach

```
┌─────────────────────────────────────────────────────────────────┐
│         WHY NOT USE GIT/RSYNC FOR DATABASE REPLICATION?         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ Git Approach Problems:                                      │
│  ┌──────────────────────────────────────────────────┐          │
│  │ 1. Too Slow                                      │          │
│  │    • Database: 10,000 writes/second              │          │
│  │    • Git: Can't commit that fast                 │          │
│  │                                                  │          │
│  │ 2. Wrong Granularity                             │          │
│  │    • Database: Need row-level changes            │          │
│  │    • Git: Works on file level                    │          │
│  │                                                  │          │
│  │ 3. Manual Intervention                           │          │
│  │    • Database: Automatic, continuous             │          │
│  │    • Git: Requires manual commit/push            │          │
│  │                                                  │          │
│  │ 4. Merge Conflicts                               │          │
│  │    • Database: Deterministic replay              │          │
│  │    • Git: Requires human to resolve              │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  ❌ Rsync Approach Problems:                                    │
│  ┌──────────────────────────────────────────────────┐          │
│  │ 1. Inefficient                                   │          │
│  │    • Must scan all files every sync              │          │
│  │    • Database: Millions of rows = huge overhead  │          │
│  │                                                  │          │
│  │ 2. No Transactional Consistency                  │          │
│  │    • Rsync: Copies files independently           │          │
│  │    • Database: Needs atomic transactions         │          │
│  │                                                  │          │
│  │ 3. Corruption Risk                               │          │
│  │    • Copying live database files = corruption    │          │
│  │    • Need to stop database first                 │          │
│  │                                                  │          │
│  │ 4. No Ordering Guarantee                         │          │
│  │    • Rsync: Files copied in any order            │          │
│  │    • Database: Operations must be ordered        │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Example: PostgreSQL WAL Streaming

```python
# PostgreSQL WAL Streaming - Simplified Example

class PostgreSQLPrimary:
    """
    PostgreSQL primary node with WAL streaming
    """
    def __init__(self):
        self.wal_sender_processes = []
        self.current_wal_position = "0/0"  # Format: file/offset

    def execute_query(self, sql):
        """
        Execute query and generate WAL
        """
        # 1. Parse SQL
        operation = self.parse_sql(sql)

        # 2. Write to WAL FIRST (Write-Ahead)
        wal_record = self.write_wal(operation)

        # 3. Apply to database
        self.apply_to_database(operation)

        # 4. Notify WAL senders (streaming to replicas)
        self.notify_wal_senders(wal_record)

        return "OK"

    def write_wal(self, operation):
        """
        Write operation to Write-Ahead Log
        """
        wal_record = {
            'lsn': self.get_next_lsn(),
            'xid': self.get_transaction_id(),
            'operation': operation['type'],
            'relation': operation['table'],
            'data': operation['data']
        }

        # Write to WAL file (on disk)
        with open(f"pg_wal/{self.current_wal_file}", 'ab') as f:
            f.write(self.serialize_wal_record(wal_record))
            os.fsync(f.fileno())  # Force to disk

        self.current_wal_position = wal_record['lsn']
        return wal_record

    def start_wal_sender(self, replica_connection):
        """
        Start WAL sender process for a replica
        """
        sender = WALSender(replica_connection)
        sender.start()
        self.wal_sender_processes.append(sender)


class WALSender:
    """
    Process that streams WAL to a replica
    """
    def __init__(self, replica_connection):
        self.replica = replica_connection
        self.last_sent_lsn = "0/0"

    def start(self):
        """
        Start streaming WAL to replica
        """
        # 1. Get replica's current position
        replica_lsn = self.replica.get_current_lsn()

        # 2. Stream all WAL records since that position
        while True:
            # Get next WAL record
            wal_record = self.read_wal_from_position(replica_lsn)

            if wal_record:
                # Send to replica
                self.replica.send(wal_record)

                # Wait for acknowledgment
                ack = self.replica.receive_ack()

                if ack['status'] == 'applied':
                    replica_lsn = ack['lsn']
                    self.last_sent_lsn = replica_lsn
            else:
                # No new WAL, wait for notification
                time.sleep(0.001)  # 1ms


class PostgreSQLReplica:
    """
    PostgreSQL replica (standby) node
    """
    def __init__(self, primary_host):
        self.primary = self.connect_to_primary(primary_host)
        self.current_lsn = "0/0"
        self.recovery_mode = True

    def start_replication(self):
        """
        Start receiving and applying WAL from primary
        """
        # 1. Tell primary our current position
        self.primary.send_replication_start(self.current_lsn)

        # 2. Receive and apply WAL records
        while self.recovery_mode:
            wal_record = self.primary.receive_wal()

            if wal_record:
                # Apply WAL record to local database
                self.apply_wal_record(wal_record)

                # Update position
                self.current_lsn = wal_record['lsn']

                # Send acknowledgment
                self.primary.send_ack({
                    'status': 'applied',
                    'lsn': self.current_lsn
                })

    def apply_wal_record(self, wal_record):
        """
        Apply WAL record to replica database
        """
        if wal_record['operation'] == 'INSERT':
            self.db.insert(
                wal_record['relation'],
                wal_record['data']
            )
        elif wal_record['operation'] == 'UPDATE':
            self.db.update(
                wal_record['relation'],
                wal_record['data'],
                wal_record['where']
            )
        elif wal_record['operation'] == 'DELETE':
            self.db.delete(
                wal_record['relation'],
                wal_record['where']
            )

        # Flush to disk
        self.db.fsync()
```

### Network Protocol: How WAL is Transferred

```
┌─────────────────────────────────────────────────────────────────┐
│              WAL STREAMING PROTOCOL                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIMARY                                    REPLICA             │
│  ┌─────────┐                                ┌─────────┐        │
│  │         │                                │         │        │
│  │         │◄───── 1. Connect ──────────────│         │        │
│  │         │       (TCP connection)         │         │        │
│  │         │                                │         │        │
│  │         │◄───── 2. START_REPLICATION ────│         │        │
│  │         │       (LSN: 0/1000000)         │         │        │
│  │         │                                │         │        │
│  │         │────── 3. WAL Record ──────────►│         │        │
│  │         │       (LSN: 0/1000001)         │         │        │
│  │         │       [Binary data: 512 bytes] │         │        │
│  │         │                                │         │        │
│  │         │◄───── 4. ACK ──────────────────│         │        │
│  │         │       (LSN: 0/1000001, OK)     │         │        │
│  │         │                                │         │        │
│  │         │────── 5. WAL Record ──────────►│         │        │
│  │         │       (LSN: 0/1000002)         │         │        │
│  │         │                                │         │        │
│  │         │◄───── 6. ACK ──────────────────│         │        │
│  │         │       (LSN: 0/1000002, OK)     │         │        │
│  │         │                                │         │        │
│  │         │────── 7. Keepalive ───────────►│         │        │
│  │         │       (every 10 seconds)       │         │        │
│  │         │                                │         │        │
│  └─────────┘                                └─────────┘        │
│                                                                 │
│  • Persistent TCP connection                                   │
│  • Binary protocol (efficient)                                 │
│  • Acknowledgments for flow control                            │
│  • Keepalives to detect connection loss                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Summary: Key Differences

```
┌─────────────────────────────────────────────────────────────────┐
│                    KEY TAKEAWAYS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Database Replication (WAL):                                   │
│  ✓ Real-time streaming (milliseconds)                          │
│  ✓ Operation-level granularity (INSERT, UPDATE, DELETE)        │
│  ✓ Automatic and continuous                                    │
│  ✓ Ordered replay (deterministic)                              │
│  ✓ Position tracking with LSN                                  │
│  ✓ Efficient (only operations, not full data)                  │
│                                                                 │
│  Git:                                                           │
│  • Snapshot-based (commits)                                    │
│  • File-level granularity                                      │
│  • Manual commits/pushes                                       │
│  • DAG structure (branches)                                    │
│  • SHA-based tracking                                          │
│  • Good for code, not live data                                │
│                                                                 │
│  Rsync/Mutagen:                                                 │
│  • Periodic comparison                                         │
│  • File/block-level granularity                                │
│  • On-demand sync                                              │
│  • No ordering guarantees                                      │
│  • Timestamp/checksum tracking                                 │
│  • Good for file backup, not databases                         │
│                                                                 │
│  Why databases use WAL:                                        │
│  1. Speed: Millisecond latency                                 │
│  2. Granularity: Row-level changes                             │
│  3. Consistency: Transactional guarantees                      │
│  4. Ordering: Strict sequential replay                         │
│  5. Efficiency: Only operations, not full data                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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
