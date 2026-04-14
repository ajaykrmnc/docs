# Out-of-Order Execution for System Programmers

## Introduction

Out-of-order execution (OoOE) is a critical microarchitectural technique that allows modern processors to execute instructions in a different order than the program specifies, while maintaining the illusion of in-order execution. This document explains how OoOE works and its implications for system programmers.

**Key Learning Objectives:**
- Understand why out-of-order execution is necessary
- Learn the key components: register renaming, reservation stations, reorder buffer
- Understand Tomasulo's algorithm and its modern variants
- Recognize the performance benefits and security implications
- Write code that leverages OoOE effectively

## 1. The Motivation for Out-of-Order Execution

### 1.1 The In-Order Limitation

**Problem: In-order pipelines stall on dependencies**

```asm
# Example instruction sequence
lw   %r1, 0(%r2)      # Load from memory (high latency)
add  %r3, %r1, %r4    # Depends on %r1 (MUST WAIT)
sub  %r5, %r6, %r7    # Independent! But stalled in in-order pipeline
mul  %r8, %r9, %r10   # Independent! But stalled
```

**In-order execution timeline:**
```
Cycle: 1   2   3   4   5   6   7   8   9   10  11  12
lw:    IF  ID  EX  EX  EX  MEM WB
add:       IF  ID  STALL STALL STALL EX  MEM WB
sub:           IF  STALL STALL STALL ID  EX  MEM WB  
mul:               STALL STALL STALL IF  ID  EX  EX  MEM

Problem: sub and mul are independent but blocked by add!
```

**Performance impact:**
- Load latency: 5 cycles
- 3 independent instructions wasted 3 cycles each
- Total waste: 9 stall cycles

### 1.2 The Out-of-Order Solution

**Out-of-order execution timeline:**
```
Cycle: 1   2   3   4   5   6   7   8   9   10
lw:    IF  ID  EX  EX  EX  MEM WB
sub:       IF  ID  EX  MEM WB          (executes immediately!)
mul:           IF  ID  EX  EX  MEM WB  (executes immediately!)
add:               IF  ID  STALL STALL EX  MEM WB (waits for lw)

Result: sub and mul execute while add waits
Speedup: 10 cycles vs 12 cycles (20% improvement)
```

**Key insight**: Execute independent instructions while waiting for dependencies.

### 1.3 Why Not Just Reorder in Compiler?

**Compiler limitations:**

```c
int compute(int *array, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += array[i];  // Load latency unknown at compile time
    }
    return sum;
}
```

**Challenges:**
1. **Unknown latencies**: Memory access time depends on cache hits/misses
2. **Pointer aliasing**: Compiler can't always prove memory independence
3. **Function calls**: Unknown side effects
4. **Interrupts/Exceptions**: Must maintain precise exception semantics

**Hardware OoOE advantages:**
- Dynamic decisions based on actual latencies
- Speculative execution past branches
- Handles all instruction types uniformly

## 2. Out-of-Order Execution Architecture

### 2.1 High-Level Overview

**OoOE processor structure:**

```
┌─────────────────────────────────────────────────────────────┐
│                      FETCH & DECODE                          │
│                    (In-order front-end)                      │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  REGISTER RENAMING                           │
│         (Eliminate false dependencies)                       │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│             INSTRUCTION QUEUE / SCHEDULER                    │
│      (Issue instructions when operands ready)                │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                EXECUTION UNITS                               │
│    [ALU] [ALU] [MUL] [DIV] [Load] [Store] [Branch]          │
│            (Out-of-order execution)                          │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   REORDER BUFFER                             │
│          (Commit results in program order)                   │
│              (In-order back-end)                             │
└─────────────────────────────────────────────────────────────┘
```

**Three key phases:**
1. **In-order front-end**: Fetch, decode, rename
2. **Out-of-order execution**: Schedule and execute when ready
3. **In-order retirement**: Commit results in program order

### 2.2 The Register Renaming Problem

**False dependencies** occur when instructions use the same architectural register but don't have true data dependency.

**Example: Write-After-Write (WAW) Hazard**
```asm
add  %r1, %r2, %r3    # r3 = r2 + r3
mul  %r4, %r5, %r6    # r6 = r5 * r6 (independent)
sub  %r7, %r8, %r3    # r3 = r8 - r3 (overwrites r3, but independent of add)
```

**Problem in in-order execution:**
```
Cycle: 1   2   3   4   5   6   7
add:   IF  ID  EX  MEM WB
mul:       IF  ID  EX  EX  MEM WB
sub:           IF  STALL (must wait for add to write r3)
```

**False dependency**: sub doesn't actually need add's result, but both write to %r3!

**Example: Write-After-Read (WAR) Hazard**
```asm
add  %r1, %r2, %r3    # r3 = r2 + r3 (reads r3)
sub  %r7, %r8, %r3    # r3 = r8 - r3 (writes r3)
```

**If sub executes before add**: add would read wrong value of r3.

### 2.3 Register Renaming Solution

**Idea**: Map architectural registers (visible to programmer) to physical registers (hidden hardware registers).

**Architectural registers**: %r0 - %r15 (16 registers in our example)
**Physical registers**: P0 - P127 (128 physical registers in hardware)

**Register Allocation Table (RAT):**

```
Architectural → Physical
%r0 → P10
%r1 → P23
%r2 → P45
%r3 → P67
...
```

**Renaming example:**

```asm
# Original code
add  %r1, %r2, %r3    # r3 = r2 + r3
mul  %r4, %r5, %r6    # r6 = r5 * r6
sub  %r7, %r8, %r3    # r3 = r8 - r3 (reuses r3)
and  %r9, %r3, %r10   # r10 = r9 & r3 (uses sub's r3)

# After renaming (internal representation)
add  P23, P45, P67    # P67 = P23 + P45 (r3 → P67)
mul  P12, P34, P56    # P56 = P12 * P34 (r6 → P56)
sub  P78, P89, P90    # P90 = P78 - P89 (r3 → P90, new physical register!)
and  P91, P90, P92    # P92 = P91 & P90 (r3 → P90, reads sub's result)

# Register Allocation Table updates:
# Initially: r3 → P67
# After sub: r3 → P90 (new mapping!)
```

**Result**: No false dependencies! add and sub can execute in parallel.

### 2.4 The Reorder Buffer (ROB)

**Purpose**: Maintain program order for commitment (retirement) of instructions.

**Structure**: Circular buffer with entries for each in-flight instruction.

**ROB Entry:**
```
┌──────────────────────────────────────────────┐
│ Instruction PC                                │
│ Destination Register (architectural)         │
│ Physical Register (renamed)                   │
│ Result Value                                  │
│ Exception Status                              │
│ Ready Bit                                     │
└──────────────────────────────────────────────┘
```

**Example: ROB in action**

```asm
# Program
1: add  %r1, %r2, %r3
2: lw   %r4, 0(%r5)
3: mul  %r6, %r7, %r8
4: sub  %r9, %r3, %r4
```

**ROB state (instructions in flight):**

```
ROB Entry | PC  | Instruction      | Dest | Physical | Value | Ready?
----------|-----|------------------|------|----------|-------|--------
  0       | 100 | add r1,r2,r3     | r3   | P10      | 42    | Yes
  1       | 104 | lw r4,0(r5)      | r4   | P20      | -     | No (waiting for memory)
  2       | 108 | mul r6,r7,r8     | r8   | P30      | 100   | Yes
  3       | 112 | sub r9,r3,r4     | r4   | P40      | -     | No (waiting for r4)
```

**Commit (retirement) process:**
- Commit in program order (entry 0, then 1, then 2, ...)
- Entry 0 ready → commit (update architectural state)
- Entry 1 not ready → STOP (even though entry 2 is ready!)
- Wait until entry 1 ready, then commit entries 1, 2, 3 in order

**Why in-order commitment?**
- Precise exceptions: If instruction 2 causes exception, instructions 3+ should not be visible
- Speculation: If branch mispredicted, can discard all instructions after branch

## 3. Tomasulo's Algorithm

### 3.1 Historical Context

**Developed by**: Robert Tomasulo (IBM, 1967)
**First implementation**: IBM System/360 Model 91
**Innovation**: Hardware-based dynamic scheduling with register renaming

**Why revolutionary:**
- No compiler support needed
- Handles dynamic memory latencies
- Works with legacy code

### 3.2 Reservation Stations

**Concept**: Buffers that hold instructions waiting for operands.

**Reservation Station Entry:**
```
┌──────────────────────────────────────────────┐
│ Operation (ADD, MUL, LOAD, etc.)             │
│ Source 1: Value or Tag                       │
│ Source 2: Value or Tag                       │
│ Destination Tag                              │
│ Busy Bit                                     │
└──────────────────────────────────────────────┘
```

**Tag**: Identifier for physical register or reservation station producing the value.

### 3.3 Execution Flow

**Step 1: Issue**
- Fetch instruction from queue
- Allocate reservation station
- Read operands from register file or tag if not ready
- Update Register Allocation Table

**Step 2: Execute**
- Wait until all operands available
- Send to execution unit when ready
- May execute out-of-order!

**Step 3: Write Result (Broadcast)**
- Broadcast result on Common Data Bus (CDB)
- All waiting reservation stations capture matching tags
- Update register file
- Free reservation station

**Step 4: Commit (in ROB-based design)**
- Reorder buffer commits results in program order
- Handle exceptions

### 3.4 Detailed Example

**Code:**
```asm
lw   %f0, 0(%r1)       # Load floating-point value
mul  %f4, %f0, %f2     # f4 = f0 * f2 (depends on load)
add  %f6, %f0, %f8     # f6 = f0 + f8 (depends on load)
sub  %f10, %f4, %f6    # f10 = f4 - f6 (depends on mul and add)
```

**Initial state:**
```
Register File:
f0: <empty>
f2: 3.0
f8: 5.0

Reservation Stations (Load):
RS1: [Busy: N]

Reservation Stations (Multiply):
RS2: [Busy: N]

Reservation Stations (Add):
RS3: [Busy: N]
RS4: [Busy: N]
```

**Cycle 1: Issue lw**
```
RS1: [Busy: Y] [Op: LOAD] [Addr: r1+0] [Dest: RS1]
RAT: f0 → RS1 (will be produced by RS1)
```

**Cycle 2: Issue mul**
```
RS2: [Busy: Y] [Op: MUL] [Src1: RS1] [Src2: 3.0] [Dest: RS2]
RAT: f4 → RS2
Note: Src1 is tagged RS1 (not ready yet)
```

**Cycle 3: Issue add**
```
RS3: [Busy: Y] [Op: ADD] [Src1: RS1] [Src2: 5.0] [Dest: RS3]
RAT: f6 → RS3
```

**Cycle 4: Issue sub**
```
RS4: [Busy: Y] [Op: SUB] [Src1: RS2] [Src2: RS3] [Dest: RS4]
RAT: f10 → RS4
Note: Both sources tagged (not ready)
```

**Cycle 5: Load completes, broadcasts value 2.0 with tag RS1**
```
RS1: Broadcasts (RS1, 2.0)
RS2: Captures RS1 → Src1 becomes 2.0 (now ready to execute!)
RS3: Captures RS1 → Src1 becomes 2.0 (now ready to execute!)
Register File: f0 = 2.0
```

**Cycle 6-8: Mul executes (3 cycles)**
```
RS2 executes: 2.0 * 3.0 = 6.0
```

**Cycle 6-7: Add executes (2 cycles, in parallel with Mul!)**
```
RS3 executes: 2.0 + 5.0 = 7.0
```

**Cycle 9: Mul broadcasts**
```
RS2: Broadcasts (RS2, 6.0)
RS4: Captures RS2 → Src1 becomes 6.0
Register File: f4 = 6.0
```

**Cycle 8: Add broadcasts**
```
RS3: Broadcasts (RS3, 7.0)
RS4: Captures RS3 → Src2 becomes 7.0 (now ready!)
Register File: f6 = 7.0
```

**Cycle 10: Sub executes**
```
RS4 executes: 6.0 - 7.0 = -1.0
```

**Cycle 11: Sub broadcasts**
```
RS4: Broadcasts (RS4, -1.0)
Register File: f10 = -1.0
```

**Key observations:**
- Mul and Add executed in parallel (both waiting for same Load)
- Sub started as soon as both operands ready
- No compiler scheduling needed!

## 4. Modern OoOE Implementation

### 4.1 Physical Register File

**Modern approach**: Use unified physical register file instead of copying values.

**Benefits:**
- No data copying (just pointer updates)
- Simpler broadcast mechanism
- Better power efficiency

**Example: Intel Skylake**
```
Architectural registers: 16 (x86-64)
Physical integer registers: 180
Physical vector registers: 168
```

### 4.2 Instruction Window Size

**Instruction window**: Maximum number of in-flight instructions.

**Limited by:**
- ROB size
- Physical register count
- Reservation station count

**Modern processors:**
- Intel Skylake: 224-entry ROB
- Apple M1: 630-entry ROB
- AMD Zen 3: 256-entry ROB

**Larger window = more parallelism** but higher complexity/power.

### 4.3 Load-Store Queues

**Challenge**: Memory operations have ambiguous addresses.

```asm
sw   %r1, 0(%r2)      # Store to address r2+0
lw   %r3, 0(%r4)      # Load from address r4+0
```

**Question**: Do these alias (same address)?
**Answer**: Unknown until addresses computed!

**Solution: Load-Store Queue**

**Store Queue Entry:**
```
Address | Data | Valid | Committed?
```

**Load Queue Entry:**
```
Address | Physical Reg | Valid | Executed?
```

**Load execution:**
1. Compute address
2. Check Store Queue for matching address (store forwarding)
3. If match: Use store data (bypass memory)
4. If no match: Issue memory load
5. Track in Load Queue for violation detection

**Memory ordering violation:**
```asm
lw   %r1, 0(%r2)      # Executes early (address r2)
sw   %r3, 0(%r4)      # Older store (address r4 = r2)
```

**If load executes before store, but they alias**: Violation!
- **Detection**: Store compares address with younger loads when executing
- **Recovery**: Flush load and all dependent instructions, re-execute

## 5. Speculative Execution

### 5.1 Branch Speculation

**Problem**: Don't know branch outcome until executed.

**Solution**: Predict and execute speculatively.

```asm
      beq  %r1, %r2, target
      add  %r3, %r4, %r5    # Speculative (predict not taken)
      mul  %r6, %r7, %r8    # Speculative
      ...
target: sub  %r9, %r10, %r11
```

**If prediction correct**: Continue normally
**If prediction wrong**: Flush speculative instructions, restart from target

**Rollback mechanism:**
- ROB tracks all speculative instructions
- Don't commit (update architectural state) until branch resolves
- If mispredicted: Invalidate ROB entries after branch

### 5.2 Aggressive Speculation

**Modern processors speculate on:**
- Branch direction
- Branch target (indirect branches)
- Memory disambiguation
- Value prediction (rare)

**Speculation depth**: How far ahead to speculate.

**Example: Nested branches**
```c
if (a > 0) {              // Branch 1 (predict taken)
    if (b > 0) {          // Branch 2 (predict taken)
        if (c > 0) {      // Branch 3 (predict not taken)
            x = 1;
        }
    }
}
```

**Processor may execute speculatively 100+ instructions ahead!**

## 6. Performance Implications

### 6.1 ILP Extraction

**Good code for OoOE (high ILP):**
```c
for (int i = 0; i < n; i++) {
    a[i] = b[i] + c[i];  // Independent iterations
    d[i] = e[i] * f[i];  // Independent iterations
}
```

**Bad code for OoOE (low ILP):**
```c
int sum = 0;
for (int i = 0; i < n; i++) {
    sum = sum + array[i];  // Dependency chain
}
```

### 6.2 Memory-Level Parallelism (MLP)

**OoOE can issue multiple loads:**
```c
int a = array[i];     // Load 1 (cache miss)
int b = array[j];     // Load 2 (cache miss, parallel!)
int c = array[k];     // Load 3 (cache miss, parallel!)
result = a + b + c;   // Wait for all
```

**Benefit**: Multiple cache misses served in parallel (~3× faster than sequential).

### 6.3 Instruction Window Optimization

**Keep instruction window full:**

```c
// Bad: Short loop, hard to keep window full
for (int i = 0; i < 4; i++) {
    sum += array[i];
}

// Good: Unrolled, easier to fill window
sum += array[0];
sum += array[1];
sum += array[2];
sum += array[3];
```

## 7. Security Implications

### 7.1 Spectre Attack

**Vulnerability**: Speculative execution leaves traces in cache.

**Attack:**
```c
if (index < array1_size) {           // Bounds check
    value = array1[index];           // Speculatively access (may be out of bounds)
    temp = array2[value * 4096];     // Leak value via cache
}
```

**Exploit**:
1. Train branch predictor to expect index < array1_size
2. Call with out-of-bounds index
3. Speculatively reads secret value
4. Speculatively accesses array2 (brings into cache)
5. Branch misprediction detected, rollback
6. **But cache state not rolled back!**
7. Attacker measures array2 access times to infer value

**Mitigations:**
- Fence instructions after bounds checks
- Index masking
- Architectural changes (flush cache on context switch)

### 7.2 Meltdown Attack

**Vulnerability**: Speculative execution bypasses privilege checks.

**Example:**
```c
// Kernel memory access (should fault)
value = *kernel_address;          // Speculatively executes!
temp = array[value * 4096];       // Leaks via cache
// Fault delivered, rollback
```

**Mitigation**: Kernel Page Table Isolation (KPTI)

## 8. Programming Guidelines

### 8.1 Write Parallelizable Code

```c
// Good: Independent operations
for (int i = 0; i < n; i++) {
    c[i] = a[i] + b[i];
}

// Bad: Sequential dependency
for (int i = 1; i < n; i++) {
    a[i] = a[i-1] + b[i];  // Depends on previous iteration
}
```

### 8.2 Break Dependency Chains

```c
// Bad: Single accumulator
int sum = 0;
for (int i = 0; i < n; i++) {
    sum += array[i];
}

// Good: Multiple accumulators
int sum0 = 0, sum1 = 0, sum2 = 0, sum3 = 0;
for (int i = 0; i < n-3; i += 4) {
    sum0 += array[i];
    sum1 += array[i+1];
    sum2 += array[i+2];
    sum3 += array[i+3];
}
int sum = sum0 + sum1 + sum2 + sum3;
```

### 8.3 Enable Memory-Level Parallelism

```c
// Good: Loads issued together
int a = ptr1[i];
int b = ptr2[i];
int c = ptr3[i];
int d = ptr4[i];
result = a + b + c + d;

// Bad: Sequential loads with dependencies
int a = ptr1[i];
int b = ptr2[a];   // Depends on a
int c = ptr3[b];   // Depends on b
int d = ptr4[c];   // Depends on c
```

## 9. Summary

**Key Takeaways:**
1. OoOE executes instructions when ready, not in program order
2. Register renaming eliminates false dependencies
3. Reorder buffer ensures in-order commitment
4. Tomasulo's algorithm enables dynamic scheduling
5. Speculation amplifies OoOE benefits
6. Security vulnerabilities arise from speculative execution

**Performance Benefits:**
- Hide memory latency (L1: 4 cycles, L3: 40 cycles, RAM: 200+ cycles)
- Extract instruction-level parallelism
- Enable memory-level parallelism
- 2-4× speedup vs in-order on typical code

**Related Documents:**
- Microarchitecture and Pipelining
- Branch Prediction
- Cache Coherency Protocols

---

*Last updated: 2026-04-11*
