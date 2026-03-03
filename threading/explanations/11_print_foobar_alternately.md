# Problem 11: Print FooBar Alternately (LeetCode 1115)

## 🎯 Problem Statement
Two threads call `foo()` and `bar()` n times each. Ensure output is "foobar" repeated n times (alternating foo, bar, foo, bar...).

## 🏢 Companies
**Databricks, Glean, Rubrik** - Tests thread alternation patterns

## 🔑 Core Principles

### 1. The Alternation Pattern

```
REQUIRED SEQUENCE:
foo() → bar() → foo() → bar() → foo() → bar()
  ↓       ↓       ↓       ↓       ↓       ↓
"foo"   "bar"   "foo"   "bar"   "foo"   "bar"
       └─────┘        └─────┘        └─────┘
        foobar         foobar         foobar
```

### 2. Turn-Based Synchronization

```
┌──────────────────────────────────────────────┐
│                 TURN SIGNALS                  │
│                                               │
│   foo_turn ◄─────────────────────┐           │
│      │                           │           │
│      ▼                           │           │
│   [foo prints]                   │           │
│      │                           │           │
│      └──► bar_turn ──────────────│           │
│              │                   │           │
│              ▼                   │           │
│          [bar prints]            │           │
│              │                   │           │
│              └───► foo_turn ─────┘           │
│                                               │
└──────────────────────────────────────────────┘
```

### 3. Semaphore Solution (Most Elegant)

```python
class FooBar:
    def __init__(self, n):
        self.n = n
        self.foo_sem = Semaphore(1)  # foo starts (1 permit)
        self.bar_sem = Semaphore(0)  # bar waits (0 permits)
    
    def foo(self, printFoo):
        for _ in range(self.n):
            self.foo_sem.acquire()   # Wait for turn
            printFoo()
            self.bar_sem.release()   # Signal bar
    
    def bar(self, printBar):
        for _ in range(self.n):
            self.bar_sem.acquire()   # Wait for turn
            printBar()
            self.foo_sem.release()   # Signal foo
```

### 4. Execution Trace

```
TIME →
Iteration 1:
  foo: acquire(foo_sem=1→0) ✓ → print "foo" → release(bar_sem=0→1)
  bar: acquire(bar_sem=1→0) ✓ → print "bar" → release(foo_sem=0→1)

Iteration 2:
  foo: acquire(foo_sem=1→0) ✓ → print "foo" → release(bar_sem=0→1)
  bar: acquire(bar_sem=1→0) ✓ → print "bar" → release(foo_sem=0→1)

Output: "foobarfoobar"
```

### 5. Condition Variable Solution

```python
class FooBar:
    def __init__(self, n):
        self.n = n
        self.foo_turn = True
        self.condition = Condition()
    
    def foo(self, printFoo):
        for _ in range(self.n):
            with self.condition:
                while not self.foo_turn:
                    self.condition.wait()
                printFoo()
                self.foo_turn = False
                self.condition.notify()
    
    def bar(self, printBar):
        for _ in range(self.n):
            with self.condition:
                while self.foo_turn:
                    self.condition.wait()
                printBar()
                self.foo_turn = True
                self.condition.notify()
```

## 📊 Solution Comparison

| Solution | Pros | Cons |
|----------|------|------|
| **Semaphores** | Clean, minimal code | Need two semaphores |
| Condition Variable | Single sync object | More verbose |
| Atomic + Spin | No syscalls | Wastes CPU |
| Events | Clear semantics | Need manual reset |

## 🧠 Key Insights

### Why Initial Values Matter
```
foo_sem = Semaphore(1)  → foo can start immediately
bar_sem = Semaphore(0)  → bar must wait

If both were 1: Both could run simultaneously! ❌
If both were 0: Neither could start! ❌
```

### Semaphore Ping-Pong
```
foo_sem: 1 → 0 (foo acquires) → 0 (bar releases→1) → 1
bar_sem: 0 → 0 (foo releases→1) → 1 → 0 (bar acquires)

The semaphores alternate between 0 and 1!
```

## 💻 C++20 Solution

```cpp
class FooBar {
    int n;
    std::binary_semaphore foo_sem{1};
    std::binary_semaphore bar_sem{0};
    
public:
    FooBar(int n) : n(n) {}
    
    void foo(function<void()> printFoo) {
        for (int i = 0; i < n; ++i) {
            foo_sem.acquire();
            printFoo();
            bar_sem.release();
        }
    }
    
    void bar(function<void()> printBar) {
        for (int i = 0; i < n; ++i) {
            bar_sem.acquire();
            printBar();
            foo_sem.release();
        }
    }
};
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Both semaphores = 1 | Race condition | One starts at 0 |
| Forgetting loop | Only one iteration | Loop n times |
| Wrong release order | Deadlock | Release after print |
| Using mutex only | Can't signal | Use semaphore or CV |

## 🔗 Related Problems
- Print In Order (LeetCode 1114) - Sequential ordering
- Print Zero Even Odd (LeetCode 1116) - Three-way alternation
- Building H2O (LeetCode 1117) - Grouping threads

