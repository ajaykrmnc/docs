# Challenge 07: String Map

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Stephane D. / Siddharth Singh | 17 cycles/op | 63 cycles/op |
| 2nd | kkhan / Malacarne | 17 cycles/op | 89 cycles/op |
| 3rd | Przemek S. / Abdulkadir Poyraz | 18 cycles/op | 128 cycles/op |

---

## Problem Description

Build a high-performance hash map with string keys (up to 16 characters) and `uint32_t` values. Insert 100K key-value pairs, then look them all up.

The key constraint is that keys are **short strings** (≤ 16 bytes), which opens up powerful optimizations that aren't possible with arbitrary-length strings.

---

## Why Short Strings Change Everything

A 16-byte string fits in:
- A single SSE register (128 bits)
- Two general-purpose 64-bit registers
- A single `__int128` or `struct { uint64_t a, b; }`

This means:
1. **No pointer to string data** — store the key inline
2. **No `strlen()` needed** — compare as two 64-bit integers
3. **Hash in one operation** — Hash 16 bytes directly, no loop
4. **Comparison in 1-2 instructions** — Two 64-bit cmps or one SSE `pcmpeqb`

---

## Data Structure Design

### Approach 1: Open-Addressing Hash Table (Optimal)

```cpp
struct StringMap {
    static constexpr int CAPACITY = 1 << 17;  // 131072 — power of 2, ~75% load for 100K
    static constexpr int MASK = CAPACITY - 1;

    struct Entry {
        uint64_t key_lo;     // First 8 bytes of key
        uint64_t key_hi;     // Last 8 bytes of key
        uint32_t value;
        uint32_t occupied;   // 0 = empty, 1 = occupied
    };

    alignas(64) Entry table[CAPACITY] = {};

    // Fast hash for 16-byte keys
    uint32_t hash(uint64_t lo, uint64_t hi) const {
        // FNV-1a style, or use hardware CRC32
        uint64_t h = lo * 0x9E3779B97F4A7C15ULL;
        h ^= hi * 0x517CC1B727220A95ULL;
        h ^= h >> 32;
        return (uint32_t)h;
    }

    void insert(const char* key, uint32_t value) {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        uint32_t idx = hash(lo, hi) & MASK;

        // Linear probing
        while (table[idx].occupied) {
            if (table[idx].key_lo == lo && table[idx].key_hi == hi) {
                table[idx].value = value;  // Update
                return;
            }
            idx = (idx + 1) & MASK;
        }

        table[idx] = {lo, hi, value, 1};
    }

    uint32_t find(const char* key) const {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        uint32_t idx = hash(lo, hi) & MASK;

        while (table[idx].occupied) {
            if (table[idx].key_lo == lo && table[idx].key_hi == hi) {
                return table[idx].value;
            }
            idx = (idx + 1) & MASK;
        }

        return UINT32_MAX;  // Not found
    }
};
```

### Approach 2: Robin Hood Hashing

Robin Hood hashing reduces worst-case probe length by "stealing" from rich entries:

```cpp
struct RobinHoodMap {
    static constexpr int CAPACITY = 1 << 17;
    static constexpr int MASK = CAPACITY - 1;

    struct Entry {
        uint64_t key_lo, key_hi;
        uint32_t value;
        int8_t probe_distance;  // -1 = empty
    };

    Entry table[CAPACITY];

    RobinHoodMap() {
        for (auto& e : table) e.probe_distance = -1;
    }

    void insert(const char* key, uint32_t value) {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        uint32_t idx = hash(lo, hi) & MASK;
        Entry incoming = {lo, hi, value, 0};

        while (true) {
            if (table[idx].probe_distance < 0) {
                table[idx] = incoming;
                return;
            }
            if (table[idx].key_lo == lo && table[idx].key_hi == hi) {
                table[idx].value = value;
                return;
            }
            // Robin Hood: swap if incoming has traveled further
            if (incoming.probe_distance > table[idx].probe_distance) {
                std::swap(incoming, table[idx]);
            }
            ++incoming.probe_distance;
            idx = (idx + 1) & MASK;
        }
    }
};
```

### Approach 3: Swiss Table / SIMD Probing

Google's Swiss Table (used in `absl::flat_hash_map`) uses SIMD to probe multiple slots simultaneously:

```cpp
struct SwissMap {
    static constexpr int GROUP_SIZE = 16;  // SSE register width
    static constexpr int NUM_GROUPS = 8192;
    static constexpr int CAPACITY = NUM_GROUPS * GROUP_SIZE;

    // Control bytes: one per slot
    // 0x80 = empty, 0xFF = deleted, 0x00-0x7F = H2 hash (top 7 bits of hash)
    alignas(16) int8_t ctrl[CAPACITY];

    struct Slot {
        uint64_t key_lo, key_hi;
        uint32_t value;
    };
    Slot slots[CAPACITY];

    uint32_t find(const char* key) const {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        uint64_t h = hash(lo, hi);
        uint8_t h2 = h >> 57;  // Top 7 bits
        uint32_t group_idx = (h & (NUM_GROUPS - 1)) * GROUP_SIZE;

        // SIMD probe: compare h2 against 16 control bytes simultaneously
        __m128i needle = _mm_set1_epi8(h2);
        __m128i haystack = _mm_load_si128((__m128i*)&ctrl[group_idx]);
        int mask = _mm_movemask_epi8(_mm_cmpeq_epi8(needle, haystack));

        while (mask) {
            int bit = __builtin_ctz(mask);
            int idx = group_idx + bit;
            if (slots[idx].key_lo == lo && slots[idx].key_hi == hi) {
                return slots[idx].value;
            }
            mask &= mask - 1;  // Clear lowest bit
        }

        // Check if group has any empty slots (meaning key doesn't exist)
        int empty_mask = _mm_movemask_epi8(haystack);  // 0x80 bytes
        if (empty_mask) return UINT32_MAX;  // Not found

        // Continue to next group (quadratic probing)
        // ...
    }
};
```

---

## Hash Function Selection

### For 16-byte Keys

```cpp
// Option 1: CRC32 intrinsic (hardware-accelerated on x86)
#include <nmmintrin.h>  // SSE4.2

uint32_t hash_crc32(uint64_t lo, uint64_t hi) {
    uint32_t h = _mm_crc32_u64(0, lo);
    h = _mm_crc32_u64(h, hi);
    return h;
}

// Option 2: wyhash (fast, good distribution)
uint64_t hash_wyhash(uint64_t lo, uint64_t hi) {
    uint64_t a = lo ^ 0x2d358dccaa6c78a5ULL;
    uint64_t b = hi ^ 0x8bb84b93962eacc9ULL;
    __uint128_t r = (__uint128_t)a * b;
    return (uint64_t)(r >> 64) ^ (uint64_t)r;
}

// Option 3: AES-NI based hash (fastest on modern CPUs)
#include <wmmintrin.h>  // AES-NI

uint64_t hash_aes(uint64_t lo, uint64_t hi) {
    __m128i key = _mm_set_epi64x(hi, lo);
    __m128i seed = _mm_set_epi64x(0x7a6d39197e100000ULL, 0x4cf5ad432745937fULL);
    key = _mm_aesenc_si128(key, seed);
    key = _mm_aesenc_si128(key, seed);
    return _mm_extract_epi64(key, 0);
}
```

### Hash Quality Test

```cpp
// Test hash distribution
void test_distribution() {
    constexpr int N = 100000;
    constexpr int BUCKETS = 131072;
    int counts[BUCKETS] = {};

    for (int i = 0; i < N; i++) {
        char key[16];
        snprintf(key, 16, "key_%d", i);
        uint32_t h = hash(key) & (BUCKETS - 1);
        counts[h]++;
    }

    // Calculate chi-squared statistic
    double expected = (double)N / BUCKETS;
    double chi2 = 0;
    for (int i = 0; i < BUCKETS; i++) {
        double diff = counts[i] - expected;
        chi2 += diff * diff / expected;
    }
    printf("Chi-squared: %.2f (ideal: ~%d)\n", chi2, BUCKETS);
}
```

---

## Critical Optimizations

### 1. Inline Key Storage (No Pointers)

```cpp
// BAD: Storing pointer to key string
struct BadEntry {
    const char* key;  // Pointer chase → cache miss
    uint32_t value;
};

// GOOD: Inline key storage
struct GoodEntry {
    uint64_t key_lo, key_hi;  // 16 bytes inline
    uint32_t value;
};
// Key comparison is two integer comparisons — no function call, no loop
```

### 2. Compact Entry Layout

```cpp
// 24 bytes per entry: key (16) + value (4) + metadata (4)
// 64 / 24 ≈ 2.6 entries per cache line
// With padding for alignment: 32 bytes → 2 entries per cache line

struct __attribute__((packed)) CompactEntry {
    uint64_t key_lo;    // 8 bytes
    uint64_t key_hi;    // 8 bytes
    uint32_t value;     // 4 bytes
    uint32_t hash_bits; // 4 bytes (store partial hash to avoid rehashing)
};
// Exactly 24 bytes — but misaligned access on subsequent entries
// Better: pad to 32 bytes for alignment

struct AlignedEntry {
    uint64_t key_lo;
    uint64_t key_hi;
    uint32_t value;
    uint32_t meta;      // Partial hash or empty flag
};
static_assert(sizeof(AlignedEntry) == 32);
// 2 entries per cache line — excellent locality
```

### 3. Prefetching During Probe

```cpp
uint32_t find_with_prefetch(const char* key) {
    uint64_t lo, hi;
    memcpy(&lo, key, 8);
    memcpy(&hi, key + 8, 8);

    uint32_t idx = hash(lo, hi) & MASK;

    // Prefetch the entry we're about to check
    __builtin_prefetch(&table[idx], 0, 3);

    while (table[idx].occupied) {
        // Prefetch next entry while checking current
        __builtin_prefetch(&table[(idx + 1) & MASK], 0, 3);

        if (table[idx].key_lo == lo && table[idx].key_hi == hi) {
            return table[idx].value;
        }
        idx = (idx + 1) & MASK;
    }
    return UINT32_MAX;
}
```

### 4. Load Factor Tuning

```
Load factor = entries / capacity

0.50 → avg 1.5 probes, best cache use, 2x memory
0.70 → avg 2.2 probes, good balance
0.80 → avg 3.0 probes, starts degrading
0.90 → avg 5.5 probes, poor performance

For 100K entries:
  0.50 load → 200K capacity → 6.4 MB at 32 bytes/entry
  0.70 load → 143K capacity → 4.6 MB (exceeds L1/L2 for some CPUs)

Sweet spot: 0.625 load (160K capacity for 100K entries)
```

---

## Benchmarking

### Setup

```cpp
void benchmark_string_map() {
    StringMap map;

    // Generate 100K unique keys
    std::vector<std::pair<std::string, uint32_t>> data;
    for (int i = 0; i < 100000; ++i) {
        char key[17] = {};
        snprintf(key, 17, "SYM_%010d", i);
        data.push_back({std::string(key, 16), (uint32_t)i});
    }

    // Insert phase
    uint64_t t0 = __rdtsc();
    for (auto& [k, v] : data) {
        map.insert(k.c_str(), v);
    }
    uint64_t insert_cycles = (__rdtsc() - t0) / data.size();

    // Lookup phase
    t0 = __rdtsc();
    for (auto& [k, v] : data) {
        uint32_t result = map.find(k.c_str());
        assert(result == v);
    }
    uint64_t lookup_cycles = (__rdtsc() - t0) / data.size();

    printf("Insert: %lu cycles/op\n", insert_cycles);
    printf("Lookup: %lu cycles/op\n", lookup_cycles);
    printf("Average: %lu cycles/op\n", (insert_cycles + lookup_cycles) / 2);
}
```

### Profiling

```bash
# Compare hash implementations
perf stat -e cycles,instructions,cache-misses ./bench_fnv
perf stat -e cycles,instructions,cache-misses ./bench_crc32
perf stat -e cycles,instructions,cache-misses ./bench_aes

# Probe length distribution
# Add counters in code to track probe lengths
# Ideal: 80%+ of lookups find key in 1-2 probes
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 20 | 20-40 | > 40 |
| Avg probe length | < 1.5 | 1.5-3.0 | > 3.0 |
| Hash throughput | > 5 GB/s | 2-5 GB/s | < 2 GB/s |

---

## Common Pitfalls

1. **Using `std::unordered_map`** — Dynamic allocation, pointer chasing, poor cache behavior
2. **Storing keys as `std::string`** — Heap allocation for each key; use inline 16-byte storage
3. **`strcmp` for comparison** — Function call overhead; compare as two `uint64_t`
4. **Poor hash function** — Leads to clustering and long probe chains
5. **Non-power-of-2 table size** — Division for modulo is expensive; use bitwise AND
6. **Ignoring load factor** — Too high → long probes; too low → wasted cache
