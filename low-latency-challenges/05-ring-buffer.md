# Challenge 05: Ring Buffer (SPSC)

## Leaderboard Reference

| Rank | Name | cycles/op |
|------|------|-----------|
| 1st | kkhan | 155 |
| 2nd | K. Reznik | 248 |
| 3rd | Andrey S. | 279 |

---

## Problem Description

Build a high-performance SPSC (Single-Producer Single-Consumer) ring buffer for passing market data messages between threads. One thread writes (producer), one thread reads (consumer), with no locks.

This is the fundamental building block of every low-latency trading system's internal communication.

---

## Core Concepts

### Ring Buffer Anatomy

```
             write_pos
                ↓
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ X │ X │ . │ . │ . │ . │ X │ X │   X = data, . = empty
└───┴───┴───┴───┴───┴───┴───┴───┘
                          ↑
                       read_pos

Capacity: 8 slots
Used: 4 (elements between read_pos and write_pos)
Free: 4

Producer writes at write_pos, advances it.
Consumer reads at read_pos, advances it.
```

### Why Lock-Free SPSC Is Possible

With exactly one producer and one consumer:
- Producer only writes `write_pos`
- Consumer only writes `read_pos`
- Neither modifies the other's position → no locks needed
- Only need proper **memory ordering** to ensure data visibility

---

## Implementation

### Version 1: Baseline Lock-Free SPSC

```cpp
#include <atomic>
#include <cstddef>
#include <cstring>

template<typename T, size_t Capacity>
class SPSCRingBuffer {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of 2");
    static constexpr size_t MASK = Capacity - 1;

    alignas(64) std::atomic<size_t> write_pos{0};
    alignas(64) std::atomic<size_t> read_pos{0};
    alignas(64) T buffer[Capacity];

public:
    bool try_push(const T& item) {
        size_t w = write_pos.load(std::memory_order_relaxed);
        size_t r = read_pos.load(std::memory_order_acquire);

        if (w - r >= Capacity) return false;  // Full

        buffer[w & MASK] = item;
        write_pos.store(w + 1, std::memory_order_release);
        return true;
    }

    bool try_pop(T& item) {
        size_t r = read_pos.load(std::memory_order_relaxed);
        size_t w = write_pos.load(std::memory_order_acquire);

        if (r == w) return false;  // Empty

        item = buffer[r & MASK];
        read_pos.store(r + 1, std::memory_order_release);
        return true;
    }
};
```

### Version 2: Optimized — Cached Positions

```cpp
// The main bottleneck in V1 is the cross-thread atomic load of the other
// thread's position. This causes a cache line transfer between cores.
// Solution: cache the other thread's position locally and only refresh
// when the cached value says we can't proceed.

template<typename T, size_t Capacity>
class OptimizedSPSC {
    static_assert((Capacity & (Capacity - 1)) == 0);
    static constexpr size_t MASK = Capacity - 1;

    // Producer's cache line
    struct alignas(64) ProducerState {
        size_t write_pos = 0;
        size_t cached_read_pos = 0;   // Producer's cached copy of read_pos
    } producer;

    // Consumer's cache line
    struct alignas(64) ConsumerState {
        size_t read_pos = 0;
        size_t cached_write_pos = 0;  // Consumer's cached copy of write_pos
    } consumer;

    // Shared atomic positions (separate cache lines)
    alignas(64) std::atomic<size_t> shared_write_pos{0};
    alignas(64) std::atomic<size_t> shared_read_pos{0};

    // Data buffer
    alignas(64) T buffer[Capacity];

public:
    bool try_push(const T& item) {
        size_t w = producer.write_pos;

        // Check if full using cached read position
        if (w - producer.cached_read_pos >= Capacity) {
            // Refresh cache
            producer.cached_read_pos = shared_read_pos.load(std::memory_order_acquire);
            if (w - producer.cached_read_pos >= Capacity) {
                return false;  // Actually full
            }
        }

        buffer[w & MASK] = item;
        shared_write_pos.store(w + 1, std::memory_order_release);
        producer.write_pos = w + 1;
        return true;
    }

    bool try_pop(T& item) {
        size_t r = consumer.read_pos;

        // Check if empty using cached write position
        if (r == consumer.cached_write_pos) {
            // Refresh cache
            consumer.cached_write_pos = shared_write_pos.load(std::memory_order_acquire);
            if (r == consumer.cached_write_pos) {
                return false;  // Actually empty
            }
        }

        item = buffer[r & MASK];
        shared_read_pos.store(r + 1, std::memory_order_release);
        consumer.read_pos = r + 1;
        return true;
    }
};
```

### Version 3: Batch Operations (Highest Throughput)

```cpp
template<typename T, size_t Capacity>
class BatchSPSC {
    static constexpr size_t MASK = Capacity - 1;

    alignas(64) std::atomic<size_t> shared_write_pos{0};
    alignas(64) std::atomic<size_t> shared_read_pos{0};
    alignas(64) T buffer[Capacity];

    // Producer-local
    alignas(64) size_t local_write = 0;
    size_t cached_read = 0;

    // Consumer-local
    alignas(64) size_t local_read = 0;
    size_t cached_write = 0;

public:
    // Push up to `count` items, return number pushed
    size_t push_batch(const T* items, size_t count) {
        size_t available = Capacity - (local_write - cached_read);
        if (available < count) {
            cached_read = shared_read_pos.load(std::memory_order_acquire);
            available = Capacity - (local_write - cached_read);
        }
        count = std::min(count, available);

        for (size_t i = 0; i < count; ++i) {
            buffer[(local_write + i) & MASK] = items[i];
        }

        local_write += count;
        shared_write_pos.store(local_write, std::memory_order_release);
        return count;
    }

    size_t pop_batch(T* items, size_t max_count) {
        size_t available = cached_write - local_read;
        if (available == 0) {
            cached_write = shared_write_pos.load(std::memory_order_acquire);
            available = cached_write - local_read;
        }
        size_t count = std::min(max_count, available);

        for (size_t i = 0; i < count; ++i) {
            items[i] = buffer[(local_read + i) & MASK];
        }

        local_read += count;
        shared_read_pos.store(local_read, std::memory_order_release);
        return count;
    }
};
```

---

## Critical Optimization Details

### 1. False Sharing Prevention

```cpp
// BAD: write_pos and read_pos on same cache line
struct BadLayout {
    std::atomic<size_t> write_pos;  // Same 64-byte cache line!
    std::atomic<size_t> read_pos;   // Every write by producer invalidates consumer's cache
};

// GOOD: Separate cache lines
struct GoodLayout {
    alignas(64) std::atomic<size_t> write_pos;  // Producer's cache line
    char pad1[64 - sizeof(std::atomic<size_t>)];
    alignas(64) std::atomic<size_t> read_pos;   // Consumer's cache line
    char pad2[64 - sizeof(std::atomic<size_t>)];
};
```

### 2. Memory Ordering (The Key to Performance)

```
Memory ordering strength (weakest to strongest):

relaxed < acquire/release < seq_cst

For SPSC:
- Producer writes data, then releases write_pos → consumer acquires write_pos, sees data
- This is the classic acquire/release pattern
- NEVER use seq_cst (sequential consistency) — it adds full memory fences

Key rules:
1. Store to shared position: memory_order_release
2. Load of other thread's position: memory_order_acquire
3. Load of own position: memory_order_relaxed (only this thread modifies it)
```

### 3. Power-of-Two Capacity

```cpp
// Modulo with power-of-2 is a single AND instruction
size_t index = pos & MASK;  // 1 cycle

// vs arbitrary size requires actual division
size_t index = pos % capacity;  // 20-30 cycles on x86!
```

### 4. Prefetching the Next Cache Line

```cpp
bool try_push(const T& item) {
    size_t w = producer.write_pos;
    // Prefetch the next buffer slot we'll write to
    __builtin_prefetch(&buffer[(w + 1) & MASK], 1, 3);  // write, high temporal locality

    // ... rest of push logic
}

bool try_pop(T& item) {
    size_t r = consumer.read_pos;
    // Prefetch the next slot we'll read
    __builtin_prefetch(&buffer[(r + 1) & MASK], 0, 3);  // read, high temporal locality

    // ... rest of pop logic
}
```

### 5. Huge Pages for Large Buffers

```cpp
// For buffers > 2MB, use huge pages to reduce TLB misses
#include <sys/mman.h>

void* alloc_huge(size_t size) {
    void* ptr = mmap(nullptr, size,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                     -1, 0);
    if (ptr == MAP_FAILED) {
        // Fallback to regular pages
        ptr = mmap(nullptr, size, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    }
    return ptr;
}
```

---

## Benchmarking

### Setup

```cpp
#include <thread>
#include <x86intrin.h>

void benchmark_spsc() {
    constexpr size_t BUF_SIZE = 65536;
    constexpr size_t NUM_OPS = 10'000'000;

    OptimizedSPSC<int64_t, BUF_SIZE> ring;
    std::atomic<uint64_t> producer_cycles{0};
    std::atomic<uint64_t> consumer_cycles{0};

    // Pin threads to specific cores
    std::thread producer([&]() {
        pin_to_core(0);
        uint64_t start = __rdtsc();
        for (size_t i = 0; i < NUM_OPS; ++i) {
            while (!ring.try_push(i)) {}  // Spin until push succeeds
        }
        producer_cycles = __rdtsc() - start;
    });

    std::thread consumer([&]() {
        pin_to_core(1);
        int64_t val;
        uint64_t start = __rdtsc();
        for (size_t i = 0; i < NUM_OPS; ++i) {
            while (!ring.try_pop(val)) {}  // Spin until pop succeeds
        }
        consumer_cycles = __rdtsc() - start;
    });

    producer.join();
    consumer.join();

    printf("Producer: %lu cycles/op\n", producer_cycles.load() / NUM_OPS);
    printf("Consumer: %lu cycles/op\n", consumer_cycles.load() / NUM_OPS);
    printf("Round-trip: %lu cycles/op\n",
           std::max(producer_cycles.load(), consumer_cycles.load()) / NUM_OPS);
}

void pin_to_core(int core) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
}
```

### What to Measure

1. **Throughput**: ops/second or cycles/op for sustained push+pop
2. **Latency**: Time from push to pop (producer-consumer delay)
3. **Cache coherency cost**: L1 miss rate (indicates cross-core traffic)

### Core Placement Matters

```
Same CCX (Core Complex):    ~50-80 cycles round-trip
Cross CCX, same socket:     ~150-300 cycles round-trip
Cross socket (NUMA):        ~300-600 cycles round-trip

Always benchmark with specific core pinning!
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op (same CCX) | < 180 | 180-300 | > 300 |
| Cache miss rate | < 5% | 5-15% | > 15% |
| Batch throughput (msgs/sec) | > 100M | 50-100M | < 50M |

---

## Common Pitfalls

1. **Using `seq_cst` ordering** — Overkill for SPSC; use acquire/release
2. **Not aligning to cache lines** — False sharing kills performance
3. **Non-power-of-two capacity** — Division is expensive; use bitwise AND
4. **Reading other thread's position on every op** — Cache the position locally
5. **Not pinning threads to cores** — OS scheduler migration destroys cache locality
6. **Using `std::queue` with a mutex** — Orders of magnitude slower than lock-free SPSC
7. **Spinning with `pause` instruction missing** — On x86, `_mm_pause()` in spin loops reduces power and improves latency
