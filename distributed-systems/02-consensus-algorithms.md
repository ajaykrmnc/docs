# Consensus Algorithms in Distributed Systems

## Table of Contents
1. [Introduction to Consensus](#introduction-to-consensus)
2. [The Consensus Problem](#the-consensus-problem)
3. [Paxos Algorithm](#paxos-algorithm)
4. [Raft Algorithm](#raft-algorithm)
5. [Zab (Zookeeper Atomic Broadcast)](#zab-zookeeper-atomic-broadcast)
6. [Byzantine Fault Tolerance](#byzantine-fault-tolerance)
7. [Comparison and Use Cases](#comparison-and-use-cases)
8. [Interview Questions](#interview-questions)

---

## Introduction to Consensus

### What is Consensus?

**Consensus** is the process by which a group of distributed nodes agree on a single value or state, even when some nodes may fail. It's the foundation for building reliable distributed systems.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSENSUS PROBLEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Node A proposes: X=5                                         │
│   Node B proposes: X=7                                         │
│   Node C proposes: X=5                                         │
│                                                                 │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                   │
│   │ Node A  │    │ Node B  │    │ Node C  │                   │
│   │  X=5    │    │  X=7    │    │  X=5    │                   │
│   └────┬────┘    └────┬────┘    └────┬────┘                   │
│        │              │              │                         │
│        └──────────────┼──────────────┘                         │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                               │
│              │   CONSENSUS     │                               │
│              │   ALGORITHM     │                               │
│              └────────┬────────┘                               │
│                       │                                         │
│                       ▼                                         │
│              All nodes agree: X=5                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why is Consensus Important?

Consensus is required for:
- **Leader Election**: Choosing a single coordinator
- **Atomic Broadcast**: Delivering messages in the same order
- **State Machine Replication**: Keeping replicas in sync
- **Distributed Locking**: Coordinating access to resources
- **Configuration Management**: Agreeing on system state

### The FLP Impossibility Result

**Fischer, Lynch, and Paterson (1985)** proved that:

> In an asynchronous distributed system, it is impossible to guarantee consensus if even ONE node can fail.

```
┌─────────────────────────────────────────────────────────────────┐
│                 FLP IMPOSSIBILITY THEOREM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Given:                                                         │
│  • Asynchronous system (no timing guarantees)                  │
│  • At least one node can fail                                  │
│                                                                 │
│  It is IMPOSSIBLE to:                                          │
│  • Always terminate (liveness)                                 │
│  • Always agree (safety)                                       │
│  • Tolerate any failure                                        │
│                                                                 │
│  Practical Workarounds:                                        │
│  • Use timeouts (partial synchrony)                            │
│  • Accept probabilistic guarantees                             │
│  • Use failure detectors                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Consensus Problem

### Formal Definition

A consensus protocol must satisfy these properties:

| Property | Description |
|----------|-------------|
| **Agreement** | All non-faulty nodes decide on the same value |
| **Validity** | The decided value was proposed by some node |
| **Termination** | All non-faulty nodes eventually decide |
| **Integrity** | Each node decides at most once |

### Types of Failures

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAILURE TYPES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐     ┌──────────────────┐                │
│  │   CRASH FAILURE  │     │ BYZANTINE FAILURE │                │
│  ├──────────────────┤     ├──────────────────┤                │
│  │                  │     │                  │                 │
│  │  Node stops      │     │  Node can:       │                 │
│  │  responding      │     │  • Lie           │                 │
│  │                  │     │  • Send wrong    │                 │
│  │  ┌────────┐     │     │    messages      │                 │
│  │  │ Node X │     │     │  • Act malicious │                 │
│  │  │   💀   │     │     │                  │                 │
│  │  └────────┘     │     │  ┌────────┐      │                 │
│  │                  │     │  │ Node X │      │                 │
│  │  Simpler to      │     │  │   😈   │      │                 │
│  │  handle          │     │  └────────┘      │                 │
│  │                  │     │                  │                 │
│  │  Paxos, Raft     │     │  Harder, needs   │                 │
│  │                  │     │  PBFT, etc.      │                 │
│  └──────────────────┘     └──────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Quorum Requirements

For **crash failures** (Paxos, Raft):
- Need `n ≥ 2f + 1` nodes to tolerate `f` failures
- Majority quorum: `⌊n/2⌋ + 1`

For **Byzantine failures** (PBFT):
- Need `n ≥ 3f + 1` nodes to tolerate `f` failures
- Quorum: `2f + 1`

```
Crash Failure Example:
• 5 nodes can tolerate 2 failures (majority = 3)
• 3 nodes can tolerate 1 failure (majority = 2)

Byzantine Failure Example:
• 4 nodes can tolerate 1 Byzantine failure
• 7 nodes can tolerate 2 Byzantine failures
```

---

## Paxos Algorithm

### Overview

**Paxos** was invented by Leslie Lamport in 1989 and is one of the most influential consensus algorithms. It's known for being correct but notoriously difficult to understand and implement.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PAXOS ROLES                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  PROPOSER   │   │  ACCEPTOR   │   │   LEARNER   │          │
│  ├─────────────┤   ├─────────────┤   ├─────────────┤          │
│  │ Proposes    │   │ Votes on    │   │ Learns the  │          │
│  │ values      │   │ proposals   │   │ chosen      │          │
│  │             │   │             │   │ value       │          │
│  │ Leaders     │   │ Memory      │   │ Replicas    │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                 │
│  Note: A single node can play multiple roles                   │
└─────────────────────────────────────────────────────────────────┘
```

### Basic Paxos: Two-Phase Protocol

#### Phase 1: Prepare

```
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 1: PREPARE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Proposer                    Acceptors                         │
│     │                                                           │
│     │   Prepare(n)          ┌─────────┐                        │
│     │───────────────────────│Acceptor1│                        │
│     │───────────────────────│Acceptor2│                        │
│     │───────────────────────│Acceptor3│                        │
│     │                       └─────────┘                        │
│     │                                                           │
│     │   Promise(n, last_accepted_value)                        │
│     │◄──────────────────────────────────                       │
│     │                                                           │
│  Proposer sends: Prepare(n)                                    │
│  • n = proposal number (must be unique and increasing)         │
│                                                                 │
│  Acceptor responds: Promise(n, v)                              │
│  • Promises not to accept proposals < n                        │
│  • Returns previously accepted value (if any)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Phase 2: Accept

```
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: ACCEPT                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Proposer                    Acceptors                         │
│     │                                                           │
│     │   Accept(n, value)    ┌─────────┐                        │
│     │───────────────────────│Acceptor1│                        │
│     │───────────────────────│Acceptor2│                        │
│     │───────────────────────│Acceptor3│                        │
│     │                       └─────────┘                        │
│     │                                                           │
│     │   Accepted(n, value)                                     │
│     │◄──────────────────────────────────                       │
│     │                                                           │
│  Proposer sends: Accept(n, value)                              │
│  • value = highest-numbered accepted value from Phase 1        │
│  • OR proposer's own value if no prior accepts                 │
│                                                                 │
│  Acceptor responds: Accepted(n, value)                         │
│  • Only accepts if n ≥ highest promised number                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Complete Paxos Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              BASIC PAXOS - COMPLETE FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Proposer         Acceptor 1    Acceptor 2    Acceptor 3       │
│     │                 │             │             │             │
│     │ PREPARE(1)      │             │             │             │
│     │────────────────►│             │             │             │
│     │────────────────────────────►  │             │             │
│     │─────────────────────────────────────────►   │             │
│     │                 │             │             │             │
│     │ PROMISE(1,null) │             │             │             │
│     │◄────────────────│             │             │             │
│     │◄─────────────────────────────│             │             │
│     │◄────────────────────────────────────────── │             │
│     │                 │             │             │             │
│     │ ACCEPT(1,"X")   │             │             │             │
│     │────────────────►│             │             │             │
│     │────────────────────────────►  │             │             │
│     │─────────────────────────────────────────►   │             │
│     │                 │             │             │             │
│     │ ACCEPTED(1,"X") │             │             │             │
│     │◄────────────────│             │             │             │
│     │◄─────────────────────────────│             │             │
│     │◄────────────────────────────────────────── │             │
│     │                 │             │             │             │
│  VALUE "X" IS CHOSEN (majority accepted)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Paxos Optimization

Basic Paxos requires two rounds for each value. **Multi-Paxos** optimizes by:

1. **Electing a stable leader**: Skip Phase 1 for subsequent proposals
2. **Pipelining**: Multiple values in flight simultaneously

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-PAXOS                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Basic Paxos:                                                  │
│  Value 1: Prepare → Accept                                     │
│  Value 2: Prepare → Accept                                     │
│  Value 3: Prepare → Accept                                     │
│                                                                 │
│  Multi-Paxos (with stable leader):                             │
│  Leader elected: Prepare (once)                                │
│  Value 1: Accept                                               │
│  Value 2: Accept                                               │
│  Value 3: Accept                                               │
│                                                                 │
│  Benefit: Reduces round trips from 2 to 1 per value            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Paxos Challenges

| Challenge | Description |
|-----------|-------------|
| **Complexity** | Hard to understand and implement correctly |
| **Livelock** | Multiple proposers can keep preempting each other |
| **No leader** | Basic Paxos doesn't specify leader election |
| **Log gaps** | Multi-Paxos can have holes in the log |
| **Reconfiguration** | Adding/removing nodes is complex |

---

## Raft Algorithm

### Overview

**Raft** was designed by Diego Ongaro and John Ousterhout in 2014 as an understandable alternative to Paxos. It provides equivalent guarantees but is structured for clarity.

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAFT DESIGN GOALS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "Raft is a consensus algorithm that is designed to be         │
│   easy to understand."                                          │
│                                                                 │
│  Key decomposition:                                             │
│  1. Leader Election                                             │
│  2. Log Replication                                             │
│  3. Safety                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Raft Node States

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAFT STATE MACHINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    starts up                                    │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                               │
│              │    FOLLOWER     │◄─────────────┐                │
│              └────────┬────────┘              │                │
│                       │                        │                │
│                       │ timeout,               │ discovers      │
│                       │ start election         │ higher term    │
│                       ▼                        │                │
│              ┌─────────────────┐              │                │
│         ┌───►│   CANDIDATE     │──────────────┘                │
│         │    └────────┬────────┘                               │
│         │             │                                         │
│  timeout,│            │ wins election                          │
│  new     │            │ (majority votes)                       │
│  election│            ▼                                         │
│         │    ┌─────────────────┐                               │
│         └────│     LEADER      │                               │
│              └─────────────────┘                               │
│                                                                 │
│  Key Terms:                                                     │
│  • Term: Logical clock, incremented on each election          │
│  • Each term has at most one leader                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```


### Leader Election in Raft

```
┌─────────────────────────────────────────────────────────────────┐
│                 RAFT LEADER ELECTION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Node A (Follower)   Node B (Follower)   Node C (Follower)     │
│       │                   │                   │                 │
│       │ election timeout  │                   │                 │
│       │ expires           │                   │                 │
│       ▼                   │                   │                 │
│  [CANDIDATE]              │                   │                 │
│  Term = 2                 │                   │                 │
│       │                   │                   │                 │
│       │ RequestVote(term=2)                   │                 │
│       │──────────────────►│                   │                 │
│       │───────────────────────────────────────►                 │
│       │                   │                   │                 │
│       │ Vote granted      │                   │                 │
│       │◄──────────────────│                   │                 │
│       │◄──────────────────────────────────────│                 │
│       │                   │                   │                 │
│       ▼                   │                   │                 │
│   [LEADER]   Majority votes received (2 of 3)│                 │
│  Term = 2                 │                   │                 │
│       │                   │                   │                 │
│       │ Heartbeat (AppendEntries)            │                 │
│       │──────────────────►│                   │                 │
│       │───────────────────────────────────────►                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Election Rules**:
1. Follower becomes candidate after election timeout
2. Candidate increments term and votes for itself
3. Candidate requests votes from all other nodes
4. Node grants vote if:
   - Hasn't voted in this term
   - Candidate's log is at least as up-to-date
5. Candidate becomes leader with majority votes

### Log Replication

```
┌─────────────────────────────────────────────────────────────────┐
│                 RAFT LOG REPLICATION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client Request: SET X=5                                       │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      LEADER                              │   │
│  │  Log: [1:SET A=1] [2:SET B=2] [3:SET X=5]              │   │
│  │                                 ▲                        │   │
│  │                          new entry                       │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│    AppendEntries(entries=[3:SET X=5], prevLogIndex=2)          │
│                         │                                       │
│         ┌───────────────┼───────────────┐                      │
│         ▼               ▼               ▼                      │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│   │ Follower │   │ Follower │   │ Follower │                  │
│   │   [1]    │   │  [1][2]  │   │[1][2][3] │                  │
│   │   [2]    │   │   [3]    │   │          │                  │
│   │   [3]    │   │          │   │          │                  │
│   └──────────┘   └──────────┘   └──────────┘                  │
│                                                                 │
│  Once majority acknowledges, entry is COMMITTED                │
│  Leader then notifies followers of commit                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Log Matching Property**:
- If two logs contain an entry with the same index and term, they contain identical commands
- If two logs contain an entry with the same index and term, all preceding entries are identical

### Raft Safety Properties

```
┌─────────────────────────────────────────────────────────────────┐
│                 RAFT SAFETY GUARANTEES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ELECTION SAFETY                                            │
│     At most one leader per term                                │
│                                                                 │
│  2. LEADER APPEND-ONLY                                         │
│     Leader never overwrites or deletes entries                 │
│                                                                 │
│  3. LOG MATCHING                                               │
│     Same index + term → identical entries up to that point    │
│                                                                 │
│  4. LEADER COMPLETENESS                                        │
│     Committed entries will be present in future leaders       │
│                                                                 │
│  5. STATE MACHINE SAFETY                                       │
│     If a server applies entry at index N, no other server     │
│     applies a different entry at index N                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Raft vs Paxos

| Aspect | Raft | Paxos |
|--------|------|-------|
| **Understandability** | Designed for clarity | Notoriously complex |
| **Leader** | Strong leader required | Leaderless (basic) |
| **Log Structure** | No gaps allowed | Can have gaps |
| **Implementation** | Many production implementations | Fewer correct implementations |
| **Membership Change** | Joint consensus | Various approaches |
| **Performance** | Similar | Similar |

---

## Zab (Zookeeper Atomic Broadcast)

### Overview

**Zab** is the consensus protocol used by Apache Zookeeper. It's designed for primary-backup systems where a primary (leader) processes all writes.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ZAB OVERVIEW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ZAB provides:                                                 │
│  1. Reliable delivery: If one server delivers, all will       │
│  2. Total order: Messages delivered in same order everywhere  │
│  3. Causal order: If message a causes b, a delivered first    │
│                                                                 │
│  Phases:                                                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  DISCOVERY  │──►│    SYNC     │──►│  BROADCAST  │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│  Find leader       Sync state        Normal operation          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Zab Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                    ZAB PHASES                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: DISCOVERY (Leader Election)                          │
│  ─────────────────────────────────────                         │
│  • Prospective leader collects epoch numbers                   │
│  • Followers send their latest transaction (zxid)             │
│  • Leader chosen based on highest zxid                         │
│                                                                 │
│  PHASE 2: SYNCHRONIZATION                                      │
│  ─────────────────────────────────────                         │
│  • Leader sends its history to followers                       │
│  • Followers sync to leader's state                           │
│  • Once quorum synced, move to broadcast                      │
│                                                                 │
│  PHASE 3: BROADCAST (Normal Operation)                         │
│  ─────────────────────────────────────                         │
│  • Leader proposes transactions                                │
│  • Followers acknowledge                                       │
│  • Leader commits after quorum ack                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Byzantine Fault Tolerance

### What are Byzantine Faults?

**Byzantine faults** occur when nodes can behave arbitrarily, including:
- Sending different values to different nodes
- Lying about their state
- Colluding with other faulty nodes

Named after the **Byzantine Generals Problem** (Lamport, 1982).

```
┌─────────────────────────────────────────────────────────────────┐
│              BYZANTINE GENERALS PROBLEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Generals must coordinate attack/retreat:                      │
│                                                                 │
│      General A ◄────► General B ◄────► General C               │
│     "Attack!"        "Attack!"       (traitor)                 │
│                                      "Retreat!"                │
│                                                                 │
│  Problem: How to reach consensus with traitors?                │
│                                                                 │
│  Solution: Need n ≥ 3f + 1 nodes to tolerate f traitors       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### PBFT (Practical Byzantine Fault Tolerance)

**PBFT** was introduced by Castro and Liskov in 1999, making BFT practical for real systems.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PBFT PROTOCOL                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client    Primary    Replica 1    Replica 2    Replica 3      │
│    │          │           │            │            │           │
│    │ REQUEST  │           │            │            │           │
│    │─────────►│           │            │            │           │
│    │          │           │            │            │           │
│    │          │ PRE-PREPARE            │            │           │
│    │          │──────────►│            │            │           │
│    │          │───────────────────────►│            │           │
│    │          │────────────────────────────────────►│           │
│    │          │           │            │            │           │
│    │          │    PREPARE (broadcast to all)      │           │
│    │          │◄──────────│            │            │           │
│    │          │◄──────────────────────►│            │           │
│    │          │◄──────────────────────────────────►│           │
│    │          │           │            │            │           │
│    │          │    COMMIT (broadcast to all)       │           │
│    │          │◄─────────►│◄──────────►│◄─────────►│           │
│    │          │           │            │            │           │
│    │◄─────────│───────────│────────────│────────────│           │
│    │          REPLY (f+1 matching replies)         │           │
│    │          │           │            │            │           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### PBFT Phases

| Phase | Description |
|-------|-------------|
| **Pre-Prepare** | Primary assigns sequence number, broadcasts to replicas |
| **Prepare** | Replicas broadcast prepare messages; wait for 2f+1 |
| **Commit** | Replicas broadcast commit; execute after 2f+1 commits |
| **Reply** | Send result to client; client waits for f+1 matching |


---

## Comparison and Use Cases

### Algorithm Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSENSUS ALGORITHM COMPARISON                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Algorithm │ Fault Type │ Nodes │ Rounds │ Message Complexity  │
│  ──────────┼────────────┼───────┼────────┼──────────────────── │
│  Paxos     │ Crash      │ 2f+1  │   2    │      O(n)          │
│  Raft      │ Crash      │ 2f+1  │   2    │      O(n)          │
│  Zab       │ Crash      │ 2f+1  │   2    │      O(n)          │
│  PBFT      │ Byzantine  │ 3f+1  │   3    │      O(n²)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Real-World Implementations

| System | Algorithm | Use Case |
|--------|-----------|----------|
| **etcd** | Raft | Kubernetes configuration, service discovery |
| **Consul** | Raft | Service mesh, KV store |
| **CockroachDB** | Raft | Distributed SQL database |
| **Zookeeper** | Zab | Configuration, coordination |
| **TiKV** | Raft | Distributed key-value store |
| **MongoDB** | Raft-like | Document database |
| **Hyperledger Fabric** | PBFT variants | Blockchain |

### When to Use What

```
┌─────────────────────────────────────────────────────────────────┐
│              CHOOSING A CONSENSUS ALGORITHM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Do you trust all nodes?                                       │
│       │                                                         │
│       ├── YES ──► Use Raft or Paxos (simpler, faster)          │
│       │                                                         │
│       └── NO ──► Need Byzantine tolerance                      │
│                       │                                         │
│                       └── Use PBFT or variants                 │
│                                                                 │
│  Need strong leader?                                           │
│       │                                                         │
│       ├── YES ──► Raft (clear leader, simpler recovery)        │
│       │                                                         │
│       └── NO ──► Basic Paxos (leaderless, but complex)         │
│                                                                 │
│  Existing system?                                              │
│       │                                                         │
│       ├── Zookeeper ──► Already uses Zab                       │
│       ├── etcd ──────► Already uses Raft                       │
│       └── Custom ────► Raft (best documentation)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: Explain the difference between Paxos and Raft.**

| Aspect | Paxos | Raft |
|--------|-------|------|
| Design goal | Correctness | Understandability |
| Leader | Optional (Multi-Paxos has leader) | Required |
| Log gaps | Allowed | Not allowed |
| Learner role | Separate | Combined with follower |
| Membership change | Complex | Joint consensus |

**Q2: Why does PBFT need 3f+1 nodes while Raft only needs 2f+1?**

- **Raft (crash failures)**: Failed nodes simply stop. With 2f+1 nodes, f can fail and f+1 (majority) still agree.
- **PBFT (Byzantine failures)**: Failed nodes can lie. With 3f+1 nodes:
  - f can be Byzantine
  - f can be slow (network)
  - Still have f+1 honest, fast nodes to agree

**Q3: What happens in Raft if the leader fails during log replication?**

```
1. Followers notice missing heartbeats
2. Election timeout expires
3. Follower becomes candidate
4. New leader elected
5. New leader:
   - Has all committed entries (leader completeness)
   - May have uncommitted entries (will be replicated)
   - May be missing entries (will truncate conflicting logs)
```

**Q4: Explain the split-brain problem and how Raft prevents it.**

**Split-brain**: Two leaders operating simultaneously

**Raft prevention**:
- Terms act as logical clocks
- Majority required for election
- Old leader's requests rejected by nodes with higher terms

```
┌─────────────────────────────────────────────────────────────────┐
│              SPLIT-BRAIN PREVENTION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Partition occurs:                                             │
│                                                                 │
│  [A, B]                    │    [C, D, E]                      │
│  Leader A (term 1)         │    New election → Leader C        │
│                            │    (term 2)                        │
│                            │                                    │
│  A cannot get majority     │    C gets majority (3/5)          │
│  (only 2/5)                │                                    │
│                            │                                    │
│  When partition heals:                                         │
│  A sees higher term from C → A steps down to follower          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Design Questions

**Q5: Design a distributed lock service using Raft.**

```
Lock Service Design:
├── State Machine
│   └── Map<LockName, Owner>
├── Operations
│   ├── Acquire(lockName, clientId, timeout)
│   ├── Release(lockName, clientId)
│   └── Renew(lockName, clientId, timeout)
├── Safety
│   ├── Fencing token (version number)
│   └── Lease expiration
└── High Availability
    └── Leader election via Raft
```

**Q6: How would you implement leader election without a consensus algorithm?**

**Simple approach (Bully algorithm)**:
1. Each node has a unique ID
2. Node with highest ID becomes leader
3. If leader fails, next highest becomes leader
4. Problem: No partition tolerance, can have multiple leaders

**Better approach**: Use consensus algorithm or existing service (etcd, Zookeeper)

---

## Summary

### Key Takeaways

1. **Consensus is fundamental**: Required for leader election, atomic broadcast, state machine replication

2. **FLP impossibility**: Perfect consensus impossible in async systems with failures

3. **Paxos vs Raft**:
   - Paxos: Theoretically elegant, hard to implement
   - Raft: Designed for understandability, widely implemented

4. **Byzantine vs Crash failures**:
   - Crash: 2f+1 nodes, simpler
   - Byzantine: 3f+1 nodes, more complex

5. **Choose based on requirements**:
   - Trust nodes? → Raft
   - Need Byzantine tolerance? → PBFT
   - Existing system? → Use its native consensus

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSENSUS CHEAT SHEET                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Crash Tolerance:                                              │
│  ─────────────────                                             │
│  Nodes needed: 2f + 1 (tolerate f failures)                   │
│  Quorum: majority (f + 1)                                      │
│  Algorithms: Paxos, Raft, Zab                                  │
│                                                                 │
│  Byzantine Tolerance:                                          │
│  ───────────────────                                           │
│  Nodes needed: 3f + 1 (tolerate f Byzantine)                  │
│  Quorum: 2f + 1                                                │
│  Algorithms: PBFT, Tendermint                                  │
│                                                                 │
│  Production Systems:                                           │
│  ──────────────────                                            │
│  etcd, Consul → Raft                                           │
│  Zookeeper → Zab                                               │
│  Blockchains → PBFT variants                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
