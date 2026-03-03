# Problem 17: Scheduled Executor Service

## 🎯 Problem Statement
Implement a scheduler that executes tasks at specified times or intervals:
- `schedule(task, delay)` - Run once after delay
- `scheduleAtFixedRate(task, delay, period)` - Run repeatedly

## 🏢 Companies
**Rubrik** (backup scheduling), **Glean** (index refresh), **Databricks** (job scheduling)

## 🔑 Core Principles

### 1. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  SCHEDULED EXECUTOR                      │
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │            PRIORITY QUEUE (Min-Heap)             │   │
│   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │   │
│   │  │Task@10s│ │Task@30s│ │Task@45s│ │Task@60s│   │   │
│   │  └────────┘ └────────┘ └────────┘ └────────┘   │   │
│   │  (soonest)                        (latest)      │   │
│   └─────────────────────────────────────────────────┘   │
│            │                                             │
│            ▼                                             │
│   ┌─────────────────────────────────────────────────┐   │
│   │              WORKER THREAD                       │   │
│   │  1. Wait until next task is due                 │   │
│   │  2. Execute task                                │   │
│   │  3. If periodic, reschedule                     │   │
│   │  4. Repeat                                       │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 2. Priority Queue for Tasks

```python
@dataclass(order=True)
class ScheduledTask:
    execute_time: float           # Sort by this!
    task_id: int = field(compare=False)
    func: Callable = field(compare=False)
    interval: float = field(default=None, compare=False)
    cancelled: bool = field(default=False, compare=False)

# Min-heap: smallest execute_time at top
heapq.heappush(queue, task)
```

### 3. Worker Loop

```python
def worker_loop(self):
    while not self.shutdown:
        with self.condition:
            if not self.queue:
                self.condition.wait()  # Wait for tasks
                continue
            
            # Calculate wait time
            next_task = self.queue[0]
            wait_time = next_task.execute_time - time.time()
            
            if wait_time > 0:
                # Sleep until task is due (but wake if new task added)
                self.condition.wait(timeout=wait_time)
                continue
            
            # Task is due - remove from queue
            task = heapq.heappop(self.queue)
        
        # Execute outside lock!
        if not task.cancelled:
            task.func()
            
            # Reschedule if periodic
            if task.interval:
                task.execute_time = time.time() + task.interval
                with self.condition:
                    heapq.heappush(self.queue, task)
```

### 4. Why Wake on New Task?

```
SCENARIO:
Worker sleeping until task at T+60s
New task added for T+10s

WITHOUT wake:           WITH wake:
Worker sleeps 60s       Worker wakes immediately
Misses T+10s task!      Sees new task, adjusts wait

SOLUTION: condition.notify() when task added
```

### 5. Fixed Rate vs Fixed Delay

```
FIXED RATE:
Task takes 20ms, period 100ms
  T=0    T=100  T=200  T=300
   │      │      │      │
  [20ms] [20ms] [20ms] [20ms]
   
Scheduled at: 0, 100, 200, 300... (consistent times)

FIXED DELAY:
Task takes 20ms, delay 100ms
  T=0      T=120    T=240    T=360
   │        │        │        │
  [20ms]   [20ms]   [20ms]   [20ms]
  └─100ms─┘└─100ms─┘└─100ms─┘
  
Scheduled at: 0, 120, 240... (delay AFTER completion)
```

```python
# Fixed Rate
def reschedule_fixed_rate(task):
    task.execute_time += task.interval  # Based on original time

# Fixed Delay
def reschedule_fixed_delay(task):
    task.execute_time = time.time() + task.interval  # Based on now
```

## 📊 Key Operations

| Operation | Time Complexity |
|-----------|-----------------|
| schedule() | O(log n) - heap insert |
| cancel() | O(n) - find task |
| Next task | O(1) - heap peek |
| Execute | O(log n) - heap pop |

## 🧠 Key Insights

### Handling Cancelled Tasks
```python
# Option 1: Lazy removal (check at execution)
if not task.cancelled:
    task.func()

# Option 2: Eager removal (remove from heap)
# More complex, requires heap rebuild or custom heap
```

### Thread Safety
```python
# Schedule must be thread-safe
def schedule(self, func, delay):
    task = ScheduledTask(
        execute_time=time.time() + delay,
        func=func
    )
    
    with self.condition:  # Lock!
        heapq.heappush(self.queue, task)
        self.condition.notify()  # Wake worker
    
    return task.task_id
```

## 💻 C++ Implementation Key Points

```cpp
class ScheduledExecutor {
    std::priority_queue<Task, vector<Task>, greater<Task>> queue_;
    std::mutex mutex_;
    std::condition_variable cv_;
    
    void schedule(function<void()> func, chrono::milliseconds delay) {
        Task task{Clock::now() + delay, next_id_++, func};
        
        {
            lock_guard<mutex> lock(mutex_);
            queue_.push(task);
        }
        cv_.notify_one();  // Wake worker
    }
};
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Not waking on new task | Late execution | notify() on schedule |
| Lock during execution | Blocks scheduling | Release lock before exec |
| No cancellation support | Can't stop tasks | Add cancelled flag |
| Busy waiting | CPU waste | Use condition.wait(timeout) |

## 🔗 Real-World Usage
- **Cron jobs**: System task scheduling
- **Retry logic**: Exponential backoff
- **Heartbeats**: Periodic health checks
- **Cache expiry**: TTL enforcement

