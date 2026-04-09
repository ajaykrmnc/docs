# Chapter 7: Transactions

## Table of Contents

1. [The Slippery Concept of a Transaction](#the-slippery-concept-of-a-transaction)
2. [ACID Guarantees](#acid-guarantees)
3. [Single-Object and Multi-Object Operations](#single-object-and-multi-object-operations)
4. [Weak Isolation Levels](#weak-isolation-levels)
5. [Serializability](#serializability)
6. [Interview Questions](#interview-questions)

---

## The Slippery Concept of a Transaction

A **transaction** groups several reads and writes into a logical unit. The entire transaction either **commits** (succeeds) or **aborts** (rolls back) — no partial results.

```
┌─────────────────────────────────────────────────────────────────┐
│              WHY TRANSACTIONS EXIST                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Without transactions, many things can go wrong:                │
│                                                                 │
│  • Database software/hardware fails mid-write                   │
│  • Application crashes mid-operation                            │
│  • Network interruption cuts off application from database      │
│  • Multiple clients write simultaneously → overwrite each other │
│  • Client reads partially-updated data                          │
│  • Race conditions between clients                              │
│                                                                 │
│  Transactions SIMPLIFY the programming model:                   │
│  Instead of handling every possible failure mode,               │
│  the database guarantees "all or nothing."                      │
│                                                                 │
│  Not every application needs transactions. But dismissing them  │
│  outright leads to subtle bugs that are hard to reproduce.      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ACID Guarantees

```
┌──────────────────────────────────────────────────────────────────┐
│              A C I D                                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A = ATOMICITY                                                   │
│      NOT about concurrency (that's Isolation).                   │
│      Means: If a transaction fails partway through,              │
│      ALL changes are rolled back. No partial writes.             │
│      "Abortability" would be a better name.                     │
│                                                                  │
│  C = CONSISTENCY                                                 │
│      Application-level concept, not a database guarantee.        │
│      Means: Data satisfies certain invariants                    │
│      (e.g., credits = debits in accounting).                    │
│      The APPLICATION is responsible for defining correct         │
│      transactions. The database just provides A, I, D.          │
│                                                                  │
│  I = ISOLATION                                                   │
│      Concurrently executing transactions don't interfere.        │
│      Ideally: each transaction runs as if it's the ONLY         │
│      one running (serializable isolation).                       │
│      In practice: databases offer WEAKER isolation levels       │
│      for performance reasons.                                   │
│                                                                  │
│  D = DURABILITY                                                  │
│      Once a transaction commits, its data is safe even if        │
│      the system crashes. Implemented via WAL, replication,       │
│      or writing to non-volatile storage.                         │
│                                                                  │
│  Note: "ACID" was coined by Theo Härder and Andreas Reuter      │
│  in 1983. It's a marketing term — the definitions are           │
│  imprecise and different databases implement them differently.  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### BASE — The NoSQL Alternative

```
┌──────────────────────────────────────────────────────────────────┐
│  BASE = Basically Available, Soft state, Eventually consistent  │
│                                                                  │
│  Even MORE vague than ACID. Essentially means:                  │
│  "We don't guarantee ACID, but we'll try our best."            │
│                                                                  │
│  Used as a marketing counter to ACID by NoSQL databases.        │
│  Not particularly useful as a precise term.                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Single-Object and Multi-Object Operations

```
┌──────────────────────────────────────────────────────────────────┐
│  SINGLE-OBJECT writes:                                          │
│  Almost every database provides atomicity for writes to a       │
│  single object (e.g., one row, one document, one key).          │
│  • Atomicity: WAL for crash recovery                            │
│  • Isolation: Lock on the object                                │
│  • Compare-and-set: Write only if value hasn't changed          │
│                                                                  │
│  These are NOT transactions in the usual sense.                 │
│                                                                  │
│  MULTI-OBJECT transactions:                                     │
│  Coordinate writes to MULTIPLE objects (rows, documents, keys). │
│  Needed when:                                                    │
│  • Foreign keys must be consistent across tables                │
│  • Document DB: denormalized data must be updated together      │
│  • Secondary indexes must match the primary data                │
│                                                                  │
│  Example (email app):                                            │
│  1. Insert new email into mailbox                                │
│  2. Update unread counter                                        │
│  Both must succeed or both must fail → need multi-object txn.  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Weak Isolation Levels

True serializability has a performance cost. Most databases use **weaker** isolation levels:

### Level 1: Read Committed

```
┌──────────────────────────────────────────────────────────────────┐
│              READ COMMITTED                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Two guarantees:                                                 │
│  1. No dirty reads: You only read data that has been COMMITTED  │
│  2. No dirty writes: You only overwrite data that has been      │
│     COMMITTED                                                    │
│                                                                  │
│  DIRTY READ (prevented):                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Tx1: SET x = 3        (not yet committed)               │    │
│  │ Tx2: READ x           → sees old value (2), not 3       │    │
│  │ Tx1: COMMIT                                              │    │
│  │ Tx2: READ x           → NOW sees 3                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  DIRTY WRITE (prevented):                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Alice: UPDATE listing SET buyer = 'Alice'                │    │
│  │ Bob:   UPDATE listing SET buyer = 'Bob'   (must wait    │    │
│  │        UPDATE invoice SET payer = 'Bob'    for Alice's   │    │
│  │                                            commit/abort) │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Implementation:                                                 │
│  • Dirty writes: Row-level locks (held until commit)            │
│  • Dirty reads: Database remembers both old and new values;     │
│    serves OLD value to other transactions until commit.          │
│    (Not locks — locks would kill read performance.)             │
│                                                                  │
│  Default level in: PostgreSQL, SQL Server, Oracle               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Level 2: Snapshot Isolation (Repeatable Read)

```
┌──────────────────────────────────────────────────────────────────┐
│              SNAPSHOT ISOLATION (MVCC)                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Problem with Read Committed — NON-REPEATABLE READ:             │
│                                                                  │
│  Alice has two accounts: Account 1 = $500, Account 2 = $500    │
│  She transfers $100 from Acct 1 to Acct 2:                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Transfer Tx:                Alice reads her accounts:     │   │
│  │                                                           │   │
│  │                             READ Acct 1 → $500            │   │
│  │ UPDATE Acct 1 SET bal=400                                 │   │
│  │ UPDATE Acct 2 SET bal=600                                 │   │
│  │ COMMIT                                                    │   │
│  │                             READ Acct 2 → $600            │   │
│  │                                                           │   │
│  │ Alice sees: $500 + $600 = $1100 ???                       │   │
│  │ Or if reads reversed: $400 + $500 = $900 ???              │   │
│  │ Either way, she sees an INCONSISTENT snapshot!            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  SNAPSHOT ISOLATION fixes this:                                  │
│  Each transaction reads from a CONSISTENT SNAPSHOT of the        │
│  database — the state at the time the transaction started.       │
│                                                                  │
│  Implementation: MVCC (Multi-Version Concurrency Control)       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Each row has multiple versions:                           │   │
│  │                                                           │   │
│  │ Row: Account 1                                            │   │
│  │ ┌──────────────────┬──────────────────┐                  │   │
│  │ │ created_by: tx5  │ created_by: tx13 │                  │   │
│  │ │ deleted_by: tx13 │ deleted_by: -    │                  │   │
│  │ │ balance: 500     │ balance: 400     │                  │   │
│  │ └──────────────────┴──────────────────┘                  │   │
│  │                                                           │   │
│  │ Tx12 (started before tx13) reads the old version (500)   │   │
│  │ Tx15 (started after tx13) reads the new version (400)    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  VISIBILITY RULES:                                               │
│  A transaction can see a row version if:                         │
│  • created_by a transaction that committed BEFORE this one      │
│  • NOT deleted_by a transaction that committed BEFORE this one  │
│                                                                  │
│  Used by: PostgreSQL, MySQL/InnoDB, Oracle, SQL Server           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Problem: Lost Updates

```
┌──────────────────────────────────────────────────────────────────┐
│              LOST UPDATE PROBLEM                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Two transactions read-modify-write the same value:             │
│                                                                  │
│  Counter = 42                                                    │
│  Tx1: READ counter → 42                                         │
│  Tx2: READ counter → 42                                         │
│  Tx1: WRITE counter = 42 + 1 = 43                               │
│  Tx2: WRITE counter = 42 + 1 = 43   ← Should be 44!           │
│                                                                  │
│  Tx2's increment is LOST.                                       │
│                                                                  │
│  SOLUTIONS:                                                      │
│  ──────────                                                      │
│  1. Atomic operations:                                           │
│     UPDATE counters SET value = value + 1 WHERE key = 'foo';    │
│     Database handles concurrency internally.                     │
│                                                                  │
│  2. Explicit locking (SELECT ... FOR UPDATE):                   │
│     SELECT * FROM accounts WHERE id = 1 FOR UPDATE;             │
│     -- Other transactions wait here                              │
│     UPDATE accounts SET balance = balance + 100;                 │
│                                                                  │
│  3. Compare-and-set:                                             │
│     UPDATE wiki SET content = 'new' WHERE id = 1                │
│       AND content = 'old';                                       │
│     Fails if content was modified concurrently.                  │
│                                                                  │
│  4. Automatic detection (PostgreSQL, Oracle, SQL Server):       │
│     Database detects lost updates and aborts one transaction.   │
│     MySQL/InnoDB does NOT detect this! Beware.                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Problem: Write Skew and Phantoms

```
┌──────────────────────────────────────────────────────────────────┐
│              WRITE SKEW                                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Example: Hospital requires at least 1 doctor on call.          │
│                                                                  │
│  Currently on call: Alice AND Bob (2 doctors)                   │
│                                                                  │
│  Alice's Tx:                    Bob's Tx:                        │
│  SELECT COUNT(*) FROM doctors   SELECT COUNT(*) FROM doctors     │
│    WHERE on_call = true;          WHERE on_call = true;          │
│  → 2 (OK, can leave)           → 2 (OK, can leave)              │
│  UPDATE doctors SET on_call     UPDATE doctors SET on_call       │
│    = false WHERE name='Alice';    = false WHERE name='Bob';      │
│  COMMIT                         COMMIT                           │
│                                                                  │
│  Result: ZERO doctors on call! Both checked, both left.         │
│  Neither violated the constraint individually.                   │
│                                                                  │
│  This is WRITE SKEW — a generalization of lost updates          │
│  involving DIFFERENT objects.                                    │
│                                                                  │
│  PHANTOM: The initial SELECT reads rows that match a condition. │
│  Another transaction INSERT/UPDATE/DELETE changes which rows    │
│  match → the original transaction's decision was based on       │
│  stale data. The new rows are "phantoms."                       │
│                                                                  │
│  More examples of write skew:                                    │
│  • Meeting room double-booking                                  │
│  • Multiplayer game: two players move to same position          │
│  • Claiming a unique username                                    │
│  • Double-spending in financial systems                          │
│                                                                  │
│  SOLUTIONS:                                                      │
│  • Serializable isolation (eliminates all anomalies)            │
│  • Materializing conflicts: create a lock table                 │
│    (e.g., rows for each time slot → SELECT FOR UPDATE)          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Serializability

The strongest isolation level: guarantees transactions execute as if they ran one at a time, serially.

### Approach 1: Actual Serial Execution

```
┌──────────────────────────────────────────────────────────────────┐
│              ACTUAL SERIAL EXECUTION                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Run transactions one at a time on a SINGLE THREAD.             │
│                                                                  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                           │
│  │ Tx 1 │→│ Tx 2 │→│ Tx 3 │→│ Tx 4 │→ ...                     │
│  └──────┘ └──────┘ └──────┘ └──────┘                           │
│                                                                  │
│  Became feasible because:                                        │
│  • RAM is cheap → entire dataset fits in memory                 │
│  • OLTP transactions are short and fast                          │
│                                                                  │
│  Requirements:                                                   │
│  • Transactions must be SHORT (no waiting for user input)       │
│  • Use STORED PROCEDURES (submit entire tx as one request)      │
│  • Dataset must fit in memory                                   │
│  • Write throughput must be low enough for single core          │
│                                                                  │
│  Used by: VoltDB, Redis, Datomic                                │
│                                                                  │
│  Partitioned serial execution:                                   │
│  Each partition has its own serial thread.                        │
│  Cross-partition transactions require coordination              │
│  (locking across partitions → much slower).                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Approach 2: Two-Phase Locking (2PL)

```
┌──────────────────────────────────────────────────────────────────┐
│              TWO-PHASE LOCKING (2PL)                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Rules:                                                          │
│  • To READ an object: acquire a SHARED lock                     │
│  • To WRITE an object: acquire an EXCLUSIVE lock                │
│  • If Tx A holds shared lock, Tx B wanting exclusive → WAITS    │
│  • If Tx A holds exclusive lock, ALL others → WAIT              │
│  • Locks held until END of transaction (commit or abort)        │
│                                                                  │
│  Phase 1 (Growing):  Acquire locks                               │
│  Phase 2 (Shrinking): Release locks (at commit/abort)           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Tx1: LOCK(A, shared)   → reads A                         │   │
│  │ Tx2: LOCK(A, shared)   → reads A (shared OK)             │   │
│  │ Tx1: LOCK(A, exclusive) → BLOCKED (Tx2 has shared lock)  │   │
│  │ Tx2: COMMIT → releases lock                               │   │
│  │ Tx1: acquires exclusive → writes A → COMMIT              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Prevents ALL anomalies including write skew and phantoms.      │
│                                                                  │
│  Problems:                                                       │
│  • Performance: transactions spend a lot of time WAITING        │
│  • Deadlocks: Tx1 waits for Tx2, Tx2 waits for Tx1            │
│    → Database detects deadlocks and aborts one transaction     │
│  • At high percentiles, response time can be very long          │
│  • One slow transaction blocks many others                      │
│                                                                  │
│  PREDICATE LOCKS (for phantoms):                                │
│  Lock not just existing rows but the CONDITION itself:          │
│  "Lock all rows WHERE room=123 AND time BETWEEN 12:00-13:00"  │
│  Any INSERT matching this condition must also acquire the lock. │
│                                                                  │
│  INDEX-RANGE LOCKS (practical approximation):                   │
│  Lock a larger range via the index (e.g., all bookings for     │
│  room 123, or all bookings between 12:00-13:00).               │
│  Coarser-grained but much faster than per-row predicate locks. │
│                                                                  │
│  Used by: MySQL/InnoDB (SERIALIZABLE mode), SQL Server          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Approach 3: Serializable Snapshot Isolation (SSI)

```
┌──────────────────────────────────────────────────────────────────┐
│              SERIALIZABLE SNAPSHOT ISOLATION (SSI)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  An OPTIMISTIC concurrency control approach:                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 2PL (pessimistic):                                       │    │
│  │ "If anything might go wrong, WAIT."                      │    │
│  │ Block first, proceed only when safe.                     │    │
│  │                                                          │    │
│  │ SSI (optimistic):                                        │    │
│  │ "Let it proceed, CHECK at commit time."                  │    │
│  │ If a conflict occurred → ABORT and retry.                │    │
│  │ If no conflict → COMMIT.                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Based on snapshot isolation + conflict detection:              │
│                                                                  │
│  The database tracks two things:                                 │
│  1. STALE READS: Did another committed transaction modify      │
│     data that this transaction read? (MVCC check)               │
│     → If yes, abort this transaction.                           │
│                                                                  │
│  2. STALE CONDITIONS: Did another committed transaction        │
│     write data that affects the result of a query this          │
│     transaction executed? (Write after read detection)          │
│     → If yes, abort this transaction.                          │
│                                                                  │
│  ADVANTAGES over 2PL:                                           │
│  • No blocking — transactions never wait for locks              │
│  • No deadlocks                                                 │
│  • Better performance (especially for read-heavy workloads)    │
│  • Reads from a consistent snapshot (no lock overhead)         │
│                                                                  │
│  DISADVANTAGES:                                                  │
│  • Aborted transactions must be retried                         │
│  • Higher abort rate under high contention                      │
│  • Wasted work if transactions are long-running                 │
│                                                                  │
│  Used by: PostgreSQL (9.1+ SERIALIZABLE), FoundationDB,        │
│           CockroachDB                                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Comparison of Serialization Approaches

| Aspect | Actual Serial | 2PL | SSI |
|--------|--------------|-----|-----|
| **Strategy** | Pessimistic (one at a time) | Pessimistic (locks) | Optimistic (detect conflicts) |
| **Concurrency** | None (single thread) | Limited (blocked by locks) | High (snapshot reads) |
| **Deadlocks** | Impossible | Possible (detected) | Impossible |
| **Performance** | Good if in-memory, low contention | Poor under contention | Good, but retries on abort |
| **Phantoms** | Prevented (serial) | Predicate/range locks | Detected at commit |
| **Cross-partition** | Very expensive | Possible but slow | Works across partitions |

---

## Interview Questions

### Q1: What does each letter in ACID mean precisely?

**Atomicity**: All writes in a transaction succeed or all are rolled back — no partial results. (Not about concurrency — "abortability" is a better name.) **Consistency**: Application-level invariants are maintained — this is the application's responsibility, not the database's. **Isolation**: Concurrent transactions don't interfere with each other; ideally each behaves as if running alone. **Durability**: Once committed, data survives crashes — implemented via WAL, replication, non-volatile storage.

### Q2: Explain the difference between Read Committed and Snapshot Isolation.

**Read Committed** prevents dirty reads (reading uncommitted data) and dirty writes (overwriting uncommitted data). But it allows non-repeatable reads: within one transaction, reading the same data twice may give different results if another transaction commits in between. **Snapshot Isolation** fixes this by giving each transaction a consistent snapshot of the database as of the transaction's start time, using MVCC (multi-version concurrency control). All reads within the transaction see the same snapshot, regardless of concurrent commits.

### Q3: What is write skew and how do you prevent it?

Write skew occurs when two transactions read the same data, make decisions based on what they read, then write to **different** objects — causing a violation of an invariant that depends on both objects. Example: two doctors both check that 2 doctors are on call, then both go off call → zero on call. Prevention: (1) **Serializable isolation** (2PL or SSI) prevents it automatically. (2) **Materializing conflicts**: create explicit lock rows for the constraint, then use SELECT FOR UPDATE. (3) **Explicit application-level locking**.

### Q4: Compare 2PL and SSI.

**2PL** (pessimistic): Transactions acquire shared/exclusive locks and wait for conflicting locks to be released. Prevents all anomalies but causes blocking, deadlocks, and poor performance under contention. **SSI** (optimistic): Transactions proceed without locks using snapshot reads. At commit time, the database checks whether the transaction's reads are still valid. If a conflict is detected, the transaction is aborted and must retry. SSI has higher concurrency and no deadlocks but wastes work when transactions are aborted.

### Q5: When is actual serial execution appropriate?

Actual serial execution works when: (1) the dataset fits in RAM (no disk I/O delays), (2) transactions are very short (OLTP, not OLAP), (3) write throughput is low enough for a single CPU core, (4) transactions are encapsulated as stored procedures (no multi-round-trip interactive transactions). Used by VoltDB, Redis, and Datomic. Cross-partition transactions degrade performance significantly because they require coordination across serial threads.

---

*Based on Chapter 7 of "Designing Data-Intensive Applications" by Martin Kleppmann*
