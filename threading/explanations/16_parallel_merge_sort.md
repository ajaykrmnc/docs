# Problem 16: Parallel Merge Sort

## 🎯 Problem Statement
Implement merge sort using multiple threads for parallel sorting. Achieve speedup over sequential version.

## 🏢 Companies
**Databricks** (distributed sorting is core to Spark)

## 🔑 Core Principles

### 1. Sequential Merge Sort

```
                [5, 2, 8, 1, 9, 3, 7, 4]
                         │
            ┌────────────┴────────────┐
            │                         │
      [5, 2, 8, 1]              [9, 3, 7, 4]
            │                         │
      ┌─────┴─────┐             ┌─────┴─────┐
      │           │             │           │
   [5, 2]      [8, 1]        [9, 3]      [7, 4]
      │           │             │           │
   ┌──┴──┐     ┌──┴──┐       ┌──┴──┐     ┌──┴──┐
  [5]   [2]   [8]   [1]     [9]   [3]   [7]   [4]
   │     │     │     │       │     │     │     │
   └──┬──┘     └──┬──┘       └──┬──┘     └──┬──┘
   [2, 5]      [1, 8]        [3, 9]      [4, 7]
      │           │             │           │
      └─────┬─────┘             └─────┬─────┘
      [1, 2, 5, 8]          [3, 4, 7, 9]
            │                         │
            └────────────┬────────────┘
                         │
         [1, 2, 3, 4, 5, 7, 8, 9]
```

### 2. Parallel Opportunity

```
INDEPENDENT SUBPROBLEMS:
                [5, 2, 8, 1, 9, 3, 7, 4]
                         │
            ┌────────────┴────────────┐
            │                         │
      [5, 2, 8, 1]              [9, 3, 7, 4]
       Thread 1                  Thread 2
       (parallel!)               (parallel!)
```

### 3. Thread Depth Limit

```
WHY LIMIT DEPTH?

Depth 0:  1 thread   → 2 threads
Depth 1:  2 threads  → 4 threads
Depth 2:  4 threads  → 8 threads
Depth 3:  8 threads  → 16 threads
...
Depth 10: 1024 threads!

PROBLEMS:
- Thread creation overhead > sorting benefit
- Context switching kills performance
- Memory overhead

SOLUTION: Limit depth (typically 2-4)
After depth limit → switch to sequential
```

### 4. Implementation

```python
class ParallelMergeSort:
    def __init__(self, max_depth=3):
        self.max_depth = max_depth
    
    def sort(self, arr):
        return self._parallel_sort(arr, depth=0)
    
    def _parallel_sort(self, arr, depth):
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        
        if depth < self.max_depth:
            # PARALLEL: Sort halves in separate threads
            left_result = [None]
            right_result = [None]
            
            def sort_left():
                left_result[0] = self._parallel_sort(arr[:mid], depth+1)
            
            def sort_right():
                right_result[0] = self._parallel_sort(arr[mid:], depth+1)
            
            t1 = Thread(target=sort_left)
            t2 = Thread(target=sort_right)
            
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
            return merge(left_result[0], right_result[0])
        else:
            # SEQUENTIAL: Below depth limit
            left = sequential_sort(arr[:mid])
            right = sequential_sort(arr[mid:])
            return merge(left, right)
```

### 5. Using std::async (C++)

```cpp
void parallelSort(vector<int>& arr, int left, int right, int depth) {
    if (left >= right) return;
    
    int mid = left + (right - left) / 2;
    
    if (depth < MAX_DEPTH) {
        // Async launches in separate thread
        auto left_future = std::async(std::launch::async,
            parallelSort, ref(arr), left, mid, depth + 1);
        
        parallelSort(arr, mid + 1, right, depth + 1);
        
        left_future.get();  // Wait for left half
    } else {
        sequentialSort(arr, left, mid);
        sequentialSort(arr, mid + 1, right);
    }
    
    merge(arr, left, mid, right);
}
```

## 📊 Speedup Analysis

```
IDEAL (Amdahl's Law):
Speedup = 1 / (S + P/N)
  S = Sequential fraction
  P = Parallel fraction
  N = Number of processors

MERGE SORT:
- Split: O(1) - sequential
- Sort halves: O(n log n) - parallel!
- Merge: O(n) - sequential

With 4 cores, max depth 2 (4 threads):
- Theoretical: ~3-4x speedup
- Practical: ~2-3x (overhead)
```

### Measured Results

| Array Size | Sequential | Parallel (4 threads) | Speedup |
|------------|------------|----------------------|---------|
| 10,000 | 5ms | 4ms | 1.25x |
| 100,000 | 50ms | 20ms | 2.5x |
| 1,000,000 | 500ms | 180ms | 2.8x |

## 🧠 Key Insights

### Why Not Unlimited Threads?
```
Thread creation:  ~1μs (microsecond)
Sorting 100 elements: ~10μs

For small subarrays, thread overhead > benefit!
```

### Work Stealing (Advanced)
```
Better approach: Thread pool with work stealing
- Fixed number of threads
- Tasks in queue
- Idle threads "steal" from busy threads

Libraries: TBB, OpenMP, Java ForkJoin
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Unlimited depth | Too many threads | Set max_depth |
| Small chunk threshold | Overhead dominates | Threshold ~1000 elements |
| Copying arrays | Memory overhead | Sort in-place |
| No load balancing | Uneven work | Use work stealing |

## 💡 Best Practices

1. **Threshold for parallelism**: Only parallelize chunks > 1000 elements
2. **Depth limit**: log₂(num_cores) levels typically sufficient
3. **Thread pool**: Reuse threads instead of creating new ones
4. **In-place operations**: Minimize memory allocation

