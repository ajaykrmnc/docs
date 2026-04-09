# Transactions & Concurrency Control — Hard Interview Questions

## Q1: MVCC Implementation Deep Dive

1. Compare PostgreSQL's MVCC (append-only, xmin/xmax) with MySQL InnoDB's MVCC (undo log, rollback segments). What are the trade-offs in terms of storage overhead, garbage collection, and long-running transaction impact?
2. In PostgreSQL, a transaction with snapshot `xmin=100, xmax=150, xip=[105, 110, 120]` tries to read a tuple with `(xmin=110, xmax=130)`. Is this tuple visible? Walk through the visibility check algorithm.
3. Explain the "transaction ID wraparound" problem in PostgreSQL. Why is it dangerous, and what does `VACUUM FREEZE` do?
4. How does Oracle's read consistency model differ from PostgreSQL's snapshot isolation? Specifically, explain statement-level vs. transaction-level snapshots.

### Expected Answer Outline

- **PostgreSQL MVCC**: Every UPDATE creates a new physical tuple version. Old versions remain on the heap until VACUUM removes them. Pros: reads never block writes, simple implementation. Cons: table bloat, VACUUM overhead, index bloat (multiple index entries per logical row).
- **InnoDB MVCC**: Updates modify the row in place. The old version is written to an undo log (rollback segment). Reads reconstruct old versions by applying undo records in reverse. Pros: no table bloat, no separate GC for heap. Cons: long undo chains degrade read performance for old snapshots, undo log space management.
- **Visibility check**: Tuple's xmin=110 is in the snapshot's xip (in-progress list), so the inserting transaction was still running when the snapshot was taken. The tuple is **not visible** — regardless of xmax, because the creating transaction is not committed from this snapshot's perspective.
- **Transaction ID wraparound**: PostgreSQL uses 32-bit transaction IDs. After ~2 billion transactions, IDs wrap around, and past-committed transactions could appear to be "in the future." `VACUUM FREEZE` marks old tuples with a special frozen xmin, removing them from the wraparound comparison. If not done in time, PostgreSQL shuts down to prevent data corruption.
- **Oracle read consistency**: Statement-level by default — each statement sees data as of the statement's start time, even within a long transaction. PostgreSQL REPEATABLE READ/Serializable sees data as of the transaction's start. Oracle achieves this by reconstructing blocks from undo when needed.

---

## Q2: Serializable Snapshot Isolation (SSI)

1. Explain the write skew anomaly. Provide a concrete example with two concurrent transactions that both pass validation under snapshot isolation but produce a result that is not serializable.
2. How does SSI (as implemented in PostgreSQL 9.1+) detect potential serialization anomalies? Explain the rw-antidependency tracking and the "dangerous structure" (two consecutive rw-antidependencies forming a cycle).
3. Why does SSI abort transactions that may cause anomalies rather than blocking them? What is the false positive rate, and how does it affect throughput?
4. Compare SSI with S2PL (Strict Two-Phase Locking). Under what workloads does SSI provide significantly better throughput?

### Expected Answer Outline

- **Write skew example**: Two doctors on call. Constraint: at least one must be on call. Both read that 2 are on call. Both concurrently remove themselves. Under SI, both succeed (each saw the other as on-call). Result: 0 on call, violating the constraint. Serializable execution would have blocked one.
- **SSI detection**: Track rw-antidependencies: T1 reads a version that T2 later overwrites (T1 -rw-> T2). If two consecutive rw-antidependencies form a cycle (T1 -rw-> T2 -rw-> T1, involving a "pivot" transaction), this is a dangerous structure. SSI aborts one transaction when it detects such a structure at commit time.
- **Abort vs block**: SSI is optimistic — transactions run without locking, maximizing concurrency. The cost is false positives: some aborted transactions would have been serializable. False positive rate depends on workload but is typically low for read-heavy workloads. The benefit is eliminating deadlocks and reducing lock contention.
- **SSI vs S2PL**: SSI excels in read-heavy workloads with rare conflicts. S2PL's shared locks on reads cause contention under high concurrency. SSI allows all reads without locking. For write-heavy, high-contention workloads, S2PL may be comparable because SSI would abort many transactions.

---

## Q3: Lock Management and Deadlocks

1. Explain the difference between a lock table (hash-table-based) and a lock-free approach using optimistic concurrency control. What are the CPU cache implications of a centralized lock table under high concurrency?
2. A system uses wound-wait deadlock prevention. Transaction T1 (timestamp 10) requests a lock held by T2 (timestamp 20). Transaction T3 (timestamp 15) requests a lock held by T1. What happens in each case? Now repeat for wait-die.
3. You observe deadlocks occurring frequently in a production system. The deadlock detector runs every 1 second via a waits-for graph cycle detection. Propose a strategy to reduce deadlock frequency without changing the application code.
4. Describe hierarchical locking (intention locks). A transaction does `SELECT * FROM T WHERE id = 5` followed by `UPDATE T SET x = 1 WHERE id = 5`. Trace the lock acquisition sequence at the table, page, and row levels.

### Expected Answer Outline

- **Lock table**: Hash table mapping resource IDs to lock queues. Centralized structure means cache line contention under high concurrency (many threads updating the same hash bucket). Lock-free OCC avoids this by validating at commit time, but aborts are expensive. Partitioned lock tables mitigate contention.
- **Wound-wait**: Older transaction "wounds" (aborts) younger if younger holds the lock. T1 (older) wounds T2 (younger) — T2 is aborted, T1 gets the lock. T3 (younger than T1) requests T1's lock — T3 waits (younger waits for older). **Wait-die**: Older waits for younger; younger dies if requesting older's lock. T1 waits for T2's lock. T3 requesting T1's lock: T3 is younger than T1, so T3 dies (is aborted).
- **Reducing deadlocks**: (a) Lock escalation — acquire coarser-grained locks to reduce the number of lock interactions. (b) Consistent lock ordering — if the system can enforce a canonical ordering on resources, deadlocks are structurally impossible. (c) Shorter transaction duration — reduce hold times. (d) Use deadlock prevention (wound-wait) instead of detection.
- **Hierarchical locking**: SELECT: acquire IS (Intention Shared) on table, IS on page, S on row (id=5). UPDATE: escalate row lock to X (Exclusive), escalate page lock to IX (Intention Exclusive), escalate table lock to IX. The intention locks at higher levels prevent conflicting table/page-level locks without checking every row.

---

## Q4: Phantom Reads and Predicate Locking

1. What is the phantom problem? Why can't row-level locking prevent it?
2. Explain how next-key locking (as in InnoDB) prevents phantoms. Given an index on column `age` with existing values {10, 20, 30}, a transaction runs `SELECT * FROM T WHERE age BETWEEN 15 AND 25`. What range is locked?
3. What is predicate locking? Why is it theoretically optimal but practically expensive?
4. Compare gap locking, next-key locking, and predicate locking in terms of false positives (unnecessarily blocked transactions) and implementation complexity.

### Expected Answer Outline

- **Phantom problem**: A transaction reads a set of rows matching a predicate. A concurrent transaction inserts a new row matching the same predicate. On re-read, the first transaction sees a "phantom" row that didn't exist before. Row-level locks only protect existing rows, not the "gaps" where new rows could be inserted.
- **Next-key locking**: InnoDB locks index records and the gap before each record. For `age BETWEEN 15 AND 25` with existing values {10, 20, 30}: locks the gap (10, 20], the record 20, and the gap (20, 30]. This prevents inserts with age 15-25 and the gap up to 30. The lock `(10, 20]` is the "next-key lock" on record 20.
- **Predicate locking**: Locks the logical predicate itself (e.g., `age BETWEEN 15 AND 25`). Any insert/update that would satisfy the predicate is blocked. Optimal precision — no false positives. But checking every insert against all active predicate locks is expensive (predicate satisfiability is NP-hard in general).
- **Comparison**: Gap locking: coarse, may block unrelated inserts in the gap. Next-key locking: slightly finer, but still locks more than necessary. Predicate locking: precise but expensive. In practice, next-key locking is the best trade-off.

---

## Q5: Two-Phase Commit Deep Dive

1. Walk through the 2PC protocol. What happens if the coordinator crashes after sending PREPARE but before sending COMMIT? Why is this the "blocking" problem?
2. Explain the three-phase commit (3PC) protocol. What property does it add over 2PC? Why is 3PC not used in practice?
3. Describe the Paxos Commit protocol. How does it solve the blocking problem of 2PC?
4. In a microservices architecture using the Saga pattern instead of 2PC, explain: (a) the difference between choreography and orchestration sagas, (b) how compensating transactions work, (c) why Sagas do not provide isolation. Give a concrete example of an anomaly.

### Expected Answer Outline

- **2PC blocking**: After participants vote YES (prepared), they cannot unilaterally abort or commit — they must wait for the coordinator's decision. If the coordinator crashes, participants holding locks are stuck indefinitely. They cannot timeout and abort because the coordinator may have committed. Recovery requires the coordinator to recover and replay its decision log.
- **3PC**: Adds a PRE-COMMIT phase between PREPARE and COMMIT. If the coordinator crashes during PRE-COMMIT, participants can detect the situation and reach a decision among themselves (if all are in PRE-COMMIT state, commit; otherwise, abort). 3PC adds non-blocking property. Not used in practice because it assumes a synchronous network with bounded message delays and no network partitions — unrealistic in distributed systems.
- **Paxos Commit**: Replaces the single coordinator with a Paxos group. Each participant runs its own Paxos instance to replicate its vote. The commit decision is made by the Paxos group, which tolerates coordinator failures. Non-blocking because Paxos can elect a new leader. Cost: more messages (O(N^2) vs O(N) for 2PC).
- **Sagas**: Choreography: each service publishes events, next service reacts. Orchestration: a central orchestrator directs each step. Compensating transactions: undo the effect of a committed step (e.g., refund a payment). Isolation anomaly: a concurrent transaction reads intermediate state (e.g., an order shows as "paid" before shipping step runs, then the shipping step fails and the saga compensates — but another transaction already read the "paid" state).
