# Microarchitecture and Pipelining for System Programmers

## Introduction

This document covers microarchitecture fundamentals and instruction pipelining based on modern processor 
design principles. Understanding how processors execute instructions at the hardware level is essential for 
writing high-performance software.

**Key Learning Objectives:**
- Understand the difference between ISA (architecture) and microarchitecture
- Learn how instruction pipelining improves throughput
- Recognize pipeline hazards and their solutions
- Understand superscalar execution
- Apply knowledge to write pipeline-friendly code

## 1. Architecture vs. Microarchitecture

### 1.1 The Distinction

**Architecture (ISA - Instruction Set Architecture)**:
- The programmer-visible interface
- Defines: instructions, registers, memory model, data types
- Examples: x86-64, ARM, RISC-V
- **Contract**: Same ISA = same program behavior

**Microarchitecture**:
- The hardware implementation of the ISA
- Defines: pipeline stages, cache sizes, execution units
- Examples: Intel Skylake, AMD Zen 3, Apple M1
- **Freedom**: Different implementations of same ISA

### 1.2 Why This Matters

```c
// Same C code
int sum = 0;
for (int i = 0; i < 1000; i++)
  sum += array[i];
```

**On different microarchitectures:**
- Intel Core i9-12900K: ~X nanoseconds
- AMD Ryzen 9 5950X: ~Y nanoseconds
- ARM Cortex-A78: ~Z nanoseconds

All execute the same x86-64 instructions, but performance varies due to:
- Pipeline depth
- Cache organization
- Execution unit count
- Branch predictor quality

### 1.3 Microarchitecture Evolution

**Example: Intel x86-64 Implementations**

| Microarchitecture | Year | Pipeline Stages | Features |
|-------------------|------|-----------------|----------|
| Pentium | 1993 | 5 | Simple in-order |
| Pentium Pro | 1995 | 14 | Out-of-order execution |
| Pentium 4 | 2000 | 20-31 | Very deep pipeline |
| Core 2 | 2006 | 14 | Return to moderate depth |
| Sandy Bridge | 2011 | 14-19 | AVX, improved µops |
| Skylake | 2015 | 14-19 | Improved cache |
| Alder Lake | 2021 | Hybrid | P-cores + E-cores |

**Key Insight**: Deeper pipelines ≠ always better. Pentium 4's deep pipeline had high branch misprediction 
penalties.

## 2. Instruction Pipelining Fundamentals

### 2.1 The Sequential Execution Problem

**Without pipelining**, each instruction completes before the next starts:

```
Instruction execution stages:
1. Fetch (IF)     - Read instruction from memory
2. Decode (ID)    - Determine operation and operands
3. Execute (EX)   - Perform ALU operation
4. Memory (MEM)   - Access data memory if needed
5. Write-back (WB)- Write result to register
```

**Example: Sequential execution (5 stages, 1 cycle each)**

```
Time:  1   2   3   4   5   6   7   8   9   10  11  12  13  14  15
Inst1: IF  ID  EX  MEM WB
Inst2:                 IF  ID  EX  MEM WB
Inst3:                                 IF  ID  EX  MEM WB

Result: 3 instructions in 15 cycles = 5 cycles per instruction (CPI = 5)
```

### 2.2 Pipelined Execution

**With pipelining**, multiple instructions execute simultaneously in different stages:

```
Time:  1   2   3   4   5   6   7   8   9
Inst1: IF  ID  EX  MEM WB
Inst2:     IF  ID  EX  MEM WB
Inst3:         IF  ID  EX  MEM WB
Inst4:             IF  ID  EX  MEM WB
Inst5:                 IF  ID  EX  MEM WB

Result: 5 instructions in 9 cycles = 1.8 CPI
Steady state: 1 instruction completes per cycle (CPI = 1)
```

**Speedup**: Ideally k-stage pipeline gives k× speedup.

### 2.3 Pipeline Analogy: Laundry

Doing laundry has 4 stages: Wash, Dry, Fold, Put-away

**Sequential approach:**
```
Load 1: [Wash] [Dry] [Fold] [Put] Load 2:                           [Wash] [Dry] [Fold] [Put]
Load 3:                                                     [Wash] [Dry] [Fold] [Put]

Time: 12 hours for 3 loads
```

**Pipelined approach:**
```
Load 1: [Wash] [Dry] [Fold] [Put]
Load 2:        [Wash] [Dry] [Fold] [Put]
Load 3:               [Wash] [Dry] [Fold] [Put]

Time: 6 hours for 3 loads (2× speedup)
```

### 2.4 Classic RISC Five-Stage Pipeline

**Stage-by-stage breakdown:**

#### Stage 1: Instruction Fetch (IF)
```
Actions:
- Read instruction from instruction cache
- Use Program Counter (PC) as address
- Increment PC by 4 (for 32-bit instructions)

Hardware:
- Instruction cache (I-cache)
- PC register
- Adder for PC+4
```

#### Stage 2: Instruction Decode (ID)
```
Actions:
- Decode instruction opcode
- Read source registers from register file
- Sign-extend immediate values
- Calculate branch target (if branch instruction)

Hardware:
- Instruction decoder
- Register file (read ports)
- Sign-extender
- Branch target adder
```

#### Stage 3: Execute (EX)
```
Actions:
- Perform ALU operation
- Calculate memory address (for load/store)
- Compare values (for branches)

Hardware:
- Arithmetic Logic Unit (ALU)
- Multiplier (may take multiple cycles)
```

#### Stage 4: Memory Access (MEM)
```
Actions:
- Read from data cache (load)
- Write to data cache (store)
- Pass through ALU result (non-memory ops)

Hardware:
- Data cache (D-cache)
- Cache controller
```

#### Stage 5: Write-Back (WB)
```
Actions:
- Write result to destination register
- Update register file

Hardware:
- Register file (write port)
```

### 2.5 Pipeline Diagram Example

**Assembly code:**
```asm
add  %r1, %r2, %r3    # r3 = r1 + r2
sub  %r4, %r3, %r5    # r5 = r4 - r3
and  %r6, %r7, %r8    # r8 = r6 & r7
or   %r9, %r10, %r11  # r11 = r9 | r10
```

**Pipeline execution:**
```
Clock: 1    2    3    4    5    6    7    8
add:   IF   ID   EX   MEM  WB
sub:        IF   ID   EX   MEM  WB
and:             IF   ID   EX   MEM  WB
or:                   IF   ID   EX   MEM  WB

Cycle 1: add fetched
Cycle 2: add decoded, sub fetched
Cycle 3: add executing, sub decoded, and fetched
Cycle 4: add in MEM, sub executing, and decoded, or fetched
Cycle 5: add writes back, sub in MEM, and executing, or decoded
Cycle 6: sub writes back, and in MEM, or executing
Cycle 7: and writes back, or in MEM
Cycle 8: or writes back
```

**Throughput**: 4 instructions in 8 cycles = 0.5 instructions/cycle (IPC)
**Steady state**: 1 instruction/cycle after pipeline fills

## 3. Pipeline Hazards

Pipeline hazards prevent the next instruction from executing in the next cycle.

### 3.1 Structural Hazards

**Definition**: Hardware cannot support all concurrent operations.

**Example: Single memory port**

```asm
lw   %r1, 0(%r2)      # Load word
add  %r3, %r4, %r5    # Add
```

**Conflict in cycle 4:**
```
Clock: 1    2    3    4    4    5    6
lw:    IF   ID   EX   MEM  WB
add:        IF   ID   EX   STALL MEM  WB
^
Both need memory!
```

**Solution**:
- Separate instruction and data caches (Harvard architecture)
- Multiple memory ports
- Pipeline stalls (performance loss)

### 3.2 Data Hazards

**Definition**: Instruction depends on result of previous instruction still in pipeline.

#### 3.2.1 Read After Write (RAW) - True Dependency

**Example:**
```asm
add  %r1, %r2, %r3    # r3 = r1 + r2
sub  %r5, %r3, %r4    # r5 = r3 - r4  (needs r3!)
```

**Problem:**
```
Clock: 1    2    3    4    5    6
add:   IF   ID   EX   MEM  WB
sub:        IF   ID   EX   MEM  WB
^
Reads r3 before add writes it!
```

**Solutions:**

**Solution 1: Stalling (Simple but slow)**
```
Clock: 1    2    3    4    5    6    7    8
add:   IF   ID   EX   MEM  WB
sub:        IF   ID   STALL STALL EX   MEM  WB
Wait for r3
```

**Solution 2: Forwarding (Bypassing)**

Hardware forwards result from later pipeline stage to earlier stage:

```
Clock: 1    2    3    4    5    6
add:   IF   ID   EX   MEM  WB
↓
sub:        IF   ID   EX   MEM  WB
↑
Forward from EX/MEM
```

**Forwarding paths:**
```
EX/MEM → EX   (1 cycle forward)
MEM/WB → EX   (2 cycle forward)
```

**Example with forwarding:**
```asm
add  %r1, %r2, %r3    # r3 = r1 + r2
sub  %r5, %r3, %r4    # r5 = r3 - r4  (forward from add's EX stage)
and  %r6, %r3, %r7    # r7 = r6 & r3  (forward from add's MEM stage)
or   %r8, %r3, %r9    # r9 = r8 | r3  (read from register file)
```

#### 3.2.2 Load-Use Hazard (Requires Stall)

**Even forwarding can't eliminate all stalls:**

```asm
lw   %r1, 0(%r2)      # Load r1 from memory
add  %r3, %r1, %r4    # Use r1 immediately
```

**Problem: Data not available until MEM stage**
```
Clock: 1    2    3    4    5    6
lw:    IF   ID   EX   MEM  WB
↓ Data available here
add:        IF   ID   STALL EX   MEM  WB
Must wait!
```

**Why stall needed**: Load doesn't have data until after MEM stage, but add needs it in EX stage.

**Solution: Compiler instruction scheduling**

```asm
# Original (1 stall)
lw   %r1, 0(%r2)
add  %r3, %r1, %r4    # Stall!

# Reordered (0 stalls)
lw   %r1, 0(%r2)
sub  %r5, %r6, %r7    # Independent instruction
add  %r3, %r1, %r4    # No stall now
```

#### 3.2.3 Write After Read (WAR) - Anti-dependency

**Not a problem in simple pipelines** (all reads happen in ID, all writes in WB).

```asm
add  %r1, %r2, %r3    # Reads r2
sub  %r2, %r4, %r5    # Writes r2
```

**No hazard in 5-stage pipeline:**
```
Clock: 1    2    3    4    5    6
add:   IF   ID   EX   MEM  WB
↑ Reads r2
sub:        IF   ID   EX   MEM  WB
↑ Writes r2 (after add reads it)
```

**Becomes a problem with out-of-order execution** (covered in separate document).

#### 3.2.4 Write After Write (WAW) - Output Dependency

**Not a problem in simple pipelines** (all writes happen in WB in order).

**Becomes a problem with out-of-order execution** (covered in separate document).

### 3.3 Control Hazards (Branch Hazards)

**Definition**: Pipeline doesn't know which instruction to fetch next due to branches.

#### 3.3.1 The Branch Problem

```asm
beq  %r1, %r2, target   # Branch if r1 == r2
add  %r3, %r4, %r5      # Next sequential instruction
sub  %r6, %r7, %r8
...
target: and  %r9, %r10, %r11   # Branch target
```

**Pipeline doesn't know branch outcome until EX stage (cycle 3):**

```
Clock: 1    2    3    4    5    6
beq:   IF   ID   EX   MEM  WB
↑ Outcome known here

add:        IF   ID   ???
↑ But we already fetched this!
```

**If branch taken**: add and sub should not execute (wasted work).
**If branch not taken**: add and sub should execute (correct).

#### 3.3.2 Solution 1: Stall Until Branch Resolved

**Simple but slow:**
```
Clock: 1    2    3    4    5    6    7
beq:   IF   ID   EX   MEM  WB
STALL STALL
IF   ID   EX   (fetch correct target)
```

**Cost**: 2-cycle penalty for every branch (20-30% of instructions are branches!).

#### 3.3.3 Solution 2: Predict Not Taken

**Assume branch not taken, fetch next sequential instruction:**

```
Clock: 1    2    3    4    5    6
beq:   IF   ID   EX   MEM  WB
add:        IF   ID   EX   MEM  WB  (if prediction correct)
```

**If prediction wrong**: Flush pipeline and fetch correct target.

```
Clock: 1    2    3    4    5    6    7
beq:   IF   ID   EX   MEM  WB
add:        IF   ID   FLUSH
sub:             IF   FLUSH
IF(target) ID   EX  ...
```

**Cost**: 0 cycles if correct, 2 cycles if wrong.

#### 3.3.4 Solution 3: Branch Prediction (Hardware)

**Modern approach**: Predict branch direction and target using hardware.

**Simple predictor**: Use history of previous branch outcomes.

```
Branch History Table (BHT):
Branch PC → Prediction (Taken/Not Taken)

0x1000 → Taken
0x1004 → Not Taken
0x1008 → Taken
```

**Loop example:**
```c
for (int i = 0; i < 100; i++) {  // Branch at 0x1000
  sum += array[i];
}
```

**Branch behavior**: Not taken 99 times, taken once.
**Prediction accuracy**: ~99% (1 misprediction out of 100).

**More sophisticated predictors** (covered in Branch Prediction document):
- 2-bit saturating counters
- Global history
- Tournament predictors
- Perceptron predictors

#### 3.3.5 Solution 4: Delayed Branches (MIPS, SPARC)

**Architectural approach**: Always execute instruction after branch.

```asm
beq  %r1, %r2, target
add  %r3, %r4, %r5      # Branch delay slot (always executes)
target: and  %r9, %r10, %r11
```

**Pipeline:**
```
Clock: 1    2    3    4    5    6
beq:   IF   ID   EX   MEM  WB
add:        IF   ID   EX   MEM  WB  (always executes)
and:             IF   ID   EX   MEM  (if branch taken)
```

**Compiler fills delay slot** with:
1. Instruction before branch (if independent)
2. Instruction from target (if branch always taken)
3. Instruction from fall-through (if branch never taken)
4. NOP (if nothing useful available)

**x86-64 doesn't use delayed branches** (uses prediction instead).

## 4. Superscalar Execution

### 4.1 Beyond Single-Issue Pipelines

**Scalar pipeline**: Executes 1 instruction per cycle (max).

**Superscalar**: Executes multiple instructions per cycle.

**Example: 2-way superscalar**
```
Clock: 1    2    3    4    5
Inst1: IF   ID   EX   MEM  WB
Inst2: IF   ID   EX   MEM  WB
Inst3:      IF   ID   EX   MEM  WB
Inst4:      IF   ID   EX   MEM  WB
Inst5:           IF   ID   EX   MEM  WB
Inst6:           IF   ID   EX   MEM  WB

Issue rate: 2 instructions per cycle
```

### 4.2 Hardware Requirements

**Multiple execution units:**
```
Fetch/Decode (2-wide)
↓
[ALU 1] [ALU 2] [Load/Store] [FP Unit] [Branch]
↓       ↓         ↓           ↓         ↓
Write-back (2-wide)
```

**Modern processors:**
- Intel Skylake: 4-wide issue, 8 execution ports
- Apple M1: 8-wide issue, 14+ execution units
- AMD Zen 3: 4-wide issue, 10 execution ports

### 4.3 Instruction-Level Parallelism (ILP)

**Example: High ILP**
```asm
add  %r1, %r2, %r3    # Independent
add  %r4, %r5, %r6    # Independent
add  %r7, %r8, %r9    # Independent
add  %r10, %r11, %r12 # Independent
```

**All can execute in parallel** (if enough execution units).

**Example: Low ILP**
```asm
add  %r1, %r2, %r3    # r3 = r1 + r2
add  %r4, %r3, %r5    # r5 = r4 + r3 (depends on r3)
add  %r6, %r5, %r7    # r7 = r6 + r5 (depends on r5)
add  %r8, %r7, %r9    # r9 = r8 + r7 (depends on r7)
```

**Must execute sequentially** (dependency chain).

### 4.4 Dependency Chains and Performance

**Critical path**: Longest dependency chain limits performance.

```c
// Low ILP (dependency chain)
int sum = 0;
for (int i = 0; i < n; i++)
  sum += array[i];  // sum depends on previous sum

// Assembly (simplified)
loop:
lw   %r1, 0(%r2)     # Load array[i]
add  %r3, %r3, %r1   # sum += array[i] (depends on previous sum)
addi %r2, %r2, 4     # i++
bne  %r2, %r4, loop
```

**Dependency chain length**: ~2-3 cycles per iteration (latency limited).

**High ILP version (loop unrolling)**:
```c
// High ILP (multiple accumulators)
int sum1 = 0, sum2 = 0;
for (int i = 0; i < n; i += 2) {
  sum1 += array[i];
  sum2 += array[i+1];
}
int sum = sum1 + sum2;

// Assembly (simplified)
loop:
lw   %r1, 0(%r2)     # Load array[i]
lw   %r5, 4(%r2)     # Load array[i+1]
add  %r3, %r3, %r1   # sum1 += array[i]
add  %r6, %r6, %r5   # sum2 += array[i+1] (independent!)
addi %r2, %r2, 8     # i += 2
bne  %r2, %r4, loop
```

**Two independent chains**: Can execute in parallel (2× throughput).

### 4.5 Execution Port Mapping (Modern x86-64)

**Intel Skylake example:**

```
Port 0: ALU, Vector ALU, Branch
Port 1: ALU, Vector ALU
Port 2: Load (AGU)
Port 3: Load (AGU)
Port 4: Store data
Port 5: ALU, Vector ALU
Port 6: ALU, Branch
Port 7: Store address (AGU)
```

**Instruction mapping:**
```asm
add  %rax, %rbx   # Can use ports 0, 1, 5, 6 (4 choices)
imul %rcx, %rdx   # Can use port 1 only (limited)
load (%rsi), %rdi # Can use ports 2, 3 (2 choices)
```

**Port contention example:**
```asm
# Good: Balanced port usage
add  %rax, %rbx   # Port 0, 1, 5, or 6
add  %rcx, %rdx   # Port 0, 1, 5, or 6
add  %rsi, %rdi   # Port 0, 1, 5, or 6
add  %r8, %r9     # Port 0, 1, 5, or 6

# Bad: All need same port (port 1)
imul %rax, %rbx   # Port 1 only
imul %rcx, %rdx   # Port 1 only (must wait)
imul %rsi, %rdi   # Port 1 only (must wait)
imul %r8, %r9     # Port 1 only (must wait)
```

## 5. Performance Analysis

### 5.1 Cycles Per Instruction (CPI)

**Ideal CPI**: 1.0 for scalar, < 1.0 for superscalar

**Real CPI** = Base CPI + Stall cycles per instruction

**Stall sources:**
- Data hazards: Load-use stalls, cache misses
- Control hazards: Branch mispredictions
- Structural hazards: Resource conflicts

**Example calculation:**

```
Program: 1,000,000 instructions
- 20% loads (200,000)
- 15% stores (150,000)
- 15% branches (150,000)
- 50% ALU ops (500,000)

Assumptions:
- 30% of loads have load-use hazard (1 cycle stall each)
- 10% of branches mispredicted (3 cycle penalty each)
- Cache hit rate: 95% (20 cycle penalty on miss)

Stall cycles:
- Load-use: 200,000 × 0.30 × 1 = 60,000
- Branch mispredict: 150,000 × 0.10 × 3 = 45,000
- Cache miss: 1,000,000 × 0.05 × 20 = 1,000,000

Total cycles: 1,000,000 (base) + 60,000 + 45,000 + 1,000,000 = 2,105,000
CPI: 2,105,000 / 1,000,000 = 2.105

Breakdown:
- Base: 1.0
- Load-use: 0.06
- Branch: 0.045
- Cache miss: 1.0 (dominant!)
```

**Key insight**: Cache misses dominate performance (covered in Cache Coherency document).

### 5.2 Instructions Per Cycle (IPC)

**IPC = 1 / CPI**

**Modern processor IPC:**
- Excellent: 3.0-4.0 (high ILP, good cache behavior)
- Good: 1.5-2.5 (typical applications)
- Poor: 0.5-1.0 (many cache misses, dependencies)

### 5.3 Measuring Pipeline Performance

**Using performance counters:**

```c
#include <stdio.h>
#include <stdint.h>

// Read Time Stamp Counter
static inline uint64_t rdtsc(void) {
  uint32_t lo, hi;
  asm volatile ("rdtsc" : "=a"(lo), "=d"(hi));
  return ((uint64_t)hi << 32) | lo;
}

void measure_performance(void) {
  uint64_t start, end;

  start = rdtsc();
  // Code to measure
  for (int i = 0; i < 1000000; i++) {
    asm volatile ("add %rax, %rbx");
  }
  end = rdtsc();

  printf("Cycles: %lu\n", end - start);
  printf("CPI: %.2f\n", (double)(end - start) / 1000000.0);
}
```

**Linux perf tool:**
```bash
# Measure IPC
perf stat -e cycles,instructions ./program

# Output:
# 1,234,567,890  cycles
#   987,654,321  instructions    # 0.80 IPC
```

## 6. Writing Pipeline-Friendly Code

### 6.1 Minimize Data Dependencies

**Bad: Long dependency chain**
```c
int sum = 0;
for (int i = 0; i < n; i++) {
  sum = sum + array[i];  // Dependency on previous sum
}
```

**Good: Multiple accumulators (loop unrolling)**
```c
int sum1 = 0, sum2 = 0, sum3 = 0, sum4 = 0;
for (int i = 0; i < n; i += 4) {
  sum1 += array[i];
  sum2 += array[i+1];
  sum3 += array[i+2];
  sum4 += array[i+3];
}
int sum = sum1 + sum2 + sum3 + sum4;
```

**Why it works**: Four independent dependency chains can execute in parallel.

### 6.2 Avoid Load-Use Stalls

**Bad: Immediate use of loaded value**
```c
int a = *ptr1;
int b = a + 5;  // Load-use stall!
```

**Good: Interleave independent work**
```c
int a = *ptr1;
int x = *ptr2;  // Independent load
int y = x + 10; // Independent work
int b = a + 5;  // No stall (a ready by now)
```

**Assembly comparison:**
```asm
# Bad (1 stall)
lw   %r1, 0(%r2)    # Load a
add  %r3, %r1, 5    # STALL! Use a immediately

# Good (0 stalls)
lw   %r1, 0(%r2)    # Load a
lw   %r4, 0(%r5)    # Load x (independent)
add  %r6, %r4, 10   # Use x (a still loading)
add  %r3, %r1, 5    # Use a (ready now)
```

### 6.3 Help the Branch Predictor

**Pattern 1: Predictable branches**
```c
// Good: Predictable (always taken in loop)
for (int i = 0; i < 1000; i++) {
  sum += array[i];
}

// Bad: Unpredictable (random data)
for (int i = 0; i < n; i++) {
  if (array[i] > threshold) {  // 50/50 random
    count++;
  }
}
```

**Pattern 2: Eliminate branches with branchless code**
```c
// Branchy version
if (x > 0) {
  sum += x;
}

// Branchless version (using conditional move)
int mask = -(x > 0);  // -1 if true, 0 if false
sum += x & mask;
```

**Assembly:**
```asm
# Branchy (misprediction penalty)
test %rdi, %rdi
jle  .skip
add  %rdi, %rax
.skip:

# Branchless (no misprediction)
xor  %rcx, %rcx
test %rdi, %rdi
cmovg %rdi, %rcx
add  %rcx, %rax
```

### 6.4 Optimize for Port Usage

**Balance instruction mix** to avoid port contention:

```c
// Bad: All multiplies (port 1 only on Skylake)
for (int i = 0; i < n; i++) {
  a[i] = b[i] * c[i] * d[i] * e[i];  // Sequential multiplies
}

// Better: Mix operations
for (int i = 0; i < n; i++) {
  int temp1 = b[i] * c[i];  // Multiply
  int temp2 = d[i] + e[i];  // Add (different port)
  a[i] = temp1 * temp2;     // Multiply
}
```

### 6.5 Cache-Aware Programming

**Principle**: Keep working set in cache (covered more in Cache Coherency doc).

```c
// Bad: Poor spatial locality
for (int i = 0; i < n; i++) {
  for (int j = 0; j < n; j++) {
    sum += matrix[j][i];  // Column-major (cache-unfriendly)
  }
}

// Good: Good spatial locality
for (int i = 0; i < n; i++) {
  for (int j = 0; j < n; j++) {
    sum += matrix[i][j];  // Row-major (cache-friendly)
  }
}
```

## 7. Advanced Pipeline Topics

### 7.1 Multi-Cycle Operations

**Not all operations complete in 1 cycle:**

| Operation | Latency (cycles) | Throughput (ops/cycle) |
|-----------|------------------|------------------------|
| Integer add | 1 | 4 (Skylake) |
| Integer mul | 3 | 1 |
| Integer div | 26-95 | 0.04-0.14 |
| FP add | 4 | 2 |
| FP mul | 4 | 2 |
| FP div | 13-14 | 0.25 |

**Latency**: Cycles until result available
**Throughput**: How many can start per cycle

**Example: FP multiply**
```asm
mulpd %xmm0, %xmm1   # Latency 4, throughput 0.5
mulpd %xmm2, %xmm3   # Can start same cycle (if port available)
```

### 7.2 Pipeline Depth Trade-offs

**Deeper pipeline:**
- ✅ Higher clock frequency (less work per stage)
- ❌ Higher branch misprediction penalty
- ❌ More complex forwarding logic
- ❌ Higher power consumption

**Shallower pipeline:**
- ✅ Lower misprediction penalty
- ✅ Simpler design
- ❌ Lower maximum clock frequency

**Modern trend**: Moderate depth (14-20 stages) with wide issue (4-8 way).

### 7.3 Simultaneous Multithreading (SMT/Hyper-Threading)

**Concept**: Run multiple threads on same physical core.

**Why it works**: Single thread rarely uses all execution units.

**Example: 2-way SMT**
```
Thread A: [ALU1] [---] [Load] [---] [---]
Thread B: [---] [ALU2] [---] [FP] [Branch]

Combined: [ALU1] [ALU2] [Load] [FP] [Branch]  (better utilization)
```

**Resource sharing:**
- Separate: PC, registers, architectural state
- Shared: Caches, execution units, pipeline

**Performance**: 20-30% improvement over single thread (not 2×).

## 8. Case Study: Intel Skylake Pipeline

### 8.1 High-Level Overview

```
Frontend:
- Fetch: 16 bytes/cycle (up to 6 instructions)
- Decode: 4 µops/cycle (macro-ops → µops)
- µop cache: 1500 µops (decoded instruction cache)

Execution:
- 8 execution ports
- 224-entry reorder buffer
- 97-entry load buffer
- 56-entry store buffer

Backend:
- L1 I-cache: 32KB, 8-way
- L1 D-cache: 32KB, 8-way
- L2 cache: 256KB, 4-way
- L3 cache: 2MB/core, 16-way (shared)
```

### 8.2 Execution Ports

**Port capabilities:**
```
Port 0: Integer ALU, Vector ALU (256-bit), Shift, Branch
Port 1: Integer ALU, Vector ALU (256-bit), Multiply (integer/FP)
Port 2: Load address (AGU), Vector ALU (simple)
Port 3: Load address (AGU), Vector ALU (simple)
Port 4: Store data
Port 5: Integer ALU, Vector ALU (256-bit), Shuffle
Port 6: Integer ALU, Branch
Port 7: Store address (AGU)
```

**Instruction examples:**
```asm
add  %rax, %rbx      # Ports 0, 1, 5, 6 (1 µop, 1 cycle latency)
imul %rcx, %rdx      # Port 1 (1 µop, 3 cycle latency)
mov  (%rsi), %rdi    # Ports 2/3 (1 µop, load)
mov  %rax, (%rbx)    # Ports 4, 7 (2 µops, store)
vaddpd %ymm0, %ymm1  # Ports 0, 1, 5 (1 µop, 4 cycle latency)
```

### 8.3 Micro-op Fusion

**Macro-fusion**: Combine compare and branch
```asm
cmp  %rax, %rbx
je   target

# Fused into single µop (no throughput penalty)
```

**Micro-fusion**: Combine operation and memory access
```asm
add  %rax, (%rbx)    # Fused into single µop (uses 2 ports)
```

### 8.4 Performance Characteristics

**Best case (tight loop of adds):**
```asm
loop:
add  %rax, %rbx
add  %rcx, %rdx
add  %rsi, %rdi
add  %r8, %r9
sub  %r10, 1
jnz  loop
```

**Analysis:**
- 5 µops/iteration
- 4 adds can use ports 0, 1, 5, 6 (no contention)
- 1 sub-branch fused (port 6)
- **Throughput**: ~1.25 cycles/iteration (4 IPC)

**Worst case (dependency chain):**
```asm
loop:
imul %rax, %rbx   # 3 cycle latency
imul %rbx, %rcx   # Depends on previous
imul %rcx, %rdx   # Depends on previous
sub  %r10, 1
jnz  loop
```

**Analysis:**
- 3 × 3 = 9 cycles for dependency chain
- **Throughput**: 9 cycles/iteration (0.44 IPC)

## 9. Practical Examples

### 9.1 Example 1: Sum Array

**Version 1: Simple (low IPC)**
```c
long sum_array_v1(long *array, long n) {
  long sum = 0;
  for (long i = 0; i < n; i++) {
    sum += array[i];
  }
  return sum;
}
```

**Assembly (simplified):**
```asm
loop_v1:
movq (%rdi), %rax       # Load array[i] (4 cycle latency)
addq %rax, %rcx         # sum += array[i] (1 cycle, depends on load)
addq $8, %rdi           # i++
cmpq %rsi, %rdi         # Compare i with n
jl   loop_v1            # Branch

# Critical path: load (4 cycles) + add (1 cycle) = 5 cycles/iteration
# IPC: ~1.0 (limited by load-to-use latency)
```

**Version 2: Unrolled 4× (higher IPC)**
```c
long sum_array_v2(long *array, long n) {
  long sum1 = 0, sum2 = 0, sum3 = 0, sum4 = 0;
  long i;
  for (i = 0; i < n - 3; i += 4) {
    sum1 += array[i];
    sum2 += array[i+1];
    sum3 += array[i+2];
    sum4 += array[i+3];
  }
  // Handle remainder
  for (; i < n; i++) {
    sum1 += array[i];
  }
  return sum1 + sum2 + sum3 + sum4;
}
```

**Assembly (simplified):**
```asm
loop_v2:
movq 0(%rdi), %rax      # Load array[i]
movq 8(%rdi), %rbx      # Load array[i+1]
movq 16(%rdi), %rcx     # Load array[i+2]
movq 24(%rdi), %rdx     # Load array[i+3]
addq %rax, %r8          # sum1 += array[i]
addq %rbx, %r9          # sum2 += array[i+1] (independent)
addq %rcx, %r10         # sum3 += array[i+2] (independent)
addq %rdx, %r11         # sum4 += array[i+3] (independent)
addq $32, %rdi          # i += 4
cmpq %rsi, %rdi
jl   loop_v2

# 4 independent chains, can execute in parallel
# IPC: ~2.5-3.0 (2.5-3× faster)
```

### 9.2 Example 2: Matrix Multiply

**Naive implementation (poor cache behavior):**
```c
void matmul_naive(double *A, double *B, double *C, int n) {
  for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {
      for (int k = 0; k < n; k++) {
        C[i*n + j] += A[i*n + k] * B[k*n + j];
      }
    }
  }
}
```

**Problems:**
- B accessed column-wise (poor spatial locality)
- Inner loop has dependency chain
- Cache misses dominate

**Optimized implementation:**
```c
void matmul_optimized(double *A, double *B, double *C, int n) {
  // Transpose B for better cache locality
  double *BT = malloc(n * n * sizeof(double));
  for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++)
      BT[j*n + i] = B[i*n + j];

  // Blocked multiplication with loop unrolling
  for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {
      double sum1 = 0, sum2 = 0, sum3 = 0, sum4 = 0;
      int k;
      for (k = 0; k < n - 3; k += 4) {
        sum1 += A[i*n + k] * BT[j*n + k];
        sum2 += A[i*n + k+1] * BT[j*n + k+1];
        sum3 += A[i*n + k+2] * BT[j*n + k+2];
        sum4 += A[i*n + k+3] * BT[j*n + k+3];
      }
      C[i*n + j] = sum1 + sum2 + sum3 + sum4;
      // Handle remainder...
    }
  }
  free(BT);
}
```

**Further optimizations:**
- Use SIMD instructions (AVX2/AVX-512)
- Tile for L1/L2/L3 cache
- Prefetch data
- Use BLAS library (highly optimized)

### 9.3 Example 3: Sorting Performance

**Insertion sort (poor branch prediction):**
```c
void insertion_sort(int *array, int n) {
  for (int i = 1; i < n; i++) {
    int key = array[i];
    int j = i - 1;
    while (j >= 0 && array[j] > key) {  // Unpredictable branch!
      array[j+1] = array[j];
      j--;
    }
    array[j+1] = key;
  }
}
```

**Branch mispredictions**: ~50% for random data (huge penalty).

**Quicksort (better, but still has branches):**
- Partition has unpredictable branches
- Better overall due to O(n log n) complexity

**Radix sort (branchless, cache-friendly):**
```c
void radix_sort(int *array, int n) {
  // No data-dependent branches
  // Sequential memory access
  // Predictable loop iterations
}
```

**Performance on random data (1M integers):**
- Insertion sort: ~2000ms (many branch mispredictions)
- Quicksort: ~150ms
- Radix sort: ~80ms (fewer branches, cache-friendly)

## 10. Summary and Best Practices

### 10.1 Key Takeaways

1. **Pipelining** improves throughput by overlapping instruction execution
2. **Hazards** (structural, data, control) reduce pipeline efficiency
3. **Forwarding** eliminates most data hazards
4. **Branch prediction** is critical for control hazards
5. **Superscalar** execution exploits ILP for higher performance
6. **Dependency chains** limit parallelism
7. **Port contention** can bottleneck superscalar processors

### 10.2 Programming Guidelines

**DO:**
- ✅ Break long dependency chains (use multiple accumulators)
- ✅ Interleave independent operations
- ✅ Write predictable branches (or eliminate them)
- ✅ Access memory sequentially (cache-friendly)
- ✅ Unroll loops moderately (2-4×)
- ✅ Use SIMD when appropriate
- ✅ Profile and measure performance

**DON'T:**
- ❌ Create long dependency chains
- ❌ Use loaded value immediately after load
- ❌ Write unpredictable branches on hot paths
- ❌ Access memory randomly (cache-unfriendly)
- ❌ Over-optimize without profiling
- ❌ Assume older optimization advice applies to modern CPUs

### 10.3 Measurement Tools

**Hardware performance counters:**
```bash
# Linux perf
perf stat -e cycles,instructions,branches,branch-misses,cache-misses ./program

# Intel VTune
vtune -collect hotspots ./program

# AMD µProf
AMDuProfCLI collect --output-dir results ./program
```

**Microbenchmarking:**
```c
#include <x86intrin.h>

uint64_t benchmark(void (*func)(void*), void *arg, int iterations) {
  uint64_t start = __rdtsc();
  for (int i = 0; i < iterations; i++) {
    func(arg);
  }
  uint64_t end = __rdtsc();
  return (end - start) / iterations;
}
```

### 10.4 Further Reading

**Papers:**
- "The Microarchitecture of Superscalar Processors" (James Smith, 1995)
- "Modern Processor Design" (Shen & Lipasti)

**Resources:**
- Intel 64 and IA-32 Architectures Optimization Reference Manual
- Agner Fog's optimization guides (agner.org/optimize)
- Computer Architecture: A Quantitative Approach (Hennessy & Patterson)

**Related documents in this series:**
- Out-of-Order Execution
- Branch Prediction
- Cache Coherency Protocols
- Virtual Memory Implementation

---

*Last updated: 2026-04-11*
