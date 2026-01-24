# JIT Compilation - Deep Dive into HotSpot

## Table of Contents
1. [JIT Compilation Overview](#jit-overview)
2. [HotSpot Architecture](#hotspot-architecture)
3. [Tiered Compilation](#tiered-compilation)
4. [C1 Compiler (Client)](#c1-compiler)
5. [C2 Compiler (Server)](#c2-compiler)
6. [Key Optimizations](#optimizations)
7. [Deoptimization](#deoptimization)
8. [JIT Tuning Parameters](#jit-tuning)
9. [Graal Compiler](#graal)
10. [Interview Questions](#interview-questions)

---

## JIT Compilation Overview

### What is JIT Compilation?

```
Execution Pipeline:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  .java ──► javac ──► .class (bytecode) ──► JVM ──► Machine Code            │
│                                              │                              │
│                                              ▼                              │
│                                    ┌─────────────────┐                      │
│                                    │   Interpreter   │ (slow, immediate)    │
│                                    └────────┬────────┘                      │
│                                             │                               │
│                                    ┌────────▼────────┐                      │
│                                    │  JIT Compiler   │ (fast, delayed)      │
│                                    └────────┬────────┘                      │
│                                             │                               │
│                                    ┌────────▼────────┐                      │
│                                    │  Native Code    │ (CPU executes)       │
│                                    │     Cache       │                      │
│                                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘

Why JIT instead of AOT (Ahead-of-Time)?
1. Platform independence (bytecode is portable)
2. Runtime profiling enables better optimizations
3. Speculative optimizations based on actual usage
4. Adaptive optimization (recompile hot paths)
```

### Compilation vs Interpretation Trade-off

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STARTUP vs PEAK PERFORMANCE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Performance                                                                │
│      ▲                                                                      │
│      │                              ┌─────────── JIT Compiled               │
│      │                         ┌────┘            (peak performance)         │
│      │                    ┌────┘                                            │
│      │               ┌────┘                                                 │
│      │          ┌────┘  ← Compilation happening                             │
│      │     ┌────┘                                                           │
│      │ ────┘ Interpreted                                                    │
│      │                                                                      │
│      └──────────────────────────────────────────────────────────► Time      │
│              ↑                                                              │
│         Warmup period                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## HotSpot Architecture

### HotSpot JVM Components

```
HotSpot JVM Architecture:
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HotSpot JVM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Class Loader Subsystem                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Runtime Data Areas                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │   │
│  │  │  Method  │ │   Heap   │ │  Stack   │ │    PC    │ │  Native   │  │   │
│  │  │   Area   │ │          │ │          │ │ Register │ │  Stacks   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Execution Engine                              │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │   │
│  │  │  Interpreter  │  │  JIT Compiler │  │  Garbage Collector    │   │   │
│  │  │               │  │  ┌─────┬─────┐│  │                       │   │   │
│  │  │   Template    │  │  │ C1  │ C2  ││  │  G1/ZGC/Shenandoah   │   │   │
│  │  │  Interpreter  │  │  └─────┴─────┘│  │                       │   │   │
│  │  └───────────────┘  └───────────────┘  └───────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Code Cache                                   │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │   │
│  │  │  Non-method     │  │  Profiled Code  │  │  Non-profiled Code  │  │   │
│  │  │  (JVM internal) │  │  (C1 compiled)  │  │  (C2 compiled)      │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Method Invocation Counter

```java
// HotSpot tracks method invocations and loop iterations
// When thresholds are reached, compilation is triggered

// Key counters per method:
// 1. Invocation counter: Times method called
// 2. Backedge counter: Loop iterations (backward branches)

// Compilation threshold (default with tiered compilation):
// - Tier 3 (C1): ~2000 invocations
// - Tier 4 (C2): ~15000 invocations

// Simplified counter logic:
// if (invocation_count + backedge_count > threshold) {
//     trigger_compilation(method);
// }
```

---

## Tiered Compilation

### Compilation Levels

```
Tiered Compilation Levels:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Level │ Description          │ Profiling │ Optimizations │ Speed/Quality   │
├───────┼──────────────────────┼───────────┼───────────────┼─────────────────┤
│   0   │ Interpreter          │ Basic     │ None          │ Slow/None       │
│   1   │ C1 simple            │ None      │ Basic         │ Fast/Low        │
│   2   │ C1 limited profiling │ Limited   │ Basic         │ Fast/Low        │
│   3   │ C1 full profiling    │ Full      │ Basic         │ Medium/Low      │
│   4   │ C2                   │ None      │ Aggressive    │ Slow/High       │
└───────┴──────────────────────┴───────────┴───────────────┴─────────────────┘

Typical Compilation Path:
        ┌─────┐     ┌─────┐     ┌─────┐
        │  0  │ ──► │  3  │ ──► │  4  │   (Normal path)
        └─────┘     └─────┘     └─────┘
        Interp.     C1+Prof     C2

Alternative Paths:
        ┌─────┐     ┌─────┐
        │  0  │ ──► │  4  │   (Trivial method, skip C1)
        └─────┘     └─────┘

        ┌─────┐     ┌─────┐     ┌─────┐
        │  0  │ ──► │  2  │ ──► │  3  │   (C2 busy, use C1 limited)
        └─────┘     └─────┘     └─────┘
```

### Compilation Thresholds

```java
// Default thresholds (with tiered compilation):
// Tier 3 (C1 full): ~2000 invocations
// Tier 4 (C2): ~15000 invocations

// JVM flags to view/modify:
// -XX:Tier3InvocationThreshold=2000
// -XX:Tier4InvocationThreshold=15000

// View compilation events:
// -XX:+PrintCompilation

// Output format:
// timestamp compilation_id attributes method_name size deopt
// 123  456  %  3  java.lang.String::hashCode (55 bytes)
//
// Attributes:
// % = OSR (On-Stack Replacement)
// s = synchronized method
// ! = has exception handlers
// b = blocking compilation
// n = native method wrapper
```

---

## C1 Compiler (Client)

### C1 Characteristics

```
C1 Compiler Overview:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Purpose: Fast compilation, moderate optimization                           │
│  Target: Quick startup, client applications                                 │
│                                                                             │
│  Compilation Pipeline:                                                      │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │Bytecode │──►│   HIR   │──►│   LIR   │──►│ Register│──►│ Machine │      │
│  │ Parsing │   │  Build  │   │  Build  │   │  Alloc  │   │  Code   │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                                                                             │
│  HIR = High-level Intermediate Representation (SSA form)                   │
│  LIR = Low-level Intermediate Representation (close to machine)            │
│                                                                             │
│  Optimizations performed:                                                   │
│  ✓ Method inlining (limited)                                               │
│  ✓ Constant folding                                                        │
│  ✓ Null check elimination                                                  │
│  ✓ Range check elimination                                                 │
│  ✓ Local value numbering                                                   │
│  ✗ Loop optimizations (limited)                                            │
│  ✗ Escape analysis (no)                                                    │
│                                                                             │
│  Compilation time: ~1-5ms per method                                       │
│  Code quality: ~2-3x faster than interpreter                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### C1 Profiling

```java
// C1 at Level 3 collects profiling data for C2:

// 1. Branch profiling
if (condition) {  // Track: how often true vs false?
    // ...
}

// 2. Type profiling
void process(Object obj) {
    obj.toString();  // Track: what types does obj have?
    // If always String, C2 can specialize
}

// 3. Call site profiling
interface Handler { void handle(); }
handler.handle();  // Track: which implementations called?
// If always ConcreteHandler, C2 can inline

// 4. Null profiling
if (obj != null) {  // Track: how often null?
    obj.method();
}
// If never null, C2 can eliminate null check
```

---

## C2 Compiler (Server)

### C2 Characteristics

```
C2 Compiler Overview:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Purpose: Maximum optimization, peak performance                            │
│  Target: Long-running server applications                                   │
│                                                                             │
│  Compilation Pipeline:                                                      │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │Bytecode │──►│  Ideal  │──►│  Mach   │──►│ Register│──►│ Machine │      │
│  │ Parsing │   │  Graph  │   │  Graph  │   │  Alloc  │   │  Code   │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                                                                             │
│  Ideal Graph: Sea-of-nodes IR, enables aggressive optimization             │
│  Mach Graph: Machine-specific representation                               │
│                                                                             │
│  Optimizations performed:                                                   │
│  ✓ Aggressive inlining                                                     │
│  ✓ Escape analysis + scalar replacement                                    │
│  ✓ Loop unrolling, vectorization                                           │
│  ✓ Dead code elimination                                                   │
│  ✓ Lock elision/coarsening                                                 │
│  ✓ Intrinsics (hand-optimized native code)                                 │
│  ✓ Speculative optimizations                                               │
│                                                                             │
│  Compilation time: ~50-500ms per method                                    │
│  Code quality: ~10-30x faster than interpreter                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ideal Graph (Sea of Nodes)

```
Traditional CFG vs Sea of Nodes:

Control Flow Graph (CFG):
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────┐                                                               │
│  │ Block 1 │  Instructions in sequence                                     │
│  │ a = 1   │                                                               │
│  │ b = 2   │                                                               │
│  └────┬────┘                                                               │
│       │                                                                     │
│  ┌────▼────┐                                                               │
│  │ Block 2 │  Control flow explicit                                        │
│  │ c = a+b │                                                               │
│  └─────────┘                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

Sea of Nodes (C2):
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│     ┌───┐     ┌───┐                                                        │
│     │ 1 │     │ 2 │   Values float freely                                  │
│     └─┬─┘     └─┬─┘                                                        │
│       │         │                                                           │
│       └────┬────┘                                                           │
│            │                                                                │
│         ┌──▼──┐                                                            │
│         │  +  │       Only data dependencies matter                        │
│         └──┬──┘                                                            │
│            │                                                                │
│         ┌──▼──┐                                                            │
│         │  c  │       Enables more optimization opportunities              │
│         └─────┘                                                            │
│                                                                             │
│  Control edges separate from data edges                                     │
│  Easier to move/eliminate operations                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Optimizations

### 1. Method Inlining

```java
// Before inlining:
public int calculate(int x) {
    return square(x) + cube(x);
}

private int square(int n) { return n * n; }
private int cube(int n) { return n * n * n; }

// After inlining:
public int calculate(int x) {
    return (x * x) + (x * x * x);
}

// Benefits:
// - Eliminates method call overhead
// - Enables further optimizations (constant folding, etc.)
// - Most important optimization!

// Inlining decisions based on:
// - Method size (bytecode bytes)
// - Call frequency (hot methods)
// - Call site type profile (monomorphic preferred)

// JVM flags:
// -XX:MaxInlineSize=35        (max bytecode size for always inline)
// -XX:FreqInlineSize=325      (max size for hot methods)
// -XX:MaxInlineLevel=9        (max depth of inlining)
```

### 2. Escape Analysis

```java
public class EscapeAnalysis {

    // Object ESCAPES - must be heap allocated
    public Point createPoint() {
        return new Point(1, 2);  // Returned to caller
    }

    // Object does NOT escape - can be optimized
    public int sumCoordinates() {
        Point p = new Point(3, 4);  // Never leaves method
        return p.x + p.y;
    }

    // After escape analysis + scalar replacement:
    public int sumCoordinates_optimized() {
        // No Point object created!
        int p_x = 3;
        int p_y = 4;
        return p_x + p_y;
    }
}

// Escape states:
// 1. NoEscape: Object doesn't escape method
//    → Stack allocation or scalar replacement
// 2. ArgEscape: Object passed as argument but doesn't escape
//    → May skip synchronization
// 3. GlobalEscape: Object escapes (stored in field, returned, etc.)
//    → Normal heap allocation

// JVM flags:
// -XX:+DoEscapeAnalysis       (enabled by default)
// -XX:+EliminateAllocations   (scalar replacement)
// -XX:+EliminateLocks         (lock elision)
```

### 3. Loop Optimizations

```java
// Loop Unrolling
// Before:
for (int i = 0; i < 100; i++) {
    sum += array[i];
}

// After unrolling (factor of 4):
for (int i = 0; i < 100; i += 4) {
    sum += array[i];
    sum += array[i + 1];
    sum += array[i + 2];
    sum += array[i + 3];
}
// Benefits: Fewer loop iterations, better instruction pipelining

// Loop Vectorization (SIMD)
// Before:
for (int i = 0; i < n; i++) {
    c[i] = a[i] + b[i];
}

// After vectorization (using AVX2):
// Process 8 integers at once using 256-bit registers
// vpaddd ymm0, ymm1, ymm2  (adds 8 ints in parallel)

// JVM flags:
// -XX:+UseSuperWord          (auto-vectorization)
// -XX:LoopUnrollLimit=60     (max unroll factor)
```

### 4. Null Check Elimination

```java
// Before optimization:
public void process(String s) {
    if (s != null) {
        int len = s.length();      // Implicit null check
        char c = s.charAt(0);      // Implicit null check
        String upper = s.toUpperCase();  // Implicit null check
    }
}

// After null check elimination:
public void process(String s) {
    if (s != null) {
        // JIT knows s is not null in this block
        int len = s.length();      // No null check needed
        char c = s.charAt(0);      // No null check needed
        String upper = s.toUpperCase();  // No null check needed
    }
}

// Implicit null checks use SIGSEGV trap:
// - Access memory at object offset
// - If null, SIGSEGV caught and converted to NullPointerException
// - Zero overhead when not null!
```

### 5. Intrinsics

```java
// Intrinsics: Hand-written assembly for critical methods
// JIT replaces bytecode with optimized native code

// Examples of intrinsified methods:
// - Math.sin(), Math.cos(), Math.sqrt()
// - System.arraycopy()
// - String.equals(), String.indexOf()
// - Object.hashCode()
// - Unsafe operations
// - CAS operations (compareAndSet)

// String.equals() intrinsic (x86-64):
// Uses SIMD instructions to compare 16/32 bytes at once
// Much faster than byte-by-byte comparison

// View intrinsics:
// -XX:+PrintIntrinsics (debug build only)
// -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining
```

### 6. Lock Optimization

```java
// Lock Elision (remove unnecessary locks)
public void lockElision() {
    StringBuffer sb = new StringBuffer();  // Synchronized internally
    sb.append("Hello");
    sb.append(" ");
    sb.append("World");
    // If sb doesn't escape, locks can be eliminated!
}

// Lock Coarsening (merge adjacent locks)
// Before:
synchronized (lock) { op1(); }
synchronized (lock) { op2(); }
synchronized (lock) { op3(); }

// After coarsening:
synchronized (lock) {
    op1();
    op2();
    op3();
}
// Reduces lock/unlock overhead

// Biased Locking (deprecated in Java 15, removed in 18)
// Lock biased to first acquiring thread
// Subsequent acquisitions by same thread are very cheap
```

---

## Deoptimization

### What is Deoptimization?

```
Deoptimization: Reverting from compiled code to interpreter

Why needed:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  JIT makes SPECULATIVE optimizations based on profiling:                   │
│                                                                             │
│  "This virtual call always goes to ConcreteHandler.handle()"               │
│  → Inline ConcreteHandler.handle() directly                                │
│                                                                             │
│  But what if a NEW implementation is loaded?                               │
│  → Speculation is WRONG                                                    │
│  → Must deoptimize and recompile                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Deoptimization triggers:
1. Class loading invalidates type assumptions
2. Uncommon trap hit (unexpected branch taken)
3. Exception thrown in optimized code
4. Debugging/profiling attached
```

### Uncommon Traps

```java
public void processPositive(int value) {
    if (value < 0) {
        // Profiling shows: never taken
        // JIT inserts "uncommon trap" instead of compiling this path
        handleNegative(value);
    }
    // Hot path optimized
    doWork(value);
}

// If value < 0 actually happens:
// 1. Uncommon trap triggered
// 2. Deoptimize to interpreter
// 3. Execute handleNegative() in interpreter
// 4. Recompile with updated profile (includes negative path)
```

### Deoptimization in Action

```
Deoptimization Flow:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────┐                                                       │
│  │ Compiled Code   │  Running optimized native code                        │
│  │ (C2 optimized)  │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           │ Speculation fails!                                              │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Deoptimization  │  1. Stop at safepoint                                 │
│  │                 │  2. Reconstruct interpreter frames                    │
│  │                 │  3. Transfer local variables                          │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │  Interpreter    │  Continue execution in interpreter                    │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           │ Method still hot?                                               │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │  Recompilation  │  Compile again with updated profile                   │
│  │  (C1 or C2)     │                                                       │
│  └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

// View deoptimizations:
// -XX:+TraceDeoptimization
// -XX:+PrintDeoptimizationDetails
```

---

## On-Stack Replacement (OSR)

### What is OSR?

```
OSR: Compile and switch to optimized code WHILE method is running

Scenario:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  public void longRunningMethod() {                                         │
│      for (int i = 0; i < 1_000_000; i++) {  // Hot loop!                   │
│          // ... work ...                                                    │
│      }                                                                      │
│  }                                                                          │
│                                                                             │
│  Problem: Method invocation count = 1 (not hot)                            │
│           But loop iterations = 1,000,000 (very hot!)                      │
│                                                                             │
│  Solution: OSR                                                              │
│  1. Detect hot loop via backedge counter                                   │
│  2. Compile method with OSR entry point at loop header                     │
│  3. Transfer execution from interpreter to compiled code                   │
│  4. Continue loop in optimized code                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### OSR Compilation

```
OSR Entry Point:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Interpreter                    Compiled Code                               │
│  ┌─────────────────┐           ┌─────────────────┐                         │
│  │ method entry    │           │ method entry    │ (normal entry)          │
│  │ ...             │           │ ...             │                         │
│  │ loop:           │           │ loop:           │                         │
│  │   i = 5000      │──────────►│   OSR entry ◄───│ (transfer here)         │
│  │   work()        │           │   work()        │                         │
│  │   i++           │           │   i++           │                         │
│  │   if i < N goto │           │   if i < N goto │                         │
│  │ ...             │           │ ...             │                         │
│  └─────────────────┘           └─────────────────┘                         │
│                                                                             │
│  OSR entry reconstructs state:                                              │
│  - Local variables (i = 5000)                                              │
│  - Stack state                                                              │
│  - Lock state                                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

// OSR compilation shown in PrintCompilation:
// 123  456  %  4  MyClass::longRunningMethod @ 15 (100 bytes)
//            ^                               ^
//            OSR                             bytecode index of loop
```

---

## JIT Tuning Parameters

### Common JIT Flags

```bash
# Compilation mode
-Xint                    # Interpreter only (no JIT)
-Xcomp                   # Compile everything (slow startup)
-Xmixed                  # Mixed mode (default)

# Tiered compilation
-XX:+TieredCompilation   # Enable tiered (default since Java 8)
-XX:-TieredCompilation   # Disable tiered (C2 only)
-XX:TieredStopAtLevel=1  # Stop at C1 (fast startup, lower peak)

# Compilation thresholds
-XX:CompileThreshold=10000        # Invocations before compile (no tiered)
-XX:Tier3InvocationThreshold=200  # Tier 3 threshold
-XX:Tier4InvocationThreshold=5000 # Tier 4 threshold

# Inlining
-XX:MaxInlineSize=35              # Always inline if smaller
-XX:FreqInlineSize=325            # Inline hot methods up to this size
-XX:MaxInlineLevel=9              # Max inline depth
-XX:InlineSmallCode=2000          # Inline if compiled code smaller

# Code cache
-XX:InitialCodeCacheSize=64m      # Initial code cache
-XX:ReservedCodeCacheSize=256m    # Maximum code cache
-XX:CodeCacheExpansionSize=64k    # Expansion increment

# Diagnostics
-XX:+PrintCompilation             # Print compilation events
-XX:+PrintInlining                # Print inlining decisions
-XX:+PrintAssembly                # Print generated assembly (needs hsdis)
-XX:+LogCompilation               # XML compilation log
```

### Code Cache

```
Code Cache Structure (Java 9+):
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CODE CACHE                                   │   │
│  ├─────────────────────┬─────────────────────┬─────────────────────────┤   │
│  │    Non-method       │   Profiled Code     │   Non-profiled Code     │   │
│  │    (JVM internal)   │   (C1 compiled)     │   (C2 compiled)         │   │
│  │                     │                     │                         │   │
│  │  - VM stubs         │  - Tier 2/3 code    │  - Tier 1/4 code        │   │
│  │  - Adapters         │  - With profiling   │  - Fully optimized      │   │
│  │  - Buffers          │    counters         │  - No profiling         │   │
│  └─────────────────────┴─────────────────────┴─────────────────────────┘   │
│                                                                             │
│  Segmented code cache (Java 9+):                                           │
│  - Better organization                                                      │
│  - Separate sweeping policies                                               │
│  - Reduced fragmentation                                                    │
│                                                                             │
│  -XX:NonMethodCodeHeapSize=8m                                              │
│  -XX:ProfiledCodeHeapSize=120m                                             │
│  -XX:NonProfiledCodeHeapSize=120m                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

// Monitor code cache:
// jcmd <pid> Compiler.codecache
```

---

## Graal Compiler

### What is Graal?

```
Graal: Next-generation JIT compiler written in Java

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Traditional HotSpot:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  JVM (C++)                                                           │   │
│  │  ├── Interpreter (C++)                                               │   │
│  │  ├── C1 Compiler (C++)                                               │   │
│  │  └── C2 Compiler (C++)                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  With Graal:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  JVM (C++)                                                           │   │
│  │  ├── Interpreter (C++)                                               │   │
│  │  ├── C1 Compiler (C++)                                               │   │
│  │  └── Graal Compiler (Java!) ◄── JVMCI interface                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Benefits:                                                                  │
│  - Written in Java (easier to maintain, extend)                            │
│  - Better optimizations for some workloads                                 │
│  - Foundation for GraalVM (polyglot, native-image)                         │
│  - Aggressive speculative optimizations                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using Graal

```bash
# Enable Graal as JIT compiler (Java 11+)
java -XX:+UnlockExperimentalVMOptions -XX:+UseJVMCICompiler MyApp

# GraalVM (includes Graal by default)
# Download from: https://www.graalvm.org/

# Graal-specific optimizations:
# - Partial escape analysis
# - Advanced inlining heuristics
# - Better loop optimizations
# - Improved speculative optimizations

# Native Image (AOT compilation)
native-image -jar myapp.jar
# Produces standalone executable with instant startup
```

### Graal vs C2 Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GRAAL vs C2                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Aspect              │ C2                    │ Graal                       │
│  ────────────────────┼───────────────────────┼─────────────────────────────│
│  Language            │ C++                   │ Java                        │
│  Maturity            │ 20+ years             │ ~10 years                   │
│  Compilation speed   │ Faster                │ Slower (but improving)      │
│  Peak performance    │ Excellent             │ Often better                │
│  Startup impact      │ Lower                 │ Higher (compiler in Java)   │
│  Extensibility       │ Hard                  │ Easy (Java)                 │
│  Partial escape      │ No                    │ Yes                         │
│  Polyglot support    │ No                    │ Yes (GraalVM)               │
│  Native image        │ No                    │ Yes                         │
│                                                                             │
│  Best for:                                                                  │
│  - C2: General purpose, proven stability                                   │
│  - Graal: Microservices, polyglot, native compilation                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Q1: Explain the difference between C1 and C2 compilers

```
Answer:

C1 (Client Compiler):
- Fast compilation, moderate optimization
- Compiles quickly to reduce startup time
- Collects profiling data for C2
- Optimizations: inlining, constant folding, null check elimination
- Code quality: ~2-3x faster than interpreter

C2 (Server Compiler):
- Slow compilation, aggressive optimization
- Uses profiling data from C1 for speculative optimizations
- Optimizations: escape analysis, loop unrolling, vectorization, lock elision
- Code quality: ~10-30x faster than interpreter

With tiered compilation (default):
- Methods start in interpreter
- Hot methods compiled by C1 (with profiling)
- Very hot methods recompiled by C2 (using C1's profile data)
- Best of both: fast startup + peak performance
```

### Q2: What is escape analysis and how does JIT use it?

```java
// Escape analysis determines if an object "escapes" its creating method

public int calculate() {
    Point p = new Point(3, 4);  // Does p escape?
    return p.x + p.y;           // No! p is local only
}

// JIT optimizations enabled by escape analysis:

// 1. Scalar Replacement
// Instead of allocating Point object:
public int calculate_optimized() {
    int p_x = 3;  // Fields become local variables
    int p_y = 4;
    return p_x + p_y;
}

// 2. Stack Allocation (theoretical, JVM usually does scalar replacement)
// Allocate on stack instead of heap - no GC needed

// 3. Lock Elision
synchronized (new Object()) {  // Lock on non-escaping object
    // ... work ...
}
// Lock can be completely removed!

// Escape states:
// - NoEscape: Doesn't leave method → optimize
// - ArgEscape: Passed to method but doesn't escape globally → partial optimize
// - GlobalEscape: Stored in field, returned, etc. → normal allocation
```

### Q3: What causes deoptimization?

```
Deoptimization: Reverting from compiled code to interpreter

Common causes:

1. Class Loading
   - New subclass loaded invalidates type assumptions
   - Example: JIT inlined ConcreteHandler.handle()
             New SubHandler loaded → must deoptimize

2. Uncommon Trap
   - Rarely-taken branch actually taken
   - Example: if (x < 0) { /* never happens */ }
             Then x = -1 → trap triggered

3. Type Check Failure
   - Speculative type assumption wrong
   - Example: JIT assumed obj always String
             Then obj = Integer → deoptimize

4. Null Check Failure
   - Assumed non-null was actually null

5. Array Bounds Check
   - Assumed in-bounds access was out of bounds

6. Debugging
   - Debugger attached, breakpoint set

After deoptimization:
- Method continues in interpreter
- If still hot, recompiled with updated profile
- New compilation avoids the failed speculation
```

### Q4: How does JIT handle polymorphic calls?

```java
interface Shape { int area(); }
class Circle implements Shape { int area() { return πr²; } }
class Square implements Shape { int area() { return s²; } }

void process(Shape shape) {
    int a = shape.area();  // Virtual call - which implementation?
}

// JIT optimization based on call site profile:

// 1. Monomorphic (1 type seen)
// Profile: 100% Circle
// Optimization: Inline Circle.area() directly
//   if (shape.getClass() != Circle.class) deoptimize;
//   return shape.r * shape.r * PI;

// 2. Bimorphic (2 types seen)
// Profile: 70% Circle, 30% Square
// Optimization: Type check + inline both
//   if (shape instanceof Circle) return πr²;
//   else if (shape instanceof Square) return s²;
//   else deoptimize;

// 3. Megamorphic (many types)
// Profile: Circle, Square, Triangle, Pentagon, ...
// Optimization: Virtual call (vtable lookup)
//   No inlining possible, use standard dispatch

// JVM tracks call site types in MethodData
// -XX:TypeProfileWidth=2 (default: track 2 types per call site)
```

### Q5: What is the code cache and why might it fill up?

```
Code Cache: Memory area storing JIT-compiled native code

Structure (Java 9+):
┌─────────────────────────────────────────────────────────────────────────────┐
│  Non-method heap  │  Profiled code heap  │  Non-profiled code heap         │
│  (JVM internal)   │  (C1 + profiling)    │  (C2 optimized)                 │
└─────────────────────────────────────────────────────────────────────────────┘

Why it fills up:
1. Too many methods compiled
2. Large methods generating lots of code
3. Deoptimization/recompilation cycles
4. Code cache too small for application

Symptoms of full code cache:
- "CodeCache is full" warning
- Compilation disabled
- Performance degradation

Solutions:
-XX:ReservedCodeCacheSize=512m    # Increase size
-XX:+UseCodeCacheFlushing         # Enable flushing (default)

Monitor:
jcmd <pid> Compiler.codecache
jcmd <pid> VM.native_memory summary
```

### Q6: Explain On-Stack Replacement (OSR)

```
OSR: Switching from interpreter to compiled code mid-execution

Scenario:
public void compute() {
    for (int i = 0; i < 10_000_000; i++) {
        // Hot loop, but method only called once
        heavyComputation(i);
    }
}

Problem:
- Method invocation count = 1 (not "hot")
- But loop runs 10 million times!
- Without OSR: Entire loop runs in interpreter

With OSR:
1. Backedge counter tracks loop iterations
2. When threshold reached (e.g., 10,000 iterations)
3. Compile method with OSR entry at loop header
4. Transfer execution: interpreter → compiled code
5. Remaining iterations run in optimized code

OSR entry point:
- Special entry into compiled code at loop header
- Must reconstruct: local variables, stack, locks
- Compiled code continues from current loop iteration

// PrintCompilation shows OSR:
// 123  456  %  4  MyClass::compute @ 15 (100 bytes)
//            ^                     ^
//            OSR marker            bytecode index
```

### Q7: How do intrinsics work?

```java
// Intrinsics: Hand-optimized native code for critical methods

// Example: System.arraycopy()
// Bytecode would be: loop copying element by element
// Intrinsic: Uses CPU's REP MOVSB or SIMD instructions

// How JIT handles intrinsics:
// 1. Recognize method signature
// 2. Replace bytecode with pre-written assembly
// 3. No interpretation or normal compilation

// Common intrinsified methods:
// - Math.sin(), cos(), sqrt(), abs()
// - String.equals(), indexOf(), hashCode()
// - Arrays.equals(), Arrays.fill()
// - Object.getClass(), hashCode()
// - Unsafe.compareAndSwap*()
// - Thread.currentThread()

// String.equals() intrinsic (x86-64):
// 1. Compare lengths (quick exit if different)
// 2. Compare 8 bytes at a time using 64-bit registers
// 3. Use SIMD (SSE/AVX) for longer strings
// 4. Much faster than byte-by-byte loop!

// View intrinsics:
// -XX:+PrintInlining shows "(intrinsic)" annotation
```

### Q8: What JIT flags would you use to diagnose performance issues?

```bash
# Basic compilation logging
-XX:+PrintCompilation
# Shows: timestamp, compilation_id, method, size

# Detailed inlining decisions
-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining
# Shows: what was inlined, why something wasn't inlined

# Compilation queue
-XX:+PrintCompilationQueue
# Shows: methods waiting to be compiled

# Deoptimization events
-XX:+TraceDeoptimization
# Shows: why methods were deoptimized

# Full compilation log (XML)
-XX:+LogCompilation -XX:LogFile=compilation.log
# Analyze with JITWatch: https://github.com/AdoptOpenJDK/jitwatch

# Generated assembly (requires hsdis plugin)
-XX:+UnlockDiagnosticVMOptions -XX:+PrintAssembly
# Shows: actual machine code generated

# Code cache status
-XX:+PrintCodeCache
# Shows: code cache usage at shutdown

# Compilation statistics
-XX:+CITime
# Shows: time spent in compilation

# Example diagnostic session:
java -XX:+PrintCompilation \
     -XX:+UnlockDiagnosticVMOptions \
     -XX:+PrintInlining \
     -XX:+TraceDeoptimization \
     -jar myapp.jar 2>&1 | tee jit.log
```


