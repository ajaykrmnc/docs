# Low-Latency Systems Programming Challenges

A comprehensive guide to high-frequency trading (HFT) and low-latency systems programming challenges. Each document covers theory, implementation strategies, optimization techniques, and benchmarking methodology.

## Challenge Index

| # | Challenge | Key Concept | Metric |
|---|-----------|-------------|--------|
| 01 | [Best Price Tracker](./01-best-price-tracker.md) | Limit Order Book | cycles/op |
| 02 | [Multi-Symbol Order Book](./02-multi-symbol-order-book.md) | Multi-symbol LOB + Queue Position | cycles/op |
| 03 | [Event Scheduler](./03-event-scheduler.md) | Timer Management with Cancellation | cycles/op |
| 04 | [Event Scheduler (No Cancel)](./04-event-scheduler-no-cancel.md) | Timer Management without Cancellation | cycles/op |
| 05 | [Ring Buffer (SPSC)](./05-ring-buffer.md) | Single-Producer Single-Consumer Queue | cycles/op |
| 06 | [Seqlock](./06-seqlock.md) | Sequence Lock (1 Writer, N Readers) | cycles/op |
| 07 | [String Map](./07-string-map.md) | Hash Map with String Keys | cycles/op |
| 08 | [Ticker Lookup](./08-ticker-lookup.md) | Symbol Lookup Table | cycles/op |
| 09 | [FIX Parser](./09-fix-parser.md) | FIX Protocol Parsing | cycles/KB |
| 10 | [FIX Encoder](./10-fix-encoder.md) | FIX Protocol Encoding | cycles/msg |
| 11 | [Rolling Counter](./11-rolling-counter.md) | Sliding Window Counter | cycles/op |
| 12 | [Feed Arbiter](./12-feed-arbiter.md) | Market Feed Arbitration | cycles/op |
| 13 | [Implied Book](./13-implied-book.md) | Implied Order Book | cycles/op |
| 14 | [Build Optimization](./14-build-optimization.md) | Compiler Flags & Link-time Optimization | cycles/kop |
| 15 | [Implied Volatility](./15-implied-volatility.md) | Options IV Solver | cycles/op |
| 16 | [Monte Carlo Pricer](./16-monte-carlo-pricer.md) | Monte Carlo Option Pricing | cycles/op |
| 17 | [Cross-CCX Ring Buffer](./17-cross-ccx-ring-buffer.md) | Cross-Core-Complex SPSC | cycles/op |
| 18 | [Build Optimization II](./18-build-optimization-ii.md) | Advanced Compiler Optimization | cycles/kop |

## Benchmarking Fundamentals

See [Benchmarking Guide](./19-benchmarking-guide.md) for the universal methodology used across all challenges.

## Performance Tiers (General Guidelines)

| Tier | cycles/op | Description |
|------|-----------|-------------|
| Elite | < 20 | Cache-line optimized, branch-free, SIMD |
| Expert | 20-100 | Excellent data structure choice, minimal branching |
| Proficient | 100-500 | Good algorithm, some overhead |
| Baseline | 500-5000 | Correct implementation, not yet optimized |
| Unoptimized | > 5000 | Naive approach, significant room for improvement |

## Key Optimization Themes Across All Challenges

1. **Cache Efficiency** — Fit hot data in L1 (32-64 KB), avoid cache misses at all costs
2. **Branch Prediction** — Eliminate branches or make them predictable; use `__builtin_expect`, branchless code
3. **Memory Layout** — SoA vs AoS, padding, alignment, false sharing avoidance
4. **SIMD** — Use SSE/AVX for parallel data processing
5. **Compiler Hints** — `__attribute__((hot))`, `__attribute__((always_inline))`, PGO, LTO
6. **Lock-Free Algorithms** — Atomic operations, memory ordering, CAS loops
7. **Prefetching** — `__builtin_prefetch` for predictable access patterns
8. **Custom Allocators** — Pool allocators, arena allocators to avoid malloc overhead
