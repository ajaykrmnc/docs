# Challenge 11: Rolling Counter

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | blumper m. / Malacarne | 14 cycles/op | 23 cycles/op |
| 2nd | Przemek S. / Siddharth Singh | 17 cycles/op | 24 cycles/op |
| 3rd | bdcbqa / Jakub Koszuliński | 18 cycles/op | 24 cycles/op |

---

## Problem Description

Build a high-performance rolling window event counter. Operations:
1. **Update time** — Advance the current timestamp
2. **Add event** — Record an event at the current time
3. **Query count** — Return the total number of events in the sliding window

This is used everywhere in trading: rate limiting, volume tracking, VWAP calculations, message throttling.

---

## Core Concepts

### Sliding Window

```
Time: ──────────────────────────────────────────→
       │          Window (W=10)          │
       │                                 │
Events: ·  ··   · ···  ··  ·  ···  ·    ·
       ↑                                 ↑
    now - W                             now

Count = number of events in [now-W, now]
As time advances, old events "fall off" the left edge.
```

### Why This Is Non-Trivial

- Naive approach: store all events, scan to count → O(n) per query
- Must handle both time updates and event additions efficiently
- Window can contain millions of events

---

## Data Structure Approaches

### Approach 1: Circular Bucket Array (Optimal)

Divide time into fixed-size buckets. Each bucket stores the count of events in that time slice.

```cpp
struct RollingCounter {
    static constexpr int NUM_BUCKETS = 1024;  // Power of 2
    static constexpr int BUCKET_MASK = NUM_BUCKETS - 1;

    int64_t buckets[NUM_BUCKETS] = {};
    int64_t total_count = 0;       // Running total of events in window
    uint64_t current_time = 0;
    uint64_t window_size;          // In time units
    uint64_t bucket_duration;      // Time units per bucket

    RollingCounter(uint64_t window, uint64_t bucket_dur)
        : window_size(window), bucket_duration(bucket_dur) {}

    int bucket_index(uint64_t time) const {
        return (time / bucket_duration) & BUCKET_MASK;
    }

    void advance_time(uint64_t new_time) {
        uint64_t old_bucket = current_time / bucket_duration;
        uint64_t new_bucket = new_time / bucket_duration;

        // Clear buckets that have expired
        uint64_t clear_start = old_bucket + 1;
        uint64_t clear_end = new_bucket;

        // Don't clear more than NUM_BUCKETS (would clear everything)
        if (clear_end - clear_start >= NUM_BUCKETS) {
            memset(buckets, 0, sizeof(buckets));
            total_count = 0;
        } else {
            for (uint64_t b = clear_start; b <= clear_end; ++b) {
                int idx = b & BUCKET_MASK;
                total_count -= buckets[idx];
                buckets[idx] = 0;
            }
        }
        current_time = new_time;
    }

    void add_event() {
        int idx = bucket_index(current_time);
        buckets[idx]++;
        total_count++;
    }

    int64_t count() const {
        return total_count;
    }
};
```

### Approach 2: Packed Bucket Array with SIMD Clear

```cpp
struct SimdRollingCounter {
    static constexpr int NUM_BUCKETS = 2048;
    static constexpr int BUCKET_MASK = NUM_BUCKETS - 1;

    alignas(64) int32_t buckets[NUM_BUCKETS] = {};
    int64_t total = 0;
    uint64_t current_time = 0;
    uint64_t window;

    void advance_and_clear(uint64_t new_time) {
        uint64_t old_slot = current_time & BUCKET_MASK;
        uint64_t new_slot = new_time & BUCKET_MASK;

        if (new_time - current_time >= NUM_BUCKETS) {
            // Clear everything with SIMD
            __m256i zero = _mm256_setzero_si256();
            for (int i = 0; i < NUM_BUCKETS; i += 8) {
                // Accumulate what we're clearing
                __m256i vals = _mm256_load_si256((__m256i*)&buckets[i]);
                _mm256_store_si256((__m256i*)&buckets[i], zero);

                // Sum cleared values (to update total)
                // Using hadd or extract
            }
            total = 0;
        } else {
            // Clear expired buckets
            for (uint64_t t = current_time + 1; t <= new_time; ++t) {
                int idx = t & BUCKET_MASK;
                total -= buckets[idx];
                buckets[idx] = 0;
            }
        }
        current_time = new_time;
    }

    void add() {
        buckets[current_time & BUCKET_MASK]++;
        total++;
    }

    int64_t count() const { return total; }
};
```

### Approach 3: Two-Level Hierarchy

```cpp
// For very large windows with fine granularity
// Use two levels: coarse (summary) + fine (detail)

struct TwoLevelCounter {
    static constexpr int FINE_BUCKETS = 256;
    static constexpr int COARSE_BUCKETS = 64;
    static constexpr int FINE_PER_COARSE = FINE_BUCKETS / COARSE_BUCKETS;

    int32_t fine[FINE_BUCKETS] = {};
    int32_t coarse[COARSE_BUCKETS] = {};  // Sum of FINE_PER_COARSE fine buckets
    int64_t total = 0;

    void add(int fine_idx) {
        fine[fine_idx]++;
        coarse[fine_idx / FINE_PER_COARSE]++;
        total++;
    }

    void clear_range(int start, int end) {
        // Use coarse buckets to quickly identify non-zero regions
        for (int c = start / FINE_PER_COARSE; c <= end / FINE_PER_COARSE; ++c) {
            if (coarse[c] == 0) continue;  // Skip zero coarse bucket

            int f_start = std::max(start, c * FINE_PER_COARSE);
            int f_end = std::min(end, (c + 1) * FINE_PER_COARSE - 1);
            for (int f = f_start; f <= f_end; ++f) {
                total -= fine[f];
                coarse[c] -= fine[f];
                fine[f] = 0;
            }
        }
    }
};
```

---

## Key Optimizations for 14 cycles/op

### 1. Maintain Running Total (Never Recount)

```cpp
// BAD: Recount every query
int64_t count() const {
    int64_t sum = 0;
    for (int i = 0; i < NUM_BUCKETS; ++i) sum += buckets[i];
    return sum;
}
// O(n) per query!

// GOOD: Maintain running total
// Add event: total++
// Clear expired bucket: total -= buckets[idx]
// Query: return total  ← O(1)
```

### 2. Minimize Work on Time Advance

```cpp
// The hot path is: advance time by 1 tick, add event, query count
// If time only advances by 1 each time, we only clear 1 bucket

void advance_by_one() {
    current_time++;
    int idx = current_time & BUCKET_MASK;
    total -= buckets[idx];  // Remove expired bucket
    buckets[idx] = 0;       // Clear it
}
// 3-4 instructions total!
```

### 3. Branchless Bucket Index

```cpp
// Power-of-2 bucket count → bitwise AND
int idx = time & BUCKET_MASK;  // No division, no branch
```

### 4. Aligned Memory

```cpp
// Ensure bucket array is cache-line aligned
alignas(64) int32_t buckets[NUM_BUCKETS];
// Adjacent buckets are in the same cache line → fast sequential access
```

---

## Benchmarking

### Workload

```cpp
// Mixed workload:
// 40% advance_time (usually by 1 tick)
// 40% add_event
// 20% query_count

void benchmark() {
    RollingCounter counter(1000, 1);  // 1000-tick window, 1-tick granularity
    constexpr int N = 10'000'000;

    auto ops = generate_mixed_ops(N);

    uint64_t start = __rdtsc();
    for (auto& op : ops) {
        switch (op.type) {
            case ADVANCE: counter.advance_time(op.new_time); break;
            case ADD:     counter.add_event(); break;
            case QUERY:   volatile auto c = counter.count(); break;
        }
    }
    uint64_t elapsed = __rdtsc() - start;

    printf("%lu cycles/op\n", elapsed / N);
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 16 | 16-30 | > 30 |
| Query cost | O(1) | O(1) | O(n) = bad |
| Cache misses | < 0.1% | 0.1-1% | > 1% |

---

## Common Pitfalls

1. **Storing individual events** — Store counts per bucket, not individual events
2. **Recomputing total on every query** — Maintain a running total
3. **Non-power-of-two bucket count** — Division is expensive; use bitwise AND
4. **Clearing too many buckets on large time jumps** — Use memset or SIMD for bulk clear
5. **Using floating-point time** — Use integer ticks; float introduces rounding issues
