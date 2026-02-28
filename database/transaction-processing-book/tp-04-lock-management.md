# Lock Management

## Overview

Lock management is the cornerstone of pessimistic concurrency control. Jim Gray's seminal 1976 paper "Granularity of Locks and Degrees of Consistency" established the hierarchical locking framework still used in modern databases.

---

## Lock Types

### Basic Lock Modes

| Lock Mode | Symbol | Description | Conflicts With |
|-----------|--------|-------------|----------------|
| Shared | S | Read lock | X |
| Exclusive | X | Write lock | S, X |

### Lock Compatibility Matrix

```
Requesting:     S      X
Holding:  ┌─────────────────┐
     S    │  Compatible   No │
     X    │     No       No │
          └─────────────────┘
```

### Extended Lock Modes

For hierarchical locking, additional intention locks are needed:

| Lock Mode | Symbol | Description | Usage |
|-----------|--------|-------------|-------|
| Intention Shared | IS | Intent to acquire S at finer granularity | Read intent |
| Intention Exclusive | IX | Intent to acquire X at finer granularity | Write intent |
| Shared + Intention Exclusive | SIX | Read entire, write some | Scan with updates |

### Full Compatibility Matrix

```
         IS    IX    S    SIX    X
    ┌───────────────────────────────┐
 IS │  Y     Y     Y     Y     N   │
 IX │  Y     Y     N     N     N   │
 S  │  Y     N     Y     N     N   │
SIX │  Y     N     N     N     N   │
 X  │  N     N     N     N     N   │
    └───────────────────────────────┘
Y = Compatible, N = Conflict
```

---

## Lock Granularity

### Granularity Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                         DATABASE                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                     TABLESPACE                       │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │                    TABLE                     │    │    │
│  │  │  ┌───────────────────────────────────────┐  │    │    │
│  │  │  │                  PAGE                  │  │    │    │
│  │  │  │  ┌─────────────────────────────────┐  │  │    │    │
│  │  │  │  │               ROW                │  │  │    │    │
│  │  │  │  └─────────────────────────────────┘  │  │    │    │
│  │  │  └───────────────────────────────────────┘  │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

Coarse ◄─────────────────────────────────────────────────► Fine
(Database)                                              (Row/Record)
```

### Granularity Trade-offs

| Granularity | Concurrency | Overhead | Use Case |
|-------------|-------------|----------|----------|
| Database | Very low | Very low | Batch maintenance |
| Table | Low | Low | Table scans |
| Page | Medium | Medium | Index traversals |
| Row | High | High | OLTP operations |

### Intention Lock Protocol

To lock a node, you must:
1. Lock the root in appropriate intention mode
2. Lock all ancestors in appropriate intention mode
3. Lock the target node

```
Example: X lock on row R in table T

                    DATABASE
                       │
                      IS (intention for table)
                       │
                       ▼
                     TABLE T
                       │
                      IX (intention for row)
                       │
                       ▼
                     PAGE P
                       │
                      IX (intention for row)
                       │
                       ▼
                     ROW R
                       │
                       X (actual exclusive lock)
```

---

## Lock Escalation

### What is Lock Escalation?

When too many fine-grained locks are held, automatically convert to coarser lock.

```
Lock Count Threshold
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  Row locks (1000+)  →  Escalate to Table lock           │
│                                                         │
│  Before:                    After:                      │
│  ┌─────────────────┐       ┌─────────────────┐         │
│  │ Table T         │       │ Table T         │         │

### Deadlock Detection

#### Wait-For Graph (WFG)

```
Build graph: Ti → Tj means Ti waits for lock held by Tj
Periodically check for cycles
If cycle found: Select victim and abort

Algorithm:
1. Build WFG from lock table
2. Perform DFS/BFS for cycle detection
3. If cycle:
   - Select victim (youngest, least work, etc.)
   - Abort victim transaction
   - Release victim's locks
   - Retry victim later
```

#### Deadlock Detection Frequency

| Approach | When to Check | Trade-off |
|----------|--------------|-----------|
| Continuous | Every lock request | High overhead |
| Periodic | Timer-based (e.g., 1 sec) | Delayed detection |
| On timeout | When transaction waits too long | May not find quickly |

### Deadlock Prevention

Avoid deadlocks by restricting lock acquisition:

#### Wait-Die Scheme (Non-preemptive)

```
IF TS(Ti) < TS(Tj):    // Ti is older
    Ti waits for Tj
ELSE:                   // Ti is younger
    Ti aborts (dies)

Older transactions never wait for younger → No cycle possible
```

#### Wound-Wait Scheme (Preemptive)

```
IF TS(Ti) < TS(Tj):    // Ti is older
    Tj is aborted (wounded)
    Ti gets the lock
ELSE:                   // Ti is younger
    Ti waits for Tj

Younger transactions never preempt older → No cycle possible
```

### Deadlock Prevention Comparison

| Scheme | Who Aborts | Properties |
|--------|-----------|------------|
| Wait-Die | Younger if it would wait for older | Non-preemptive |
| Wound-Wait | Younger when older needs its lock | Preemptive |
| Conservative 2PL | None (prevents by pre-declaring) | Most restrictive |

---

## Lock Table Implementation

### Hash-Based Lock Table

```
┌─────────────────────────────────────────────────────────────┐
│                      LOCK TABLE                              │
├─────────────────────────────────────────────────────────────┤
│ Hash Index │                                                │
│ ┌────────┐ │  ┌──────────────────────────────────────────┐ │
│ │   0    │───►│ Data Item: X                             │ │
│ ├────────┤ │  │ Lock Mode: X (Exclusive)                 │ │
│ │   1    │ │  │ Holder: T1                               │ │
│ ├────────┤ │  │ Wait Queue: [T2, T3]                     │ │
│ │   2    │───►│ ┌──────────────────────────────────────┐ │ │
│ ├────────┤ │  │ │ Data Item: Y                         │ │ │
│ │  ...   │ │  │ │ Lock Mode: S (Shared)                │ │ │
│ ├────────┤ │  │ │ Holders: [T4, T5, T6]                │ │ │
│ │   n    │ │  │ │ Wait Queue: [T7(X)]                  │ │ │
│ └────────┘ │  │ └──────────────────────────────────────┘ │ │
│            │  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Lock Table Entry Structure

```c
struct LockEntry {
    DataItemID  item_id;        // What is locked
    LockMode    granted_mode;   // Current lock mode granted
    int         holder_count;   // Number of holders (for S locks)
    TxnList     holders;        // List of holding transactions
    WaitQueue   waiters;        // Queue of waiting transactions
    LockEntry*  next;           // Next entry in hash chain
};

struct WaitEntry {
    TxnID       txn_id;         // Waiting transaction
    LockMode    requested_mode; // Desired lock mode
    WaitEntry*  next;           // Next in wait queue
};
```

---

## Lock Manager Operations

### Lock Request Algorithm

```
LOCK(txn_id, data_item, mode):
    entry = find_or_create_lock_entry(data_item)

    IF entry.granted_mode is compatible with mode:
        IF wait_queue is empty:
            grant lock to txn_id
            RETURN SUCCESS

    // Must wait
    add txn_id to wait_queue
    block txn_id
    RETURN BLOCKED

UNLOCK(txn_id, data_item):
    entry = find_lock_entry(data_item)
    remove txn_id from holders

    IF holders is empty:
        // Try to grant to waiters
        WHILE wait_queue not empty:
            next_waiter = dequeue from wait_queue
            IF next_waiter.mode compatible with current grants:
                grant lock to next_waiter
                wake up next_waiter
            ELSE:
                break  // FIFO ordering

    IF no holders and no waiters:
        delete entry
```

---

## Degrees of Consistency (Gray's Levels)

### Degree 0 (Chaos)
- No read locks required
- Write locks held only during write operation
- No guarantees

### Degree 1 (Read Uncommitted)
- Write locks held until commit
- No read locks
- Prevents lost updates
- Allows dirty reads

### Degree 2 (Read Committed)
- Write locks held until commit
- Read locks held only during read
- Prevents dirty reads
- Allows non-repeatable reads

### Degree 3 (Serializable)
- Write locks held until commit
- Read locks held until commit
- Full isolation

```
Degree Comparison:

              │ Lost  │ Dirty │ Non-Repeatable │ Phantom │
              │Update │ Read  │     Read       │  Read   │
──────────────┼───────┼───────┼────────────────┼─────────┤
Degree 0      │  Yes  │  Yes  │      Yes       │   Yes   │
Degree 1      │  No   │  Yes  │      Yes       │   Yes   │
Degree 2      │  No   │  No   │      Yes       │   Yes   │
Degree 3      │  No   │  No   │      No        │   No    │
```

---

## Locking Special Structures

### Index Locking

```
B+Tree Index Locking (simplified):

Top-Down Traversal:
1. Lock root in S or IX mode
2. Lock child node
3. Release parent lock (if safe)
4. Continue to leaf

Safe Node: Can release parent lock if child has room for
           splits/merges without affecting ancestors
```

### Predicate Locking (Phantom Prevention)

```
SELECT * FROM employees WHERE salary > 50000

Must lock the PREDICATE (salary > 50000), not just existing rows

Implementations:
1. Table lock (too coarse)
2. Index range lock (practical)
3. Gap locks (between index entries)
4. Next-key locking (entry + gap before)
```

---

## Key Takeaways

1. **Intention locks** enable efficient hierarchical locking
2. **Granularity** choice is a trade-off between concurrency and overhead
3. **Lock escalation** balances memory usage and concurrency
4. **Deadlock** must be detected and resolved (victim selection)
5. **Degrees of consistency** map to SQL isolation levels
6. **Special structures** (indexes, predicates) need careful locking

---

## References

- Gray, J. et al. (1976). "Granularity of Locks and Degrees of Consistency in a Shared Data Base"
- Gray, J. & Reuter, A. (1993). Chapters 10-11: "Lock-Based Concurrency Control"
- Mohan, C. (1990). "ARIES/KVL: A Key-Value Locking Method for Concurrency Control"

│  │  └─Row1 (X)     │       │  (X)            │         │
│  │  └─Row2 (X)     │  →    │                 │         │
│  │  └─Row3 (X)     │       │                 │         │
│  │  └─...          │       │                 │         │
│  │  └─Row1000 (X)  │       │                 │         │
│  └─────────────────┘       └─────────────────┘         │
│                                                         │
│  Lock table entries: 1000  Lock table entries: 1       │
└─────────────────────────────────────────────────────────┘
```

### Escalation Trade-offs

| Aspect | Fine-Grained | Escalated |
|--------|--------------|-----------|
| Concurrency | High | Low (blocks entire table) |
| Memory | High (many lock entries) | Low (one entry) |
| CPU | High (many checks) | Low |

---

## Deadlock Handling

### What is Deadlock?

A circular wait condition where transactions wait for each other indefinitely.

```
DEADLOCK EXAMPLE:

T1: Holds X(A), Waits for X(B)
T2: Holds X(B), Waits for X(A)

Wait-For Graph:
     ┌───────────┐
     │     T1    │───── waits for B ─────►│
     │           │◄─── waits for A ───────│
     └───────────┘                         │
            ▲                              │
            │                              ▼
            │                        ┌───────────┐
            └────────────────────────│     T2    │
                                     └───────────┘

Cycle detected = DEADLOCK!
```

