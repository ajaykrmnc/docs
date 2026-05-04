# Challenge 01: Best Price Tracker (Limit Order Book)

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Jikan / Roman Sztergbaum | 14 cycles/op | 36 cycles/op |
| 2nd | Stefan P. / Emmanuel M. | 15 cycles/op | 36 cycles/op |
| 3rd | Suntae L. / Pavel Baikov | 15 cycles/op | 37 cycles/op |

---

## What Is a Limit Order Book?

A Limit Order Book (LOB) is the core data structure of any electronic exchange. It maintains a sorted collection of buy (bid) and sell (ask) orders at various price levels.

```
        ASK SIDE (Sellers)
        ┌─────────────────┐
        │ $101.50  200 qty│  ← Best Ask (lowest sell price)
        │ $101.25  150 qty│
        │ $101.00   50 qty│
        ├─────────────────┤
        │    SPREAD        │
        ├─────────────────┤
        │ $100.75  300 qty│  ← Best Bid (highest buy price)
        │ $100.50  100 qty│
        │ $100.25  250 qty│
        └─────────────────┘
        BID SIDE (Buyers)
```

### Operations Required

1. **Add Order** — Insert a new limit order at a given price level
2. **Cancel Order** — Remove an existing order by ID
3. **Modify Order** — Change quantity or price of an existing order
4. **Get Best Bid/Ask** — Return the top-of-book prices (this is the "best price tracking")
5. **Execute/Match** — Match incoming orders against resting orders

### Key Constraint

The "Best Price Tracker" specifically emphasizes O(1) retrieval of the best bid and best ask after every operation.

---

## Data Structure Design

### Approach 1: Array-Indexed by Price (Optimal for Dense Price Ranges)

```cpp
// Price levels are typically in "ticks" — integer multiples of the minimum price increment
// For a tick size of $0.01 and range $0-$10000, we need 1,000,000 entries
// This is feasible and gives O(1) access

struct PriceLevel {
    int64_t total_qty;
    int32_t order_count;
};

struct OrderBook {
    static constexpr int MAX_PRICE = 1'000'000;

    std::array<PriceLevel, MAX_PRICE> levels;  // Direct-indexed by tick price
    int best_bid = -1;    // Highest bid price (tick)
    int best_ask = MAX_PRICE;  // Lowest ask price (tick)

    // Order ID → (price, qty, side) for O(1) cancel
    struct OrderInfo {
        int32_t price;
        int32_t qty;
        bool is_bid;
    };
    std::array<OrderInfo, MAX_ORDERS> orders;  // Direct-indexed by order ID
};
```

**Why this is fast:**
- Add/cancel: O(1) array access
- Best bid/ask: O(1) cached value
- Only update best bid/ask when the operation affects the current best level

### Approach 2: Sorted Array of Active Levels

```cpp
// For very sparse price ranges, maintain a compact sorted array of active levels
// Use binary search for insert/delete but benefit from cache locality

struct CompactBook {
    struct Level {
        int32_t price;
        int64_t qty;
        int32_t count;
    };

    Level bids[MAX_LEVELS];  // Sorted descending
    Level asks[MAX_LEVELS];  // Sorted ascending
    int num_bids = 0;
    int num_asks = 0;
    // Best bid = bids[0], Best ask = asks[0]
};
```

### Approach 3: Hybrid (What Top Competitors Use)

```cpp
// Direct-indexed price level array + cached best prices
// + side-specific scan for new best when current best is depleted

struct HybridBook {
    // Price level data — direct indexed
    int64_t bid_qty[MAX_TICKS] = {};   // quantity at each bid tick
    int64_t ask_qty[MAX_TICKS] = {};   // quantity at each ask tick

    int best_bid = -1;
    int best_ask = MAX_TICKS;

    // Flat array for order lookup
    struct Order {
        int32_t price;
        int32_t qty;
    };
    Order orders[MAX_ORDERS];
    bool is_bid[MAX_ORDERS];

    void add_order(int id, int price, int qty, bool bid) {
        orders[id] = {price, qty};
        is_bid[id] = bid;

        if (bid) {
            bid_qty[price] += qty;
            if (price > best_bid) best_bid = price;
        } else {
            ask_qty[price] += qty;
            if (price < best_ask) best_ask = price;
        }
    }

    void cancel_order(int id) {
        auto& o = orders[id];
        if (is_bid[id]) {
            bid_qty[o.price] -= o.qty;
            // Only scan for new best if we depleted the current best level
            if (o.price == best_bid && bid_qty[o.price] == 0) {
                while (best_bid >= 0 && bid_qty[best_bid] == 0) --best_bid;
            }
        } else {
            ask_qty[o.price] -= o.qty;
            if (o.price == best_ask && ask_qty[o.price] == 0) {
                while (best_ask < MAX_TICKS && ask_qty[best_ask] == 0) ++best_ask;
            }
        }
    }
};
```

---

## Optimization Techniques for 14 cycles/op

### 1. Eliminate Branching on the Hot Path

```cpp
// BAD: Branch on every add
if (side == BUY) {
    // bid logic
} else {
    // ask logic
}

// GOOD: Template on side to eliminate runtime branch
template<Side S>
void add_order(int price, int qty) {
    if constexpr (S == BUY) {
        bid_qty[price] += qty;
        best_bid = std::max(best_bid, price);
    } else {
        ask_qty[price] += qty;
        best_ask = std::min(best_ask, price);
    }
}
```

### 2. Branchless Best-Price Update

```cpp
// Branchless max for best_bid update
best_bid += (price - best_bid) & ((price - best_bid) >> 31 ^ (price - best_bid) >> 31);
// Or simply:
best_bid = price > best_bid ? price : best_bid;  // Compiler often generates cmov
```

### 3. Memory Layout for Cache Efficiency

```cpp
// Keep hot data together — the qty arrays are the hot data
// Order metadata is cold (only accessed on cancel)
// Separate them to avoid polluting cache with cold data

struct HotData {
    alignas(64) int64_t bid_qty[MAX_TICKS];
    alignas(64) int64_t ask_qty[MAX_TICKS];
    int best_bid;
    int best_ask;
};

struct ColdData {
    // Only accessed during cancel
    struct Order { int32_t price; int32_t qty; };
    Order orders[MAX_ORDERS];
    bool is_bid[MAX_ORDERS];
};
```

### 4. Avoid Hash Maps

```cpp
// BAD: Using unordered_map for order lookup
std::unordered_map<int, OrderInfo> orders;  // Hash overhead, pointer chasing, cache misses

// GOOD: Direct array indexing (if order IDs are sequential/bounded)
OrderInfo orders[MAX_ORDERS];
```

### 5. Compiler Hints

```cpp
// Mark the hot path
__attribute__((hot, always_inline))
void add_order(int id, int price, int qty, bool bid) { ... }

// Hint branch prediction for rare paths
if (__builtin_expect(price == best_bid && bid_qty[price] == 0, 0)) {
    // Scan for new best — rare
    scan_new_best_bid();
}
```

---

## Benchmarking This Challenge

### What to Measure

- **Primary metric**: Average cycles per operation across a mixed workload (adds, cancels, queries)
- Measure using `rdtsc` (Read Time Stamp Counter)

### Benchmark Harness

```cpp
#include <x86intrin.h>

uint64_t benchmark_orderbook(int num_ops) {
    OrderBook book;
    // Pre-generate deterministic workload
    auto ops = generate_workload(num_ops);

    // Warmup — fill caches
    for (auto& op : ops) execute(book, op);
    book.reset();

    // Timed run
    uint64_t start = __rdtsc();
    for (auto& op : ops) {
        execute(book, op);
    }
    uint64_t end = __rdtsc();

    return (end - start) / num_ops;
}
```

### Workload Characteristics

1. **Realistic order flow**: ~60% adds, ~30% cancels, ~10% modifies
2. **Price distribution**: Concentrated around mid-price (normal distribution)
3. **Order ID pattern**: Sequential or random (tests lookup performance)

### Profiling Checklist

```bash
# 1. Compile with full optimization
g++ -O3 -march=native -mtune=native -flto -fomit-frame-pointer -o bench bench.cpp

# 2. Pin to a single core (avoid migration)
taskset -c 0 ./bench

# 3. Disable frequency scaling
sudo cpupower frequency-set -g performance

# 4. Profile cache misses
perf stat -e cache-misses,cache-references,instructions,cycles ./bench

# 5. Profile branch mispredictions
perf stat -e branch-misses,branches ./bench

# 6. Detailed hotspot analysis
perf record -g ./bench
perf report
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 20 | 20-50 | > 50 |
| Cache miss rate | < 1% | 1-5% | > 5% |
| Branch mispredict rate | < 0.5% | 0.5-2% | > 2% |
| IPC (Instructions/Cycle) | > 3.0 | 2.0-3.0 | < 2.0 |

---

## Rust Implementation Notes

Rust solutions average ~36 cycles/op vs C++'s ~14. The gap comes from:

1. **Bounds checking** — Rust arrays check bounds by default; use `get_unchecked()` in unsafe blocks
2. **Ownership model** — Borrow checker can force extra copies; use indices instead of references
3. **No `cmov` guarantee** — Rust's optimizer may not emit branchless code; use explicit bit manipulation

```rust
// Rust equivalent of the hybrid approach
struct OrderBook {
    bid_qty: Vec<i64>,  // Use Box<[i64; MAX_TICKS]> to avoid heap allocation overhead
    ask_qty: Vec<i64>,
    best_bid: i32,
    best_ask: i32,
    orders: Vec<Order>,
}

impl OrderBook {
    #[inline(always)]
    pub fn add_order(&mut self, id: usize, price: usize, qty: i64, is_bid: bool) {
        unsafe {
            if is_bid {
                *self.bid_qty.get_unchecked_mut(price) += qty;
                self.best_bid = self.best_bid.max(price as i32);
            } else {
                *self.ask_qty.get_unchecked_mut(price) += qty;
                self.best_ask = self.best_ask.min(price as i32);
            }
            *self.orders.get_unchecked_mut(id) = Order { price: price as i32, qty: qty as i32 };
        }
    }
}
```

---

## Common Pitfalls

1. **Using `std::map` / `BTreeMap`** — O(log n) per operation, cache-unfriendly; use arrays
2. **Scanning for best price on every operation** — Cache the best price; only scan when depleted
3. **Dynamic memory allocation** — Pre-allocate everything; zero malloc on the hot path
4. **Pointer-based linked lists for order queues** — Cache-hostile; use array-based queues
5. **Unnecessary data copies** — Pass by reference, avoid returning structs by value on hot path
