# Chapter 12: Distributed Transactions

## Table of Contents

1. [Introduction](#introduction)
2. [Atomic Commit Problem](#atomic-commit-problem)
3. [Two-Phase Commit (2PC)](#two-phase-commit-2pc)
4. [Three-Phase Commit (3PC)](#three-phase-commit-3pc)
5. [Distributed Transaction Patterns](#distributed-transaction-patterns)
6. [Calvin and Deterministic Databases](#calvin-and-deterministic-databases)
7. [Google Spanner](#google-spanner)
8. [Saga Pattern](#saga-pattern)
9. [Summary](#summary)
10. [Navigation](#navigation)

---

## Introduction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DISTRIBUTED TRANSACTIONS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE CHALLENGE                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  In a distributed system, a single transaction may span multiple     │  │
│  │  nodes. We need ALL nodes to either commit or abort together.         │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Transfer $100 from Account A (Node 1) to Account B (Node 2)    │  │  │
│  │  │                                                                 │  │  │
│  │  │     Node 1                          Node 2                      │  │  │
│  │  │    ┌────────────┐                  ┌────────────┐               │  │  │
│  │  │    │ Account A  │                  │ Account B  │               │  │  │
│  │  │    │ Balance:   │                  │ Balance:   │               │  │  │
│  │  │    │ $500       │                  │ $200       │               │  │  │
│  │  │    └────────────┘                  └────────────┘               │  │  │
│  │  │                                                                 │  │  │
│  │  │  Operation: A -= $100, B += $100                                │  │  │
│  │  │                                                                 │  │  │
│  │  │  What if Node 1 commits but Node 2 crashes before committing?   │  │  │
│  │  │  → $100 disappears! Money is lost!                              │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REQUIREMENTS                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ATOMICITY: All-or-nothing across all participating nodes            │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  ✗ Partial commits:                                             │  │  │
│  │  │    Node1: COMMITTED     Node2: ABORTED                          │  │  │
│  │  │                                                                 │  │  │
│  │  │  ✓ Consistent outcomes:                                         │  │  │
│  │  │    Node1: COMMITTED     Node2: COMMITTED                        │  │  │
│  │  │    or                                                           │  │  │
│  │  │    Node1: ABORTED       Node2: ABORTED                          │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Additional Goals:                                                    │  │
│  │  • Agreement: All nodes decide the same outcome                       │  │
│  │  • Validity: If any node aborts, all must abort                       │  │
│  │  • Termination: All non-failed nodes eventually decide                │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Atomic Commit Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ATOMIC COMMIT PROBLEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  THE CORE DIFFICULTY                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Nodes must make an IRREVOCABLE decision, but they can't know         │  │
│  │  what other nodes will decide (or if they'll even respond).           │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Timeline of a distributed transaction:                         │  │  │
│  │  │                                                                 │  │  │
│  │  │  Coordinator        Participant A        Participant B          │  │  │
│  │  │       │                   │                    │                │  │  │
│  │  │       │── "Prepare" ─────▶│                    │                │  │  │
│  │  │       │── "Prepare" ─────────────────────────▶│                │  │  │
│  │  │       │                   │                    │                │  │  │
│  │  │       │◀── "Ready" ──────│                    │                │  │  │
│  │  │       │                   │           ????     │                │  │  │
│  │  │       │                   │      (crashed? slow? network?)      │  │  │
│  │  │                                                                 │  │  │
│  │  │  Coordinator doesn't know if B is ready or crashed!             │  │  │
│  │  │  Can't safely commit or abort.                                  │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FUNDAMENTAL LIMITS                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  FLP IMPOSSIBILITY (Fischer, Lynch, Paterson, 1985):                  │  │
│  │  ─────────────────────────────────────────────────────                │  │
│  │                                                                       │  │
│  │  In an asynchronous system with even ONE faulty process,              │  │
│  │  there is NO protocol that guarantees consensus.                      │  │
│  │                                                                       │  │
│  │  Implications:                                                        │  │
│  │  • Cannot distinguish slow node from crashed node                     │  │
│  │  • Must make trade-offs:                                              │  │
│  │    - Safety (never commit inconsistently)                             │  │
│  │    - Liveness (always make progress)                                  │  │
│  │                                                                       │  │
│  │  Practical protocols sacrifice liveness (blocking) for safety         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Two-Phase Commit (2PC)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TWO-PHASE COMMIT (2PC)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The classic atomic commit protocol. Simple but BLOCKING.                   │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │              ┌─────────────────────┐                                  │  │
│  │              │    COORDINATOR      │                                  │  │
│  │              │  (Transaction Mgr)  │                                  │  │
│  │              └──────────┬──────────┘                                  │  │
│  │                         │                                             │  │
│  │         ┌───────────────┼───────────────┐                             │  │
│  │         │               │               │                             │  │
│  │         ▼               ▼               ▼                             │  │
│  │   ┌───────────┐  ┌───────────┐  ┌───────────┐                         │  │
│  │   │Participant│  │Participant│  │Participant│                         │  │
│  │   │    A      │  │    B      │  │    C      │                         │  │
│  │   └───────────┘  └───────────┘  └───────────┘                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  THE TWO PHASES                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  PHASE 1: PREPARE (Voting Phase)                                      │  │
│  │  ───────────────────────────────                                      │  │
│  │                                                                       │  │
│  │  Coordinator         Participant A         Participant B              │  │
│  │       │                    │                     │                    │  │
│  │       │                    │                     │                    │  │
│  │       │─── PREPARE ───────▶│                     │                    │  │
│  │       │─── PREPARE ─────────────────────────────▶│                    │  │
│  │       │                    │                     │                    │  │
│  │       │                    │  Lock resources     │  Lock resources    │  │
│  │       │                    │  Write to WAL       │  Write to WAL      │  │
│  │       │                    │                     │                    │  │
│  │       │◀── VOTE: YES ─────│                     │                    │  │
│  │       │◀── VOTE: YES ────────────────────────────│                    │  │
│  │       │                    │                     │                    │  │
│  │                                                                       │  │
│  │  Each participant:                                                    │  │
│  │  1. Executes transaction operations                                   │  │
│  │  2. Writes PREPARE record to WAL                                      │  │
│  │  3. Votes YES (can commit) or NO (must abort)                         │  │
│  │  4. Holds locks until final decision                                  │  │
│  │                                                                       │  │
│  │  ────────────────────────────────────────────────────────────────     │  │
│  │                                                                       │  │
│  │  PHASE 2: COMMIT (Decision Phase)                                     │  │
│  │  ─────────────────────────────────                                    │  │
│  │                                                                       │  │
│  │  Coordinator         Participant A         Participant B              │  │
│  │       │                    │                     │                    │  │
│  │       │  (all voted YES)   │                     │                    │  │
│  │       │                    │                     │                    │  │
│  │       │─── COMMIT ────────▶│                     │                    │  │
│  │       │─── COMMIT ──────────────────────────────▶│                    │  │
│  │       │                    │                     │                    │  │
│  │       │                    │  Commit changes     │  Commit changes    │  │
│  │       │                    │  Release locks      │  Release locks     │  │
│  │       │                    │                     │                    │  │
│  │       │◀── ACK ───────────│                     │                    │  │
│  │       │◀── ACK ─────────────────────────────────│                    │  │
│  │       │                    │                     │                    │  │
│  │                                                                       │  │
│  │  If ANY participant voted NO, coordinator sends ABORT instead.        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  STATE MACHINES                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  COORDINATOR:                                                         │  │
│  │  ┌────────┐  send    ┌─────────┐  all YES  ┌───────────┐              │  │
│  │  │ INIT   │─PREPARE─▶│ WAITING │──────────▶│ COMMITTED │              │  │
│  │  └────────┘          └────┬────┘           └───────────┘              │  │
│  │                           │ any NO                                    │  │
│  │                           ▼                                           │  │
│  │                     ┌───────────┐                                     │  │
│  │                     │  ABORTED  │                                     │  │
│  │                     └───────────┘                                     │  │
│  │                                                                       │  │
│  │  PARTICIPANT:                                                         │  │
│  │  ┌────────┐ receive  ┌──────────┐   COMMIT  ┌───────────┐             │  │
│  │  │ INIT   │─PREPARE─▶│ PREPARED │──────────▶│ COMMITTED │             │  │
│  │  └────────┘          └─────┬────┘           └───────────┘             │  │
│  │                            │ ABORT                                    │  │
│  │                            ▼                                          │  │
│  │                      ┌───────────┐                                    │  │
│  │                      │  ABORTED  │                                    │  │
│  │                      └───────────┘                                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  THE BLOCKING PROBLEM                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Once a participant votes YES, it MUST wait for coordinator decision │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Participant A: "I voted YES"                                   │  │  │
│  │  │  Participant B: "I voted YES"                                   │  │  │
│  │  │  Coordinator:   *crashes*                                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  Participants are STUCK:                                        │  │  │
│  │  │  • Can't commit (don't know if coordinator decided to commit)   │  │  │
│  │  │  • Can't abort (don't know if other participants committed)     │  │  │
│  │  │  • Must HOLD LOCKS until coordinator recovers!                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  This is the "in-doubt" or "uncertain" state                    │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Even worse: Coordinator AND one participant crash              │  │  │
│  │  │                                                                 │  │  │
│  │  │  Participant A: "I voted YES"                                   │  │  │
│  │  │  Participant B: *crashes* (had voted YES before crash)          │  │  │
│  │  │  Coordinator:   *crashes*                                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  Participant A cannot safely decide! Even asking B won't help   │  │  │
│  │  │  since both B and coordinator might have committed before crash │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  RECOVERY                                                                   │
│  ════════                                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  All state changes are logged to WAL before any action               │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Coordinator WAL:              Participant WAL:                 │  │  │
│  │  │  ─────────────────             ────────────────                 │  │  │
│  │  │  • Transaction started         • PREPARE received              │  │  │
│  │  │  • Participants list           • Vote YES written              │  │  │
│  │  │  • PREPARE sent                • COMMIT/ABORT received         │  │  │
│  │  │  • Decision (COMMIT/ABORT)     • Transaction completed         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  On recovery:                                                         │  │
│  │  • If no COMMIT in log → safe to abort                                │  │
│  │  • If COMMIT in log → must complete the commit                        │  │
│  │  • Participant in PREPARED state → ask coordinator for decision       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Three-Phase Commit (3PC)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THREE-PHASE COMMIT (3PC)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Adds a PRE-COMMIT phase to avoid blocking in some cases.                   │
│                                                                             │
│  THE THREE PHASES                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  PHASE 1: CAN-COMMIT (Same as 2PC prepare)                            │  │
│  │                                                                       │  │
│  │  Coordinator         Participant A         Participant B              │  │
│  │       │                    │                     │                    │  │
│  │       │─── CAN-COMMIT ────▶│                     │                    │  │
│  │       │─── CAN-COMMIT ──────────────────────────▶│                    │  │
│  │       │◀── YES ────────────│                     │                    │  │
│  │       │◀── YES ─────────────────────────────────│                    │  │
│  │                                                                       │  │
│  │  ────────────────────────────────────────────────────────────────     │  │
│  │                                                                       │  │
│  │  PHASE 2: PRE-COMMIT (The new phase!)                                 │  │
│  │                                                                       │  │
│  │  Coordinator         Participant A         Participant B              │  │
│  │       │                    │                     │                    │  │
│  │       │─── PRE-COMMIT ────▶│                     │                    │  │
│  │       │─── PRE-COMMIT ──────────────────────────▶│                    │  │
│  │       │◀── ACK ────────────│                     │                    │  │
│  │       │◀── ACK ─────────────────────────────────│                    │  │
│  │                                                                       │  │
│  │  Participants know: "Coordinator decided to commit"                   │  │
│  │  But haven't committed yet - can still abort if coordinator crashes  │  │
│  │                                                                       │  │
│  │  ────────────────────────────────────────────────────────────────     │  │
│  │                                                                       │  │
│  │  PHASE 3: DO-COMMIT                                                   │  │
│  │                                                                       │  │
│  │  Coordinator         Participant A         Participant B              │  │
│  │       │                    │                     │                    │  │
│  │       │─── DO-COMMIT ─────▶│                     │                    │  │
│  │       │─── DO-COMMIT ───────────────────────────▶│                    │  │
│  │       │◀── ACK ────────────│                     │                    │  │
│  │       │◀── ACK ─────────────────────────────────│                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHY THREE PHASES HELPS                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  If coordinator crashes after PRE-COMMIT:                             │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Participants received PRE-COMMIT → they know decision is COMMIT│  │  │
│  │  │  Can elect new coordinator and proceed with COMMIT              │  │  │
│  │  │                                                                 │  │  │
│  │  │  vs. 2PC: "I voted YES but don't know the decision"             │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  If coordinator crashes before PRE-COMMIT:                            │  │
│  │  Participants can safely ABORT (no one committed yet)                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LIMITATIONS OF 3PC                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Still has problems with NETWORK PARTITIONS:                          │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Scenario:                                                      │  │  │
│  │  │  • Coordinator sends PRE-COMMIT to A (received)                 │  │  │
│  │  │  • Network partition! B doesn't receive PRE-COMMIT              │  │  │
│  │  │  • Coordinator crashes                                          │  │  │
│  │  │                                                                 │  │  │
│  │  │  A thinks: "Got PRE-COMMIT, should commit"                      │  │  │
│  │  │  B thinks: "No PRE-COMMIT after timeout, should abort"          │  │  │
│  │  │                                                                 │  │  │
│  │  │  INCONSISTENT STATE!                                            │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  3PC only helps with CRASH failures, not NETWORK failures             │  │
│  │  This is why 3PC is rarely used in practice                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  2PC vs 3PC COMPARISON                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Property          │  2PC             │  3PC                          │  │
│  │  ═══════════════════════════════════════════════════════════════════  │  │
│  │  Message rounds    │  2               │  3                            │  │
│  │  Blocking          │  Yes (always)    │  No (crash only)              │  │
│  │  Network partition │  Safe but blocks │  May be inconsistent!         │  │
│  │  Complexity        │  Simple          │  More complex                 │  │
│  │  Practical use     │  Very common     │  Rare                         │  │
│  │                                                                       │  │
│  │  Conclusion: 2PC is preferred; use consensus protocols instead       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Distributed Transaction Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED TRANSACTION PATTERNS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Modern systems use various patterns to handle distributed transactions     │
│                                                                             │
│  XA TRANSACTIONS                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Standard interface for 2PC across heterogeneous systems              │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │              ┌────────────────────┐                             │  │  │
│  │  │              │ Transaction Manager│                             │  │  │
│  │  │              │      (TM)          │                             │  │  │
│  │  │              └─────────┬──────────┘                             │  │  │
│  │  │                        │ XA Protocol                            │  │  │
│  │  │         ┌──────────────┼──────────────┐                         │  │  │
│  │  │         │              │              │                         │  │  │
│  │  │         ▼              ▼              ▼                         │  │  │
│  │  │   ┌──────────┐  ┌──────────┐  ┌──────────┐                      │  │  │
│  │  │   │ Database │  │ Message  │  │  Other   │                      │  │  │
│  │  │   │  (RM)    │  │  Queue   │  │   RM     │                      │  │  │
│  │  │   └──────────┘  └──────────┘  └──────────┘                      │  │  │
│  │  │                                                                 │  │  │
│  │  │  RM = Resource Manager (database, queue, etc.)                  │  │  │
│  │  │  TM = Transaction Manager (coordinator)                         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Pros: Standard, widely supported                                     │  │
│  │  Cons: Blocking, high latency, scalability limits                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TRANSACTION OUTBOX PATTERN                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Reliably publish events with local database transactions             │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Instead of:                                                    │  │  │
│  │  │    1. Write to DB                                               │  │  │
│  │  │    2. Publish to message queue  ← May fail after DB commit!     │  │  │
│  │  │                                                                 │  │  │
│  │  │  Do this:                                                       │  │  │
│  │  │    1. Write to DB (business data)                               │  │  │
│  │  │    2. Write to OUTBOX table (in same transaction)               │  │  │
│  │  │    3. Background process reads OUTBOX → publishes to queue      │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────────────────────────────────────────────────────┐   │  │  │
│  │  │  │                                                          │   │  │  │
│  │  │  │  ┌──────────────────┐      ┌───────────────────────────┐ │   │  │  │
│  │  │  │  │   Business DB    │      │      Outbox Table         │ │   │  │  │
│  │  │  │  │  ┌────────────┐  │      │  ┌─────────────────────┐  │ │   │  │  │
│  │  │  │  │  │ Orders     │  │      │  │ id | event | status│  │ │   │  │  │
│  │  │  │  │  │ Customers  │  │ ──▶  │  │ 1  | ...   | PENDING│  │ │   │  │  │
│  │  │  │  │  │ Products   │  │      │  │ 2  | ...   | SENT   │  │ │   │  │  │
│  │  │  │  │  └────────────┘  │      │  └─────────────────────┘  │ │   │  │  │
│  │  │  │  └──────────────────┘      └───────────────────────────┘ │   │  │  │
│  │  │  │            Same transaction                              │   │  │  │
│  │  │  └──────────────────────────────────────────────────────────┘   │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Calvin and Deterministic Databases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   CALVIN: DETERMINISTIC DATABASES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  A radically different approach: determine execution order BEFORE executing │
│                                                                             │
│  KEY INSIGHT                                                                │
│  ═══════════                                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Traditional 2PC problem: Nodes execute independently, then try to    │  │
│  │  agree on outcome → requires coordination and blocking                │  │
│  │                                                                       │  │
│  │  Calvin insight: Agree on ORDER first, then execute deterministically │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  If all nodes:                                                  │  │  │
│  │  │    1. See the same transactions in the same order               │  │  │
│  │  │    2. Execute them deterministically (same input → same output) │  │  │
│  │  │                                                                 │  │  │
│  │  │  Then all nodes will end up in the same state!                  │  │  │
│  │  │  No need for 2PC!                                               │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ARCHITECTURE                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │                    ┌───────────────────────┐                          │  │
│  │                    │     SEQUENCER         │                          │  │
│  │                    │  (Orders all txns)    │                          │  │
│  │                    └───────────┬───────────┘                          │  │
│  │                                │                                      │  │
│  │                    ┌───────────▼───────────┐                          │  │
│  │                    │    TRANSACTION LOG    │                          │  │
│  │                    │  [T1, T2, T3, T4...] │                          │  │
│  │                    └───────────┬───────────┘                          │  │
│  │                                │                                      │  │
│  │         ┌──────────────────────┼──────────────────────┐               │  │
│  │         │                      │                      │               │  │
│  │         ▼                      ▼                      ▼               │  │
│  │   ┌───────────┐          ┌───────────┐          ┌───────────┐         │  │
│  │   │ Executor  │          │ Executor  │          │ Executor  │         │  │
│  │   │ Node A    │          │ Node B    │          │ Node C    │         │  │
│  │   │           │          │           │          │           │         │  │
│  │   │ Execute   │          │ Execute   │          │ Execute   │         │  │
│  │   │ T1,T2,T3  │          │ T1,T2,T3  │          │ T1,T2,T3  │         │  │
│  │   │ in order  │          │ in order  │          │ in order  │         │  │
│  │   └───────────┘          └───────────┘          └───────────┘         │  │
│  │                                                                       │  │
│  │   All nodes execute same txns in same order → same final state!       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HANDLING DEPENDENT READS                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Challenge: Some transactions read data to decide what to write       │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Example: Transfer $100 if balance > $100                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  Can't pre-order because outcome depends on current balance!    │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Solution: RECONNAISSANCE phase                                       │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. Reconnaissance: Pre-read all data needed                    │  │  │
│  │  │  2. Sequencer: Assign order with the pre-read data              │  │  │
│  │  │  3. Execute: Run deterministically with pre-read values         │  │  │
│  │  │                                                                 │  │  │
│  │  │  If data changed since reconnaissance → abort and retry         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  BENEFITS AND TRADE-OFFS                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ✓ No 2PC blocking                                                    │  │
│  │  ✓ High throughput (no distributed locking)                           │  │
│  │  ✓ Fast replication (just replicate the log)                          │  │
│  │                                                                       │  │
│  │  ✗ All transactions go through sequencer (bottleneck?)                │  │
│  │  ✗ Transactions must be deterministic                                 │  │
│  │  ✗ High abort rate for dependent reads in high-contention scenarios   │  │
│  │  ✗ Latency for multi-partition transactions                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Google Spanner

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GOOGLE SPANNER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Globally distributed database with strong consistency using TrueTime       │
│                                                                             │
│  THE TIME PROBLEM                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  For strong consistency across datacenters, we need a global order    │  │
│  │                                                                       │  │
│  │  Problem: Clocks are never perfectly synchronized!                    │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  US datacenter:  T1 at 10:00:00.000                             │  │  │
│  │  │  EU datacenter:  T2 at 10:00:00.001                             │  │  │
│  │  │                                                                 │  │  │
│  │  │  Is T1 really before T2?                                        │  │  │
│  │  │  What if US clock is 5ms ahead?                                 │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TRUETIME: BOUNDED CLOCK UNCERTAINTY                                        │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Instead of "current time is X", TrueTime returns an INTERVAL:       │  │
│  │                                                                       │  │
│  │  TrueTime API:                                                        │  │
│  │  ─────────────                                                        │  │
│  │  TT.now()  → [earliest, latest]                                       │  │
│  │  TT.after(t) → true if t is definitely in the past                    │  │
│  │  TT.before(t) → true if t is definitely in the future                 │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  TT.now() = [10:00:00.000, 10:00:00.007]                        │  │  │
│  │  │                                                                 │  │  │
│  │  │  "True time is somewhere in this 7ms window"                    │  │  │
│  │  │                                                                 │  │  │
│  │  │     ◀────────── ε ──────────▶                                   │  │  │
│  │  │  [earliest]               [latest]                              │  │  │
│  │  │     10:00:00.000          10:00:00.007                          │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ε (epsilon) is typically 1-7ms, maintained by:                       │  │
│  │  • GPS receivers in each datacenter                                   │  │
│  │  • Atomic clocks for redundancy                                       │  │
│  │  • Frequent clock synchronization                                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  COMMIT WAIT: THE KEY MECHANISM                                             │
│  ═══════════════════════════════                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  After getting all locks and deciding to commit, Spanner WAITS:       │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. Assign commit timestamp s = TT.now().latest                 │  │  │
│  │  │  2. Wait until TT.after(s) is true                              │  │  │
│  │  │  3. Then commit and release locks                               │  │  │
│  │  │                                                                 │  │  │
│  │  │  Wait time = 2ε (typically 2-14ms)                              │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Timeline:                                                      │  │  │
│  │  │                                                                 │  │  │
│  │  │       s = TT.now().latest                                       │  │  │
│  │  │            │                                                    │  │  │
│  │  │  ──────────┼────────────────┼─────────────▶ time                │  │  │
│  │  │            │     WAIT       │                                   │  │  │
│  │  │            │◀───  2ε  ─────▶│                                   │  │  │
│  │  │            │                │                                   │  │  │
│  │  │       Assign s          TT.after(s) = true                      │  │  │
│  │  │                         NOW SAFE TO COMMIT                      │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Why? After waiting, we GUARANTEE that:                               │  │
│  │    • No other node can get a timestamp ≤ s                            │  │
│  │    • Any transaction starting now will see our committed data         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  EXTERNAL CONSISTENCY                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Spanner provides "external consistency" (also called "linearizable"):│  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  If transaction T1 commits before T2 starts:                    │  │  │
│  │  │  • T1's commit timestamp < T2's commit timestamp                │  │  │
│  │  │  • T2 will see T1's writes                                      │  │  │
│  │  │                                                                 │  │  │
│  │  │  This holds ACROSS DATACENTERS worldwide!                       │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Commit wait ensures the real-time order matches the timestamp order  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PAXOS GROUPS                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Spanner uses Paxos for replication within each partition             │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │              ┌─────────────────────────────┐                    │  │  │
│  │  │              │       Spanner Database      │                    │  │  │
│  │  │              └─────────────────────────────┘                    │  │  │
│  │  │                          │                                      │  │  │
│  │  │        ┌─────────────────┼─────────────────┐                    │  │  │
│  │  │        │                 │                 │                    │  │  │
│  │  │        ▼                 ▼                 ▼                    │  │  │
│  │  │   ┌─────────┐       ┌─────────┐       ┌─────────┐               │  │  │
│  │  │   │Paxos    │       │Paxos    │       │Paxos    │               │  │  │
│  │  │   │Group 1  │       │Group 2  │       │Group 3  │               │  │  │
│  │  │   │(shard A)│       │(shard B)│       │(shard C)│               │  │  │
│  │  │   └────┬────┘       └────┬────┘       └────┬────┘               │  │  │
│  │  │        │                 │                 │                    │  │  │
│  │  │   ┌────┼────┐       ┌────┼────┐       ┌────┼────┐               │  │  │
│  │  │   ▼    ▼    ▼       ▼    ▼    ▼       ▼    ▼    ▼               │  │  │
│  │  │  [R1] [R2] [R3]    [R1] [R2] [R3]    [R1] [R2] [R3]             │  │  │
│  │  │  (replicas)        (replicas)        (replicas)                 │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  • Each Paxos group handles one shard                                 │  │
│  │  • 2PC coordinates BETWEEN Paxos groups for cross-shard transactions  │  │
│  │  • Paxos handles replication WITHIN each group                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Saga Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SAGA PATTERN                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  For LONG-RUNNING transactions that can't hold locks for extended periods  │
│                                                                             │
│  THE PROBLEM WITH LONG TRANSACTIONS                                         │
│  ══════════════════════════════════                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Example: Book a trip (flight + hotel + car)                          │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  With 2PC:                                                      │  │  │
│  │  │  • Lock flight seat for entire booking process                  │  │  │
│  │  │  • Lock hotel room for entire booking process                   │  │  │
│  │  │  • Lock rental car for entire booking process                   │  │  │
│  │  │  • Process might take minutes (waiting for payment, etc.)       │  │  │
│  │  │                                                                 │  │  │
│  │  │  PROBLEMS:                                                      │  │  │
│  │  │  • Locks held for too long                                      │  │  │
│  │  │  • Reduced availability                                         │  │  │
│  │  │  • Doesn't work well across organizational boundaries           │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SAGA SOLUTION: COMPENSATING TRANSACTIONS                                   │
│  ════════════════════════════════════════                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Instead of one big transaction, use sequence of small transactions  │  │
│  │  Each step has a COMPENSATING action to undo it if later steps fail  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Step                 │  Compensation                           │  │  │
│  │  │  ═════════════════════════════════════════════════════════════  │  │  │
│  │  │  Book flight          │  Cancel flight reservation              │  │  │
│  │  │  Book hotel           │  Cancel hotel reservation               │  │  │
│  │  │  Book rental car      │  Cancel car reservation                 │  │  │
│  │  │  Charge credit card   │  Refund credit card                     │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SAGA EXECUTION FLOW                                                        │
│  ═══════════════════                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Success case:                                                        │  │
│  │                                                                       │  │
│  │  T1 ───▶ T2 ───▶ T3 ───▶ T4 ───▶ DONE                                 │  │
│  │  (book    (book    (book    (charge                                   │  │
│  │  flight)  hotel)   car)     card)                                     │  │
│  │                                                                       │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │                                                                       │  │
│  │  Failure case (T3 fails):                                             │  │
│  │                                                                       │  │
│  │  T1 ───▶ T2 ───▶ T3 ──X                                               │  │
│  │                    │                                                  │  │
│  │                    └───▶ C2 ───▶ C1 ───▶ ROLLED BACK                  │  │
│  │                         (cancel  (cancel                              │  │
│  │                          hotel)   flight)                             │  │
│  │                                                                       │  │
│  │  C1, C2 = Compensating transactions                                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CHOREOGRAPHY vs ORCHESTRATION                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  CHOREOGRAPHY (Event-driven):                                         │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Each service publishes events; others listen and react        │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────┐     ┌──────────┐     ┌──────────┐                │  │  │
│  │  │  │  Flight  │────▶│  Hotel   │────▶│   Car    │                │  │  │
│  │  │  │ Service  │event│ Service  │event│ Service  │                │  │  │
│  │  │  └──────────┘     └──────────┘     └──────────┘                │  │  │
│  │  │       │                 │                 │                     │  │  │
│  │  │       ▼                 ▼                 ▼                     │  │  │
│  │  │   [Message Bus / Event Stream]                                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  ✓ Loose coupling                                               │  │  │
│  │  │  ✓ Each service is independent                                  │  │  │
│  │  │  ✗ Hard to understand overall flow                              │  │  │
│  │  │  ✗ Complex failure handling                                     │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ORCHESTRATION (Central coordinator):                                 │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Central orchestrator tells each service what to do             │  │  │
│  │  │                                                                 │  │  │
│  │  │              ┌──────────────────┐                               │  │  │
│  │  │              │   Orchestrator   │                               │  │  │
│  │  │              │   (Saga Engine)  │                               │  │  │
│  │  │              └────────┬─────────┘                               │  │  │
│  │  │         ┌─────────────┼─────────────┐                           │  │  │
│  │  │         ▼             ▼             ▼                           │  │  │
│  │  │    ┌────────┐    ┌────────┐    ┌────────┐                       │  │  │
│  │  │    │ Flight │    │ Hotel  │    │  Car   │                       │  │  │
│  │  │    │Service │    │Service │    │Service │                       │  │  │
│  │  │    └────────┘    └────────┘    └────────┘                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  ✓ Clear flow visible in one place                              │  │  │
│  │  │  ✓ Easier failure handling                                      │  │  │
│  │  │  ✗ Single point of failure                                      │  │  │
│  │  │  ✗ Tighter coupling to orchestrator                             │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SAGA ISOLATION AND ANOMALIES                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Sagas do NOT provide ACID isolation!                                 │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Possible anomalies:                                            │  │  │
│  │  │                                                                 │  │  │
│  │  │  • Lost updates: Two sagas update same record                   │  │  │
│  │  │  • Dirty reads: Saga reads data that will be compensated       │  │  │
│  │  │  • Non-repeatable reads: Same read returns different values    │  │  │
│  │  │                                                                 │  │  │
│  │  │  Countermeasures:                                               │  │  │
│  │  │  • Semantic locks (mark records as "in progress")               │  │  │
│  │  │  • Commutative operations (order doesn't matter)                │  │  │
│  │  │  • Pessimistic view (read latest committed)                     │  │  │
│  │  │  • Reread values before critical operations                     │  │  │
│  │  │  • Version files (record operations, not values)                │  │  │
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
│                 DISTRIBUTED TRANSACTIONS COMPARISON                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Protocol     │ Blocking │ Net Part │ Latency   │ Use Case            │  │
│  │  ═════════════════════════════════════════════════════════════════════│  │
│  │  2PC          │ Yes      │ Safe     │ 2 RTT     │ Cross-DB txns       │  │
│  │  3PC          │ No(crash)│ UNSAFE!  │ 3 RTT     │ Rarely used         │  │
│  │  Calvin       │ No       │ Safe     │ Sequencer │ High throughput     │  │
│  │  Spanner      │ 2ε wait  │ Safe     │ ~7ms wait │ Global consistency  │  │
│  │  Sagas        │ No       │ Safe     │ Varies    │ Long-running txns   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  KEY TAKEAWAYS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. 2PC is the foundation but has blocking problem                    │  │
│  │                                                                       │  │
│  │  2. 3PC tries to solve blocking but fails with network partitions     │  │
│  │                                                                       │  │
│  │  3. Consensus protocols (Paxos, Raft) are better for replication      │  │
│  │                                                                       │  │
│  │  4. Deterministic databases (Calvin) avoid coordination by ordering   │  │
│  │     transactions upfront                                              │  │
│  │                                                                       │  │
│  │  5. Spanner uses TrueTime to provide external consistency globally    │  │
│  │                                                                       │  │
│  │  6. Sagas trade isolation for availability in long-running processes  │  │
│  │                                                                       │  │
│  │  7. There is no perfect solution - choose based on requirements       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHEN TO USE WHAT                                                           │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Need strong consistency within datacenter?                           │  │
│  │    → 2PC with good recovery (PostgreSQL, MySQL)                       │  │
│  │                                                                       │  │
│  │  Need global strong consistency?                                      │  │
│  │    → Spanner or CockroachDB                                           │  │
│  │                                                                       │  │
│  │  Need maximum throughput, can pre-order transactions?                 │  │
│  │    → Calvin-style deterministic database                              │  │
│  │                                                                       │  │
│  │  Long-running business process across services?                       │  │
│  │    → Saga pattern                                                     │  │
│  │                                                                       │  │
│  │  Need reliable messaging with database?                               │  │
│  │    → Transactional Outbox pattern                                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Navigation

| Previous | Up | Next |
|----------|-----|------|
| [← Chapter 11: Replication and Consistency](./11-replication-consistency.md) | [Index](./README.md) | [Chapter 13: Consensus Algorithms →](./13-consensus-algorithms.md) |
