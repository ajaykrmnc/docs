# Chapter 11: Replication and Consistency

## Table of Contents
- [Introduction](#introduction)
- [Why Replicate Data](#why-replicate-data)
- [Single-Leader Replication](#single-leader-replication)
- [Multi-Leader Replication](#multi-leader-replication)
- [Leaderless Replication](#leaderless-replication)
- [Quorums](#quorums)
- [Anti-Entropy and Read Repair](#anti-entropy-and-read-repair)
- [Summary](#summary)

---

## Introduction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REPLICATION AND CONSISTENCY                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "Replication means keeping copies of data on multiple machines.            │
│   The challenge is keeping those copies consistent."                         │
│                                                                             │
│  THE CORE TRADE-OFF                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │                     ┌──────────────┐                                  │  │
│  │                     │   PRIMARY    │                                  │  │
│  │                     │   DATABASE   │                                  │  │
│  │                     └──────┬───────┘                                  │  │
│  │                            │                                          │  │
│  │              ┌─────────────┼─────────────┐                            │  │
│  │              │             │             │                            │  │
│  │              ▼             ▼             ▼                            │  │
│  │       ┌──────────┐  ┌──────────┐  ┌──────────┐                        │  │
│  │       │ Replica  │  │ Replica  │  │ Replica  │                        │  │
│  │       │    1     │  │    2     │  │    3     │                        │  │
│  │       └──────────┘  └──────────┘  └──────────┘                        │  │
│  │                                                                       │  │
│  │  Question: When a write happens to Primary,                           │  │
│  │            when do replicas need to have it?                          │  │
│  │                                                                       │  │
│  │  ┌───────────────────┬─────────────────────────────────────────────┐  │  │
│  │  │ Strong Consistency│ All replicas have write before acknowledgment│  │  │
│  │  │                   │ (+) Simple for apps  (-) Slow, less available│  │  │
│  │  ├───────────────────┼─────────────────────────────────────────────┤  │  │
│  │  │ Eventual Consist. │ Replicas will converge "eventually"         │  │  │
│  │  │                   │ (+) Fast, available  (-) Complex for apps   │  │  │
│  │  └───────────────────┴─────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Replicate Data

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       WHY REPLICATE DATA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REASON 1: HIGH AVAILABILITY                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Without replication:           With replication:                     │  │
│  │                                                                       │  │
│  │     ┌──────────┐                   ┌──────────┐ ╳                     │  │
│  │     │  Server  │ ╳                 │ Replica1 │ (failed)              │  │
│  │     └──────────┘                   └──────────┘                       │  │
│  │      (failed)                      ┌──────────┐ ✓                     │  │
│  │                                    │ Replica2 │ (serving)             │  │
│  │  Service DOWN!                     └──────────┘                       │  │
│  │                                    ┌──────────┐ ✓                     │  │
│  │                                    │ Replica3 │ (serving)             │  │
│  │                                    └──────────┘                       │  │
│  │                                                                       │  │
│  │                                    Service continues!                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REASON 2: REDUCED LATENCY                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Place replicas close to users:                                       │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │     US-WEST         US-EAST         EUROPE        ASIA          │  │  │
│  │  │    ┌───────┐       ┌───────┐       ┌───────┐     ┌───────┐      │  │  │
│  │  │    │Replica│◀─────▶│Primary│◀─────▶│Replica│◀───▶│Replica│      │  │  │
│  │  │    └───┬───┘       └───────┘       └───┬───┘     └───┬───┘      │  │  │
│  │  │        │                               │             │          │  │  │
│  │  │        ▼                               ▼             ▼          │  │  │
│  │  │    US-WEST                         EUROPE         ASIA          │  │  │
│  │  │    Users                           Users          Users         │  │  │
│  │  │    (5ms)                           (5ms)          (5ms)         │  │  │
│  │  │                                                                 │  │  │
│  │  │  Without local replica: 100-200ms across ocean                  │  │  │
│  │  │  With local replica: 5-10ms                                     │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REASON 3: READ SCALABILITY                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Distribute read load across replicas:                                │  │
│  │                                                                       │  │
│  │      1000 reads/sec     1000 reads/sec     1000 reads/sec            │  │
│  │           │                   │                  │                    │  │
│  │           ▼                   ▼                  ▼                    │  │
│  │      ┌──────────┐       ┌──────────┐       ┌──────────┐              │  │
│  │      │ Replica1 │       │ Replica2 │       │ Replica3 │              │  │
│  │      └──────────┘       └──────────┘       └──────────┘              │  │
│  │                                                                       │  │
│  │  Total capacity: 3000 reads/sec (vs 1000 with single server)         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Single-Leader Replication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SINGLE-LEADER REPLICATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Also called: Master-Slave, Primary-Secondary, Active-Passive               │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │                   Writes                                              │  │
│  │                     │                                                 │  │
│  │                     ▼                                                 │  │
│  │              ┌─────────────┐                                          │  │
│  │              │   LEADER    │                                          │  │
│  │              │  (Primary)  │                                          │  │
│  │              └──────┬──────┘                                          │  │
│  │                     │                                                 │  │
│  │           Replication Stream                                          │  │
│  │                     │                                                 │  │
│  │         ┌───────────┼───────────┐                                     │  │
│  │         │           │           │                                     │  │
│  │         ▼           ▼           ▼                                     │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐                              │  │
│  │   │ FOLLOWER │ │ FOLLOWER │ │ FOLLOWER │                              │  │
│  │   │    1     │ │    2     │ │    3     │                              │  │
│  │   └────┬─────┘ └────┬─────┘ └────┬─────┘                              │  │
│  │        │            │            │                                    │  │
│  │        ▼            ▼            ▼                                    │  │
│  │      Reads        Reads        Reads                                  │  │
│  │                                                                       │  │
│  │  ALL writes go to leader, replicated to followers                     │  │
│  │  Reads can go to leader OR followers                                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SYNCHRONOUS VS ASYNCHRONOUS REPLICATION                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  SYNCHRONOUS:                                                         │  │
│  │  ────────────                                                         │  │
│  │                                                                       │  │
│  │  Client ──write──▶ Leader ──replicate──▶ Follower                     │  │
│  │                        │                     │                        │  │
│  │                        │◀───────ack──────────│                        │  │
│  │  Client ◀────ack───────│                                              │  │
│  │                                                                       │  │
│  │  ✓ Follower guaranteed to have data                                   │  │
│  │  ✗ High latency (wait for slowest follower)                           │  │
│  │  ✗ If follower down, writes blocked                                   │  │
│  │                                                                       │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │                                                                       │  │
│  │  ASYNCHRONOUS:                                                        │  │
│  │  ─────────────                                                        │  │
│  │                                                                       │  │
│  │  Client ──write──▶ Leader                                             │  │
│  │                        │                                              │  │
│  │  Client ◀────ack───────│                                              │  │
│  │                        │                                              │  │
│  │                        └──replicate──▶ Follower (later)               │  │
│  │                                                                       │  │
│  │  ✓ Low latency (don't wait for followers)                             │  │
│  │  ✓ Writes not blocked by follower issues                              │  │
│  │  ✗ Data loss risk if leader fails before replication                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SEMI-SYNCHRONOUS REPLICATION                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Compromise: Wait for at least one follower (not all)                 │  │
│  │                                                                       │  │
│  │  Leader ──replicate──▶ Follower1 (sync)  ──ack──▶                     │  │
│  │         └─replicate──▶ Follower2 (async) ──ack──▶ (later)             │  │
│  │         └─replicate──▶ Follower3 (async) ──ack──▶ (later)             │  │
│  │                                                                       │  │
│  │  Guarantees at least 2 copies (leader + 1 sync follower)              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REPLICATION LAG                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  With async replication, followers can fall behind:                   │  │
│  │                                                                       │  │
│  │  Timeline:                                                            │  │
│  │  ─────────                                                            │  │
│  │  Leader:   [A] [B] [C] [D] [E] [F]                                    │  │
│  │  Follower: [A] [B] [C] [D]                                            │  │
│  │                        ▲                                              │  │
│  │                        │                                              │  │
│  │                   Replication lag                                     │  │
│  │                                                                       │  │
│  │  Problems with lag:                                                   │  │
│  │  ──────────────────                                                   │  │
│  │                                                                       │  │
│  │  • Read-after-write inconsistency                                     │  │
│  │    User writes, then reads from follower → doesn't see write!         │  │
│  │                                                                       │  │
│  │  • Monotonic reads violation                                          │  │
│  │    User reads newer value, then older from lagging follower           │  │
│  │                                                                       │  │
│  │  • Causality violation                                                │  │
│  │    User sees response before question (due to lag differences)        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HANDLING LEADER FAILURE (Failover)                                         │
│  ══════════════════════════════════                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Detect failure (heartbeat timeout)                                │  │
│  │                                                                       │  │
│  │  2. Choose new leader (most up-to-date follower)                      │  │
│  │                                                                       │  │
│  │  3. Reconfigure system (clients use new leader)                       │  │
│  │                                                                       │  │
│  │  Challenges:                                                          │  │
│  │  ───────────                                                          │  │
│  │                                                                       │  │
│  │  • What if old leader comes back? (split-brain risk)                  │  │
│  │  • What about unreplicated writes on old leader?                      │  │
│  │  • How to handle out-of-sync auto-increment IDs?                      │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Leader Replication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MULTI-LEADER REPLICATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Also called: Master-Master, Active-Active                                   │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   Datacenter A              Datacenter B              Datacenter C    │  │
│  │  ┌───────────────┐         ┌───────────────┐         ┌───────────────┐│  │
│  │  │               │         │               │         │               ││  │
│  │  │  ┌─────────┐  │         │  ┌─────────┐  │         │  ┌─────────┐  ││  │
│  │  │  │ LEADER  │◀─┼────────▶│  │ LEADER  │◀─┼────────▶│  │ LEADER  │  ││  │
│  │  │  │   A     │  │         │  │   B     │  │         │  │   C     │  ││  │
│  │  │  └────┬────┘  │         │  └────┬────┘  │         │  └────┬────┘  ││  │
│  │  │       │       │         │       │       │         │       │       ││  │
│  │  │   Followers   │         │   Followers   │         │   Followers   ││  │
│  │  │               │         │               │         │               ││  │
│  │  │  ▲  Writes    │         │  ▲  Writes    │         │  ▲  Writes    ││  │
│  │  │  │            │         │  │            │         │  │            ││  │
│  │  └──┼────────────┘         └──┼────────────┘         └──┼────────────┘│  │
│  │     │                         │                         │             │  │
│  │   Local                     Local                     Local           │  │
│  │   Users                     Users                     Users           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  USE CASES                                                                  │
│  ═════════                                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  • Multi-datacenter operation                                         │  │
│  │    └─ Each datacenter has local leader for low latency                │  │
│  │                                                                       │  │
│  │  • Offline operation (mobile apps)                                    │  │
│  │    └─ Device is "leader" while offline, syncs when connected          │  │
│  │                                                                       │  │
│  │  • Collaborative editing                                              │  │
│  │    └─ Each user's browser is a "leader"                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  THE CONFLICT PROBLEM                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Two leaders can accept conflicting writes concurrently!              │  │
│  │                                                                       │  │
│  │  User A in DC-West:  UPDATE users SET email='a@new.com' WHERE id=1    │  │
│  │  User B in DC-East:  UPDATE users SET email='b@new.com' WHERE id=1    │  │
│  │                                                                       │  │
│  │  Both succeed locally → Conflict when replicated!                     │  │
│  │                                                                       │  │
│  │    DC-West Leader               DC-East Leader                        │  │
│  │    email='a@new.com'            email='b@new.com'                     │  │
│  │         │                             │                               │  │
│  │         └──────────▶ X ◀──────────────┘                               │  │
│  │                   CONFLICT!                                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CONFLICT RESOLUTION STRATEGIES                                             │
│  ══════════════════════════════                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. LAST WRITER WINS (LWW)                                            │  │
│  │  ─────────────────────────                                            │  │
│  │                                                                       │  │
│  │     Use timestamp to determine winner                                 │  │
│  │     Write A (t=100), Write B (t=101) → B wins                         │  │
│  │                                                                       │  │
│  │     ✓ Simple                                                          │  │
│  │     ✗ Data loss (A's write discarded)                                 │  │
│  │     ✗ Clock skew can cause wrong winner                               │  │
│  │                                                                       │  │
│  │  ──────────────────────────────────────────────────────────────────   │  │
│  │                                                                       │  │
│  │  2. MERGE VALUES                                                      │  │
│  │  ───────────────────                                                  │  │
│  │                                                                       │  │
│  │     Keep both values, merge intelligently                             │  │
│  │                                                                       │  │
│  │     Shopping cart: UNION of items                                     │  │
│  │     Text: CRDT-based merge                                            │  │
│  │                                                                       │  │
│  │  ──────────────────────────────────────────────────────────────────   │  │
│  │                                                                       │  │
│  │  3. APPLICATION RESOLVES                                              │  │
│  │  ───────────────────────────                                          │  │
│  │                                                                       │  │
│  │     Store all conflicting versions                                    │  │
│  │     Let application (or user) resolve                                 │  │
│  │                                                                       │  │
│  │     Example: "You edited from two devices, which version to keep?"    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REPLICATION TOPOLOGIES                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  CIRCULAR                 STAR                    ALL-TO-ALL          │  │
│  │                                                                       │  │
│  │    ┌───┐                   ┌───┐                ┌───┐   ┌───┐        │  │
│  │    │ A │──┐             ┌──│ B │──┐             │ A │◀─▶│ B │        │  │
│  │    └───┘  │             │  └───┘  │             └───┘   └───┘        │  │
│  │      ▲    ▼             ▼         ▼               ▲  ╲   ╱  ▲        │  │
│  │      │  ┌───┐       ┌───┐       ┌───┐              ╲  ╲ ╱  ╱         │  │
│  │      │  │ B │       │ A │       │ C │               ╲  X  ╱          │  │
│  │      │  └───┘       └───┘       └───┘                ╲╱ ╲╱           │  │
│  │      │    │                                          ╱╲ ╱╲           │  │
│  │      │    ▼                                         ╱  X  ╲          │  │
│  │    ┌───┐◀─┘                                      ┌───┐   ┌───┐       │  │
│  │    │ C │                                         │ C │◀─▶│ D │       │  │
│  │    └───┘                                         └───┘   └───┘       │  │
│  │                                                                       │  │
│  │  Fault tolerant: Poor      Medium              Best                   │  │
│  │  Complexity:     Medium    Low                 High (conflicts)       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Leaderless Replication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LEADERLESS REPLICATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Also called: Dynamo-style, Peer-to-peer replication                         │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  No leader! Client writes to multiple replicas directly               │  │
│  │                                                                       │  │
│  │              ┌────────────────┐                                       │  │
│  │              │     CLIENT     │                                       │  │
│  │              └───────┬────────┘                                       │  │
│  │                      │                                                │  │
│  │         ┌────────────┼────────────┐                                   │  │
│  │         │            │            │                                   │  │
│  │      write        write        write                                  │  │
│  │         │            │            │                                   │  │
│  │         ▼            ▼            ▼                                   │  │
│  │    ┌──────────┐ ┌──────────┐ ┌──────────┐                             │  │
│  │    │ Replica  │ │ Replica  │ │ Replica  │                             │  │
│  │    │    1     │ │    2     │ │    3     │                             │  │
│  │    └──────────┘ └──────────┘ └──────────┘                             │  │
│  │                                                                       │  │
│  │  Each replica is equal - no "primary" or "secondary"                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WRITE & READ OPERATIONS                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  WRITE: Send to all N replicas, wait for W acknowledgments            │  │
│  │  READ:  Send to all N replicas, wait for R responses                  │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │                                                                  │ │  │
│  │  │  Example: N=3, W=2, R=2                                          │ │  │
│  │  │                                                                  │ │  │
│  │  │  WRITE x=5:                                                      │ │  │
│  │  │  Client ──▶ Replica1 (ack ✓)                                     │ │  │
│  │  │         ──▶ Replica2 (ack ✓)  → 2 acks, write succeeds!          │ │  │
│  │  │         ──▶ Replica3 (slow, no ack yet)                          │ │  │
│  │  │                                                                  │ │  │
│  │  │  READ x:                                                         │ │  │
│  │  │  Client ──▶ Replica1 (x=5)                                       │ │  │
│  │  │         ──▶ Replica2 (x=5)    → 2 responses, use latest!         │ │  │
│  │  │         ──▶ Replica3 (x=3, stale)                                │ │  │
│  │  │                                                                  │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  VERSION VECTORS                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  How to determine "latest" value? Use version vectors!                │  │
│  │                                                                       │  │
│  │  Each replica tracks version for each key:                            │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                │   │  │
│  │  │  key="user:1"                                                  │   │  │
│  │  │                                                                │   │  │
│  │  │  Replica1: version=[R1:3, R2:2, R3:1]  value="Alice"           │   │  │
│  │  │  Replica2: version=[R1:3, R2:2, R3:2]  value="Alice Smith"     │   │  │
│  │  │  Replica3: version=[R1:3, R2:2, R3:2]  value="Alice Smith"     │   │  │
│  │  │                                                                │   │  │
│  │  │  Replica1 is behind (R3:1 < R3:2)                              │   │  │
│  │  │                                                                │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HINTED HANDOFF                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  What if a replica is temporarily down?                               │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │                                                                  │ │  │
│  │  │  Replica3 is DOWN                                                │ │  │
│  │  │                                                                  │ │  │
│  │  │  Client ──▶ Replica1 (ack)                                       │ │  │
│  │  │         ──▶ Replica2 (ack)                                       │ │  │
│  │  │         ──▶ Replica3 ✗ → Send to Replica4 instead!               │ │  │
│  │  │                         (with hint: "this is for Replica3")      │ │  │
│  │  │                                                                  │ │  │
│  │  │  When Replica3 comes back:                                       │ │  │
│  │  │  Replica4 ──▶ Replica3: "Here's the data I was holding for you"  │ │  │
│  │  │                                                                  │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  Improves availability, maintains durability                          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quorums

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QUORUMS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE QUORUM CONDITION                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  For reads to see latest write:  W + R > N                            │  │
│  │                                                                       │  │
│  │  N = total replicas                                                   │  │
│  │  W = replicas that must acknowledge write                             │  │
│  │  R = replicas that must respond to read                               │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │                                                                  │ │  │
│  │  │  Example: N=5, W=3, R=3   (3 + 3 = 6 > 5 ✓)                      │ │  │
│  │  │                                                                  │ │  │
│  │  │  Write set:  [R1, R2, R3]                                        │ │  │
│  │  │  Read set:   [R3, R4, R5]                                        │ │  │
│  │  │                      ▲                                           │ │  │
│  │  │                      │                                           │ │  │
│  │  │                  R3 in both! Will see latest write.              │ │  │
│  │  │                                                                  │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  Visual:                                                              │  │
│  │  ───────                                                              │  │
│  │                                                                       │  │
│  │  N=5: [R1] [R2] [R3] [R4] [R5]                                        │  │
│  │                                                                       │  │
│  │  W=3:  ✓    ✓    ✓                   (write acks)                    │  │
│  │  R=3:            ✓    ✓    ✓         (read responses)                │  │
│  │                  ▲                                                    │  │
│  │                  │                                                    │  │
│  │            OVERLAP GUARANTEED                                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TUNING QUORUMS                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Different configurations for different needs:                        │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                │   │  │
│  │  │  N=3, W=3, R=1  "Write-heavy, strong consistency"              │   │  │
│  │  │  ─────────────────────────────────────────────────             │   │  │
│  │  │  • Every write goes to ALL replicas                            │   │  │
│  │  │  • Reads only need one replica                                 │   │  │
│  │  │  • Fast reads, slower writes                                   │   │  │
│  │  │                                                                │   │  │
│  │  │  N=3, W=1, R=3  "Read-heavy, eventual consistency"             │   │  │
│  │  │  ─────────────────────────────────────────────────             │   │  │
│  │  │  • Write returns after one ack (fast!)                         │   │  │
│  │  │  • Reads check ALL replicas                                    │   │  │
│  │  │  • Risk: write might be lost if that one replica fails         │   │  │
│  │  │                                                                │   │  │
│  │  │  N=3, W=2, R=2  "Balanced"                                     │   │  │
│  │  │  ─────────────────────────────────────────────────             │   │  │
│  │  │  • Majority for both reads and writes                          │   │  │
│  │  │  • Good balance of consistency and availability                │   │  │
│  │  │                                                                │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SLOPPY QUORUMS                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  What if not enough designated replicas are reachable?                │  │
│  │                                                                       │  │
│  │  Strict Quorum:  Return error if can't reach W or R nodes             │  │
│  │  Sloppy Quorum:  Accept writes on ANY available node                  │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                │   │  │
│  │  │  Scenario: N=3, W=2, but R2 and R3 are unreachable             │   │  │
│  │  │                                                                │   │  │
│  │  │  Strict:   Can't write! (only R1 available)                    │   │  │
│  │  │  Sloppy:   Write to R1 + any 2 other nodes (R4, R5)            │   │  │
│  │  │            Handoff to R2, R3 when they recover                 │   │  │
│  │  │                                                                │   │  │
│  │  │  WARNING: Sloppy quorums don't guarantee overlap!              │   │  │
│  │  │  Read might go to R2, R3 (just recovered) and miss new data    │   │  │
│  │  │                                                                │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  │  Trade-off: Higher availability vs weaker consistency guarantees     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Anti-Entropy and Read Repair

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ANTI-ENTROPY AND READ REPAIR                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Quorums help, but replicas can still diverge. How to fix?                  │
│                                                                             │
│  READ REPAIR                                                                │
│  ═══════════                                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  During reads, fix stale replicas:                                    │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                │   │  │
│  │  │  1. Client reads from 3 replicas:                              │   │  │
│  │  │                                                                │   │  │
│  │  │     Replica1: x=5, version=3                                   │   │  │
│  │  │     Replica2: x=5, version=3                                   │   │  │
│  │  │     Replica3: x=3, version=2  ← STALE!                         │   │  │
│  │  │                                                                │   │  │
│  │  │  2. Client returns x=5 (latest version)                        │   │  │
│  │  │                                                                │   │  │
│  │  │  3. Client also sends repair to Replica3:                      │   │  │
│  │  │     "Update x=5, version=3"                                    │   │  │
│  │  │                                                                │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  │  ✓ Repairs data on the read path                                      │  │
│  │  ✓ No extra background process                                        │  │
│  │  ✗ Only repairs data that is read                                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ANTI-ENTROPY (MERKLE TREES)                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Background process to sync replicas:                                 │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                │   │  │
│  │  │  MERKLE TREE: Hash tree of all data                            │   │  │
│  │  │                                                                │   │  │
│  │  │              ┌─────────┐                                       │   │  │
│  │  │              │ Root    │                                       │   │  │
│  │  │              │ Hash    │                                       │   │  │
│  │  │              │ abc123  │                                       │   │  │
│  │  │              └────┬────┘                                       │   │  │
│  │  │           ┌───────┴───────┐                                    │   │  │
│  │  │           ▼               ▼                                    │   │  │
│  │  │      ┌────────┐     ┌────────┐                                 │   │  │
│  │  │      │ Left   │     │ Right  │                                 │   │  │
│  │  │      │ def456 │     │ ghi789 │                                 │   │  │
│  │  │      └───┬────┘     └───┬────┘                                 │   │  │
│  │  │       ┌──┴──┐        ┌──┴──┐                                   │   │  │
│  │  │       ▼     ▼        ▼     ▼                                   │   │  │
│  │  │     [A-M] [N-P]    [Q-T] [U-Z]   (key ranges)                  │   │  │
│  │  │                                                                │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  │  Comparison Process:                                                  │  │
│  │  ───────────────────                                                  │  │
│  │                                                                       │  │
│  │  1. Replica1 and Replica2 exchange root hashes                        │  │
│  │     • If same → all data matches! (common case)                       │  │
│  │     • If different → recurse down the tree                            │  │
│  │                                                                       │  │
│  │  2. Compare child hashes to narrow down differences                   │  │
│  │                                                                       │  │
│  │  3. Only sync the specific key ranges that differ                     │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                                                                │   │  │
│  │  │  Replica1: Root=abc123    Replica2: Root=xyz999                │   │  │
│  │  │                                                                │   │  │
│  │  │  Different! Check children:                                    │   │  │
│  │  │  R1.Left=def456  R2.Left=def456  ← Same!                       │   │  │
│  │  │  R1.Right=ghi789 R2.Right=qqq111 ← Different!                  │   │  │
│  │  │                                                                │   │  │
│  │  │  Only sync Right subtree (Q-Z keys)                            │   │  │
│  │  │                                                                │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ✓ Finds ALL differences, not just read data                                │
│  ✓ Efficient: O(log N) comparisons to find differences                      │
│  ✗ Background CPU/IO cost                                                   │
│  ✗ Tree must be rebuilt when data changes (or use incremental updates)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CHAPTER SUMMARY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REPLICATION MODEL COMPARISON                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  Model          │ Consistency │ Availability │ Complexity │ Writes │    │
│  │  ════════════════════════════════════════════════════════════════   │    │
│  │  Single-Leader  │ Strong      │ Limited*     │ Low        │ Leader │    │
│  │  Multi-Leader   │ Eventual    │ High         │ High       │ Any DC │    │
│  │  Leaderless     │ Tunable     │ High         │ Medium     │ Any    │    │
│  │                                                                     │    │
│  │  * Failover can cause brief unavailability                          │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  KEY CONCEPTS                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                 │    │
│  │  │ SINGLE-LEADER        │  │ MULTI-LEADER         │                 │    │
│  │  ├──────────────────────┤  ├──────────────────────┤                 │    │
│  │  │ • One write path     │  │ • Multiple write     │                 │    │
│  │  │ • Sync/Async options │  │   paths              │                 │    │
│  │  │ • Replication lag    │  │ • Conflict handling  │                 │    │
│  │  │ • Failover needed    │  │ • Topologies matter  │                 │    │
│  │  └──────────────────────┘  └──────────────────────┘                 │    │
│  │                                                                     │    │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                 │    │
│  │  │ LEADERLESS           │  │ QUORUMS              │                 │    │
│  │  ├──────────────────────┤  ├──────────────────────┤                 │    │
│  │  │ • W+R>N guarantees   │  │ • W + R > N          │                 │    │
│  │  │ • Version vectors    │  │ • Tunable trade-offs │                 │    │
│  │  │ • Hinted handoff     │  │ • Sloppy for avail.  │                 │    │
│  │  │ • Anti-entropy       │  │ • Strict for consist │                 │    │
│  │  └──────────────────────┘  └──────────────────────┘                 │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  WHEN TO USE WHAT                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  Single-Leader:                                                     │    │
│  │  • Default choice for most applications                             │    │
│  │  • When strong consistency is required                              │    │
│  │  • Single datacenter deployments                                    │    │
│  │                                                                     │    │
│  │  Multi-Leader:                                                      │    │
│  │  • Multi-datacenter with local writes                               │    │
│  │  • Offline-capable applications                                     │    │
│  │  • Collaborative editing (with CRDTs)                               │    │
│  │                                                                     │    │
│  │  Leaderless:                                                        │    │
│  │  • High availability requirements                                   │    │
│  │  • Tunable consistency needs                                        │    │
│  │  • Eventually consistent use cases                                  │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  CONSISTENCY REPAIR MECHANISMS                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  Read Repair          │ Anti-Entropy (Merkle Trees)                 │    │
│  │  ═══════════════════════════════════════════════════                │    │
│  │  On read path         │ Background process                          │    │
│  │  Fixes stale values   │ Compares all data                           │    │
│  │  Only for read data   │ Finds all differences                       │    │
│  │  No extra resources   │ Uses CPU/IO                                 │    │
│  │                                                                     │    │
│  │  Best: Use both together for complete coverage                      │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  REAL-WORLD EXAMPLES                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  Single-Leader:  PostgreSQL, MySQL, MongoDB (default)               │    │
│  │                                                                     │    │
│  │  Multi-Leader:   CouchDB, Tungsten Replicator, custom solutions     │    │
│  │                                                                     │    │
│  │  Leaderless:     Amazon DynamoDB, Apache Cassandra, Riak, Voldemort │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Navigation

| Previous | Up | Next |
|----------|-----|------|
| [← Chapter 10: Leader Election](10-leader-election.md) | [Index](README.md) | [Chapter 12: Distributed Transactions →](12-distributed-transactions.md) |

