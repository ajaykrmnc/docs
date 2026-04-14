# Just-In-Time Compilation for System Programmers

## Introduction

Just-In-Time (JIT) compilation translates code to native machine code at runtime, combining the benefits of interpretation (portability, dynamic optimization) with the performance of ahead-of-time compilation. This document covers JIT fundamentals, techniques, and implementation.

**Key Learning Objectives:**
- Understand JIT vs AOT vs interpretation
- Learn JIT compilation stages and tiers
- Understand optimization techniques (inlining, type specialization)
- Learn code generation and patching
- Explore practical JIT implementations (V8, Java HotSpot, LLVM JIT)

## 1. Compilation Models

### 1.1 Comparison

| Model | Compile Time | Runtime Performance | Startup Time | Portability |
|-------|--------------|---------------------|--------------|-------------|
| **AOT** | Long | Excellent | Fast | Architecture-specific |
| **JIT** | None (pre-runtime) | Excellent | Medium | Portable bytecode |
| **Interpreter** | None | Poor | Instant | Portable bytecode |

### 1.2 Why JIT?

**Advantages over AOT:**
- Runtime information (types, hot paths)
- Platform-specific optimizations
- Dynamic code generation (eval, reflection)

**Advantages over interpretation:**
- Native code execution (10-100× faster)
- Aggressive optimization with profiling

**Disadvantages:**
- Startup latency (compilation overhead)
- Memory overhead (code cache)
- Warmup time (before optimized)

## 2. JIT Architecture

### 2.1 Basic Flow

```
Source Code
    ↓
Bytecode (portable)
    ↓
┌─────────────────────────────────┐
│       JIT Runtime               │
│                                 │
│  1. Interpreter (initially)     │
│        ↓                        │
│  2. Profile execution           │
│        ↓                        │
│  3. Detect hot code             │
│        ↓                        │
│  4. Compile to native           │
│        ↓                        │
│  5. Execute native code         │
└─────────────────────────────────┘
```

### 2.2 Tiered Compilation

**Example: Java HotSpot**

```
Level 0: Interpreter
  - Instant startup
  - Collect profiling data
  - Very slow (100× slower than native)
  
Level 1: C1 Compiler (Client Compiler)
  - Fast compilation (~1ms)
  - Basic optimizations
  - Medium performance (5× slower than native)
  - Continue profiling
  
Level 2-3: C1 with more profiling

Level 4: C2 Compiler (Server Compiler)
  - Slow compilation (~100ms)
  - Aggressive optimizations
  - Excellent performance (near AOT)
```

**Decision logic:**
```
Method invocation count > threshold?
  → Compile at C1 level

Method running time > threshold?
  → Recompile at C2 level
```

### 2.3 V8 JavaScript Engine

**Pipeline:**

```
JavaScript Source
    ↓
Parser → AST
    ↓
Ignition Interpreter (bytecode)
    ↓
TurboFan JIT Compiler (optimized code)
    ↓
Deoptimization (if assumptions violated)
    ↓
Back to Interpreter
```

**Example:**
```javascript
function add(a, b) {
    return a + b;
}

// Initially: Interpreted
add(1, 2);        // Slow, profile types
add(3, 4);        // Still interpreted
...
add(99, 100);     // Hot! Compile with assumption: a, b are integers

// Optimized native code:
// mov eax, a
// add eax, b
// ret

add(5, "hello");  // Deoptimization! (string + number)
                  // Fall back to interpreter
```

## 3. Optimization Techniques

### 3.1 Type Specialization

**JavaScript example:**
```javascript
function multiply(x, y) {
    return x * y;
}
```

**Without profiling (generic):**
```asm
# Generic multiply (handles int, float, string, object)
multiply:
    call check_type_x      # ~50 cycles
    call check_type_y
    call dispatch_multiply # ~100 cycles
    ret
# Total: ~200 cycles
```

**With profiling (specialized for integers):**
```asm
# Specialized for int × int
multiply_int:
    # Guard: check types still integers
    test_int(x) or deopt
    test_int(y) or deopt
    # Fast path
    imul eax, x, y        # ~3 cycles
    ret
# Total: ~10 cycles (20× faster!)
```

### 3.2 Inlining

**Before inlining:**
```javascript
function square(x) { return x * x; }
function sum_squares(a, b) {
    return square(a) + square(b);  // Two function calls
}
```

**After JIT inlining:**
```javascript
function sum_squares(a, b) {
    return (a * a) + (b * b);  // Inlined, no function calls
}
```

**Benefits:**
- Eliminates call overhead (~10 cycles)
- Enables further optimizations (CSE, constant folding)

### 3.3 Escape Analysis

**Determines if object can be stack-allocated.**

```java
// Before optimization
public Point addPoints(int x1, int y1, int x2, int y2) {
    Point p1 = new Point(x1, y1);  // Heap allocation
    Point p2 = new Point(x2, y2);  // Heap allocation
    return p1.add(p2);
}

// After escape analysis
public Point addPoints(int x1, int y1, int x2, int y2) {
    // p1, p2 don't escape → scalar replacement
    int p1_x = x1, p1_y = y1;  // Stack variables (no allocation!)
    int p2_x = x2, p2_y = y2;
    return new Point(p1_x + p2_x, p1_y + p2_y);  // Only one allocation
}
```

**Benefit**: Avoid heap allocation/GC (10-100× faster).

### 3.4 Loop Optimizations

**Loop unrolling:**
```javascript
// Original
for (let i = 0; i < 1000; i++) {
    sum += array[i];
}

// JIT-optimized (unrolled 4×)
for (let i = 0; i < 1000; i += 4) {
    sum += array[i];
    sum += array[i+1];
    sum += array[i+2];
    sum += array[i+3];
}
```

**Loop invariant code motion:**
```javascript
// Original
for (let i = 0; i < n; i++) {
    result[i] = array[i] * Math.sqrt(constant);
}

// JIT-optimized
let temp = Math.sqrt(constant);  // Moved outside loop
for (let i = 0; i < n; i++) {
    result[i] = array[i] * temp;
}
```

## 4. Code Generation

### 4.1 IR (Intermediate Representation)

**Example: LLVM IR for add function**
```llvm
define i32 @add(i32 %a, i32 %b) {
entry:
  %sum = add nsw i32 %a, %b
  ret i32 %sum
}
```

**Optimized:**
```llvm
define i32 @add(i32 %a, i32 %b) {
  %sum = add nsw i32 %a, %b  # nsw = no signed wrap (enable opts)
  ret i32 %sum
}
```

**Native x86-64:**
```asm
add:
  lea eax, [rdi+rsi]  # eax = rdi + rsi (using LEA for speed)
  ret
```

### 4.2 Code Cache Management

**Structure:**
```
Code Cache (RWX memory region)
┌──────────────────────────────────┐
│ Method 1 (native code)           │ 100 bytes
├──────────────────────────────────┤
│ Method 2 (native code)           │ 50 bytes
├──────────────────────────────────┤
│ Free space                       │
└──────────────────────────────────┘
```

**Challenges:**
- Limited size (typical: 100-500 MB)
- Fragmentation
- Eviction policy (LRU, LFU)

**Tiered eviction:**
- Keep hot C2-compiled code
- Evict cold C1-compiled code
- Re-compile if becomes hot again

### 4.3 On-Stack Replacement (OSR)

**Problem**: Long-running interpreted loop.

```java
// Starts in interpreter
for (int i = 0; i < 1_000_000; i++) {
    // After 100 iterations: detected as hot
    // Compile to native
    // But loop already running!
}
```

**Solution: OSR**
```
1. Compile loop to native
2. Save interpreter state (i, locals, stack)
3. Transfer state to compiled code
4. Continue in compiled code
5. Huge speedup mid-execution!
```

## 5. Deoptimization

### 5.1 Speculative Optimization

**JIT makes assumptions to optimize:**

```javascript
function process(obj) {
    return obj.x + obj.y;  // Assume obj has shape {x: int, y: int}
}

// After profiling: obj always has same shape
// JIT generates:
process_optimized:
    # Guard: check obj shape
    cmp [obj], expected_shape
    jne deoptimize
    # Fast path: direct field access (no lookup)
    mov eax, [obj+offset_x]  # Hardcoded offset
    add eax, [obj+offset_y]
    ret
```

### 5.2 Deoptimization Triggers

**Type changes:**
```javascript
process({x: 1, y: 2});      // Optimized for integers
process({x: 1.5, y: 2.5});  // DEOPT! (now floats)
```

**Shape changes:**
```javascript
process({x: 1, y: 2});      // Optimized for shape {x, y}
process({x: 1, y: 2, z: 3});// DEOPT! (different shape)
```

**Inlining invalidation:**
```javascript
// Inlined based on: Class.method is always funcA
Class.method = funcB;  // DEOPT! Invalidate inlined code
```

### 5.3 Deoptimization Process

```
1. Detect guard failure
2. Stop native code execution
3. Reconstruct interpreter state from optimized state
4. Transfer to interpreter
5. Invalidate optimized code
6. Continue in interpreter (or re-optimize later)
```

## 6. Practical JIT Implementations

### 6.1 Java HotSpot Example

```java
public class Benchmark {
    static int factorial(int n) {
        int result = 1;
        for (int i = 2; i <= n; i++) {
            result *= i;
        }
        return result;
    }
    
    public static void main(String[] args) {
        // Warm-up: trigger JIT compilation
        for (int i = 0; i < 10000; i++) {
            factorial(10);
        }
        
        // Now runs at native speed
        long start = System.nanoTime();
        for (int i = 0; i < 1000000; i++) {
            factorial(10);
        }
        long end = System.nanoTime();
        System.out.println("Time: " + (end - start) / 1000000 + "ms");
    }
}

// JVM flags to observe JIT:
// java -XX:+PrintCompilation -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining Benchmark
```

### 6.2 LLVM JIT Example

```cpp
#include <llvm/ExecutionEngine/Orc/LLJIT.h>

using namespace llvm;
using namespace llvm::orc;

int main() {
    // Create JIT
    auto J = LLJITBuilder().create();
    
    // Add module (IR code)
    auto M = parseIRFile("mycode.ll", Err, Context);
    J->addIRModule(ThreadSafeModule(std::move(M), TSCtx));
    
    // Lookup and execute function
    auto Sym = J->lookup("add");
    int (*add)(int, int) = (int (*)(int, int))Sym->getAddress();
    
    printf("%d\n", add(5, 3));  // Runs JIT-compiled code
}
```

## 7. Performance Characteristics

### 7.1 Warmup vs Steady State

```
Performance over time:
 ^
 │                 ┌─────────── Steady state (optimized)
 │                ╱
 │              ╱
 │            ╱
 │          ╱
 │        ╱
 └────────────────────────> Time
   Warmup (compiling)
```

**Warmup period**: 1-10 seconds typical
**Steady state**: Near AOT performance

### 7.2 Benchmarking Considerations

```java
// Bad: Measures warmup + steady state
long start = System.nanoTime();
runBenchmark();
long end = System.nanoTime();

// Good: Warmup first
for (int i = 0; i < 10000; i++) runBenchmark();  // Warmup
long start = System.nanoTime();
runBenchmark();  // Measure
long end = System.nanoTime();
```

## 8. Summary

**Key Takeaways:**
- JIT combines portability with native performance
- Tiered compilation balances startup and steady-state
- Profile-guided optimization enables aggressive specialization
- Deoptimization handles speculative optimization failures
- Warmup time is critical consideration

**Performance:**
- Steady state: Within 5-20% of AOT
- Warmup: 1000-10000× slower initially
- Memory: 2-5× overhead (code cache, profiling)

---

*Last updated: 2026-04-11*
