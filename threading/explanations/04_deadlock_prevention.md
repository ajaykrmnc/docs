# Problem 4: Deadlock Detection and Prevention

## 🎯 Problem Statement
Given a system where multiple threads acquire multiple locks, implement mechanisms to detect and prevent deadlocks.

## 🏢 Companies
**Rubrik** (distributed storage), **Databricks** (distributed computing) - CRITICAL topic!

## 🔑 Core Principles

### 1. Coffman Conditions (All 4 Required for Deadlock)

```
┌─────────────────────────────────────────────────────────────┐
│  1. MUTUAL EXCLUSION                                        │
│     Resource can only be held by one thread                 │
│                                                             │
│  2. HOLD AND WAIT                                           │
│     Thread holds resources while waiting for others         │
│                                                             │
│  3. NO PREEMPTION                                           │
│     Resources cannot be forcibly taken away                 │
│                                                             │
│  4. CIRCULAR WAIT                                           │
│     Circular chain of threads waiting for each other        │
└─────────────────────────────────────────────────────────────┘

Break ANY ONE condition → No deadlock possible!
```

### 2. Classic Deadlock Scenario
```
Thread 1                    Thread 2
   │                           │
   ▼                           ▼
Lock(A) ✓                   Lock(B) ✓
   │                           │
   ▼                           ▼
Lock(B) ⏳ waiting          Lock(A) ⏳ waiting
   │                           │
   └───────── DEADLOCK! ───────┘
```

### 3. Prevention Strategies

#### Strategy 1: Lock Ordering (Break Circular Wait)
```
RULE: Always acquire locks in consistent order (by ID, address, etc.)

Thread 1: Lock(A) → Lock(B)    ✓
Thread 2: Lock(A) → Lock(B)    ✓ (NOT Lock(B) → Lock(A))

Result: No circular dependency possible!
```

#### Strategy 2: Try-Lock with Timeout (Break Hold and Wait)
```
while True:
    if try_lock(A, timeout=1s):
        if try_lock(B, timeout=1s):
            # Got both! Do work
            break
        else:
            unlock(A)  # Release and retry
    sleep(random_backoff)
```

#### Strategy 3: Acquire All at Once (Break Hold and Wait)
```cpp
// C++17 std::scoped_lock
std::scoped_lock lock(mutex_a, mutex_b, mutex_c);
// Acquires all atomically, no deadlock possible!
```

#### Strategy 4: Resource Hierarchy (Break Circular Wait)
```
Assign levels to resources:
  Level 1: Database connections
  Level 2: File handles  
  Level 3: Network sockets

Rule: Only acquire resources at HIGHER levels than currently held
```

## 📊 Visual: Lock Ordering Solution

```
WITHOUT ORDERING (Deadlock possible):
  T1: A ──→ B
        ╲  ╱
         ╳    ← Circular dependency!
        ╱  ╲
  T2: B ──→ A

WITH ORDERING (No deadlock):
  T1: A ──→ B
            │
  T2: A ──→ B
  
  Both try A first → One waits → No cycle!
```

## 🧠 Detection vs Prevention

| Approach | When | How |
|----------|------|-----|
| **Prevention** | Design time | Lock ordering, timeouts |
| **Avoidance** | Runtime | Banker's algorithm (check before grant) |
| **Detection** | Runtime | Build wait-for graph, find cycles |
| **Recovery** | After deadlock | Kill process, rollback transaction |

## 💻 Code Patterns

### C++17 (Best: std::scoped_lock)
```cpp
std::scoped_lock lock(mutex1, mutex2, mutex3);
// Automatically handles ordering, no deadlock!
```

### C++11 (std::lock)
```cpp
std::lock(mutex1, mutex2);  // Deadlock-free
std::lock_guard<std::mutex> lg1(mutex1, std::adopt_lock);
std::lock_guard<std::mutex> lg2(mutex2, std::adopt_lock);
```

### Python (Lock Ordering)
```python
def acquire_ordered(*locks):
    for lock in sorted(locks, key=id):
        lock.acquire()
```

## ⚠️ Common Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Inconsistent lock order | Deadlock | Establish global ordering |
| Holding lock while calling unknown code | Potential deadlock | Release before callback |
| Nested lock acquisition | Complex ordering | Flatten or use hierarchy |
| Ignoring try_lock failures | Potential deadlock | Always handle timeout |

## 🎓 Interview Tips

1. **Always mention Coffman conditions** - shows theoretical knowledge
2. **Prefer `std::scoped_lock`** in C++17+ interviews
3. **Lock ordering is the most common solution**
4. **Discuss trade-offs**: Prevention is simpler but less flexible

