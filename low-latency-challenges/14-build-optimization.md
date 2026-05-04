# Challenge 14: Build Optimization

## Leaderboard Reference

| Rank | Name | cycles/kop |
|------|------|------------|
| 1st | Przemek S. | 2278 |
| 2nd | blumper m. | 2290 |
| 3rd | K. Reznik | 2299 |

---

## Problem Description

**This challenge is different.** The code is frozen — you cannot modify it. Your only lever is the compilation and linking process:

- Compiler flags (`-O3`, `-march`, `-fprofile-generate`, etc.)
- Linker flags (`-flto`, `-Wl,--gc-sections`, etc.)
- Compiler choice (GCC vs Clang vs ICC)
- Build pipeline (PGO, BOLT, etc.)

---

## Core Concepts

### Why Build Optimization Matters

The same C++ source code can run at vastly different speeds depending on how it's compiled:

```
Compilation Mode          Typical Performance
───────────────────       ─────────────────
-O0 (debug)               1x (baseline)
-O2                       3-5x faster
-O3                       4-6x faster
-O3 -march=native         5-7x faster
-O3 -march=native -flto   6-8x faster
PGO + LTO                 7-10x faster
PGO + LTO + BOLT          8-12x faster
```

---

## Optimization Flags Deep Dive

### Tier 1: Basic Optimization

```bash
# Start here
-O3                    # Aggressive optimization (inlining, vectorization, etc.)
-DNDEBUG               # Disable assertions
-march=native          # Target the exact CPU you're running on
-mtune=native          # Tune scheduling for your CPU
```

### Tier 2: Additional Useful Flags

```bash
# Fine-tuning
-fomit-frame-pointer          # Free up a register (rbp on x86)
-funroll-loops                # Unroll small loops
-ffast-math                   # Relaxed floating-point (if applicable)
-fno-exceptions               # Remove exception handling overhead
-fno-rtti                     # Remove RTTI overhead
-fprefetch-loop-arrays        # Auto-insert prefetch instructions
-fno-math-errno               # Don't set errno for math functions
-ffinite-math-only            # Assume no NaN/Inf
-fno-trapping-math            # Don't generate traps for FP exceptions
-fno-signed-zeros             # -0.0 == +0.0
```

### Tier 3: Link-Time Optimization (LTO)

```bash
# LTO lets the compiler optimize across translation units
-flto                         # Enable LTO
-flto=thin                    # Thin LTO (faster compile, nearly as good)
-fwhole-program               # GCC: assume no external callers
-fvisibility=hidden           # Hide symbols by default (helps LTO)
-ffunction-sections           # Each function in its own section
-fdata-sections               # Each data object in its own section
-Wl,--gc-sections             # Remove unused sections at link time
-Wl,-O2                       # Linker optimization level
-Wl,--icf=all                 # Identical code folding
```

### Tier 4: Profile-Guided Optimization (PGO)

PGO is the single biggest optimization beyond -O3:

```bash
# Step 1: Build instrumented binary
g++ -O3 -march=native -fprofile-generate=./pgo_data -o bench_instrumented bench.cpp

# Step 2: Run with representative workload
./bench_instrumented < sample_input.txt

# Step 3: Rebuild with profile data
g++ -O3 -march=native -fprofile-use=./pgo_data -o bench_optimized bench.cpp
```

**What PGO optimizes:**
- **Branch prediction hints** — Compiler knows which branches are taken
- **Function inlining decisions** — Inline hot functions, don't inline cold ones
- **Code layout** — Put hot code together, cold code separate
- **Loop optimizations** — Unroll loops that execute many times
- **Switch statement optimization** — Reorder cases by frequency

### Tier 5: BOLT (Binary Optimization and Layout Tool)

BOLT reorders functions and basic blocks in the final binary based on runtime profiling:

```bash
# Step 1: Build optimized binary with relocations preserved
g++ -O3 -march=native -flto -fprofile-use=./pgo -Wl,--emit-relocs -o bench bench.cpp

# Step 2: Collect runtime profile with perf
perf record -e cycles:u -j any,u -o perf.data ./bench

# Step 3: Convert perf data to BOLT format
perf2bolt -p perf.data -o perf.fdata ./bench

# Step 4: Apply BOLT optimization
llvm-bolt ./bench -o ./bench_bolted -data=perf.fdata \
    -reorder-blocks=ext-tsp \
    -reorder-functions=hfsort \
    -split-functions \
    -split-all-cold \
    -icf=1 \
    -use-gnu-stack
```

**What BOLT optimizes:**
- **Function reordering** — Hot functions placed together to reduce iTLB misses
- **Basic block reordering** — Fall-through on the hot path
- **Function splitting** — Cold code moved to a separate section
- **ICF** — Identical code folding in the binary

---

## Advanced Techniques

### Compiler-Specific Optimizations

```bash
# GCC-specific
-fipa-pta                    # Inter-procedural points-to analysis
-fdevirtualize-speculatively # Speculative devirtualization
-ftree-vectorize             # Tree vectorizer (included in -O3)
-ftree-slp-vectorize         # SLP vectorizer

# Clang-specific
-mllvm -polly               # Polyhedral loop optimizer
-mllvm -polly-vectorizer=stripmine

# Intel ICC/ICX
-ipo                         # Interprocedural optimization
-qopt-report=5               # Detailed optimization report
-xHost                       # Target host architecture
```

### Custom Linker Scripts

```bash
# Control code layout in the binary
# Place hot functions at specific addresses for alignment

SECTIONS {
    .text.hot : {
        *(.text.hot*)
        *(.text.likely*)
    }
    .text : {
        *(.text*)
    }
    .text.cold : {
        *(.text.cold*)
        *(.text.unlikely*)
    }
}
```

### Memory Allocator Selection

```bash
# Even without modifying code, you can preload a faster allocator
LD_PRELOAD=/usr/lib/libjemalloc.so ./bench
LD_PRELOAD=/usr/lib/libtcmalloc.so ./bench
LD_PRELOAD=/usr/lib/libmimalloc.so ./bench
```

### Huge Pages

```bash
# Enable transparent huge pages for the binary
echo always > /sys/kernel/mm/transparent_hugepage/enabled

# Or use explicit huge pages
LD_PRELOAD=/usr/lib/libhugetlbfs.so HUGETLB_MORECORE=yes ./bench
```

---

## Benchmarking Build Configurations

### A/B Testing Framework

```bash
#!/bin/bash
# Script to compare build configurations

configs=(
    "-O3 -march=native"
    "-O3 -march=native -flto"
    "-O3 -march=native -flto -fprofile-use=./pgo"
)

for config in "${configs[@]}"; do
    echo "=== $config ==="
    g++ $config -o bench bench.cpp

    # Run 5 times, take median
    for i in $(seq 1 5); do
        taskset -c 0 ./bench 2>&1 | grep "cycles/op"
    done
    echo
done
```

### Analyzing Compiler Output

```bash
# View assembly for specific functions
g++ -O3 -march=native -S -o bench.s bench.cpp
# Or for a specific function:
objdump -d -M intel --no-show-raw-insn bench | grep -A 100 '<hot_function>'

# Compiler optimization report
g++ -O3 -march=native -fopt-info-all=opt.log bench.cpp
# Clang:
clang++ -O3 -march=native -Rpass=.* -Rpass-missed=.* bench.cpp 2> opt.log

# Check vectorization
g++ -O3 -march=native -fopt-info-vec-optimized bench.cpp
```

### What to Measure

```bash
# Instructions per cycle (higher is better)
perf stat -e cycles,instructions ./bench

# Cache behavior
perf stat -e L1-icache-load-misses,iTLB-load-misses ./bench

# Branch prediction
perf stat -e branch-misses ./bench

# Frontend vs backend stalls
perf stat -e frontend-stalls,backend-stalls ./bench
```

---

## Optimization Checklist

```
□ -O3 -march=native -mtune=native
□ -DNDEBUG
□ -fomit-frame-pointer
□ -flto (or -flto=thin for Clang)
□ -fno-exceptions -fno-rtti (if applicable)
□ -ffunction-sections -fdata-sections -Wl,--gc-sections
□ Profile-Guided Optimization (PGO)
□ BOLT post-link optimization
□ Huge pages enabled
□ Tried both GCC and Clang (pick whichever is faster)
□ Fast memory allocator (jemalloc/tcmalloc/mimalloc)
□ Verified no unexpected debug/instrumentation code left
□ Core pinning during benchmarks
□ CPU governor set to performance
```

### Target Metrics

| Metric | Elite | Good | Needs Work |
|--------|-------|------|------------|
| cycles/kop | < 2300 | 2300-2500 | > 2500 |
| Improvement over -O2 | > 30% | 15-30% | < 15% |
| PGO improvement | > 10% | 5-10% | < 5% |

---

## Common Pitfalls

1. **Forgetting -DNDEBUG** — Assertions can dominate runtime
2. **Not using PGO** — It's free performance; always try it
3. **Using -Os (optimize for size)** — Trades speed for binary size; wrong for this challenge
4. **Not testing both GCC and Clang** — They have different strengths
5. **Ignoring linker flags** — LTO and gc-sections can make a big difference
6. **Benchmarking with frequency scaling** — Set `cpufreq governor` to `performance`
7. **Not pinning to a core** — CPU migration causes cache thrashing
