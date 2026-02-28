# Transaction Models

## Overview

Jim Gray and Andreas Reuter describe several transaction models beyond the basic "flat" transaction. Each model addresses different requirements for complex business operations, long-running processes, and distributed systems.

---

## 1. Flat Transactions

### Definition

The simplest and most common transaction model. A flat transaction is a sequence of operations with a single start and end point.

```
BEGIN TRANSACTION
    operation1
    operation2
    ...
    operationN
COMMIT/ROLLBACK
```

### Characteristics

| Property | Description |
|----------|-------------|
| Single level | No sub-transactions |
| All-or-nothing | Complete rollback on failure |
| Short duration | Designed for brief operations |
| Simple | Easy to implement and understand |

### Limitations

1. **All-or-nothing problem**: If operation N fails, ALL previous work is lost
2. **No partial rollback**: Cannot save intermediate progress
3. **Lock duration**: All locks held until commit/abort
4. **Not suitable for long operations**: Resources held too long

### Example: Bank Transfer

```sql
BEGIN TRANSACTION;
    UPDATE accounts SET balance = balance - 100 WHERE id = 'A';
    UPDATE accounts SET balance = balance + 100 WHERE id = 'B';
    INSERT INTO transfers(from_acc, to_acc, amount) VALUES ('A', 'B', 100);
COMMIT;
-- If ANY statement fails, ALL changes are rolled back
```

---

## 2. Flat Transactions with Savepoints

### Definition

An extension of flat transactions that allows partial rollback to predefined savepoints.

```
BEGIN TRANSACTION
    operation1
    SAVEPOINT sp1
    operation2
    SAVEPOINT sp2
    operation3
    -- If error occurs:
    ROLLBACK TO sp1  -- Undo operation2 and operation3
    -- Continue from sp1
COMMIT
```

### Savepoint Semantics

```
┌─────────────────────────────────────────────────────────┐
│                    Transaction T                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  BEGIN ─────► op1 ─────► SAVEPOINT1 ─────► op2         │
│                              │                          │
│                              │ (ROLLBACK TO SAVEPOINT1) │
│                              ▼                          │
│                         ┌────────┐                      │
│                         │ op1    │ ← State preserved    │
│                         │ kept   │                      │
│                         └────────┘                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### SQL Syntax

```sql
BEGIN TRANSACTION;

    INSERT INTO orders(id, customer) VALUES (1, 'John');
    SAVEPOINT order_created;

    INSERT INTO order_items(order_id, product) VALUES (1, 'Widget');
    SAVEPOINT items_added;

    UPDATE inventory SET quantity = quantity - 1 WHERE product = 'Widget';

    -- If inventory update fails:
    ROLLBACK TO items_added;
    -- Order and items still exist, only inventory change rolled back

COMMIT;
```

### Savepoint Properties

| Feature | Behavior |
|---------|----------|
| Nested savepoints | Supported - rollback to any previous savepoint |
| Lock retention | Locks acquired after savepoint may be released |
| Persistent | Savepoints persist until transaction ends |
| Named | Each savepoint has a unique identifier |

---

## 3. Chained Transactions

### Definition

A sequence of transactions where each transaction automatically starts when the previous one commits. The commit of one transaction is the begin of the next.

---

## 4. Nested Transactions

### Definition

Transactions that can contain sub-transactions, forming a hierarchy. Each sub-transaction can commit or abort independently.

### Nested Transaction Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     Top-Level Transaction T                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Sub-transaction T1                  │    │
│  │  ┌─────────────────┐    ┌─────────────────┐        │    │
│  │  │ Sub-sub T1.1    │    │ Sub-sub T1.2    │        │    │
│  │  │                 │    │                 │        │    │
│  │  └─────────────────┘    └─────────────────┘        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Sub-transaction T2                  │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Commit Rules for Nested Transactions

| Rule | Description |
|------|-------------|
| **Commit rule** | Sub-transaction commit is conditional on parent commit |
| **Abort rule** | Parent abort causes all descendants to abort |
| **Visibility** | Sub-transaction results visible to parent after sub-commit |
| **Isolation** | Sub-transactions isolated from siblings |

### Nested Transaction Semantics

```
T (parent)
├── T1 (child) - COMMITS
│   └── Result visible to T
├── T2 (child) - ABORTS
│   └── Changes undone, but T continues
└── T COMMITS
    └── T1's changes become durable

If T ABORTS:
└── Even T1's committed changes are undone!
```

### Example: Travel Booking

```
BEGIN TRANSACTION BookTrip

    BEGIN SUB-TRANSACTION BookFlight
        -- Reserve flight
        IF success THEN COMMIT
        ELSE ABORT  -- Only flight booking undone
    END

    BEGIN SUB-TRANSACTION BookHotel
        -- Reserve hotel
        IF success THEN COMMIT
        ELSE ABORT  -- Only hotel booking undone
    END

    BEGIN SUB-TRANSACTION BookCar
        -- Reserve car
        IF success THEN COMMIT
        ELSE ABORT  -- Only car booking undone
    END

    IF all_bookings_successful THEN
        COMMIT BookTrip  -- All become permanent
    ELSE
        ABORT BookTrip   -- All undone (even committed subs)
    END

END TRANSACTION
```

---

## 5. Sagas

### Definition

A saga is a long-lived transaction (LLT) implemented as a sequence of sub-transactions with compensating transactions for each step. Developed by Garcia-Molina and Salem (1987), heavily influenced by Gray's work.

### Saga Structure

```
Saga S = T1, T2, T3, ..., Tn
Compensating Transactions: C1, C2, C3, ..., Cn-1

Forward execution: T1 → T2 → T3 → ... → Tn
Compensation (if Tk fails): Ck-1 → Ck-2 → ... → C1
```

### Saga Execution Patterns

```
SUCCESSFUL SAGA:
T1 ──► T2 ──► T3 ──► T4 ──► T5 ──► COMPLETE
 │      │      │      │      │
 ▼      ▼      ▼      ▼      ▼
C1     C2     C3     C4     --  (compensations available but not needed)


FAILED SAGA (failure at T4):
T1 ──► T2 ──► T3 ──► T4 ✗
 │      │      │
 ▼      ▼      ▼
C1 ◄── C2 ◄── C3     (compensations execute in reverse)
```

### Compensating Transactions

| Original Transaction | Compensating Transaction |
|---------------------|-------------------------|
| Debit account | Credit account |
| Create reservation | Cancel reservation |
| Ship order | Return shipment |
| Send email | Send cancellation email |

### Saga Example: E-Commerce Order

```
SAGA: ProcessOrder

T1: Reserve Inventory
    C1: Release Inventory

T2: Charge Credit Card
    C2: Refund Credit Card

T3: Update Order Status
    C3: Revert Order Status

T4: Ship Product
    C4: Request Return

T5: Send Confirmation Email
    C5: Send Cancellation Email

-- If T3 fails:
-- Execute: C2 (refund) → C1 (release inventory)
-- T3, T4, T5 never executed, so no compensation needed
```

### Saga Coordination Patterns

#### Choreography (Event-Driven)
```
┌─────────┐   event   ┌─────────┐   event   ┌─────────┐
│Service A│ ────────► │Service B│ ────────► │Service C│
│   T1    │           │   T2    │           │   T3    │
└─────────┘           └─────────┘           └─────────┘
     │                     │                     │
     ▼                     ▼                     ▼
  publishes            publishes            publishes
   event                event                event
```

#### Orchestration (Central Coordinator)
```
              ┌─────────────────┐
              │   Orchestrator  │
              │   (Saga Exec)   │
              └───────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │Service A│   │Service B│   │Service C│
   │   T1    │   │   T2    │   │   T3    │
   └─────────┘   └─────────┘   └─────────┘
```

---

## 6. Multi-Level Transactions

### Definition

A transaction model that leverages the semantics of operations at different abstraction levels to provide more flexibility than strict serializability.

### Levels of Abstraction

```
Level 2: Business Operations
├── Transfer(A→B, $100)
│
Level 1: Database Operations
├── Update(A, balance -= 100)
├── Update(B, balance += 100)
│
Level 0: Page Operations
├── Read Page(p1)
├── Write Page(p1)
├── Read Page(p2)
├── Write Page(p2)
```

### Semantic-Based Concurrency

At higher levels, operations that conflict at the page level may be compatible:

```
T1: Deposit(A, $50)    -- Write page containing A
T2: Withdraw(A, $30)   -- Write page containing A

At page level: CONFLICT (both write same page)
At semantic level: COMMUTATIVE (order doesn't matter for final balance)
```

---

## Model Comparison

| Model | Rollback Scope | Duration | Complexity | Use Case |
|-------|---------------|----------|------------|----------|
| Flat | All or nothing | Short | Simple | OLTP |
| Savepoints | To savepoint | Short-Medium | Medium | Batch processing |
| Chained | Per chain | Long | Medium | Large batches |
| Nested | Per sub-transaction | Variable | Complex | Modular operations |
| Sagas | Via compensation | Long | Complex | Distributed workflows |
| Multi-level | Level-dependent | Variable | Very Complex | Specialized systems |

---

## Key Takeaways

1. **Flat transactions** are simple but limited for complex operations
2. **Savepoints** provide partial rollback within a transaction
3. **Chained transactions** release locks incrementally
4. **Nested transactions** allow modular transaction design
5. **Sagas** handle long-running distributed transactions via compensation
6. **Multi-level transactions** exploit semantic knowledge for better concurrency

---

## References

- Gray, J. & Reuter, A. (1993). Chapter 4: "Transaction Models"
- Garcia-Molina, H. & Salem, K. (1987). "Sagas"
- Moss, J.E.B. (1985). "Nested Transactions"


```
BEGIN T1
    operations...
COMMIT AND CHAIN  ──► BEGIN T2 (automatic)
    operations...
COMMIT AND CHAIN  ──► BEGIN T3 (automatic)
    operations...
COMMIT
```

### Chained Transaction Flow

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│   T1   │────►│   T2   │────►│   T3   │────►│   T4   │
│        │     │        │     │        │     │        │
│ ops... │     │ ops... │     │ ops... │     │ ops... │
└────────┘     └────────┘     └────────┘     └────────┘
    │              │              │              │
 COMMIT         COMMIT         COMMIT         COMMIT
 & CHAIN        & CHAIN        & CHAIN           │
    │              │              │              ▼
    ▼              ▼              ▼           (ends)
 T1 durable    T2 durable    T3 durable    T4 durable
```

### Benefits Over Flat Transactions

1. **Reduced lock holding time**: Locks released at each commit point
2. **Incremental durability**: Work persisted at each chain point
3. **Better resource utilization**: Shorter transactions = less contention

### Chained Transaction Example

```sql
-- Processing a large batch in chunks
BEGIN TRANSACTION;
    -- Process first 1000 records
    UPDATE orders SET status = 'processed'
    WHERE id BETWEEN 1 AND 1000;
COMMIT AND CHAIN;
    -- First 1000 are now durable, locks released

    -- Process next 1000 records
    UPDATE orders SET status = 'processed'
    WHERE id BETWEEN 1001 AND 2000;
COMMIT AND CHAIN;
    -- Second batch durable

    -- Continue...
COMMIT;
```

