# Java Performance Tuning and Optimization - Deep Dive

## Table of Contents
1. [JVM Tuning Parameters](#jvm-tuning)
2. [Memory Optimization](#memory-optimization)
3. [Garbage Collection Tuning](#gc-tuning)
4. [String Optimization](#string-optimization)
5. [Collection Performance](#collection-performance)
6. [Concurrency Optimization](#concurrency-optimization)
7. [Profiling and Benchmarking](#profiling)
8. [Common Performance Anti-patterns](#anti-patterns)
9. [Interview Questions](#interview-questions)

---

## JVM Tuning Parameters

### Memory Configuration

```bash
# Heap Size Configuration
-Xms<size>      # Initial heap size (e.g., -Xms2g)
-Xmx<size>      # Maximum heap size (e.g., -Xmx8g)
-Xmn<size>      # Young generation size

# Metaspace (Java 8+)
-XX:MetaspaceSize=256m       # Initial metaspace size
-XX:MaxMetaspaceSize=512m    # Maximum metaspace size

# Stack Size
-Xss<size>      # Thread stack size (e.g., -Xss512k)

# Direct Memory
-XX:MaxDirectMemorySize=1g   # For NIO direct buffers
```

### Generation Sizing Strategy

```
Heap Layout:
┌─────────────────────────────────────────────────────────────────────────┐
│                              HEAP (-Xmx)                                │
├─────────────────────────────────┬───────────────────────────────────────┤
│      Young Generation (-Xmn)    │         Old Generation                │
│         (1/3 of heap)           │          (2/3 of heap)                │
├──────────┬──────────┬───────────┼───────────────────────────────────────┤
│   Eden   │ Survivor │ Survivor  │                                       │
│   (8/10) │  S0(1/10)│ S1(1/10)  │            Tenured Space              │
│          │          │           │                                       │
└──────────┴──────────┴───────────┴───────────────────────────────────────┘

-XX:NewRatio=2           # Old/Young ratio (2 means Old is 2x Young)
-XX:SurvivorRatio=8      # Eden/Survivor ratio
-XX:MaxTenuringThreshold=15  # Age before promotion to Old
```

### GC Algorithm Selection

```bash
# Serial GC (Single-threaded, small heaps)
-XX:+UseSerialGC

# Parallel GC (Throughput-focused)
-XX:+UseParallelGC
-XX:ParallelGCThreads=4

# G1 GC (Default in Java 9+, balanced)
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200    # Target pause time
-XX:G1HeapRegionSize=16m    # Region size (1-32MB)

# ZGC (Java 11+, ultra-low latency)
-XX:+UseZGC
-XX:ZCollectionInterval=5   # Minimum time between collections

# Shenandoah (Java 12+, low latency)
-XX:+UseShenandoahGC
```

---

## Memory Optimization

### Object Memory Layout

```java
// Object size calculation (64-bit JVM with compressed oops)

// Empty object: 16 bytes
class Empty {}
// Header: 12 bytes + Padding: 4 bytes = 16 bytes

// With one int: 16 bytes
class WithInt { int x; }
// Header: 12 bytes + int: 4 bytes = 16 bytes

// With one long: 24 bytes
class WithLong { long x; }
// Header: 12 bytes + Padding: 4 bytes + long: 8 bytes = 24 bytes

// Memory-efficient field ordering
class Inefficient {
    boolean a;  // 1 byte + 7 padding
    long b;     // 8 bytes
    boolean c;  // 1 byte + 7 padding
    long d;     // 8 bytes
}  // Total: 32 bytes (wasted: 14 bytes)

class Efficient {
    long b;     // 8 bytes
    long d;     // 8 bytes
    boolean a;  // 1 byte
    boolean c;  // 1 byte + 6 padding
}  // Total: 24 bytes (wasted: 6 bytes)
```

### Escape Analysis and Scalar Replacement

```java
// JIT can eliminate allocations through escape analysis

public class EscapeAnalysisDemo {
    
    // Object ESCAPES - must be heap allocated
    public Point getPoint() {
        return new Point(1, 2);  // Escapes method
    }
    
    // Object does NOT escape - can be stack allocated or eliminated
    public int sumCoordinates() {
        Point p = new Point(1, 2);  // Never escapes
        return p.x + p.y;  // JIT can replace with: return 1 + 2;
    }
    
    // Scalar replacement: fields inlined as local variables
    public int calculate() {
        Point p = new Point(10, 20);
        // JIT optimization: no Point object created!
        // Becomes: int p_x = 10; int p_y = 20;
        return p.x * p.y;
    }
}

// Enable/disable escape analysis
// -XX:+DoEscapeAnalysis     (default: enabled)
// -XX:-DoEscapeAnalysis     (disable)
```

### Object Pooling Patterns

```java
// Object pool for expensive objects
public class ObjectPool<T> {
    private final ConcurrentLinkedQueue<T> pool;
    private final Supplier<T> factory;
    private final Consumer<T> reset;
    private final int maxSize;
    private final AtomicInteger size = new AtomicInteger(0);
    
    public ObjectPool(Supplier<T> factory, Consumer<T> reset, int maxSize) {
        this.pool = new ConcurrentLinkedQueue<>();
        this.factory = factory;
        this.reset = reset;
        this.maxSize = maxSize;
    }
    
    public T borrow() {
        T obj = pool.poll();
        if (obj == null) {
            size.incrementAndGet();
            return factory.get();
        }
        return obj;
    }
    
    public void release(T obj) {
        if (size.get() <= maxSize) {
            reset.accept(obj);
            pool.offer(obj);
        }
    }
}

// Usage
ObjectPool<StringBuilder> sbPool = new ObjectPool<>(
    () -> new StringBuilder(256),
    sb -> sb.setLength(0),
    100
);

StringBuilder sb = sbPool.borrow();
try {
    sb.append("Hello").append(" World");
    return sb.toString();
} finally {
    sbPool.release(sb);
}
```

---

## Garbage Collection Tuning

### GC Log Analysis

```bash
# Enable GC logging (Java 9+)
-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=10M

# Java 8 style
-XX:+PrintGCDetails
-XX:+PrintGCTimeStamps
-XX:+PrintGCDateStamps
-Xloggc:gc.log
```

### GC Log Interpretation

```
# G1 GC Log Entry:
[2024-01-15T10:30:45.123+0000][1.234s][info][gc] GC(0) Pause Young (Normal) 
    (G1 Evacuation Pause) 24M->8M(256M) 12.345ms

# Breakdown:
# GC(0)           - GC event number
# Pause Young     - Young generation collection
# (Normal)        - Normal collection (not concurrent)
# 24M->8M(256M)   - Heap: 24MB before → 8MB after (256MB total)
# 12.345ms        - Pause time
```

### G1 GC Tuning

```java
// G1 is region-based:
// - Heap divided into equal-sized regions (1-32MB)
// - Regions can be Eden, Survivor, Old, or Humongous
// - Humongous: Objects > 50% of region size

// Key G1 tuning parameters:
// -XX:MaxGCPauseMillis=200       Target pause time (default: 200ms)
// -XX:G1HeapRegionSize=16m       Region size (default: auto)
// -XX:G1NewSizePercent=5         Min young gen (default: 5%)
// -XX:G1MaxNewSizePercent=60     Max young gen (default: 60%)
// -XX:InitiatingHeapOccupancyPercent=45  Start mixed GC (default: 45%)
// -XX:G1MixedGCLiveThresholdPercent=85   Skip regions with high liveness
```

---

## String Optimization

### String Concatenation Performance

```java
public class StringOptimization {

    // BAD: String concatenation in loop
    public String badConcat(List<String> items) {
        String result = "";
        for (String item : items) {
            result += item + ", ";  // Creates new String each time!
        }
        return result;
    }

    // GOOD: StringBuilder for mutable operations
    public String goodConcat(List<String> items) {
        StringBuilder sb = new StringBuilder(items.size() * 20);  // Pre-size!
        for (String item : items) {
            sb.append(item).append(", ");
        }
        return sb.toString();
    }

    // BETTER: String.join for simple cases
    public String betterConcat(List<String> items) {
        return String.join(", ", items);
    }

    // BEST: Stream collectors for complex cases
    public String streamConcat(List<String> items) {
        return items.stream()
            .collect(Collectors.joining(", ", "[", "]"));
    }
}
```

### String Deduplication

```java
// G1 can deduplicate strings automatically
// -XX:+UseStringDeduplication  (G1 only)

// Manual deduplication using intern()
public class StringDedup {
    private Map<String, WeakReference<String>> cache = new WeakHashMap<>();

    public String deduplicate(String s) {
        // For high-repetition strings
        return s.intern();  // Returns canonical reference

        // Custom deduplication (more control)
        // WeakReference<String> ref = cache.get(s);
        // if (ref != null && ref.get() != null) {
        //     return ref.get();
        // }
        // cache.put(s, new WeakReference<>(s));
        // return s;
    }
}
```

### Compact Strings (Java 9+)

```
Java 9+ String representation:
- LATIN1: 1 byte per character (for ASCII-only strings)
- UTF16: 2 bytes per character (when needed)

Benefits:
- ~50% memory reduction for ASCII strings
- Automatic, no code changes needed
- -XX:-CompactStrings to disable (rarely needed)
```

---

## Collection Performance

### Choosing the Right Collection

```
Operation Time Complexity:
┌──────────────────┬─────────┬───────────┬─────────────┬────────────────┐
│ Operation        │ArrayList│LinkedList │   HashSet   │    TreeSet     │
├──────────────────┼─────────┼───────────┼─────────────┼────────────────┤
│ get(index)       │   O(1)  │   O(n)    │     N/A     │      N/A       │
│ add(end)         │   O(1)* │   O(1)    │    O(1)*    │    O(log n)    │
│ add(index)       │   O(n)  │   O(n)    │     N/A     │      N/A       │
│ remove(index)    │   O(n)  │   O(n)    │     N/A     │      N/A       │
│ contains()       │   O(n)  │   O(n)    │    O(1)*    │    O(log n)    │
│ iterator.remove()│   O(n)  │   O(1)    │    O(1)*    │    O(log n)    │
└──────────────────┴─────────┴───────────┴─────────────┴────────────────┘
* amortized

Map Performance:
┌──────────────────┬──────────┬───────────┬─────────────────────┐
│ Operation        │ HashMap  │  TreeMap  │ LinkedHashMap       │
├──────────────────┼──────────┼───────────┼─────────────────────┤
│ get()            │   O(1)*  │ O(log n)  │     O(1)*           │
│ put()            │   O(1)*  │ O(log n)  │     O(1)*           │
│ remove()         │   O(1)*  │ O(log n)  │     O(1)*           │
│ Iteration order  │  Random  │  Sorted   │   Insertion order   │
└──────────────────┴──────────┴───────────┴─────────────────────┘
```

### Collection Sizing

```java
public class CollectionSizing {

    // Pre-size collections when size is known
    public void properSizing(int expectedSize) {
        // ArrayList: Avoid reallocations
        List<String> list = new ArrayList<>(expectedSize);

        // HashMap: Account for load factor (0.75)
        // Formula: expectedSize / 0.75 + 1
        Map<String, Object> map = new HashMap<>(expectedSize * 4 / 3 + 1);

        // Or simpler: just add 33%
        Map<String, Object> map2 = new HashMap<>((int) (expectedSize * 1.34));
    }

    // Avoid excessive reallocations
    public void avoidReallocations() {
        // BAD: Unknown size, multiple reallocations
        List<Integer> list = new ArrayList<>();
        for (int i = 0; i < 1_000_000; i++) {
            list.add(i);  // Multiple internal array copies
        }

        // GOOD: Pre-sized
        List<Integer> list2 = new ArrayList<>(1_000_000);
        for (int i = 0; i < 1_000_000; i++) {
            list2.add(i);  // No reallocations
        }
    }
}
```

### Primitive Collections

```java
// Wrapper objects have overhead:
// - Object header: 12 bytes
// - int value: 4 bytes
// - Padding: 0 bytes
// Total: 16 bytes per Integer (vs 4 bytes for int)

// For large primitive collections, consider:
// 1. Eclipse Collections
// 2. Trove
// 3. Koloboke
// 4. FastUtil

// Example with primitive arrays
public class PrimitivePerformance {

    // ~4x memory difference
    int[] primitiveArray = new int[1_000_000];        // ~4 MB
    Integer[] wrapperArray = new Integer[1_000_000];  // ~16 MB + references

    // Use primitive streams
    public int sumPrimitive(int[] arr) {
        return IntStream.of(arr).sum();  // No boxing
    }
}
```

---

## Concurrency Optimization

### Lock-Free Data Structures

```java
public class LockFreeCounter {
    private final AtomicLong counter = new AtomicLong(0);

    // Non-blocking increment
    public long increment() {
        return counter.incrementAndGet();
    }

    // CAS loop for complex operations
    public long incrementWithLimit(long limit) {
        long current, next;
        do {
            current = counter.get();
            if (current >= limit) return current;
            next = current + 1;
        } while (!counter.compareAndSet(current, next));
        return next;
    }
}

// LongAdder for high contention (better than AtomicLong)
public class HighContentionCounter {
    private final LongAdder adder = new LongAdder();

    public void increment() {
        adder.increment();  // Uses striped cells
    }

    public long sum() {
        return adder.sum();  // May not be exact under contention
    }
}
```

### False Sharing Prevention

```java
// Cache lines are typically 64 bytes
// False sharing occurs when unrelated data shares a cache line

// BAD: Counters on same cache line
public class FalseSharing {
    volatile long counter1;  // Same cache line!
    volatile long counter2;  // Causes invalidation traffic
}

// GOOD: Padded to separate cache lines
public class NoPadding {
    volatile long counter1;
    long p1, p2, p3, p4, p5, p6, p7;  // Padding
    volatile long counter2;
}

// Java 8+: @Contended annotation
@sun.misc.Contended
public class ContentionFree {
    volatile long counter1;
    volatile long counter2;
}
// Requires: -XX:-RestrictContended
```

### Thread Pool Sizing

```java
public class ThreadPoolSizing {

    // CPU-bound tasks: N threads (N = number of cores)
    ExecutorService cpuBound = Executors.newFixedThreadPool(
        Runtime.getRuntime().availableProcessors()
    );

    // I/O-bound tasks: More threads
    // Formula: N * (1 + W/C) where W = wait time, C = compute time
    // If 80% waiting: N * (1 + 0.8/0.2) = N * 5
    ExecutorService ioBound = Executors.newFixedThreadPool(
        Runtime.getRuntime().availableProcessors() * 5
    );

    // Mixed workload: Use work-stealing
    ExecutorService mixed = Executors.newWorkStealingPool();
}
```

---

## Profiling and Benchmarking

### JMH (Java Microbenchmark Harness)

```java
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Benchmark)
@Fork(value = 2, warmups = 1)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class StringBenchmark {

    private List<String> items;

    @Setup
    public void setup() {
        items = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            items.add("item" + i);
        }
    }

    @Benchmark
    public String concatWithPlus() {
        String result = "";
        for (String item : items) {
            result += item;
        }
        return result;
    }

    @Benchmark
    public String concatWithBuilder() {
        StringBuilder sb = new StringBuilder();
        for (String item : items) {
            sb.append(item);
        }
        return sb.toString();
    }

    @Benchmark
    public String concatWithJoin() {
        return String.join("", items);
    }
}

// Run: mvn clean install && java -jar target/benchmarks.jar
```

### Profiling Tools

```
Common profiling tools:
1. JVisualVM (bundled with JDK)
2. JProfiler (commercial)
3. YourKit (commercial)
4. async-profiler (free, low overhead)
5. Java Flight Recorder (JFR)

# Enable JFR (Java 11+)
java -XX:StartFlightRecording=duration=60s,filename=recording.jfr MyApp

# Analyze with JDK Mission Control (JMC)
jmc recording.jfr
```

---

## Common Performance Anti-patterns

### 1. Premature Optimization

```java
// DON'T optimize without measuring!
// Profile first, then optimize hot paths

// Often these micro-optimizations don't matter:
int x = value / 2;      // vs
int x = value >> 1;     // Compiler optimizes anyway

// Focus on:
// 1. Algorithm complexity (O(n²) → O(n log n))
// 2. I/O operations
// 3. Memory allocations in hot loops
// 4. Lock contention
```

### 2. Excessive Object Creation

```java
// BAD: Creating objects in hot loop
public void processEvents(List<Event> events) {
    for (Event event : events) {
        DateFormat df = new SimpleDateFormat("yyyy-MM-dd");  // Created each time!
        String date = df.format(event.getDate());
    }
}

// GOOD: Reuse or use ThreadLocal
private static final ThreadLocal<DateFormat> DATE_FORMAT =
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

public void processEventsBetter(List<Event> events) {
    DateFormat df = DATE_FORMAT.get();
    for (Event event : events) {
        String date = df.format(event.getDate());
    }
}
```

### 3. Inefficient Iteration

```java
// BAD: LinkedList with index access
LinkedList<String> list = getLinkedList();
for (int i = 0; i < list.size(); i++) {
    String s = list.get(i);  // O(n) each time! O(n²) total
}

// GOOD: Use iterator
for (String s : list) {
    // O(1) per element, O(n) total
}
```

---

## Interview Questions

### Q1: How would you identify a memory leak?

```java
// Signs of memory leak:
// 1. OutOfMemoryError
// 2. Increasing heap usage over time
// 3. GC taking longer and longer

// Investigation steps:
// 1. Take heap dump: jmap -dump:format=b,file=heap.hprof <pid>
// 2. Analyze with MAT (Memory Analyzer Tool)
// 3. Look for dominator tree, largest objects
// 4. Check for references that should have been cleared

// Common causes:
// - Collections growing without bounds
// - Static fields holding references
// - Listeners not unregistered
// - ThreadLocal not cleaned in thread pools
```

### Q2: Explain JIT compilation levels

```
JIT Compilation Levels:
Level 0: Interpreter
Level 1: Simple C1 (quick compilation, few optimizations)
Level 2: Limited C1 (with profiling)
Level 3: Full C1 (with profiling)
Level 4: C2 (aggressive optimizations)

Tiered Compilation (default):
Interpreter → C1 (quick startup) → C2 (peak performance)

Key C2 optimizations:
- Inlining
- Escape analysis
- Loop unrolling
- Dead code elimination
- Lock elision
```

### Q3: What is the difference between -Xms and -Xmx?

```bash
-Xms: Initial (minimum) heap size
-Xmx: Maximum heap size

Best practice: Set them equal to avoid heap resizing overhead
java -Xms4g -Xmx4g MyApp

Why resize is expensive:
1. JVM must allocate new memory
2. Copy objects to new space
3. Update all references
4. May trigger GC
```
