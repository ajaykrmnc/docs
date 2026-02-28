# ACID Properties - The Foundation of Reliable Transactions

## Overview

The ACID properties, formalized by Jim Gray and Andreas Reuter, define the fundamental guarantees that a transaction processing system must provide. These properties ensure that database transactions are processed reliably and consistently.

**ACID** stands for:
- **A**tomicity
- **C**onsistency
- **I**solation
- **D**urability

---

## 1. Atomicity

### Definition

> A transaction is an atomic unit of work - either all operations complete successfully, or none do.

Atomicity guarantees the "all-or-nothing" property. If any part of a transaction fails, the entire transaction is rolled back.

### The Atomicity Sphere

```
┌─────────────────────────────────────┐
│         Transaction T1               │
│  ┌──────────────────────────────┐   │
│  │ BEGIN TRANSACTION            │   │
│  │ UPDATE accounts SET bal=     │   │
│  │   bal - 100 WHERE id = 1     │   │
│  │ UPDATE accounts SET bal=     │   │
│  │   bal + 100 WHERE id = 2     │   │
│  │ COMMIT                       │   │
│  └──────────────────────────────┘   │
│                                     │
│   All operations succeed together   │
│        OR none take effect          │
└─────────────────────────────────────┘
```

### Implementation Mechanisms

1. **Write-Ahead Logging (WAL)**
   - Log all changes BEFORE applying to database
   - Log contains both old and new values (UNDO/REDO information)
   - On failure, use log to undo partial changes

2. **Shadow Paging**
   - Maintain two copies of data pages
   - Write to shadow page, switch pointer on commit
   - Original page remains until commit succeeds

### Atomicity Example

```sql
-- Bank transfer: $100 from Account A to Account B
BEGIN TRANSACTION;

UPDATE accounts
SET balance = balance - 100
WHERE account_id = 'A';

-- System crashes here WITHOUT atomicity = $100 lost!
-- WITH atomicity = entire transaction rolled back

UPDATE accounts
SET balance = balance + 100
WHERE account_id = 'B';

COMMIT;
```

### Two Phases of Atomicity

| Phase | Description | Actions |
|-------|-------------|---------|
| **Execute Phase** | Transaction runs | Operations are performed, changes logged |
| **Commit/Abort Phase** | Final decision | Either commit all changes or abort and undo |

---

## 2. Consistency

### Definition

> A transaction takes the database from one consistent state to another consistent state.

Consistency ensures that all data integrity constraints are satisfied before and after the transaction.

### Types of Consistency Constraints

1. **Domain Constraints**
   - Data type restrictions
   - Value ranges (e.g., age > 0)

2. **Entity Integrity**
   - Primary keys must be unique
   - No NULL primary keys

3. **Referential Integrity**
   - Foreign keys must reference existing primary keys
   - Cascading updates/deletes

4. **Application-Level Constraints**
   - Business rules (e.g., account balance ≥ 0)
   - Semantic constraints

### Consistency in Action

```
State S1 (Consistent)           State S2 (Consistent)
┌──────────────────┐           ┌──────────────────┐
│ Account A: $500  │           │ Account A: $400  │
│ Account B: $300  │  ─T1→     │ Account B: $400  │
│ Total:     $800  │           │ Total:     $800  │
└──────────────────┘           └──────────────────┘

Invariant: Total balance remains constant
```

### Consistency vs Integrity

| Aspect | Consistency | Integrity |
|--------|-------------|-----------|
| Scope | Transaction level | Data level |
| Timing | Before and after transaction | Always |

### Isolation Levels (SQL Standard)

Jim Gray's work significantly influenced the SQL isolation levels:

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|-------|------------|---------------------|--------------|
| READ UNCOMMITTED | Possible | Possible | Possible |
| READ COMMITTED | Prevented | Possible | Possible |
| REPEATABLE READ | Prevented | Prevented | Possible |
| SERIALIZABLE | Prevented | Prevented | Prevented |

### Isolation Anomalies Explained

#### Dirty Read
```
T1: WRITE(X = 100)
T2: READ(X) → 100      ← Reads uncommitted data
T1: ABORT              ← T1 rolls back
T2: Uses X = 100       ← T2 has incorrect data!
```

#### Non-Repeatable Read
```
T1: READ(X) → 50
T2: WRITE(X = 100); COMMIT
T1: READ(X) → 100      ← Different value on second read!
```

#### Phantom Read
```
T1: SELECT * WHERE age > 20  → Returns {A, B}
T2: INSERT C (age=25); COMMIT
T1: SELECT * WHERE age > 20  → Returns {A, B, C}  ← New row appeared!
```

### Serializability

The gold standard for isolation - a schedule is serializable if its effect is equivalent to some serial execution.

```
Serializable Schedule Example:
T1: R(A) W(A)          T2: R(A) W(A)

Serial Order 1: T1 → T2
Serial Order 2: T2 → T1

Schedule S is serializable if S ≡ T1→T2 OR S ≡ T2→T1
```

---

## 4. Durability

### Definition

> Once a transaction commits, its effects persist even if the system fails.

Durability ensures that committed data survives:
- System crashes
- Power failures
- Hardware failures

### Durability Implementation

```
┌───────────────────────────────────────────────────┐
│                    Durability                      │
├───────────────────────────────────────────────────┤
│                                                   │
│  1. Write-Ahead Logging (WAL)                     │
│     ┌─────────────┐                               │
│     │ Transaction │                               │
│     │   Changes   │                               │
│     └──────┬──────┘                               │
│            │                                      │
│            ▼                                      │
│     ┌─────────────┐    ┌─────────────┐           │
│     │    Log      │───→│   Disk      │           │
│     │   Buffer    │    │   Log       │           │
│     └─────────────┘    └─────────────┘           │
│            │                                      │
│            │ (Commit)                             │
│            ▼                                      │
│     ┌─────────────┐    ┌─────────────┐           │
│     │   Buffer    │───→│   Disk      │           │
│     │   Pool      │    │   Database  │           │
│     └─────────────┘    └─────────────┘           │
│                                                   │
└───────────────────────────────────────────────────┘
```

### The FORCE vs NO-FORCE Dilemma

| Policy | Description | Durability | Performance |
|--------|-------------|------------|-------------|
| FORCE | Write all changes to disk at commit | ✓ Guaranteed | Slow |
| NO-FORCE | Allow dirty pages in buffer | Requires WAL | Fast |

### Recovery Guarantees

```
System Crash Timeline:
────────────────────────────────────────────────────
     T1 commits     T2 commits    CRASH
         │              │            │
─────────┴──────────────┴────────────┴──────────────
         ↓              ↓
     Durability    Durability
     guarantees    guarantees
     T1 effects    T2 effects
     persist       persist
```

---

## ACID Interactions

### How ACID Properties Work Together

```
                    ┌─────────────┐
                    │ Transaction │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │Atomicity │     │Consistency│     │ Isolation│
   │ (Undo)   │     │(Invariants)│    │ (Locking)│
   └────┬─────┘     └─────┬────┘     └────┬─────┘
        │                 │               │
        └─────────────────┼───────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Durability  │
                   │    (WAL)     │
                   └──────────────┘
```

### Implementation Summary

| Property | Primary Mechanism | Secondary Mechanism |
|----------|-------------------|---------------------|
| Atomicity | Undo logging | Shadow pages |
| Consistency | Constraint checking | Triggers |
| Isolation | Locking/MVCC | Timestamp ordering |
| Durability | Write-ahead logging | Replication |

---

## Trade-offs and Relaxations

### CAP Theorem Connection

In distributed systems, you can only have 2 of 3:
- **C**onsistency
- **A**vailability
- **P**artition tolerance

This leads to relaxed ACID (BASE):
- **B**asically **A**vailable
- **S**oft state
- **E**ventual consistency

### When to Relax ACID

| Scenario | Relaxation | Benefit |
|----------|------------|---------|
| High read throughput | Lower isolation | Better concurrency |
| Geo-distributed | Eventual consistency | Lower latency |
| Analytics workloads | Snapshot isolation | No blocking |

---

## Key Takeaways

1. **Atomicity** = All or nothing (Undo logging)
2. **Consistency** = Maintain invariants (Constraints)
3. **Isolation** = Hide intermediate states (Locking/MVCC)
4. **Durability** = Survive crashes (WAL + Force at commit)

The ACID properties together ensure that transactions are reliable units of work that maintain database integrity regardless of failures or concurrent access.

---

## Further Reading

- Chapter 4: "Transaction Models" in Gray & Reuter
- Chapter 7-8: "Recovery" concepts
- Chapter 9-12: Isolation and concurrency control

| Responsibility | DBMS + Application | DBMS enforced |

---

## 3. Isolation

### Definition

> Concurrent transactions execute as if they were running sequentially (serially).

Isolation ensures that the intermediate states of a transaction are not visible to other concurrent transactions.

### The Isolation Problem

```
Without Isolation (Problem):
Time    T1                      T2
────────────────────────────────────────
t1      READ(X) → 100
t2                              READ(X) → 100
t3      X = X + 10
t4                              X = X + 20
t5      WRITE(X) → 110
t6                              WRITE(X) → 120
────────────────────────────────────────
Result: X = 120 (Lost T1's update!)

With Isolation (Correct):
Time    T1                      T2
────────────────────────────────────────
t1      READ(X) → 100
t2      X = X + 10
t3      WRITE(X) → 110
t4      COMMIT
t5                              READ(X) → 110
t6                              X = X + 20
t7                              WRITE(X) → 130
t8                              COMMIT
────────────────────────────────────────
Result: X = 130 (Both updates preserved!)
```

