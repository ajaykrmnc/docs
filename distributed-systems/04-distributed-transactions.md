# Distributed Transactions: 2PC, 3PC, and Saga Patterns

## Table of Contents
1. [Introduction to Distributed Transactions](#introduction-to-distributed-transactions)
2. [ACID in Distributed Systems](#acid-in-distributed-systems)
3. [Two-Phase Commit (2PC)](#two-phase-commit-2pc)
4. [Three-Phase Commit (3PC)](#three-phase-commit-3pc)
5. [Saga Pattern](#saga-pattern)
6. [Other Patterns](#other-patterns)
7. [Comparison and Trade-offs](#comparison-and-trade-offs)
8. [Interview Questions](#interview-questions)

---

## Introduction to Distributed Transactions

### What is a Distributed Transaction?

A **distributed transaction** is a transaction that spans multiple nodes, databases, or services. It must ensure that either ALL operations succeed or ALL operations fail, maintaining data consistency across the entire system.

```
┌─────────────────────────────────────────────────────────────────┐
│           DISTRIBUTED TRANSACTION EXAMPLE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Transfer $100 from Account A to Account B:                    │
│                                                                 │
│  ┌───────────────┐                    ┌───────────────┐        │
│  │   Bank A DB   │                    │   Bank B DB   │        │
│  │               │                    │               │        │
│  │  Account A:   │      $100          │  Account B:   │        │
│  │  Balance: 500 │ ──────────────────►│  Balance: 200 │        │
│  │  - 100 = 400  │                    │  + 100 = 300  │        │
│  │               │                    │               │        │
│  └───────────────┘                    └───────────────┘        │
│                                                                 │
│  BOTH must succeed OR BOTH must fail!                          │
│                                                                 │
│  What if:                                                      │
│  • Bank A deducts but Bank B fails? → Money lost!             │
│  • Bank B credits but Bank A fails? → Money duplicated!       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Challenges in Distributed Transactions

| Challenge | Description |
|-----------|-------------|
| **Partial Failures** | Some nodes succeed, others fail |
| **Network Partitions** | Communication between nodes interrupted |
| **Timeouts** | Uncertain if operation succeeded or failed |
| **Node Crashes** | Node fails mid-transaction |
| **Ordering** | Ensuring consistent order across nodes |
| **Coordination Overhead** | Performance impact of synchronization |

### Transaction Models

```
┌─────────────────────────────────────────────────────────────────┐
│              TRANSACTION MODEL SPECTRUM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STRICT CONSISTENCY ◄─────────────────────► EVENTUAL CONSISTENCY│
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     2PC      │  │     3PC      │  │    SAGA      │         │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤         │
│  │ Strong ACID  │  │ Non-blocking │  │ Eventual     │         │
│  │ Blocking     │  │ More messages│  │ Non-blocking │         │
│  │ Coordinator  │  │ Coordinator  │  │ Compensation │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  Performance: Slower ◄───────────────────────────► Faster      │
│  Consistency: Stronger ◄─────────────────────────► Weaker      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ACID in Distributed Systems

### ACID Properties Revisited

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACID PROPERTIES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  A - ATOMICITY                                                 │
│  ─────────────                                                 │
│  All operations complete or none do.                           │
│  "All or nothing"                                              │
│                                                                 │
│  C - CONSISTENCY                                               │
│  ───────────────                                               │
│  Database moves from one valid state to another.               │
│  Constraints always satisfied.                                 │
│                                                                 │
│  I - ISOLATION                                                 │
│  ────────────                                                  │
│  Concurrent transactions don't interfere.                      │
│  As if executed serially.                                      │
│                                                                 │
│  D - DURABILITY                                                │
│  ────────────                                                  │
│  Committed data survives failures.                             │
│  Written to persistent storage.                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ACID Challenges in Distributed Systems

| Property | Single-Node | Distributed Challenge |
|----------|------------|----------------------|
| **Atomicity** | Undo log, rollback | Coordinating rollback across nodes |
| **Consistency** | Local constraints | Global constraints across nodes |
| **Isolation** | Local locks | Distributed locking, deadlocks |
| **Durability** | WAL to disk | Replication before commit |

---

## Two-Phase Commit (2PC)

### Overview

**2PC** is a protocol that ensures all participants in a distributed transaction either commit or abort together. It uses a **coordinator** to manage the process.

```
┌─────────────────────────────────────────────────────────────────┐
│              TWO-PHASE COMMIT (2PC)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: PREPARE (Voting Phase)                               │
│  ───────────────────────────────                               │
│                                                                 │
│     Coordinator          Participants                          │
│         │                                                       │
│         │   PREPARE       ┌──────────┐                         │
│         │────────────────►│Participant│                        │
│         │────────────────►│    A     │                         │
│         │                 └──────────┘                         │
│         │   PREPARE       ┌──────────┐                         │
│         │────────────────►│Participant│                        │
│         │                 │    B     │                         │
│         │                 └──────────┘                         │
│         │                                                       │


### 2PC State Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              2PC STATE TRANSITIONS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  COORDINATOR:                                                  │
│                                                                 │
│  ┌───────┐  send PREPARE   ┌─────────┐  all YES   ┌─────────┐ │
│  │INITIAL│─────────────────►│ WAITING │────────────►│COMMITTED│ │
│  └───────┘                 └────┬────┘            └─────────┘ │
│                                 │                              │
│                                 │ any NO or timeout            │
│                                 ▼                              │
│                            ┌─────────┐                        │
│                            │ ABORTED │                        │
│                            └─────────┘                        │
│                                                                 │
│  PARTICIPANT:                                                  │
│                                                                 │
│  ┌───────┐  recv PREPARE   ┌─────────┐  recv COMMIT ┌────────┐│
│  │INITIAL│─────────────────►│ READY   │─────────────►│COMMITTED││
│  └───────┘                 └────┬────┘              └────────┘│
│                                 │                              │
│                                 │ recv ABORT                   │
│                                 ▼                              │
│                            ┌─────────┐                        │
│                            │ ABORTED │                        │
│                            └─────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2PC Message Flow (Success Case)

```
┌─────────────────────────────────────────────────────────────────┐
│              2PC SUCCESS FLOW                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Coordinator     Participant A      Participant B              │
│      │                │                   │                    │
│      │──PREPARE──────►│                   │                    │
│      │──PREPARE───────────────────────────►                    │
│      │                │                   │                    │
│      │                │ (write to log)    │ (write to log)     │
│      │                │                   │                    │
│      │◄──YES─────────│                   │                    │
│      │◄──YES─────────────────────────────│                    │
│      │                │                   │                    │
│      │ (write COMMIT to log)             │                    │
│      │                │                   │                    │
│      │──COMMIT───────►│                   │                    │
│      │──COMMIT────────────────────────────►                    │
│      │                │                   │                    │
│      │◄──ACK─────────│                   │                    │
│      │◄──ACK─────────────────────────────│                    │
│      │                │                   │                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2PC Problems

```
┌─────────────────────────────────────────────────────────────────┐
│              2PC PROBLEMS                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. BLOCKING PROBLEM                                           │
│  ───────────────────                                           │
│                                                                 │
│  If coordinator crashes after sending PREPARE but before       │
│  sending COMMIT/ABORT, participants are stuck in READY state.  │
│                                                                 │
│  Participant A: "I voted YES, now what?"                       │
│  Participant B: "Same here... waiting..."                      │
│  Coordinator:   💀 (crashed)                                   │
│                                                                 │
│  Participants CANNOT:                                          │
│  • Commit (might violate atomicity if others abort)           │
│  • Abort (might violate atomicity if others commit)           │
│  • Continue (holding locks, blocking other transactions)      │
│                                                                 │
│  2. COORDINATOR SINGLE POINT OF FAILURE                        │
│  ──────────────────────────────────────                        │
│                                                                 │
│  All decisions go through coordinator.                         │
│  If coordinator fails, entire system blocked.                  │
│                                                                 │
│  3. NETWORK PARTITION ISSUES                                   │
│  ───────────────────────────                                   │
│                                                                 │
│  Participants might not receive COMMIT/ABORT message.          │
│  Need timeout + recovery mechanisms.                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2PC Recovery

```
┌─────────────────────────────────────────────────────────────────┐
│              2PC RECOVERY SCENARIOS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PARTICIPANT CRASH RECOVERY:                                   │
│                                                                 │
│  Check local log:                                              │
│  • No PREPARE → Abort (coordinator will timeout)              │
│  • PREPARE logged, no decision → Ask coordinator              │
│  • COMMIT logged → Redo commit                                 │
│  • ABORT logged → Redo abort                                   │
│                                                                 │
│  COORDINATOR CRASH RECOVERY:                                   │
│                                                                 │
│  Check local log:                                              │
│  • No PREPARE → Abort all                                      │
│  • PREPARE logged, no decision → Re-run protocol              │
│  • COMMIT logged → Re-send COMMIT to all                      │
│  • ABORT logged → Re-send ABORT to all                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Three-Phase Commit (3PC)

### Why 3PC?

3PC adds a **PRE-COMMIT** phase to reduce blocking. It ensures that if any participant is in the "ready to commit" state, all participants have agreed to commit.

```
┌─────────────────────────────────────────────────────────────────┐
│              THREE-PHASE COMMIT (3PC)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: CAN-COMMIT (Voting)                                  │
│  ────────────────────────────                                  │
│  Coordinator asks: "Can you commit?"                           │
│  Participants respond: YES/NO                                  │
│                                                                 │
│  Phase 2: PRE-COMMIT                                           │
│  ───────────────────                                           │
│  If all YES: Coordinator sends PRE-COMMIT                      │
│  Participants acknowledge, enter "prepared" state              │
│                                                                 │
│  Phase 3: DO-COMMIT                                            │
│  ──────────────────                                            │
│  Coordinator sends COMMIT                                      │
│  Participants commit and acknowledge                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3PC Message Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              3PC MESSAGE FLOW                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Coordinator    Participant A    Participant B                 │
│      │                │                │                        │
│      │──CAN-COMMIT───►│                │     Phase 1           │
│      │──CAN-COMMIT────────────────────►│                       │
│      │                │                │                        │
│      │◄──YES──────────│                │                       │
│      │◄──YES──────────────────────────│                        │
│      │                │                │                        │
│      │──PRE-COMMIT───►│                │     Phase 2           │
│      │──PRE-COMMIT────────────────────►│                       │
│      │                │                │                        │
│      │◄──ACK──────────│                │                       │
│      │◄──ACK──────────────────────────│                        │
│      │                │                │                        │
│      │──DO-COMMIT────►│                │     Phase 3           │
│      │──DO-COMMIT─────────────────────►│                       │
│      │                │                │                        │
│      │◄──COMMITTED────│                │                       │
│      │◄──COMMITTED────────────────────│                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3PC vs 2PC

| Aspect | 2PC | 3PC |
|--------|-----|-----|
| **Phases** | 2 (Prepare, Commit) | 3 (CanCommit, PreCommit, DoCommit) |
| **Blocking** | Yes (coordinator failure) | No (can timeout and decide) |
| **Messages** | 4n (n participants) | 6n (n participants) |
| **Network Partitions** | Blocks | Can cause inconsistency |
| **Complexity** | Simpler | More complex |
| **Usage** | Widely used | Rarely used in practice |

### 3PC Timeout Behavior

```
┌─────────────────────────────────────────────────────────────────┐
│              3PC TIMEOUT HANDLING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  State: WAITING (voted YES)                                    │
│  Timeout → ABORT (safe, no PRE-COMMIT received)               │
│                                                                 │
│  State: PRE-COMMITTED                                          │
│  Timeout → COMMIT (safe, everyone agreed in Phase 2)          │
│                                                                 │
│  Key insight:                                                  │
│  PRE-COMMIT means "everyone agreed, commit is inevitable"      │
│  So participants can safely commit on timeout                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Saga Pattern

### Overview

**Saga** is a pattern for managing distributed transactions using a sequence of local transactions with compensating actions for rollback.

```
┌─────────────────────────────────────────────────────────────────┐
│              SAGA PATTERN                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Instead of one big transaction:                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  T1 → T2 → T3 → T4  (all or nothing)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Break into local transactions + compensations:                │
│                                                                 │
│  ┌────┐    ┌────┐    ┌────┐    ┌────┐                        │
│  │ T1 │───►│ T2 │───►│ T3 │───►│ T4 │  SUCCESS              │
│  └────┘    └────┘    └────┘    └────┘                        │
│                                                                 │
│  If T3 fails:                                                  │
│  ┌────┐    ┌────┐    ┌────┐                                   │
│  │ T1 │───►│ T2 │───►│ T3 │ ✗                                │
│  └────┘    └────┘    └────┘                                   │
│    │         │                                                 │
│    ▼         ▼                                                 │
│  ┌────┐    ┌────┐                                             │
│  │ C1 │◄───│ C2 │  COMPENSATE                                 │
│  └────┘    └────┘                                             │
│                                                                 │
│  Ci = Compensation for Ti                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Saga Example: E-Commerce Order

```
┌─────────────────────────────────────────────────────────────────┐
│              SAGA EXAMPLE: ORDER PROCESSING                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FORWARD TRANSACTIONS:                                         │
│  ────────────────────                                          │
│                                                                 │
│  T1: Create Order        │  C1: Cancel Order                   │
│         │                │                                      │
│         ▼                │                                      │
│  T2: Reserve Inventory   │  C2: Release Inventory              │
│         │                │                                      │
│         ▼                │                                      │
│  T3: Charge Payment      │  C3: Refund Payment                 │
│         │                │                                      │
│         ▼                │                                      │
│  T4: Ship Order          │  C4: Cancel Shipment                │
│                                                                 │
│  If T3 (Payment) fails:                                        │
│  Execute: C2 → C1 (reverse order)                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Saga Coordination: Choreography vs Orchestration

```
┌─────────────────────────────────────────────────────────────────┐
│         CHOREOGRAPHY vs ORCHESTRATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CHOREOGRAPHY (Event-Driven):                                  │
│  ─────────────────────────────                                 │
│                                                                 │
│  ┌────────┐ OrderCreated ┌──────────┐ InventoryReserved        │
│  │ Order  │──────────────►│Inventory │──────────────────►       │
│  │Service │              │ Service  │                          │
│  └────────┘              └──────────┘                          │
│                                                                 │
│                                          ┌─────────┐            │
│                                          │ Payment │            │
│                                          │ Service │            │
│                                          └─────────┘            │
│                                                                 │
│  • Services react to events                                    │
│  • No central controller                                       │
│  • Loosely coupled                                             │
│  • Hard to track overall flow                                  │
│                                                                 │
│  ORCHESTRATION (Central Controller):                           │
│  ────────────────────────────────────                          │
│                                                                 │
│                    ┌────────────┐                               │
│                    │ORCHESTRATOR│                               │
│                    └─────┬──────┘                               │
│           ┌──────────────┼──────────────┐                      │
│           ▼              ▼              ▼                      │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│     │  Order   │  │Inventory │  │ Payment  │                  │
│     │ Service  │  │ Service  │  │ Service  │                  │
│     └──────────┘  └──────────┘  └──────────┘                  │
│                                                                 │
│  • Central controller manages flow                             │
│  • Easier to understand and debug                              │
│  • Single point of failure                                     │
│  • Tighter coupling                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Saga Characteristics

| Aspect | Description |
|--------|-------------|
| **Isolation** | No isolation between steps (ACD, not ACID) |
| **Consistency** | Eventual consistency |
| **Compensation** | Must be idempotent |
| **Ordering** | Compensations run in reverse order |
| **Atomicity** | Achieved through compensations |

---

## Other Patterns

### TCC (Try-Confirm-Cancel)

```
┌─────────────────────────────────────────────────────────────────┐
│              TCC PATTERN                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRY PHASE:                                                    │
│  • Reserve resources                                           │
│  • No permanent changes yet                                    │
│  • Check business rules                                        │
│                                                                 │
│  CONFIRM PHASE:                                                │
│  • Make reservations permanent                                 │
│  • Idempotent operation                                        │
│                                                                 │
│  CANCEL PHASE:                                                 │
│  • Release reservations                                        │
│  • Rollback try phase                                          │
│                                                                 │
│  Example: Seat Reservation                                     │
│  ─────────────────────────                                     │
│  Try:     Reserve seat (mark as "pending")                    │
│  Confirm: Book seat (mark as "confirmed")                     │
│  Cancel:  Release seat (mark as "available")                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Outbox Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│              OUTBOX PATTERN                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Problem: How to update DB and send message atomically?        │
│                                                                 │
│  Solution: Write message to DB outbox table in same txn        │
│                                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │           LOCAL TRANSACTION             │                   │
│  │  ┌─────────────┐   ┌─────────────┐     │                   │
│  │  │ Update      │   │ Insert into │     │                   │
│  │  │ Business    │ + │ Outbox      │     │                   │
│  │  │ Table       │   │ Table       │     │                   │
│  │  └─────────────┘   └──────┬──────┘     │                   │
│  └───────────────────────────┼─────────────┘                   │
│                              │                                  │
│                              ▼                                  │
│                    ┌─────────────────┐                         │
│                    │ Message Relay   │  (reads outbox)         │
│                    │ Process         │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │ Message Broker  │                         │
│                    └─────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comparison and Trade-offs

### Pattern Comparison

| Pattern | Consistency | Isolation | Complexity | Performance |
|---------|------------|-----------|------------|-------------|
| **2PC** | Strong | Yes | Medium | Low |
| **3PC** | Strong | Yes | High | Lower |
| **Saga** | Eventual | No | Medium | High |
| **TCC** | Eventual | Partial | High | Medium |

### When to Use What

```
┌─────────────────────────────────────────────────────────────────┐
│              PATTERN SELECTION GUIDE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Need strong ACID across databases?                            │
│  └── YES → 2PC (if you can tolerate blocking)                 │
│                                                                 │
│  Long-running transaction (minutes/hours)?                     │
│  └── YES → Saga pattern                                       │
│                                                                 │
│  Microservices with different data stores?                     │
│  └── YES → Saga or TCC                                        │
│                                                                 │
│  Need to reserve resources before commit?                      │
│  └── YES → TCC pattern                                        │
│                                                                 │
│  Can design idempotent compensations?                          │
│  └── YES → Saga works well                                    │
│                                                                 │
│  High throughput critical?                                     │
│  └── YES → Avoid 2PC, prefer Saga                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: Explain the blocking problem in 2PC.**

In 2PC, after a participant votes YES (sends VOTE-YES) in the prepare phase, it enters a "prepared" state and holds locks. If the coordinator crashes before sending the commit/abort decision:
- Participant cannot commit (might violate atomicity if others abort)
- Participant cannot abort (might violate atomicity if others commit)
- Participant is blocked, holding locks indefinitely

**Q2: How does 3PC solve the blocking problem?**

3PC introduces a PRE-COMMIT phase that guarantees:
- If ANY participant received PRE-COMMIT, ALL participants voted YES
- Participants in PRE-COMMIT state can safely COMMIT on timeout
- Participants who only voted YES can safely ABORT on timeout

**Q3: What's the difference between Saga and 2PC?**

| Aspect | 2PC | Saga |
|--------|-----|------|
| Atomicity | True atomicity | Compensating transactions |
| Isolation | Full isolation (locks) | No isolation |
| Duration | Short (locks held) | Long-running OK |
| Consistency | Strong | Eventual |
| Failure handling | Rollback | Compensation |

**Q4: What are compensating transactions?**

Compensating transactions undo the effect of previously committed transactions. They must be:
- **Semantically opposite**: Undo the business effect
- **Idempotent**: Safe to execute multiple times
- **Commutative**: Order shouldn't matter for retries

Example:
- Transaction: Debit $100 from account
- Compensation: Credit $100 to account

### Design Questions

**Q5: Design a distributed transaction for hotel + flight booking.**

```
Using Saga Orchestration:

1. Create Booking (Orchestrator)
2. Reserve Flight (T1) → Cancel Flight (C1)
3. Reserve Hotel (T2) → Cancel Hotel (C2)
4. Charge Payment (T3) → Refund Payment (C3)
5. Confirm All Reservations

Failure at step 3:
- Execute C2 (cancel hotel)
- Execute C1 (cancel flight)
- Return failure to user
```

**Q6: How would you handle partial failures in a Saga?**

1. **Idempotent operations**: Each step can be safely retried
2. **Compensation tracking**: Log completed steps
3. **Retry with backoff**: For transient failures
4. **Dead letter queue**: For unrecoverable failures
5. **Manual intervention**: Last resort for complex failures

---

## Summary

### Key Takeaways

1. **2PC** provides strong consistency but blocks on coordinator failure
2. **3PC** reduces blocking but adds complexity and message overhead
3. **Saga** trades isolation for availability and scalability
4. **TCC** provides reservations before commitment
5. **Choose based on**: consistency needs, transaction duration, failure tolerance

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         DISTRIBUTED TRANSACTIONS CHEAT SHEET                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  2PC:                                                          │
│  • Prepare → Commit/Abort                                      │
│  • Strong ACID                                                 │
│  • Blocking on coordinator failure                             │
│                                                                 │
│  3PC:                                                          │
│  • CanCommit → PreCommit → DoCommit                           │
│  • Non-blocking (timeout-based decisions)                     │
│  • More messages, rarely used                                  │
│                                                                 │
│  Saga:                                                         │
│  • Local transactions + compensations                          │
│  • Eventual consistency                                        │
│  • Choreography or Orchestration                               │
│                                                                 │
│  TCC:                                                          │
│  • Try → Confirm/Cancel                                        │
│  • Resource reservation                                        │
│  • Good for inventory, bookings                                │
│                                                                 │
│  Decision:                                                     │
│  • Short + ACID needed → 2PC                                  │
│  • Long-running → Saga                                        │
│  • Reservation needed → TCC                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

