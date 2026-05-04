# Challenge 13: Implied Book

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | blumper m. / Malacarne | 92 cycles/op | 131 cycles/op |
| 2nd | Przemek S. / Baseline | 95 cycles/op | 597 cycles/op |
| 3rd | Hang / Jakub Koszuliński | 189 cycles/op | 597 cycles/op |

---

## Problem Description

Build an implied order book — a system that computes synthetic liquidity from related instruments.

This is one of the most important concepts in derivatives trading. Implied pricing allows traders to see liquidity that doesn't explicitly exist in any single order book.

---

## Core Concepts

### What Are Implied Orders?

In futures markets, if you can buy the March contract and sell the June contract, you're effectively trading the March-June spread. Implied pricing works both ways:

```
Outright Books:           Spread Book:           Implied:
┌──────────────┐         ┌──────────────┐        ┌──────────────┐
│ March Future │         │ Mar-Jun Sprd │        │ June Future  │
│ Bid: 100.00  │    +    │ Bid: -2.50   │   =    │ Offer: 102.50│
│              │         │              │        │ (implied)    │
└──────────────┘         └──────────────┘        └──────────────┘

Logic: If someone will buy March at 100 and someone will buy the
spread (Mar-Jun) at -2.50, then implicitly someone is willing to
sell June at 100 + 2.50 = 102.50
```

### Implied Pricing Rules

```
Given three related instruments: A, B, and Spread(A-B):

1. Implied Ask of B = Best Ask of A - Best Bid of Spread(A-B)
2. Implied Bid of B = Best Bid of A - Best Ask of Spread(A-B)
3. Implied Ask of Spread = Best Ask of A - Best Bid of B
4. Implied Bid of Spread = Best Bid of A - Best Ask of B
5. Implied Ask of A = Best Ask of B + Best Ask of Spread(A-B)
6. Implied Bid of A = Best Bid of B + Best Bid of Spread(A-B)
```

### Implied Quantity

The implied quantity is the minimum of the quantities that create it:

```cpp
// Implied Ask of B from A and Spread(A-B):
implied_ask_price_B = ask_price_A - bid_price_spread;
implied_ask_qty_B = min(ask_qty_A, bid_qty_spread);
```

---

## Implementation

### Data Structure

```cpp
struct ImpliedBook {
    struct Level {
        int64_t price;      // In ticks (integer)
        int32_t qty;
        bool is_implied;    // true if this level is implied, not direct
    };

    struct Book {
        Level best_bid;
        Level best_ask;
    };

    // Three books: Leg A, Leg B, Spread(A-B)
    Book leg_a;
    Book leg_b;
    Book spread;

    // Combined books (direct + implied)
    Book combined_a;
    Book combined_b;
    Book combined_spread;

    void update_leg_a(int64_t bid_price, int32_t bid_qty,
                      int64_t ask_price, int32_t ask_qty) {
        leg_a.best_bid = {bid_price, bid_qty, false};
        leg_a.best_ask = {ask_price, ask_qty, false};
        recalculate_implied();
    }

    void update_leg_b(int64_t bid_price, int32_t bid_qty,
                      int64_t ask_price, int32_t ask_qty) {
        leg_b.best_bid = {bid_price, bid_qty, false};
        leg_b.best_ask = {ask_price, ask_qty, false};
        recalculate_implied();
    }

    void update_spread(int64_t bid_price, int32_t bid_qty,
                       int64_t ask_price, int32_t ask_qty) {
        spread.best_bid = {bid_price, bid_qty, false};
        spread.best_ask = {ask_price, ask_qty, false};
        recalculate_implied();
    }

private:
    void recalculate_implied() {
        // Implied prices for Leg B
        // Implied Ask B = Ask A - Bid Spread
        int64_t imp_ask_b = leg_a.best_ask.price - spread.best_bid.price;
        int32_t imp_ask_b_qty = std::min(leg_a.best_ask.qty, spread.best_bid.qty);

        // Implied Bid B = Bid A - Ask Spread
        int64_t imp_bid_b = leg_a.best_bid.price - spread.best_ask.price;
        int32_t imp_bid_b_qty = std::min(leg_a.best_bid.qty, spread.best_ask.qty);

        // Combined book for B: best of direct and implied
        combined_b.best_bid = best_level(leg_b.best_bid,
                                          {imp_bid_b, imp_bid_b_qty, true},
                                          true);  // true = bid side (higher is better)
        combined_b.best_ask = best_level(leg_b.best_ask,
                                          {imp_ask_b, imp_ask_b_qty, true},
                                          false); // false = ask side (lower is better)

        // Similarly for Leg A and Spread...
        recalculate_implied_a();
        recalculate_implied_spread();
    }

    Level best_level(const Level& direct, const Level& implied, bool is_bid) {
        if (direct.qty == 0) return implied;
        if (implied.qty == 0) return direct;

        if (is_bid) {
            return (implied.price > direct.price) ? implied : direct;
        } else {
            return (implied.price < direct.price) ? implied : direct;
        }
    }
};
```

### Optimized: Branchless Implied Calculation

```cpp
struct FastImpliedBook {
    // Store prices and quantities in arrays for SIMD-friendly access
    // Index: 0=Leg A Bid, 1=Leg A Ask, 2=Leg B Bid, 3=Leg B Ask,
    //        4=Spread Bid, 5=Spread Ask

    alignas(32) int64_t prices[6];
    alignas(32) int32_t qtys[6];

    // Output: combined best prices
    alignas(32) int64_t combined_prices[6];
    alignas(32) int32_t combined_qtys[6];

    enum { A_BID=0, A_ASK=1, B_BID=2, B_ASK=3, SP_BID=4, SP_ASK=5 };

    void recalculate() {
        // Implied Ask B = Ask A - Bid Spread
        int64_t imp_ask_b = prices[A_ASK] - prices[SP_BID];
        int32_t imp_ask_b_q = std::min(qtys[A_ASK], qtys[SP_BID]);

        // Implied Bid B = Bid A - Ask Spread
        int64_t imp_bid_b = prices[A_BID] - prices[SP_ASK];
        int32_t imp_bid_b_q = std::min(qtys[A_BID], qtys[SP_ASK]);

        // Implied Ask A = Ask B + Ask Spread
        int64_t imp_ask_a = prices[B_ASK] + prices[SP_ASK];
        int32_t imp_ask_a_q = std::min(qtys[B_ASK], qtys[SP_ASK]);

        // Implied Bid A = Bid B + Bid Spread
        int64_t imp_bid_a = prices[B_BID] + prices[SP_BID];
        int32_t imp_bid_a_q = std::min(qtys[B_BID], qtys[SP_BID]);

        // Implied Ask Spread = Ask A - Bid B
        int64_t imp_ask_sp = prices[A_ASK] - prices[B_BID];
        int32_t imp_ask_sp_q = std::min(qtys[A_ASK], qtys[B_BID]);

        // Implied Bid Spread = Bid A - Ask B
        int64_t imp_bid_sp = prices[A_BID] - prices[B_ASK];
        int32_t imp_bid_sp_q = std::min(qtys[A_BID], qtys[B_ASK]);

        // Combine: branchless max for bids, branchless min for asks
        // Bid: take higher price (use cmov)
        combined_prices[A_BID] = branchless_max(prices[A_BID], imp_bid_a);
        combined_prices[B_BID] = branchless_max(prices[B_BID], imp_bid_b);
        combined_prices[SP_BID] = branchless_max(prices[SP_BID], imp_bid_sp);

        combined_prices[A_ASK] = branchless_min(prices[A_ASK], imp_ask_a);
        combined_prices[B_ASK] = branchless_min(prices[B_ASK], imp_ask_b);
        combined_prices[SP_ASK] = branchless_min(prices[SP_ASK], imp_ask_sp);

        // Quantities follow the selected price
        // ... (select qty based on which price was chosen)
    }

    static int64_t branchless_max(int64_t a, int64_t b) {
        return a ^ ((a ^ b) & -(a < b));  // Returns b if a < b
    }

    static int64_t branchless_min(int64_t a, int64_t b) {
        return b ^ ((a ^ b) & -(a < b));  // Returns a if a < b
    }
};
```

### Multi-Level Implied Book

For production systems, you need implied prices at multiple depth levels, not just top-of-book:

```cpp
struct MultiLevelImplied {
    static constexpr int MAX_DEPTH = 10;

    struct BookSide {
        int64_t prices[MAX_DEPTH];
        int32_t qtys[MAX_DEPTH];
        int depth;
    };

    struct Instrument {
        BookSide bids;
        BookSide asks;
    };

    Instrument legs[3];  // Leg A, Leg B, Spread

    // Build combined book by merging direct and implied levels
    void build_combined_book(int instrument, BookSide& combined_bids,
                             BookSide& combined_asks) {
        // Generate implied levels
        BookSide implied_bids, implied_asks;
        compute_implied_levels(instrument, implied_bids, implied_asks);

        // Merge direct and implied (like merge step of merge sort)
        merge_levels(legs[instrument].bids, implied_bids, combined_bids, true);
        merge_levels(legs[instrument].asks, implied_asks, combined_asks, false);
    }
};
```

---

## Benchmarking

### Workload

```cpp
// Simulate market data updates across three instruments
// Each update triggers implied recalculation

void benchmark() {
    FastImpliedBook book;
    constexpr int N = 10'000'000;

    // Pre-generate price updates
    std::mt19937 rng(42);
    auto updates = generate_price_updates(N, rng);

    uint64_t start = __rdtsc();
    for (auto& u : updates) {
        book.prices[u.field] = u.price;
        book.qtys[u.field] = u.qty;
        book.recalculate();
    }
    uint64_t elapsed = __rdtsc() - start;

    printf("%lu cycles/op\n", elapsed / N);
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 100 | 100-200 | > 200 |
| Branch mispredictions | < 0.5% | 0.5-2% | > 2% |
| Arithmetic ops | < 20/recalc | 20-50 | > 50 |

---

## Common Pitfalls

1. **Recalculating all implied prices when only one book changes** — Only recalculate affected implied prices
2. **Using floating-point for prices** — Integer tick prices avoid rounding errors
3. **Not handling zero-quantity levels** — A level with zero quantity should not generate implied prices
4. **Branchy min/max** — Use branchless comparison; the "which is better" comparison happens on every update
5. **Ignoring crossed implied books** — When implied bid > implied ask, there's an arbitrage opportunity; the arbiter must handle this
