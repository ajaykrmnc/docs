# Challenge 06: Seqlock

## Leaderboard Reference

| Rank | Name | cycles/op |
|------|------|-----------|
| 1st | Suntae L. | 352 |
| 2nd | kkhan | 353 |
| 3rd | Noah | 354 |

---

## Problem Description

Build a high-performance sequence lock (seqlock) that allows **one writer** and **multiple readers** to share data without blocking the writer.

A seqlock is a reader-writer synchronization primitive used extensively in the Linux kernel and HFT systems for sharing rapidly updated data (e.g., market data snapshots, time-of-day).

---

## Core Concepts

### How a Seqlock Works

```
Writer                                  Reader
  │                                       │
  ├── seq++ (odd = write in progress)     │
  ├── write data                          │
  ├── seq++ (even = write complete)       │
  │                                       ├── s1 = seq (must be even to start)
  │                                       ├── read data
  │                                       ├── s2 = seq
  │                                       ├── if s1 == s2: data is valid
  │                                       └── else: retry (writer was active)
```

**Key properties:**
- Writer never blocks (no readers can stall the writer)
- Readers may retry if they detect a concurrent write (optimistic concurrency)
- Zero contention on the write path — writer just increments a sequence number
- Best when writes are very fast (< a few hundred nanoseconds)

### Seqlock vs Read-Write Lock

| Property | Seqlock | RWLock |
|----------|---------|--------|
| Writer blocks? | Never | If readers hold lock |
| Reader blocks? | Never (retries) | If writer holds lock |
| Starvation | Readers may starve | Writers may starve |
| Best for | Frequent writes, short data | Infrequent writes, long reads |
| Overhead | 2 atomic ops per write | Heavy (mutex acquire/release) |

---

## Implementation

### Version 1: Basic Seqlock

```cpp
#include <atomic>
#include <cstring>

class Seqlock {
    alignas(64) std::atomic<uint32_t> seq{0};
    // Payload — must be trivially copyable
    struct Data {
        int64_t price;
        int64_t quantity;
        uint64_t timestamp;
    };
    alignas(64) Data data{};

public:
    void write(const Data& new_data) {
        uint32_t s = seq.load(std::memory_order_relaxed);
        seq.store(s + 1, std::memory_order_release);       // Odd → writing
        std::atomic_thread_fence(std::memory_order_release);

        data = new_data;  // Non-atomic write

        seq.store(s + 2, std::memory_order_release);       // Even → done
    }

    Data read() const {
        Data result;
        uint32_t s1, s2;
        do {
            s1 = seq.load(std::memory_order_acquire);
            if (s1 & 1) continue;  // Writer active, retry immediately

            std::atomic_thread_fence(std::memory_order_acquire);
            result = data;  // Optimistic read
            std::atomic_thread_fence(std::memory_order_acquire);

            s2 = seq.load(std::memory_order_acquire);
        } while (s1 != s2);  // Mismatch → data was modified during read

        return result;
    }
};
```

### Version 2: Optimized Seqlock (What Top Competitors Use)

```cpp
class OptimizedSeqlock {
    // Keep seq and data on SAME cache line if data is small enough
    // This way, writer only dirties one cache line

    struct alignas(64) {
        uint32_t seq = 0;
        // Pad to specific offset for data alignment
        char pad[4];
        int64_t price;
        int64_t quantity;
        uint64_t timestamp;
    } state;

public:
    void write(int64_t price, int64_t qty, uint64_t ts) {
        // Use a compiler barrier + store, not full atomic RMW
        auto s = state.seq;
        // Compiler barrier to prevent reordering past seq store
        asm volatile("" ::: "memory");
        state.seq = s + 1;
        // Ensure seq write is visible before data writes
        asm volatile("" ::: "memory");

        state.price = price;
        state.quantity = qty;
        state.timestamp = ts;

        // Ensure data writes complete before seq update
        asm volatile("" ::: "memory");
        state.seq = s + 2;
    }

    struct ReadResult {
        int64_t price;
        int64_t qty;
        uint64_t ts;
    };

    ReadResult read() const {
        ReadResult r;
        uint32_t s1, s2;
        do {
            s1 = state.seq;
            asm volatile("" ::: "memory");

            // Skip if write in progress
            if (__builtin_expect(s1 & 1, 0)) {
                _mm_pause();
                continue;
            }

            r.price = state.price;
            r.qty = state.quantity;
            r.ts = state.timestamp;

            asm volatile("" ::: "memory");
            s2 = state.seq;
        } while (__builtin_expect(s1 != s2, 0));

        return r;
    }
};
```

### Version 3: Cache-Line Aligned with Separate Sequence

```cpp
// For larger payloads that don't fit in one cache line,
// use double-buffering with sequence-based selection

template<typename T>
class DoubleBufferSeqlock {
    static_assert(std::is_trivially_copyable_v<T>);

    alignas(64) std::atomic<uint64_t> seq{0};
    alignas(64) T buffers[2];  // Double buffer

public:
    void write(const T& value) {
        uint64_t s = seq.load(std::memory_order_relaxed);
        int write_idx = ((s + 1) / 2) & 1;  // Alternate between buffers

        seq.store(s + 1, std::memory_order_release);  // Mark writing
        buffers[write_idx] = value;                    // Write to inactive buffer
        seq.store(s + 2, std::memory_order_release);  // Mark done
    }

    T read() const {
        T result;
        uint64_t s1, s2;
        do {
            s1 = seq.load(std::memory_order_acquire);
            if (s1 & 1) { _mm_pause(); continue; }

            int read_idx = (s1 / 2) & 1;
            result = buffers[read_idx];

            s2 = seq.load(std::memory_order_acquire);
        } while (s1 != s2);
        return result;
    }
};
```

---

## Deep Dive: Memory Ordering

### Why This Ordering Matters

```
CPU 0 (Writer)                    CPU 1 (Reader)
─────────────────                 ─────────────────
seq = 1   ──release──→            s1 = seq  ←──acquire──
price = 100                       p = price
qty = 200                         q = qty
seq = 2   ──release──→            s2 = seq  ←──acquire──

The release on the writer side ensures:
  - All data writes (price, qty) are visible BEFORE seq update

The acquire on the reader side ensures:
  - seq is read BEFORE data (we see the seq that was published before the data)

If s1 == s2 == 2 (even), we know no write happened between our reads.
```

### x86 Specifics

On x86, the memory model is already quite strong (TSO — Total Store Order):
- All stores are automatically ordered (no store-store reordering)
- All loads are automatically ordered after loads
- Only store→load can be reordered

This means on x86, `acquire/release` on atomic loads/stores compile to plain loads/stores. The compiler barriers (`asm volatile("" ::: "memory")`) are enough to prevent compiler reordering.

On ARM/RISC-V, explicit memory barriers are needed (the atomics provide them).

---

## Optimization Techniques

### 1. Single Cache Line Optimization

```cpp
// If your data fits in < 56 bytes (64 - 8 for seq),
// put everything on ONE cache line
// Writer dirties one line, reader loads one line

struct alignas(64) SingleLineSeqlock {
    uint32_t seq;
    uint32_t pad;
    // Your data here — up to 56 bytes
    int64_t field1;
    int64_t field2;
    int64_t field3;
    int64_t field4;
    int64_t field5;
    int64_t field6;
    int64_t field7;
};
static_assert(sizeof(SingleLineSeqlock) == 64);
```

### 2. _mm_pause() in Retry Loop

```cpp
// When reader detects write-in-progress, don't busy-spin at full speed
// _mm_pause() hints the CPU to save power and avoid pipeline issues

do {
    s1 = seq.load(std::memory_order_acquire);
    if (s1 & 1) {
        _mm_pause();  // ~40 cycles on modern Intel — lets writer finish
        continue;
    }
    // ... read data ...
} while (s1 != s2);
```

### 3. Avoid Torn Reads on Non-Atomic Data

```cpp
// On x86, aligned 8-byte loads/stores are atomic
// But structs larger than 8 bytes can be torn
// The seqlock protocol handles this — a torn read will be detected
// by s1 != s2 and retried

// Ensure data members are naturally aligned
struct __attribute__((packed)) BadData {
    char type;        // offset 0
    int64_t price;    // offset 1 — MISALIGNED! Torn read possible
};

struct GoodData {
    int64_t price;    // offset 0 — aligned
    int64_t qty;      // offset 8 — aligned
    char type;        // offset 16
    // 7 bytes padding
};
```

### 4. Read-Side Compiler Barrier Placement

```cpp
// CRITICAL: The compiler must not reorder reads past the sequence checks
// Use asm volatile("" ::: "memory") or std::atomic_thread_fence

// WITHOUT barrier (broken — compiler may move data read after s2 read):
s1 = seq;
data = read_data();  // Compiler might move this after s2 load!
s2 = seq;

// WITH barrier (correct):
s1 = seq;
asm volatile("" ::: "memory");  // Compiler cannot move reads past this
data = read_data();
asm volatile("" ::: "memory");  // Compiler cannot move reads past this
s2 = seq;
```

---

## Benchmarking

### Test Setup

```cpp
#include <thread>
#include <vector>
#include <x86intrin.h>

void benchmark_seqlock() {
    OptimizedSeqlock lock;
    constexpr int NUM_OPS = 10'000'000;
    constexpr int NUM_READERS = 4;

    // Writer thread
    std::thread writer([&]() {
        pin_to_core(0);
        uint64_t start = __rdtsc();
        for (int i = 0; i < NUM_OPS; ++i) {
            lock.write(i * 100, i * 10, i);
        }
        uint64_t elapsed = __rdtsc() - start;
        printf("Write: %lu cycles/op\n", elapsed / NUM_OPS);
    });

    // Reader threads
    std::vector<std::thread> readers;
    for (int r = 0; r < NUM_READERS; ++r) {
        readers.emplace_back([&, r]() {
            pin_to_core(r + 1);
            uint64_t retries = 0;
            uint64_t start = __rdtsc();
            for (int i = 0; i < NUM_OPS; ++i) {
                auto data = lock.read();
                (void)data;
            }
            uint64_t elapsed = __rdtsc() - start;
            printf("Reader %d: %lu cycles/op\n", r, elapsed / NUM_OPS);
        });
    }

    writer.join();
    for (auto& t : readers) t.join();
}
```

### Key Metrics

```bash
# Cache coherency traffic
perf stat -e L1-dcache-load-misses,LLC-load-misses ./seqlock_bench

# Retry rate (tells you how often readers collide with writers)
# Track this in code: count iterations of the do-while loop

# Memory fence overhead
perf stat -e stalled-cycles-frontend,stalled-cycles-backend ./seqlock_bench
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op (combined) | < 360 | 360-500 | > 500 |
| Reader retry rate | < 1% | 1-5% | > 5% |
| Write latency | < 20 cycles | 20-50 cycles | > 50 cycles |

---

## Real-World Applications in HFT

1. **Market data dissemination** — Writer updates NBBO (National Best Bid/Offer), readers query it
2. **Position tracking** — One thread updates P&L, many threads read it
3. **Clock sharing** — One thread reads hardware clock, others get the cached value
4. **Risk limits** — Risk engine writes limits, strategy threads check against them

---

## Common Pitfalls

1. **Using `std::mutex` or `std::shared_mutex`** — Too heavy for this use case
2. **Forgetting compiler barriers** — Data reads/writes may be reordered
3. **Data spanning multiple cache lines** — Increases retry rate; use double-buffering
4. **Not checking for odd sequence on entry** — Wastes time reading data that will be invalid
5. **Using `seq_cst` everywhere** — Acquire/release is sufficient; seq_cst adds mfence on x86
