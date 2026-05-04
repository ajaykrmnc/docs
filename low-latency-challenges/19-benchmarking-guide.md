# Universal Benchmarking Guide for Low-Latency Challenges

A comprehensive methodology for measuring, profiling, and optimizing performance across all challenges.

---

## Part 1: Measurement Fundamentals

### The rdtsc Instruction

All challenges measure performance in **CPU cycles** using the `rdtsc` (Read Time Stamp Counter) instruction.

```cpp
#include <x86intrin.h>

// Basic cycle measurement
uint64_t start = __rdtsc();
// ... code to measure ...
uint64_t end = __rdtsc();
uint64_t cycles = end - start;
```

#### rdtsc Pitfalls and Solutions

```cpp
// Problem 1: Out-of-order execution can reorder rdtsc
// Solution: Use rdtscp (serializing) or lfence + rdtsc

// Option A: rdtscp (reads TSC and waits for prior instructions to complete)
uint64_t start, end;
unsigned int aux;
start = __rdtscp(&aux);
// ... code ...
end = __rdtscp(&aux);

// Option B: lfence + rdtsc (fully serialized)
_mm_lfence();
start = __rdtsc();
// ... code ...
_mm_lfence();
end = __rdtsc();

// Problem 2: Core migration changes TSC
// Solution: Pin thread to a specific core
cpu_set_t cpuset;
CPU_ZERO(&cpuset);
CPU_SET(0, &cpuset);
pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
```

### Statistical Rigor

```cpp
// Don't take the average — take the median or minimum of multiple runs
// Outliers are caused by interrupts, context switches, cache cold-start

#include <algorithm>
#include <vector>

uint64_t benchmark_robust(auto&& func, int repetitions = 100) {
    std::vector<uint64_t> measurements(repetitions);

    for (int i = 0; i < repetitions; ++i) {
        _mm_lfence();
        uint64_t start = __rdtsc();
        func();
        _mm_lfence();
        uint64_t end = __rdtsc();
        measurements[i] = end - start;
    }

    std::sort(measurements.begin(), measurements.end());

    // Report multiple statistics
    uint64_t min = measurements[0];
    uint64_t median = measurements[repetitions / 2];
    uint64_t p99 = measurements[repetitions * 99 / 100];
    uint64_t max = measurements[repetitions - 1];

    printf("Min: %lu, Median: %lu, P99: %lu, Max: %lu\n",
           min, median, p99, max);

    return median;  // Most stable metric
}
```

### Preventing Compiler Optimization of Benchmarked Code

```cpp
// Problem: Compiler optimizes away code with no observable side effects

// Solution 1: volatile sink
volatile int sink;
for (int i = 0; i < N; ++i) {
    sink = compute(data[i]);
}

// Solution 2: asm volatile (Google Benchmark style)
template<typename T>
void DoNotOptimize(T& value) {
    asm volatile("" : "+r"(value) : : "memory");
}

for (int i = 0; i < N; ++i) {
    auto result = compute(data[i]);
    DoNotOptimize(result);
}

// Solution 3: escape memory
void ClobberMemory() {
    asm volatile("" : : : "memory");
}
```

---

## Part 2: System Preparation

### CPU Configuration

```bash
# 1. Set CPU governor to performance (disable frequency scaling)
sudo cpupower frequency-set -g performance
# Or:
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee $cpu
done

# 2. Disable turbo boost (for consistent measurements)
# Intel:
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
# AMD:
echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost

# 3. Verify frequency is stable
watch -n 0.5 "cat /proc/cpuinfo | grep MHz | head -4"

# 4. Disable hyperthreading (optional, reduces noise)
echo 0 | sudo tee /sys/devices/system/cpu/cpu{N}/online  # For sibling cores
```

### System Noise Reduction

```bash
# 1. Isolate CPU cores from the scheduler
# Add to kernel boot parameters: isolcpus=2,3
# Then pin benchmark to isolated cores: taskset -c 2 ./bench

# 2. Disable IRQ balancing on benchmark cores
# Move IRQs away from benchmark cores
echo 1 | sudo tee /proc/irq/*/smp_affinity_list  # Move to core 1

# 3. Minimize background processes
sudo systemctl stop cron
sudo systemctl stop snapd
# etc.

# 4. Drop filesystem caches
echo 3 | sudo tee /proc/sys/vm/drop_caches

# 5. Lock memory to prevent swapping
ulimit -l unlimited  # Allow memory locking
# In code: mlockall(MCL_CURRENT | MCL_FUTURE);
```

### Huge Pages Setup

```bash
# Enable transparent huge pages
echo always | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# Or allocate explicit huge pages
echo 256 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Use in code:
#include <sys/mman.h>
void* buf = mmap(nullptr, size,
                 PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                 -1, 0);
```

---

## Part 3: Profiling with perf

### Essential perf Commands

```bash
# Basic statistics
perf stat ./bench

# Detailed hardware counters
perf stat -e cycles,instructions,cache-misses,cache-references,\
branch-misses,branches,L1-dcache-load-misses,L1-dcache-loads,\
L1-icache-load-misses,LLC-load-misses,LLC-loads,\
dTLB-load-misses,iTLB-load-misses \
./bench

# Sampling profile (find hotspots)
perf record -g ./bench
perf report --stdio

# Annotate source (requires -g compilation)
perf record -g ./bench
perf annotate --source hot_function

# Top-down analysis
perf stat --topdown ./bench
```

### Understanding perf Metrics

| Metric | What It Tells You | Action If High |
|--------|-------------------|----------------|
| IPC (Instructions/Cycle) | CPU efficiency | > 3.0 is good; < 1.5 → memory or branch bound |
| L1-dcache-load-misses | Data cache misses | Improve data layout, prefetching, reduce working set |
| L1-icache-load-misses | Instruction cache misses | BOLT/PGO, function reordering, reduce code size |
| LLC-load-misses | Last-level cache misses | Reduce memory footprint, use huge pages |
| branch-misses | Mispredicted branches | Use branchless code, PGO, likely/unlikely hints |
| dTLB-load-misses | TLB misses | Use huge pages, reduce memory footprint |
| frontend-stalls | Instruction fetch delays | BOLT, PGO, code alignment |
| backend-stalls | Execution unit delays | Better algorithms, SIMD |

### Flamegraph Generation

```bash
# Record with call graph
perf record -F 99 -g ./bench

# Generate flamegraph (requires FlameGraph tools)
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

---

## Part 4: Compilation for Benchmarks

### Debug vs Release Builds

```bash
# Debug (for development/correctness testing)
g++ -g -O0 -fsanitize=address,undefined -o bench_debug bench.cpp

# Release (for benchmarking)
g++ -O3 -march=native -mtune=native -DNDEBUG -fomit-frame-pointer \
    -flto -o bench_release bench.cpp

# Profile-ready (release speed + debug symbols)
g++ -O3 -march=native -DNDEBUG -g -fno-omit-frame-pointer \
    -o bench_profile bench.cpp
```

### Examining Generated Assembly

```bash
# Full assembly output
g++ -O3 -march=native -S -fverbose-asm -o bench.s bench.cpp

# Assembly for a specific function
objdump -d -M intel -j .text bench | grep -A 200 '<hot_function>'

# With source interleaving
objdump -d -S -M intel bench | less

# Compiler Explorer (godbolt.org) equivalent locally:
g++ -O3 -march=native -S -masm=intel -o /dev/stdout bench.cpp | c++filt
```

---

## Part 5: Benchmarking Patterns

### Warmup

```cpp
// Always warmup caches before measuring
void warmup(auto&& func, int iterations = 1000) {
    for (int i = 0; i < iterations; ++i) {
        func();
    }
}
```

### Prevent Dead Code Elimination

```cpp
// Ensure the compiler cannot prove the result is unused
uint64_t checksum = 0;
for (int i = 0; i < N; ++i) {
    auto result = operation(data[i]);
    checksum ^= *(uint64_t*)&result;
}
// Print checksum after measurement to prevent DCE
printf("Checksum: %lu\n", checksum);
```

### Measuring Latency vs Throughput

```cpp
// THROUGHPUT: operations are independent
uint64_t start = __rdtsc();
for (int i = 0; i < N; ++i) {
    results[i] = compute(inputs[i]);  // No data dependency between iterations
}
uint64_t throughput_cycles = (__rdtsc() - start) / N;

// LATENCY: each operation depends on the previous
int64_t value = initial;
uint64_t start = __rdtsc();
for (int i = 0; i < N; ++i) {
    value = compute(value);  // Result feeds back as input
}
uint64_t latency_cycles = (__rdtsc() - start) / N;
DoNotOptimize(value);

// These can differ by 4-10x due to instruction-level parallelism!
```

### Avoiding Measurement Bias

```cpp
// Bias 1: Sequential access patterns → unrealistically good cache behavior
// Solution: Randomize access order
std::vector<int> indices(N);
std::iota(indices.begin(), indices.end(), 0);
std::shuffle(indices.begin(), indices.end(), rng);

for (auto idx : indices) {
    result += lookup(keys[idx]);
}

// Bias 2: Small working set fits in cache → unrealistically fast
// Solution: Ensure working set matches real-world size
// If production handles 1M orders, benchmark with 1M orders

// Bias 3: Constant inputs → branch predictor learns the pattern
// Solution: Use varied, realistic inputs
```

---

## Part 6: Common Optimization Techniques

### Ranked by Impact (Across All Challenges)

| Rank | Technique | Typical Improvement | Applicable To |
|------|-----------|-------------------|---------------|
| 1 | Algorithm/data structure choice | 2-100x | All |
| 2 | Cache-friendly memory layout | 2-10x | All with data |
| 3 | PGO + LTO | 10-30% | All |
| 4 | SIMD vectorization | 2-8x | Compute-heavy |
| 5 | Branchless code | 10-50% | Branch-heavy |
| 6 | Memory ordering relaxation | 10-50% | Lock-free |
| 7 | Prefetching | 5-30% | Memory-bound |
| 8 | Custom allocators | 5-20% | Alloc-heavy |
| 9 | Loop unrolling | 5-15% | Tight loops |
| 10 | Compiler hints (likely/unlikely) | 2-10% | All |

### Quick Reference: Performance Numbers

```
Operation                           Cycles (approx)
─────────────────────────────       ────────────────
Register-to-register move           0 (eliminated)
Integer add/sub/shift               1
Integer multiply                    3
Integer divide                      20-40
L1 cache hit                        4-5
L2 cache hit                        12-15
L3 cache hit                        30-50
DRAM access                         100-300
Branch misprediction                15-20
Atomic CAS (uncontended)            10-15
Atomic CAS (contended)              50-200
System call                         100-1000
malloc/free                         50-200
std::unordered_map lookup           30-100
memcpy (small, cached)              5-20
SIMD add (8 × float)                1
SIMD multiply (8 × float)          1
sqrt                                10-15
exp/log                             20-50
sin/cos                             30-70
division (double)                   15-25
```

---

## Part 7: Reporting Results

### Standard Format

```
System: AMD Ryzen 9 5900X, 3.7 GHz base, 4.8 GHz boost
RAM: 32 GB DDR4-3600
OS: Ubuntu 22.04, kernel 5.15
Compiler: g++ 12.2, flags: -O3 -march=native -flto -fprofile-use

Challenge 07 (String Map):
  Insert: 22 cycles/op (median of 100 runs)
  Lookup: 14 cycles/op (median of 100 runs)
  Combined: 18 cycles/op

  Hardware counters (perf stat):
    IPC: 3.21
    L1 miss rate: 0.8%
    Branch miss rate: 0.2%
    Total instructions: 2.1B

  Load factor: 0.625
  Table size: 128 KB (fits in L2)
```

### Reproducibility Checklist

```
□ CPU model and frequency documented
□ OS and kernel version documented
□ Compiler version and exact flags documented
□ CPU governor set to performance
□ Turbo boost disabled (or noted)
□ Core pinning specified
□ Number of runs and aggregation method stated
□ Warmup iterations noted
□ Checksum/correctness verification included
□ perf counter data included
```
