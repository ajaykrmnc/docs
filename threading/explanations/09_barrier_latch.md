# Problem 9: Barrier and CountDownLatch

## 🎯 Problem Statement
Implement synchronization primitives:
1. **Barrier**: N threads wait until all N reach the barrier
2. **CountDownLatch**: Threads wait until count reaches zero

## 🏢 Companies
**Databricks** (parallel data processing), **Rubrik** (distributed backup)

## 🔑 Core Principles

### 1. Barrier Concept

```
BARRIER: All must arrive before any can proceed

Thread 1: ════════●════════════════════►
Thread 2: ═══════════●═════════════════►
Thread 3: ═════●═══════════════════════►
Thread 4: ════════════════●════════════►
                          │
                       BARRIER
                    (all arrive)
                          │
                          ▼
             All proceed simultaneously
```

### 2. CountDownLatch Concept

```
LATCH: Wait for N events to occur

Main Thread: ═════════════════════●════►
                                  │
                        latch.await()
                                  │
Worker 1: ═══●──count_down()      │
Worker 2: ═════●──count_down()    │
Worker 3: ═══════●──count_down()  │
                       │          │
                 count reaches 0──┘
                       │
                       ▼
               Main proceeds
```

### 3. Barrier vs Latch

| Feature | Barrier | CountDownLatch |
|---------|---------|----------------|
| **Reusable** | ✅ Yes (cyclic) | ❌ One-shot |
| **Who waits** | All participants | Subset waits |
| **Who signals** | All participants | Anyone can count down |
| **Use case** | Phased computation | Wait for initialization |

### 4. Barrier Implementation

```python
class Barrier:
    def __init__(self, parties):
        self.parties = parties
        self.count = parties
        self.generation = 0  # For reuse detection
        self.condition = Condition()
    
    def wait(self):
        with self.condition:
            gen = self.generation
            self.count -= 1
            
            if self.count == 0:
                # Last to arrive - reset and wake all
                self.count = self.parties
                self.generation += 1
                self.condition.notify_all()
            else:
                # Wait for others
                while gen == self.generation:
                    self.condition.wait()
```

### 5. Latch Implementation

```python
class CountDownLatch:
    def __init__(self, count):
        self.count = count
        self.condition = Condition()
    
    def count_down(self):
        with self.condition:
            if self.count > 0:
                self.count -= 1
                if self.count == 0:
                    self.condition.notify_all()
    
    def await(self):
        with self.condition:
            while self.count > 0:
                self.condition.wait()
```

## 📊 Use Cases

### Barrier: Parallel Algorithm Phases
```
PHASE 1: All workers compute partial results
    ║
 BARRIER  ← Everyone must finish Phase 1
    ║
PHASE 2: All workers exchange data
    ║
 BARRIER  ← Everyone must finish Phase 2
    ║
PHASE 3: All workers compute final result
```

### Latch: Service Initialization
```
Main Thread                    Services
     │                            │
     │ wait for services ────────►│ DB initializing...
     │                            │ Cache initializing...
     │                            │ Queue initializing...
     │◄───────────────────────────│ All ready!
     │ proceed with app           │
```

### Latch: Test Synchronization
```
Test Thread                   Worker Threads
     │                              │
     │ create workers               │
     │ startLatch.await() ─────────►│ all start together
     │                              │ (fair timing test)
     │ doneLatch.await() ◄─────────│ all finish
     │ verify results               │
```

## 🧠 Key Insights

### Why Generation Counter in Barrier?
```
WITHOUT generation (BUG):
Thread 1: wait() → wakes up → loops back → wait()
                                    ↓
              Sees count reset, immediately passes! ❌

WITH generation:
Thread 1: wait() → wakes up → checks generation changed → passes ✓
                              (gen 0 ≠ gen 1)
```

### C++20 Barrier with Completion Function
```cpp
std::barrier sync_point(3, []() noexcept {
    // Called by LAST arriving thread
    // Use for: cleanup, aggregation, phase transition
    std::cout << "Phase complete!" << std::endl;
});
```

## 💻 C++20 Standard Library

```cpp
#include <barrier>
#include <latch>

// Barrier (reusable)
std::barrier sync_point(num_threads);
sync_point.arrive_and_wait();

// Latch (one-shot)
std::latch done(num_tasks);
done.count_down();
done.wait();
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Reusing latch | Undefined behavior | Use barrier or create new latch |
| Wrong party count | Hang forever | Match exact participant count |
| Exception in barrier | Others hang | Use try-catch, signal failure |
| No generation tracking | Spurious passes | Track generation/epoch |

## 📝 Interview Tips

1. **Know the difference** - Barrier reusable, Latch one-shot
2. **Explain generation counter** - Shows deep understanding
3. **Mention C++20** - `std::barrier`, `std::latch`
4. **Real examples**: MapReduce sync, game engine frames

