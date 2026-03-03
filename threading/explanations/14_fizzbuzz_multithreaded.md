# Problem 14: FizzBuzz Multithreaded (LeetCode 1195)

## 🎯 Problem Statement
4 threads print numbers 1 to n:
- Thread A: prints "fizz" for numbers divisible by 3 (not 5)
- Thread B: prints "buzz" for numbers divisible by 5 (not 3)
- Thread C: prints "fizzbuzz" for numbers divisible by both
- Thread D: prints the number for other cases

## 🏢 Companies
**Databricks, Glean** - Tests multi-way coordination

## 🔑 Core Principles

### 1. Number Distribution

```
Number:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
Thread:  D   D   A   D   B   A   D   D   A   B   D   A   D   D   C
Output:  1   2  fizz 4 buzz fizz 7   8  fizz buzz 11 fizz 13  14 fizzbuzz
```

### 2. Turn-Based Coordination

```
┌─────────────────────────────────────────────────────────────┐
│                 SHARED STATE: current = 1                    │
│                                                              │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
│   │ FIZZ   │  │ BUZZ   │  │FIZZBUZZ│  │ NUMBER │           │
│   │Thread  │  │Thread  │  │ Thread │  │ Thread │           │
│   └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘           │
│       │           │           │           │                  │
│       ▼           ▼           ▼           ▼                  │
│   Wait for    Wait for    Wait for    Wait for              │
│   current%3=0 current%5=0 current%15=0 none of              │
│   && %5≠0     && %3≠0                  above                │
│       │           │           │           │                  │
│       ▼           ▼           ▼           ▼                  │
│   [print]     [print]     [print]     [print]               │
│       │           │           │           │                  │
│       └───────────┴───────────┴───────────┘                  │
│                       │                                      │
│                       ▼                                      │
│               current++ & notify_all()                       │
└─────────────────────────────────────────────────────────────┘
```

### 3. Each Thread's Logic

```python
class FizzBuzz:
    def __init__(self, n):
        self.n = n
        self.current = 1
        self.cv = Condition()
    
    def fizz(self, printFizz):
        while True:
            with self.cv:
                # Wait for: divisible by 3 BUT NOT 5
                while self.current <= self.n and not (
                    self.current % 3 == 0 and self.current % 5 != 0
                ):
                    self.cv.wait()
                
                if self.current > self.n:
                    return
                
                printFizz()
                self.current += 1
                self.cv.notify_all()
    
    # Similarly for buzz(), fizzbuzz(), number()
```

### 4. Wait Conditions

| Thread | Condition to Print | Numbers |
|--------|-------------------|---------|
| fizz | `n % 3 == 0 && n % 5 != 0` | 3, 6, 9, 12... |
| buzz | `n % 5 == 0 && n % 3 != 0` | 5, 10, 20, 25... |
| fizzbuzz | `n % 15 == 0` | 15, 30, 45... |
| number | `n % 3 != 0 && n % 5 != 0` | 1, 2, 4, 7, 8... |

### 5. Execution Example (n=5)

```
TIME →

current=1: (1%3≠0, 1%5≠0) → number prints "1", current=2
current=2: (2%3≠0, 2%5≠0) → number prints "2", current=3
current=3: (3%3=0, 3%5≠0) → fizz prints "fizz", current=4
current=4: (4%3≠0, 4%5≠0) → number prints "4", current=5
current=5: (5%3≠0, 5%5=0) → buzz prints "buzz", current=6

current=6 > n → All threads exit

Output: "1 2 fizz 4 buzz"
```

## 📊 Why notify_all()?

```
After printing, WHY notify_all() instead of notify()?

Thread A (fizz):     waiting for %3==0 && %5≠0
Thread B (buzz):     waiting for %5==0 && %3≠0
Thread C (fizzbuzz): waiting for %15==0
Thread D (number):   waiting for %3≠0 && %5≠0

Each has DIFFERENT condition!
notify() might wake wrong thread → deadlock
notify_all() wakes all, each checks its condition
```

## 🧠 Key Insights

### Termination Handling
```python
# CRITICAL: Check termination INSIDE the loop
while True:
    with self.cv:
        while self.current <= self.n and not my_condition():
            self.cv.wait()
        
        if self.current > self.n:
            return  # EXIT the thread!
        
        # ... do work
```

### Why `while` Instead of `if`?
```
1. Spurious wakeups (thread wakes without notification)
2. Wrong thread woke up (notify_all wakes all, only one should proceed)
3. Condition changed before we got lock

Always re-check condition after waking!
```

## 💻 C++ Solution

```cpp
class FizzBuzz {
    int n;
    int current = 1;
    mutex m;
    condition_variable cv;
    
public:
    FizzBuzz(int n) : n(n) {}
    
    void fizz(function<void()> printFizz) {
        while (true) {
            unique_lock<mutex> lock(m);
            cv.wait(lock, [this] {
                return current > n || (current % 3 == 0 && current % 5 != 0);
            });
            if (current > n) return;
            printFizz();
            ++current;
            cv.notify_all();
        }
    }
    // ... similar for buzz, fizzbuzz, number
};
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using notify() | Wrong thread wakes | Use notify_all() |
| Missing termination check | Infinite wait | Check current > n |
| Wrong condition logic | Wrong output | Double-check mod logic |
| Incrementing outside lock | Race condition | Increment inside lock |

## 📝 Complexity
- **Time**: O(n) - each number processed once
- **Space**: O(1) - only counters and sync primitives

