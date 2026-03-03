# Problem 1: Producer-Consumer Problem

## 🎯 Problem Statement
Implement a thread-safe bounded buffer where multiple producer threads add items and multiple consumer threads remove items. The buffer has a fixed capacity. Producers must wait when buffer is full, consumers must wait when buffer is empty.

## 🏢 Companies
**Databricks, Rubrik, Glean** - This is a CLASSIC interview question!

## 🔑 Core Principles

### 1. Mutual Exclusion
Only one thread can modify the buffer at a time. We use a **mutex/lock** to ensure this.

```
Thread 1: [LOCK] → modify buffer → [UNLOCK]
Thread 2: ----waiting---- → [LOCK] → modify buffer → [UNLOCK]
```

### 2. Condition Variables
Threads need to **wait for specific conditions**:
- **Producers wait** when buffer is FULL
- **Consumers wait** when buffer is EMPTY

**Why not busy-wait (spinning)?**
```
# BAD: Wastes CPU cycles
while buffer_is_full():
    pass  # Spinning!

# GOOD: Releases CPU while waiting
condition.wait()  # Sleeps until notified
```

### 3. The Wait Pattern
```python
with condition:
    while not condition_is_true():  # Use WHILE, not IF!
        condition.wait()
    # Do work
    condition.notify()
```

**Why `while` instead of `if`?**
- **Spurious wakeups**: Thread can wake without being notified
- **Multiple waiters**: Another thread might act first after notification

### 4. Notify vs Notify_All
| Method | Behavior | Use When |
|--------|----------|----------|
| `notify()` | Wakes ONE waiting thread | One waiter can proceed |
| `notify_all()` | Wakes ALL waiting threads | Multiple might proceed, or condition varies |

## 📊 Visual Representation

```
BOUNDED BUFFER (capacity=3)
┌─────────────────────────────┐
│  [Item1] [Item2] [  ]       │  ← 2 items, space for 1 more
└─────────────────────────────┘
     ↑                    ↑
  Consumer             Producer
  removes              adds here
  from here

STATE TRANSITIONS:
┌────────┐  put()   ┌────────┐  put()   ┌────────┐
│ EMPTY  │ ───────→ │ PARTIAL │ ───────→ │  FULL  │
└────────┘          └────────┘          └────────┘
     ↑                   ↑                   │
     │      get()        │      get()        │
     └───────────────────┴───────────────────┘
```

## 🧠 Key Insights for Interviews

1. **Always use `while` for condition checks** - handles spurious wakeups
2. **Two conditions needed**: `not_full` and `not_empty`
3. **Lock must be held when calling wait()** - it's released automatically during wait
4. **Bounded buffer prevents OOM** - unbounded queues can exhaust memory

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using `if` instead of `while` | Spurious wakeup bugs | Always use `while` |
| Single condition variable | Can't distinguish full vs empty | Use two conditions |
| Not notifying after state change | Threads wait forever | Always notify after modification |
| Unbounded buffer | Memory exhaustion | Use bounded capacity |

## 🔗 Related Patterns
- Blocking Queue
- Message Queue
- Thread Pool Task Queue
- Pipeline Pattern

## 📝 Complexity
- **Time**: O(1) for put/get operations
- **Space**: O(capacity) for buffer storage

