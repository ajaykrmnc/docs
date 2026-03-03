# Problem 15: Concurrent HashMap

## 🎯 Problem Statement
Implement a thread-safe hash map with good concurrency. Operations on different parts of the map should be able to proceed in parallel.

## 🏢 Companies
**Rubrik, Databricks** - Critical for any concurrent system!

## 🔑 Core Principles

### 1. The Problem with Global Lock

```
GLOBAL LOCK:
┌───────────────────────────────────────┐
│              HASH MAP                  │
│  [A] [B] [C] [D] [E] [F] [G] [H]      │
│                                        │
│         ONE LOCK FOR ALL               │
└───────────────────────────────────────┘

Thread 1: put(A) ──[LOCK]────────────[UNLOCK]──
Thread 2: get(H) ────────waiting─────[LOCK]────
Thread 3: put(D) ─────────────waiting──────────

ALL operations serialize! Poor performance.
```

### 2. Lock Striping Solution

```
LOCK STRIPING:
┌───────────────────────────────────────┐
│              HASH MAP                  │
│  Segment 0    Segment 1    Segment 2   │
│  [A][B][C]    [D][E][F]    [G][H][I]   │
│    Lock 0       Lock 1       Lock 2    │
└───────────────────────────────────────┘

Thread 1: put(A) ─[Lock 0]────────────
Thread 2: get(H) ─[Lock 2]──parallel!─
Thread 3: put(D) ─[Lock 1]──parallel!─

Different segments → PARALLEL operations!
```

### 3. Implementation

```python
class ConcurrentHashMap:
    def __init__(self, num_segments=16):
        self.num_segments = num_segments
        self.segments = [{} for _ in range(num_segments)]
        self.locks = [Lock() for _ in range(num_segments)]
    
    def _get_segment(self, key):
        return hash(key) % self.num_segments
    
    def put(self, key, value):
        idx = self._get_segment(key)
        with self.locks[idx]:
            self.segments[idx][key] = value
    
    def get(self, key):
        idx = self._get_segment(key)
        with self.locks[idx]:
            return self.segments[idx].get(key)
```

### 4. Read-Write Locks for Better Read Concurrency

```
SHARED_MUTEX per segment:
┌─────────────────────────────────────────┐
│           Segment with RW Lock           │
│                                          │
│   Reader 1 ────┐                         │
│   Reader 2 ────┼──► [Shared Lock] ──OK!  │
│   Reader 3 ────┘                         │
│                                          │
│   Writer ──────► [Exclusive Lock]        │
│                  (waits for readers)     │
└─────────────────────────────────────────┘
```

```cpp
template<typename K, typename V>
class ConcurrentMapRW {
    struct Segment {
        std::unordered_map<K, V> map;
        std::shared_mutex mutex;
    };
    
    std::array<Segment, 16> segments_;
    
public:
    V get(const K& key) {
        auto& seg = segments_[hash(key) % 16];
        std::shared_lock lock(seg.mutex);  // Read lock
        return seg.map[key];
    }
    
    void put(const K& key, const V& value) {
        auto& seg = segments_[hash(key) % 16];
        std::unique_lock lock(seg.mutex);  // Write lock
        seg.map[key] = value;
    }
};
```

### 5. Sizing the Number of Segments

```
TOO FEW SEGMENTS:        OPTIMAL:              TOO MANY:
┌─────┬─────┐           ┌──┬──┬──┬──┐         ┌┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┐
│     │     │           │  │  │  │  │         ││││││││││││││││││
│BUSY │BUSY │           │OK│OK│OK│OK│         │Memory overhead!│
└─────┴─────┘           └──┴──┴──┴──┘         └┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┴┘
High contention         Good balance          Wasted memory

Rule of thumb: 16-32 segments for general use
More for high-contention scenarios
```

## 📊 Comparison

| Approach | Read Concurrency | Write Concurrency | Memory |
|----------|------------------|-------------------|--------|
| Global Lock | 1 | 1 | Low |
| **Lock Striping** | N | N | Medium |
| RW Lock Striping | N × readers | N | Medium |
| Lock-Free | Unlimited | Unlimited | Higher |

## 🧠 Key Insights

### Java's ConcurrentHashMap
```
Java 7: Segment-based (like our implementation)
Java 8: Per-bucket locks + CAS operations
        More fine-grained, better scalability
```

### Why Hash % NumSegments?
```
hash("key") = 12345678
segment = 12345678 % 16 = 14

Same key → always same segment → consistent locking
Different keys may share segment → some contention OK
```

### Size Operation Caveat
```python
def size(self):
    # WARNING: NOT atomic across segments!
    total = 0
    for i in range(self.num_segments):
        with self.locks[i]:
            total += len(self.segments[i])
    return total
    
# Size can change while iterating!
# Use with caution in concurrent scenarios
```

## ⚠️ Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Same lock for all | No concurrency | Lock striping |
| Too few segments | High contention | Increase segments |
| Not holding lock for check-then-act | Race condition | Atomic operations |
| Resizing without locks | Data corruption | Lock all segments |

## 💻 Advanced: Lock-Free with CAS

```cpp
// Compare-And-Swap for lock-free updates
std::atomic<Node*> head;

void put(K key, V value) {
    Node* new_node = new Node(key, value);
    Node* expected = head.load();
    do {
        new_node->next = expected;
    } while (!head.compare_exchange_weak(expected, new_node));
}
```

## 📈 When to Use What

| Scenario | Recommendation |
|----------|----------------|
| Mostly reads | RW Lock + Lock Striping |
| Balanced read/write | Lock Striping |
| Extreme performance | Lock-free structures |
| Simple use case | Global lock (it's fine!) |

