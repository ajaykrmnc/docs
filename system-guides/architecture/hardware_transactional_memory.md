# Hardware Transactional Memory for System Programmers

## Introduction

Hardware Transactional Memory (HTM) provides atomic execution of code blocks without explicit locks, using hardware support to detect and resolve conflicts. This document covers HTM fundamentals, Intel TSX implementation, and practical programming considerations.

**Key Learning Objectives:**
- Understand transactional memory concepts (atomicity, isolation)
- Learn Intel TSX (HLE and RTM)
- Understand conflict detection and resolution
- Recognize HTM limitations and fallback strategies
- Write efficient transactional code

## 1. Transactional Memory Fundamentals

### 1.1 The Lock Problem

**Traditional lock-based synchronization:**
```c
pthread_mutex_lock(&mutex);
// Critical section
balance += amount;
pthread_mutex_unlock(&mutex);
```

**Problems:**
- **Coarse-grained locks**: Poor parallelism (serialize all operations)
- **Fine-grained locks**: Complex, deadlock-prone, high overhead
- **Priority inversion**: Low-priority thread holds lock
- **Convoying**: Threads queue behind lock holder

### 1.2 Transactional Memory Concept

**Idea**: Execute critical sections as atomic transactions.

```c
transaction {
    // Atomic block - all or nothing
    balance += amount;
    count++;
}
```

**ACID properties (from databases):**
- **Atomicity**: All operations succeed or all fail
- **Consistency**: Valid state before and after
- **Isolation**: No interference from other transactions
- **Durability**: Not applicable to TM (volatile memory)

### 1.3 TM vs. Locks

| Aspect | Locks | Transactional Memory |
|--------|-------|---------------------|
| Composition | Difficult (deadlock) | Easy (nest transactions) |
| Granularity | Manual (coarse/fine trade-off) | Automatic (hardware tracks) |
| Priority inversion | Possible | No |
| Performance | Predictable overhead | Variable (conflicts cause retries) |
| Debugging | Familiar | New challenges |

## 2. Hardware Transactional Memory (HTM)

### 2.1 How HTM Works

**Basic mechanism:**
```
1. Begin transaction
2. Execute speculatively (buffer writes, track reads)
3. Detect conflicts with other transactions
4. Commit (if no conflicts) or Abort (if conflicts)
```

**Buffering writes:**
```
Transaction:           L1 Cache:              Memory:
x = 1;       →     [x=1, speculative]    [x=0, old value]
y = 2;       →     [y=2, speculative]    [y=0, old value]

Commit:            Flush to memory →     [x=1, y=2]
Abort:             Discard changes →     [x=0, y=0]
```

**Tracking reads (read-set):**
```
Read-set = {addresses read during transaction}
If another thread writes to read-set → CONFLICT → ABORT
```

**Tracking writes (write-set):**
```
Write-set = {addresses written during transaction}
If another thread reads/writes write-set → CONFLICT → ABORT
```

### 2.2 Conflict Detection

**Example: Bank transfer**

```c
// Thread 1                   // Thread 2
transaction {                 transaction {
    int a = account[0];           int b = account[1];
    int b = account[1];           int c = account[2];
    account[0] = a - 100;         account[1] = b - 50;
    account[1] = b + 100;         account[2] = c + 50;
}                             }
```

**Conflict analysis:**
```
Thread 1 read-set:  {account[0], account[1]}
Thread 1 write-set: {account[0], account[1]}

Thread 2 read-set:  {account[1], account[2]}
Thread 2 write-set: {account[1], account[2]}

Conflict: Both access account[1]!
Resolution: One transaction aborts and retries
```

### 2.3 Eager vs. Lazy Versioning

**Eager (direct update):**
```
Write immediately to cache, keep old values in undo log
Commit: Discard undo log (fast)
Abort: Restore from undo log (slow)
```

**Lazy (buffered update):**
```
Buffer writes separately, don't modify cache
Commit: Apply buffered writes (slow)
Abort: Discard buffer (fast)
```

**Most HTM**: Use lazy (optimistic: assume success).

## 3. Intel TSX (Transactional Synchronization Extensions)

### 3.1 TSX Overview

**Two interfaces:**
1. **HLE (Hardware Lock Elision)**: Hint to existing lock code
2. **RTM (Restricted Transactional Memory)**: Explicit transactions

**Availability:**
- Intel Haswell (2013) - Skylake (disabled due to bugs)
- Ice Lake (2019+): Re-enabled with fixes
- AMD Zen 4 (2022+): Not supported

### 3.2 HLE (Hardware Lock Elision)

**Concept**: Add hints to lock prefix to try transactional execution.

**Example:**
```c
// Traditional locked increment
lock:
    __asm__ __volatile__(
        "lock; incl %0"
        : "+m" (counter)
    );

// HLE version
lock_hle:
    __asm__ __volatile__(
        "xacquire; lock; incl %0"  // Try transaction
        : "+m" (counter)
    );
// If transaction succeeds: no actual lock acquired!
// If transaction fails: fall back to normal lock
```

**XACQUIRE**: Start transaction at lock acquisition
**XRELEASE**: Commit transaction at lock release

**Full example:**
```c
void increment_hle(int *counter, int *lock) {
    // Acquire with HLE
    while (!__atomic_test_and_set(lock, __ATOMIC_ACQUIRE)) {
        __asm__ __volatile__("pause");
    }
    
    (*counter)++;
    
    // Release with HLE
    __asm__ __volatile__(
        "xrelease; movl $0, %0"
        : "=m" (*lock)
    );
}
```

**Benefit**: Drop-in optimization for existing lock code.

### 3.3 RTM (Restricted Transactional Memory)

**Explicit transaction control:**

**Instructions:**
- `XBEGIN`: Start transaction
- `XEND`: Commit transaction
- `XABORT`: Explicitly abort
- `XTEST`: Test if in transaction

**Example:**
```c
#include <immintrin.h>

void transfer(int *accounts, int from, int to, int amount) {
    unsigned status;
    
    // Try transaction
    if ((status = _xbegin()) == _XBEGIN_STARTED) {
        // Transaction started successfully
        accounts[from] -= amount;
        accounts[to] += amount;
        _xend();  // Commit
    } else {
        // Transaction failed, use fallback (lock)
        pthread_mutex_lock(&fallback_lock);
        accounts[from] -= amount;
        accounts[to] += amount;
        pthread_mutex_unlock(&fallback_lock);
    }
}
```

**Status codes:**
```
_XBEGIN_STARTED (0xFFFFFFFF): Transaction started
_XABORT_EXPLICIT: Explicit XABORT
_XABORT_RETRY: May succeed if retried
_XABORT_CONFLICT: Data conflict
_XABORT_CAPACITY: Transaction too large
_XABORT_DEBUG: Debug trap occurred
_XABORT_NESTED: Nested transaction abort
```

### 3.4 TSX Limitations

**Capacity limitations:**
- Read-set: ~L1 cache size (~32-64 KB)
- Write-set: ~L1 cache size (~32-64 KB)
- Exceeding capacity → abort

**Abort triggers:**
- Data conflicts
- Capacity overflow
- System calls
- Interrupts / exceptions
- Certain instructions (CPUID, IO, etc.)
- Page faults
- Context switch

**No forward progress guarantee**: Transaction may never succeed!

## 4. Programming with HTM

### 4.1 Basic Transaction Pattern

```c
#define MAX_RETRIES 3

int transactional_operation() {
    int retries = 0;
    
    while (retries < MAX_RETRIES) {
        unsigned status = _xbegin();
        
        if (status == _XBEGIN_STARTED) {
            // Transactional code
            do_work();
            _xend();
            return SUCCESS;
        }
        
        // Transaction aborted
        if (!(status & _XABORT_RETRY)) {
            break;  // No point retrying
        }
        retries++;
    }
    
    // Fallback path (use locks)
    pthread_mutex_lock(&lock);
    do_work();
    pthread_mutex_unlock(&lock);
    return SUCCESS;
}
```

### 4.2 Reducing Aborts

**1. Keep transactions small:**
```c
// Bad: Large transaction
_xbegin();
process_array(large_array);  // May exceed capacity
_xend();

// Good: Small transactions
for (int i = 0; i < n; i++) {
    _xbegin();
    process_element(&array[i]);
    _xend();
}
```

**2. Avoid I/O and system calls:**
```c
// Bad
_xbegin();
data = compute();
printf("%d\n", data);  // Aborts transaction!
_xend();

// Good
_xbegin();
data = compute();
_xend();
printf("%d\n", data);  // Outside transaction
```

**3. Minimize contention:**
```c
// Bad: Hotspot on shared variable
_xbegin();
global_counter++;  // High contention
process_data();
_xend();

// Good: Local accumulation
local_sum += value;
// Later (outside hot path):
_xbegin();
global_counter += local_sum;
_xend();
```

### 4.3 Hybrid Lock/Transaction Approach

```c
typedef struct {
    int lock;
    int data;
} protected_t;

void update(protected_t *obj, int value) {
    int retries = 0;
    
    while (retries < 3) {
        unsigned status = _xbegin();
        
        if (status == _XBEGIN_STARTED) {
            // Transactional path
            if (obj->lock) {
                _xabort(0);  // Lock held, abort
            }
            obj->data = value;
            _xend();
            return;
        }
        retries++;
    }
    
    // Fallback: Acquire lock
    while (__sync_lock_test_and_set(&obj->lock, 1)) {
        _mm_pause();
    }
    obj->data = value;
    __sync_lock_release(&obj->lock);
}
```

## 5. Performance Characteristics

### 5.1 Best Case (No Conflicts)

```
Lock-based:     ~50-100 cycles (uncontended lock)
HTM:            ~20-30 cycles (successful transaction)
Speedup:        2-3×
```

### 5.2 Worst Case (High Contention)

```
Lock-based:     Queuing, but forward progress guaranteed
HTM:            Repeated aborts, may livelock
Fallback:       Required!
```

### 5.3 Abort Rate vs Performance

```
Abort rate:  Performance:
0-10%        Excellent (2-4× speedup)
10-30%       Good (1.5-2× speedup)
30-50%       Marginal (1-1.5× speedup)
>50%         Poor (slower than locks)
```

## 6. Real-World Examples

### 6.1 Concurrent Hash Table

```c
typedef struct {
    int key;
    int value;
} entry_t;

entry_t table[TABLE_SIZE];

int lookup(int key) {
    unsigned status = _xbegin();
    if (status == _XBEGIN_STARTED) {
        int idx = hash(key);
        int val = table[idx].value;
        _xend();
        return val;
    }
    // Fallback
    return locked_lookup(key);
}

void insert(int key, int value) {
    // Similar pattern
}
```

**Benefit**: No lock overhead for common case (reads).

### 6.2 Red-Black Tree

```c
void rb_insert(rb_tree_t *tree, int key) {
    if (_xbegin() == _XBEGIN_STARTED) {
        rb_insert_internal(tree, key);  // Complex rotations
        _xend();
    } else {
        pthread_mutex_lock(&tree->lock);
        rb_insert_internal(tree, key);
        pthread_mutex_unlock(&tree->lock);
    }
}
```

**Challenge**: Tree rotation may touch many nodes (capacity risk).

## 7. Summary

**Key Takeaways:**
- HTM provides lock-free atomicity using hardware
- Intel TSX offers HLE (implicit) and RTM (explicit)
- Transactions can abort due to conflicts, capacity, or interrupts
- Always provide lock-based fallback
- Best for low-contention, small critical sections

**When to use HTM:**
- ✅ Low-contention scenarios
- ✅ Small transactions (< 32 KB)
- ✅ No I/O or system calls
- ❌ High contention (use locks)
- ❌ Large data structures
- ❌ Real-time requirements (unpredictable aborts)

---

*Last updated: 2026-04-11*
