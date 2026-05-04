# Challenge 17: Cross-CCX Ring Buffer

## Leaderboard Reference

| Rank | Name | cycles/op |
|------|------|-----------|
| 1st | kkhan | 310 |
| 2nd | K. Reznik | 682 |
| 3rd | Przemek S. | 930 |

---

## Problem Description

Same interface as Challenge 05 (SPSC Ring Buffer) — but the producer and consumer run on different **Core Complexes (CCXs)** within the same CPU.

This dramatically changes the performance characteristics because cross-CCX communication goes through the L3 cache or Infinity Fabric (on AMD), which has 3-10x higher latency than same-CCX communication.

---

## Core Concepts

### What Is a CCX?

Modern AMD CPUs (Zen architecture) group cores into Core Complexes:

```
┌─────────────────────────────────────────────┐
│                  AMD Ryzen                   │
│                                              │
│  ┌─────────────────┐  ┌─────────────────┐  │
│  │     CCX 0        │  │     CCX 1        │  │
│  │                  │  │                  │  │
│  │  Core 0  Core 1  │  │  Core 4  Core 5  │  │
│  │  Core 2  Core 3  │  │  Core 6  Core 7  │  │
│  │                  │  │                  │  │
│  │  Shared L3 (16MB)│  │  Shared L3 (16MB)│  │
│  └────────┬─────────┘  └────────┬─────────┘  │
│           │      Infinity Fabric      │       │
│           └────────────┬──────────────┘       │
│                        │                      │
└────────────────────────┘

Same CCX latency:    ~40 ns (cache-to-cache)
Cross CCX latency:   ~70-120 ns (through Infinity Fabric)
```

Intel has a similar concept with "core clusters" or "tiles" in recent architectures.

### Why Cross-CCX Is Harder

| Aspect | Same CCX | Cross CCX |
|--------|----------|-----------|
| Cache coherency | L3 shared | L3 NOT shared |
| Atomic latency | ~10-15 cycles | ~50-100 cycles |
| Cache line transfer | L3 → L1 (~10 cycles) | CCX0 L3 → Fabric → CCX1 L3 → L1 (~70+ cycles) |
| Bandwidth | ~100 GB/s (L3) | ~30-50 GB/s (Infinity Fabric) |

Every atomic operation (write_pos, read_pos) must traverse the Infinity Fabric in both directions. This is the fundamental bottleneck.

---

## Optimization Strategies

### Strategy 1: Reduce Cross-CCX Traffic (Batch Publishing)

```cpp
// Instead of publishing every single message via atomic store,
// batch messages and publish once per batch

template<typename T, size_t Capacity>
class BatchedSPSC {
    static constexpr size_t MASK = Capacity - 1;
    static constexpr size_t BATCH_SIZE = 32;  // Publish every 32 messages

    alignas(64) T buffer[Capacity];

    // Shared atomics (cross-CCX traffic)
    alignas(64) std::atomic<size_t> shared_write_pos{0};
    alignas(64) std::atomic<size_t> shared_read_pos{0};

    // Producer local (no cross-CCX traffic)
    alignas(64) size_t local_write = 0;
    size_t cached_read = 0;
    size_t pending_writes = 0;

    // Consumer local
    alignas(64) size_t local_read = 0;
    size_t cached_write = 0;

public:
    bool try_push(const T& item) {
        if (local_write - cached_read >= Capacity) {
            cached_read = shared_read_pos.load(std::memory_order_acquire);
            if (local_write - cached_read >= Capacity) return false;
        }

        buffer[local_write & MASK] = item;
        ++local_write;
        ++pending_writes;

        // Only publish atomically every BATCH_SIZE writes
        if (pending_writes >= BATCH_SIZE) {
            shared_write_pos.store(local_write, std::memory_order_release);
            pending_writes = 0;
        }

        return true;
    }

    void flush() {
        // Force publish remaining messages
        if (pending_writes > 0) {
            shared_write_pos.store(local_write, std::memory_order_release);
            pending_writes = 0;
        }
    }

    bool try_pop(T& item) {
        if (local_read == cached_write) {
            cached_write = shared_write_pos.load(std::memory_order_acquire);
            if (local_read == cached_write) return false;
        }

        item = buffer[local_read & MASK];
        ++local_read;

        // Batch read position updates too
        if ((local_read & (BATCH_SIZE - 1)) == 0) {
            shared_read_pos.store(local_read, std::memory_order_release);
        }

        return true;
    }
};
```

### Strategy 2: Write Combining with Store Buffer

```cpp
// Use a local staging buffer that gets memcpy'd to the ring buffer
// Reduces the number of cross-CCX cache line invalidations

template<typename T, size_t Capacity>
class WriteCombiningSPSC {
    static constexpr size_t MASK = Capacity - 1;
    static constexpr size_t STAGING_SIZE = 64 / sizeof(T);  // One cache line worth

    alignas(64) T buffer[Capacity];
    alignas(64) std::atomic<size_t> shared_write_pos{0};
    alignas(64) std::atomic<size_t> shared_read_pos{0};

    // Producer staging buffer (local cache line, never leaves this CCX)
    alignas(64) T staging[STAGING_SIZE];
    size_t staging_count = 0;
    size_t local_write = 0;
    size_t cached_read = 0;

public:
    void push_staged(const T& item) {
        staging[staging_count++] = item;

        if (staging_count == STAGING_SIZE) {
            flush_staging();
        }
    }

private:
    void flush_staging() {
        // Write entire staging buffer (one cache line) to ring buffer
        for (size_t i = 0; i < staging_count; ++i) {
            buffer[(local_write + i) & MASK] = staging[i];
        }
        local_write += staging_count;
        staging_count = 0;

        // One atomic publish for STAGING_SIZE messages
        shared_write_pos.store(local_write, std::memory_order_release);
    }
};
```

### Strategy 3: Non-Temporal Stores

```cpp
// Use non-temporal (streaming) stores to bypass the cache hierarchy
// The data goes directly to memory or the remote CCX's cache

#include <immintrin.h>

void write_nontemporal(void* dst, const void* src, size_t len) {
    // Write in 64-byte cache line chunks
    const char* s = (const char*)src;
    char* d = (char*)dst;

    for (size_t i = 0; i < len; i += 64) {
        __m256i data0 = _mm256_loadu_si256((__m256i*)(s + i));
        __m256i data1 = _mm256_loadu_si256((__m256i*)(s + i + 32));

        _mm256_stream_si256((__m256i*)(d + i), data0);
        _mm256_stream_si256((__m256i*)(d + i + 32), data1);
    }
    _mm_sfence();  // Ensure stores are globally visible
}
```

### Strategy 4: Adaptive Batching

```cpp
// Dynamically adjust batch size based on queue occupancy
// When queue is nearly empty: flush immediately (latency-sensitive)
// When queue has slack: batch more (throughput-sensitive)

size_t adaptive_batch_size() {
    size_t used = local_write - cached_read;
    size_t free = Capacity - used;

    if (free > Capacity * 3/4) return 64;   // Lots of room: batch aggressively
    if (free > Capacity * 1/2) return 16;   // Moderate room
    if (free > Capacity * 1/4) return 4;    // Getting full
    return 1;                                // Nearly full: publish immediately
}
```

### Strategy 5: Cache Line Padding of Data

```cpp
// Ensure each message occupies exactly one cache line
// Prevents false sharing on adjacent messages

struct alignas(64) PaddedMessage {
    int64_t price;
    int32_t qty;
    int32_t symbol_id;
    uint64_t timestamp;
    char pad[64 - 24];  // Pad to 64 bytes
};

// Now writing one message = dirtying exactly one cache line
// No adjacent messages share a line
```

---

## Prefetch Strategies

```cpp
// Prefetch the next cache line the consumer will read
bool try_pop(T& item) {
    size_t r = local_read;

    // Prefetch next item while processing current
    __builtin_prefetch(&buffer[(r + 1) & MASK], 0, 1);  // Read, low temporal locality

    // Also prefetch from remote CCX's shared_write_pos periodically
    if ((r & 15) == 0) {
        __builtin_prefetch(&shared_write_pos, 0, 0);
    }

    // ... rest of pop logic
}
```

---

## Benchmarking

### Critical: Core Placement

```bash
# Identify CCX topology
lscpu --extended
# or
lstopo

# Pin producer to CCX 0, consumer to CCX 1
taskset -c 0 ./producer &
taskset -c 4 ./consumer &
# (Cores 0-3 = CCX 0, Cores 4-7 = CCX 1 on Zen 2/3)
```

### Measurement

```cpp
void benchmark_cross_ccx() {
    constexpr size_t N = 10'000'000;
    auto ring = std::make_shared<BatchedSPSC<int64_t, 65536>>();

    std::atomic<uint64_t> producer_cycles{0};
    std::atomic<uint64_t> consumer_cycles{0};

    std::thread producer([&]() {
        pin_to_core(0);  // CCX 0
        uint64_t start = __rdtsc();
        for (size_t i = 0; i < N; ++i) {
            while (!ring->try_push(i)) { _mm_pause(); }
        }
        ring->flush();
        producer_cycles = __rdtsc() - start;
    });

    std::thread consumer([&]() {
        pin_to_core(4);  // CCX 1
        int64_t val;
        uint64_t start = __rdtsc();
        for (size_t i = 0; i < N; ++i) {
            while (!ring->try_pop(val)) { _mm_pause(); }
        }
        consumer_cycles = __rdtsc() - start;
    });

    producer.join();
    consumer.join();

    printf("Producer: %lu cycles/op\n", producer_cycles.load() / N);
    printf("Consumer: %lu cycles/op\n", consumer_cycles.load() / N);
}
```

### Key Measurements

```bash
# Cross-CCX traffic
perf stat -e amd_l3/l3_lookup_state.all_l3_req_typs/ ./bench

# Cache coherency events
perf stat -e cache-misses,LLC-load-misses,LLC-store-misses ./bench

# Compare same-CCX vs cross-CCX
echo "=== Same CCX ==="
PRODUCER_CORE=0 CONSUMER_CORE=1 ./bench
echo "=== Cross CCX ==="
PRODUCER_CORE=0 CONSUMER_CORE=4 ./bench
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 350 | 350-700 | > 700 |
| Batch efficiency | > 90% | 70-90% | < 70% |
| Cross-CCX overhead vs same-CCX | < 3x | 3-5x | > 5x |

---

## Common Pitfalls

1. **Not batching atomic updates** — Every atomic op crosses the Infinity Fabric; batch them
2. **Same benchmarking as same-CCX** — Must verify core placement; use `lstopo` or `/proc/cpuinfo`
3. **Too small batch size** — Amortization of cross-CCX latency needs batches of 16-64
4. **Too large batch size** — Increases latency per message; find the sweet spot
5. **Not using non-temporal stores** — Can bypass local cache and write directly to remote CCX
6. **Ignoring NUMA effects** — On multi-socket systems, memory placement matters too
