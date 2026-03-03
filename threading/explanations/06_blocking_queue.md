# Problem 6: Blocking Queue Implementation

## 🎯 Problem Statement
Implement a thread-safe blocking queue with:
- `put(item)` - blocks if queue is full
- `get()` - blocks if queue is empty
- `put_nowait(item)` - raises exception if full
- `get_nowait()` - raises exception if empty

## 🏢 Companies
**Rubrik, Databricks** - Core data structure for pipeline processing

## 🔑 Core Principles

### 1. Blocking vs Non-Blocking Operations

```
BLOCKING:                     NON-BLOCKING:
┌─────────────────────┐       ┌─────────────────────┐
│ put(item)           │       │ try_put(item)       │
│   if full:          │       │   if full:          │
│     WAIT ⏳         │       │     return FALSE ❌  │
│   else:             │       │   else:             │
│     add item ✓      │       │     add item ✓      │
└─────────────────────┘       └─────────────────────┘

Use blocking when:            Use non-blocking when:
- Can't proceed without       - Have alternative work
- OK to wait                  - Need to check conditions
```

### 2. Queue States and Transitions

```
EMPTY STATE:          PARTIAL STATE:         FULL STATE:
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ [   ] [   ]   │     │ [A] [B] [   ] │     │ [A] [B] [C]   │
│               │     │               │     │               │
│ get() BLOCKS  │     │ get() OK      │     │ get() OK      │
│ put() OK      │     │ put() OK      │     │ put() BLOCKS  │
└───────────────┘     └───────────────┘     └───────────────┘
        ↑                    ↑  ↓                   ↓
        │      put()         │  │      put()        │
        └────────────────────┘  └───────────────────┘
                   get()               get()
```

### 3. Condition Variables Pattern

```python
class BlockingQueue:
    def __init__(self, capacity):
        self.queue = []
        self.capacity = capacity
        self.lock = Lock()
        self.not_empty = Condition(self.lock)  # Signal when items added
        self.not_full = Condition(self.lock)   # Signal when items removed
    
    def put(self, item):
        with self.not_full:                    # Acquire lock
            while len(self.queue) >= self.capacity:
                self.not_full.wait()           # Release lock & wait
            self.queue.append(item)
            self.not_empty.notify()            # Wake consumer
    
    def get(self):
        with self.not_empty:                   # Acquire lock
            while len(self.queue) == 0:
                self.not_empty.wait()          # Release lock & wait
            item = self.queue.pop(0)
            self.not_full.notify()             # Wake producer
            return item
```

### 4. Timeout Handling

```
WITHOUT TIMEOUT:             WITH TIMEOUT:
┌─────────────────────┐     ┌─────────────────────┐
│ get()               │     │ get(timeout=5s)     │
│   if empty:         │     │   start = now()     │
│     wait() FOREVER  │     │   while empty:      │
│                     │     │     remaining =     │
│                     │     │       timeout -     │
│                     │     │       (now()-start) │
│                     │     │     if remaining<=0:│
│                     │     │       raise Timeout │
│                     │     │     wait(remaining) │
└─────────────────────┘     └─────────────────────┘
```

## 📊 Visual: Put and Get Operations

```
PUT OPERATION:
                    Queue: [A][B][_]  (size=2, cap=3)
                              │
Producer ──put(C)──→         [A][B][C]  (size=3, cap=3)
                              │
                    notify(not_empty) → wake consumers

GET OPERATION:
                    Queue: [A][B][C]  (size=3, cap=3)
                              │
Consumer ──get()───→         [B][C][_]  (size=2, cap=3)
    │                         │
    └─returns A      notify(not_full) → wake producers
```

## 🧠 Key Insights

### Why Two Conditions?
```
WRONG: Single condition
  - put() notifies, but another producer wakes up → WRONG!
  
RIGHT: Two conditions
  - not_full: Producers wait here, consumers signal here
  - not_empty: Consumers wait here, producers signal here
```

### Notify vs Notify_All
| Scenario | Use |
|----------|-----|
| One waiter can proceed | `notify()` (efficient) |
| Multiple might proceed | `notify_all()` |
| Broadcast state change | `notify_all()` |

## 💻 Implementation Variants

### FIFO Queue (Standard)
```cpp
std::queue<T> buffer;  // First in, first out
```

### Priority Queue
```cpp
std::priority_queue<T> buffer;  // Highest priority first
```

### LIFO Stack
```cpp
std::stack<T> buffer;  // Last in, first out
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using `if` instead of `while` | Spurious wakeup bugs | Always `while` |
| Signaling outside lock | Race condition | Signal inside lock |
| No timeout option | Potential deadlock | Implement timeout |
| Unbounded capacity | Memory exhaustion | Set reasonable max |

## 📝 Time Complexity
| Operation | Average | Worst |
|-----------|---------|-------|
| put() | O(1) | O(wait time) |
| get() | O(1) | O(wait time) |
| size() | O(1) | O(1) |

