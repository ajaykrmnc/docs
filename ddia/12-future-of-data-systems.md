# Chapter 12: The Future of Data Systems

## Table of Contents

1. [Data Integration](#data-integration)
2. [Unbundling Databases](#unbundling-databases)
3. [Designing for Correctness](#designing-for-correctness)
4. [Lambda and Kappa Architecture](#lambda-and-kappa-architecture)
5. [End-to-End Argument for Databases](#end-to-end-argument-for-databases)
6. [Doing the Right Thing — Ethics](#doing-the-right-thing--ethics)
7. [Interview Questions](#interview-questions)

---

## Data Integration

The biggest challenge in modern data systems is not building any single tool, but **integrating data across different systems**.

```
┌──────────────────────────────────────────────────────────────────┐
│              THE DATA INTEGRATION PROBLEM                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A typical organization has data in:                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ OLTP DB  │ │ OLTP DB  │ │  Search  │ │  Cache   │          │
│  │(Postgres)│ │(MongoDB) │ │(Elastic) │ │ (Redis)  │          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       │            │            │            │                  │
│       └────────────┼────────────┼────────────┘                  │
│                    │            │                                │
│  ┌──────────┐ ┌────┴─────┐ ┌───┴──────┐ ┌──────────┐          │
│  │  Data    │ │Analytics │ │ ML Model │ │  Graph   │          │
│  │Warehouse │ │ Dashboard│ │ Training │ │ Database │          │
│  │(Redshift)│ │          │ │          │ │ (Neo4j)  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                  │
│  PROBLEM: How do you keep all these systems consistent?         │
│                                                                  │
│  DUAL WRITES (write to each system directly):                   │
│  ✗ Race conditions → systems go out of sync                    │
│  ✗ Partial failure → some updated, some not                    │
│                                                                  │
│  SOLUTION: Use a single SOURCE OF TRUTH (e.g., OLTP database)  │
│  and derive all other representations via CDC or event streams. │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Total Ordering and Deterministic Transforms

```
┌──────────────────────────────────────────────────────────────────┐
│              DERIVED DATA ARCHITECTURE                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Source of truth          Derived systems                        │
│  (system of record)       (read-optimized views)                │
│                                                                  │
│  ┌──────────┐   CDC    ┌─────────────────────────────────┐     │
│  │  OLTP    │─────────►│  Totally Ordered Event Log      │     │
│  │ Database │          │  (e.g., Kafka)                  │     │
│  └──────────┘          └──┬────────┬──────────┬──────────┘     │
│                           │        │          │                  │
│                    Deterministic transformation                  │
│                           │        │          │                  │
│                           ▼        ▼          ▼                  │
│                    ┌──────┐ ┌──────┐ ┌────────┐                 │
│                    │Search│ │Cache │ │Data WH │                 │
│                    │Index │ │      │ │        │                 │
│                    └──────┘ └──────┘ └────────┘                 │
│                                                                  │
│  If the transformation is DETERMINISTIC and the log is          │
│  TOTALLY ORDERED, all derived systems will converge to          │
│  the same state — guaranteed.                                   │
│                                                                  │
│  This is more robust than distributed transactions (2PC)        │
│  because it's asynchronous and loosely coupled.                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Unbundling Databases

A database provides many features: storage, indexing, query processing, transactions, replication, access control. The "unbundling" idea: compose these from **separate, specialized tools**.

```
┌──────────────────────────────────────────────────────────────────┐
│              BUNDLED vs UNBUNDLED DATABASE                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BUNDLED (Traditional RDBMS):                                   │
│  ┌────────────────────────────────────────────┐                 │
│  │              PostgreSQL                     │                 │
│  │  ┌──────────┬──────────┬──────────────┐    │                 │
│  │  │ Storage  │ Indexes  │ Query Planner│    │                 │
│  │  ├──────────┼──────────┼──────────────┤    │                 │
│  │  │   WAL    │   MVCC   │ Transactions │    │                 │
│  │  ├──────────┼──────────┼──────────────┤    │                 │
│  │  │Replicat. │  Roles   │   Triggers   │    │                 │
│  │  └──────────┴──────────┴──────────────┘    │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
│  UNBUNDLED (Compose from specialized systems):                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Storage  │  │  Index   │  │ Caching  │  │Analytics │       │
│  │(Postgres)│  │(Elastic) │  │ (Redis)  │  │(Redshift)│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └──────────────┴─────────────┴─────────────┘              │
│                          │                                       │
│                    ┌─────┴─────┐                                │
│                    │  Kafka    │  (the "glue" — event log)      │
│                    │  CDC Log  │                                 │
│                    └───────────┘                                 │
│                                                                  │
│  Analogy: Unix did to operating systems what this does to       │
│  databases — decompose into composable, single-purpose tools.  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### The Advantages of Unbundling

| Aspect | Bundled (RDBMS) | Unbundled |
|--------|----------------|-----------|
| **Flexibility** | One-size-fits-all | Best tool for each job |
| **Evolution** | Upgrade entire DB | Replace/upgrade individual components |
| **Scaling** | Scale the entire system | Scale each component independently |
| **Specialization** | Good at many things | Excellent at one thing |
| **Complexity** | Simple to operate | More moving parts |
| **Consistency** | Built-in transactions | Eventual consistency (async) |

---

## Designing for Correctness

### The Problem with Exactly-Once

```
┌──────────────────────────────────────────────────────────────────┐
│              END-TO-END CORRECTNESS                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Even if the stream processor guarantees exactly-once,          │
│  the END-TO-END system may not be correct:                     │
│                                                                  │
│  User ──► Web App ──► Message Broker ──► Processor ──► Database│
│                                                                  │
│  What if the user's BROWSER retries a request?                 │
│  The message broker might see it as a new event!                │
│  Exactly-once at the broker level ≠ exactly-once end-to-end.  │
│                                                                  │
│  SOLUTIONS:                                                      │
│  1. IDEMPOTENCY KEYS: Client generates a unique request ID.    │
│     Server deduplicates by checking if ID was already processed.│
│                                                                  │
│  2. OPERATION IDENTIFIERS: Include a unique operation ID        │
│     that flows through the entire pipeline end-to-end.          │
│     Each stage deduplicates.                                    │
│                                                                  │
│  3. DETERMINISTIC DERIVATION: If derived data is a             │
│     deterministic function of input, replaying the same         │
│     input always produces the same output.                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Enforcing Constraints

```
┌──────────────────────────────────────────────────────────────────┐
│              ENFORCING UNIQUENESS IN ASYNC SYSTEMS               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Unique username constraint in an event-driven system:          │
│                                                                  │
│  APPROACH 1: Log-based (single partition per username)          │
│  All requests for the same username → same Kafka partition      │
│  → processed sequentially by a single consumer                 │
│  → first request wins, later requests rejected                  │
│                                                                  │
│  APPROACH 2: Consensus (e.g., via ZooKeeper/etcd)              │
│  Use a linearizable compare-and-set operation                   │
│  More expensive but immediately consistent                      │
│                                                                  │
│  APPROACH 3: Compensating transaction                           │
│  Accept all requests, detect conflicts later, and              │
│  send an apology email if a duplicate was accepted.            │
│  Works for many business cases (booking, orders).              │
│                                                                  │
│  Trade-off: timeliness vs. integrity vs. availability.          │
│  Not everything needs synchronous enforcement.                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Lambda and Kappa Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│              LAMBDA ARCHITECTURE                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────────┐                          │
│                    │   Incoming Data  │                          │
│                    └────────┬─────────┘                          │
│                             │                                    │
│              ┌──────────────┼──────────────┐                     │
│              ▼                             ▼                     │
│  ┌───────────────────┐         ┌───────────────────┐            │
│  │  BATCH LAYER      │         │  SPEED LAYER      │            │
│  │  (MapReduce/Spark) │         │  (Storm/Flink)    │            │
│  │                    │         │                    │            │
│  │  Processes ALL     │         │  Processes RECENT  │            │
│  │  historical data   │         │  data in real-time │            │
│  │  Correct but slow  │         │  Fast but approx.  │            │
│  └────────┬───────────┘         └────────┬───────────┘           │
│           │                               │                      │
│           ▼                               ▼                      │
│  ┌───────────────────┐         ┌───────────────────┐            │
│  │  BATCH VIEW       │         │  REAL-TIME VIEW   │            │
│  │  (complete,correct)│         │  (recent, fast)   │            │
│  └────────┬───────────┘         └────────┬──────────┘           │
│           │                               │                      │
│           └────────────┬──────────────────┘                      │
│                        ▼                                         │
│              ┌─────────────────┐                                │
│              │  SERVING LAYER  │  Merge batch + real-time views │
│              │  (query both)   │                                │
│              └─────────────────┘                                │
│                                                                  │
│  Problems: Must maintain TWO codebases (batch + stream).        │
│  Merging outputs is complex. Batch layer is slow to update.     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│              KAPPA ARCHITECTURE (simpler alternative)            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Use ONLY a stream processing layer. No separate batch layer.  │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │   Incoming Data  │                                           │
│  └────────┬─────────┘                                           │
│           ▼                                                      │
│  ┌───────────────────┐                                          │
│  │  STREAM LAYER     │  Process everything as a stream.         │
│  │  (Kafka + Flink)  │  To reprocess: replay from beginning.  │
│  └────────┬──────────┘                                          │
│           ▼                                                      │
│  ┌───────────────────┐                                          │
│  │  SERVING LAYER    │  Only one codebase to maintain.          │
│  └───────────────────┘                                          │
│                                                                  │
│  Requires: long-term log retention (Kafka with infinite         │
│  retention or tiered storage).                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Argument for Databases

```
┌──────────────────────────────────────────────────────────────────┐
│              END-TO-END ARGUMENT                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  The "end-to-end argument" (Saltzer, Reed, Clark, 1984):       │
│                                                                  │
│  Reliability features at low levels of the stack                │
│  (TCP checksums, database transactions) are NOT sufficient —   │
│  you still need end-to-end checks at the APPLICATION level.    │
│                                                                  │
│  Example:                                                        │
│  TCP guarantees in-order, reliable delivery.                    │
│  BUT: an application-level bug could still corrupt data.        │
│  You need an APPLICATION-LEVEL checksum to detect this.         │
│                                                                  │
│  For databases:                                                  │
│  A database provides ACID transactions.                         │
│  BUT: the application may still have bugs that cause            │
│  inconsistencies (write skew, race conditions in app logic).   │
│  You need END-TO-END verification (auditing, reconciliation).  │
│                                                                  │
│  AUDIT TRAIL:                                                    │
│  If you store an immutable event log, you can VERIFY            │
│  that derived state matches the events. If there's a bug,      │
│  you can detect it and recompute.                               │
│                                                                  │
│  Event sourcing + deterministic derivation + auditing           │
│  = a self-verifying, repairable data system.                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Doing the Right Thing — Ethics

```
┌──────────────────────────────────────────────────────────────────┐
│              ETHICAL CONSIDERATIONS FOR DATA SYSTEMS              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  As engineers building data-intensive applications, we must     │
│  consider the IMPACT of our systems on people:                  │
│                                                                  │
│  PREDICTIVE ANALYTICS AND BIAS:                                 │
│  • ML models trained on biased data → biased predictions       │
│  • Credit scoring, hiring, criminal justice, insurance          │
│  • Feedback loops: biased predictions → biased actions →       │
│    biased training data → worse predictions                    │
│                                                                  │
│  PRIVACY AND SURVEILLANCE:                                      │
│  • Data collected for one purpose used for another              │
│  • Users rarely understand what data is collected               │
│  • "If you have nothing to hide" is a fallacy                  │
│  • GDPR, CCPA attempt to address this legally                  │
│                                                                  │
│  DATA AS AN ASSET vs DATA AS A LIABILITY:                       │
│  • More data = more useful for analytics                        │
│  • More data = bigger target for breaches                       │
│  • Data minimization: collect only what you need               │
│  • Right to deletion: can you actually delete it from          │
│    all backups, caches, logs, and derived systems?             │
│                                                                  │
│  ACCOUNTABILITY:                                                 │
│  • Automated decisions affect real lives                        │
│  • Right to explanation (GDPR Article 22)                      │
│  • Engineers have a professional responsibility                 │
│                                                                  │
│  "Just because it's technically possible doesn't mean           │
│   it's ethically acceptable."                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: What is the dual-write problem and how do you solve it?

The dual-write problem occurs when an application writes to two systems (e.g., database and search index) independently. If one write succeeds and the other fails, or if two concurrent writes arrive in different orders at the two systems, they go out of sync. The solution is to use a **single source of truth** and derive all other representations. Write to the database, and use **Change Data Capture (CDC)** to propagate changes to search indexes, caches, and other derived systems via an event log (Kafka). This ensures a single total order of changes.

### Q2: Compare Lambda and Kappa architectures.

**Lambda architecture** runs both a batch layer (for correctness using all historical data) and a speed layer (for low-latency using recent data), then merges their outputs. It provides accurate results but requires maintaining two separate codebases doing the same computation. **Kappa architecture** uses only a stream processing layer — to reprocess historical data, replay the event log from the beginning. It's simpler (one codebase) but requires the event log to retain data long-term. Kappa is increasingly preferred due to improvements in stream processing frameworks (Flink, Kafka Streams).

### Q3: What does "unbundling the database" mean?

Traditional databases bundle many features: storage, indexing, queries, transactions, replication, access control. "Unbundling" means decomposing these into separate specialized systems (e.g., PostgreSQL for storage, Elasticsearch for search, Redis for caching, Kafka for replication/CDC) and composing them together. The event log (Kafka) plays the role of the database's internal WAL but at a system level. This gives flexibility to use the best tool for each job but adds operational complexity and trades strong consistency for eventual consistency.

### Q4: Why is end-to-end verification important even with ACID transactions?

ACID transactions guarantee correctness at the database level, but they don't protect against: application-level bugs, race conditions in application logic, data corruption in network transit, or issues in derived systems downstream. The **end-to-end argument** says reliability checks must also exist at the application level. Techniques include: immutable event logs for audit trails, checksums on application data, periodic reconciliation between source and derived systems, and deterministic derivation (so you can recompute and verify derived data matches the event log).

### Q5: What ethical considerations should engineers think about when building data systems?

(1) **Bias and fairness**: ML models can perpetuate and amplify biases in training data, affecting credit, hiring, and justice. (2) **Privacy**: Data collected for one purpose may be used for surveillance or sold; users rarely understand the full scope. (3) **Data as liability**: Every piece of data collected is a breach risk; practice data minimization. (4) **Right to deletion**: With CDC, event logs, caches, and backups, true deletion is technically very difficult. (5) **Accountability**: Automated decisions affect real lives; engineers share responsibility for the impact of their systems.

### Q6: How do you enforce a uniqueness constraint in an event-driven architecture?

Three approaches: (1) **Log-based**: Route all requests for the same key to the same Kafka partition → single consumer processes them sequentially → first wins. (2) **Consensus**: Use a linearizable store (ZooKeeper, etcd) with compare-and-set to atomically claim the unique value. (3) **Compensating transactions**: Accept all requests optimistically, detect duplicates asynchronously, and compensate (e.g., cancel one, notify the user). The choice depends on whether the business can tolerate a brief window of inconsistency.

---

*Based on Chapter 12 of "Designing Data-Intensive Applications" by Martin Kleppmann*
