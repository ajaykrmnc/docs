# Chapter 8: The Trouble with Distributed Systems

## Table of Contents

1. [Faults and Partial Failures](#faults-and-partial-failures)
2. [Unreliable Networks](#unreliable-networks)
3. [Unreliable Clocks](#unreliable-clocks)
4. [Knowledge, Truth, and Lies](#knowledge-truth-and-lies)
5. [System Models and Reality](#system-models-and-reality)
6. [Interview Questions](#interview-questions)

---

## Faults and Partial Failures

```
┌─────────────────────────────────────────────────────────────────┐
│              SINGLE MACHINE vs DISTRIBUTED SYSTEM                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SINGLE MACHINE:                                                │
│  • Deterministic: same operation → same result                 │
│  • Either works correctly or fails completely                  │
│  • Hardware fault → total failure (crash, bluescreen)          │
│  • Software bugs are usually reproducible                       │
│                                                                 │
│  DISTRIBUTED SYSTEM:                                            │
│  • NON-DETERMINISTIC: same operation may succeed or fail        │
│  • PARTIAL FAILURE: some parts work, some don't                │
│  • You may not even KNOW if something succeeded                │
│  • Failures are often not reproducible                         │
│                                                                 │
│  The defining characteristic: PARTIAL FAILURES that are         │
│  non-deterministic. This makes distributed systems              │
│  fundamentally harder to reason about.                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Unreliable Networks

Distributed systems communicate via **asynchronous packet networks** (e.g., Ethernet, TCP/IP). The network is
fundamentally unreliable.

```
┌─────────────────────────────────────────────────────────────────┐
│              WHAT CAN GO WRONG WITH A NETWORK REQUEST           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Node A ──request──► Node B                                     │
│                                                                 │
│  1. Request LOST (dropped by network)                           │
│  2. Request QUEUED (sitting in a switch buffer, delivered late) │
│  3. Node B CRASHED (received request but can't process)        │
│  4. Node B PAUSED (GC pause, busy processing other requests)   │
│  5. Response LOST (B processed it but reply was dropped)       │
│  6. Response QUEUED (reply delayed in the network)             │
│                                                                 │
│       ┌────┐    ?????    ┌────┐                                │
│       │ A  │──────────►  │ B  │                                │
│       └────┘             └────┘                                │
│         ▲                                                       │
│         │  A sent request. No response. What happened?          │
│         │  A CANNOT DISTINGUISH between these cases.            │
│         │                                                       │
│         └── The only information A has is:                      │
│             "I haven't received a response yet."                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Timeouts and Unbounded Delays

```
┌─────────────────────────────────────────────────────────────────┐
│              THE TIMEOUT DILEMMA                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  How long should A wait before declaring B dead?                │
│                                                                 │
│  TIMEOUT TOO SHORT:                                             │
│  • Declares nodes dead that are merely slow                     │
│  • Unnecessary failovers                                       │
│  • Extra load (transferred actions + retries) can cause         │
│    CASCADING FAILURES (node was slow due to overload, now      │
│    we've moved its work to OTHER nodes which also overload!)   │
│                                                                 │
│  TIMEOUT TOO LONG:                                              │
│  • Long wait before a dead node is declared dead                │
│  • Users see errors or stale data while waiting                │
│                                                                 │
│  NO "CORRECT" TIMEOUT VALUE:                                    │
│  Network delays are UNBOUNDED — a packet might take 1ms         │
│  or 1 minute. You can only choose a trade-off.                  │
│                                                                 │
│  Practical approach:                                            │
│  • Measure the distribution of network round-trip times         │
│  • Consider the application's requirements                      │
│  • Use an adaptive timeout (like TCP's retransmission timeout  │
│    which adjusts based on observed RTT variance)               │
│  • Phi Accrual failure detector (Akka, Cassandra)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Network Congestion and Queueing

```
┌─────────────────────────────────────────────────────────────────┐
│              WHERE DO NETWORK DELAYS COME FROM?                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. NETWORK SWITCH QUEUE                                        │
│     Switch buffer full → packets DROPPED (need retransmission) │
│                                                                 │
│  2. OS RECEIVE BUFFER                                           │
│     Destination CPU is busy → packets queue in OS buffer        │
│                                                                 │
│  3. VM MONITOR QUEUE                                            │
│     In virtualized environments, the hypervisor pauses VMs      │
│     to let other VMs run → incoming packets buffer              │
│                                                                 │
│  4. TCP FLOW CONTROL                                            │
│     Sender throttled if receiver can't keep up                  │
│     (TCP window, congestion avoidance)                          │
│                                                                 │
│  5. TCP RETRANSMISSION                                          │
│     Lost packet → retransmit after timeout (seconds!)          │
│                                                                 │
│  In public clouds (AWS, GCP), you share network with            │
│  other tenants → noisy neighbors cause variable delays.         │
│                                                                 │
│  On a single datacenter Ethernet: <1ms typical                  │
│  Congested network / cloud: can exceed 100ms or seconds         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Unreliable Clocks

Each machine has its own clock (quartz oscillator). Clocks drift: faster or slower than real time.

### Time-of-Day Clocks vs. Monotonic Clocks

```
┌──────────────────────────────────────────────────────────────────┐
│              TWO KINDS OF CLOCKS                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIME-OF-DAY CLOCK:                                              │
│  • Returns wall-clock time (e.g., 2024-03-15 14:23:05.123)     │
│  • Synchronized with NTP (Network Time Protocol)                │
│  • Can JUMP forwards or backwards (NTP correction!)             │
│  • Coarse resolution (often ~millisecond)                       │
│  • System.currentTimeMillis() (Java), time.time() (Python)     │
│  • BAD for measuring elapsed time (may jump during measurement)│
│                                                                  │
│  MONOTONIC CLOCK:                                                │
│  • Guaranteed to always move forward                             │
│  • Only the DIFFERENCE between two readings is meaningful       │
│  • Not synchronized across machines                              │
│  • Fine resolution (nanosecond on modern systems)               │
│  • System.nanoTime() (Java), clock_gettime(CLOCK_MONOTONIC)    │
│  • GOOD for measuring elapsed time (timeouts, benchmarks)      │
│  • The absolute value is meaningless (arbitrary epoch)          │
│                                                                  │
│  RULE: Use monotonic clocks for measuring durations.            │
│        Use time-of-day clocks only when you need wall time.    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Clock Synchronization Problems (NTP)

```
┌──────────────────────────────────────────────────────────────────┐
│              NTP CLOCK SYNCHRONIZATION ISSUES                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  • Quartz clock DRIFT: up to 200 ppm (parts per million)       │
│    = 6 seconds per month = 17 seconds per day in worst case    │
│                                                                  │
│  • NTP accuracy: ~35ms over the internet, <1ms on LAN          │
│    But can be much worse with network congestion                │
│                                                                  │
│  • NTP can JUMP the clock forward or backward                   │
│    (step correction, not just rate adjustment)                  │
│                                                                  │
│  • Leap seconds: occasionally a minute has 61 seconds           │
│    Has caused outages (e.g., Reddit, 2012)                     │
│                                                                  │
│  • Virtualization: VM pause freezes the clock; when resumed,   │
│    the clock jumps forward suddenly                             │
│                                                                  │
│  • Firewall may block NTP traffic → no synchronization         │
│                                                                  │
│  CONSEQUENCE: You cannot assume two machines' clocks are        │
│  in sync. Even a "small" difference of 100ms can cause bugs.  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Timestamps for Ordering Events — A Dangerous Assumption

```
┌──────────────────────────────────────────────────────────────────┐
│              LAST WRITE WINS (LWW) — DANGER!                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Node A writes x=1 at timestamp t=42.004s (A's clock)          │
│  Node B writes x=2 at timestamp t=42.001s (B's clock)          │
│                                                                  │
│  LWW picks the "latest" timestamp → x=1 wins                   │
│                                                                  │
│  But B's write ACTUALLY happened AFTER A's write!               │
│  B's clock was just 3ms behind A's clock.                       │
│                                                                  │
│  Node A:  ──────[write x=1]───────────────────────►             │
│  Node B:  ─────────────[write x=2]────────────────►             │
│                         ▲ Actually later, but clock is behind   │
│                                                                  │
│  LWW silently drops B's write. Data loss with no error!         │
│                                                                  │
│  This is a REAL problem in Cassandra, DynamoDB, Riak.           │
│  The "winning" write is determined by clock skew, not causality.│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Logical Clocks (Lamport Timestamps)

```
┌──────────────────────────────────────────────────────────────────┐
│              LAMPORT TIMESTAMPS                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Instead of physical time, use a LOGICAL COUNTER:               │
│                                                                  │
│  Each node maintains a counter. On each event:                  │
│  1. Increment own counter                                        │
│  2. Attach counter to messages                                   │
│  3. On receiving a message: counter = max(own, received) + 1   │
│                                                                  │
│  Node A:  1 ──► 2 ──────────────────► 5 ──► 6                  │
│                   \                  /                            │
│  Node B:       1 ──► 3 ──► 4 ──► 5                              │
│                                                                  │
│  Lamport timestamps give TOTAL ORDER of events.                 │
│  If event A happened before event B, then                       │
│  timestamp(A) < timestamp(B).                                   │
│                                                                  │
│  But: If timestamp(A) < timestamp(B), A did NOT necessarily     │
│  happen before B! (They might be concurrent.)                   │
│  For true causal ordering → need VECTOR CLOCKS.                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Knowledge, Truth, and Lies

### The Truth Is Defined by the Majority

```
┌──────────────────────────────────────────────────────────────────┐
│              TRUTH BY MAJORITY (QUORUM)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A node cannot trust its OWN assessment of its status.          │
│                                                                  │
│  Example: Node A has a GC pause for 15 seconds.                 │
│  • Node A thinks: "I'm fine, just processing a request."        │
│  • All other nodes think: "Node A is dead (no heartbeat)."     │
│  • The other nodes are RIGHT. Node A's lease has expired.      │
│    If A continues acting as leader → SPLIT BRAIN.              │
│                                                                  │
│  SOLUTION: Decisions require votes from a QUORUM (majority).   │
│  A node that claims "I'm the leader" must have agreement        │
│  from a majority of nodes. A single node can't unilaterally    │
│  decide anything in a distributed system.                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Process Pauses

```
┌──────────────────────────────────────────────────────────────────┐
│              PROCESS PAUSES                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A process can be paused for an extended time:                  │
│                                                                  │
│  • GC pause (Java, Go, .NET): can be 100ms to several SECONDS │
│    — "stop-the-world" pauses freeze the entire process          │
│  • VM migration (live migration): hypervisor pauses VM          │
│  • OS swapping (thrashing): process waiting for disk I/O       │
│  • Ctrl+Z (SIGSTOP): process suspended by operator             │
│  • Context switches: CPU taken away by scheduler               │
│                                                                  │
│  During a pause, the process has NO IDEA it was paused.        │
│  It resumes and thinks no time has passed.                      │
│                                                                  │
│  This is why LEASE-BASED approaches are dangerous:             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Node obtains lease (valid for 10 seconds)             │   │
│  │ 2. Node starts processing (has 10s)                      │   │
│  │ 3. GC pause for 15 seconds                               │   │
│  │ 4. Node resumes — LEASE HAS EXPIRED but node doesn't    │   │
│  │    know it. Another node became leader!                   │   │
│  │ 5. Node continues writing → DATA CORRUPTION             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Fencing Tokens

```
┌──────────────────────────────────────────────────────────────────┐
│              FENCING TOKENS                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Solution to the expired-lease problem:                         │
│                                                                  │
│  Lock service issues a MONOTONICALLY INCREASING token           │
│  with each lease grant.                                         │
│                                                                  │
│  ┌──────┐ acquires lock (token=33) ┌────────────┐              │
│  │Node 1│──────────────────────────│Lock Service│              │
│  └──┬───┘                          └──────┬─────┘              │
│     │                                      │                    │
│     │ (GC pause...)                        │                    │
│     │                              ┌──────┐│                   │
│     │                              │Node 2││ acquires lock     │
│     │                              └──┬───┘│ (token=34)        │
│     │                                 │    │                    │
│     │ write(token=33) ──►  ┌──────────┴────┴───┐               │
│     │                      │    Storage        │               │
│     │                      │                    │               │
│     │                      │ Rejects token=33   │               │
│     │                      │ because it already │               │
│     │                      │ saw token=34       │               │
│     │                      └───────────────────┘               │
│                                                                  │
│  Storage server rejects writes with OLD fencing tokens.         │
│  Requires storage to CHECK the token on every write.            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Byzantine Faults

```
┌──────────────────────────────────────────────────────────────────┐
│              BYZANTINE FAULTS                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  All the problems above assume nodes are HONEST but may fail.   │
│                                                                  │
│  BYZANTINE FAULT: A node may LIE — send contradictory or       │
│  fabricated messages to other nodes.                            │
│                                                                  │
│  Relevant in:                                                    │
│  • Aerospace (radiation may flip bits in CPU)                   │
│  • Blockchain / cryptocurrency (nodes don't trust each other)  │
│  • Systems with multiple organizations (no mutual trust)       │
│                                                                  │
│  Most database systems ASSUME no Byzantine faults.              │
│  It's too expensive to tolerate. Instead:                       │
│  • Use checksums to detect corrupted data                       │
│  • Use TLS/authentication to verify message authenticity       │
│  • Sanitize inputs from users                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## System Models and Reality

```
┌──────────────────────────────────────────────────────────────────┐
│              SYSTEM MODELS                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIMING ASSUMPTIONS:                                             │
│  ─────────────────                                               │
│  Synchronous:        Known upper bound on network delay         │
│                      and process pauses. UNREALISTIC.            │
│                                                                  │
│  Partially sync:     Usually behaves like synchronous,          │
│                      but occasionally exceeds bounds.            │
│                      REALISTIC model for most systems.          │
│                                                                  │
│  Asynchronous:       No timing assumptions at all.              │
│                      No timeouts possible (can't tell           │
│                      slow from crashed). Very restrictive.      │
│                                                                  │
│  NODE FAILURE MODELS:                                            │
│  ──────────────────                                              │
│  Crash-stop:         Node crashes and never comes back.         │
│                                                                  │
│  Crash-recovery:     Node crashes but may restart later         │
│                      with stable storage intact.                 │
│                      MOST REALISTIC for real systems.           │
│                                                                  │
│  Byzantine:          Node may behave arbitrarily (including     │
│                      maliciously). Hardest to handle.           │
│                                                                  │
│  MOST PRACTICAL MODEL:                                          │
│  Partially synchronous + crash-recovery                         │
│  This is what most distributed algorithms assume.               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: Why can't you simply use a timeout to detect node failure?

In an asynchronous network, there is no upper bound on message delivery time. A node might be alive but experiencing a
long GC pause, network congestion, or VM migration. A short timeout causes false positives (declaring live nodes dead),
which can trigger unnecessary failovers and even cascading failures (overloading other nodes with the "dead" node's
work). A long timeout means genuine failures take too long to detect. There is no perfect timeout — only trade-offs
between speed of detection and false positive rate.

### Q2: Why are physical clocks unreliable for ordering events in distributed systems?

Each machine's clock drifts independently (up to 200 ppm). NTP synchronization provides at best ~35ms accuracy over the
internet. NTP can jump clocks forward or backward. GC pauses and VM suspensions can freeze a process while its clock
advances. Using physical timestamps for Last-Write-Wins (LWW) ordering means clock skew between nodes silently
determines which writes survive — leading to data loss. Instead, use logical clocks (Lamport timestamps, vector clocks)
for causal ordering.

### Q3: What are fencing tokens and why are they needed?

Fencing tokens solve the problem of expired leases after process pauses. When a lock/lease is granted, the lock service
issues a monotonically increasing token number. Every write to the storage system must include the token. The storage
server rejects writes with a token lower than the highest token it has already seen. This prevents a node that held an
old lease (and experienced a long pause) from making writes that conflict with the new leaseholder.

### Q4: What is a Byzantine fault?

A Byzantine fault is when a node not only crashes but acts **maliciously** — sending contradictory, fabricated, or
incorrect messages. Named after the Byzantine Generals Problem. Most database systems don't try to tolerate Byzantine
faults (it requires 3f+1 nodes to tolerate f Byzantine nodes). Byzantine fault tolerance is mainly relevant for
blockchain/cryptocurrency systems, aerospace (bit-flip protection), and multi-party computation where nodes don't trust
each other.

### Q5: What is the most realistic system model for distributed databases?

**Partially synchronous timing + crash-recovery failure model**. Partially synchronous means the system usually meets
timing bounds but occasionally exceeds them (realistic for networks and OS scheduling). Crash-recovery means nodes can
crash and restart with their persistent storage intact (realistic for servers with SSDs/HDDs). This model is assumed by
most practical distributed algorithms (Raft, Paxos, etc.).

---

_Based on Chapter 8 of "Designing Data-Intensive Applications" by Martin Kleppmann_
