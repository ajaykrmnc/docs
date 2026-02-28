# Concurrency Control

## Overview

Concurrency control is the mechanism that ensures correct results when multiple transactions execute simultaneously. Jim Gray's work established the theoretical foundations and practical techniques used in all modern database systems.

---

## The Concurrency Problem

### Why Concurrency Control?

Without concurrency control, interleaved transaction execution can lead to:
- Lost updates
- Dirty reads
- Non-repeatable reads
- Phantom reads

### Serial vs Concurrent Execution

```
SERIAL EXECUTION (Correct but slow):
T1: ████████████████
                    T2: ████████████████
                                        T3: ████████████████

CONCURRENT EXECUTION (Fast but needs control):
T1: ████████████████
T2:     ████████████████
T3:         ████████████████
```

---

## Schedules and Serializability

### Schedule Definition

A schedule S is an ordering of operations from a set of transactions that preserves the order of operations within each transaction.

### Notation

```
r[x] = read item x
w[x] = write item x
c   = commit
a   = abort
```

### Example Schedules

```
Schedule S1 (Serial: T1 then T2):
T1: r[x] w[x] c
T2:             r[x] w[x] c

Schedule S2 (Interleaved):
T1: r[x]     w[x]     c
T2:      r[x]     w[x]     c
```

### Conflict Operations

Two operations conflict if:
1. They belong to different transactions
2. They access the same data item
3. At least one is a write

```
CONFLICT MATRIX:
              T2
           Read   Write
    Read    No     Yes
T1  Write   Yes    Yes
```

### Conflict Serializability

A schedule is conflict serializable if it can be transformed into a serial schedule by swapping non-conflicting adjacent operations.

```
Conflict Serializable Schedule:
     T1          T2
1.   r[x]
2.               r[y]
3.   w[x]
4.               w[y]
5.   c
6.               c

Non-conflicting: r1[x] and r2[y], w1[x] and w2[y]
Equivalent to: T1 → T2 (serial)
```

### Precedence Graph (Serialization Graph)

Used to test for conflict serializability:

```
For each conflict between Ti and Tj where Ti's operation comes first:
    Add edge Ti → Tj

Schedule is conflict serializable ⟺ Precedence graph is acyclic
```

**Example:**
```
Schedule: r1[x] r2[x] w1[x] w2[x]

Conflicts:
- r1[x] → w2[x]: T1 → T2
- r2[x] → w1[x]: T2 → T1
- w1[x] → w2[x]: T1 → T2

Precedence Graph:
T1 ←→ T2  (cycle exists!)

Result: NOT conflict serializable
```

---

## Concurrency Control Techniques

### Overview of Approaches

```
┌─────────────────────────────────────────────────────────────┐
│              Concurrency Control Techniques                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │

### 2PL Variants

| Variant | Description | Cascading Aborts | Deadlock |
|---------|-------------|------------------|----------|
| Basic 2PL | Release after lock point | Possible | Possible |
| Strict 2PL | Hold write locks until commit | Prevented | Possible |
| Rigorous 2PL | Hold ALL locks until commit | Prevented | Possible |
| Conservative 2PL | Acquire all locks before start | Prevented | Prevented |

### Strict 2PL Example

```
T1: lock-X(A) r(A) w(A) lock-X(B) r(B) w(B) commit unlock(A) unlock(B)
                                                    ↑
                                          All unlocks at commit

Benefits:
- No cascading aborts (committed data always read)
- Simplifies recovery
```

---

## 2. Timestamp-Based Concurrency Control

### Basic Timestamp Ordering (BTO)

Each transaction gets a timestamp (TS) at start. Operations ordered by timestamp.

**Data Item Timestamps:**
- `W-TS(X)`: Timestamp of transaction that last wrote X
- `R-TS(X)`: Timestamp of transaction that last read X

### BTO Rules

```
READ(X) by transaction T:
    IF TS(T) < W-TS(X):
        ABORT T (trying to read old value)
    ELSE:
        Execute read
        R-TS(X) = max(R-TS(X), TS(T))

WRITE(X) by transaction T:
    IF TS(T) < R-TS(X):
        ABORT T (trying to overwrite value already read)
    ELSE IF TS(T) < W-TS(X):
        Thomas Write Rule: Skip write (older write ignored)
    ELSE:
        Execute write
        W-TS(X) = TS(T)
```

### Thomas Write Rule

An optimization that allows some out-of-order writes:

```
Without Thomas Write Rule:
T1(TS=10): w[x]           ← T1 writes x
T2(TS=20):      w[x]      ← T2 writes x (newer)
T1 later commits...       ← Would overwrite T2's newer value!

With Thomas Write Rule:
T1(TS=10): w[x]           ← T1 wants to write, but TS(T1) < W-TS(x)=20
                          ← Skip T1's write (outdated anyway)
Result: x has T2's value (correct!)
```

---

## 3. Optimistic Concurrency Control (OCC)

### Philosophy

Assume conflicts are rare. Execute without restrictions, validate before commit.

### Three Phases

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    READ     │ ──► │  VALIDATION │ ──► │    WRITE    │
│   PHASE     │     │    PHASE    │     │   PHASE     │
└─────────────┘     └─────────────┘     └─────────────┘

Read Phase:
- Read from database
- Write to private workspace

Validation Phase:
- Check for conflicts with concurrent transactions
- If conflict: ABORT
- If no conflict: proceed

Write Phase:
- Copy changes to database
- Commit
```

### Validation Rules

For transaction T validating against committed transaction Ti:

```
Rule 1: Ti completes before T starts
        Ti: |-------|
        T:           |-------|
        Always valid

Rule 2: Ti completes before T's write phase
        Ti: |-------|
        T:      |-------|
        Valid if: WriteSet(Ti) ∩ ReadSet(T) = ∅

Rule 3: Ti completes write phase before T enters validation
        Ti: |-------|
        T:    |-------|
        Valid if: WriteSet(Ti) ∩ ReadSet(T) = ∅
              AND WriteSet(Ti) ∩ WriteSet(T) = ∅
```

### OCC Example

```
T1 starts at t=0, reads A and B
T2 starts at t=1, reads A, writes A
T2 validates at t=2: No conflicts, commits
T1 validates at t=3:
    - T2 committed during T1's execution
    - T2 wrote A, T1 read A
    - WriteSet(T2) ∩ ReadSet(T1) = {A} ≠ ∅
    - ABORT T1
```

---

## 4. Multi-Version Concurrency Control (MVCC)

### Core Idea

Maintain multiple versions of each data item. Readers access appropriate version without blocking writers.

### Version Structure

```
Data Item X:
┌─────────────────────────────────────────────────┐
│ Version Chain                                    │
│                                                 │
│ X_v1 ────► X_v2 ────► X_v3 ────► X_v4 (latest) │
│ (TS=5)    (TS=10)    (TS=15)    (TS=20)        │
│                                                 │
│ Each version has:                               │
│ - Value                                         │
│ - Write timestamp (when created)                │
│ - Read timestamp (most recent read)             │
└─────────────────────────────────────────────────┘
```

### MVCC Read Rule

```
READ(X) by transaction T with TS(T) = 25:
    Find version Xi where:
        W-TS(Xi) ≤ TS(T) < W-TS(Xi+1)

    For X with versions at TS = 5, 10, 15, 20:
        T(TS=25) reads X_v4 (TS=20)
        T(TS=12) reads X_v2 (TS=10)
        T(TS=8)  reads X_v1 (TS=5)
```

### Snapshot Isolation (SI)

A popular MVCC implementation:

```
Transaction sees snapshot of database at start time

T1 starts at t=100:
    - Sees all committed values as of t=100
    - Doesn't see T2's changes (started at t=105)

Write-Write Conflict:
    - First committer wins
    - Second transaction aborts
```

### SI Anomaly: Write Skew

```
Constraint: x + y ≥ 0

Initial: x = 50, y = 50

T1: READ x → 50
    READ y → 50
    WRITE x = x - 100 = -50

T2: READ x → 50
    READ y → 50
    WRITE y = y - 100 = -50

Both commit (no write-write conflict)
Final: x = -50, y = -50
x + y = -100 (Constraint violated!)
```

---

## Comparison of Techniques

| Aspect | 2PL | Timestamp | OCC | MVCC |
|--------|-----|-----------|-----|------|
| Blocking | Yes | No | No | Readers: No |
| Aborts | Deadlock | Conflict | Validation | Write-Write |
| Overhead | Lock management | Timestamp tracking | Validation | Version storage |
| Best for | High contention | Moderate load | Low contention | Read-heavy |

---

## Concurrency Control in Practice

### PostgreSQL
- MVCC with Snapshot Isolation
- Optional Serializable SI (SSI)

### MySQL InnoDB
- MVCC + 2PL hybrid
- Configurable isolation levels

### Oracle
- MVCC-based
- Read consistency via undo segments

### SQL Server
- 2PL by default
- Optional MVCC (Snapshot Isolation)

---

## Key Takeaways

1. **Serializability** is the gold standard for correctness
2. **Two-Phase Locking** guarantees serializability but can cause deadlocks
3. **Timestamp Ordering** provides serialization without locks but may abort more
4. **Optimistic Control** works well with low contention
5. **MVCC** allows readers and writers to not block each other
6. **No single technique is best** - choose based on workload characteristics

---

## References

- Gray, J. & Reuter, A. (1993). Chapters 9-13: "Concurrency Control"
- Bernstein, P. & Goodman, N. (1981). "Concurrency Control in Distributed Database Systems"
- Kung, H.T. & Robinson, J.T. (1981). "On Optimistic Methods for Concurrency Control"

│  │   Pessimistic  │  │   Optimistic  │  │  Multi-Version │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘   │
│          │                  │                  │            │
│    ┌─────┴─────┐      ┌────┴────┐        ┌───┴────┐       │
│    │           │      │         │        │        │       │
│    ▼           ▼      ▼         ▼        ▼        ▼       │
│  Locking   Timestamp  Validation       MVCC   Snapshot    │
│  (2PL)     Ordering   Phase            SI     Isolation   │
│                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Lock-Based Concurrency Control

### Two-Phase Locking (2PL)

The fundamental theorem of concurrency control:

> **Theorem:** If all transactions follow two-phase locking, the resulting schedule is conflict serializable.

### 2PL Rules

```
GROWING PHASE                    SHRINKING PHASE
┌─────────────────┐             ┌─────────────────┐
│ Acquire locks   │             │ Release locks   │
│ No releases     │──Lock Point→│ No acquisitions │
└─────────────────┘             └─────────────────┘

Transaction:
   Locks held
        ^
        │     ****
        │   **    **
        │  *        *
        │ *          *
        │*            *
        └──────────────────► Time
        Growing    Shrinking
         Phase       Phase
```

