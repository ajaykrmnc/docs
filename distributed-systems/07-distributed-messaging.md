# Distributed Messaging Systems

## Table of Contents
1. [Introduction to Messaging](#introduction-to-messaging)
2. [Message Queue Fundamentals](#message-queue-fundamentals)
3. [Publish-Subscribe Pattern](#publish-subscribe-pattern)
4. [Message Delivery Semantics](#message-delivery-semantics)
5. [Apache Kafka Deep Dive](#apache-kafka-deep-dive)
6. [Other Messaging Systems](#other-messaging-systems)
7. [Event-Driven Architecture](#event-driven-architecture)
8. [Interview Questions](#interview-questions)

---

## Introduction to Messaging

### Why Messaging Systems?

```
┌─────────────────────────────────────────────────────────────────┐
│              WHY MESSAGING?                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SYNCHRONOUS COMMUNICATION (Direct calls):                     │
│  ─────────────────────────────────────────                     │
│  Service A ────request────► Service B                          │
│            ◄───response────                                    │
│                                                                 │
│  Problems:                                                     │
│  • Tight coupling (A must know B)                             │
│  • A blocked waiting for B                                     │
│  • If B is down, A fails                                      │
│  • Scaling is hard                                             │
│                                                                 │
│  ASYNCHRONOUS MESSAGING:                                       │
│  ────────────────────────                                      │
│  Service A ──message──► [Message Queue] ──message──► Service B │
│                                                                 │
│  Benefits:                                                     │
│  • Loose coupling                                              │
│  • A doesn't wait for B                                        │
│  • Queue buffers if B is down                                 │
│  • Scale independently                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Decoupling** | Producers and consumers are independent |
| **Scalability** | Add more consumers to process faster |
| **Resilience** | Messages persist if consumers fail |
| **Buffering** | Handle traffic spikes |
| **Async Processing** | Fire and forget |
| **Load Leveling** | Smooth out processing over time |

---

## Message Queue Fundamentals

### Basic Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              MESSAGE QUEUE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐                           ┌──────────┐           │
│  │Producer 1│───┐                   ┌───│Consumer 1│           │
│  └──────────┘   │   ┌───────────┐   │   └──────────┘           │
│                 │   │           │   │                          │
│  ┌──────────┐   ├──►│   QUEUE   │───┼───►┌──────────┐          │
│  │Producer 2│───┤   │ [●●●●●●] │   │   │Consumer 2│          │
│  └──────────┘   │   │           │   │   └──────────┘           │
│                 │   └───────────┘   │                          │
│  ┌──────────┐   │        │         │   ┌──────────┐           │
│  │Producer 3│───┘        │         └───│Consumer 3│           │
│  └──────────┘            │             └──────────┘           │
│                          │                                     │
│                    Message Broker                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Queue vs Topic

```
┌─────────────────────────────────────────────────────────────────┐
│              QUEUE vs TOPIC                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  QUEUE (Point-to-Point):                                       │
│  ─────────────────────────                                     │
│  Each message consumed by ONE consumer                         │
│                                                                 │
│  Producer ───► [QUEUE: A B C D E] ───► Consumer 1 gets A      │
│                                   ───► Consumer 2 gets B      │
│                                   ───► Consumer 1 gets C      │
│                                                                 │
│  Use case: Work distribution, task processing                  │
│                                                                 │
│  TOPIC (Pub-Sub):                                              │
│  ─────────────────                                             │
│  Each message delivered to ALL subscribers                     │
│                                                                 │
│  Publisher ───► [TOPIC: A B C] ───► Subscriber 1 gets A,B,C   │
│                                ───► Subscriber 2 gets A,B,C   │
│                                ───► Subscriber 3 gets A,B,C   │
│                                                                 │
│  Use case: Event broadcasting, notifications                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Message Ordering

```
┌─────────────────────────────────────────────────────────────────┐
│              MESSAGE ORDERING                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. NO ORDERING GUARANTEE                                      │
│     Messages may arrive in any order                           │
│     Sent: A → B → C                                           │
│     Received: B → A → C (possible)                            │
│                                                                 │
│  2. FIFO (First-In-First-Out)                                 │
│     Messages arrive in send order                              │
│     Sent: A → B → C                                           │
│     Received: A → B → C (guaranteed)                          │
│                                                                 │
│  3. PARTITION ORDERING                                         │
│     Order guaranteed within partition only                     │
│                                                                 │
│     Partition 0: A1 → A2 → A3  (ordered)                      │
│     Partition 1: B1 → B2 → B3  (ordered)                      │
│     No order between A and B messages                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Publish-Subscribe Pattern

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              PUB-SUB PATTERN                                    │


---

## Message Delivery Semantics

### The Three Guarantees

```
┌─────────────────────────────────────────────────────────────────┐
│              DELIVERY SEMANTICS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. AT-MOST-ONCE                                               │
│  ───────────────                                               │
│  Message delivered 0 or 1 time                                 │
│  • Fire and forget                                             │
│  • No retries                                                  │
│  • Possible message loss                                       │
│                                                                 │
│  Producer ───[msg]───X───► Lost!                              │
│                                                                 │
│  Use case: Metrics, logging (loss acceptable)                 │
│                                                                 │
│  2. AT-LEAST-ONCE                                              │
│  ────────────────                                              │
│  Message delivered 1 or more times                             │
│  • Retries until acknowledged                                  │
│  • Possible duplicates                                         │
│  • No message loss                                             │
│                                                                 │
│  Producer ───[msg]───► Consumer                               │
│          ───[msg]───► (retry on timeout, duplicate!)          │
│                                                                 │
│  Use case: Payments (with idempotency)                        │
│                                                                 │
│  3. EXACTLY-ONCE                                               │
│  ───────────────                                               │
│  Message delivered exactly 1 time                              │
│  • Hardest to achieve                                          │
│  • Requires idempotency or deduplication                      │
│  • Often "effectively once"                                    │
│                                                                 │
│  Producer ───[msg]───► Consumer (processed exactly once)      │
│                                                                 │
│  Use case: Financial transactions                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementing Exactly-Once

```
┌─────────────────────────────────────────────────────────────────┐
│              EXACTLY-ONCE STRATEGIES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. IDEMPOTENCY                                                │
│  ──────────────                                                │
│  Make operations safe to repeat:                               │
│  • Use unique message ID                                       │
│  • Check if already processed before processing               │
│                                                                 │
│  CREATE TABLE processed_messages (                             │
│    message_id UUID PRIMARY KEY,                                │
│    processed_at TIMESTAMP                                      │
│  );                                                             │
│                                                                 │
│  2. TRANSACTIONAL OUTBOX                                       │
│  ────────────────────────                                      │
│  Write business data + message in single transaction:          │
│                                                                 │
│  BEGIN TRANSACTION;                                            │
│    UPDATE accounts SET balance = balance - 100;                │
│    INSERT INTO outbox (message) VALUES ('transfer');           │
│  COMMIT;                                                        │
│                                                                 │
│  3. DEDUPLICATION AT CONSUMER                                  │
│  ────────────────────────────                                  │
│  Track processed message IDs and skip duplicates              │
│                                                                 │
│  4. KAFKA EXACTLY-ONCE (idempotent producer + transactions)   │
│  ────────────────────────────────────────────────             │
│  Producer: idempotent writes (sequence numbers)                │
│  Consumer: read-process-commit atomically                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Apache Kafka Deep Dive

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              KAFKA ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    KAFKA CLUSTER                         │   │
│  │                                                           │   │
│  │  Broker 1          Broker 2          Broker 3            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │Topic A, P0(L)│  │Topic A, P0(R)│  │Topic A, P1(R)│   │   │
│  │  │Topic A, P1(L)│  │Topic B, P0(L)│  │Topic B, P0(R)│   │   │
│  │  │Topic B, P1(R)│  │Topic B, P1(L)│  │Topic A, P0(R)│   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                           │   │
│  │  L = Leader, R = Replica                                 │   │
│  │                                                           │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│              ┌───────────────┼───────────────┐                 │
│              ▼               ▼               ▼                 │
│         Zookeeper/     Producers        Consumers              │
│         KRaft                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Topic and Partitions

```
┌─────────────────────────────────────────────────────────────────┐
│              KAFKA TOPICS AND PARTITIONS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Topic: orders                                                 │
│                                                                 │
│  Partition 0:  [0][1][2][3][4][5][6] ──────► write            │
│                        │                                        │
│  Partition 1:  [0][1][2][3][4] ────────────► write            │
│                        │                                        │
│  Partition 2:  [0][1][2][3][4][5][6][7] ──► write             │
│                        │                                        │
│                        │                                        │
│                  Each message has:                             │
│                  • Offset (position in partition)              │
│                  • Key (optional, for partitioning)           │
│                  • Value (message payload)                     │
│                  • Timestamp                                   │
│                                                                 │
│  Partitioning Strategy:                                        │
│  • Key-based: hash(key) % num_partitions                      │
│  • Round-robin: distribute evenly (no key)                    │
│  • Custom: user-defined partitioner                           │
│                                                                 │
│  Benefits of partitioning:                                     │
│  • Parallelism (more consumers)                               │
│  • Ordering per partition                                      │
│  • Throughput scaling                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Kafka Replication

```
┌─────────────────────────────────────────────────────────────────┐
│              KAFKA REPLICATION                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Partition 0 with replication factor = 3:                      │
│                                                                 │
│  Broker 1           Broker 2           Broker 3                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   P0        │   │   P0        │   │   P0        │          │
│  │  (LEADER)   │   │  (FOLLOWER) │   │  (FOLLOWER) │          │
│  │             │   │             │   │             │          │
│  │  [0][1][2]  │──►│  [0][1][2]  │   │  [0][1]     │          │
│  │   ISR ✓     │   │   ISR ✓     │   │   not ISR   │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                 │
│  ISR (In-Sync Replicas):                                      │
│  • Replicas caught up with leader                             │
│  • Messages only committed after all ISR acknowledge          │
│                                                                 │
│  Writes: Only to leader                                        │
│  Reads: From leader (or followers with read-your-writes)      │
│                                                                 │
│  Durability settings:                                          │
│  • acks=0: No wait (fastest, may lose)                        │
│  • acks=1: Wait for leader (balance)                          │
│  • acks=all: Wait for all ISR (safest, slowest)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Consumer Offsets

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSUMER OFFSET MANAGEMENT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Partition 0:  [0][1][2][3][4][5][6][7][8][9]                 │
│                               │                                 │
│                     committed offset = 5                       │
│                               │                                 │
│                     Consumer reading from here                 │
│                                                                 │
│  Offset Commit Strategies:                                     │
│  ──────────────────────────                                    │
│                                                                 │
│  1. AUTO-COMMIT (default)                                      │
│     • Periodic commit (every N seconds)                       │
│     • May lose messages or duplicate                          │
│                                                                 │
│  2. MANUAL COMMIT                                              │
│     • Commit after processing                                  │
│     • More control, at-least-once                             │
│                                                                 │
│  3. MANUAL COMMIT + IDEMPOTENCY                               │
│     • Process + commit atomically                             │
│     • Effectively exactly-once                                │
│                                                                 │
│  Stored in: __consumer_offsets topic                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Other Messaging Systems

### Comparison

| Feature | Kafka | RabbitMQ | AWS SQS | Redis Pub/Sub |
|---------|-------|----------|---------|---------------|
| **Model** | Log-based | Queue + Pub/Sub | Queue | Pub/Sub |
| **Ordering** | Partition | Per queue | FIFO optional | None |
| **Persistence** | Yes | Optional | Yes | No |
| **Throughput** | Very high | Medium | Medium | High |
| **Replay** | Yes | No | No | No |
| **Use case** | Event streaming | Task queues | Cloud queues | Real-time |

### RabbitMQ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              RABBITMQ ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Producer ──► Exchange ──► Queue ──► Consumer                  │
│                  │                                              │
│                  │ Binding (routing rule)                      │
│                  │                                              │
│  Exchange Types:                                               │
│  • Direct: exact routing key match                            │
│  • Fanout: broadcast to all queues                            │
│  • Topic: pattern matching (*.error, #.log)                   │
│  • Headers: match on message headers                          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                    DIRECT EXCHANGE                      │   │
│  │                                                          │   │
│  │  Producer ───[routing_key=error]──► Exchange           │   │
│  │                                         │               │   │
│  │                        ┌────────────────┼────────┐      │   │
│  │                        ▼                ▼        ▼      │   │
│  │                   [Q: error]      [Q: warning] [Q: info]│   │
│  │                        │                               │   │
│  │                   Consumer                              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Event-Driven Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              EVENT-DRIVEN ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Traditional Request-Response:                                 │
│  ───────────────────────────                                   │
│  Order Service ───► Inventory ───► Payment ───► Shipping      │
│  (synchronous, coupled)                                        │
│                                                                 │
│  Event-Driven:                                                 │
│  ─────────────                                                 │
│                    ┌───────────────────────┐                   │
│  Order Service ───►│    EVENT BUS          │                   │
│                    │  [OrderCreated]       │                   │
│                    └─────────┬─────────────┘                   │
│           ┌──────────────────┼──────────────────┐              │
│           ▼                  ▼                  ▼              │
│       Inventory         Payment            Shipping           │
│       Service           Service            Service            │
│                                                                 │
│  Benefits:                                                     │
│  • Services loosely coupled                                   │
│  • Easy to add new consumers                                  │
│  • Better scalability                                         │
│  • Audit trail (event log)                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Event Sourcing

```
┌─────────────────────────────────────────────────────────────────┐
│              EVENT SOURCING                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Traditional: Store current state                              │
│  ───────────────────────────────                               │
│  Account: { id: 123, balance: 150 }                           │
│                                                                 │
│  Event Sourcing: Store events                                  │
│  ────────────────────────────────                              │
│  Event 1: AccountCreated(id=123, balance=0)                   │
│  Event 2: MoneyDeposited(id=123, amount=200)                  │
│  Event 3: MoneyWithdrawn(id=123, amount=50)                   │
│                                                                 │
│  Current state = replay(events)                               │
│  0 + 200 - 50 = 150                                           │
│                                                                 │
│  Benefits:                                                     │
│  • Complete audit history                                     │
│  • Reconstruct state at any point                            │
│  • Debug by replaying events                                  │
│  • Event-driven by design                                     │
│                                                                 │
│  Challenges:                                                   │
│  • Schema evolution                                            │
│  • Storage growth                                              │
│  • Query complexity (need CQRS)                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### CQRS (Command Query Responsibility Segregation)

```
┌─────────────────────────────────────────────────────────────────┐
│              CQRS PATTERN                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     ┌───────────────┐                          │
│                     │   Commands    │                          │
│                     │  (Write ops)  │                          │
│                     └───────┬───────┘                          │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────┐     ┌───────────┐     ┌─────────────────┐    │
│  │   Event     │◄────│  Command  │────►│  Event Store    │    │
│  │   Bus       │     │  Handler  │     │  (Write Model)  │    │
│  └──────┬──────┘     └───────────┘     └─────────────────┘    │
│         │                                                       │
│         │  Events                                              │
│         ▼                                                       │
│  ┌─────────────┐     ┌───────────┐     ┌─────────────────┐    │
│  │   Query     │◄────│  Query    │────►│  Read Model     │    │
│  │   Results   │     │  Handler  │     │  (Optimized)    │    │
│  └─────────────┘     └───────────┘     └─────────────────┘    │
│                                                                 │
│  Separate models for writes and reads!                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: What's the difference between at-least-once and exactly-once delivery?**

| Aspect | At-Least-Once | Exactly-Once |
|--------|--------------|--------------|
| Guarantee | Message delivered ≥1 time | Message delivered =1 time |
| Duplicates | Possible | None |
| Implementation | Retry until ACK | Idempotency + deduplication |
| Performance | Faster | Slower (more overhead) |
| Use case | Most applications | Financial transactions |

**Q2: How does Kafka achieve high throughput?**

1. **Sequential I/O**: Append-only log, no random seeks
2. **Zero-copy**: sendfile() system call
3. **Batching**: Batch messages for network and disk
4. **Compression**: Reduce network/disk usage
5. **Partitioning**: Parallel processing
6. **Page cache**: OS caches data in memory

**Q3: Explain consumer groups in Kafka.**

- Consumer group = set of consumers sharing work
- Each partition assigned to ONE consumer in group
- Multiple groups can read same topic independently
- Enables both load balancing AND fan-out

**Q4: What is the transactional outbox pattern?**

```
Problem: Need to update DB AND send message atomically

Solution:
1. Write business data + message to outbox table in same transaction
2. Separate process reads outbox and publishes to message broker
3. Mark outbox entries as processed

Benefits:
- Atomic operation (single transaction)
- At-least-once delivery
- No distributed transaction needed
```

### Design Questions

**Q5: Design a notification system using messaging.**

```
Architecture:
├── Event producers (user actions, system events)
├── Kafka topics by event type
├── Notification service (consumer)
│   ├── Deduplication (idempotency key)
│   ├── User preferences check
│   ├── Rate limiting
│   └── Channel routing (email, push, SMS)
├── Dead letter queue for failures
└── Retry with exponential backoff
```

**Q6: How would you handle message ordering in a distributed system?**

Strategies:
1. **Single partition**: All related messages to same partition
2. **Sequence numbers**: Consumer reorders based on sequence
3. **Causal ordering**: Vector clocks for causality
4. **Accept eventual consistency**: Design for out-of-order

---

## Summary

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         MESSAGING CHEAT SHEET                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DELIVERY SEMANTICS:                                           │
│  • At-most-once: Fire and forget                              │
│  • At-least-once: Retry until ACK (may duplicate)             │
│  • Exactly-once: Idempotency + deduplication                  │
│                                                                 │
│  KAFKA KEY CONCEPTS:                                           │
│  • Topic: Category of messages                                 │
│  • Partition: Ordered, immutable log                          │
│  • Offset: Position in partition                              │
│  • Consumer group: Load-balanced consumers                    │
│  • ISR: In-sync replicas                                      │
│                                                                 │
│  PATTERNS:                                                     │
│  • Queue: Point-to-point, work distribution                   │
│  • Pub/Sub: Broadcast to all subscribers                      │
│  • Event sourcing: Store events, derive state                 │
│  • CQRS: Separate read/write models                           │
│                                                                 │
│  KAFKA ACKS:                                                   │
│  • acks=0: No wait (fastest, may lose)                        │
│  • acks=1: Wait for leader                                    │
│  • acks=all: Wait for all ISR (safest)                       │
│                                                                 │
│  EXACTLY-ONCE STRATEGIES:                                      │
│  • Idempotent operations                                       │
│  • Transactional outbox                                        │
│  • Deduplication at consumer                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

