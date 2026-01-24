# JVM Internals for Systems Programmers

For readers of Bach and Stevens — mapping JVM abstractions to OS primitives.

---

## 1. Process Model: JVM as a User-Space OS

The JVM is essentially a **user-space operating system** running atop the host OS:

| OS Concept (Bach/Stevens) | JVM Equivalent |
|---------------------------|----------------|
| Process | JVM instance |
| Thread (LWP/pthread) | `java.lang.Thread` (1:1 mapped to native threads since JDK 1.3) |
| Virtual address space | JVM heap + metaspace + native memory | | `exec()` loading | Class loading & linking | | Dynamic linking (`ld.so`) | `ClassLoader` hierarchy | | Signal handling | `sun.misc.Signal` (limited), safepoints |
| `mmap()` regions | Memory-mapped buffers (`MappedByteBuffer`) |

**Key insight**: Unlike a process that gets a flat virtual address space from the kernel, the JVM *partitions* its heap into generations and manages it with its own allocator — the OS sees one big `mmap`'d region.

---

## 2. Memory Layout: Beyond `brk()` and `mmap()`

The JVM doesn't use `malloc()`/`brk()` for Java objects. Instead:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Native Memory                            │
│  (JNI allocations, direct buffers, JVM internal structures)     │
├─────────────────────────────────────────────────────────────────┤
│                         Metaspace                               │
│  (Class metadata — replaced PermGen in JDK 8)                   │
│  Allocated via mmap(), grows dynamically, no GC                 │
├─────────────────────────────────────────────────────────────────┤
│                        Code Cache                               │
│  (JIT-compiled native code, mmap with PROT_EXEC)                │
├─────────────────────────────────────────────────────────────────┤
│                          Heap                                   │
│  ┌────────────┬────────────┬──────────────────────────────┐    │
│  │   Eden     │ Survivor   │         Old Generation       │    │
│  │  (Young)   │   S0/S1    │                              │    │
│  └────────────┴────────────┴──────────────────────────────┘    │
│  Reserved via mmap(MAP_PRIVATE|MAP_ANONYMOUS|MAP_NORESERVE)     │
│  Committed incrementally as needed                              │
├─────────────────────────────────────────────────────────────────┤
│                     Thread Stacks                               │
│  (One per thread, default ~1MB, native stack via pthread)       │
└─────────────────────────────────────────────────────────────────┘
```

### Heap Reservation vs Commitment

```c
// Conceptually, what HotSpot does at startup:
void* heap = mmap(NULL, max_heap_size,
                  PROT_NONE,  // Reserve only, no physical pages
                  MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);

// As heap grows, commit pages:
mprotect(heap + committed, new_commit_size, PROT_READ | PROT_WRITE);
```

This is why `-Xmx` can be huge without immediate RSS impact — only `-Xms` pages are committed.

---

## 3. Threading: From Green Threads to Virtual Threads

### Historical Evolution

1. **JDK 1.0-1.2**: Green threads (M:1, user-space scheduling like early `setjmp/longjmp` coroutines)
2. **JDK 1.3+**: Native threads (1:1 mapping to `pthread_create()`)
3. **JDK 21+**: Virtual threads (M:N scheduling, similar to goroutines)

### Native Thread Mapping (Current Default)

```
Java Thread                    OS/Kernel
───────────────────────────────────────────
new Thread().start()  ──────►  pthread_create()
                               clone(CLONE_VM | CLONE_FS | ...)
Thread.sleep()        ──────►  nanosleep() / futex wait
synchronized          ──────►  futex (fast path: CAS in userspace)
Object.wait()         ──────►  futex_wait() via pthread_cond
Thread.interrupt()    ──────►  pthread_kill(SIGUSR2) + flag check
```

### Thread Stack Layout

Each Java thread has **two stacks**:
1. **Native stack**: Normal pthread stack for JNI, VM code (~256KB-1MB)
2. **Java stack**: Frames for Java methods (within native stack, managed by JVM)

```
High Address ─────────────────────────
              │ Native Frame (JNI)   │
              ├──────────────────────┤
              │ Java Frame (interp)  │
              │  - locals[]          │
              │  - operand stack     │
              │  - frame data        │
              ├──────────────────────┤
              │ Java Frame (compiled)│
              │  (register-based,    │
              │   different layout)  │
              ├──────────────────────┤
              │       ...            │
Low Address  ─────────────────────────
              │ Guard Page (SIGSEGV) │  ◄── Stack overflow detection
              ─────────────────────────
```

---

## 4. Synchronization: Locks Without Always Syscalling

Java's `synchronized` is **not** a naive `pthread_mutex_lock()`. HotSpot uses a sophisticated hierarchy:

### Lock Inflation States

```
┌─────────────────┐    contention    ┌─────────────────┐    contention    ┌─────────────────┐
│   Biased Lock   │ ───────────────► │   Thin Lock     │ ───────────────► │   Fat Lock      │
│  (thread ID in  │                  │  (CAS spinlock) │                  │  (OS mutex +    │
│   object header)│                  │                 │                  │   futex wait)   │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
     No syscall                          No syscall                           syscall
    (until revoked)                   (spin a few times)                  (pthread_mutex)
```

### Object Header (Mark Word) — 64-bit

```
Biased:      [JavaThread* (54-bit) | epoch (2) | age (4) | 1 | 01]
Thin:        [         ptr to lock record (62)          | 00     ]
Fat:         [     ptr to ObjectMonitor (62)            | 10     ]
GC marked:   [                                          | 11     ]
```

Compare to futex: Java tries to avoid kernel transitions entirely for uncontended cases.

---

## 5. Class Loading: Dynamic Linking, JVM-Style

Think of `ClassLoader` as the JVM's `ld.so`:

| `ld.so` / Dynamic Linker | JVM Class Loader |
|--------------------------|------------------|
| `dlopen()` | `ClassLoader.loadClass()` |
| Symbol resolution | Constant pool resolution |
| Relocation | Bytecode rewriting / linking |
| `LD_LIBRARY_PATH` | `-classpath`, module path |
| Lazy binding (`RTLD_LAZY`) | Lazy resolution (default) |

### Loading Phases

```
┌─────────┐    ┌─────────────┐    ┌───────────┐    ┌──────────────┐
│ Loading │───►│  Linking    │───►│ Preparing │───►│ Initializing │
│         │    │ (verify +   │    │ (allocate │    │ (<clinit>)   │
│         │    │  resolve)   │    │  statics) │    │              │
└─────────┘    └─────────────┘    └───────────┘    └──────────────┘
   │
   └── Read .class bytes, parse into internal Klass structure
       (like reading ELF headers, but for JVM bytecode)

```

## 6. Garbage Collection: Userspace Memory Management

The GC is the JVM's equivalent of a memory allocator + compactor. Unlike `malloc/free`, it's automatic and stop-the-world (mostly).

### Allocation Fast Path (TLAB)

Each thread gets a **Thread-Local Allocation Buffer** — a pre-allocated chunk of Eden:

```c
// Pseudo-code for object allocation
Object* allocate(size_t size) {
    Thread* t = current_thread();
    if (t->tlab_top + size <= t->tlab_end) {
        Object* obj = t->tlab_top;
        t->tlab_top += size;      // No CAS, no lock — just bump pointer
        return obj;
    }
    return slow_path_allocate(size);  // Refill TLAB or allocate in shared Eden
}
```

This is faster than `malloc()` — literally a pointer bump with no syscall.

### GC Algorithms Comparison

| Algorithm | Pause Behavior | Memory Overhead | Use Case |
|-----------|---------------|-----------------|----------|
| Serial | Full STW | Minimal | Single-core, small heaps |
| Parallel (Throughput) | Full STW, parallel threads | Low | Batch processing |
| G1 | Incremental, region-based | ~10-20% | General purpose (default) |
| ZGC | Sub-ms pauses, concurrent | ~15% | Low-latency (<10ms) |
| Shenandoah | Sub-ms, concurrent compact | ~15% | Low-latency |

### Write Barriers: Tracking Cross-Generation Pointers

When old generation objects point to young objects, GC needs to know. This is tracked via **card tables**:

```c
// After every reference store: old.field = young_obj
void post_write_barrier(Object** field, Object* new_val) {
    // Card table: 1 byte per 512-byte heap region
    size_t card_index = ((uintptr_t)field - heap_base) >> 9;
    card_table[card_index] = DIRTY;
}
```

Similar concept to OS dirty bit tracking for copy-on-write, but in userspace.

---

## 7. JIT Compilation: Runtime Code Generation

The JVM starts interpreting bytecode, then compiles hot methods to native code.

### Compilation Tiers (Tiered Compilation, default since JDK 8)

```
Level 0: Interpreter
    │
    ▼ (invocation count > threshold)
Level 1-3: C1 (Client compiler) — fast compilation, moderate optimization
    │
    ▼ (more profiling data)
Level 4: C2 (Server compiler) — slow compilation, aggressive optimization
```

### Generated Code Location

JIT code goes into the **Code Cache**, an `mmap`'d region with `PROT_EXEC`:

```c
// Simplified code cache allocation
void* code_cache = mmap(NULL, code_cache_size,
                        PROT_READ | PROT_WRITE | PROT_EXEC,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
```

Modern JVMs split this into segments (non-method, profiled, non-profiled) for better cache behavior.

### Deoptimization

Unlike static compilation, JIT can **undo** optimizations at runtime:

```
Speculative optimization:
  "This virtual call always goes to ArrayList.add()"
  → Inline the method directly

Guard fails (different subclass appears):
  → Deoptimize: throw away compiled code
  → Return to interpreter
  → Recompile with less aggressive assumptions
```

This is impossible with static linking — the JVM has runtime type feedback.

---

## 8. Safepoints: Cooperative Scheduling for GC

The JVM can't just `SIGSTOP` all threads for GC — it needs threads at "safe" locations where object references are known.

### Safepoint Mechanism

```c
// Global safepoint page (mapped to a known address)
volatile int* safepoint_page;

// In compiled code, periodic poll:
void safepoint_poll() {
    int dummy = *safepoint_page;  // Load from safepoint page
}

// To trigger safepoint (e.g., for GC):
void arm_safepoint() {
    mprotect(safepoint_page, page_size, PROT_NONE);  // Remove read permission
    // All threads will SIGSEGV on next poll, handled by JVM signal handler
}
```

This is similar to how a kernel might use IPIs, but implemented with `mprotect` + `SIGSEGV`.

### Time-To-Safepoint (TTSP) Problem

Long TTSP = GC latency. Common culprits:
- Counted loops without safepoint polls (JVM optimization gone wrong)
- Large array copies (no safepoint in `System.arraycopy`)
- JNI calls (thread not at safepoint while in native code)

---

## 9. JNI: The FFI Boundary

JNI is the JVM's foreign function interface, like calling C from Python but more structured.

### Thread State Transitions

```
┌────────────────┐              ┌────────────────┐
│  _thread_in_   │   JNI call   │  _thread_in_   │
│     Java       │ ───────────► │    native      │
│  (at safepoint │              │ (not at safe-  │
│   polls)       │              │  point)        │
└────────────────┘              └────────────────┘
        ▲                              │
        │         JNI return           │
        └──────────────────────────────┘
              (must check for pending safepoint)
```

**Critical**: When in native code, thread doesn't respond to safepoint requests. Long-running native code blocks GC.

### JNI Handle Types

| Handle Type | Scope | GC Behavior |
|-------------|-------|-------------|
| Local | Current native method | Auto-freed on return |
| Global | Until explicitly deleted | Prevents GC of referent |
| Weak Global | Until explicitly deleted | Doesn't prevent GC |

### Critical Regions

```c
jbyte* bytes = (*env)->GetPrimitiveArrayCritical(env, array, NULL);
// Inside critical region: GC is BLOCKED
// Don't do anything slow here!
(*env)->ReleasePrimitiveArrayCritical(env, array, bytes, 0);
```

---

## 10. Signals: JVM's Handler Chain

The JVM installs its own signal handlers, chained with application handlers:

| Signal | JVM Use |
|--------|---------|
| `SIGSEGV` | Safepoint polling, null pointer checks, stack overflow |
| `SIGBUS` | Memory mapping errors |
| `SIGUSR1` | Thread dump (often) |
| `SIGUSR2` | Internal (e.g., thread interruption) |
| `SIGQUIT` | Print thread dump to stderr |

### Null Check Optimization

Instead of:
```c
if (obj == NULL) throw NullPointerException;
obj->field;  // access
```

JVM does:
```c
obj->field;  // Just access it — if NULL, SIGSEGV
// Signal handler catches SIGSEGV, checks if in generated code,
// throws NullPointerException from handler
```

This is called **implicit null checks** — removes a branch from the hot path.

---

## 11. Useful Diagnostic Tools

| Tool | Purpose | Analogy |
|------|---------|---------|
| `jstack <pid>` | Thread dump | `pstack` / `gdb bt` |
| `jmap -heap <pid>` | Heap summary | `/proc/pid/maps` analysis |
| `jmap -dump:format=b,file=heap.hprof <pid>` | Heap dump | Core dump |
| `jstat -gc <pid>` | GC statistics | `vmstat` for GC |
| `jhsdb` (JDK 9+) | Serviceability agent | `gdb` for JVM |
| `async-profiler` | Low-overhead profiling | `perf` |
| `-XX:+PrintAssembly` | Show JIT output | `objdump -d` |

### Viewing JIT-Generated Assembly

```bash
# Requires hsdis (HotSpot disassembler plugin)
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintAssembly -XX:PrintAssemblyOptions=intel MyClass
```

---

## 12. Key Flags for Systems Programmers

```bash
# Memory
-Xms4g -Xmx4g          # Initial/max heap (set equal to avoid resize pauses)
-XX:MaxMetaspaceSize=512m  # Limit metaspace
-XX:ReservedCodeCacheSize=256m  # JIT code cache

# GC Selection
-XX:+UseG1GC           # G1 (default in JDK 9+)
-XX:+UseZGC            # ZGC (low latency)
-XX:+UseShenandoahGC   # Shenandoah

# Diagnostics
-XX:+HeapDumpOnOutOfMemoryError
-XX:NativeMemoryTracking=summary  # Track native memory
-XX:+PrintSafepointStatistics     # Safepoint timing

# Performance
-XX:+UseTransparentHugePages      # If OS supports
-XX:+AlwaysPreTouch               # Commit all heap pages at startup
```

---

## Quick Reference: JVM ↔ OS Mapping

| You Know (UNIX) | JVM Equivalent |
|-----------------|----------------|
| `fork()` | `ProcessBuilder` (no fork, uses `posix_spawn`) |
| `exec()` | Class loading + linking |
| `pthread_create()` | `new Thread().start()` |
| `pthread_mutex` | `synchronized` (fat lock state) |
| Spin lock | `synchronized` (thin lock state) |
| `mmap(PROT_NONE)` + `mprotect()` | Heap reservation + commitment |
| `brk()`/`sbrk()` | Not used — heap is one big `mmap` |
| Page fault handler | Safepoint page SIGSEGV handler |
| TLB shootdown | Safepoint (cooperative, not IPI) |
| `/proc/self/maps` | `jcmd <pid> VM.native_memory` |
| `strace` | `async-profiler`, `perf`, or JVMTI agents |
| Core dump | `jmap -dump` (heap dump) |

---

*"The JVM is what happens when you implement half an operating system in userspace, then spend 25 years optimizing it."*
```

