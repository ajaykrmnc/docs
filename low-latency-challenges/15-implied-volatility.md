# Challenge 15: Implied Volatility Solver

## Leaderboard Reference

| Rank | Name | C++ | Rust |
|------|------|-----|------|
| 1st | Malacarne / Malacarne | 23 cycles/op | 32 cycles/op |
| 2nd | bdcbqa / Baseline | 53 cycles/op | 731 cycles/op |
| 3rd | blumper m. / Jakub Koszuliński | 63 cycles/op | 732 cycles/op |

---

## Problem Description

Compute the implied volatility of a European option given:
- Option price (market price)
- Underlying price (spot)
- Strike price
- Time to expiration
- Risk-free rate
- Option type (call or put)

This is inverting the Black-Scholes formula: given the output (option price), find the input (volatility) that produces it.

---

## Background: Black-Scholes Formula

### Call Option Price

```
C = S·N(d₁) - K·e^(-rT)·N(d₂)

where:
  d₁ = [ln(S/K) + (r + σ²/2)T] / (σ√T)
  d₂ = d₁ - σ√T

  S = spot price
  K = strike price
  T = time to expiration (years)
  r = risk-free rate
  σ = volatility (what we're solving for)
  N(x) = cumulative normal distribution
```

### The Implied Volatility Problem

Given market price `C_market`, find `σ` such that `BS(σ) = C_market`.

This is a root-finding problem: find σ where `f(σ) = BS(σ) - C_market = 0`.

---

## Solver Approaches

### Approach 1: Newton-Raphson (Standard)

```cpp
// f(σ) = BS(σ) - C_market
// f'(σ) = vega = S·√T·N'(d₁)
// σ_{n+1} = σ_n - f(σ_n) / f'(σ_n)

double implied_vol_newton(double S, double K, double T, double r,
                          double market_price, bool is_call) {
    double sigma = 0.3;  // Initial guess
    constexpr int MAX_ITER = 20;
    constexpr double EPSILON = 1e-10;

    for (int i = 0; i < MAX_ITER; ++i) {
        double sqrtT = sqrt(T);
        double d1 = (log(S / K) + (r + sigma * sigma / 2) * T) / (sigma * sqrtT);
        double d2 = d1 - sigma * sqrtT;

        double bs_price;
        if (is_call) {
            bs_price = S * norm_cdf(d1) - K * exp(-r * T) * norm_cdf(d2);
        } else {
            bs_price = K * exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1);
        }

        double vega = S * sqrtT * norm_pdf(d1);

        double diff = bs_price - market_price;
        if (fabs(diff) < EPSILON) break;

        sigma -= diff / vega;
    }

    return sigma;
}
```

**Convergence**: Quadratic (doubles correct digits per iteration).
Typically 4-6 iterations needed.

### Approach 2: Householder's Method (Cubic Convergence)

```cpp
// Third-order method: converges in 2-3 iterations instead of 4-6
// σ_{n+1} = σ_n - f/f' · [1 + (f·f'')/(2·f'^2)]

double implied_vol_householder(double S, double K, double T, double r,
                                double market_price, bool is_call) {
    double sigma = initial_guess(S, K, T, r, market_price, is_call);

    for (int i = 0; i < 4; ++i) {
        auto [f, f1, f2] = bs_derivatives(sigma, S, K, T, r, is_call, market_price);

        // Householder update
        double correction = f / f1 * (1.0 + 0.5 * f * f2 / (f1 * f1));
        sigma -= correction;
    }

    return sigma;
}
```

### Approach 3: Rational Approximation (Fastest)

The top solutions avoid iterative methods entirely by using polynomial approximations:

```cpp
// Peter Jäckel's "Let's Be Rational" approach
// Uses rational approximations to directly compute IV
// No iteration needed for most inputs

double implied_vol_rational(double price, double F, double K, double T,
                            bool is_call) {
    double intrinsic = is_call ? std::max(F - K, 0.0) : std::max(K - F, 0.0);
    double time_value = price - intrinsic;

    if (time_value <= 0) return 0;  // Deep ITM

    // Normalized variables
    double x = log(F / K);
    double s = price / sqrt(F * K);  // Normalized price

    // Rational approximation (coefficients fitted to high precision)
    // Different branches for ATM, ITM, OTM
    double sigma;

    if (fabs(x) < 0.01) {
        // Near ATM: simple approximation
        sigma = s * sqrt(2.0 * M_PI / T);
    } else {
        // Rational function approximation
        sigma = rational_approx(x, s) / sqrt(T);
    }

    // One Newton refinement for full precision
    sigma = newton_refine(sigma, F, K, T, price, is_call);

    return sigma;
}
```

---

## Critical Speed Optimizations

### 1. Fast Normal CDF Approximation

```cpp
// Abramowitz and Stegun approximation (error < 7.5e-8)
inline double fast_norm_cdf(double x) {
    const double a1 = 0.254829592;
    const double a2 = -0.284496736;
    const double a3 = 1.421413741;
    const double a4 = -1.453152027;
    const double a5 = 1.061405429;
    const double p = 0.3275911;

    double sign = (x >= 0) ? 1.0 : -1.0;
    x = fabs(x);
    double t = 1.0 / (1.0 + p * x);
    double y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * exp(-x * x / 2);

    return 0.5 * (1.0 + sign * y);
}

// Even faster: polynomial approximation using Horner's method
inline double fast_norm_cdf_poly(double x) {
    // Hart's approximation — relative error < 1e-7
    double ax = fabs(x);
    double t = 1.0 / (1.0 + 0.2316419 * ax);
    double d = 0.3989422804014327;  // 1/sqrt(2π)
    double p = d * exp(-0.5 * x * x);
    double result = 1.0 - p * t * (0.319381530 + t * (-0.356563782 +
        t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
    return (x >= 0) ? result : 1.0 - result;
}
```

### 2. Fast exp() Approximation

```cpp
// Schraudolph's approximation of exp(x)
// Uses IEEE 754 bit manipulation — ~3 cycles vs ~20 for full exp()
inline double fast_exp(double x) {
    union { double d; int64_t i; } u;
    u.i = (int64_t)(6497320848556798LL * x + 4606794787188039895LL);
    return u.d;
}

// Better: Remez minimax polynomial
inline double fast_exp_remez(double x) {
    // Reduce x to range [0, ln(2)]
    double k = floor(x * 1.4426950408889634);  // x / ln(2)
    double r = x - k * 0.6931471805599453;     // x mod ln(2)

    // Polynomial approximation of exp(r) for r in [0, ln(2)]
    double e = 1.0 + r * (1.0 + r * (0.5 + r * (1.0/6.0 + r * (1.0/24.0))));

    // Scale by 2^k using bit manipulation
    union { double d; int64_t i; } u;
    u.d = e;
    u.i += (int64_t)k << 52;
    return u.d;
}
```

### 3. Fast log() Approximation

```cpp
// Fast log using IEEE 754 bit extraction
inline double fast_log(double x) {
    union { double d; int64_t i; } u;
    u.d = x;

    // Extract exponent and mantissa
    int64_t e = ((u.i >> 52) & 0x7FF) - 1023;
    u.i = (u.i & 0x000FFFFFFFFFFFFFLL) | 0x3FF0000000000000LL;

    // Polynomial approximation of log(mantissa)
    double m = u.d;
    double log_m = (m - 1.0) * (2.0 / (m + 1.0));  // First-order Padé

    return e * 0.6931471805599453 + log_m;
}
```

### 4. Avoid Repeated Computation

```cpp
// Pre-compute values used in every iteration
struct PrecomputedParams {
    double sqrtT;
    double exp_neg_rT;
    double log_S_K;

    PrecomputedParams(double S, double K, double T, double r) {
        sqrtT = sqrt(T);
        exp_neg_rT = exp(-r * T);
        log_S_K = log(S / K);
    }
};
```

### 5. Better Initial Guess

```cpp
// Brenner-Subrahmanyam approximation for initial guess
double initial_guess(double S, double K, double T, double C, bool is_call) {
    // For ATM options: σ ≈ C √(2π/T) / S
    double sigma = C * sqrt(2.0 * M_PI / T) / S;

    // Clamp to reasonable range
    return std::clamp(sigma, 0.01, 5.0);
}
```

### 6. SIMD Batch Computation

```cpp
// Process 4 options simultaneously using AVX
#include <immintrin.h>

void batch_implied_vol_4(__m256d S, __m256d K, __m256d T, __m256d r,
                         __m256d prices, __m256d* result) {
    __m256d sigma = _mm256_set1_pd(0.3);  // Initial guess

    for (int iter = 0; iter < 5; ++iter) {
        // Vectorized d1, d2 calculation
        __m256d sqrtT = _mm256_sqrt_pd(T);
        __m256d d1 = /* vectorized d1 formula */;
        __m256d d2 = _mm256_sub_pd(d1, _mm256_mul_pd(sigma, sqrtT));

        // Vectorized norm_cdf and BS price
        // ... (apply polynomial approximation to all 4 simultaneously)

        // Vectorized Newton step
        // sigma = sigma - (bs_price - market_price) / vega
    }

    *result = sigma;
}
```

---

## Benchmarking

### Setup

```cpp
void benchmark_iv() {
    constexpr int N = 10'000'000;

    // Generate options across the volatility surface
    std::vector<OptionParams> options(N);
    std::mt19937 rng(42);
    for (auto& o : options) {
        o.S = 100.0 + (rng() % 100 - 50) * 0.1;  // Spot: 95-105
        o.K = 100.0 + (rng() % 200 - 100) * 0.5;  // Strike: 50-150
        o.T = 0.01 + (rng() % 1000) * 0.001;       // 0.01 to 1.0 years
        o.r = 0.05;
        o.sigma = 0.1 + (rng() % 100) * 0.005;     // Vol: 10% to 60%
        o.price = black_scholes(o.S, o.K, o.T, o.r, o.sigma, true);
    }

    uint64_t start = __rdtsc();
    double total_vol = 0;
    for (auto& o : options) {
        total_vol += implied_vol(o.S, o.K, o.T, o.r, o.price, true);
    }
    uint64_t elapsed = __rdtsc() - start;

    printf("%lu cycles/op (checksum: %.4f)\n", elapsed / N, total_vol / N);
}
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/op | < 30 | 30-70 | > 70 |
| Iterations to converge | 2-3 | 4-6 | > 6 |
| Accuracy | < 1e-8 relative | < 1e-6 | < 1e-4 |

---

## Common Pitfalls

1. **Using full-precision math functions** — Fast approximations are critical
2. **Too many Newton iterations** — Good initial guess + Householder → 2-3 iterations
3. **Not exploiting put-call parity** — Compute one side, derive the other
4. **Scalar computation when batch is possible** — SIMD gives 4x throughput for free
5. **Ignoring edge cases** — Deep ITM/OTM options need different handling
6. **Starting with σ=0.5 always** — Better initial guess saves 1-2 iterations
