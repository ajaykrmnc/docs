# Challenge 04: Event Scheduler — No Cancel

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | h3isenberg / Hang | 310 cycles/op | 1488 cycles/op |
| 2nd | bdcbqa / Roman Sztergbaum | 310 cycles/op | 1798 cycles/op |
| 3rd | Roman Sztergbaum / Baseline | 310 cycles/op | 4340 cycles/op |

---

## Problem Description

Same as Challenge 03 but **without cancel support**. This dramatically changes the optimal data structure because:
- No need for per-event tracking / lookup by ID
- No need for intrusive linked lists in timer wheel slots
- Data structures can be more compact (no prev/next pointers per event)

This is essentially a pure "priority queue with advance" problem.

---

## Why Removing Cancel Changes Everything

| Feature | With Cancel | Without Cancel |
|---------|-------------|----------------|
| Event storage | Need O(1) lookup by ID | No lookup needed |
| Data structure | Timer wheel + intrusive list | Simple timer wheel or heap |
| Memory per event | ~32-40 bytes (prev, next, id, deadline, cancelled) | ~12 bytes (deadline + payload) |
| Insert | O(1) timer wheel | O(1) timer wheel or O(log n) heap |
| Advance | Skip cancelled events | Every event fires |

---

## Optimal Data Structures

### Approach 1: Simple Timer Wheel with Array-Based Slots

```cpp
// Without cancel, each slot can just be a simple dynamic array
// or a fixed-size ring buffer of events

static constexpr int WHEEL_BITS = 16;
static constexpr int WHEEL_SIZE = 1 << WHEEL_BITS;
static constexpr int WHEEL_MASK = WHEEL_SIZE - 1;

struct SimpleWheel {
    // Each slot stores events as a compact array
    struct Slot {
        uint64_t deadlines[64];   // Fixed max per slot
        uint32_t payloads[64];
        int count = 0;

        void push(uint64_t deadline, uint32_t payload) {
            deadlines[count] = deadline;
            payloads[count] = payload;
            ++count;
        }
    };

    Slot slots[WHEEL_SIZE];
    uint64_t current_time = 0;

    void schedule(uint64_t deadline, uint32_t payload) {
        int slot = deadline & WHEEL_MASK;
        slots[slot].push(deadline, payload);
    }

    template<typename Callback>
    void advance(uint64_t target, Callback&& cb) {
        while (current_time <= target) {
            int slot = current_time & WHEEL_MASK;
            auto& s = slots[slot];
            for (int i = 0; i < s.count; ++i) {
                if (s.deadlines[i] <= target) {
                    cb(s.payloads[i]);
                }
            }
            s.count = 0;  // Clear slot (can do partial clear for multi-round events)
            ++current_time;
        }
    }
};
```

### Approach 2: Bucket Queue (Calendar Queue)

A calendar queue divides time into fixed-size "days" and uses a circular array of buckets. Without cancel, this is extremely efficient.

```cpp
struct CalendarQueue {
    static constexpr int NUM_BUCKETS = 4096;
    static constexpr int BUCKET_MASK = NUM_BUCKETS - 1;
    static constexpr int DAY_SIZE = 1;  // Each bucket covers 1 tick

    struct Event {
        uint64_t deadline;
        uint32_t payload;
    };

    // Each bucket is a small vector
    struct Bucket {
        Event events[32];
        int size = 0;

        void add(uint64_t deadline, uint32_t payload) {
            events[size++] = {deadline, payload};
        }
    };

    Bucket buckets[NUM_BUCKETS];
    uint64_t current_time = 0;

    void schedule(uint64_t deadline, uint32_t payload) {
        buckets[deadline & BUCKET_MASK].add(deadline, payload);
    }

    template<typename Callback>
    void advance(uint64_t target, Callback&& cb) {
        while (current_time <= target) {
            auto& b = buckets[current_time & BUCKET_MASK];
            for (int i = 0; i < b.size; ++i) {
                if (b.events[i].deadline == current_time) {
                    cb(b.events[i].payload);
                }
            }
            // Remove fired events (swap with end)
            int j = 0;
            for (int i = 0; i < b.size; ++i) {
                if (b.events[i].deadline > current_time) {
                    b.events[j++] = b.events[i];
                }
            }
            b.size = j;
            ++current_time;
        }
    }
};
```

### Approach 3: 4-ary Min-Heap (Simpler, Competitive)

Without cancel overhead, a cache-friendly heap can be very fast:

```cpp
struct HeapScheduler {
    struct Entry {
        uint64_t deadline;
        uint32_t payload;
    };

    alignas(64) Entry heap[MAX_EVENTS];
    int size = 0;

    void schedule(uint64_t deadline, uint32_t payload) {
        heap[size] = {deadline, payload};
        sift_up_4ary(size);
        ++size;
    }

    template<typename Callback>
    void advance(uint64_t target, Callback&& cb) {
        while (size > 0 && heap[0].deadline <= target) {
            cb(heap[0].payload);
            heap[0] = heap[--size];
            sift_down_4ary(0);
        }
    }

private:
    void sift_up_4ary(int i) {
        Entry val = heap[i];
        while (i > 0) {
            int parent = (i - 1) / 4;
            if (val.deadline < heap[parent].deadline) {
                heap[i] = heap[parent];
                i = parent;
            } else break;
        }
        heap[i] = val;
    }

    void sift_down_4ary(int i) {
        Entry val = heap[i];
        while (true) {
            int first_child = 4 * i + 1;
            if (first_child >= size) break;

            // Find minimum among up to 4 children
            int best = first_child;
            int last_child = std::min(first_child + 4, size);
            for (int c = first_child + 1; c < last_child; ++c) {
                if (heap[c].deadline < heap[best].deadline)
                    best = c;
            }

            if (heap[best].deadline < val.deadline) {
                heap[i] = heap[best];
                i = best;
            } else break;
        }
        heap[i] = val;
    }
};
```

---

## Key Optimizations for 310 cycles/op

### 1. Minimize Memory per Event

```cpp
// Pack event data as tightly as possible
// 8 bytes deadline + 4 bytes payload = 12 bytes
// vs 32+ bytes with cancel support

struct __attribute__((packed)) CompactEvent {
    uint64_t deadline;
    uint32_t payload;
};
// 5 events per cache line (64 bytes)
```

### 2. Prefetching for Heap Operations

```cpp
void sift_down_prefetch(int i) {
    Entry val = heap[i];
    while (true) {
        int child = 4 * i + 1;
        if (child >= size) break;

        // Prefetch grandchildren while comparing children
        if (4 * child + 1 < size) {
            __builtin_prefetch(&heap[4 * child + 1], 0, 3);
        }

        int best = child;
        int end = std::min(child + 4, size);
        for (int c = child + 1; c < end; ++c) {
            if (heap[c].deadline < heap[best].deadline) best = c;
        }
        if (heap[best].deadline < val.deadline) {
            heap[i] = heap[best];
            i = best;
        } else break;
    }
    heap[i] = val;
}
```

### 3. SIMD Min-Finding in Heap

```cpp
// Find minimum of 4 children using SIMD
#include <immintrin.h>

int find_min_child_simd(int first_child) {
    // Load 4 deadlines (assuming uint64_t)
    __m256i deadlines = _mm256_loadu_si256(
        (__m256i*)&heap[first_child].deadline
    );
    // For 64-bit comparison, use horizontal min
    // (This is more complex with 64-bit values; 32-bit timestamps would be simpler)
}
```

### 4. Use Radix Structure for Very Dense Deadlines

```cpp
// If deadlines are clustered within a small range,
// use a direct-mapped array of small buckets
struct DenseBucketQueue {
    static constexpr int WINDOW = 1024;  // Active time window

    struct Bucket {
        uint32_t payloads[16];
        uint8_t count = 0;
    };

    Bucket buckets[WINDOW];
    uint64_t base_time = 0;

    void schedule(uint64_t deadline, uint32_t payload) {
        int offset = deadline - base_time;
        if (offset < WINDOW) {
            buckets[offset].payloads[buckets[offset].count++] = payload;
        }
        // Handle overflow with a secondary structure
    }
};
```

---

## Benchmarking

### Workload Design

```cpp
// Without cancel, workload is simpler:
// - Schedule: 50% of ops
// - Advance: 50% of ops (with varying time jumps)

// Deadline distribution matters enormously:
// - Clustered: events within ±100 ticks of current time (favors bucket queues)
// - Spread: events 1-1M ticks in future (favors heaps or hierarchical wheels)
// - Uniform random: events uniformly distributed (stress test)
```

### Measurement

```cpp
uint64_t bench_no_cancel() {
    HeapScheduler sched;
    std::mt19937 rng(42);

    // Pre-generate events
    std::vector<uint64_t> deadlines(1'000'000);
    for (auto& d : deadlines) d = rng() % 1'000'000;

    uint64_t start = __rdtsc();
    uint64_t time = 0;
    for (int i = 0; i < 1'000'000; i++) {
        sched.schedule(time + deadlines[i], i);
        if (i % 2 == 0) {
            time += 100;
            sched.advance(time, [](uint32_t) {});
        }
    }
    uint64_t end = __rdtsc();

    return (end - start) / 1'000'000;
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 350 | 350-700 | > 700 |
| Heap sift overhead | < 50 cycles | 50-150 cycles | > 150 cycles |
| Cache miss rate | < 2% | 2-5% | > 5% |

---

## C++ vs Rust Gap

The gap is enormous here (310 vs 1488 cycles/op). This is likely because:
1. Rust's bounds checking adds overhead on every heap access
2. The top C++ solutions use very aggressive SIMD and compiler-specific tricks
3. Rust's `unsafe` is necessary but adds ergonomic friction
4. Cache alignment control (`alignas`) is more straightforward in C++
