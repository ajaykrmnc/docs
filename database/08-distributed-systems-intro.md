# Chapter 8: Distributed Systems Introduction

## Table of Contents
- [Why Distributed Systems](#why-distributed-systems)
- [Fallacies of Distributed Computing](#fallacies-of-distributed-computing)
- [Network Fundamentals](#network-fundamentals)
- [CAP Theorem](#cap-theorem)
- [Consistency Models](#consistency-models)
- [Time and Ordering](#time-and-ordering)
- [Summary](#summary)

---

## Why Distributed Systems

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WHY DISTRIBUTED SYSTEMS?                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MOTIVATIONS                                                                │
│  ═══════════                                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. SCALABILITY                                                       │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                                                               │    │  │
│  │  │  Vertical Scaling (Scale Up)    Horizontal Scaling (Scale Out)│   │  │
│  │  │                                                               │    │  │
│  │  │       ┌───────┐                  ┌───┐ ┌───┐ ┌───┐ ┌───┐     │    │  │
│  │  │       │███████│                  │   │ │   │ │   │ │   │     │    │  │
│  │  │       │███████│                  └───┘ └───┘ └───┘ └───┘     │    │  │
│  │  │       │███████│                     ↓     ↓     ↓     ↓      │    │  │
│  │  │       │███████│                  ┌─────────────────────┐     │    │  │
│  │  │       └───────┘                  │     NETWORK         │     │    │  │
│  │  │       Bigger box                 └─────────────────────┘     │    │  │
│  │  │       (limited!)                  More boxes (unlimited!)    │    │  │
│  │  │                                                               │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  2. FAULT TOLERANCE                                                   │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                                                               │    │  │
│  │  │  Single Server:            Distributed System:                │    │  │
│  │  │                                                               │    │  │
│  │  │    ┌─────┐                   ┌───┐   ┌───┐   ┌───┐           │    │  │
│  │  │    │  X  │ ← fails           │ ✓ │   │ X │   │ ✓ │           │    │  │
│  │  │    └─────┘                   └───┘   └───┘   └───┘           │    │  │
│  │  │    System DOWN               System still UP!                 │    │  │
│  │  │                              (2/3 nodes available)            │    │  │
│  │  │                                                               │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  3. GEOGRAPHIC DISTRIBUTION                                           │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                                                               │    │  │
│  │  │      🌎 US-West        🌍 Europe        🌏 Asia               │    │  │
│  │  │        ┌───┐            ┌───┐            ┌───┐                │    │  │
│  │  │        │ A │────────────│ B │────────────│ C │                │    │  │
│  │  │        └───┘            └───┘            └───┘                │    │  │
│  │  │                                                               │    │  │
│  │  │      Low latency for users worldwide                          │    │  │
│  │  │      Data locality for compliance                             │    │  │
│  │  │                                                               │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  4. PERFORMANCE                                                       │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                                                               │    │  │
│  │  │  Parallel processing across multiple nodes:                   │    │  │
│  │  │                                                               │    │  │
│  │  │  Query: SELECT * FROM orders WHERE date > '2024-01-01'       │    │  │
│  │  │                                                               │    │  │
│  │  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                          │    │  │
│  │  │  │Node1│  │Node2│  │Node3│  │Node4│                          │    │  │
│  │  │  │ 25% │  │ 25% │  │ 25% │  │ 25% │  ← Each scans portion    │    │  │
│  │  │  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘                          │    │  │
│  │  │     └────────┴───┬────┴────────┘                             │    │  │
│  │  │                  ▼                                           │    │  │
│  │  │            ┌──────────┐                                      │    │  │
│  │  │            │ Combine  │  ← Merge results                     │    │  │
│  │  │            └──────────┘                                      │    │  │
│  │  │                                                               │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  THE CHALLENGES                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Distribution introduces fundamental challenges:                      │  │
│  │                                                                       │  │
│  │  • Network failures (messages lost, delayed, duplicated)             │  │
│  │  • Partial failures (some nodes work, others don't)                  │  │
│  │  • Clock synchronization (no global time)                            │  │
│  │  • Concurrent access (ordering of events)                            │  │
│  │  • Data consistency (keeping replicas in sync)                       │  │
│  │                                                                       │  │
│  │  "A distributed system is one where the failure of a computer        │  │
│  │   you didn't even know existed can render your own computer          │  │
│  │   unusable." — Leslie Lamport                                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fallacies of Distributed Computing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FALLACIES OF DISTRIBUTED COMPUTING                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE EIGHT FALLACIES (Peter Deutsch, 1994)                                  │
│  ═════════════════════════════════════════                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. THE NETWORK IS RELIABLE                                           │  │
│  │  ─────────────────────────                                            │  │
│  │                                                                       │  │
│  │    Reality:                                                           │  │
│  │    ┌───┐         ┌───┐                                                │  │
│  │    │ A │──── X ──│ B │   Packets can be lost, delayed, reordered     │  │
│  │    └───┘         └───┘                                                │  │
│  │                                                                       │  │
│  │    • Network switches fail                                            │  │
│  │    • Cables get disconnected                                          │  │
│  │    • Packets get dropped under load                                   │  │
│  │    • Must handle: retries, timeouts, idempotency                      │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  2. LATENCY IS ZERO                                                   │  │
│  │  ──────────────────                                                   │  │
│  │                                                                       │  │
│  │    Reality:                                                           │  │
│  │    ┌─────────────────────────────────────────────────────────────┐    │  │
│  │    │  Same datacenter:     0.5ms  ████                           │    │  │
│  │    │  Cross-country:       30ms   ████████████████               │    │  │
│  │    │  Cross-continent:    100ms   ████████████████████████████   │    │  │
│  │    │  Cross-world:        300ms   █████████████████████████████+ │    │  │
│  │    └─────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │    • Every network hop adds latency                                   │  │
│  │    • Speed of light is a hard limit (~200km/ms in fiber)              │  │
│  │    • Must minimize round trips                                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  3. BANDWIDTH IS INFINITE                                             │  │
│  │  ────────────────────────                                             │  │
│  │                                                                       │  │
│  │    • Network links have capacity limits                              │  │
│  │    • Shared bandwidth with other users                               │  │
│  │    • Must batch and compress data                                    │  │
│  │                                                                       │  │
│  │  4. THE NETWORK IS SECURE                                             │  │
│  │  ─────────────────────────                                            │  │
│  │                                                                       │  │
│  │    • Man-in-the-middle attacks                                       │  │
│  │    • Data interception                                               │  │
│  │    • Must use encryption (TLS), authentication                       │  │
│  │                                                                       │  │
│  │  5. TOPOLOGY DOESN'T CHANGE                                           │  │
│  │  ─────────────────────────────                                        │  │
│  │                                                                       │  │
│  │    • Servers added/removed dynamically                               │  │
│  │    • Network routes change                                           │  │
│  │    • Must use service discovery, dynamic routing                     │  │
│  │                                                                       │  │
│  │  6. THERE IS ONE ADMINISTRATOR                                        │  │
│  │  ─────────────────────────────                                        │  │
│  │                                                                       │  │
│  │    • Multiple teams, multiple orgs                                   │  │
│  │    • Different policies, different SLAs                              │  │
│  │    • Must handle heterogeneous environments                          │  │
│  │                                                                       │  │
│  │  7. TRANSPORT COST IS ZERO                                            │  │
│  │  ─────────────────────────────                                        │  │
│  │                                                                       │  │
│  │    • Serialization/deserialization has CPU cost                      │  │
│  │    • Data transfer costs money (cloud egress)                        │  │
│  │    • Must consider data placement                                    │  │
│  │                                                                       │  │
│  │  8. THE NETWORK IS HOMOGENEOUS                                        │  │
│  │  ─────────────────────────────────                                    │  │
│  │                                                                       │  │
│  │    • Different hardware, protocols, capabilities                     │  │
│  │    • Must use standard protocols                                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Network Fundamentals

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NETWORK FUNDAMENTALS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TYPES OF NETWORK FAILURES                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. MESSAGE LOSS                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │   ┌───┐           ┌───┐          ┌───┐                          │  │  │
│  │  │   │ A │──MSG1──▶  │   │    ──▶   │ B │  MSG1 never arrives      │  │  │
│  │  │   └───┘           │   │          └───┘                          │  │  │
│  │  │                   │   │                                         │  │  │
│  │  │                   │ X │  ← Router/switch failure                │  │  │
│  │  │                   │   │                                         │  │  │
│  │  │                   └───┘                                         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  2. MESSAGE DUPLICATION                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │   ┌───┐  MSG1 ─────────────────────────▶ ┌───┐                  │  │  │
│  │  │   │ A │                                  │ B │ Receives twice!  │  │  │
│  │  │   └───┘  MSG1 ─────────────────────────▶ └───┘                  │  │  │
│  │  │        (retry after timeout, but original was just slow)        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  3. MESSAGE REORDERING                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │   ┌───┐  MSG1 ───(slow path)────────────▶ ┌───┐                 │  │  │
│  │  │   │ A │                                   │ B │ Receives 2,1    │  │  │
│  │  │   └───┘  MSG2 ───(fast path)─────────────▶└───┘                 │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  NETWORK PARTITIONS                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  A network partition occurs when nodes cannot communicate:            │  │
│  │                                                                       │  │
│  │  BEFORE PARTITION:                                                    │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                                                               │    │  │
│  │  │   ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐              │    │  │
│  │  │   │ A │─────│ B │─────│ C │─────│ D │─────│ E │              │    │  │
│  │  │   └───┘     └───┘     └───┘     └───┘     └───┘              │    │  │
│  │  │                                                               │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  AFTER PARTITION:                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                                                               │    │  │
│  │  │   ┌───┐     ┌───┐     ┌───┐  ║  ┌───┐     ┌───┐              │    │  │
│  │  │   │ A │─────│ B │─────│ C │  ║  │ D │─────│ E │              │    │  │
│  │  │   └───┘     └───┘     └───┘  ║  └───┘     └───┘              │    │  │
│  │  │                              ║                                │    │  │
│  │  │   Partition 1 (majority)     ║  Partition 2 (minority)        │    │  │
│  │  │   Can make progress          ║  Cannot make progress          │    │  │
│  │  │                              ║  (in typical consensus)        │    │  │
│  │  │                                                               │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  │                                                                       │  │
│  │  Types of partitions:                                                 │  │
│  │  • Complete: No communication between partitions                     │  │
│  │  • Partial: Some nodes can communicate across partition               │  │
│  │  • Asymmetric: A can reach B, but B cannot reach A                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CAP Theorem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAP THEOREM                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE THREE PROPERTIES (Eric Brewer, 2000)                                   │
│  ════════════════════════════════════════                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │                        ┌──────────────────┐                           │  │
│  │                        │   CONSISTENCY    │                           │  │
│  │                        │   (C)            │                           │  │
│  │                        │                  │                           │  │
│  │                        │ All nodes see    │                           │  │
│  │                        │ same data at     │                           │  │
│  │                        │ same time        │                           │  │
│  │                        └────────┬─────────┘                           │  │
│  │                                 │                                     │  │
│  │                    ┌────────────┼────────────┐                        │  │
│  │                    │            │            │                        │  │
│  │           ┌────────▼───────┐    │   ┌────────▼────────┐               │  │
│  │           │ AVAILABILITY   │◄───┴──►│ PARTITION       │               │  │
│  │           │ (A)            │        │ TOLERANCE (P)   │               │  │
│  │           │                │        │                 │               │  │
│  │           │ Every request  │        │ System works    │               │  │
│  │           │ gets response  │        │ despite network │               │  │
│  │           │                │        │ failures        │               │  │
│  │           └────────────────┘        └─────────────────┘               │  │
│  │                                                                       │  │
│  │  The CAP Theorem: During a network partition, you must choose         │  │
│  │  between Consistency and Availability - you cannot have both.         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CAP TRADE-OFFS                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  DURING A PARTITION:                                                  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │   Client                                                        │  │  │
│  │  │     │                                                           │  │  │
│  │  │     │ WRITE x=1                                                 │  │  │
│  │  │     ▼                                                           │  │  │
│  │  │   ┌───┐                           ┌───┐                         │  │  │
│  │  │   │ A │ x=1                   ║   │ B │ x=0 (stale)             │  │  │
│  │  │   └───┘                       ║   └───┘                         │  │  │
│  │  │                               ║                                 │  │  │
│  │  │                    PARTITION ─╨─                                │  │  │
│  │  │                                                                 │  │  │
│  │  │   Option 1: CP (Consistency + Partition Tolerance)              │  │  │
│  │  │   • Node B rejects reads/writes until partition heals           │  │  │
│  │  │   • Maintains consistency, sacrifices availability              │  │  │
│  │  │   • Example: HBase, MongoDB (in default mode)                   │  │  │
│  │  │                                                                 │  │  │
│  │  │   Option 2: AP (Availability + Partition Tolerance)             │  │  │
│  │  │   • Node B accepts reads/writes with stale data                 │  │  │
│  │  │   • Maintains availability, sacrifices consistency              │  │  │
│  │  │   • Example: Cassandra, DynamoDB                                │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  DATABASE CLASSIFICATION                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │        CP Systems                    AP Systems                 │  │  │
│  │  │        ──────────                    ──────────                 │  │  │
│  │  │                                                                 │  │  │
│  │  │        • HBase                       • Cassandra                │  │  │
│  │  │        • MongoDB*                    • DynamoDB                 │  │  │
│  │  │        • Redis Cluster               • Riak                     │  │  │
│  │  │        • Zookeeper                   • CouchDB                  │  │  │
│  │  │        • etcd                        • Voldemort                │  │  │
│  │  │        • Consul                                                 │  │  │
│  │  │                                                                 │  │  │
│  │  │   * MongoDB can be configured for either CP or AP               │  │  │
│  │  │                                                                 │  │  │
│  │  │   Note: Traditional RDBMS (PostgreSQL, MySQL) are typically     │  │  │
│  │  │   CA in single-node mode but become CP when distributed         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PACELC THEOREM (Extension of CAP)                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  "If Partition (P), choose Availability or Consistency (A/C).        │  │
│  │   Else (E), even when running normally, choose Latency or            │  │
│  │   Consistency (L/C)."                                                 │  │
│  │                                                                       │  │
│  │  ┌────────────────────────┬─────────────────┬─────────────────┐       │  │
│  │  │ System                 │ During Partition│ Normal Operation│       │  │
│  │  ├────────────────────────┼─────────────────┼─────────────────┤       │  │
│  │  │ DynamoDB, Cassandra    │ PA              │ EL              │       │  │
│  │  │ MongoDB, HBase         │ PC              │ EC              │       │  │
│  │  │ PNUTS (Yahoo!)         │ PC              │ EL              │       │  │
│  │  │ VoltDB                 │ PC              │ EC              │       │  │
│  │  └────────────────────────┴─────────────────┴─────────────────┘       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Consistency Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONSISTENCY MODELS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CONSISTENCY SPECTRUM                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   STRONG ◄────────────────────────────────────────────────────► WEAK  │  │
│  │                                                                       │  │
│  │   ┌──────────┬──────────┬──────────┬──────────┬──────────────┐        │  │
│  │   │Lineariz- │Sequential│ Causal   │ Session  │  Eventual    │        │  │
│  │   │ ability  │Consistency│Consistency│Consistency│Consistency  │        │  │
│  │   └──────────┴──────────┴──────────┴──────────┴──────────────┘        │  │
│  │       ▲           │          │          │              ▲              │  │
│  │       │           │          │          │              │              │  │
│  │   Harder to      │          │          │         Easier to           │  │
│  │   implement      │          │          │         implement           │  │
│  │   Lower perf     │          │          │         Higher perf         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LINEARIZABILITY (Strongest)                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  "Operations appear to execute atomically at some point between       │  │
│  │   invocation and completion"                                          │  │
│  │                                                                       │  │
│  │  Time ──────────────────────────────────────────────────────────────▶ │  │
│  │                                                                       │  │
│  │  Client A:  ├───── W(x=1) ─────┤                                      │  │
│  │                          ●  ← linearization point                     │  │
│  │  Client B:              ├───── R(x) ─────┤ → must return 1            │  │
│  │                                                                       │  │
│  │  If B's read starts after A's write starts, and A's write             │  │
│  │  completes before B's read completes, B must see A's write.           │  │
│  │                                                                       │  │
│  │  Use cases: Leader election, lock services, unique constraints        │  │
│  │  Examples: ZooKeeper, etcd, Consul                                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SEQUENTIAL CONSISTENCY                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  "Operations appear to execute in some total order consistent         │  │
│  │   with the order seen by each client"                                 │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Client A:  W(x=1) ─────▶ W(x=2)                                │  │  │
│  │  │  Client B:      W(x=3) ─────▶ W(x=4)                            │  │  │
│  │  │                                                                 │  │  │
│  │  │  Valid global orders:                                           │  │  │
│  │  │  • W(x=1), W(x=2), W(x=3), W(x=4)  ✓                           │  │  │
│  │  │  • W(x=1), W(x=3), W(x=2), W(x=4)  ✓                           │  │  │
│  │  │  • W(x=2), W(x=1), W(x=3), W(x=4)  ✗ (violates A's order)      │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Weaker than linearizable: doesn't respect real-time ordering        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CAUSAL CONSISTENCY                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  "Causally related operations are seen in the same order by all"     │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Causally related:                                              │  │  │
│  │  │  • A writes, then A reads (same process)                        │  │  │
│  │  │  • A writes, B reads, B writes (read-from)                      │  │  │
│  │  │  • Transitively related                                         │  │  │
│  │  │                                                                 │  │  │
│  │  │  Example (social media):                                        │  │  │
│  │  │                                                                 │  │  │
│  │  │  Alice posts: "I got a job!"                                    │  │  │
│  │  │  Bob sees post, replies: "Congrats!"                            │  │  │
│  │  │                                                                 │  │  │
│  │  │  Carol must see Alice's post before Bob's reply                 │  │  │
│  │  │  (they are causally related)                                    │  │  │
│  │  │                                                                 │  │  │
│  │  │  But concurrent, unrelated posts can appear in any order        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  EVENTUAL CONSISTENCY                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  "If no new updates, all replicas will eventually converge"          │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Time ─────────────────────────────────────────────────────────▶│  │  │
│  │  │                                                                 │  │  │
│  │  │  Node A:  x=1 ─────── x=1 ─────── x=1 ─────── x=5 ──────       │  │  │
│  │  │  Node B:  x=0 ─────── x=1 ─────── x=1 ─────── x=5 ──────       │  │  │
│  │  │  Node C:  x=0 ─────── x=0 ─────── x=1 ─────── x=5 ──────       │  │  │
│  │  │                 ▲          ▲           ▲                        │  │  │
│  │  │             Write to A  Propagates  All converged               │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Variants:                                                            │  │
│  │  • Read-your-writes: See your own writes                             │  │
│  │  • Monotonic reads: Once read value, never see older                 │  │
│  │  • Monotonic writes: Your writes apply in order                      │  │
│  │                                                                       │  │
│  │  Examples: DNS, CDNs, Cassandra, DynamoDB                            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Time and Ordering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TIME AND ORDERING                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE PROBLEM WITH PHYSICAL CLOCKS                                           │
│  ══════════════════════════════════                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Clocks drift and can never be perfectly synchronized:               │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Node A clock:  10:00:00.000                                    │  │  │
│  │  │  Node B clock:  10:00:00.150   (150ms ahead)                    │  │  │
│  │  │  Node C clock:  09:59:59.850   (150ms behind)                   │  │  │
│  │  │                                                                 │  │  │
│  │  │  Even with NTP, drift of 10-250ms is common                     │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Issues:                                                              │  │
│  │  • Using timestamps to order events can be wrong                     │  │
│  │  • "Last write wins" based on timestamps loses data                  │  │
│  │  • Cannot determine causality from timestamps                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LAMPORT CLOCKS (Logical Clocks)                                            │
│  ════════════════════════════════                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Rules:                                                               │  │
│  │  1. Before any event: counter++                                       │  │
│  │  2. Send message: include counter                                     │  │
│  │  3. Receive message: counter = max(local, received) + 1               │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Process A:  (1) ────────(2)────────────────(5)─────────        │  │  │
│  │  │                   \                        /                    │  │  │
│  │  │                    \                      /                     │  │  │
│  │  │  Process B:    (1)──(2)────(3)────(4)───/                       │  │  │
│  │  │                        \        /                               │  │  │
│  │  │                         \      /                                │  │  │
│  │  │  Process C:         (1)──(3)──(4)────────(5)──────────          │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Properties:                                                          │  │
│  │  • If a → b (a happens-before b), then L(a) < L(b)                   │  │
│  │  • But NOT: L(a) < L(b) implies a → b (concurrent events may have    │  │
│  │    any order)                                                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  VECTOR CLOCKS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each node maintains a vector of counters (one per node):             │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Node A: [A:1, B:0, C:0]                                        │  │  │
│  │  │          │                                                      │  │  │
│  │  │          │ send message                                         │  │  │
│  │  │          ▼                                                      │  │  │
│  │  │  Node B: [A:1, B:1, C:0]  (received A's clock, incremented B)   │  │  │
│  │  │          │                                                      │  │  │
│  │  │          │ send message                                         │  │  │
│  │  │          ▼                                                      │  │  │
│  │  │  Node C: [A:1, B:1, C:1]  (received B's clock, incremented C)   │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Comparison:                                                          │  │
│  │  • V1 ≤ V2 if ∀i: V1[i] ≤ V2[i]                                      │  │
│  │  • V1 < V2 if V1 ≤ V2 and V1 ≠ V2                                    │  │
│  │  • Concurrent if neither V1 ≤ V2 nor V2 ≤ V1                         │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  [2,1,0] vs [1,2,0]  → CONCURRENT (neither dominates)           │  │  │
│  │  │  [2,1,0] vs [2,2,1]  → [2,1,0] < [2,2,1] (causally related)     │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Used for: Conflict detection in Dynamo-style systems, Riak          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HYBRID LOGICAL CLOCKS (HLC)                                                │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Combines physical time with logical counter:                         │  │
│  │                                                                       │  │
│  │  HLC = (physical_time, logical_counter)                               │  │
│  │                                                                       │  │
│  │  • Uses physical time when possible (human-readable)                 │  │
│  │  • Falls back to logical counter when clocks are close               │  │
│  │  • Bounded drift from physical time                                  │  │
│  │                                                                       │  │
│  │  Used by: CockroachDB, Spanner (TrueTime)                            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHAPTER 8 SUMMARY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DISTRIBUTED SYSTEMS FUNDAMENTALS                                           │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  Why Distributed Systems:                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ • Scalability: Handle more load than single machine                   │  │
│  │ • Fault Tolerance: Continue operating despite failures                │  │
│  │ • Geographic Distribution: Reduce latency, compliance                 │  │
│  │ • Performance: Parallel processing across machines                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Key Challenges:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ • Network is unreliable (8 fallacies of distributed computing)        │  │
│  │ • Partial failures: Some nodes fail while others continue             │  │
│  │ • No global clock: Cannot rely on synchronized time                   │  │
│  │ • Message delays, losses, duplicates, reordering                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CAP THEOREM                                                                │
│  ═══════════                                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Pick two (during partition):                                         │  │
│  │                                                                       │  │
│  │         Consistency                                                   │  │
│  │            /\                                                         │  │
│  │           /  \                                                        │  │
│  │          /    \                                                       │  │
│  │         /      \                                                      │  │
│  │  Availability ── Partition Tolerance                                  │  │
│  │                                                                       │  │
│  │  CP Systems: Sacrifice availability (banks, ZooKeeper)                │  │
│  │  AP Systems: Sacrifice consistency (DNS, Cassandra)                   │  │
│  │                                                                       │  │
│  │  PACELC: During Partition (A vs C), Else (Latency vs Consistency)     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CONSISTENCY MODELS (Strongest to Weakest)                                  │
│  ═════════════════════════════════════════                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Linearizability (Strongest)                                       │  │
│  │     └─ Operations appear instantaneous, respect real-time order       │  │
│  │                                                                       │  │
│  │  2. Sequential Consistency                                            │  │
│  │     └─ Total order respects each client's order (not real-time)       │  │
│  │                                                                       │  │
│  │  3. Causal Consistency                                                │  │
│  │     └─ Causally related operations seen in same order                 │  │
│  │                                                                       │  │
│  │  4. Eventual Consistency (Weakest)                                    │  │
│  │     └─ Replicas eventually converge if no new updates                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TIME AND ORDERING                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Physical Clocks: Unreliable (drift, skew), cannot order events       │  │
│  │                                                                       │  │
│  │  Lamport Clocks: Single counter, captures happens-before              │  │
│  │                  • If a → b, then L(a) < L(b)                         │  │
│  │                  • Cannot detect concurrent events                    │  │
│  │                                                                       │  │
│  │  Vector Clocks: One counter per node, detects concurrency             │  │
│  │                 • Can determine: a → b, b → a, or concurrent          │  │
│  │                 • Size grows with number of nodes                     │  │
│  │                                                                       │  │
│  │  Hybrid Logical Clocks: Best of both worlds                           │  │
│  │                         • Physical time + logical counter             │  │
│  │                         • Used by CockroachDB, Spanner                │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  KEY TAKEAWAYS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Distributed systems require explicit handling of failures         │  │
│  │  2. Network partitions will happen - design for them                  │  │
│  │  3. Choose consistency model based on application requirements        │  │
│  │  4. Use logical clocks for ordering, not physical time                │  │
│  │  5. Understand the tradeoffs: consistency vs availability vs latency  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Next Chapter: [Chapter 9: Failure Detection](./09-failure-detection.md)**

**Previous Chapter: [Chapter 7: Log-Structured Storage](./07-log-structured-storage.md)**