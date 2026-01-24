# JVM Internals and Java Memory Model - Deep Dive

## Table of Contents
1. [JVM Architecture Overview](#jvm-architecture-overview)
2. [Class Loading Mechanism](#class-loading-mechanism)
3. [Runtime Data Areas](#runtime-data-areas)
4. [Execution Engine](#execution-engine)
5. [Garbage Collection Internals](#garbage-collection-internals)
6. [Java Memory Model (JMM)](#java-memory-model)
7. [JIT Compilation](#jit-compilation)
8. [Interview Questions](#interview-questions)

---

## JVM Architecture Overview

The Java Virtual Machine is an abstract computing machine that enables a computer to run Java programs. Understanding its internals is crucial for writing efficient code and debugging complex issues.

### JVM Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              JVM Architecture                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                                                    │
│  │  Class Loader   │ ◄── Loading, Linking, Initialization              │
│  │    Subsystem    │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Runtime Data Areas                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ │   │
│  │  │  Method  │ │   Heap   │ │  Java    │ │   PC   │ │ Native  │ │   │
│  │  │   Area   │ │          │ │  Stacks  │ │Register│ │ Method  │ │   │
│  │  │ (Shared) │ │ (Shared) │ │(Per-Thrd)│ │(P-Thrd)│ │ Stacks  │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ └─────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Execution Engine                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │ Interpreter │  │ JIT Compiler│  │ Garbage Collector       │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Native Method   │ ◄── JNI (Java Native Interface)                   │
│  │   Interface     │                                                    │
│  └─────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Class Loading Mechanism

### The Class Loading Process

Class loading follows a three-phase process: **Loading → Linking → Initialization**

#### Phase 1: Loading

The class loader reads the `.class` file and creates a binary representation in the Method Area.

```java
// Example: Understanding when classes are loaded
public class ClassLoadingDemo {
    public static void main(String[] args) {
        // Class A is loaded when first referenced
        System.out.println("Before A reference");
        A a = new A();  // Class A loaded here
        System.out.println("After A instantiation");
    }
}

class A {
    static {
        System.out.println("Class A static initializer");
    }
    
    {
        System.out.println("Class A instance initializer");
    }
}
// Output:
// Before A reference
// Class A static initializer
// Class A instance initializer
// After A instantiation
```

### Class Loader Hierarchy (Delegation Model)

```
┌─────────────────────────────────────────┐
│         Bootstrap ClassLoader           │  ← Loads rt.jar, core Java classes
│         (Native Code - C/C++)           │     java.lang.*, java.util.*, etc.
└─────────────────┬───────────────────────┘
                  │ delegates to parent
                  ▼
┌─────────────────────────────────────────┐
│       Extension/Platform ClassLoader    │  ← Loads jre/lib/ext directory
│         (sun.misc.Launcher$ExtClassLoader) │   Security extensions, etc.
└─────────────────┬───────────────────────┘
                  │ delegates to parent
                  ▼
┌─────────────────────────────────────────┐
│       Application/System ClassLoader    │  ← Loads classpath classes
│      (sun.misc.Launcher$AppClassLoader) │     Your application classes
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Custom ClassLoaders             │  ← User-defined loaders
│      (Extends ClassLoader class)        │     Tomcat, OSGi, etc.
└─────────────────────────────────────────┘
```

#### Parent Delegation Model - How It Works

```java
// Simplified pseudocode of class loading
protected Class<?> loadClass(String name, boolean resolve) {
    // 1. Check if class already loaded
    Class<?> c = findLoadedClass(name);
    
    if (c == null) {
        try {
            // 2. Delegate to parent first (Parent Delegation)
            if (parent != null) {
                c = parent.loadClass(name, false);
            } else {
                c = findBootstrapClassOrNull(name);
            }
        } catch (ClassNotFoundException e) {
            // Parent couldn't find it
        }
        
        if (c == null) {
            // 3. If parent fails, try to load ourselves
            c = findClass(name);
        }
    }
    
    if (resolve) {
        resolveClass(c);
    }
    return c;
}
```

#### Why Parent Delegation?

1. **Security**: Prevents malicious code from replacing core Java classes
2. **Uniqueness**: Ensures class is loaded only once
3. **Visibility**: Child can see parent's classes, not vice versa

#### Phase 2: Linking (Verification → Preparation → Resolution)

```java
// Linking has three sub-phases:

// 1. VERIFICATION
// - Ensures bytecode is valid and secure
// - Checks: magic number (0xCAFEBABE), version, constant pool
// - Verifies: type safety, stack operations, branch targets
// Errors: VerifyError, ClassFormatError

// 2. PREPARATION
// - Allocates memory for static fields
// - Initializes to DEFAULT values (not assigned values!)
class Example {
    static int count = 10;  // Preparation: count = 0
                            // Initialization: count = 10
    static Object obj = new Object();  // Preparation: obj = null
}

// 3. RESOLUTION
// - Converts symbolic references to direct references
// - Symbolic: "java.lang.String" (name)
// - Direct: actual memory address
// Can be eager or lazy (JVM implementation dependent)
```

#### Phase 3: Initialization

```java
// Static initializers run in order
class InitOrder {
    static int a = initA();  // 1st
    static { System.out.println("Static block 1"); }  // 2nd
    static int b = initB();  // 3rd
    static { System.out.println("Static block 2"); }  // 4th

    static int initA() { System.out.println("initA"); return 1; }
    static int initB() { System.out.println("initB"); return 2; }
}
// Output: initA, Static block 1, initB, Static block 2

// When does initialization occur?
// 1. new keyword
// 2. Accessing static field (not final compile-time constant)
// 3. Calling static method
// 4. Reflection (Class.forName)
// 5. Initializing a subclass
// 6. Main class of JVM startup
```

---

## Runtime Data Areas

### Method Area (Metaspace since Java 8)

```
Method Area Contents:
┌────────────────────────────────────────────────────────────────────────┐
│                          Method Area / Metaspace                        │
├────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Runtime Constant Pool (per class)                                 │  │
│  │ - Numeric literals, string literals                               │  │
│  │ - Class/method/field references                                   │  │
│  │ - Method handles, invokedynamic bootstrap methods                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Class Metadata                                                    │  │
│  │ - Fully qualified name, modifiers, superclass                     │  │
│  │ - Interfaces, fields, methods, attributes                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Method Bytecode                                                   │  │
│  │ - Instructions for each method                                    │  │
│  │ - Exception tables                                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Static Variables (Java 8+: moved to Heap)                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Heap Structure

```
Java Heap Memory Layout:
┌─────────────────────────────────────────────────────────────────────────┐
│                               HEAP                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Young Generation                              │  │
│  │  ┌─────────────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │        Eden         │  │  Survivor   │  │  Survivor   │        │  │
│  │  │  (new allocations)  │  │     S0      │  │     S1      │        │  │
│  │  │                     │  │  (From/To)  │  │  (To/From)  │        │  │
│  │  └─────────────────────┘  └─────────────┘  └─────────────┘        │  │
│  │          80%                  10%              10%                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       Old Generation                               │  │
│  │                                                                    │  │
│  │   Long-lived objects that survived multiple minor GCs             │  │
│  │   Larger, collected less frequently (Major/Full GC)               │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Object Lifecycle:
1. New object allocated in Eden
2. Eden full → Minor GC → Survivors copied to S0/S1
3. Object survives N GCs → Promoted to Old Generation
4. Old Generation full → Major/Full GC
```

### Java Stack (Thread Stack)

```
Stack Frame Structure:
┌─────────────────────────────────────────────────────────────────────┐
│                         Stack Frame                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Local Variable Array                                          │   │
│  │ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐           │   │
│  │ │  0  │  1  │  2  │  3  │  4  │  5  │  6  │ ... │           │   │
│  │ │this │arg1 │arg2 │local│local│     │     │     │           │   │
│  │ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘           │   │
│  │ - Slot 0: 'this' reference (for instance methods)            │   │
│  │ - Slots 1-N: method parameters                                │   │
│  │ - Remaining: local variables                                  │   │
│  │ - long/double take 2 slots                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Operand Stack (for bytecode operations)                       │   │
│  │ ┌─────┬─────┬─────┬─────┐                                    │   │
│  │ │     │     │     │ top │  ← push/pop operations             │   │
│  │ └─────┴─────┴─────┴─────┘                                    │   │
│  │ Example: a + b                                                │   │
│  │   iload_1    → push a                                        │   │
│  │   iload_2    → push b                                        │   │
│  │   iadd       → pop both, push result                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Frame Data                                                    │   │
│  │ - Reference to runtime constant pool                          │   │
│  │ - Exception table reference                                   │   │
│  │ - Return address                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Execution Engine

### Interpreter vs JIT Compiler

```
Execution Phases:
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Bytecode ──────► Interpreter ──────► Native Code (line by line)        │
│      │                                                                   │
│      │           ┌─────────────────────────────────────────────────┐    │
│      └──────────►│              JIT Compiler                        │    │
│                  │                                                  │    │
│   Hot Method ───►│  ┌────────────┐    ┌─────────────────────────┐  │    │
│   Detected       │  │   C1       │───►│          C2             │  │    │
│                  │  │ (Client)   │    │       (Server)          │  │    │
│                  │  │            │    │                         │  │    │
│                  │  │ Quick      │    │ Aggressive optimization │  │    │
│                  │  │ compilation│    │ - Inlining              │  │    │
│                  │  │ Basic opt  │    │ - Escape analysis       │  │    │
│                  │  │            │    │ - Loop unrolling        │  │    │
│                  │  │            │    │ - Dead code elimination │  │    │
│                  │  └────────────┘    └─────────────────────────┘  │    │
│                  └─────────────────────────────────────────────────┘    │
│                                       │                                  │
│                                       ▼                                  │
│                              Optimized Native Code (cached)             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tiered Compilation (Default in modern JVMs)

```
Level 0: Interpreted
    │
    ▼ (invocation count)
Level 1: C1 with full instrumentation
    │
    ▼ (more invocations)
Level 2: C1 with limited profiling
    │
    ▼ (even more)
Level 3: C1 with full profiling
    │
    ▼ (hot method threshold)
Level 4: C2 fully optimized

// JVM flags:
// -XX:+TieredCompilation (default: on)
// -XX:CompileThreshold=10000 (invocations before compilation)
```

---

## Garbage Collection Internals

### Mark and Sweep Algorithm

```
Phase 1: Mark (Stop-the-World)
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   GC Roots:                       Heap Objects:                          │
│   ┌──────────┐                    ┌───┐  ┌───┐  ┌───┐                   │
│   │ Stack    │───────────────────►│ A │─►│ B │  │ C │ (unreachable)     │
│   │ Variables│                    └───┘  └─┬─┘  └───┘                   │
│   └──────────┘                             │                             │
│   ┌──────────┐                    ┌───┐    │    ┌───┐                   │
│   │ Static   │───────────────────►│ D │◄───┘    │ E │ (unreachable)     │
│   │ Variables│                    └───┘         └───┘                   │
│   └──────────┘                                                          │
│   ┌──────────┐                                                          │
│   │ JNI Refs │                    Marked: A, B, D (reachable from roots)│
│   └──────────┘                    Unmarked: C, E (garbage)              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Phase 2: Sweep
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   Before:  [A][C][B][E][D][   ][   ]                                    │
│                                                                          │
│   After:   [A][   ][B][   ][D][   ][   ]  ← C, E memory reclaimed       │
│                ▲       ▲                                                 │
│                └───────┴──── Free list (memory fragmentation)           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Phase 3: Compact (Optional)
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   After:   [A][B][D][   ][   ][   ][   ]  ← Defragmented                │
│                     ▲                                                    │
│                     └──── Free space pointer (bump allocation)          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### G1 GC Internals (Default GC since Java 9)

```
G1 Heap Layout (Region-based):
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐    │
│  │ E │ E │ S │ O │ O │ H │ H │   │ E │ O │ O │   │ S │ O │   │   │    │
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘    │
│                                                                          │
│  E = Eden region       (Young generation)                                │
│  S = Survivor region   (Young generation)                                │
│  O = Old region        (Old generation)                                  │
│  H = Humongous region  (Large objects > 50% region size)                │
│    = Free region                                                         │
│                                                                          │
│  Region size: 1MB - 32MB (based on heap size)                           │
│  Typical: 2048 regions                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

G1 Collection Types:
1. Young GC: Collects all Eden + Survivor regions
2. Mixed GC: Young + selected Old regions (garbage first!)
3. Full GC: Fallback, entire heap (avoid!)
```

---

## Java Memory Model (JMM)

### Happens-Before Relationships

```java
// JMM defines which memory operations are guaranteed to be visible

// 1. Program Order Rule
// Within a thread, each action happens-before subsequent actions
int a = 1;  // HB
int b = 2;  // This sees a = 1

// 2. Monitor Lock Rule
// Unlock happens-before subsequent lock on same monitor
synchronized (lock) {
    sharedVar = 42;
}  // Unlock HB...
// ...another thread:
synchronized (lock) {  // Lock
    int x = sharedVar;  // Sees 42
}

// 3. Volatile Variable Rule
// Write to volatile happens-before subsequent read
volatile boolean ready = false;
// Thread 1:
data = 42;
ready = true;  // volatile write HB...
// Thread 2:
if (ready) {   // volatile read
    // Guaranteed to see data = 42
}

// 4. Thread Start Rule
// Thread.start() happens-before any action in started thread
data = 42;
thread.start();  // HB
// In thread: sees data = 42

// 5. Thread Join Rule
// All actions in thread happen-before join() returns
// In thread: data = 42
thread.join();  // HB
// After join: sees data = 42
```

### Memory Barriers

```
CPU Memory Barriers (enforced by JMM):

┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  LoadLoad   - Ensures Load1 completes before Load2                      │
│               Load1; LoadLoad; Load2                                     │
│                                                                          │
│  StoreStore - Ensures Store1 visible before Store2                      │
│               Store1; StoreStore; Store2                                 │
│                                                                          │
│  LoadStore  - Ensures Load1 completes before Store2 visible             │
│               Load1; LoadStore; Store2                                   │
│                                                                          │
│  StoreLoad  - Ensures Store1 visible before Load2 (most expensive)      │
│               Store1; StoreLoad; Load2                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

volatile semantics:
- volatile read:  LoadLoad + LoadStore barrier after
- volatile write: StoreStore barrier before + StoreLoad barrier after
```

---

## Interview Questions

### Q1: What is the difference between stack and heap memory?

| Stack | Heap |
|-------|------|
| Per-thread, private | Shared across threads |
| LIFO order | No particular order |
| Stores primitives, references | Stores objects |
| Fast allocation (bump pointer) | Slower (GC managed) |
| Auto-deallocated on method exit | GC deallocates |
| Fixed size (-Xss) | Dynamic size (-Xmx) |
| StackOverflowError if exhausted | OutOfMemoryError |

### Q2: Explain class loading with code example

```java
// Class is loaded only when first actively used
public class LazyLoading {
    public static void main(String[] args) {
        System.out.println("Main started");

        // Reference to class doesn't cause loading
        Class<?> clazz = MyClass.class;  // Loaded

        // Accessing constant doesn't cause initialization
        int x = MyClass.CONSTANT;  // NOT initialized!

        // This causes full initialization
        MyClass.doSomething();  // Loaded + Initialized
    }
}

class MyClass {
    static final int CONSTANT = 42;  // Compile-time constant
    static int value = initValue();

    static {
        System.out.println("MyClass initialized");
    }

    static int initValue() {
        System.out.println("initValue called");
        return 100;
    }

    static void doSomething() { }
}
```

### Q3: How does G1 GC determine which regions to collect?

G1 maintains a priority queue of regions sorted by "garbage first" - regions with most garbage (lowest live data ratio) are collected first, maximizing freed memory with minimal work.

### Q4: What causes a Full GC and how to avoid it?

**Causes:**
1. Old Generation full
2. Metaspace exhaustion
3. Humongous allocation failure
4. Explicit System.gc() call
5. Promotion failure

**Avoidance:**
1. Size heap appropriately
2. Tune young generation size
3. Avoid creating large objects
4. Use -XX:+DisableExplicitGC
5. Monitor and tune GC parameters


