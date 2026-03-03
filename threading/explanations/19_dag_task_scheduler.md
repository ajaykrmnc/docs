# Problem 19: Async Task Scheduler with Dependencies

## 🎯 Problem Statement
Execute tasks respecting dependencies. Task B depends on A means A must complete before B starts. Maximize parallelism.

## 🏢 Companies
**Databricks** (Spark DAG), **Glean** (pipeline processing)

## 🔑 Core Principles

### 1. Task Dependency Graph (DAG)

```
        ┌───┐
        │ A │  ← No dependencies (ready immediately)
        └─┬─┘
          │
    ┌─────┴─────┐
    ▼           ▼
  ┌───┐       ┌───┐
  │ B │       │ C │  ← Both depend on A (can run in PARALLEL!)
  └─┬─┘       └─┬─┘
    │           │
    └─────┬─────┘
          ▼
        ┌───┐
        │ D │  ← Depends on B AND C
        └───┘

Execution Order: A → (B || C) → D
```

### 2. Kahn's Algorithm (Topological Sort)

```
ALGORITHM:
1. Calculate in-degree for each node (# of dependencies)
2. Add all nodes with in-degree 0 to ready queue
3. While ready queue not empty:
   a. Remove node, execute task
   b. For each dependent: decrement in-degree
   c. If in-degree becomes 0, add to ready queue

PARALLEL VERSION:
- Execute all ready tasks in parallel (thread pool)
- When task completes, update dependents
```

### 3. In-Degree Calculation

```
Task:     A    B    C    D
Deps:     []   [A]  [A]  [B,C]
In-deg:   0    1    1    2

Initially ready: [A]  (in-degree 0)

After A completes:
  B.in_degree-- → 0 (ready!)
  C.in_degree-- → 0 (ready!)

Ready: [B, C]  (run in parallel)

After B completes:
  D.in_degree-- → 1

After C completes:
  D.in_degree-- → 0 (ready!)

Ready: [D]
```

### 4. Implementation

```python
class DAGScheduler:
    def __init__(self, num_workers=4):
        self.tasks = {}  # task_id -> Task
        self.num_workers = num_workers

    def add_task(self, task_id, func, dependencies=[]):
        self.tasks[task_id] = Task(task_id, func, dependencies)

    def execute(self):
        # Calculate in-degrees
        in_degree = {t: len(self.tasks[t].deps) for t in self.tasks}

        # Initial ready tasks
        ready = Queue()
        for t in self.tasks:
            if in_degree[t] == 0:
                ready.put(t)

        results = {}
        remaining = len(self.tasks)
        lock = Lock()

        with ThreadPoolExecutor(max_workers=self.num_workers) as pool:
            futures = {}

            while remaining > 0:
                # Submit all ready tasks
                while not ready.empty():
                    task_id = ready.get()
                    futures[task_id] = pool.submit(
                        self.tasks[task_id].func
                    )

                # Wait for any completion
                for task_id, future in list(futures.items()):
                    if future.done():
                        results[task_id] = future.result()
                        del futures[task_id]
                        remaining -= 1

                        # Update dependents
                        for dep_id in self.tasks[task_id].dependents:
                            with lock:
                                in_degree[dep_id] -= 1
                                if in_degree[dep_id] == 0:
                                    ready.put(dep_id)

        return results
```

### 5. Simpler: Future-Based Approach

```python
def execute_with_futures(self):
    futures = {}

    with ThreadPoolExecutor(max_workers=4) as pool:
        def submit_task(task_id):
            if task_id in futures:
                return futures[task_id]

            # Submit dependencies first
            dep_futures = [submit_task(d) for d in self.tasks[task_id].deps]

            def run():
                # Wait for all dependencies
                for f in dep_futures:
                    f.result()
                return self.tasks[task_id].func()

            futures[task_id] = pool.submit(run)
            return futures[task_id]

        # Submit all tasks
        for task_id in self.tasks:
            submit_task(task_id)

        # Collect results
        return {t: f.result() for t, f in futures.items()}
```

## 📊 Parallelism Analysis

```
MAXIMUM PARALLELISM:
        A
       /|\
      B C D     ← 3 tasks can run in parallel
       \|/
        E

Width of DAG = max concurrent tasks

MINIMUM PARALLELISM:
A → B → C → D → E  (chain)

Only 1 task at a time (no parallelism)
```

## 🧠 Key Insights

### Thread Safety Requirements
```python
# SHARED STATE that needs protection:
- in_degree dictionary (decrement operation)
- ready queue (add operation)
- remaining counter

# IMMUTABLE after construction:
- task definitions
- dependency graph
```

### Cycle Detection
```python
def has_cycle(tasks):
    """Detect cycle using DFS"""
    UNVISITED, VISITING, VISITED = 0, 1, 2
    state = {t: UNVISITED for t in tasks}

    def dfs(node):
        if state[node] == VISITING:
            return True  # CYCLE!
        if state[node] == VISITED:
            return False

        state[node] = VISITING
        for dep in tasks[node].dependents:
            if dfs(dep):
                return True
        state[node] = VISITED
        return False

    return any(dfs(t) for t in tasks)
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Not detecting cycles | Infinite wait | Check for cycles first |
| Race on in-degree | Wrong scheduling | Lock updates |
| Starting before deps done | Wrong results | Wait for futures |
| No parallelism | Slow execution | Use thread pool |

## 🔗 Real-World Examples
- **Apache Spark**: Stage DAG for job execution
- **Airflow**: Workflow task dependencies
- **Make/Bazel**: Build dependency graphs
- **CI/CD**: Pipeline stage dependencies