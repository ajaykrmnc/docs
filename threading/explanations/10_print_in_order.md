# Problem 10: Print In Order (LeetCode 1114)

## 🎯 Problem Statement
Three threads will call `first()`, `second()`, `third()` potentially in any order. Ensure they print "first", "second", "third" in order regardless of which thread starts first.

## 🏢 Companies
**Databricks, Glean** - Tests understanding of thread ordering

## 🔑 Core Principles

### 1. The Challenge

```
RANDOM EXECUTION ORDER:        REQUIRED OUTPUT:
Thread 3: third()  ←starts     "first"
Thread 1: first()              "second"  
Thread 2: second()             "third"

We must ENFORCE: first → second → third
```

### 2. State Machine Approach

```
STATE TRANSITIONS:
┌─────────┐  first()  ┌─────────┐  second()  ┌─────────┐
│ State 0 │ ────────► │ State 1 │ ─────────► │ State 2 │
└─────────┘           └─────────┘            └─────────┘

- second() waits for State ≥ 1
- third() waits for State ≥ 2
```

### 3. Solution 1: Condition Variable

```python
class Foo:
    def __init__(self):
        self.state = 0
        self.condition = Condition()
    
    def first(self, printFirst):
        with self.condition:
            printFirst()
            self.state = 1
            self.condition.notify_all()
    
    def second(self, printSecond):
        with self.condition:
            while self.state < 1:      # Wait for first
                self.condition.wait()
            printSecond()
            self.state = 2
            self.condition.notify_all()
    
    def third(self, printThird):
        with self.condition:
            while self.state < 2:      # Wait for second
                self.condition.wait()
            printThird()
```

### 4. Solution 2: Semaphores (More Elegant)

```
SEMAPHORE AS GATES:

gate1 (init=0): Blocks second() until first() completes
gate2 (init=0): Blocks third() until second() completes

┌─────────┐    ┌─────────┐    ┌─────────┐
│ first() │───►│second() │───►│ third() │
└─────────┘    └─────────┘    └─────────┘
      │  gate1.release()  │  gate2.release()
      │        │          │        │
      └────────┘          └────────┘
```

```python
class Foo:
    def __init__(self):
        self.gate1 = Semaphore(0)
        self.gate2 = Semaphore(0)
    
    def first(self, printFirst):
        printFirst()
        self.gate1.release()  # Open gate for second
    
    def second(self, printSecond):
        self.gate1.acquire()  # Wait for first
        printSecond()
        self.gate2.release()  # Open gate for third
    
    def third(self, printThird):
        self.gate2.acquire()  # Wait for second
        printThird()
```

### 5. Solution 3: Events (Simplest)

```python
class Foo:
    def __init__(self):
        self.first_done = Event()
        self.second_done = Event()
    
    def first(self, printFirst):
        printFirst()
        self.first_done.set()
    
    def second(self, printSecond):
        self.first_done.wait()
        printSecond()
        self.second_done.set()
    
    def third(self, printThird):
        self.second_done.wait()
        printThird()
```

## 📊 Solution Comparison

| Solution | Memory | Complexity | Best For |
|----------|--------|------------|----------|
| Condition Variable | 1 CV + 1 int | Medium | Complex state |
| Semaphores | 2 semaphores | Simple | **Sequential deps** |
| Events | 2 events | **Simplest** | Boolean flags |
| Atomics | 2 bools | Low-level | Performance |

## 🧠 Key Insights

### Why Semaphore(0)?
```
Semaphore initialized to 0:
- acquire() blocks immediately
- release() allows one acquire() to proceed

Perfect for "wait until signaled" pattern!
```

### Why notify_all()?
```
notify():     Wakes ONE waiter (might be wrong one)
notify_all(): Wakes ALL waiters (each checks its condition)

For state machine: Use notify_all() to wake all potential waiters
```

### Event vs Semaphore
```
EVENT:                    SEMAPHORE:
- Binary (set/clear)      - Counter
- wait() checks flag      - acquire() decrements
- Can check without wait  - Always blocks if 0
- Manual reset option     - Auto "reset" on acquire

Use Event for: "Did X happen?"
Use Semaphore for: "Can I proceed?"
```

## 💻 C++ Solutions

```cpp
// Semaphore (C++20)
std::binary_semaphore gate1{0}, gate2{0};

void first(function<void()> printFirst) {
    printFirst();
    gate1.release();
}

void second(function<void()> printSecond) {
    gate1.acquire();
    printSecond();
    gate2.release();
}

void third(function<void()> printThird) {
    gate2.acquire();
    printThird();
}
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using if instead of while | Spurious wakeup | Use while loop |
| Wrong semaphore initial value | Never proceeds | Start with 0 |
| notify() instead of notify_all() | Wrong thread wakes | Use notify_all() |
| Not holding lock during state check | Race condition | Check inside lock |

## 🔗 Related Problems
- Print FooBar Alternately (LeetCode 1115)
- Print Zero Even Odd (LeetCode 1116)
- Building H2O (LeetCode 1117)

