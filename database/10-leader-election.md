# Chapter 10: Leader Election

## Table of Contents
- [Introduction](#introduction)
- [Why Leader Election](#why-leader-election)
- [Bully Algorithm](#bully-algorithm)
- [Ring Election Algorithm](#ring-election-algorithm)
- [Consensus-Based Election](#consensus-based-election)
- [Split-Brain Prevention](#split-brain-prevention)
- [Summary](#summary)

---

## Introduction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEADER ELECTION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "In distributed systems, someone needs to make decisions.                  │
│   Leader election ensures exactly one node has that authority."             │
│                                                                             │
│  THE COORDINATION PROBLEM                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Without a leader, distributed decisions require:                     │  │
│  │                                                                       │  │
│  │  • Consensus on every operation (expensive)                           │  │
│  │  • Complex conflict resolution                                        │  │
│  │  • Risk of inconsistent decisions                                     │  │
│  │                                                                       │  │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐             │  │
│  │  │   Node A    │     │   Node B    │     │   Node C    │             │  │
│  │  │ "Do X now!" │     │ "Do Y now!" │     │ "Do Z now!" │             │  │
│  │  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘             │  │
│  │         │                   │                   │                     │  │
│  │         └───────────────────┴───────────────────┘                     │  │
│  │                         │                                             │  │
│  │                         ▼                                             │  │
│  │                    Who wins?                                          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WITH A LEADER                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  One node makes decisions, others follow:                             │  │
│  │                                                                       │  │
│  │                    ┌─────────────┐                                    │  │
│  │                    │   LEADER    │                                    │  │
│  │                    │  (Node A)   │                                    │  │
│  │                    └──────┬──────┘                                    │  │
│  │                           │                                           │  │
│  │            ┌──────────────┼──────────────┐                            │  │
│  │            ▼              ▼              ▼                            │  │
│  │     ┌───────────┐  ┌───────────┐  ┌───────────┐                      │  │
│  │     │ Follower  │  │ Follower  │  │ Follower  │                      │  │
│  │     │  Node B   │  │  Node C   │  │  Node D   │                      │  │
│  │     └───────────┘  └───────────┘  └───────────┘                      │  │
│  │                                                                       │  │
│  │  Simple, efficient, but leader is single point of failure            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Leader Election

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       WHY LEADER ELECTION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Leaders simplify many distributed systems problems:                         │
│                                                                             │
│  USE CASES                                                                  │
│  ═════════                                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  DATABASE REPLICATION                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Leader accepts writes, replicates to followers                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  Client ──write──▶ Leader ──replicate──▶ Follower 1            │  │  │
│  │  │                       │                                         │  │  │
│  │  │                       └──replicate──▶ Follower 2                │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  DISTRIBUTED LOCKS / LEASES                                           │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Leader grants locks, ensures mutual exclusion                  │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  TASK ASSIGNMENT                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Leader assigns work to workers, tracks completion              │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  CONSENSUS (Raft, Multi-Paxos)                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Leader proposes values, coordinates agreement                  │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ELECTION REQUIREMENTS                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Safety: At most one leader at a time                                 │  │
│  │          (No split-brain!)                                            │  │
│  │                                                                       │  │
│  │  Liveness: Eventually a leader is elected                             │  │
│  │            (System makes progress)                                    │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  ✗ Bad: Two leaders (split-brain)                               │  │  │
│  │  │                                                                 │  │  │
│  │  │     Leader A               │               Leader B             │  │  │
│  │  │        │                   │                  │                 │  │  │
│  │  │        ▼                  WALL               ▼                 │  │  │
│  │  │   "x = 5"                                 "x = 7"              │  │  │
│  │  │                                                                 │  │  │
│  │  │  Both think they're in charge → DATA CORRUPTION                │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Bully Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BULLY ALGORITHM                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The highest-ID node wins (like a playground bully)                          │
│                                                                             │
│  ASSUMPTIONS                                                                │
│  ═══════════                                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  • Each node has a unique ID (e.g., 1, 2, 3, ...)                    │  │
│  │  • Nodes can crash but don't behave maliciously                       │  │
│  │  • Messages are eventually delivered (synchronous system)             │  │
│  │  • Nodes know about all other nodes in the system                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  MESSAGE TYPES                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ELECTION:   "I'm starting an election"                               │  │
│  │  OK:         "I'm alive and have higher ID, I'll take over"          │  │
│  │  COORDINATOR: "I am the new leader"                                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ALGORITHM                                                                  │
│  ═════════                                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  When node P detects leader failure:                                  │  │
│  │                                                                       │  │
│  │  1. P sends ELECTION to all nodes with higher IDs                     │  │
│  │                                                                       │  │
│  │  2. If P receives OK from any higher node:                            │  │
│  │     └─ P waits for COORDINATOR message (higher node handles it)       │  │
│  │                                                                       │  │
│  │  3. If P receives no OK (timeout):                                    │  │
│  │     └─ P becomes leader, sends COORDINATOR to all                     │  │
│  │                                                                       │  │
│  │  When node receives ELECTION:                                         │  │
│  │  └─ Reply OK, then start own election                                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  EXAMPLE                                                                    │
│  ═══════                                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Nodes: 1, 2, 3, 4, 5 (5 was leader, now crashed)                     │  │
│  │                                                                       │  │
│  │  Step 1: Node 2 detects failure, starts election                      │  │
│  │  ─────────────────────────────────────────────────                    │  │
│  │                                                                       │  │
│  │    [2] ──ELECTION──▶ [3]                                              │  │
│  │    [2] ──ELECTION──▶ [4]                                              │  │
│  │    [2] ──ELECTION──▶ [5] (crashed, no response)                       │  │
│  │                                                                       │  │
│  │  Step 2: Higher nodes respond                                         │  │
│  │  ───────────────────────────                                          │  │
│  │                                                                       │  │
│  │    [2] ◀────OK────── [3]  (3 will start own election)                │  │
│  │    [2] ◀────OK────── [4]  (4 will start own election)                │  │
│  │                                                                       │  │
│  │  Step 3: Node 3 starts election                                       │  │
│  │  ───────────────────────────                                          │  │
│  │                                                                       │  │
│  │    [3] ──ELECTION──▶ [4]                                              │  │
│  │    [3] ──ELECTION──▶ [5] (crashed)                                    │  │
│  │    [3] ◀────OK────── [4]                                              │  │
│  │                                                                       │  │
│  │  Step 4: Node 4 starts election                                       │  │
│  │  ───────────────────────────                                          │  │
│  │                                                                       │  │
│  │    [4] ──ELECTION──▶ [5] (crashed, timeout)                           │  │
│  │    No OK received!                                                    │  │
│  │                                                                       │  │
│  │  Step 5: Node 4 becomes leader                                        │  │
│  │  ────────────────────────────                                         │  │
│  │                                                                       │  │
│  │    [4] ──COORDINATOR──▶ [1]                                           │  │
│  │    [4] ──COORDINATOR──▶ [2]                                           │  │
│  │    [4] ──COORDINATOR──▶ [3]                                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PROPERTIES                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ✓ Simple to understand and implement                                 │  │
│  │  ✓ Highest-ID node always wins                                        │  │
│  │                                                                       │  │
│  │  ✗ Worst case: O(n²) messages                                         │  │
│  │  ✗ Requires synchronous system (bounded delays)                       │  │
│  │  ✗ If highest-ID node is flaky → repeated elections                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Ring Election Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RING ELECTION ALGORITHM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Nodes arranged in a logical ring, pass election message around             │
│                                                                             │
│  TOPOLOGY                                                                   │
│  ════════                                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │              ┌─────┐                                                  │  │
│  │         ╱───▶│  1  │───╲                                              │  │
│  │       ╱      └─────┘     ╲                                            │  │
│  │     ╱                      ╲                                          │  │
│  │  ┌─────┐                ┌─────┐                                       │  │
│  │  │  5  │                │  2  │                                       │  │
│  │  └─────┘                └─────┘                                       │  │
│  │     ╲                      ╱                                          │  │
│  │       ╲      ┌─────┐     ╱                                            │  │
│  │         ╲───│  4  │◀──╱                                              │  │
│  │              └──┬──┘                                                  │  │
│  │                 │                                                     │  │
│  │              ┌──▼──┐                                                  │  │
│  │              │  3  │                                                  │  │
│  │              └─────┘                                                  │  │
│  │                                                                       │  │
│  │  Each node knows its successor in the ring                            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ALGORITHM                                                                  │
│  ═════════                                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  When node P detects leader failure:                                  │  │
│  │                                                                       │  │
│  │  1. P creates ELECTION message containing its ID                      │  │
│  │  2. P sends ELECTION message to successor                             │  │
│  │                                                                       │  │
│  │  When node receives ELECTION message with candidate list:             │  │
│  │                                                                       │  │
│  │  1. If own ID not in list:                                            │  │
│  │     └─ Add own ID to list, forward to successor                       │  │
│  │                                                                       │  │
│  │  2. If own ID IS in list (message went full circle):                  │  │
│  │     └─ Select highest ID as leader                                    │  │
│  │     └─ Send COORDINATOR message with leader ID                        │  │
│  │                                                                       │  │
│  │  When node receives COORDINATOR message:                              │  │
│  │  1. Set leader to indicated node                                      │  │
│  │  2. Forward COORDINATOR to successor (unless it started)              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  EXAMPLE                                                                    │
│  ═══════                                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Ring: 1 → 2 → 3 → 4 → 5 → 1  (Node 5 was leader, crashed)           │  │
│  │                                                                       │  │
│  │  Step 1: Node 2 starts election                                       │  │
│  │  ─────────────────────────────                                        │  │
│  │                                                                       │  │
│  │    [2] ──ELECTION{2}──▶ [3]                                           │  │
│  │                                                                       │  │
│  │  Step 2: Node 3 adds ID, forwards                                     │  │
│  │  ────────────────────────────                                         │  │
│  │                                                                       │  │
│  │    [3] ──ELECTION{2,3}──▶ [4]                                         │  │
│  │                                                                       │  │
│  │  Step 3: Node 4 adds ID, forwards                                     │  │
│  │  ────────────────────────────                                         │  │
│  │                                                                       │  │
│  │    [4] ──ELECTION{2,3,4}──▶ [5] (crashed!)                            │  │
│  │                                                                       │  │
│  │  Step 4: Timeout, skip 5, forward to 1                                │  │
│  │  ──────────────────────────────────────                               │  │
│  │                                                                       │  │
│  │    [4] ──ELECTION{2,3,4}──▶ [1]                                       │  │
│  │                                                                       │  │
│  │  Step 5: Node 1 adds ID, forwards to 2                                │  │
│  │  ─────────────────────────────────────                                │  │
│  │                                                                       │  │
│  │    [1] ──ELECTION{2,3,4,1}──▶ [2]                                     │  │
│  │                                                                       │  │
│  │  Step 6: Node 2 sees own ID - full circle!                            │  │
│  │  ──────────────────────────────────────────                           │  │
│  │                                                                       │  │
│  │    Highest ID = 4                                                     │  │
│  │    [2] ──COORDINATOR{4}──▶ [3] ──▶ [4] ──▶ [1] ──▶ [2]               │  │
│  │                                                                       │  │
│  │  Result: Node 4 is the new leader!                                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PROPERTIES                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ✓ Uses O(n) messages in best case (vs O(n²) for Bully)               │  │
│  │  ✓ Only needs to know successor (not all nodes)                       │  │
│  │                                                                       │  │
│  │  ✗ Slow: must traverse entire ring                                    │  │
│  │  ✗ If multiple nodes start elections simultaneously,                  │  │
│  │    multiple election messages circulate                               │  │
│  │  ✗ Node failure requires ring repair (find new successor)             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Consensus-Based Election

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CONSENSUS-BASED ELECTION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Use consensus protocols (Paxos, Raft) to elect leader                       │
│                                                                             │
│  WHY CONSENSUS?                                                             │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Problem with Bully/Ring: Assume synchronous system                   │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Synchronous:   Bounded message delays                          │  │  │
│  │  │                 Can use timeouts to detect failure              │  │  │
│  │  │                                                                 │  │  │
│  │  │  Asynchronous:  Unbounded delays                                │  │  │
│  │  │                 Cannot distinguish slow from failed             │  │  │
│  │  │                                                                 │  │  │
│  │  │  Real systems are partially synchronous:                        │  │  │
│  │  │  Usually fast, occasionally slow                                │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Consensus protocols handle partial synchrony safely!                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  RAFT LEADER ELECTION (Example)                                             │
│  ═══════════════════════════════                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Terms: Logical clock that increases with each election               │  │
│  │                                                                       │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                    │  │
│  │  │Term 1│  │Term 2│  │Term 3│  │Term 4│  │Term 5│  ...               │  │
│  │  │Leader│  │Leader│  │Leader│  │Leader│  │Leader│                    │  │
│  │  │  A   │  │  B   │  │ None │  │  C   │  │  C   │                    │  │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘                    │  │
│  │   normal   election   failed    election  normal                      │  │
│  │                       election                                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ELECTION PROCESS IN RAFT                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  States:                                                              │  │
│  │  ┌──────────┐    ┌───────────┐    ┌──────────┐                        │  │
│  │  │ Follower │───▶│ Candidate │───▶│  Leader  │                        │  │
│  │  └──────────┘    └───────────┘    └──────────┘                        │  │
│  │       ▲               │                │                              │  │
│  │       │               │                │                              │  │
│  │       └───────────────┴────────────────┘                              │  │
│  │              (discover higher term)                                   │  │
│  │                                                                       │  │
│  │  Election Trigger:                                                    │  │
│  │  ─────────────────                                                    │  │
│  │  Follower hasn't heard from leader in election_timeout                │  │
│  │                                                                       │  │
│  │  1. Increment current term                                            │  │
│  │  2. Transition to Candidate                                           │  │
│  │  3. Vote for self                                                     │  │
│  │  4. Send RequestVote RPCs to all other nodes                          │  │
│  │                                                                       │  │
│  │  Outcomes:                                                            │  │
│  │  ─────────                                                            │  │
│  │  • Win: Receive majority votes → become Leader                        │  │
│  │  • Lose: Discover leader or higher term → become Follower             │  │
│  │  • Split: No majority → timeout and start new election                │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  VOTING RULES                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  A node votes YES for candidate if:                                   │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. Candidate's term ≥ voter's term                             │  │  │
│  │  │  2. Voter hasn't voted in this term yet                         │  │  │
│  │  │  3. Candidate's log is at least as up-to-date as voter's        │  │  │
│  │  │                                                                 │  │  │
│  │  │  Vote once per term → at most one leader per term               │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Example:                                                             │  │
│  │  ────────                                                             │  │
│  │                                                                       │  │
│  │    Node A (term=5) ──RequestVote(term=6)──▶ Node B (term=5)          │  │
│  │                                                                       │  │
│  │    Node B: "Term 6 > my term 5, haven't voted in term 6"             │  │
│  │             → Grant vote, update my term to 6                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  RANDOMIZED TIMEOUTS                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Problem: What if all nodes timeout simultaneously?                   │  │
│  │           Everyone starts election, votes split, no winner!           │  │
│  │                                                                       │  │
│  │  Solution: Randomize election timeouts                                │  │
│  │                                                                       │  │
│  │    Node A: timeout = 150ms + random(0, 150ms) = 234ms                │  │
│  │    Node B: timeout = 150ms + random(0, 150ms) = 187ms   ← Times out  │  │
│  │    Node C: timeout = 150ms + random(0, 150ms) = 291ms        first   │  │
│  │                                                                       │  │
│  │  Node B starts election first, likely wins before others timeout      │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PROPERTIES                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ✓ Safety: At most one leader per term (vote once rule)               │  │
│  │  ✓ Handles network partitions safely                                  │  │
│  │  ✓ Works in partially synchronous systems                             │  │
│  │  ✓ Leader has most up-to-date log                                     │  │
│  │                                                                       │  │
│  │  ✗ More complex than Bully/Ring                                       │  │
│  │  ✗ Requires majority of nodes to be available                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Split-Brain Prevention

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SPLIT-BRAIN PREVENTION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE SPLIT-BRAIN PROBLEM                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Network partition separates cluster into two groups                  │  │
│  │  Each group might elect its own leader!                               │  │
│  │                                                                       │  │
│  │  ┌─────────────────────┐   PARTITION   ┌─────────────────────┐        │  │
│  │  │                     │      ║        │                     │        │  │
│  │  │  ┌───────┐          │      ║        │         ┌───────┐   │        │  │
│  │  │  │Leader │  [B]     │      ║        │   [D]   │Leader │   │        │  │
│  │  │  │  A    │          │══════╬════════│         │  E    │   │        │  │
│  │  │  └───────┘          │      ║        │         └───────┘   │        │  │
│  │  │       [C]           │      ║        │                     │        │  │
│  │  │                     │      ║        │                     │        │  │
│  │  └─────────────────────┘               └─────────────────────┘        │  │
│  │                                                                       │  │
│  │  Both A and E accept writes → DATA DIVERGENCE!                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SOLUTION 1: QUORUM REQUIREMENT                                             │
│  ══════════════════════════════                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Require majority (quorum) to elect leader AND to commit writes       │  │
│  │                                                                       │  │
│  │  5 node cluster: quorum = 3                                           │  │
│  │                                                                       │  │
│  │  ┌─────────────────────┐   PARTITION   ┌─────────────────────┐        │  │
│  │  │                     │               │                     │        │  │
│  │  │  [A]  [B]  [C]     │      ║        │    [D]   [E]        │        │  │
│  │  │   (3 nodes)        │══════╬════════│    (2 nodes)        │        │  │
│  │  │                     │      ║        │                     │        │  │
│  │  │  CAN elect leader   │               │  CANNOT elect       │        │  │
│  │  │  (has quorum)       │               │  (no quorum)        │        │  │
│  │  │                     │               │                     │        │  │
│  │  └─────────────────────┘               └─────────────────────┘        │  │
│  │                                                                       │  │
│  │  Only one partition can have majority → only one leader!              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SOLUTION 2: FENCING TOKENS                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each leader gets monotonically increasing token                      │  │
│  │  Resources reject operations from stale tokens                        │  │
│  │                                                                       │  │
│  │  Timeline:                                                            │  │
│  │  ─────────                                                            │  │
│  │                                                                       │  │
│  │   Leader A (token=33)                                                 │  │
│  │       │                                                               │  │
│  │       │  write(x=1, token=33) ────────────────┐                       │  │
│  │       │                                       │                       │  │
│  │       ╳ (network partition / pause)           │                       │  │
│  │                                               ▼                       │  │
│  │   Leader B elected (token=34)            ┌──────────┐                 │  │
│  │       │                                  │ Storage  │                 │  │
│  │       │  write(x=2, token=34) ──────────▶│ seen: 34 │                 │  │
│  │       │                                  └────┬─────┘                 │  │
│  │                                               │                       │  │
│  │   A's delayed write arrives                   │                       │  │
│  │       │  write(x=1, token=33) ────────────────┼─▶ REJECTED!           │  │
│  │                                               │    (33 < 34)          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SOLUTION 3: LEASES                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Leader holds time-limited lease                                      │  │
│  │  Must renew lease to stay leader                                      │  │
│  │                                                                       │  │
│  │  Timeline:                                                            │  │
│  │  ─────────                                                            │  │
│  │                                                                       │  │
│  │  ┌────────────────┬────────────────┬────────────────┬──────────       │  │
│  │  │   Lease A      │   Lease A      │                │                 │  │
│  │  │   (renewed)    │   (expired)    │   Lease B      │                 │  │
│  │  ├────────────────┼────────────────┼────────────────┼──────────       │  │
│  │  0s              10s              20s              30s                │  │
│  │                                                                       │  │
│  │  Rules:                                                               │  │
│  │  ──────                                                               │  │
│  │  • Leader must renew before expiry                                    │  │
│  │  • New election only after lease expires                              │  │
│  │  • Leader must stop operations before lease expires                   │  │
│  │                                                                       │  │
│  │  Challenge: Clock skew between nodes!                                 │  │
│  │  Solution: Use bounded clock skew + safety margins                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  COMBINING APPROACHES                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Production systems often use multiple mechanisms:                    │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. Quorum for election                                         │  │  │
│  │  │     └─ Ensures only one leader can be elected                   │  │  │
│  │  │                                                                 │  │  │
│  │  │  2. Leases for leader validity                                  │  │  │
│  │  │     └─ Old leader automatically gives up                        │  │  │
│  │  │                                                                 │  │  │
│  │  │  3. Fencing tokens for storage                                  │  │  │
│  │  │     └─ Storage layer rejects stale writes                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  Defense in depth!                                              │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUMMARY                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEADER ELECTION ALGORITHMS COMPARISON                                      │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Algorithm      Messages   System Model    Complexity   Safety        │  │
│  │  ──────────────────────────────────────────────────────────────────   │  │
│  │  Bully          O(n²)      Synchronous     Simple       Weak          │  │
│  │  Ring           O(n)       Synchronous     Simple       Weak          │  │
│  │  Raft/Paxos     O(n)       Part-Sync       Complex      Strong        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  KEY TAKEAWAYS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Leaders simplify coordination but are single point of failure     │  │
│  │                                                                       │  │
│  │  2. Safety (at most one leader) is more important than liveness       │  │
│  │                                                                       │  │
│  │  3. Simple algorithms (Bully, Ring) assume synchronous networks       │  │
│  │                                                                       │  │
│  │  4. Consensus-based election handles real-world network issues        │  │
│  │                                                                       │  │
│  │  5. Quorums prevent split-brain by requiring majority                 │  │
│  │                                                                       │  │
│  │  6. Fencing tokens and leases provide additional safety layers        │  │
│  │                                                                       │  │
│  │  7. Real systems combine multiple mechanisms for defense in depth     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REAL-WORLD IMPLEMENTATIONS                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  System          Election Protocol                                    │  │
│  │  ─────────────────────────────────────────────────────────            │  │
│  │  etcd            Raft                                                 │  │
│  │  ZooKeeper       ZAB (Zookeeper Atomic Broadcast)                     │  │
│  │  Consul          Raft                                                 │  │
│  │  CockroachDB     Raft (per range)                                     │  │
│  │  MongoDB         Raft-like (Replica Set)                              │  │
│  │  Kafka           ZooKeeper/KRaft                                      │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

[← Previous: Chapter 9 - Failure Detection](./09-failure-detection.md) | [Next: Chapter 11 - Replication and Consistency →](./11-replication-consistency.md)

