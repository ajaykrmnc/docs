# Clocks and Time in Distributed Systems

## Table of Contents
1. [The Time Problem](#the-time-problem)
2. [Physical Clocks](#physical-clocks)
3. [Logical Clocks](#logical-clocks)
4. [Vector Clocks](#vector-clocks)
5. [Hybrid Logical Clocks](#hybrid-logical-clocks)
6. [Time Synchronization Protocols](#time-synchronization-protocols)
7. [Real-World Applications](#real-world-applications)
8. [Interview Questions](#interview-questions)

---

## The Time Problem

### Why is Time Hard in Distributed Systems?

```
┌─────────────────────────────────────────────────────────────────┐
│              THE TIME PROBLEM                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  In a single machine:                                          │
│  • One clock, events naturally ordered                         │
│  • If A happens before B, clock(A) < clock(B)                 │
│                                                                 │
│  In a distributed system:                                      │
│  • Each node has its own clock                                 │
│  • Clocks drift at different rates                             │
│  • Network delays are unpredictable                            │
│  • No global notion of "now"                                   │
│                                                                 │
│  ┌─────────┐              ┌─────────┐                         │
│  │ Node A  │              │ Node B  │                         │
│  │ 10:00:00│              │ 10:00:03│   ← 3 second difference!│
│  └────┬────┘              └────┬────┘                         │
│       │                        │                               │
│       │   "What time is it?"   │                               │
│       │       Who's right?     │                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Does Order Matter?

```
┌─────────────────────────────────────────────────────────────────┐
│              ORDERING PROBLEM EXAMPLE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Bank Account Balance: $100                                    │
│                                                                 │
│  Node A (clock: 10:00:05): Deposit $50                        │
│  Node B (clock: 10:00:03): Withdraw $80                       │
│                                                                 │
│  Real world order:                                             │
│  1. Deposit happened FIRST (actually at real time 10:00:01)   │
│  2. Withdraw happened SECOND (actually at real time 10:00:02) │
│                                                                 │
│  If we use timestamps:                                         │
│  • B's withdraw appears first (10:00:03 < 10:00:05)          │
│  • System thinks: $100 - $80 = $20, then $20 + $50 = $70     │
│                                                                 │
│  Correct order:                                                │
│  • A's deposit first                                          │
│  • System should: $100 + $50 = $150, then $150 - $80 = $70   │
│                                                                 │
│  Same final balance by luck, but wrong intermediate states!    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Happened-Before Relation

Leslie Lamport's **happened-before** (→) relation:

```
┌─────────────────────────────────────────────────────────────────┐
│              HAPPENED-BEFORE RELATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Event A "happened before" Event B (A → B) if:                 │
│                                                                 │
│  1. A and B are in the same process, A comes before B          │
│                                                                 │
│  2. A is send of message, B is receive of same message         │
│                                                                 │
│  3. Transitivity: If A → B and B → C, then A → C              │
│                                                                 │
│  CONCURRENT events: Neither A → B nor B → A                    │
│  (Cannot determine order)                                      │
│                                                                 │
│  Process 1:  a ─────────► b ─────────► c                      │
│                    ╲             ╱                              │
│                     ╲  message  ╱                               │
│                      ╲        ╱                                 │
│  Process 2:           d ────► e ─────────► f                  │
│                                                                 │
│  a → b → c (same process)                                      │
│  a → d (message send/receive)                                  │
│  d → e → f (same process)                                      │
│  a → e (transitivity: a → d → e)                              │
│  c ∥ f (concurrent: no causal path)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Physical Clocks

### Types of Physical Clocks

| Clock Type | Accuracy | Drift | Use Case |
|------------|----------|-------|----------|
| **Quartz** | ~1 sec/day | 10-100 ppm | Consumer devices |
| **Atomic** | 1 sec/million years | ~0.01 ppb | GPS satellites, time servers |
| **GPS** | ~10 nanoseconds | Depends on signal | Location-based systems |

### Clock Drift

```
┌─────────────────────────────────────────────────────────────────┐
│              CLOCK DRIFT                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Perfect Clock:    ────────────────────────────────►           │
│                    |       |       |       |       |           │
│                   t=0    t=1     t=2     t=3     t=4           │
│                                                                 │
│  Fast Clock:       ────────────────────────────────►           │
│  (drift > 0)       |     |     |     |     |                   │
│                   t=0  t=1   t=2   t=3   t=4                   │
│                                                                 │
│  Slow Clock:       ────────────────────────────────►           │
│  (drift < 0)       |         |         |         |             │
│                   t=0       t=1       t=2       t=3            │
│                                                                 │
│  Drift rate: 50 ppm = 50 microseconds per second              │
│             = 4.32 seconds per day                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Clock Skew

**Clock skew** is the difference between two clocks at a given instant.


---

## Logical Clocks

### Lamport Clocks

**Lamport clocks** (1978) capture the happened-before relation without physical time.

```
┌─────────────────────────────────────────────────────────────────┐
│              LAMPORT CLOCK RULES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Each process maintains a counter C:                           │
│                                                                 │
│  RULE 1: Before each event, increment counter                  │
│          C = C + 1                                             │
│                                                                 │
│  RULE 2: When sending message, include counter                 │
│          send(message, C)                                      │
│                                                                 │
│  RULE 3: When receiving message with timestamp t:              │
│          C = max(C, t) + 1                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Lamport Clock Example

```
┌─────────────────────────────────────────────────────────────────┐
│              LAMPORT CLOCK EXAMPLE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Process P1:    (1)────────(2)────────(5)────────(6)          │
│                            ╲                                    │
│                             ╲ m1                                │
│                              ╲                                  │
│  Process P2:    (1)────────(3)────────(4)                     │
│                             ╲                                   │
│                              ╲ m2                               │
│                               ╲                                 │
│  Process P3:    (1)────────(2)────────(5)                     │
│                                                                 │
│  Event flow:                                                   │
│  • P1 sends m1 at C=2, P2 receives: C = max(1,2)+1 = 3       │
│  • P2 sends m2 at C=4, P3 receives: C = max(2,4)+1 = 5       │
│  • P1 event at C=5: C = max(2)+1, then m1 returns... = 5     │
│                                                                 │
│  Key insight: If A → B, then C(A) < C(B)                      │
│  But NOT: If C(A) < C(B), then A → B                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Lamport Clock Limitations

```
┌─────────────────────────────────────────────────────────────────┐
│              LAMPORT CLOCK LIMITATIONS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Problem: Cannot detect concurrent events                      │
│                                                                 │
│  P1:  ──(1)──────(2)──                                        │
│                                                                 │
│  P2:  ──(1)──────(2)──                                        │
│                                                                 │
│  Both have timestamp 2, but are they:                          │
│  • The same event?                                             │
│  • Concurrent events?                                          │
│  • One happened before the other?                              │
│                                                                 │
│  CANNOT TELL with Lamport clocks alone!                       │
│                                                                 │
│  Need: Vector Clocks                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Vector Clocks

### Overview

**Vector clocks** extend Lamport clocks to capture the complete happened-before relation and detect concurrent events.

```
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR CLOCK STRUCTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For N processes, each maintains vector of N counters:         │
│                                                                 │
│  Process i: VC[i] = [c1, c2, c3, ..., cn]                     │
│                                                                 │
│  • VC[i][i] = number of events at process i                   │
│  • VC[i][j] = latest known event count from process j         │
│                                                                 │
│  Example (3 processes):                                        │
│  P1's vector: [3, 2, 1]                                       │
│  • P1 has had 3 events                                         │
│  • P1 knows P2 had at least 2 events                          │
│  • P1 knows P3 had at least 1 event                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Vector Clock Rules

```
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR CLOCK RULES                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RULE 1: LOCAL EVENT at process i                              │
│          VC[i][i] = VC[i][i] + 1                              │
│                                                                 │
│  RULE 2: SEND MESSAGE from process i                           │
│          VC[i][i] = VC[i][i] + 1                              │
│          Send (message, VC[i])                                 │
│                                                                 │
│  RULE 3: RECEIVE MESSAGE at process i with vector VCmsg       │
│          VC[i] = max(VC[i], VCmsg) element-wise               │
│          VC[i][i] = VC[i][i] + 1                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Vector Clock Example

```
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR CLOCK EXAMPLE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  P1: [1,0,0]───[2,0,0]──────────────[3,2,0]───[4,2,0]        │
│                    │                   ▲                       │
│                    │ m1                │ m3                    │
│                    ▼                   │                       │
│  P2: [0,1,0]───[2,2,0]───[2,3,0]────[2,4,0]                  │
│                           │                                    │
│                           │ m2                                 │
│                           ▼                                    │
│  P3: [0,0,1]─────────[2,3,2]───[2,3,3]                       │
│                                                                 │
│  Analysis:                                                     │
│  • m1: P1[2,0,0] → P2: max([0,1,0],[2,0,0])+1 = [2,2,0]      │
│  • m2: P2[2,3,0] → P3: max([0,0,1],[2,3,0])+1 = [2,3,2]      │
│  • m3: P2[2,4,0] → P1: max([2,0,0],[2,4,0])+1 = [3,2,0]      │
│                           (wait, should be [3,4,0])           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparing Vector Clocks

```
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR CLOCK COMPARISON                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Given vectors A and B:                                        │
│                                                                 │
│  A = B:       All elements equal                               │
│               A[i] = B[i] for all i                            │
│                                                                 │
│  A < B:       A[i] ≤ B[i] for all i, AND                      │
│  (A → B)      A[j] < B[j] for at least one j                  │
│                                                                 │
│  A ∥ B:       Neither A < B nor B < A                         │
│  (concurrent) (Some A[i] > B[i], some A[j] < B[j])            │
│                                                                 │
│  Examples:                                                     │
│  [1,2,3] < [1,2,4]  ✓  (happened-before)                      │
│  [1,2,3] < [2,3,4]  ✓  (happened-before)                      │
│  [1,2,3] ∥ [2,1,3]  ✓  (concurrent: 1<2 but 2>1)             │
│  [1,2,3] ∥ [0,3,4]  ✓  (concurrent: 1>0 but 2<3)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Vector Clocks vs Lamport Clocks

| Property | Lamport Clock | Vector Clock |
|----------|--------------|--------------|
| Size | Single integer | N integers |
| Happens-before detection | If A→B then C(A)<C(B) | Bidirectional |
| Concurrency detection | No | Yes |
| Scalability | O(1) | O(N) |
| Use case | Total ordering | Causality tracking |

---

## Hybrid Logical Clocks

### Overview

**Hybrid Logical Clocks (HLC)** combine physical time with logical clocks to get benefits of both.

```
┌─────────────────────────────────────────────────────────────────┐
│              HYBRID LOGICAL CLOCK                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HLC = (physical_time, logical_counter)                        │
│                                                                 │
│  Properties:                                                   │
│  • Close to physical time (bounded drift)                      │
│  • Captures causality like Lamport clocks                     │
│  • Compact (2 values vs N for vector clocks)                  │
│                                                                 │
│  Format: (pt, lc)                                              │
│  • pt: physical time component                                 │
│  • lc: logical counter for same pt value                      │
│                                                                 │
│  Example:                                                      │
│  (1000, 0) < (1000, 1) < (1001, 0) < (1001, 5)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### HLC Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│              HLC ALGORITHM                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Local variables: l (last pt), c (counter)                     │
│                                                                 │
│  SEND/LOCAL EVENT:                                             │
│  ──────────────────                                            │
│  l' = l                                                        │
│  l = max(l', pt)  // pt = current physical time               │
│  if (l == l'):                                                 │
│      c = c + 1                                                 │
│  else:                                                         │
│      c = 0                                                     │
│  return (l, c)                                                 │
│                                                                 │
│  RECEIVE EVENT (with message timestamp l_m, c_m):              │
│  ─────────────────────────────────────────────                 │
│  l' = l                                                        │
│  l = max(l', l_m, pt)                                         │
│  if (l == l' == l_m):                                         │
│      c = max(c, c_m) + 1                                      │
│  else if (l == l'):                                            │
│      c = c + 1                                                 │
│  else if (l == l_m):                                           │
│      c = c_m + 1                                               │
│  else:                                                         │
│      c = 0                                                     │
│  return (l, c)                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Time Synchronization Protocols

### Network Time Protocol (NTP)

```
┌─────────────────────────────────────────────────────────────────┐
│              NTP (NETWORK TIME PROTOCOL)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                              Server                    │
│    │                                    │                      │
│    │────── Request (t1) ───────────────►│                      │
│    │                                    │ t2 (receive)         │
│    │                                    │ t3 (send)            │
│    │◄───── Response (t2, t3) ──────────│                      │
│    │                                    │                      │
│    ▼ t4 (receive)                                              │
│                                                                 │
│  Round-trip delay: δ = (t4 - t1) - (t3 - t2)                  │
│  Clock offset:     θ = ((t2 - t1) + (t3 - t4)) / 2            │
│                                                                 │
│  Accuracy: 1-50 ms over internet                               │
│           <1 ms on LAN                                         │
│                                                                 │
│  Stratum hierarchy:                                            │
│  • Stratum 0: Atomic clocks, GPS receivers                    │
│  • Stratum 1: Directly connected to Stratum 0                 │
│  • Stratum 2: Sync to Stratum 1                               │
│  • ...                                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Precision Time Protocol (PTP)

```
┌─────────────────────────────────────────────────────────────────┐
│              PTP (IEEE 1588)                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  More precise than NTP:                                        │
│  • Sub-microsecond accuracy                                    │
│  • Hardware timestamping                                       │
│  • Used in financial trading, telecom                          │
│                                                                 │
│  Master                              Slave                     │
│    │                                   │                       │
│    │──── Sync (t1) ───────────────────►│                       │
│    │──── Follow_Up (t1) ──────────────►│  t2 (receive)        │
│    │                                   │                       │
│    │◄─── Delay_Req ───────────────────│  t3                   │
│    │──── Delay_Resp (t4) ─────────────►│                       │
│    │                                   │                       │
│                                                                 │
│  Offset = ((t2 - t1) - (t4 - t3)) / 2                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Google TrueTime

```
┌─────────────────────────────────────────────────────────────────┐
│              GOOGLE TRUETIME                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Instead of single timestamp, returns interval:                │
│                                                                 │
│  TT.now() → [earliest, latest]                                │
│                                                                 │
│  ◄────── ε ──────►                                             │
│  │               │                                              │
│  earliest   TRUE  latest                                       │
│             TIME                                                │
│                                                                 │
│  Guarantees:                                                   │
│  • True time is within interval                                │
│  • ε typically 1-7 milliseconds                                │
│                                                                 │
│  Used in Spanner for:                                          │
│  • External consistency                                        │
│  • Lock-free read-only transactions                            │
│  • Commit-wait: wait 2ε before commit visible                 │
│                                                                 │
│  Implementation:                                               │
│  • GPS receivers + atomic clocks in data centers              │
│  • Time masters in each data center                           │
│  • Clients poll multiple masters                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Real-World Applications

### System Usage of Clocks

| System | Clock Type | Purpose |
|--------|-----------|---------|
| **DynamoDB** | Vector clocks | Conflict detection |
| **Cassandra** | Timestamps (LWW) | Last-write-wins |
| **Spanner** | TrueTime | External consistency |
| **CockroachDB** | HLC | Serializable transactions |
| **Riak** | Vector clocks | Sibling resolution |

### Version Vectors vs Vector Clocks

```
┌─────────────────────────────────────────────────────────────────┐
│         VERSION VECTORS vs VECTOR CLOCKS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  VECTOR CLOCKS:                                                │
│  • Track causality for events/messages                         │
│  • Updated on every event                                      │
│  • Size: O(number of processes)                                │
│                                                                 │
│  VERSION VECTORS:                                              │
│  • Track causality for data items                              │
│  • Updated on data modification                                │
│  • Size: O(number of replicas)                                 │
│  • Used in: Dynamo, Riak                                       │
│                                                                 │
│  Same algorithm, different granularity!                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: Why can't we just use physical clocks in distributed systems?**

Physical clocks have several problems:
- **Clock drift**: Different rates of drift
- **Clock skew**: Different times on different machines
- **Synchronization limits**: Best is microseconds, not nanoseconds
- **Leap seconds**: Occasional adjustments
- **Network delay**: Can't compare times across network

**Q2: What's the difference between Lamport clocks and vector clocks?**

| Aspect | Lamport Clock | Vector Clock |
|--------|--------------|--------------|
| If A→B | C(A) < C(B) | VC(A) < VC(B) |
| If C(A) < C(B) | Can't tell if A→B | A→B is guaranteed |
| Concurrent detection | No | Yes |
| Space | O(1) | O(N) |

**Q3: Explain happened-before relation.**

A → B (A happened before B) if:
1. A and B on same process, A occurred before B
2. A is a send, B is receive of same message
3. Transitivity: A→C and C→B implies A→B

Concurrent (A ∥ B): Neither A→B nor B→A

**Q4: How does Google Spanner achieve external consistency?**

1. **TrueTime API**: Returns interval [earliest, latest]
2. **Commit-wait**: Wait until latest time passes
3. **Guaranteed ordering**: If T1 commits before T2 starts, T1's timestamp < T2's timestamp
4. **Hardware support**: GPS + atomic clocks reduce uncertainty (ε)

### Design Questions

**Q5: Design a distributed counter that handles concurrent increments.**

```
Using Vector Clocks:

Node A: counter_A, VC_A
Node B: counter_B, VC_B

Increment at A:
1. counter_A++
2. VC_A[A]++

Merge (A and B meet):
1. If VC_A < VC_B: take B's counter
2. If VC_B < VC_A: take A's counter
3. If concurrent: counter = counter_A + counter_B
   VC = max(VC_A, VC_B)
```

**Q6: How would you implement Last-Write-Wins (LWW)?**

```
LWW Implementation:
1. Each write has timestamp (physical or logical)
2. On conflict, higher timestamp wins
3. Tie-breaker: node ID or random

Pros: Simple, deterministic
Cons: Can lose writes, requires synchronized clocks

Better alternative: CRDTs (e.g., LWW-Register)
```

---

## Summary

### Key Takeaways

1. **Physical clocks** are imprecise and drift; can't rely on them alone

2. **Lamport clocks** capture happened-before but can't detect concurrency

3. **Vector clocks** detect both causality and concurrency but don't scale

4. **HLC** combines physical and logical time efficiently

5. **TrueTime** uses hardware to bound clock uncertainty

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│              CLOCKS CHEAT SHEET                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAMPORT CLOCK:                                                │
│  • Single counter per process                                  │
│  • Rules: increment, max+1 on receive                         │
│  • A→B implies C(A)<C(B), not vice versa                      │
│                                                                 │
│  VECTOR CLOCK:                                                 │
│  • N counters per process                                      │
│  • Detects both causality and concurrency                     │
│  • A<B: all elements ≤, at least one <                        │
│                                                                 │
│  HLC (pt, lc):                                                 │
│  • Bounded from physical time                                  │
│  • Compact like Lamport, causality tracking                   │
│                                                                 │
│  TRUETIME [earliest, latest]:                                  │
│  • Hardware-backed intervals                                   │
│  • Commit-wait for external consistency                        │
│                                                                 │
│  HAPPENED-BEFORE (A→B):                                        │
│  1. Same process, A before B                                   │
│  2. A=send, B=receive of same message                         │
│  3. Transitive closure                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

