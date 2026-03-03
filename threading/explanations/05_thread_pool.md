# Problem 5: Thread Pool Implementation

## 🎯 Problem Statement
Implement a thread pool that:
1. Maintains a fixed number of worker threads
2. Accepts tasks via a submit method
3. Returns Future objects for task results
4. Supports graceful shutdown

## 🏢 Companies
**Databricks** (Spark uses thread pools), **Glean** (parallel indexing)

## 🔑 Core Principles

### 1. Why Thread Pools?

```
WITHOUT POOL:                    WITH POOL:
┌─────────────────┐              ┌─────────────────┐
│ Task 1 → Create Thread         │ Task 1 ──┐      │
│ Task 2 → Create Thread         │ Task 2 ──┼──→ [Worker 1]
│ Task 3 → Create Thread         │ Task 3 ──┼──→ [Worker 2]
│ ...                            │ Task 4 ──┼──→ [Worker 3]
│ Task N → Create Thread         │ ...      │     [Worker 4]
└─────────────────┘              └──────────┴─────┘

Problems:                        Benefits:
- Thread creation overhead       - Reuse threads
- Too many threads = thrashing   - Control concurrency
- Resource exhaustion            - Predictable resource usage
```

### 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    THREAD POOL                       │
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │   TASK QUEUE    │    │      WORKER THREADS     │ │
│  │  ┌───┐ ┌───┐    │    │  ┌────┐ ┌────┐ ┌────┐  │ │
│  │  │T1 │ │T2 │... │───→│  │ W1 │ │ W2 │ │ W3 │  │ │
│  │  └───┘ └───┘    │    │  └────┘ └────┘ └────┘  │ │
│  └─────────────────┘    └─────────────────────────┘ │
│          ↑                         │                │
│      submit()                  execute()            │
└─────────────────────────────────────────────────────┘
```

### 3. The Future Pattern

```
SUBMIT:                          GET RESULT:
┌─────────┐    ┌────────┐       ┌────────┐
│ submit()│───→│ Future │       │ future │
└─────────┘    └────────┘       │ .get() │
     │              │           └────────┘
     │              │                │
     ▼              ▼                ▼
[Task queued]  [Placeholder]    [Block until ready]
                    │                │
                    ▼                ▼
              [Task runs]       [Return result]
                    │
                    ▼
              [Set result]
```

### 4. Worker Thread Lifecycle

```
┌─────────────────────────────────────────┐
│              WORKER LOOP                 │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │ while (not shutdown):              │  │
│  │   task = queue.get()  # BLOCKS    │  │
│  │   if task is POISON_PILL:         │  │
│  │       break                        │  │
│  │   try:                             │  │
│  │       result = task.run()          │  │
│  │       future.set_result(result)    │  │
│  │   except Exception as e:           │  │
│  │       future.set_exception(e)      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 🧠 Key Design Decisions

### Task Queue
| Type | Behavior | Use Case |
|------|----------|----------|
| Unbounded | Never blocks put() | Memory risk |
| **Bounded** | Blocks when full | Backpressure |
| Priority | Highest priority first | Task prioritization |

### Rejection Policy (when queue full)
| Policy | Behavior |
|--------|----------|
| Abort | Throw exception |
| Discard | Silently drop task |
| Caller Runs | Caller thread executes |
| Discard Oldest | Remove oldest, add new |

### Shutdown Modes
| Mode | Behavior |
|------|----------|
| Graceful | Finish queued tasks, then stop |
| Immediate | Stop accepting, interrupt current |
| Forceful | Kill threads immediately |

## 💻 Implementation Key Points

```cpp
// C++ with packaged_task
template<typename F>
auto submit(F&& func) -> std::future<decltype(func())> {
    auto task = std::make_shared<std::packaged_task<decltype(func())()>>(
        std::forward<F>(func)
    );
    std::future<decltype(func())> result = task->get_future();
    
    queue.push([task]() { (*task)(); });
    return result;
}
```

```python
# Python with concurrent.futures (built-in!)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as pool:
    future = pool.submit(my_function, arg1, arg2)
    result = future.result()  # Blocks until done
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Unbounded queue | OOM on burst | Use bounded queue |
| No exception handling | Lost exceptions | Catch and store in Future |
| Hard shutdown | Lost work | Implement graceful shutdown |
| Too many threads | Context switching overhead | Size = CPU cores (for CPU work) |

## 📊 Sizing Guidelines

| Workload Type | Optimal Pool Size |
|---------------|-------------------|
| CPU-bound | # of CPU cores |
| I/O-bound | # cores × (1 + wait_time/compute_time) |
| Mixed | Separate pools for CPU and I/O |

