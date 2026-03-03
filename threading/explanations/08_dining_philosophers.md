# Problem 8: Dining Philosophers

## 🎯 Problem Statement
Five philosophers sit at a round table with five forks. Each needs TWO forks (left and right) to eat. Implement a solution that prevents deadlock and starvation.

## 🏢 Companies
**Databricks, Rubrik, Glean** - Classic concurrency problem!

## 🔑 Core Principles

### 1. The Problem Setup

```
           [P0]
        F0      F4
      [P1]      [P4]
        F1      F3
           [P2]
             F2
           [P3]

Each philosopher needs:
- Left fork: Fork[i]
- Right fork: Fork[(i+1) % 5]
```

### 2. The Deadlock Scenario

```
TIME →
P0: Lock(F0) ✓ → Lock(F4) ⏳ waiting...
P1: Lock(F1) ✓ → Lock(F0) ⏳ waiting...
P2: Lock(F2) ✓ → Lock(F1) ⏳ waiting...
P3: Lock(F3) ✓ → Lock(F2) ⏳ waiting...
P4: Lock(F4) ✓ → Lock(F3) ⏳ waiting...

     ┌──────────────────────────┐
     │    CIRCULAR DEADLOCK!    │
     │                          │
     │   P0 → P4 → P3 → P2 →   │
     │   ↑                 ↓    │
     │   └──── P1 ←────────┘    │
     └──────────────────────────┘
```

### 3. Solution 1: Resource Hierarchy (Lock Ordering)

```
RULE: Always pick up lower-numbered fork first!

P0: Lock(F0) → Lock(F4)     [0 < 4] ✓
P1: Lock(F0) → Lock(F1)     [0 < 1] ✓  (NOT F1 → F0!)
P2: Lock(F1) → Lock(F2)     [1 < 2] ✓
P3: Lock(F2) → Lock(F3)     [2 < 3] ✓
P4: Lock(F3) → Lock(F4)     [3 < 4] ✓

Now P4 tries F3 first, breaking the cycle!

WHY IT WORKS:
- No circular dependency possible
- At least one philosopher gets both forks
- Breaks Coffman's "Circular Wait" condition
```

### 4. Solution 2: Arbitrator (Waiter)

```
┌─────────────────────────────────────────┐
│                WAITER                    │
│         (Semaphore with N-1)            │
│                                          │
│  Only 4 philosophers can TRY at once    │
│  → Guarantees at least 1 gets both!     │
│                                          │
│  P0: waiter.acquire() ✓ → try eating    │
│  P1: waiter.acquire() ✓ → try eating    │
│  P2: waiter.acquire() ✓ → try eating    │
│  P3: waiter.acquire() ✓ → try eating    │
│  P4: waiter.acquire() ⏳ waiting...     │
└─────────────────────────────────────────┘
```

### 5. Solution 3: Try-Lock with Backoff

```python
def eat():
    while True:
        if left_fork.try_lock():
            if right_fork.try_lock():
                # Got both! Eat!
                EAT()
                right_fork.unlock()
                left_fork.unlock()
                return
            else:
                # Can't get right, release left
                left_fork.unlock()
        
        # Random backoff to avoid livelock
        sleep(random(0.01, 0.1))
```

## 📊 Solution Comparison

| Solution | Deadlock-Free | Starvation-Free | Simplicity | Concurrency |
|----------|---------------|-----------------|------------|-------------|
| Resource Ordering | ✅ | ❌* | Simple | High |
| Arbitrator | ✅ | ✅ | Simple | Medium (N-1) |
| Try-Lock | ✅ | ❌** | Medium | High |
| Chandy-Misra | ✅ | ✅ | Complex | High |

*Ordering can have starvation in pathological cases
**Livelock possible without proper backoff

## 🧠 Key Insights

### Why N-1 in Arbitrator?
```
5 philosophers, 5 forks
If 5 try simultaneously → Each gets 1 fork → Deadlock
If 4 try simultaneously → 5 forks / 4 people → At least 1 gets 2!
```

### Why Random Backoff?
```
WITHOUT backoff (Livelock):
P0: lock(A) → fail(B) → unlock(A) → lock(A) → fail(B) → ...
P1: lock(B) → fail(A) → unlock(B) → lock(B) → fail(A) → ...
    [Repeats forever, no progress!]

WITH random backoff:
P0: lock(A) → fail(B) → unlock(A) → sleep(50ms)
P1: lock(B) → fail(A) → unlock(B) → sleep(30ms) → lock(B) → lock(A) ✓
    [P1 succeeds during P0's longer wait]
```

## 💻 C++17 Solution (Simplest)

```cpp
void philosopher(int id) {
    auto& left = forks[id];
    auto& right = forks[(id + 1) % 5];
    
    // std::scoped_lock handles ordering automatically!
    std::scoped_lock lock(left, right);
    eat();
}
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Lock ordering inconsistent | Deadlock | Sort by fork ID |
| No backoff in try-lock | Livelock | Add random delay |
| Releasing forks out of order | Potential issues | RAII / reverse order |
| Ignoring starvation | Some never eat | Use fair scheduling |

