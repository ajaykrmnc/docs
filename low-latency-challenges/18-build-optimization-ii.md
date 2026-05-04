# Challenge 18: Build Optimization II

## Problem Description

A second flags-only challenge. The code is frozen — your only lever is the compilation and linking process. This is an extension of Challenge 14 with potentially different code characteristics that benefit from different optimization strategies.

---

## Key Differences from Challenge 14

While the fundamentals are the same (compiler flags, LTO, PGO, BOLT), the second challenge likely features code that:
- Has different hotspot characteristics (more branches, different loop structures)
- May benefit from different optimization passes
- Could have different memory access patterns (cache-sensitive vs compute-bound)

---

## Advanced Techniques Beyond Challenge 14

### 1. AutoFDO (Automatic Feedback-Directed Optimization)

An alternative to traditional PGO that uses `perf` sampling instead of instrumentation:

```bash
# Step 1: Build with debug info (no instrumentation overhead!)
g++ -O3 -march=native -g -o bench bench.cpp

# Step 2: Profile with perf
perf record -b -e cycles:u ./bench  # -b enables branch recording

# Step 3: Convert to AutoFDO format
create_llvm_prof --binary=bench --profile=perf.data --out=bench.afdo

# Step 4: Rebuild with AutoFDO data
g++ -O3 -march=native -fauto-profile=bench.afdo -o bench_optimized bench.cpp
```

**Advantage over PGO**: No instrumentation overhead means the profile is more representative of real execution.

### 2. Polly (Polyhedral Optimization)

```bash
# Clang's polyhedral optimizer can restructure loop nests
clang++ -O3 -march=native -mllvm -polly -mllvm -polly-vectorizer=stripmine \
    -mllvm -polly-parallel -o bench bench.cpp
```

### 3. Compiler-Specific Tuning Knobs

```bash
# GCC: Tune specific optimization passes
-finline-limit=1000          # Increase inline threshold
--param max-unrolled-insns=200   # More aggressive unrolling
--param max-inline-insns-auto=100
--param inline-unit-growth=200
--param large-function-growth=400
--param early-inlining-insns=200

# Clang: LLVM pass tuning
-mllvm -inline-threshold=1000
-mllvm -unroll-count=8
-mllvm -vectorize-loops=true
-mllvm -vectorize-slp=true
```

### 4. Propeller (Alternative to BOLT)

Google's Propeller is another post-link optimizer:

```bash
# Build with special options
clang++ -O3 -march=native -funique-internal-linkage-names \
    -fbasic-block-sections=labels -o bench bench.cpp

# Profile
perf record -b ./bench
create_llvm_prof --binary=bench --profile=perf.data --format=propeller \
    --propeller_symorder=symorder.txt --propeller_bborder=bborder.txt

# Rebuild with Propeller data
clang++ -O3 -march=native -fbasic-block-sections=list=bborder.txt \
    -Wl,--symbol-ordering-file=symorder.txt -o bench_propeller bench.cpp
```

### 5. Machine-Specific Tuning

```bash
# Identify exact CPU model
cat /proc/cpuinfo | grep "model name"
# or
lscpu

# Intel-specific:
-march=alderlake    # 12th gen
-march=sapphirerapids  # Xeon 4th gen
-march=meteorlake   # 14th gen

# AMD-specific:
-march=znver3       # Zen 3 (Ryzen 5000)
-march=znver4       # Zen 4 (Ryzen 7000)

# Fine-grained feature control:
-mavx2 -mfma -mbmi2 -mpopcnt -mlzcnt
```

### 6. Trying Multiple Compilers

```bash
# Build with GCC, Clang, and (if available) ICC
# Each may optimize different code patterns better

# GCC
g++-13 -O3 -march=native -flto -fprofile-use=pgo_data -o bench_gcc bench.cpp

# Clang
clang++-17 -O3 -march=native -flto=thin -fprofile-use=pgo_data -o bench_clang bench.cpp

# Intel ICX
icx -O3 -xHost -ipo -qopt-report=5 -o bench_icx bench.cpp

# Compare
for bin in bench_gcc bench_clang bench_icx; do
    echo "=== $bin ==="
    taskset -c 0 ./$bin | tail -1
done
```

### 7. Link-Order and Section Placement

```bash
# Function and data ordering can affect i-cache and d-cache utilization
# Use gold linker or lld with ordering files

# Generate function ordering from profile
perf record -e cycles:u -g ./bench
perf report --sort=symbol | head -50  # Identify hot functions

# Create ordering file (hot functions first)
echo "hot_function_1
hot_function_2
hot_function_3" > function_order.txt

# Link with ordering
g++ -O3 -march=native -flto -Wl,--section-ordering-file=function_order.txt \
    -o bench bench.cpp
```

### 8. Exhaustive Flag Search

```bash
#!/bin/bash
# Systematically test flag combinations

BASE="-O3 -march=native -DNDEBUG"
EXTRAS=(
    "-flto"
    "-flto -fwhole-program"
    "-fomit-frame-pointer"
    "-funroll-loops"
    "-fprefetch-loop-arrays"
    "-fno-exceptions"
    "-fno-rtti"
    "-fno-plt"
    "-ffast-math"
)

best_time=999999
best_flags=""

# Test all 2^N combinations of extras
for ((mask=0; mask < (1 << ${#EXTRAS[@]}); mask++)); do
    flags="$BASE"
    for ((i=0; i < ${#EXTRAS[@]}; i++)); do
        if ((mask & (1 << i))); then
            flags="$flags ${EXTRAS[$i]}"
        fi
    done

    g++ $flags -o bench bench.cpp 2>/dev/null || continue

    # Run 3 times, take minimum
    time=$(for run in 1 2 3; do
        taskset -c 0 ./bench 2>&1 | grep -oP '\d+(?= cycles)'
    done | sort -n | head -1)

    if [ "$time" -lt "$best_time" ]; then
        best_time=$time
        best_flags=$flags
        echo "NEW BEST: $time cycles with: $flags"
    fi
done

echo "WINNER: $best_time cycles with: $best_flags"
```

---

## Performance Analysis Deep Dive

### Identifying the Bottleneck Type

```bash
# 1. Is it frontend-bound? (instruction fetch/decode)
perf stat -e frontend-stalls,instructions ./bench
# If frontend stalls > 20%, try: BOLT, function reordering, code alignment

# 2. Is it backend-bound? (execution units)
perf stat -e backend-stalls,instructions ./bench
# If backend stalls > 30%, try: -funroll-loops, SIMD hints, -ffast-math

# 3. Is it memory-bound?
perf stat -e L1-dcache-load-misses,LLC-load-misses ./bench
# If LLC miss rate > 1%, try: prefetch hints, data layout, huge pages

# 4. Is it branch-bound?
perf stat -e branch-misses,branches ./bench
# If branch miss rate > 2%, try: PGO (biggest impact), cmov hints
```

### Compiler Optimization Reports

```bash
# GCC: Detailed inline report
g++ -O3 -march=native -fopt-info-inline-all 2> inline.log bench.cpp

# GCC: Vectorization report
g++ -O3 -march=native -fopt-info-vec-all 2> vec.log bench.cpp

# Clang: All optimization remarks
clang++ -O3 -march=native -Rpass='.*' -Rpass-missed='.*' \
    -Rpass-analysis='.*' 2> all_remarks.log bench.cpp

# Look for missed optimizations
grep "missed" all_remarks.log | sort | uniq -c | sort -rn | head -20
```

---

## Checklist for Build Optimization II

```
Phase 1: Baseline
□ -O3 -march=native -DNDEBUG
□ -fomit-frame-pointer
□ -fno-exceptions -fno-rtti
□ Establish baseline measurement (5 runs, take median)

Phase 2: LTO
□ -flto (full) vs -flto=thin
□ -ffunction-sections -fdata-sections -Wl,--gc-sections
□ -Wl,--icf=all

Phase 3: PGO
□ Build instrumented binary
□ Run with representative workload
□ Rebuild with profile data
□ (Alternative: try AutoFDO)

Phase 4: Post-Link
□ BOLT optimization
□ (Alternative: Propeller)
□ Huge page support

Phase 5: Micro-Tuning
□ Test GCC vs Clang vs ICC
□ Adjust inline thresholds
□ Try -ffast-math (if applicable)
□ Try Polly (Clang only)
□ Machine-specific -march flags

Phase 6: Environment
□ CPU governor: performance
□ Core pinning
□ Disable turbo boost for consistent results
□ Transparent huge pages
□ Alternative allocator (jemalloc/tcmalloc)
```

---

## Common Pitfalls

1. **Applying Challenge 14 flags blindly** — Different code benefits from different flags
2. **Not profiling first** — Understand the bottleneck before optimizing
3. **Over-inlining** — Can increase code size and hurt i-cache; tune the threshold
4. **Ignoring PGO training workload quality** — PGO is only as good as its training data
5. **Not testing compiler alternatives** — GCC and Clang can differ by 10-20% on the same code
6. **Forgetting environment setup** — CPU frequency scaling, other processes running
