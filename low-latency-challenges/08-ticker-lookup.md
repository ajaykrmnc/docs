# Challenge 08: Ticker Lookup

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Michael Ostapenko / Malacarne | 10 cycles/op | 16 cycles/op |
| 2nd | Fatih Karaoğlu / Siddharth Singh | 13 cycles/op | 17 cycles/op |
| 3rd | blumper m. / Abdulkadir Poyraz | 14 cycles/op | 18 cycles/op |

---

## Problem Description

Build the fastest possible ticker symbol lookup table. `build()` is called once (not timed), then `lookup()` is called millions of times (timed).

Key insight: **build time doesn't matter** — you can spend arbitrary time constructing a perfect data structure, then amortize over millions of lookups.

---

## Why This Is Different from String Map

| Aspect | String Map (Ch. 07) | Ticker Lookup (Ch. 08) |
|--------|---------------------|----------------------|
| Insert + Lookup | Both timed | Only lookup timed |
| Build time | Matters | Unlimited |
| Key set | Dynamic | Static (known at build) |
| Optimization | Balance insert/lookup | Maximize lookup speed |
| Best approach | Open-addressing hash | Perfect hash / direct mapping |

---

## Optimal Approaches

### Approach 1: Minimal Perfect Hash Function (MPH)

A perfect hash function maps N keys to N unique integers with no collisions. This gives guaranteed O(1) lookup with no probing.

```cpp
// Build phase: construct a perfect hash function
// Lookup phase: single hash + single array access

struct PerfectHashLookup {
    // CHD (Compress, Hash, Displace) algorithm
    struct PHF {
        uint32_t seed;
        uint32_t displacement[NUM_BUCKETS];
        uint32_t slots[NUM_KEYS];  // Maps perfect hash → value
    };

    PHF phf;

    void build(const char keys[][16], const uint32_t* values, int n) {
        // Offline construction of perfect hash
        // 1. Hash each key to a bucket
        // 2. For each bucket, find a displacement that maps all keys
        //    in that bucket to unique slots
        // 3. Store displacements and values
        // This can take seconds — doesn't matter
        construct_phf(keys, values, n, phf);
    }

    uint32_t lookup(const char* key) const {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        // Two-level hash:
        uint32_t bucket = hash1(lo, hi, phf.seed) % NUM_BUCKETS;
        uint32_t slot = hash2(lo, hi, phf.displacement[bucket]) % NUM_KEYS;

        return phf.slots[slot];
    }
};
```

### Approach 2: Cuckoo Hash Table (Static Build)

Build a cuckoo hash table offline with two hash functions. Lookup checks exactly 2 positions:

```cpp
struct CuckooLookup {
    static constexpr int TABLE_SIZE = 1 << 17;  // 2x the number of keys
    static constexpr int MASK = TABLE_SIZE - 1;

    struct Entry {
        uint64_t key_lo, key_hi;
        uint32_t value;
        bool occupied;
    };

    Entry table1[TABLE_SIZE] = {};
    Entry table2[TABLE_SIZE] = {};
    uint64_t seed1, seed2;

    void build(const char keys[][16], const uint32_t* values, int n) {
        // Try random seeds until successful placement
        // Can take many attempts — doesn't matter
        while (true) {
            seed1 = random_seed();
            seed2 = random_seed();
            if (try_build(keys, values, n)) break;
        }
    }

    uint32_t lookup(const char* key) const {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        // Check position 1
        uint32_t h1 = hash(lo, hi, seed1) & MASK;
        if (table1[h1].key_lo == lo && table1[h1].key_hi == hi) {
            return table1[h1].value;
        }

        // Check position 2
        uint32_t h2 = hash(lo, hi, seed2) & MASK;
        return table2[h2].value;  // Must be here (no third option)
    }
};
```

### Approach 3: Frozen Hash Map with Precomputed Probes

```cpp
// Build an open-addressing table offline, optimized for lookup:
// - Minimize average probe distance
// - Place frequently-looked-up keys at their ideal position
// - Use the unlimited build time to find optimal placement

struct FrozenMap {
    static constexpr int CAPACITY = 1 << 14;  // Tight fit to reduce cache footprint
    static constexpr int MASK = CAPACITY - 1;

    struct Entry {
        uint64_t key_lo, key_hi;
        uint32_t value;
    };

    alignas(64) Entry table[CAPACITY];

    void build(const char keys[][16], const uint32_t* values, int n) {
        // Sort keys by hash to minimize probe length
        // Try multiple hash seeds, pick the one with lowest max probe
        uint64_t best_seed = 0;
        int best_max_probe = INT_MAX;

        for (int attempt = 0; attempt < 100000; ++attempt) {
            uint64_t seed = random_seed();
            int max_probe = simulate_insertion(keys, n, seed);
            if (max_probe < best_max_probe) {
                best_max_probe = max_probe;
                best_seed = seed;
            }
        }

        // Build with best seed
        build_with_seed(keys, values, n, best_seed);
    }

    uint32_t lookup(const char* key) const {
        uint64_t lo, hi;
        memcpy(&lo, key, 8);
        memcpy(&hi, key + 8, 8);

        uint32_t idx = hash(lo, hi) & MASK;

        // Most lookups hit on first probe (thanks to offline optimization)
        if (__builtin_expect(table[idx].key_lo == lo && table[idx].key_hi == hi, 1)) {
            return table[idx].value;
        }

        // Linear probe (rare path)
        do {
            idx = (idx + 1) & MASK;
        } while (table[idx].key_lo != lo || table[idx].key_hi != hi);

        return table[idx].value;
    }
};
```

### Approach 4: Direct Computed Index (If Ticker Set Is Small)

```cpp
// For common stock tickers (< 10000 symbols), we can sometimes find
// a direct mapping function that maps each ticker to a unique index
// without any hash table at all

// Example: For 4-character uppercase tickers
// Each char has 26 possible values → 26^4 = 456,976 possible tickers
// If we only have 5000 actual tickers, use a bitmap + ranked index

struct DirectLookup {
    // Map 4-char ticker to 26-base number
    uint32_t values[456976];  // ~1.7 MB — fits in L2 cache

    void build(const char keys[][16], const uint32_t* vals, int n) {
        memset(values, 0xFF, sizeof(values));
        for (int i = 0; i < n; ++i) {
            uint32_t idx = encode(keys[i]);
            values[idx] = vals[i];
        }
    }

    uint32_t lookup(const char* key) const {
        return values[encode(key)];  // Single array access — ~4 cycles
    }

private:
    static uint32_t encode(const char* s) {
        return (s[0] - 'A') * 17576 + (s[1] - 'A') * 676 +
               (s[2] - 'A') * 26 + (s[3] - 'A');
    }
};
```

---

## The 10-Cycle Barrier

To achieve 10 cycles/op, the lookup must consist of:
1. Key encoding/hashing: ~3-5 cycles
2. Array access: ~3-4 cycles (L1 cache hit)
3. Comparison + return: ~2-3 cycles

This means:
- **Zero probing** — Every key must be found on the first try
- **L1 cache** — The entire table must fit in L1 (32-64 KB typically)
- **No branch mispredictions** — Branchless comparison

### Fitting in L1 Cache

```
L1 data cache: typically 32 KB (some CPUs have 48 KB)

If each entry is 24 bytes (16 key + 4 value + 4 pad):
  32768 / 24 = 1365 entries max in L1

For 100K keys, this is impossible → must use a compact representation
or accept L2 latency (~12 cycles on modern CPUs)

Alternative: Store only values (4 bytes each) if hash is perfect:
  32768 / 4 = 8192 entries in L1
  → Perfect hash to 8192 slots for keys that fit the access pattern
```

### AES-NI Hash (Fastest on x86)

```cpp
#include <wmmintrin.h>

uint32_t hash_aes_fast(uint64_t lo, uint64_t hi) {
    __m128i key = _mm_set_epi64x(hi, lo);
    __m128i seed = _mm_set_epi64x(0x0123456789ABCDEFULL, 0xFEDCBA9876543210ULL);
    key = _mm_aesenc_si128(key, seed);  // Single AES round: ~3-4 cycles
    return _mm_extract_epi32(key, 0);
}
```

---

## Benchmarking

### Setup

```cpp
void benchmark_ticker_lookup() {
    // Generate keys
    std::vector<std::array<char, 16>> keys(100000);
    std::vector<uint32_t> values(100000);
    for (int i = 0; i < 100000; ++i) {
        snprintf(keys[i].data(), 16, "TKR%010d", i);
        values[i] = i;
    }

    // Build (not timed)
    TickerLookup table;
    table.build(keys, values);

    // Warmup
    for (int i = 0; i < 100000; ++i) {
        volatile auto v = table.lookup(keys[i].data());
    }

    // Timed lookups
    uint64_t start = __rdtsc();
    for (int rep = 0; rep < 10; ++rep) {
        for (int i = 0; i < 100000; ++i) {
            volatile auto v = table.lookup(keys[i].data());
        }
    }
    uint64_t elapsed = __rdtsc() - start;

    printf("Lookup: %lu cycles/op\n", elapsed / 1000000);
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 12 | 12-20 | > 20 |
| First-probe hit rate | 100% | > 95% | < 95% |
| Table memory | < 64 KB | < 256 KB | > 256 KB |

---

## Common Pitfalls

1. **Not exploiting unlimited build time** — Spend build time finding perfect hash parameters
2. **Using generic hash maps** — They're optimized for insert+lookup; here only lookup matters
3. **Table too large for cache** — Reduce entry size; use perfect hashing to eliminate keys
4. **String comparison with `strcmp`** — Compare as integers
5. **Ignoring access pattern** — If lookups are sequential, prefetching helps massively
