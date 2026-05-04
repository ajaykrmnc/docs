# Challenge 02: Multi-Symbol Order Book

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | agherghesanu / Malacarne | 974 cycles/op | 1843 cycles/op |
| 2nd | Pavel Baikov / Roman Sztergbaum | 1008 cycles/op | 2504 cycles/op |
| 3rd | Suntae L. / Hang | 1148 cycles/op | 2539 cycles/op |

---

## Problem Description

Build a multi-symbol order book with:
- **Multiple independent symbols** (e.g., AAPL, GOOG, MSFT)
- **Queue position tracking** — Know exactly where an order sits in the FIFO queue at its price level
- **Venue interaction** — Simulate exchange-level operations (fills, partial fills, queue position updates)

This is significantly more complex than Challenge 01 because you must manage multiple order books and track per-order queue positions.

---

## Core Concepts

### Queue Position Tracking

When you place a limit order at a price level that already has resting orders, your order is placed at the back of the queue. Knowing your queue position tells you:
- How many shares/contracts are ahead of you
- Probability of getting filled at this price level
- Whether to cancel and re-place if position is unfavorable

```
Price Level $100.50:
┌──────┬──────┬──────┬──────┬──────┐
│ 200  │ 150  │ 300  │ 100  │ 250  │  ← quantities
│ #001 │ #002 │ #003 │ #004 │ #005 │  ← order IDs
└──────┴──────┴──────┴──────┴──────┘
  ↑ Front of queue (filled first)        Back of queue ↑

Order #004 queue position = 200 + 150 + 300 = 650 shares ahead
```

### Venue Interaction

```
Market Participant                Exchange
      │                              │
      ├── New Order (AAPL BUY 100@150.50) ──→│
      │                              │── Accept / Add to book
      │←── Acknowledgment ───────────│
      │                              │
      │                              │── Match against resting sell
      │←── Fill (50@150.50) ─────────│
      │                              │
      ├── Cancel remaining ──────────→│
      │←── Cancel Ack ───────────────│
```

---

## Data Structure Architecture

### Per-Symbol Book + Fast Symbol Dispatch

```cpp
// Symbol → Book mapping must be O(1)
// If symbols are enumerated (0..N), use a flat array
// If symbols are strings, use a perfect hash or pre-mapped index

static constexpr int MAX_SYMBOLS = 4096;
static constexpr int MAX_PRICE_LEVELS = 100000;
static constexpr int MAX_ORDERS = 10'000'000;

struct PriceLevel {
    int64_t total_qty;          // Sum of all order quantities at this level
    int32_t head;               // Index of first order in queue (linked list head)
    int32_t tail;               // Index of last order in queue
    int16_t order_count;
};

struct Order {
    int32_t price;
    int32_t qty;
    int32_t remaining_qty;
    int32_t next;               // Next order in same price level queue
    int32_t prev;               // Previous order in same price level queue
    int16_t symbol_id;
    int8_t side;                // 0 = bid, 1 = ask
    int64_t queue_position;     // Quantity ahead of this order
};

struct SymbolBook {
    PriceLevel bid_levels[MAX_PRICE_LEVELS];
    PriceLevel ask_levels[MAX_PRICE_LEVELS];
    int32_t best_bid;
    int32_t best_ask;
};

struct MultiSymbolBook {
    SymbolBook books[MAX_SYMBOLS];
    Order orders[MAX_ORDERS];

    // Symbol name → ID mapping (built once at startup)
    int symbol_id_map[MAX_SYMBOLS];  // Or use perfect hash
};
```

### Queue Position Calculation

```cpp
// Option A: Eager — maintain position on every operation
// Pro: O(1) query, Con: O(n) update on cancel/fill at front

void calculate_position_eager(int order_id) {
    auto& order = orders[order_id];
    auto& level = books[order.symbol_id].get_level(order.price, order.side);

    int64_t pos = 0;
    int cur = level.head;
    while (cur != order_id) {
        pos += orders[cur].remaining_qty;
        cur = orders[cur].next;
    }
    order.queue_position = pos;
}

// Option B: Lazy — calculate on demand
// Pro: No maintenance cost, Con: O(n) query per position check
// In practice this is better if position queries are rare

int64_t get_queue_position(int order_id) {
    auto& order = orders[order_id];
    auto& level = books[order.symbol_id].get_level(order.price, order.side);

    int64_t pos = 0;
    int cur = level.head;
    while (cur != order_id) {
        pos += orders[cur].remaining_qty;
        cur = orders[cur].next;
    }
    return pos;
}

// Option C: Prefix-sum with dirty flag
// Maintain a cumulative quantity. Mark levels as dirty when modified.
// Rebuild prefix sum lazily on next query.
```

### Array-Based Doubly Linked List for Order Queue

```cpp
// Avoid pointer-based linked lists — they destroy cache performance
// Use array indices as "pointers"

struct IntrinsicList {
    static constexpr int NIL = -1;

    struct Node {
        int32_t prev = NIL;
        int32_t next = NIL;
        int32_t qty;
    };

    Node nodes[MAX_ORDERS];  // Index = order ID
    int head = NIL;
    int tail = NIL;

    void push_back(int id, int qty) {
        nodes[id] = {tail, NIL, qty};
        if (tail != NIL) nodes[tail].next = id;
        else head = id;
        tail = id;
    }

    void remove(int id) {
        auto& n = nodes[id];
        if (n.prev != NIL) nodes[n.prev].next = n.next;
        else head = n.next;
        if (n.next != NIL) nodes[n.next].prev = n.prev;
        else tail = n.prev;
    }
};
```

---

## Optimization Strategies

### 1. Symbol Dispatch — Avoid Hash Maps

```cpp
// If symbols are provided as short strings (e.g., "AAPL", "GOOG")
// Pre-compute a perfect hash at startup

// Simple approach: map symbol string to a dense integer ID at init time
// Then use book_array[symbol_id] for O(1) dispatch

struct SymbolMapper {
    // Use a minimal perfect hash function for known symbol set
    // Or a simple open-addressing hash table with linear probing
    int ids[HASH_SIZE];
    char symbols[MAX_SYMBOLS][8];

    int lookup(const char* sym) {
        uint64_t h = hash_symbol(sym);
        // Linear probe
        for (int i = h % HASH_SIZE; ; i = (i+1) % HASH_SIZE) {
            if (memcmp(symbols[ids[i]], sym, 8) == 0) return ids[i];
        }
    }
};
```

### 2. Hot/Cold Data Separation

```cpp
// Hot path: add order, get best price
// Cold path: queue position query, complex fills

// Keep hot data in a compact struct that fits in cache
struct HotBookData {
    alignas(64) int64_t bid_qty[MAX_LEVELS];
    alignas(64) int64_t ask_qty[MAX_LEVELS];
    int best_bid;
    int best_ask;
};  // This is the per-symbol hot data

// Cold data: order queue linked list nodes
struct ColdOrderData {
    int32_t prev, next;
    int32_t remaining_qty;
    int32_t symbol_id;
};
```

### 3. Batch Processing

```cpp
// If the workload allows, batch operations per symbol
// This improves cache locality — all ops on AAPL hit the same cache lines

void process_batch(std::span<Operation> ops) {
    // Sort ops by symbol (or bucket them)
    // Process all ops for symbol 0, then symbol 1, etc.
    // Keeps each symbol's book data hot in cache
    for (int sym = 0; sym < num_symbols; ++sym) {
        for (auto& op : ops) {
            if (op.symbol_id == sym) process(op);
        }
    }
}
```

### 4. SIMD for Queue Position

```cpp
// If orders at a price level are stored contiguously, SIMD sum is possible
#include <immintrin.h>

int64_t simd_queue_position(const int32_t* qtys, int count, int target_idx) {
    __m256i sum = _mm256_setzero_si256();
    int i = 0;
    for (; i + 8 <= target_idx; i += 8) {
        __m256i v = _mm256_loadu_si256((__m256i*)(qtys + i));
        sum = _mm256_add_epi32(sum, v);
    }
    // Horizontal sum + scalar remainder
    int32_t result[8];
    _mm256_storeu_si256((__m256i*)result, sum);
    int64_t total = 0;
    for (int j = 0; j < 8; j++) total += result[j];
    for (; i < target_idx; i++) total += qtys[i];
    return total;
}
```

---

## Benchmarking

### Workload Design

```cpp
struct BenchmarkWorkload {
    int num_symbols = 100;        // Realistic: 100-5000 symbols
    int orders_per_symbol = 1000;
    float add_ratio = 0.50;
    float cancel_ratio = 0.30;
    float fill_ratio = 0.15;
    float position_query_ratio = 0.05;

    // Price distribution per symbol:
    // Normal distribution centered at mid-price, σ = 20 ticks
    // This creates a realistic book shape
};
```

### Key Measurements

```bash
# Overall throughput
perf stat -e cycles,instructions ./multi_book_bench

# Per-symbol cache behavior (are different symbols thrashing each other?)
perf stat -e L1-dcache-load-misses,L1-dcache-loads ./bench

# Memory bandwidth (important with many symbols)
perf stat -e LLC-load-misses,LLC-loads ./bench
```

### Performance Breakdown by Operation

```cpp
// Measure each operation type separately
auto t0 = __rdtsc();
for (auto& op : add_ops) book.add(op);
auto add_cycles = (__rdtsc() - t0) / add_ops.size();

t0 = __rdtsc();
for (auto& op : cancel_ops) book.cancel(op);
auto cancel_cycles = (__rdtsc() - t0) / cancel_ops.size();

t0 = __rdtsc();
for (auto& op : position_queries) book.get_position(op);
auto position_cycles = (__rdtsc() - t0) / position_queries.size();

printf("Add: %lu cycles/op\n", add_cycles);
printf("Cancel: %lu cycles/op\n", cancel_cycles);
printf("Position: %lu cycles/op\n", position_cycles);
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op (mixed) | < 1100 | 1100-2000 | > 2000 |
| L1 cache miss rate | < 3% | 3-10% | > 10% |
| Symbol dispatch overhead | < 5 cycles | 5-20 cycles | > 20 cycles |

---

## Why Rust Is Slower Here

The ~2x gap (974 vs 1843 cycles/op) comes from:

1. **Multiple mutable borrows** — Managing linked lists across price levels requires careful ownership; often forces `unsafe` or `Cell`/`RefCell`
2. **Bounds checking overhead** — Multiple array accesses per operation across symbol arrays, price arrays, and order arrays
3. **Indirection cost** — Rust's ownership model can force extra indirection (e.g., `Vec<Box<SymbolBook>>` instead of flat arrays)
4. **Less mature SIMD ecosystem** — Though `std::simd` is improving

---

## Common Pitfalls

1. **Per-symbol `HashMap`** — Use flat arrays indexed by symbol ID
2. **`std::list` for order queues** — Use intrusive array-based linked lists
3. **Recomputing queue position on every add** — Only recompute when queried or when orders ahead are modified
4. **Not separating symbol data** — Different symbols should not share cache lines
5. **Dynamic allocation during order processing** — Pre-allocate all storage
