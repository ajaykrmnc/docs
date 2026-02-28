# Distributed Transactions

## Overview

Distributed transactions span multiple nodes, databases, or resource managers. Jim Gray's work on distributed transaction protocols, particularly the Two-Phase Commit (2PC), remains foundational to distributed systems today.

---

## The Challenge of Distribution

### Why Distributed Transactions are Hard

```
┌─────────────────────────────────────────────────────────────────┐
│                 DISTRIBUTED TRANSACTION CHALLENGES              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PARTIAL FAILURES                                            │
│     - Some nodes may fail while others succeed                  │
│     - Network partitions can isolate nodes                      │
│                                                                 │
│  2. NO GLOBAL STATE                                             │
│     - No single point knows complete system state               │
│     - Messages have non-zero transmission time                  │
│                                                                 │
│  3. ASYNCHRONY                                                  │
│     - Cannot distinguish slow node from failed node             │
│     - Timeouts are imperfect failure detectors                  │
│                                                                 │
│  4. CONSISTENCY vs AVAILABILITY                                 │
│     - CAP theorem: cannot have all three (C, A, P)              │
│     - Must choose trade-offs                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Distributed Transaction Model

```
                    ┌─────────────────┐
                    │  Coordinator    │
                    │  (Transaction   │
                    │   Manager)      │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ Participant │   │ Participant │   │ Participant │
    │   (RM 1)    │   │   (RM 2)    │   │   (RM 3)    │
    │             │   │             │   │             │
    │  Database   │   │  Queue      │   │  Database   │
    │  Server A   │   │  Manager    │   │  Server B   │
    └─────────────┘   └─────────────┘   └─────────────┘

RM = Resource Manager
```

---

## Two-Phase Commit Protocol (2PC)

### Overview

2PC ensures all participants either commit or abort together (atomicity across distributed nodes).

### Phase 1: Prepare (Voting)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 1: PREPARE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Coordinator                    Participants                    │
│      │                              │                           │
│      │──── PREPARE ────────────────►│                           │
│      │                              │                           │
│      │                         ┌────┴────┐                      │
│      │                         │ Can I   │                      │
│      │                         │ commit? │                      │
│      │                         └────┬────┘                      │
│      │                              │                           │
│      │◄─── VOTE (YES/NO) ──────────│                           │
│      │                              │                           │
│  ┌───┴───┐                                                      │
│  │Collect│  If ALL votes = YES → proceed to Phase 2 (COMMIT)   │
│  │ votes │  If ANY vote = NO  → proceed to Phase 2 (ABORT)     │
│  └───────┘                                                      │
│                                                                 │
│  VOTE YES means:                                                │
│  • Participant has acquired all locks                           │
│  • All updates are logged (can be redone)                       │
│  • Participant PROMISES to commit if asked                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2: Commit/Abort (Decision)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 2: COMMIT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Coordinator                    Participants                    │
│      │                              │                           │
│      │──── COMMIT ─────────────────►│                           │
│      │     (or ABORT)               │                           │
│      │                              │                           │
│      │                         ┌────┴────┐                      │
│      │                         │ Apply   │                      │
│      │                         │ decision│                      │
│      │                         └────┬────┘                      │
│      │                              │                           │
│      │◄─── ACK ────────────────────│                           │
│      │                              │                           │


---

## 2PC Failure Handling

### The "In Doubt" Problem

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE IN-DOUBT STATE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Participant voted YES but hasn't received decision             │
│                                                                 │
│  Timeline:                                                      │
│  ─────────────────────────────────────────────────────────────  │
│  │ PREPARE │ Vote YES │ ... waiting ... │ ??? │                │
│  ─────────────────────────────────────────────────────────────  │
│                            ↑                                    │
│                     Participant is                              │
│                     "in doubt"                                  │
│                                                                 │
│  In doubt, participant:                                         │
│  • Cannot commit (don't know coordinator's decision)            │
│  • Cannot abort (promised to commit if asked)                   │
│  • Must HOLD LOCKS until resolved                               │
│  • Is BLOCKING other transactions                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Coordinator Failure Scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│            COORDINATOR FAILURE SCENARIOS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BEFORE sending PREPARE:                                        │
│  → All participants abort (no work done)                        │
│                                                                 │
│  AFTER sending PREPARE, BEFORE decision:                        │
│  → Participants are IN DOUBT                                    │
│  → Must wait for coordinator recovery                           │
│  → BLOCKING!                                                    │
│                                                                 │
│  AFTER logging decision, BEFORE sending:                        │
│  → Coordinator recovery will resend decision                    │
│  → Non-blocking                                                 │
│                                                                 │
│  AFTER sending decision:                                        │
│  → Transaction completes normally                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Participant Failure Scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│             PARTICIPANT FAILURE SCENARIOS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BEFORE voting:                                                 │
│  → Coordinator times out                                        │
│  → Coordinator aborts (vote considered NO)                      │
│                                                                 │
│  AFTER voting YES:                                              │
│  → Participant recovers                                         │
│  → Checks log for PREPARED record                               │
│  → Asks coordinator for decision                                │
│                                                                 │
│  Recovery protocol:                                             │
│  IF find COMMIT record → already committed, done                │
│  IF find ABORT record → already aborted, done                   │
│  IF find PREPARED record → contact coordinator                  │
│  IF no record → transaction never prepared, abort               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2PC Optimizations

### Presumed Abort

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESUMED ABORT                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Optimization for abort case (which is rare in practice)        │
│                                                                 │
│  Rules:                                                         │
│  • Coordinator does NOT log ABORT decision                      │
│  • Participants do NOT send ACK for ABORT                       │
│  • If participant asks about unknown transaction → ABORT        │
│                                                                 │
│  Cost savings:                                                  │
│  • 1 less forced log write (no abort log)                       │
│  • N fewer messages (no abort ACKs)                             │
│                                                                 │
│  Trade-off:                                                     │
│  • COMMIT must be logged before sending                         │
│  • COMMIT ACKs required (to know when to forget)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Presumed Commit

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESUMED COMMIT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Optimization for commit case (common path)                     │
│                                                                 │
│  Rules:                                                         │
│  • Coordinator does NOT log COMMIT decision                     │
│  • Participants do NOT send ACK for COMMIT                      │
│  • If participant asks about unknown transaction → COMMIT       │
│                                                                 │
│  More complex because:                                          │
│  • Must log "collecting" state before prepare                   │
│  • Must know participant list to distinguish:                   │
│    - Unknown (presumed commit)                                  │
│    - Known but not started (abort)                              │
│                                                                 │
│  Better for commit-heavy workloads                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Read-Only Optimization

```
If participant did read-only work:
  • Vote READ-ONLY instead of YES
  • Coordinator excludes from Phase 2
  • Participant releases locks immediately
  • Fewer messages in Phase 2
```

---

## Three-Phase Commit (3PC)

### Motivation: Non-Blocking Commit

2PC is blocking - participants may wait indefinitely if coordinator fails.
3PC attempts to make the protocol non-blocking.

### 3PC Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│                 THREE-PHASE COMMIT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: CAN COMMIT? (Same as 2PC Prepare)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Coordinator → Participants: "Can you commit?"            │  │
│  │ Participants → Coordinator: YES/NO vote                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  Phase 2: PRE-COMMIT (New phase!)                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ If all YES: Coordinator → Participants: PRE-COMMIT       │  │
│  │ Participants acknowledge, enter PRE-COMMITTED state      │  │
│  │                                                          │  │
│  │ Key insight: In PRE-COMMITTED state, we KNOW decision    │  │
│  │ will be COMMIT (barring total failure)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│  Phase 3: DO COMMIT                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Coordinator → Participants: DO COMMIT                    │  │
│  │ Participants commit and acknowledge                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3PC State Diagram

```
COORDINATOR:                        PARTICIPANT:

  ┌─────────┐                         ┌─────────┐
  │ INITIAL │                         │ INITIAL │
  └────┬────┘                         └────┬────┘
       │                                   │
       ▼                                   ▼
  ┌─────────┐                         ┌─────────┐
  │  WAIT   │                         │ WAITING │
  └────┬────┘                         └────┬────┘
       │ All YES                           │ PRE-COMMIT
       ▼                                   ▼
  ┌─────────┐                         ┌─────────┐
  │PRE-COMM │ ←─ Non-blocking ──────► │PRE-COMM │
  └────┬────┘    point                └────┬────┘
       │                                   │
       ▼                                   ▼
  ┌─────────┐                         ┌─────────┐
  │COMMITTED│                         │COMMITTED│
  └─────────┘                         └─────────┘
```

### 3PC Recovery: Why Non-Blocking?

```
Key Property:
  If ANY participant is in PRE-COMMITTED state,
  NO participant can be in ABORTED state.

Recovery when coordinator fails:
  • Participants communicate with each other
  • If any is PRE-COMMITTED → all can commit
  • If any is ABORTED → all can abort
  • If all are WAITING → all can abort

No blocking because decision can be made locally!
```

### 3PC Limitations

```
┌─────────────────────────────────────────────────────────────────┐
│                    3PC LIMITATIONS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. NETWORK PARTITIONS                                          │
│     • 3PC assumes fail-stop (crash) failures                    │
│     • Network partitions can cause inconsistency                │
│     • One partition commits, other aborts                       │
│                                                                 │
│  2. HIGHER LATENCY                                              │
│     • Extra round-trip for PRE-COMMIT phase                     │
│     • More messages: 3n vs 2n for n participants                │
│                                                                 │
│  3. RARELY USED IN PRACTICE                                     │
│     • 2PC with timeouts usually sufficient                      │
│     • Modern systems use consensus (Paxos, Raft)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Distributed Deadlock Detection

### Global Wait-For Graph

```
┌─────────────────────────────────────────────────────────────────┐
│               DISTRIBUTED DEADLOCK DETECTION                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Local Site A:          Local Site B:                           │
│  T1 → T2                T2 → T3                                 │
│                         T3 → T1                                 │
│                                                                 │
│  Global Wait-For Graph:                                         │
│        ┌────┐                                                   │
│        │ T1 │───────────────────┐                               │
│        └────┘                   │                               │
│           ↑                     ▼                               │
│        ┌────┐              ┌────┐                               │
│        │ T3 │◄─────────────│ T2 │                               │
│        └────┘              └────┘                               │
│                                                                 │
│  Cycle detected! T1 → T2 → T3 → T1                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Detection Approaches

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| Centralized | One node collects all wait-for info | Simple | Single point of failure |
| Hierarchical | Tree of detectors | Scalable | Complex |
| Distributed | Each node detects cycles | No SPOF | Phantom deadlocks |
| Timeout | Abort after waiting too long | Simple | May abort unnecessarily |

---

## X/Open DTP Model

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    X/OPEN DTP MODEL                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    APPLICATION                          │   │
│  │                    PROGRAM (AP)                          │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │ TX Interface                        │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               TRANSACTION MANAGER (TM)                   │   │
│  │                                                          │   │
│  │  • Coordinates global transactions                       │   │
│  │  • Implements 2PC protocol                               │   │
│  │  • Manages transaction log                               │   │
│  └──────────┬──────────────────────────────┬───────────────┘   │
│             │ XA Interface                  │ XA Interface      │
│             ▼                               ▼                   │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │  RESOURCE MANAGER 1  │      │  RESOURCE MANAGER 2  │        │
│  │  (Database)          │      │  (Message Queue)     │        │
│  └──────────────────────┘      └──────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### XA Interface Functions

```
xa_open()      - Connect to resource manager
xa_close()     - Disconnect from resource manager
xa_start()     - Start work on behalf of transaction
xa_end()       - End work on behalf of transaction
xa_prepare()   - Prepare to commit (Phase 1)
xa_commit()    - Commit transaction (Phase 2)
xa_rollback()  - Abort transaction
xa_recover()   - Get list of prepared transactions
xa_forget()    - Forget heuristically completed transaction
```

---

## Key Takeaways

1. **2PC** is the standard protocol for distributed atomicity
2. **"In doubt"** state is the key challenge - participant has voted but awaits decision
3. **Presumed abort** optimizes the common case (commit)
4. **3PC** adds non-blocking but doesn't handle network partitions
5. **XA interface** standardizes TM-RM communication
6. **Distributed deadlocks** require global coordination to detect

---

## References

- Gray, J. & Reuter, A. (1993). Chapters 10-12: "Distributed Transaction Processing"
- Gray, J. (1978). "Notes on Data Base Operating Systems"
- Mohan, C. & Lindsay, B. (1983). "Efficient Commit Protocols for the Tree of Processes Model"
- X/Open Company (1991). "Distributed Transaction Processing: The XA Specification"

### 2PC State Diagram

```
COORDINATOR:                        PARTICIPANT:

  ┌─────────┐                         ┌─────────┐
  │ INITIAL │                         │ INITIAL │
  └────┬────┘                         └────┬────┘
       │ Send PREPARE                      │ Receive PREPARE
       ▼                                   ▼
  ┌─────────┐                         ┌─────────┐
  │  WAIT   │                         │ PREPARED│ ← "In doubt"
  └────┬────┘                         └────┬────┘
       │ Receive all votes                 │ Receive decision
       ▼                                   ▼
  ┌─────────┐                         ┌─────────┐
  │COMMITTED│                         │COMMITTED│
  │or ABORT │                         │or ABORT │
  └─────────┘                         └─────────┘
```

