# Problem 13: Building H2O (LeetCode 1117)

## 🎯 Problem Statement
Multiple threads call `hydrogen()` and `oxygen()`. Ensure they proceed in groups of 2 hydrogen + 1 oxygen to form H₂O molecules.

## 🏢 Companies
**Databricks** - Tests resource grouping and synchronization

## 🔑 Core Principles

### 1. The Grouping Problem

```
INCOMING THREADS:        REQUIRED OUTPUT:
H H O H O H H O H O     Groups of (H, H, O):
│ │ │ │ │ │ │ │ │ │        H─┐
│ │ │ │ │ │ │ │ │ │        H─┼─O → H₂O
│ │ │ │ │ │ │ │ │ │           │
└─┴─┴─┴─┴─┴─┴─┴─┴─┘           │
                            H─┐
Random arrival              H─┼─O → H₂O
                               ...
```

### 2. Synchronization Strategy

```
┌───────────────────────────────────────────────────┐
│              H₂O MOLECULE BARRIER                  │
│                                                    │
│   H Semaphore ─────┐                              │
│   (permits: 2)     │      ┌─────────────┐         │
│                    ├────► │   BARRIER   │ ◄──┐    │
│   O Semaphore ─────┘      │  (parties=3)│    │    │
│   (permits: 1)            └─────────────┘    │    │
│                                  │           │    │
│                                  ▼           │    │
│                           [Form molecule]    │    │
│                                  │           │    │
│                           Release permits ───┘    │
│                                                    │
└───────────────────────────────────────────────────┘
```

### 3. Semaphore + Barrier Solution

```python
class H2O:
    def __init__(self):
        self.h_sem = Semaphore(2)  # 2 H slots
        self.o_sem = Semaphore(1)  # 1 O slot
        self.barrier = Barrier(3)  # Wait for 3 threads
    
    def hydrogen(self, releaseHydrogen):
        self.h_sem.acquire()       # Get H slot
        releaseHydrogen()          # Output 'H'
        self.barrier.wait()        # Wait for 2H + 1O
        self.h_sem.release()       # Release for next molecule
    
    def oxygen(self, releaseOxygen):
        self.o_sem.acquire()       # Get O slot
        releaseOxygen()            # Output 'O'
        self.barrier.wait()        # Wait for 2H + 1O
        self.o_sem.release()       # Release for next molecule
```

### 4. Execution Flow

```
TIME →
H1: acquire(h_sem=2→1) ✓ → print 'H' → barrier.wait()────────┐
H2: acquire(h_sem=1→0) ✓ → print 'H' → barrier.wait()────────┤
H3: acquire(h_sem=0) BLOCKED                                  │
O1: acquire(o_sem=1→0) ✓ → print 'O' → barrier.wait()────────┤
O2: acquire(o_sem=0) BLOCKED                                  │
                                                              ▼
                                              [All 3 at barrier - RELEASE!]
                                                              │
H1: ←──────────── barrier passed ─── h_sem.release() ────────┤
H2: ←──────────── barrier passed ─── h_sem.release() ────────┤
O1: ←──────────── barrier passed ─── o_sem.release() ────────┘
                                              │
H3: acquire(h_sem=2→1) ✓ [NOW PROCEEDS]      │
O2: acquire(o_sem=1→0) ✓ [NOW PROCEEDS]      ▼
```

### 5. Alternative: Condition Variable

```python
class H2O:
    def __init__(self):
        self.h_count = 0
        self.o_count = 0
        self.cv = Condition()
    
    def hydrogen(self, releaseHydrogen):
        with self.cv:
            while self.h_count >= 2:  # Wait if 2 H already waiting
                self.cv.wait()
            self.h_count += 1
            releaseHydrogen()
            self._try_form_molecule()
    
    def oxygen(self, releaseOxygen):
        with self.cv:
            while self.o_count >= 1:  # Wait if 1 O already waiting
                self.cv.wait()
            self.o_count += 1
            releaseOxygen()
            self._try_form_molecule()
    
    def _try_form_molecule(self):
        if self.h_count >= 2 and self.o_count >= 1:
            self.h_count -= 2
            self.o_count -= 1
            self.cv.notify_all()  # Release waiting threads
```

## 📊 Solution Comparison

| Approach | Pros | Cons |
|----------|------|------|
| **Sem + Barrier** | Clean, correct | Needs C++20/Python barrier |
| Condition Variable | Works everywhere | More complex logic |
| CyclicBarrier | Reusable | Java-specific |

## 🧠 Key Insights

### Why Release After Barrier?
```
WRONG: Release before barrier
  H1 releases → H3 acquires → H3 prints before molecule forms!

RIGHT: Release after barrier
  All three print → barrier → then release → next molecule can form
```

### Why Exactly 2 and 1?
```
H₂O chemical formula:
- 2 Hydrogen atoms
- 1 Oxygen atom

Semaphore(2): Allows exactly 2 H threads
Semaphore(1): Allows exactly 1 O thread
Barrier(3):   Ensures all 3 are ready
```

## 💻 C++20 Solution

```cpp
class H2O {
    std::counting_semaphore<2> h_sem{2};
    std::counting_semaphore<1> o_sem{1};
    std::barrier<> barrier{3};
    
public:
    void hydrogen(function<void()> releaseHydrogen) {
        h_sem.acquire();
        releaseHydrogen();
        barrier.arrive_and_wait();
        h_sem.release();
    }
    
    void oxygen(function<void()> releaseOxygen) {
        o_sem.acquire();
        releaseOxygen();
        barrier.arrive_and_wait();
        o_sem.release();
    }
};
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No limit on H/O | Wrong ratios | Use counting semaphores |
| Release before barrier | Premature proceed | Release after barrier |
| Missing barrier | Threads don't sync | All 3 must wait |
| Wrong barrier count | Hang or wrong grouping | Exactly 3 parties |

## 🔗 Related Problems
- Print FooBar (2-thread alternation)
- Fizz Buzz Multithreaded (4-thread coordination)
- Print In Order (sequential ordering)

