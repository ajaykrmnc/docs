# Performance and Benchmarks

## Overview

Performance measurement is critical for transaction processing systems. Jim Gray was instrumental in creating standardized database benchmarks through the Transaction Processing Performance Council (TPC). This document covers performance metrics, TPC benchmarks, and Gray's influential Five-Minute Rule.

---

## Performance Metrics

### Key Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                   PERFORMANCE METRICS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. THROUGHPUT                                                  │
│     • Transactions per second (TPS)                             │
│     • Transactions per minute (TPM)                             │
│     • Higher is better                                          │
│                                                                 │
│  2. RESPONSE TIME                                               │
│     • Time from request to response                             │
│     • Often measured as percentiles (p50, p95, p99)             │
│     • Lower is better                                           │
│                                                                 │
│  3. COST EFFICIENCY                                             │
│     • $/TPM (cost per transaction per minute)                   │
│     • Price/performance ratio                                   │
│     • Lower is better                                           │
│                                                                 │
│  4. SCALABILITY                                                 │
│     • Linear: 2x resources = 2x throughput                      │
│     • Sub-linear: diminishing returns                           │
│     • Super-linear: rare, usually caching effects               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Response Time Distribution

```
┌─────────────────────────────────────────────────────────────────┐
│              RESPONSE TIME PERCENTILES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Count                                                          │
│    │                                                            │
│    │  ████                                                      │
│    │  ████                                                      │
│    │  ████████                                                  │
│    │  ████████████                                              │
│    │  ██████████████████                                        │
│    │  ██████████████████████████                   ██           │
│    └───────────────────────────────────────────────────► Time   │
│         p50    p90  p95  p99             p99.9                  │
│                                                                 │
│  Example Values:                                                │
│  • p50 (median):  10ms  - 50% of requests faster               │
│  • p95:           50ms  - 95% of requests faster               │
│  • p99:          200ms  - 99% of requests faster               │
│  • p99.9:        500ms  - 99.9% of requests faster             │
│                                                                 │
│  The "tail latency" (p99+) is critical for user experience     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## TPC Benchmarks

### TPC Overview

The Transaction Processing Performance Council (TPC) creates standardized benchmarks:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TPC BENCHMARK FAMILY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Benchmark   │ Workload Type         │ Metric                   │
│  ────────────┼───────────────────────┼─────────────────────────│
│  TPC-A       │ Simple debit/credit   │ tpsA (retired)          │
│  TPC-B       │ Database stress test  │ tpsB (retired)          │
│  TPC-C       │ OLTP (complex)        │ tpmC                    │
│  TPC-E       │ OLTP (brokerage)      │ tpsE                    │
│  TPC-H       │ Decision support      │ QphH (queries/hour)     │
│  TPC-DS      │ Big data analytics    │ QphDS                   │
│                                                                 │
│  Key Principles:                                                │
│  • Standardized schema and transactions                         │
│  • Full disclosure reports                                      │
│  • Independent auditing                                         │
│  • Price/performance metrics                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### TPC-C Benchmark (The Gold Standard)

```
┌─────────────────────────────────────────────────────────────────┐
│                      TPC-C BENCHMARK                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Simulates wholesale supplier with:                             │
│  • Multiple warehouses                                          │
│  • Districts within warehouses                                  │
│  • Customers placing orders                                     │
│                                                                 │
│  Five Transaction Types:                                        │
│  ┌────────────────┬──────────┬─────────────────────────┐       │
│  │ Transaction    │ Mix %    │ Description             │       │
│  ├────────────────┼──────────┼─────────────────────────┤       │
│  │ New-Order      │ 45%      │ Enter new customer order│       │


```
┌─────────────────────────────────────────────────────────────────┐
│                      TPC-C SCHEMA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │  WAREHOUSE   │────┐                                          │
│  │  (W)         │    │ 1:N                                      │
│  └──────────────┘    │                                          │
│         │            ▼                                          │
│         │      ┌──────────────┐                                 │
│    1:N  │      │   DISTRICT   │────┐                            │
│         │      │   (10 per W) │    │ 1:N                        │
│         │      └──────────────┘    │                            │
│         │            │             ▼                            │
│         │       1:N  │      ┌──────────────┐                    │
│         │            │      │  CUSTOMER    │                    │
│         │            │      │(3000 per D)  │                    │
│         │            │      └──────┬───────┘                    │
│         │            │             │                            │
│         ▼            ▼             ▼                            │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │    STOCK     │  │    ORDER     │────► ORDER-LINE             │
│  │(100K per W)  │  │              │      HISTORY                │
│  └──────────────┘  └──────────────┘      NEW-ORDER              │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │    ITEM      │ (100,000 items - shared)                      │
│  └──────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Five-Minute Rule

### Jim Gray's Original Five-Minute Rule (1987)

One of Jim Gray's most influential contributions to database performance analysis:

```
┌─────────────────────────────────────────────────────────────────┐
│                   THE FIVE-MINUTE RULE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "Pages referenced every five minutes should be memory          │
│   resident."                                                    │
│                                                                 │
│  The Rule:                                                      │
│  ───────────────────────────────────────────────────────────── │
│  If a page is accessed more frequently than once every 5        │
│  minutes, keep it in memory. Otherwise, read it from disk.      │
│                                                                 │
│  Break-Even Formula:                                            │
│                                                                 │
│            PagesPerMBofRAM × AccessesPerSecondToBreakEven       │
│  Minutes = ─────────────────────────────────────────────────    │
│                       AccessesPerSecondPerDisk                  │
│                                                                 │
│  In 1987:                                                       │
│  • Memory: $5,000/MB                                            │
│  • Disk access: $15/access per second                           │
│  • Result: ~5 minutes                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Five-Minute Rule Evolution

```
┌─────────────────────────────────────────────────────────────────┐
│              FIVE-MINUTE RULE OVER TIME                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Year  │ Interval │ Key Changes                                 │
│  ──────┼──────────┼─────────────────────────────────────────── │
│  1987  │ 5 min    │ Original rule (RAM vs HDD)                  │
│  1997  │ 5 min    │ RAM/disk price ratio stayed constant        │
│  2007  │ 5 min    │ Still roughly valid for HDD                 │
│  2017  │ 1.5 hrs  │ SSD changes the equation                    │
│                                                                 │
│  Modern Consideration:                                          │
│                                                                 │
│  ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐       │
│  │  RAM   │ ◄─► │  SSD   │ ◄─► │  HDD   │ ◄─► │ Cloud  │       │
│  │ (hot)  │     │ (warm) │     │ (cold) │     │Storage │       │
│  └────────┘     └────────┘     └────────┘     └────────┘       │
│                                                                 │
│  Multiple tiers require multiple "break-even" calculations      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Optimization

### Bottleneck Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                  TYPICAL BOTTLENECKS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Resource      │ Symptom            │ Solution                  │
│  ─────────────┼────────────────────┼─────────────────────────  │
│  CPU          │ High utilization   │ Query optimization,       │
│               │ on all cores       │ better indexing           │
│  ─────────────┼────────────────────┼─────────────────────────  │
│  Memory       │ High page faults,  │ Increase buffer pool,     │
│               │ swapping           │ reduce working set        │
│  ─────────────┼────────────────────┼─────────────────────────  │
│  Disk I/O     │ High disk queue    │ Faster storage, caching,  │
│               │ lengths            │ better data placement     │
│  ─────────────┼────────────────────┼─────────────────────────  │
│  Locks        │ High lock waits,   │ Finer granularity,        │
│               │ deadlocks          │ optimistic concurrency    │
│  ─────────────┼────────────────────┼─────────────────────────  │
│  Network      │ High latency,      │ Connection pooling,       │
│               │ packet loss        │ data locality             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Capacity Planning

### Little's Law

```
┌─────────────────────────────────────────────────────────────────┐
│                      LITTLE'S LAW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L = λ × W                                                      │
│                                                                 │
│  Where:                                                         │
│  • L = Average number of items in system                        │
│  • λ = Average arrival rate                                     │
│  • W = Average time in system                                   │
│                                                                 │
│  Example:                                                       │
│  • 100 transactions/second arrive (λ)                           │
│  • Each takes 50ms average (W = 0.05s)                          │
│  • Need capacity for 100 × 0.05 = 5 concurrent transactions     │
│                                                                 │
│  Application:                                                   │
│  • Sizing connection pools                                      │
│  • Sizing thread pools                                          │
│  • Estimating queue depths                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Throughput vs latency** - often trade-offs; optimize for the right metric
2. **TPC benchmarks** provide standardized, auditable performance comparisons
3. **TPC-C** remains the gold standard for OLTP workload comparison
4. **Five-Minute Rule** guides memory vs storage trade-offs (adjusts with technology)
5. **Percentile latencies** (p99, p99.9) matter more than averages for user experience
6. **Little's Law** is fundamental for capacity planning
7. **Identify bottlenecks** before optimizing - don't guess

---

## References

- Gray, J. & Reuter, A. (1993). Chapter 7: "System Performance"
- Gray, J. & Putzolu, F. (1987). "The 5 Minute Rule for Trading Memory for Disc Accesses"
- Gray, J. & Graefe, G. (1997). "The Five-Minute Rule Ten Years Later"
- Transaction Processing Performance Council (TPC). www.tpc.org
- TPC-C Benchmark Standard Specification
- Dean, J. & Barroso, L. (2013). "The Tail at Scale"