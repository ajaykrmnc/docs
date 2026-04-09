# Chapter 11: Stream Processing

## Table of Contents

1. [Transmitting Event Streams](#transmitting-event-streams)
2. [Message Brokers](#message-brokers)
3. [Log-Based Message Brokers](#log-based-message-brokers)
4. [Databases and Streams](#databases-and-streams)
5. [Processing Streams](#processing-streams)
6. [Stream Joins](#stream-joins)
7. [Fault Tolerance in Streaming](#fault-tolerance-in-streaming)
8. [Interview Questions](#interview-questions)

---

## Transmitting Event Streams

A **stream** is data that is incrementally made available over time — an unbounded dataset.

```
┌──────────────────────────────────────────────────────────────────┐
│              EVENT STREAM CONCEPTS                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EVENT: An immutable, timestamped record of something that      │
│         happened. Small, self-contained.                        │
│                                                                  │
│  Examples:                                                       │
│  • User clicked button (user_id, page, timestamp)               │
│  • Temperature reading (sensor_id, temp, timestamp)             │
│  • Order placed (order_id, items, total, timestamp)             │
│                                                                  │
│  PRODUCER (publisher/sender) ──► TOPIC/STREAM ──► CONSUMER      │
│                                                  (subscriber)   │
│                                                                  │
│  TOPIC: Named group of related events (e.g., "user-clicks")    │
│                                                                  │
│  Batch processing: input is bounded (finite dataset)            │
│  Stream processing: input is UNBOUNDED (events keep arriving)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Message Brokers

### Traditional Message Brokers vs Log-Based Brokers

```
┌──────────────────────────────────────────────────────────────────┐
│              TRADITIONAL MESSAGE BROKER                           │
│              (RabbitMQ, ActiveMQ, SQS)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Producer ──► ┌────────────────────┐ ──► Consumer A              │
│               │   Message Queue    │ ──► Consumer B              │
│               │                    │                              │
│               │ Messages DELETED   │ ← After acknowledgment     │
│               │ after consumption  │                              │
│               └────────────────────┘                              │
│                                                                  │
│  • Messages delivered to ONE consumer per queue                 │
│    (or fan-out with exchanges/topics)                           │
│  • Message DELETED after acknowledgment                         │
│  • Order NOT guaranteed across consumers                        │
│  • Consumers can be added/removed dynamically                   │
│  • If consumer is slow → messages queue up (bounded buffer)    │
│                                                                  │
│  DELIVERY GUARANTEES:                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ At-most-once:  Message may be lost, never redelivered   │    │
│  │ At-least-once: Message never lost, may be redelivered   │    │
│  │ Exactly-once:  Message processed exactly once           │    │
│  │                (hardest to achieve — see below)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Log-Based Message Brokers

```
┌──────────────────────────────────────────────────────────────────┐
│              LOG-BASED BROKER (Apache Kafka)                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Combines the durable storage of a database with the            │
│  notification mechanism of a message broker.                     │
│                                                                  │
│  TOPIC = partitioned, append-only LOG                           │
│                                                                  │
│  Topic "orders":                                                 │
│  Partition 0: [msg0 | msg1 | msg2 | msg3 | msg4 |    ...]     │
│  Partition 1: [msg0 | msg1 | msg2 | msg3 |    ...]             │
│  Partition 2: [msg0 | msg1 | msg2 |    ...]                     │
│                ▲                   ▲                              │
│                │                   │                              │
│              Oldest              Newest                          │
│                                                                  │
│  Each partition is an ORDERED, IMMUTABLE sequence of messages.  │
│  Each message has a monotonically increasing OFFSET.            │
│                                                                  │
│  CONSUMERS track their own offset:                              │
│  ┌───────────────────────────────────────────────────┐          │
│  │ Consumer Group A: [partition 0 @ offset 3]        │          │
│  │                    [partition 1 @ offset 5]        │          │
│  │ Consumer Group B: [partition 0 @ offset 1]        │ ← behind│
│  │                    [partition 1 @ offset 5]        │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                  │
│  Messages NOT deleted after consumption — retained for         │
│  a configurable period (days/weeks/forever).                    │
│  Consumer can RE-READ old messages by resetting offset.        │
│                                                                  │
│  PARTITIONING for parallelism:                                  │
│  Each partition assigned to ONE consumer in a consumer group.  │
│  More partitions → more consumers → more throughput.           │
│  Within a partition: messages ordered. Across partitions: no   │
│  ordering guarantee.                                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Kafka vs Traditional Brokers

| Feature | Traditional (RabbitMQ) | Log-Based (Kafka) |
|---------|----------------------|-------------------|
| **Message retention** | Deleted after ack | Retained for configured period |
| **Replay** | No (once consumed, gone) | Yes (reset offset) |
| **Ordering** | Per-consumer, not global | Per-partition guaranteed |
| **Consumer parallelism** | Any number of consumers | Max = number of partitions |
| **Throughput** | Lower (per-message ack) | Higher (sequential disk I/O) |
| **Use case** | Task queues, async processing | Event sourcing, CDC, analytics |

---

## Databases and Streams

### Change Data Capture (CDC)

```
┌──────────────────────────────────────────────────────────────────┐
│              CHANGE DATA CAPTURE (CDC)                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Observe all changes written to a database and extract them     │
│  as a stream of events.                                         │
│                                                                  │
│  ┌──────────┐   CDC    ┌──────────┐   Stream   ┌──────────┐   │
│  │ Primary  │─────────►│  Kafka   │──────────►│ Search   │   │
│  │ Database │  binlog   │  Topic   │           │ Index    │   │
│  │ (source  │  parsing  │          │──────────►│ (Elastic)│   │
│  │  of truth│          │          │           └──────────┘   │
│  └──────────┘          │          │──────────►┌──────────┐   │
│                         └──────────┘           │ Cache    │   │
│                                                │ (Redis)  │   │
│                                                └──────────┘   │
│                                                                  │
│  Benefits:                                                       │
│  • Derived systems (search, cache) stay in sync with DB         │
│  • No dual-write problem (write to DB, CDC handles the rest)   │
│  • Can rebuild derived system from scratch (replay CDC log)    │
│                                                                  │
│  CDC tools: Debezium, Maxwell, LinkedIn Databus, DynamoDB       │
│  Streams, PostgreSQL logical decoding                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Event Sourcing

```
┌──────────────────────────────────────────────────────────────────┐
│              EVENT SOURCING                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Instead of storing CURRENT STATE, store the SEQUENCE OF        │
│  EVENTS that led to the current state.                          │
│                                                                  │
│  Traditional (state-based):       Event Sourcing:               │
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │ Account balance: $50 │        │ Event 1: Deposit $100│      │
│  │ (just the latest     │        │ Event 2: Withdraw $30│      │
│  │  state)              │        │ Event 3: Withdraw $20│      │
│  └──────────────────────┘        │ → Derived: bal = $50 │      │
│                                   └──────────────────────┘      │
│                                                                  │
│  Key principles:                                                 │
│  • Events are IMMUTABLE (append-only log, never modified)      │
│  • Current state is DERIVED by replaying events                 │
│  • Full AUDIT TRAIL (who did what, when)                       │
│  • Can reconstruct state at ANY point in time                  │
│  • Can create NEW derived views from old events                │
│                                                                  │
│  Difference from CDC:                                            │
│  • CDC: events describe low-level DB changes (row inserted)    │
│  • Event sourcing: events describe DOMAIN-LEVEL actions         │
│    ("customer placed order", not "row inserted in orders table")│
│                                                                  │
│  Used by: Event Store, Axon Framework, accounting systems      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Processing Streams

### Stream-Table Duality

```
┌──────────────────────────────────────────────────────────────────┐
│              STREAM-TABLE DUALITY                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TABLE → STREAM:                                                │
│  Capture every change to a table → stream of changes (CDC).    │
│                                                                  │
│  STREAM → TABLE:                                                │
│  Apply every event in a stream → materialized table.           │
│  (Replay the changelog to build current state.)                │
│                                                                  │
│  Stream          Table                                           │
│  ┌──────┐        ┌──────────────────┐                           │
│  │ +A=1 │        │ A=1              │                           │
│  │ +B=2 │  ───►  │ A=1, B=2         │                           │
│  │ A=3  │        │ A=3, B=2         │  (apply events to table) │
│  │ -B   │        │ A=3              │                           │
│  └──────┘        └──────────────────┘                           │
│                                                                  │
│  This duality is fundamental:                                    │
│  • A table is a materialized view of a stream                  │
│  • A stream is the derivative (changelog) of a table           │
│  • Kafka's KSQL and Kafka Streams build on this idea           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Window Types

```
┌──────────────────────────────────────────────────────────────────┐
│              WINDOWING STRATEGIES                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TUMBLING WINDOW (fixed, non-overlapping):                      │
│  ┌────────┐┌────────┐┌────────┐┌────────┐                      │
│  │ 0-5min ││ 5-10min││10-15min││15-20min│                      │
│  └────────┘└────────┘└────────┘└────────┘                      │
│  Each event belongs to exactly one window.                      │
│                                                                  │
│  HOPPING WINDOW (fixed, overlapping):                           │
│  ┌──────────────┐                                                │
│  │  0 - 10 min  │                                                │
│  └──────────────┘                                                │
│       ┌──────────────┐                                           │
│       │  5 - 15 min  │                                           │
│       └──────────────┘                                           │
│            ┌──────────────┐                                      │
│            │ 10 - 20 min  │                                      │
│            └──────────────┘                                      │
│  Size=10min, hop=5min. Events can be in multiple windows.       │
│                                                                  │
│  SLIDING WINDOW:                                                 │
│  Contains all events within a time INTERVAL of each other.     │
│  No fixed boundaries — slides continuously.                    │
│  "All events within 5 minutes of each other."                  │
│                                                                  │
│  SESSION WINDOW:                                                 │
│  Groups events by user activity. Window ends after a            │
│  period of INACTIVITY (e.g., 30 min gap → new session).       │
│  Variable length, depends on user behavior.                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stream Joins

```
┌──────────────────────────────────────────────────────────────────┐
│              THREE TYPES OF STREAM JOINS                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. STREAM-STREAM JOIN (Window Join):                            │
│     ────────────────────────────────                             │
│     Both inputs are streams. Match events within a time window. │
│                                                                  │
│     Stream A (clicks):  ──[click user=1, url=/foo]──►           │
│     Stream B (searches): ──[search user=1, q="bar"]──►          │
│                                                                  │
│     Join: "Find searches followed by a click within 1 hour"    │
│     Must buffer events from both streams (within window).       │
│                                                                  │
│  2. STREAM-TABLE JOIN (Enrichment):                             │
│     ──────────────────────────────                               │
│     One input is a stream, the other is a database table.       │
│                                                                  │
│     Stream (orders):   ──[order: user_id=123, product=X]──►    │
│     Table (users):     {123: {name: "Bob", tier: "gold"}}      │
│                                                                  │
│     Join: Enrich each order with user info.                     │
│     Processor keeps local copy of table (updated via CDC).     │
│                                                                  │
│  3. TABLE-TABLE JOIN (Materialized View Maintenance):           │
│     ─────────────────────────────────────────────               │
│     Both inputs are CDC streams (changelogs of tables).         │
│                                                                  │
│     Stream A (tweets CDC):    ──[user=1 posted tweet]──►       │
│     Stream B (follows CDC):   ──[user=2 follows user=1]──►    │
│                                                                  │
│     Join: Maintain a timeline view (who sees which tweets).    │
│     Like a continuously-maintained materialized view.          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Fault Tolerance in Streaming

```
┌──────────────────────────────────────────────────────────────────┐
│              FAULT TOLERANCE APPROACHES                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. MICROBATCHING (Spark Streaming):                            │
│     Break stream into small batches (e.g., 1 second).          │
│     Process each batch as a mini batch job.                     │
│     If batch fails → re-run the entire batch.                  │
│     Latency = batch interval (at least 1 second).              │
│                                                                  │
│  2. CHECKPOINTING (Flink):                                      │
│     Periodically save processor state to durable storage.      │
│     On failure: restore from last checkpoint, replay events    │
│     since checkpoint from the message broker.                   │
│     Lower latency than microbatching.                           │
│                                                                  │
│  3. IDEMPOTENT WRITES:                                          │
│     Make outputs idempotent: writing the same result twice     │
│     has the same effect as writing once.                        │
│     Use (partition, offset) as a deterministic key.            │
│     If failure causes replay → same result written again      │
│     → no duplicate effect.                                     │
│                                                                  │
│  4. TRANSACTIONAL OUTPUT (Exactly-Once):                        │
│     Atomically commit processing result AND offset advance.    │
│     Kafka transactions: read → process → write output +        │
│     commit offset as a single atomic operation.                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ EXACTLY-ONCE is really "effectively-once":               │    │
│  │ Events may be PROCESSED more than once (on retry),       │    │
│  │ but the EFFECT on the output is as if processed once.    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: What is the difference between a traditional message broker and a log-based message broker?

**Traditional brokers** (RabbitMQ, SQS) delete messages after consumer acknowledgment, don't support replay, and deliver messages to individual consumers. **Log-based brokers** (Kafka) retain messages in an append-only log for a configurable period, support replay by resetting the consumer's offset, guarantee ordering within partitions, and allow multiple consumer groups to independently read the same topic. Log-based brokers are better for event sourcing, CDC, and analytics pipelines; traditional brokers are better for task queues where messages should be processed exactly once and discarded.

### Q2: What is Change Data Capture (CDC) and why is it useful?

CDC captures all changes (inserts, updates, deletes) made to a database and publishes them as a stream of events. It solves the **dual-write problem**: instead of writing to both a database and a search index (which can fail inconsistently), you write only to the database and let CDC propagate changes to derived systems (search, cache, data warehouse). Benefits: derived systems stay in sync, you can rebuild them from scratch by replaying the CDC log, and there's no risk of inconsistency from partial failures in dual writes.

### Q3: Explain the stream-table duality.

A **table** can be turned into a stream by capturing every change (CDC → changelog stream). A **stream** can be turned into a table by replaying all events and building up current state (materialized view). They are two sides of the same coin: a table is the accumulated state at a point in time; a stream is the derivative (sequence of changes) of that state. This duality underpins systems like Kafka Streams and KSQL, where you can switch between stream and table representations.

### Q4: How does exactly-once processing work in stream processing?

True "exactly-once" means events may be processed more than once (after failure and replay) but the **effect** is as if processed once. Approaches: (1) **Idempotent writes**: use deterministic keys so duplicate writes overwrite with the same value. (2) **Transactional output**: atomically commit the output and the consumer offset — if the transaction fails, both are rolled back, and the event is reprocessed. (3) **Flink checkpointing**: periodically snapshot operator state; on failure, restore and replay from the checkpoint. (4) **Microbatching** (Spark): process small batches atomically.

### Q5: What is event sourcing and how does it differ from traditional CRUD?

In traditional CRUD, you store the **current state** and overwrite it on updates. In event sourcing, you store an **immutable log of domain events** ("order placed", "item shipped") and derive current state by replaying events. Benefits: complete audit trail, ability to reconstruct state at any point in time, ability to create new derived views from historical events, and natural fit for event-driven architectures. The main challenge is that the event log grows indefinitely — you need compaction or snapshotting for practical query performance.

### Q6: Compare the four windowing strategies in stream processing.

| Window | Boundaries | Overlap | Use Case |
|--------|-----------|---------|----------|
| **Tumbling** | Fixed, aligned | None | Hourly aggregates |
| **Hopping** | Fixed, overlapping | Yes | Moving averages |
| **Sliding** | Event-relative | Yes | "Events within 5 min of each other" |
| **Session** | Activity-based, variable length | None | User session analytics |

---

*Based on Chapter 11 of "Designing Data-Intensive Applications" by Martin Kleppmann*
