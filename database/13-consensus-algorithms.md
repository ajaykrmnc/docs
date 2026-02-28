# Chapter 13: Consensus Algorithms

## Table of Contents
1. [Introduction](#introduction)
2. [The Consensus Problem](#the-consensus-problem)
3. [Paxos](#paxos)
4. [Multi-Paxos](#multi-paxos)
5. [Raft](#raft)
6. [ZAB (Zookeeper Atomic Broadcast)](#zab-zookeeper-atomic-broadcast)
7. [Viewstamped Replication](#viewstamped-replication)
8. [Comparison and Practical Considerations](#comparison-and-practical-considerations)
9. [Summary](#summary)

---

## Introduction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONSENSUS ALGORITHMS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Fundamental building block for distributed systems reliability             │
│                                                                             │
│  WHAT IS CONSENSUS?                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Getting multiple nodes to agree on a single value                    │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │                    "What value was committed?"                  │  │  │
│  │  │                                                                 │  │  │
│  │  │      Node A               Node B               Node C          │  │  │
│  │  │         │                    │                    │            │  │  │
│  │  │    proposes X           proposes Y           proposes X        │  │  │
│  │  │         │                    │                    │            │  │  │
│  │  │         └────────────────────┼────────────────────┘            │  │  │
│  │  │                              ▼                                  │  │  │
│  │  │                    ┌─────────────────┐                          │  │  │
│  │  │                    │   CONSENSUS     │                          │  │  │
│  │  │                    │   ALGORITHM     │                          │  │  │
│  │  │                    └────────┬────────┘                          │  │  │
│  │  │                             ▼                                   │  │  │
│  │  │               All agree: "The value is X"                       │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHY CONSENSUS MATTERS                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Consensus enables:                                                   │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  • Leader election    - Who is the current leader?              │  │  │
│  │  │  • Atomic broadcast   - Deliver messages in same order          │  │  │
│  │  │  • Distributed locks  - Who holds the lock?                     │  │  │
│  │  │  • Configuration      - What is the cluster membership?         │  │  │
│  │  │  • Replicated state   - What is the committed log entry?        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Without consensus, distributed systems can have split-brain,         │  │
│  │  data loss, and inconsistent state.                                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Consensus Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE CONSENSUS PROBLEM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FORMAL DEFINITION                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Three properties a consensus algorithm must satisfy:                 │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. AGREEMENT (Safety)                                          │  │  │
│  │  │     All correct nodes decide on the same value                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  2. VALIDITY (Non-triviality)                                   │  │  │
│  │  │     The decided value was proposed by some node                 │  │  │
│  │  │     (can't just always return "42")                             │  │  │
│  │  │                                                                 │  │  │
│  │  │  3. TERMINATION (Liveness)                                      │  │  │
│  │  │     All correct nodes eventually decide                         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FLP IMPOSSIBILITY                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Fischer, Lynch, and Paterson (1985) proved:                          │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  In an ASYNCHRONOUS system where even ONE process can fail,     │  │  │
│  │  │  there is NO algorithm that guarantees consensus.               │  │  │
│  │  │                                                                 │  │  │
│  │  │  ═══════════════════════════════════════════════════════════    │  │  │
│  │  │                                                                 │  │  │
│  │  │  Why? Cannot distinguish between:                               │  │  │
│  │  │  • A crashed node                                               │  │  │
│  │  │  • A very slow node                                             │  │  │
│  │  │  • A node with slow network                                     │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  This doesn't mean consensus is impossible in practice!               │  │
│  │  It means we need to relax assumptions (use timeouts, randomization)  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SYSTEM MODELS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  SYNCHRONOUS MODEL                                              │  │  │
│  │  │  ─────────────────────                                          │  │  │
│  │  │  • Known upper bound on message delay                           │  │  │
│  │  │  • Known upper bound on processing time                         │  │  │
│  │  │  • Easy to detect failures (just use timeouts)                  │  │  │
│  │  │  • Consensus is SOLVABLE                                        │  │  │
│  │  │  • BUT: Unrealistic for real networks                           │  │  │
│  │  │                                                                 │  │  │
│  │  │  ───────────────────────────────────────────────────────────    │  │  │
│  │  │                                                                 │  │  │
│  │  │  ASYNCHRONOUS MODEL                                             │  │  │
│  │  │  ─────────────────────                                          │  │  │
│  │  │  • No bounds on message delay                                   │  │  │
│  │  │  • No bounds on processing time                                 │  │  │
│  │  │  • Cannot distinguish slow from failed                          │  │  │
│  │  │  • Consensus is IMPOSSIBLE (FLP)                                │  │  │
│  │  │  • Most realistic model                                         │  │  │
│  │  │                                                                 │  │  │
│  │  │  ───────────────────────────────────────────────────────────    │  │  │
│  │  │                                                                 │  │  │
│  │  │  PARTIALLY SYNCHRONOUS MODEL (practical)                        │  │  │
│  │  │  ────────────────────────────────────────                       │  │  │
│  │  │  • System is asynchronous, but eventually becomes synchronous   │  │  │
│  │  │  • OR: Bounds exist but are unknown                             │  │  │
│  │  │  • Consensus IS solvable with eventual termination              │  │  │
│  │  │  • This is what Paxos, Raft, etc. assume                        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  QUORUMS AND FAILURE TOLERANCE                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  MAJORITY QUORUM                                                │  │  │
│  │  │                                                                 │  │  │
│  │  │      Quorum size = ⌊N/2⌋ + 1  (majority)                        │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │  │  │
│  │  │  │                                                         │    │  │  │
│  │  │  │    5 nodes: quorum = 3    (can tolerate 2 failures)    │    │  │  │
│  │  │  │    3 nodes: quorum = 2    (can tolerate 1 failure)     │    │  │  │
│  │  │  │    7 nodes: quorum = 4    (can tolerate 3 failures)    │    │  │  │
│  │  │  │                                                         │    │  │  │
│  │  │  │    General: N nodes can tolerate ⌊(N-1)/2⌋ failures     │    │  │  │
│  │  │  │                                                         │    │  │  │
│  │  │  └─────────────────────────────────────────────────────────┘    │  │  │
│  │  │                                                                 │  │  │
│  │  │  WHY MAJORITIES?                                                │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │  │  │
│  │  │  │                                                         │    │  │  │
│  │  │  │  Any two majorities MUST overlap by at least one node   │    │  │  │
│  │  │  │                                                         │    │  │  │
│  │  │  │    Quorum 1:  [ A  B  C ]      (3 of 5)                 │    │  │  │
│  │  │  │    Quorum 2:  [    B  C  D ]   (3 of 5)                 │    │  │  │
│  │  │  │                   ↑  ↑                                  │    │  │  │
│  │  │  │               Overlap guarantees information transfer    │    │  │  │
│  │  │  │                                                         │    │  │  │
│  │  │  └─────────────────────────────────────────────────────────┘    │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Paxos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                    PAXOS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The foundational consensus algorithm (Leslie Lamport, 1989/1998)           │
│                                                                             │
│  ROLES IN PAXOS                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  PROPOSER                                                       │  │  │
│  │  │  • Proposes values to be agreed upon                            │  │  │
│  │  │  • Drives the protocol forward                                  │  │  │
│  │  │  • Multiple proposers can exist (leader election helps)         │  │  │
│  │  │                                                                 │  │  │
│  │  │  ─────────────────────────────────────────────────────────────  │  │  │
│  │  │                                                                 │  │  │
│  │  │  ACCEPTOR                                                       │  │  │
│  │  │  • Votes on proposals                                           │  │  │
│  │  │  • Stores accepted values durably                               │  │  │
│  │  │  • Must be a majority for safety                                │  │  │
│  │  │                                                                 │  │  │
│  │  │  ─────────────────────────────────────────────────────────────  │  │  │
│  │  │                                                                 │  │  │
│  │  │  LEARNER                                                        │  │  │
│  │  │  • Learns the decided value                                     │  │  │
│  │  │  • Does not participate in voting                               │  │  │
│  │  │  • Often combined with acceptor role                            │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  In practice: Each node plays all three roles                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  TWO PHASES OF BASIC PAXOS                                                  │
│  ═════════════════════════                                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  PHASE 1: PREPARE (Promise)                                           │  │
│  │  ──────────────────────────                                           │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Proposer                     Acceptors                         │  │  │
│  │  │      │                           │                              │  │  │
│  │  │      │───── Prepare(n) ─────────►│  "I want to propose with     │  │  │
│  │  │      │                           │   proposal number n"         │  │  │
│  │  │      │                           │                              │  │  │
│  │  │      │◄──── Promise(n, v) ───────│  "I promise not to accept    │  │  │
│  │  │      │                           │   proposals < n"             │  │  │
│  │  │      │                           │   Returns: previously        │  │  │
│  │  │      │                           │   accepted value (if any)    │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  PHASE 2: ACCEPT (Accepted)                                           │  │
│  │  ──────────────────────────                                           │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Proposer                     Acceptors                         │  │  │
│  │  │      │                           │                              │  │  │
│  │  │      │── Accept(n, value) ──────►│  "Please accept this value   │  │  │
│  │  │      │                           │   with proposal n"           │  │  │
│  │  │      │                           │                              │  │  │
│  │  │      │◄── Accepted(n, value) ────│  "I have accepted (n, v)"    │  │  │
│  │  │      │                           │                              │  │  │
│  │  │                                                                 │  │  │
│  │  │  If proposer received promises from Phase 1 with values,        │  │  │
│  │  │  it MUST propose the value with highest proposal number!        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PAXOS EXAMPLE: SUCCESSFUL CONSENSUS                                        │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  3 Acceptors (A, B, C), Proposer wants to commit value "X"            │  │
│  │                                                                       │  │
│  │   Proposer            A              B              C                 │  │
│  │      │                │              │              │                 │  │
│  │      │─ Prepare(1) ──►│              │              │                 │  │
│  │      │─ Prepare(1) ───┼─────────────►│              │                 │  │
│  │      │─ Prepare(1) ───┼──────────────┼─────────────►│                 │  │
│  │      │                │              │              │                 │  │
│  │      │◄─ Promise(1) ──│              │              │                 │  │
│  │      │◄─ Promise(1) ──┼──────────────│              │                 │  │
│  │      │◄─ Promise(1) ──┼──────────────┼──────────────│                 │  │
│  │      │                │              │              │                 │  │
│  │      │  Got majority (3/3), proceed to Phase 2                        │  │
│  │      │                │              │              │                 │  │
│  │      │─ Accept(1,X) ─►│              │              │                 │  │
│  │      │─ Accept(1,X) ──┼─────────────►│              │                 │  │
│  │      │─ Accept(1,X) ──┼──────────────┼─────────────►│                 │  │
│  │      │                │              │              │                 │  │
│  │      │◄─ Accepted ────│              │              │                 │  │
│  │      │◄─ Accepted ────┼──────────────│              │                 │  │
│  │      │◄─ Accepted ────┼──────────────┼──────────────│                 │  │
│  │      │                │              │              │                 │  │
│  │      │  Consensus reached: value "X" is decided                       │  │
│  │      ▼                ▼              ▼              ▼                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HANDLING COMPETING PROPOSERS                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Two proposers (P1, P2) compete:                                      │  │
│  │                                                                       │  │
│  │   P1            P2           A              B              C          │  │
│  │    │             │           │              │              │          │  │
│  │    │─ Prepare(1)────────────►│              │              │          │  │
│  │    │             │           │              │              │          │  │
│  │    │             │─ Prepare(2)─────────────►│              │          │  │
│  │    │             │           │              │              │          │  │
│  │    │◄─ Promise(1)────────────│              │              │          │  │
│  │    │             │◄─ Promise(2)─────────────│              │          │  │
│  │    │             │           │              │              │          │  │
│  │    │─ Accept(1,X)───────────►│              │              │          │  │
│  │    │             │           │              │              │          │  │
│  │    │◄─ REJECTED! ────────────│  A already promised to P2 (n=2)        │  │
│  │    │             │           │              │              │          │  │
│  │    │             │─ Accept(2,Y)────────────►│              │          │  │
│  │    │             │           │              │              │          │  │
│  │    │             │◄─ Accepted ──────────────│              │          │  │
│  │    │             │           │              │              │          │  │
│  │    │  P1 must retry with higher proposal number (n=3)                 │  │
│  │    │                                                                  │  │
│  │                                                                       │  │
│  │  The KEY insight: In Phase 1, if acceptors return previously          │  │
│  │  accepted values, proposer MUST use that value, not its own.          │  │
│  │  This ensures we don't "un-decide" an already decided value.          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PAXOS SAFETY GUARANTEE                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  If a value V is chosen (accepted by majority), then any        │  │  │
│  │  │  higher-numbered proposal that is chosen will also have value V │  │  │
│  │  │                                                                 │  │  │
│  │  │  Proof sketch:                                                  │  │  │
│  │  │  1. V accepted by majority S1                                   │  │  │
│  │  │  2. Any future majority S2 overlaps with S1                     │  │  │
│  │  │  3. At least one node in S2 has accepted V                      │  │  │
│  │  │  4. Phase 1 will return V to new proposer                       │  │  │
│  │  │  5. Proposer must propose V (highest accepted value)            │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Paxos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                MULTI-PAXOS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Basic Paxos is inefficient: 2 RTTs per decision.                           │
│  Multi-Paxos optimizes for the common case.                                 │
│                                                                             │
│  THE KEY OPTIMIZATION: STABLE LEADER                                        │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  BASIC PAXOS (per decision):                                    │  │  │
│  │  │                                                                 │  │  │
│  │  │    Prepare ──► Promise ──► Accept ──► Accepted                  │  │  │
│  │  │    └────── 1 RTT ──────┘   └────── 1 RTT ──────┘                │  │  │
│  │  │    Total: 2 round trips per value                               │  │  │
│  │  │                                                                 │  │  │
│  │  │  ─────────────────────────────────────────────────────────────  │  │  │
│  │  │                                                                 │  │  │
│  │  │  MULTI-PAXOS (with stable leader):                              │  │  │
│  │  │                                                                 │  │  │
│  │  │    Once: Prepare ──► Promise (leader established)               │  │  │
│  │  │                                                                 │  │  │
│  │  │    Then: Accept ──► Accepted   (repeated for each value)        │  │  │
│  │  │          └────── 1 RTT ──────┘                                  │  │  │
│  │  │    Total: 1 round trip per value (amortized)                    │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LOG REPLICATION WITH MULTI-PAXOS                                           │
│  ════════════════════════════════                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each log slot is an independent Paxos instance                       │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Log Index:    1      2      3      4      5      6             │  │  │
│  │  │              ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐          │  │  │
│  │  │  Leader:     │ A  │ │ B  │ │ C  │ │ D  │ │ E  │ │ ?  │          │  │  │
│  │  │              └────┘ └────┘ └────┘ └────┘ └────┘ └────┘          │  │  │
│  │  │              decided decided decided decided deciding           │  │  │
│  │  │                                                                 │  │  │
│  │  │  Each slot runs its own Paxos:                                  │  │  │
│  │  │  • Slot 1: Paxos instance 1 → decided "A"                       │  │  │
│  │  │  • Slot 2: Paxos instance 2 → decided "B"                       │  │  │
│  │  │  • ...                                                          │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HANDLING GAPS AND RECOVERY                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Gaps can occur when leader fails mid-replication:              │  │  │
│  │  │                                                                 │  │  │
│  │  │  Log Index:    1      2      3      4      5                    │  │  │
│  │  │              ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                 │  │  │
│  │  │  Node 1:     │ A  │ │ B  │ │    │ │ D  │ │ E  │   ← gap at 3   │  │  │
│  │  │              └────┘ └────┘ └────┘ └────┘ └────┘                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  New leader must:                                               │  │  │
│  │  │  1. Run Phase 1 for all incomplete slots                        │  │  │
│  │  │  2. Learn what (if anything) was previously proposed            │  │  │
│  │  │  3. Re-propose and fill gaps (or commit no-ops)                 │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PAXOS COMPLEXITY                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  "There are only two hard problems in distributed systems:            │  │
│  │   2. Exactly-once delivery                                            │  │
│  │   1. Guaranteed order of messages                                     │  │
│  │   2. Exactly-once delivery"                                           │  │
│  │                                                                       │  │
│  │  ─────────────────────────────────────────────────────────────────    │  │
│  │                                                                       │  │
│  │  Paxos challenges:                                                    │  │
│  │  • Original paper is notoriously difficult to understand              │  │
│  │  • Many implementation details left unspecified                       │  │
│  │  • Leader election not clearly defined                                │  │
│  │  • Cluster membership changes complex                                 │  │
│  │  • Liveness depends on single proposer (dueling proposers = livelock) │  │
│  │                                                                       │  │
│  │  This led to the development of Raft...                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Raft

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                     RAFT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "In Search of an Understandable Consensus Algorithm" (Ongaro & Ousterhout) │
│                                                                             │
│  KEY DESIGN PRINCIPLE: UNDERSTANDABILITY                                    │
│  ═══════════════════════════════════════                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Raft decomposes consensus into three sub-problems:                   │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. LEADER ELECTION                                             │  │  │
│  │  │     Select one server as leader                                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  2. LOG REPLICATION                                             │  │  │
│  │  │     Leader replicates log entries to followers                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  3. SAFETY                                                      │  │  │
│  │  │     Ensure logs stay consistent across crashes                  │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SERVER STATES AND TERMS                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  SERVER STATES:                                                 │  │  │
│  │  │                                                                 │  │  │
│  │  │        ┌──────────┐    election     ┌───────────┐               │  │  │
│  │  │        │ FOLLOWER │───timeout──────►│ CANDIDATE │               │  │  │
│  │  │        └──────────┘                 └───────────┘               │  │  │
│  │  │              ▲                           │  │                   │  │  │
│  │  │              │                     wins  │  │ discovers         │  │  │
│  │  │         discovers               election │  │ current           │  │  │
│  │  │         current leader                   │  │ leader            │  │  │
│  │  │              │          ┌───────────┐    │  │                   │  │  │
│  │  │              └──────────│  LEADER   │◄───┘  │                   │  │  │
│  │  │                         └───────────┘       │                   │  │  │
│  │  │                              │              │                   │  │  │
│  │  │                              └──────────────┘                   │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  TERMS: Logical clock for the cluster                          │  │  │
│  │  │                                                                 │  │  │
│  │  │   Term 1        Term 2        Term 3        Term 4              │  │  │
│  │  │  ┌────────────┬─────────────┬─────────────┬─────────────►       │  │  │
│  │  │  │ Election   │  Election   │  Normal     │  Election           │  │  │
│  │  │  │ + Normal   │  (no winner)│  operation  │  + Normal           │  │  │
│  │  │  │ operation  │             │             │  operation          │  │  │
│  │  │  └────────────┴─────────────┴─────────────┴─────────────►       │  │  │
│  │  │                                                                 │  │  │
│  │  │  • Each term has at most one leader                             │  │  │
│  │  │  • Terms act as logical clocks                                  │  │  │
│  │  │  • Higher term = more recent information                        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LEADER ELECTION                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. Follower times out (no heartbeat from leader)               │  │  │
│  │  │  2. Becomes candidate, increments term                          │  │  │
│  │  │  3. Votes for self, sends RequestVote to all others             │  │  │
│  │  │  4. Wins if receives majority of votes                          │  │  │
│  │  │  5. Becomes leader, starts sending heartbeats                   │  │  │
│  │  │                                                                 │  │  │
│  │  │  ─────────────────────────────────────────────────────────────  │  │  │
│  │  │                                                                 │  │  │
│  │  │  VOTE GRANTING RULES:                                           │  │  │
│  │  │                                                                 │  │  │
│  │  │  • Grant vote if:                                               │  │  │
│  │  │    - Haven't voted for anyone else in this term                 │  │  │
│  │  │    - Candidate's log is "at least as up-to-date"                │  │  │
│  │  │                                                                 │  │  │
│  │  │  "At least as up-to-date" means:                                │  │  │
│  │  │    - Higher term in last entry, OR                              │  │  │
│  │  │    - Same term but longer log                                   │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Election example:                                              │  │  │
│  │  │                                                                 │  │  │
│  │  │    S1 (candidate)      S2         S3         S4         S5      │  │  │
│  │  │         │               │          │          │          │      │  │  │
│  │  │    term=5, last        │          │          │          │      │  │  │
│  │  │    entry term=4        │          │          │          │      │  │  │
│  │  │         │               │          │          │          │      │  │  │
│  │  │         │─RequestVote──►│          │          │          │      │  │  │
│  │  │         │─RequestVote───┼─────────►│          │          │      │  │  │
│  │  │         │─RequestVote───┼──────────┼─────────►│          │      │  │  │
│  │  │         │─RequestVote───┼──────────┼──────────┼─────────►│      │  │  │
│  │  │         │               │          │          │          │      │  │  │
│  │  │         │◄──yes─────────│          │          │          │      │  │  │
│  │  │         │◄──yes─────────┼──────────│          │          │      │  │  │
│  │  │         │◄──yes─────────┼──────────┼──────────│          │      │  │  │
│  │  │         │               │          │          │          │      │  │  │
│  │  │    Got 4 votes (including self), becomes leader                 │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  LOG REPLICATION                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  LOG STRUCTURE:                                                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  Index:  1      2      3      4      5      6      7            │  │  │
│  │  │        ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐         │  │  │
│  │  │  Log:  │t=1 │ │t=1 │ │t=1 │ │t=2 │ │t=3 │ │t=3 │ │t=3 │         │  │  │
│  │  │        │x←3 │ │y←1 │ │y←9 │ │x←2 │ │x←0 │ │y←7 │ │x←5 │         │  │  │
│  │  │        └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘         │  │  │
│  │  │                                         ▲                       │  │  │
│  │  │                                   commitIndex                   │  │  │
│  │  │                                                                 │  │  │
│  │  │  Each entry has: (term, command)                                │  │  │
│  │  │  commitIndex: highest entry known to be replicated              │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  APPENDENTRIES RPC:                                             │  │  │
│  │  │                                                                 │  │  │
│  │  │  Leader sends to each follower:                                 │  │  │
│  │  │  • term: leader's term                                          │  │  │
│  │  │  • prevLogIndex: index of entry before new ones                 │  │  │
│  │  │  • prevLogTerm: term of prevLogIndex entry                      │  │  │
│  │  │  • entries[]: new entries to replicate                          │  │  │
│  │  │  • leaderCommit: leader's commitIndex                           │  │  │
│  │  │                                                                 │  │  │
│  │  │  ─────────────────────────────────────────────────────────────  │  │  │
│  │  │                                                                 │  │  │
│  │  │  Follower consistency check:                                    │  │  │
│  │  │  • Reject if log doesn't contain entry at prevLogIndex          │  │  │
│  │  │    with prevLogTerm                                             │  │  │
│  │  │  • This ensures log matching property                           │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  RAFT SAFETY PROPERTIES                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. ELECTION SAFETY                                             │  │  │
│  │  │     At most one leader per term                                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  2. LEADER APPEND-ONLY                                          │  │  │
│  │  │     Leader never overwrites or deletes entries                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  3. LOG MATCHING                                                │  │  │
│  │  │     If two logs have entry with same index and term,            │  │  │
│  │  │     they are identical through that index                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  4. LEADER COMPLETENESS                                         │  │  │
│  │  │     If entry is committed in term T, it's in log                │  │  │
│  │  │     of all leaders in terms > T                                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  5. STATE MACHINE SAFETY                                        │  │  │
│  │  │     If a server applies entry at index i,                       │  │  │
│  │  │     no other server applies a different entry at i              │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CLUSTER MEMBERSHIP CHANGES                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  JOINT CONSENSUS (original Raft):                               │  │  │
│  │  │                                                                 │  │  │
│  │  │  Transition through intermediate configuration:                 │  │  │
│  │  │                                                                 │  │  │
│  │  │  C_old ───► C_old,new ───► C_new                                │  │  │
│  │  │                                                                 │  │  │
│  │  │  During joint consensus:                                        │  │  │
│  │  │  • Log entries replicated to both configurations                │  │  │
│  │  │  • Decisions need majority from BOTH old AND new                │  │  │
│  │  │  • Prevents split-brain during transition                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  ─────────────────────────────────────────────────────────────  │  │  │
│  │  │                                                                 │  │  │
│  │  │  SINGLE-SERVER CHANGES (simpler):                               │  │  │
│  │  │                                                                 │  │  │
│  │  │  Add or remove one server at a time                             │  │  │
│  │  │  • Simpler to implement                                         │  │  │
│  │  │  • Used by etcd and other implementations                       │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ZAB (Zookeeper Atomic Broadcast)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ZAB - ZOOKEEPER ATOMIC BROADCAST                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ZAB is the consensus protocol used by Apache ZooKeeper                     │
│                                                                             │
│  KEY PROPERTIES                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  1. RELIABLE DELIVERY                                           │  │  │
│  │  │     If message m is delivered to one server,                    │  │  │
│  │  │     it will eventually be delivered to all servers              │  │  │
│  │  │                                                                 │  │  │
│  │  │  2. TOTAL ORDER                                                 │  │  │
│  │  │     If m1 is delivered before m2 to one server,                 │  │  │
│  │  │     m1 is delivered before m2 on all servers                    │  │  │
│  │  │                                                                 │  │  │
│  │  │  3. CAUSAL ORDER                                                │  │  │
│  │  │     If m1 causally precedes m2, m1 delivered before m2          │  │  │
│  │  │                                                                 │  │  │
│  │  │  4. PREFIX PROPERTY                                             │  │  │
│  │  │     If m is delivered, any message m' from same leader          │  │  │
│  │  │     proposed before m is also delivered                         │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ZAB PHASES                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  ZAB operates in cycles of phases:                              │  │  │
│  │  │                                                                 │  │  │
│  │  │     ┌────────────┐    ┌────────────┐    ┌────────────┐          │  │  │
│  │  │     │   PHASE 0  │───►│   PHASE 1  │───►│   PHASE 2  │─┐        │  │  │
│  │  │     │  Discovery │    │   Sync     │    │  Broadcast │ │        │  │  │
│  │  │     └────────────┘    └────────────┘    └────────────┘ │        │  │  │
│  │  │            ▲                                           │        │  │  │
│  │  │            └───────────── on failure ──────────────────┘        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  PHASE 0 - DISCOVERY (Leader Election)                                │  │
│  │  ─────────────────────────────────────                                │  │
│  │  • Followers connect to prospective leader                            │  │
│  │  • Leader collects acceptedEpoch from quorum                          │  │
│  │  • Leader proposes new epoch = max(acceptedEpoch) + 1                 │  │
│  │  • Followers acknowledge new epoch                                    │  │
│  │                                                                       │  │
│  │  PHASE 1 - SYNCHRONIZATION                                            │  │
│  │  ─────────────────────────                                            │  │
│  │  • Leader collects transaction history from quorum                    │  │
│  │  • Picks follower with most complete history                          │  │
│  │  • Sends missing transactions to followers                            │  │
│  │  • Followers catch up to leader's state                               │  │
│  │                                                                       │  │
│  │  PHASE 2 - BROADCAST (Normal Operation)                               │  │
│  │  ──────────────────────────────────────                               │  │
│  │  • Leader receives client requests                                    │  │
│  │  • Proposes transactions to followers                                 │  │
│  │  • Commits after quorum acknowledgment                                │  │
│  │  • 2-phase commit within each transaction                             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ZAB BROADCAST PROTOCOL                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │   Leader            Follower 1        Follower 2                      │  │
│  │      │                   │                │                           │  │
│  │      │───PROPOSE(zxid)──►│                │                           │  │
│  │      │───PROPOSE(zxid)───┼───────────────►│                           │  │
│  │      │                   │                │                           │  │
│  │      │◄────ACK───────────│                │                           │  │
│  │      │◄────ACK───────────┼────────────────│                           │  │
│  │      │                   │                │                           │  │
│  │      │     Got quorum, commit                                         │  │
│  │      │                   │                │                           │  │
│  │      │───COMMIT(zxid)───►│                │                           │  │
│  │      │───COMMIT(zxid)────┼───────────────►│                           │  │
│  │      │                   │                │                           │  │
│  │      ▼                   ▼                ▼                           │  │
│  │                                                                       │  │
│  │  zxid = (epoch, counter)                                              │  │
│  │  • epoch: leader's term                                               │  │
│  │  • counter: transaction number within epoch                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Viewstamped Replication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VIEWSTAMPED REPLICATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Developed by Oki & Liskov (1988), precursor to many modern algorithms      │
│                                                                             │
│  KEY CONCEPTS                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  VIEW: Configuration with designated primary                    │  │  │
│  │  │                                                                 │  │  │
│  │  │   View 1            View 2            View 3                    │  │  │
│  │  │  ┌────────────┐    ┌────────────┐    ┌────────────┐             │  │  │
│  │  │  │ Primary: A │───►│ Primary: B │───►│ Primary: C │             │  │  │
│  │  │  │ Backups:   │    │ Backups:   │    │ Backups:   │             │  │  │
│  │  │  │  B, C, D   │    │  A, C, D   │    │  A, B, D   │             │  │  │
│  │  │  └────────────┘    └────────────┘    └────────────┘             │  │  │
│  │  │                                                                 │  │  │
│  │  │  View change occurs when primary fails                          │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  NORMAL OPERATION                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Client         Primary            Backups                      │  │  │
│  │  │     │               │                  │                        │  │  │
│  │  │     │──REQUEST────►│                  │                        │  │  │
│  │  │     │               │──PREPARE───────►│                        │  │  │
│  │  │     │               │◄──PREPAREOK─────│                        │  │  │
│  │  │     │               │                  │                        │  │  │
│  │  │     │               │   (got quorum)   │                        │  │  │
│  │  │     │               │──COMMIT────────►│                        │  │  │
│  │  │     │◄──REPLY──────│                  │                        │  │  │
│  │  │     │               │                  │                        │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  VIEW CHANGE PROTOCOL                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Replicas suspect primary has failed                               │  │
│  │  2. New primary candidate starts view change                          │  │
│  │  3. Collects state from quorum of replicas                            │  │
│  │  4. Merges state, fills in any gaps                                   │  │
│  │  5. Broadcasts new view to all replicas                               │  │
│  │  6. Resumes normal operation in new view                              │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Similar to Raft leader election + log repair                   │  │  │
│  │  │                                                                 │  │  │
│  │  │  Key difference: VR predates Raft by decades                    │  │  │
│  │  │  and influenced its design                                      │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Comparison and Practical Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  COMPARISON AND PRACTICAL CONSIDERATIONS                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ALGORITHM COMPARISON                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Algorithm     │ Leader  │ RTTs    │ Understandable │ Used By   │  │  │
│  │  │  ══════════════════════════════════════════════════════════════ │  │  │
│  │  │  Basic Paxos   │ No      │ 2       │ Hard           │ Academic  │  │  │
│  │  │  Multi-Paxos   │ Yes     │ 1       │ Medium         │ Chubby    │  │  │
│  │  │  Raft          │ Yes     │ 1       │ Easy           │ etcd      │  │  │
│  │  │  ZAB           │ Yes     │ 1       │ Medium         │ ZooKeeper │  │  │
│  │  │  VR            │ Yes     │ 1       │ Medium         │ Research  │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REAL-WORLD IMPLEMENTATIONS                                                 │
│  ══════════════════════════                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  etcd (Raft)                                                    │  │  │
│  │  │  ─────────────                                                  │  │  │
│  │  │  • Key-value store for Kubernetes                               │  │  │
│  │  │  • Implements Raft for consensus                                │  │  │
│  │  │  • Linearizable reads and writes                                │  │  │
│  │  │  • Used by: Kubernetes, CoreDNS, Rook                           │  │  │
│  │  │                                                                 │  │  │
│  │  │  ZooKeeper (ZAB)                                                │  │  │
│  │  │  ───────────────                                                │  │  │
│  │  │  • Coordination service for distributed applications            │  │  │
│  │  │  • Hierarchical key-value store                                 │  │  │
│  │  │  • Used by: Kafka, HBase, Hadoop, Solr                          │  │  │
│  │  │                                                                 │  │  │
│  │  │  Consul (Raft)                                                  │  │  │
│  │  │  ─────────────                                                  │  │  │
│  │  │  • Service discovery and configuration                          │  │  │
│  │  │  • Health checking built-in                                     │  │  │
│  │  │  • Multi-datacenter support                                     │  │  │
│  │  │                                                                 │  │  │
│  │  │  CockroachDB (Raft)                                             │  │  │
│  │  │  ──────────────────                                             │  │  │
│  │  │  • Distributed SQL database                                     │  │  │
│  │  │  • Uses Raft for each range (partition)                         │  │  │
│  │  │  • Thousands of Raft groups per cluster                         │  │  │
│  │  │                                                                 │  │  │
│  │  │  TiKV (Raft)                                                    │  │  │
│  │  │  ───────────                                                    │  │  │
│  │  │  • Distributed transactional key-value store                    │  │  │
│  │  │  • Part of TiDB distributed database                            │  │  │
│  │  │  • Multi-Raft: one group per region                             │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CHOOSING THE RIGHT ALGORITHM                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Consider Raft when:                                            │  │  │
│  │  │  • Understandability is important                               │  │  │
│  │  │  • Strong tooling/library support needed                        │  │  │
│  │  │  • Starting a new project                                       │  │  │
│  │  │                                                                 │  │  │
│  │  │  Consider ZAB/ZooKeeper when:                                   │  │  │
│  │  │  • Already using ZooKeeper ecosystem                            │  │  │
│  │  │  • Need hierarchical data model                                 │  │  │
│  │  │  • Require watches/notifications                                │  │  │
│  │  │                                                                 │  │  │
│  │  │  Consider Multi-Paxos when:                                     │  │  │
│  │  │  • Building highly specialized systems                          │  │  │
│  │  │  • Need flexibility in protocol variants                        │  │  │
│  │  │  • Have deep distributed systems expertise                      │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  PRACTICAL ADVICE                                               │  │  │
│  │  │                                                                 │  │  │
│  │  │  1. Use existing implementations when possible                  │  │  │
│  │  │     • etcd, ZooKeeper, Consul are battle-tested                 │  │  │
│  │  │     • Implementing consensus correctly is very hard             │  │  │
│  │  │                                                                 │  │  │
│  │  │  2. Understand the failure modes                                │  │  │
│  │  │     • Network partitions can cause availability issues          │  │  │
│  │  │     • Slow disks can cause leader thrashing                     │  │  │
│  │  │                                                                 │  │  │
│  │  │  3. Monitor your consensus cluster                              │  │  │
│  │  │     • Leader election frequency                                 │  │  │
│  │  │     • Commit latency                                            │  │  │
│  │  │     • Proposal rate                                             │  │  │
│  │  │                                                                 │  │  │
│  │  │  4. Plan for operations                                         │  │  │
│  │  │     • Rolling upgrades                                          │  │  │
│  │  │     • Adding/removing nodes                                     │  │  │
│  │  │     • Backup and restore                                        │  │  │
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
│                                    SUMMARY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KEY TAKEAWAYS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. CONSENSUS IS FUNDAMENTAL                                          │  │
│  │     • Enables replicated state machines                               │  │
│  │     • Foundation for fault-tolerant distributed systems               │  │
│  │     • Requires majority (quorum) for progress                         │  │
│  │                                                                       │  │
│  │  2. FLP IMPOSSIBILITY                                                 │  │
│  │     • No deterministic algorithm solves consensus in async system     │  │
│  │     • Practical algorithms use timeouts and randomization             │  │
│  │     • Trade-off between safety and liveness                           │  │
│  │                                                                       │  │
│  │  3. PAXOS                                                             │  │
│  │     • Classic consensus algorithm                                     │  │
│  │     • Two phases: Prepare and Accept                                  │  │
│  │     • Difficult to understand and implement                           │  │
│  │     • Multi-Paxos adds stable leader for efficiency                   │  │
│  │                                                                       │  │
│  │  4. RAFT                                                              │  │
│  │     • Designed for understandability                                  │  │
│  │     • Strong leader model                                             │  │
│  │     • Clear separation of concerns                                    │  │
│  │     • Most popular choice for new systems                             │  │
│  │                                                                       │  │
│  │  5. ZAB (ZooKeeper Atomic Broadcast)                                  │  │
│  │     • Designed for ZooKeeper's needs                                  │  │
│  │     • Three phases: Discovery, Sync, Broadcast                        │  │
│  │     • Optimized for primary-backup replication                        │  │
│  │                                                                       │  │
│  │  6. PRACTICAL CONSIDERATIONS                                          │  │
│  │     • Use battle-tested implementations                               │  │
│  │     • Understand failure modes                                        │  │
│  │     • Monitor and plan for operations                                 │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CONSENSUS ALGORITHM DECISION FLOW                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │              ┌─────────────────────────────┐                          │  │
│  │              │ Need distributed consensus? │                          │  │
│  │              └──────────────┬──────────────┘                          │  │
│  │                             │                                         │  │
│  │                             ▼                                         │  │
│  │              ┌─────────────────────────────┐                          │  │
│  │              │ Can use existing service?   │─── Yes ──▶ Use etcd/     │  │
│  │              │ (etcd, ZooKeeper, Consul)   │           ZK/Consul      │  │
│  │              └──────────────┬──────────────┘                          │  │
│  │                             │ No                                      │  │
│  │                             ▼                                         │  │
│  │              ┌─────────────────────────────┐                          │  │
│  │              │ Can use embedded library?   │─── Yes ──▶ Use Raft      │  │
│  │              │ (hashicorp/raft, etcd/raft) │           library        │  │
│  │              └──────────────┬──────────────┘                          │  │
│  │                             │ No                                      │  │
│  │                             ▼                                         │  │
│  │              ┌─────────────────────────────┐                          │  │
│  │              │ Implement Raft from spec    │                          │  │
│  │              │ (last resort, very hard!)   │                          │  │
│  │              └─────────────────────────────┘                          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Navigation

| Previous | Up | Next |
|----------|-----|------|
| [Chapter 12: Distributed Transactions](12-distributed-transactions.md) | [Index](README.md) | - |

---

*This documentation is based on "Database Internals" by Alex Petrov and covers consensus algorithms used in distributed database systems.*
