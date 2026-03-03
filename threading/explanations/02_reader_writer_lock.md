# Problem 2: Reader-Writer Lock

## 🎯 Problem Statement
Implement a read-write lock that allows:
- Multiple readers to access shared resource simultaneously
- Only one writer at a time with exclusive access
- No readers while a writer is writing

## 🏢 Companies
**Rubrik** (storage systems), **Glean** (search indexing), **Databricks** (data processing)

## 🔑 Core Principles

### 1. Shared vs Exclusive Access
```
SHARED (Read) Lock:     EXCLUSIVE (Write) Lock:
┌─────────────────┐     ┌─────────────────┐
│ Reader 1 ──────→│     │                 │
│ Reader 2 ──────→│     │ Writer ────────→│
│ Reader 3 ──────→│     │                 │
└─────────────────┘     └─────────────────┘
   All can read            Only one writes
   simultaneously          No readers allowed
```

### 2. Lock Compatibility Matrix
|  | Read Lock Held | Write Lock Held |
|--|----------------|-----------------|
| **Read Request** | ✅ Granted | ❌ Wait |
| **Write Request** | ❌ Wait | ❌ Wait |

### 3. Reader Preference vs Writer Preference

**Reader Preference** (simple, can starve writers):
```
Readers keep arriving → Writers never get access
R1 → R2 → R3 → R4 → ...  [Writer waiting forever]
```

**Writer Preference** (prevents writer starvation):
```
When writer waiting → New readers must wait too
R1 → R2 → [W1 waiting] → R3 waits → W1 executes → R3 executes
```

**Fair (FIFO)** (no starvation):
```
Requests served in order of arrival
R1 → W1 → R2 → R3 → W2 (served in this order)
```

### 4. Implementation Strategy
```
READER ENTERS:
1. Lock reader_mutex
2. Increment reader_count
3. If first reader → acquire write_lock (block writers)
4. Unlock reader_mutex
5. READ DATA

READER EXITS:
1. Lock reader_mutex
2. Decrement reader_count
3. If last reader → release write_lock (allow writers)
4. Unlock reader_mutex

WRITER ENTERS:
1. Acquire write_lock (exclusive)
2. WRITE DATA
3. Release write_lock
```

## 📊 Visual Representation

```
TIME →
        t1    t2    t3    t4    t5    t6    t7
Reader1 [====READ====]
Reader2       [====READ====]
Reader3             [====READ====]
Writer1                         [==WRITE==]
Reader4                                   [===READ===]

│←─ Multiple readers OK ─→│←─ Writer exclusive ─→│
```

## 🧠 Key Insights for Interviews

1. **First reader blocks writers** - acquires write lock
2. **Last reader unblocks writers** - releases write lock
3. **Writer starvation is real** - continuous readers block writers forever
4. **Use order lock for fairness** - additional mutex to ensure FIFO

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No writer starvation prevention | Writers wait forever | Add order_lock or writer preference |
| Forgetting to release locks | Deadlock | Use RAII/context managers |
| Not tracking reader count atomically | Race conditions | Protect count with mutex |

## 🔧 C++ Standard Library
```cpp
std::shared_mutex mutex;

// Reader
std::shared_lock<std::shared_mutex> lock(mutex);  // Multiple OK

// Writer  
std::unique_lock<std::shared_mutex> lock(mutex);  // Exclusive
```

## 🐍 Python
```python
# Python doesn't have built-in RW lock
# Use custom implementation or third-party library
```

## 📈 Performance Comparison
| Scenario | Regular Mutex | RW Lock |
|----------|---------------|---------|
| 90% reads, 10% writes | Slow (serialized) | Fast (parallel reads) |
| 50% reads, 50% writes | OK | Similar or worse (overhead) |
| 10% reads, 90% writes | OK | Worse (RW lock overhead) |

**Use RW Lock when**: Read-heavy workloads (>70% reads)

