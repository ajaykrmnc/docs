# Branch Prediction for System Programmers

## Introduction

Branch prediction is a critical microarchitectural technique that enables modern processors to maintain high instruction throughput despite control flow uncertainty. This document explains branch prediction mechanisms, their evolution, and practical implications for system programmers.

**Key Learning Objectives:**
- Understand why branch prediction is essential for performance
- Learn various prediction algorithms (static, dynamic, tournament)
- Understand branch target prediction and return address prediction
- Recognize the performance impact of mispredictions
- Write branch-predictor-friendly code

## 1. The Branch Problem

### 1.1 Why Branches Are Challenging

**Fundamental issue**: Pipeline must fetch next instruction, but branches determine control flow.

```asm
      cmp  %rax, %rbx
      je   target           # Branch if equal
      add  %rcx, %rdx       # Next sequential (if not taken)
      ...
target: sub  %rsi, %rdi       # Branch target (if taken)
```

**Problem**: Don't know branch outcome until comparison completes (cycle 3-4).

**Pipeline without prediction:**
```
Cycle: 1   2   3   4   5   6   7
beq:   IF  ID  EX  MEM WB
       STALL STALL (wait for branch resolution)
                  IF  ID  EX  (fetch correct path)
```

**Cost**: 2-3 cycle penalty per branch.

### 1.2 Branch Frequency

**Typical programs:**
- 15-25% of instructions are branches
- One branch every 4-6 instructions

**Impact without prediction:**
```
100 instructions:
- 20 branches
- 20 × 3 = 60 wasted cycles
- Effective CPI: 1.6 (vs ideal 1.0)
- 60% performance loss!
```

**With perfect prediction**: No stalls, CPI = 1.0

### 1.3 Types of Branches

**Conditional branches:**
```c
if (x > 0) { ... }              // Data-dependent
for (int i = 0; i < n; i++) {}  // Loop (highly predictable)
while (condition) { ... }        // Variable
```

**Unconditional branches:**
```c
goto label;                      // Always taken
function_call();                 // Requires target prediction
return value;                    // Requires return address prediction
```

**Indirect branches:**
```c
switch (x) { ... }              // Computed jump table
(*func_ptr)();                  // Function pointer call
virtual_method();               // C++ virtual function
```

## 2. Static Branch Prediction

### 2.1 Predict-Not-Taken

**Simplest scheme**: Always predict branch not taken.

```asm
loop:
    add  %rax, %rbx
    dec  %rcx
    jnz  loop         # Predict not taken (WRONG 99 times out of 100!)
```

**Performance on loops**: Terrible (1 correct, 99 mispredictions).

**When good**: Forward branches (likely not taken).

```c
if (unlikely_error) {   // Rarely taken
    handle_error();
}
// Continue...
```

### 2.2 Predict-Taken (Backward Branches)

**Heuristic**: Backward branches (loops) are usually taken.

```asm
loop:
    # Loop body
    jnz  loop         # Backward branch → Predict TAKEN (correct 99/100)
```

**Performance on loops**: Excellent (99% accuracy).

### 2.3 Compiler Hints (Profile-Guided)

**Modern approach**: Compiler provides static hints based on profiling.

```c
if (__builtin_expect(error, 0)) {  // Hint: unlikely
    handle_error();
}

// GCC/Clang attributes
if (condition) [[likely]] {
    common_path();
}
```

**Branch encoding**: Some ISAs have "likely" and "unlikely" branch variants.

**Limitation**: Static predictions can't adapt to runtime behavior.

## 3. Dynamic Branch Prediction

### 3.1 One-Bit Predictor

**Idea**: Remember last outcome for each branch.

**Structure**: Branch History Table (BHT)

```
Branch PC → Prediction (1 bit: Taken/Not Taken)

0x1000 → T (Taken)
0x1004 → N (Not Taken)
0x1008 → T (Taken)
```

**Example: Loop**
```c
for (int i = 0; i < 100; i++) {  // Branch at 0x1000
    sum += array[i];
}
```

**Branch behavior**: T T T T ... T T N (99 taken, 1 not taken)

**Predictions with 1-bit predictor:**
```
Iteration | Actual | Prediction | Correct?
    1     |   T    |     ?      | (cold start)
    2     |   T    |     T      | ✓
    3     |   T    |     T      | ✓
   ...    |  ...   |    ...     | ✓
   99     |   T    |     T      | ✓
  100     |   N    |     T      | ✗ (misprediction)
  Exit loop
  
Next time loop executes:
    1     |   T    |     N      | ✗ (misprediction)
    2     |   T    |     T      | ✓
```

**Problem**: 2 mispredictions per loop (exit + re-entry).

**Accuracy**: 98% (2 misses out of 100).

### 3.2 Two-Bit Saturating Counter

**Improvement**: Use 2-bit counter (4 states).

**States:**
```
00 = Strongly Not Taken (SN)
01 = Weakly Not Taken (WN)
10 = Weakly Taken (WT)
11 = Strongly Taken (ST)
```

**State machine:**
```
        Taken               Taken               Taken
    SN ------→ WN ------→ WT ------→ ST
    ↑           ↑           ↓           ↓
    └───────────┴───────────┴───────────┘
         Not Taken   Not Taken   Not Taken
```

**Prediction**: Taken if state ≥ 10 (WT or ST).

**Example: Same loop**
```
Iteration | Actual | State Before | Prediction | State After
    1     |   T    |      ?       |     ?      |    WT
    2     |   T    |     WT       |     T      |    ST
    3     |   T    |     ST       |     T      |    ST
   ...    |  ...   |     ST       |     T      |    ST
   99     |   T    |     ST       |     T      |    ST
  100     |   N    |     ST       |     T      |    WT (✗)
  Exit loop

Next time:
    1     |   T    |     WT       |     T      |    ST (✓)
```

**Improvement**: Only 1 misprediction per loop (exit only).

**Accuracy**: 99% (1 miss out of 100).

### 3.3 Correlating Predictors (Two-Level Adaptive)

**Observation**: Branch outcome often correlates with recent branch history.

**Example: Correlated branches**
```c
if (a == 0) {          // Branch 1
    // ...
}
if (a == 0) {          // Branch 2 (highly correlated with Branch 1!)
    // ...
}
```

**Pattern**: If B1 taken, B2 almost always taken.

**Structure**: Use global branch history to index predictor.

**Global History Register (GHR):**
```
GHR = 101100  (Last 6 branch outcomes: T N T T N N)
```

**Predictor table:**
```
GHR Value → 2-bit Counter

000000 → ST
000001 → WT
000010 → WN
...
101100 → ST
```

**Prediction**: Index table with (Branch PC XOR GHR), read counter.

**Example: (gshare predictor)**
```
Index = PC[11:0] XOR GHR[11:0]
```

**Benefit**: Captures patterns like alternating branches.

**Pattern example:**
```c
// Alternating: T N T N T N ...
if (toggle) { toggle = 0; }  // Branch 1
if (!toggle) { toggle = 1; } // Branch 2
```

**2-bit predictor**: 50% accuracy (can't learn pattern).
**Correlating predictor**: 100% accuracy (learns T→N, N→T pattern).

### 3.4 Tournament Predictor (Hybrid)

**Idea**: Different predictors work better for different branches.

**Structure**: Multiple predictors + selector.

**Components:**
1. **Local predictor**: Uses per-branch history
2. **Global predictor**: Uses global branch history  
3. **Selector**: 2-bit counter to choose between them

**Selector logic:**
```
If local predictor more accurate: Increment selector (favor local)
If global predictor more accurate: Decrement selector (favor global)

Selector ≥ 2: Use local prediction
Selector < 2: Use global prediction
```

**Example: Intel Pentium M**
- Local: 4K-entry × 10-bit history
- Global: 4K-entry gshare
- Selector: 4K-entry × 2-bit counters

**Accuracy**: 95-98% on typical code.

### 3.5 Perceptron Predictor

**Modern approach**: Machine learning (neural network) predictor.

**Structure**: Perceptron per branch.

**Weights:**
```
w[0], w[1], w[2], ..., w[n]  (integer weights)
```

**Prediction:**
```
y = w[0] +                    // Bias
    w[1] × history[0] +       // Recent branch
    w[2] × history[1] +       // Previous branch
    ...
    w[n] × history[n-1]

Predict Taken if y ≥ 0
```

**Training:**
```
If misprediction:
    If should have been Taken:
        w[i] += history[i]    // Increase weight for Taken correlation
    Else:
        w[i] -= history[i]    // Increase weight for Not Taken correlation
```

**Accuracy**: 98-99% (better than tournament on some workloads).

**Used in**: AMD Zen processors.

## 4. Branch Target Prediction

### 4.1 The Target Problem

**For conditional branches**: Target address usually known (PC-relative offset).

**For indirect branches**: Target computed at runtime.

```c
// Function pointer call
void (*func_ptr)(int);
func_ptr(arg);              // Target unknown until runtime

// Switch statement (jump table)
switch (x) {
    case 0: ... break;
    case 1: ... break;
    ...
}

// C++ virtual function
object->virtual_method();   // Target depends on object type
```

### 4.2 Branch Target Buffer (BTB)

**Structure**: Cache mapping PC → Target Address.

**BTB Entry:**
```
┌────────────────────────────────┐
│ Tag (partial PC)                │
│ Target Address                  │
│ Valid Bit                       │
│ Branch Type (conditional/unconditional/call/return) │
└────────────────────────────────┘
```

**Lookup:**
```
Index = PC[11:6]
Tag = PC[31:12]

If BTB[Index].Tag == Tag and Valid:
    Predicted Target = BTB[Index].Target
Else:
    Miss (stall or use default)
