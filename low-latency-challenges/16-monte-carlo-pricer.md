# Challenge 16: Monte Carlo Pricer

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Davide Spataro / Siddharth Singh | 206,809 cycles/op | 17,585,588 cycles/op |
| 2nd | frfx / Jakub Koszuliński | 324,035 cycles/op | 131,927,651 cycles/op |
| 3rd | Hang / Baseline | 790,484 cycles/op | 132,753,483 cycles/op |

---

## Problem Description

Build a Monte Carlo option pricer. Simulate many random stock price paths and average the payoffs to estimate the option price.

This is fundamentally a compute-heavy problem — the challenge is pure throughput of:
1. Random number generation
2. Exponential/log computation
3. Payoff calculation
4. Aggregation

---

## Background: Monte Carlo Option Pricing

### The Method

```
1. Simulate N stock price paths from today to expiry:
   S(T) = S₀ · exp((r - σ²/2)T + σ√T · Z)
   where Z ~ N(0,1)

2. Calculate payoff for each path:
   Call: max(S(T) - K, 0)
   Put:  max(K - S(T), 0)

3. Average payoffs and discount:
   Price = e^(-rT) · (1/N) · Σ payoff_i
```

### Why Monte Carlo?

- Works for any payoff structure (exotic options, path-dependent)
- Trivially parallelizable
- Accuracy scales as O(1/√N) — more paths = more precision

### The Computational Challenge

For 10M paths:
- 10M random normal samples
- 10M exponentials
- 10M max operations
- 1 reduction (sum)

At ~20 cycles per sample (the theoretical minimum), that's ~200M cycles.

---

## Implementation Approaches

### Approach 1: Scalar Baseline

```cpp
double monte_carlo_price(double S0, double K, double T, double r,
                         double sigma, int num_paths, bool is_call) {
    double drift = (r - 0.5 * sigma * sigma) * T;
    double vol_sqrt_t = sigma * sqrt(T);
    double discount = exp(-r * T);

    double sum_payoff = 0.0;
    std::mt19937_64 rng(42);
    std::normal_distribution<double> norm(0.0, 1.0);

    for (int i = 0; i < num_paths; ++i) {
        double z = norm(rng);
        double st = S0 * exp(drift + vol_sqrt_t * z);
        double payoff = is_call ? std::max(st - K, 0.0) : std::max(K - st, 0.0);
        sum_payoff += payoff;
    }

    return discount * sum_payoff / num_paths;
}
```

### Approach 2: AVX2 Vectorized

```cpp
#include <immintrin.h>

// Process 4 paths simultaneously with AVX2 (double precision)
double monte_carlo_avx2(double S0, double K, double T, double r,
                        double sigma, int num_paths) {
    __m256d v_drift = _mm256_set1_pd((r - 0.5 * sigma * sigma) * T);
    __m256d v_vol_sqrt_t = _mm256_set1_pd(sigma * sqrt(T));
    __m256d v_S0 = _mm256_set1_pd(S0);
    __m256d v_K = _mm256_set1_pd(K);
    __m256d v_zero = _mm256_setzero_pd();
    __m256d v_sum = _mm256_setzero_pd();

    for (int i = 0; i < num_paths; i += 4) {
        // Generate 4 normal random numbers (see RNG section below)
        __m256d z = generate_4_normals_avx2();

        // S(T) = S0 * exp(drift + vol*sqrt(T)*z)
        __m256d exponent = _mm256_fmadd_pd(v_vol_sqrt_t, z, v_drift);
        __m256d st = _mm256_mul_pd(v_S0, fast_exp_avx2(exponent));

        // payoff = max(S(T) - K, 0)
        __m256d payoff = _mm256_max_pd(_mm256_sub_pd(st, v_K), v_zero);

        v_sum = _mm256_add_pd(v_sum, payoff);
    }

    // Horizontal sum
    double result[4];
    _mm256_storeu_pd(result, v_sum);
    double total = result[0] + result[1] + result[2] + result[3];

    return exp(-r * T) * total / num_paths;
}
```

### Approach 3: AVX-512 (8 paths at once)

```cpp
#ifdef __AVX512F__
double monte_carlo_avx512(double S0, double K, double T, double r,
                          double sigma, int num_paths) {
    __m512d v_drift = _mm512_set1_pd((r - 0.5 * sigma * sigma) * T);
    __m512d v_vol_sqrt_t = _mm512_set1_pd(sigma * sqrt(T));
    __m512d v_S0 = _mm512_set1_pd(S0);
    __m512d v_K = _mm512_set1_pd(K);
    __m512d v_zero = _mm512_setzero_pd();
    __m512d v_sum = _mm512_setzero_pd();

    for (int i = 0; i < num_paths; i += 8) {
        __m512d z = generate_8_normals_avx512();
        __m512d exponent = _mm512_fmadd_pd(v_vol_sqrt_t, z, v_drift);
        __m512d st = _mm512_mul_pd(v_S0, fast_exp_avx512(exponent));
        __m512d payoff = _mm512_max_pd(_mm512_sub_pd(st, v_K), v_zero);
        v_sum = _mm512_add_pd(v_sum, payoff);
    }

    return exp(-r * T) * _mm512_reduce_add_pd(v_sum) / num_paths;
}
#endif
```

---

## Critical Components

### 1. Fast Random Number Generation

The RNG is often the bottleneck. Standard `mt19937` is too slow.

```cpp
// xoshiro256+ — fast, high-quality PRNG
struct Xoshiro256Plus {
    uint64_t state[4];

    uint64_t next() {
        uint64_t result = state[0] + state[3];
        uint64_t t = state[1] << 17;
        state[2] ^= state[0];
        state[3] ^= state[1];
        state[1] ^= state[2];
        state[0] ^= state[3];
        state[2] ^= t;
        state[3] = (state[3] << 45) | (state[3] >> 19);
        return result;
    }
};

// Generate uniform [0,1) from uint64
inline double u64_to_double(uint64_t x) {
    union { uint64_t i; double d; } u;
    u.i = (x >> 12) | 0x3FF0000000000000ULL;
    return u.d - 1.0;
}
```

### 2. Box-Muller Transform (Uniform → Normal)

```cpp
// Generate 2 normal random numbers from 2 uniform random numbers
void box_muller(double u1, double u2, double& z1, double& z2) {
    double r = sqrt(-2.0 * log(u1));
    double theta = 2.0 * M_PI * u2;
    z1 = r * cos(theta);
    z2 = r * sin(theta);
}

// Vectorized Box-Muller with AVX2
void box_muller_avx2(__m256d u1, __m256d u2, __m256d& z1, __m256d& z2) {
    __m256d neg2 = _mm256_set1_pd(-2.0);
    __m256d two_pi = _mm256_set1_pd(2.0 * M_PI);

    __m256d r = _mm256_sqrt_pd(_mm256_mul_pd(neg2, fast_log_avx2(u1)));
    __m256d theta = _mm256_mul_pd(two_pi, u2);

    // Need vectorized sin/cos — use polynomial approximation
    z1 = _mm256_mul_pd(r, fast_cos_avx2(theta));
    z2 = _mm256_mul_pd(r, fast_sin_avx2(theta));
}
```

### 3. Ziggurat Algorithm (Faster Normal Generation)

```cpp
// Ziggurat is faster than Box-Muller for generating normal samples
// Pre-compute table of rectangle boundaries

struct ZigguratNormal {
    static constexpr int NUM_LAYERS = 256;

    double x_table[NUM_LAYERS + 1];
    double y_table[NUM_LAYERS];
    double area;

    ZigguratNormal() { precompute_tables(); }

    double sample(Xoshiro256Plus& rng) {
        while (true) {
            uint64_t u = rng.next();
            int layer = u & 0xFF;
            double x = (int64_t)(u >> 1) * x_table[layer] * (1.0 / (1ULL << 62));

            if (fabs(x) < x_table[layer + 1]) return x;  // Fast accept

            // Slow path: handle tail and boundary
            if (layer == 0) return sample_tail(rng);
            double y_rand = u64_to_double(rng.next());
            if (y_table[layer - 1] + y_rand * (y_table[layer] - y_table[layer - 1])
                < exp(-0.5 * x * x)) return x;
        }
    }
};
```

### 4. Fast Vectorized exp()

```cpp
// AVX2 fast exp using Remez polynomial
__m256d fast_exp_avx2(__m256d x) {
    // Reduce: x = k*ln(2) + r, where |r| < ln(2)/2
    __m256d log2e = _mm256_set1_pd(1.4426950408889634);
    __m256d ln2 = _mm256_set1_pd(0.6931471805599453);

    __m256d k = _mm256_round_pd(_mm256_mul_pd(x, log2e), _MM_FROUND_TO_NEAREST_INT);
    __m256d r = _mm256_fnmadd_pd(k, ln2, x);  // r = x - k*ln2

    // Polynomial approximation of exp(r)
    __m256d c5 = _mm256_set1_pd(1.0 / 120.0);
    __m256d c4 = _mm256_set1_pd(1.0 / 24.0);
    __m256d c3 = _mm256_set1_pd(1.0 / 6.0);
    __m256d c2 = _mm256_set1_pd(0.5);
    __m256d one = _mm256_set1_pd(1.0);

    __m256d poly = _mm256_fmadd_pd(c5, r, c4);
    poly = _mm256_fmadd_pd(poly, r, c3);
    poly = _mm256_fmadd_pd(poly, r, c2);
    poly = _mm256_fmadd_pd(poly, r, one);
    poly = _mm256_fmadd_pd(poly, r, one);

    // Scale by 2^k
    __m256i ki = _mm256_cvtpd_epi32(k);
    // ... (bit manipulation to multiply by 2^k)

    return poly;
}
```

### 5. Kahan Summation (Accuracy)

```cpp
// When summing millions of values, floating-point error accumulates
// Kahan compensated summation maintains precision

struct KahanSum {
    double sum = 0;
    double comp = 0;  // Compensation for lost low-order bits

    void add(double val) {
        double y = val - comp;
        double t = sum + y;
        comp = (t - sum) - y;
        sum = t;
    }
};
```

---

## Parallelization

### Thread-Level Parallelism

```cpp
#include <thread>
#include <vector>

double parallel_monte_carlo(double S0, double K, double T, double r,
                            double sigma, int total_paths, int num_threads) {
    std::vector<std::thread> threads;
    std::vector<double> partial_sums(num_threads);
    int paths_per_thread = total_paths / num_threads;

    for (int t = 0; t < num_threads; ++t) {
        threads.emplace_back([&, t]() {
            // Each thread has its own RNG with different seed
            Xoshiro256Plus rng;
            rng.seed(t * 12345);

            double sum = 0;
            double drift = (r - 0.5 * sigma * sigma) * T;
            double vol_sqrt_t = sigma * sqrt(T);

            for (int i = 0; i < paths_per_thread; ++i) {
                double z = sample_normal(rng);
                double st = S0 * fast_exp(drift + vol_sqrt_t * z);
                sum += std::max(st - K, 0.0);
            }

            partial_sums[t] = sum;
        });
    }

    for (auto& t : threads) t.join();

    double total = 0;
    for (auto& s : partial_sums) total += s;

    return exp(-r * T) * total / total_paths;
}
```

### Anti-Thetic Variates (Variance Reduction)

```cpp
// For each Z, also use -Z → reduces variance without extra exp() calls
for (int i = 0; i < paths; i += 2) {
    double z = sample_normal(rng);

    double st_pos = S0 * fast_exp(drift + vol_sqrt_t * z);
    double st_neg = S0 * fast_exp(drift - vol_sqrt_t * z);
    // Note: drift - vol_sqrt_t * z = drift + vol_sqrt_t * (-z)

    sum += std::max(st_pos - K, 0.0);
    sum += std::max(st_neg - K, 0.0);
}
// Only generated N/2 random numbers but got N paths!
```

---

## Benchmarking

### Setup

```cpp
void benchmark() {
    constexpr int PATHS = 10'000'000;
    double S0 = 100, K = 100, T = 1.0, r = 0.05, sigma = 0.2;

    // Warmup
    volatile double warmup = monte_carlo(S0, K, T, r, sigma, 100000);

    uint64_t start = __rdtsc();
    double price = monte_carlo(S0, K, T, r, sigma, PATHS);
    uint64_t elapsed = __rdtsc() - start;

    double bs_price = black_scholes(S0, K, T, r, sigma);
    printf("MC: %.6f, BS: %.6f, Error: %.6f\n", price, bs_price, fabs(price - bs_price));
    printf("%lu cycles/op (%lu total cycles for %d paths)\n",
           elapsed / PATHS, elapsed, PATHS);
}
```

### Profiling

```bash
# Vectorization check
perf stat -e fp_arith_inst_retired.256b_packed_double ./bench

# Memory bandwidth (should be compute-bound, not memory-bound)
perf stat -e LLC-load-misses ./bench

# Compare scalar vs AVX2 vs AVX-512
./bench_scalar
./bench_avx2
./bench_avx512
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/path | < 25 | 25-50 | > 50 |
| Total for 10M paths | < 250M cycles | 250M-500M | > 500M |
| SIMD utilization | > 90% | 60-90% | < 60% |

---

## Why Rust Is Much Slower

The gap is massive (206K vs 17.5M cycles/op). Reasons:
1. **SIMD ecosystem is less mature** — Rust's `std::simd` is nightly-only; `core::arch` works but is verbose
2. **Auto-vectorization** — LLVM does auto-vectorize Rust, but explicit intrinsics in C++ are more reliable
3. **Fast math flags** — C++'s `-ffast-math` enables aggressive FP optimizations; Rust doesn't have an equivalent without unsafe
4. **Top C++ solutions likely use AVX-512** with custom exp/log approximations

---

## Common Pitfalls

1. **Using `std::mt19937`** — Too slow; use xoshiro256+ or similar
2. **Using `std::exp()`** — Full precision is unnecessary; use polynomial approximation
3. **Not vectorizing** — Scalar code wastes 4-8x throughput
4. **Box-Muller with full sin/cos** — Use polynomial approximations or Ziggurat
5. **Ignoring variance reduction** — Anti-thetic variates double effective paths for free
6. **Not using FMA instructions** — `_mm256_fmadd_pd` is both faster and more accurate
