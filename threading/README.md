# 🧵 Multithreading Interview Questions

**Target Companies**: Databricks, Rubrik, Glean

A comprehensive collection of 20 multithreading interview questions with implementations in **Python** and **C++**, along with detailed explanations.

## 📁 Structure

```
threading/
├── python/          # Python implementations
├── cpp/             # C++ implementations
├── explanations/    # Detailed markdown explanations
└── README.md        # This file
```

## 📋 Questions Overview

| # | Problem | Difficulty | Key Concepts |
|---|---------|------------|--------------|
| 01 | Producer-Consumer | Medium | Bounded buffer, Condition variables |
| 02 | Reader-Writer Lock | Medium | Shared vs Exclusive locks |
| 03 | Thread-Safe Singleton | Medium | Double-checked locking, `call_once` |
| 04 | Deadlock Prevention | Hard | Coffman conditions, Lock ordering |
| 05 | Thread Pool | Hard | Future/Promise, Task queuing |
| 06 | Blocking Queue | Medium | Condition variables, Timeout |
| 07 | Rate Limiter | Medium | Token bucket, Sliding window |
| 08 | Dining Philosophers | Hard | Resource hierarchy, Semaphores |
| 09 | Barrier & Latch | Medium | Phase synchronization |
| 10 | Print In Order | Easy | Thread ordering, Events |
| 11 | Print FooBar Alternately | Easy | Thread alternation |
| 12 | Web Crawler | Hard | Parallel BFS, Thread-safe sets |
| 13 | Building H2O | Medium | Barrier, Semaphore grouping |
| 14 | FizzBuzz Multithreaded | Medium | Multi-way coordination |
| 15 | Concurrent HashMap | Hard | Lock striping, Fine-grained locking |
| 16 | Parallel Merge Sort | Medium | Divide & conquer, Thread overhead |
| 17 | Scheduled Executor | Hard | Priority queue, Timer thread |
| 18 | Traffic Light | Medium | State machine, Mutual exclusion |
| 19 | DAG Task Scheduler | Hard | Topological sort, Dependency graph |
| 20 | Connection Pool | Medium | Thread-local, Resource pooling |

## 🔧 Compilation

### C++ (Most files)
```bash
g++ -std=c++17 -pthread cpp/01_producer_consumer.cpp -o producer_consumer
```

### C++20 (For semaphores, barriers, latches)
```bash
g++ -std=c++20 -pthread cpp/09_barrier_latch.cpp -o barrier_latch
```

### Python
```bash
python3 python/01_producer_consumer.py
```

## 🎯 Core Concepts Covered

### Synchronization Primitives
- `mutex` / `Lock`
- `condition_variable` / `Condition`
- `semaphore` / `Semaphore`
- `barrier` / `Barrier`
- `latch` / `CountDownLatch`

### Patterns
- Producer-Consumer
- Reader-Writer
- Thread Pool
- Lock Striping
- Double-Checked Locking

### C++ Specific
- `std::scoped_lock` (C++17)
- `std::shared_mutex` (C++17)
- `std::call_once`
- `std::atomic`
- `std::future` / `std::promise`
- `std::barrier` / `std::latch` (C++20)

### Python Specific
- `threading.Lock`
- `threading.Condition`
- `threading.Semaphore`
- `threading.Barrier`
- `threading.Event`
- `concurrent.futures`

## 📚 How to Use

1. **Read the explanation first** (`explanations/XX_problem.md`)
2. **Study the implementation** (`python/` or `cpp/`)
3. **Run and experiment** with the code
4. **Try implementing yourself** before looking at solutions

## 💡 Interview Tips

1. **Always clarify requirements** - bounded vs unbounded, fairness, etc.
2. **Start with the simplest solution** - then optimize
3. **Mention trade-offs** - memory vs CPU, fairness vs throughput
4. **Know your primitives** - when to use mutex vs semaphore vs CV
5. **Discuss edge cases** - shutdown, timeout, error handling

