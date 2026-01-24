# Java Concurrency and Multithreading - Deep Dive

## Table of Contents
1. [Thread Fundamentals](#thread-fundamentals)
2. [Thread Lifecycle and States](#thread-lifecycle)
3. [Synchronization Internals](#synchronization-internals)
4. [Locks and Monitors](#locks-and-monitors)
5. [volatile and Memory Barriers](#volatile-keyword)
6. [java.util.concurrent Package](#concurrent-utilities)
7. [Thread Pools and Executors](#thread-pools)
8. [Concurrent Collections](#concurrent-collections)
9. [Common Concurrency Patterns](#concurrency-patterns)
10. [Interview Questions](#interview-questions)

---

## Thread Fundamentals

### Thread Creation Methods

```java
// Method 1: Extending Thread class
class MyThread extends Thread {
    @Override
    public void run() {
        System.out.println("Thread running: " + Thread.currentThread().getName());
    }
}

// Method 2: Implementing Runnable (Preferred)
class MyRunnable implements Runnable {
    @Override
    public void run() {
        System.out.println("Runnable running: " + Thread.currentThread().getName());
    }
}

// Method 3: Using Callable (Returns value, can throw exceptions)
class MyCallable implements Callable<Integer> {
    @Override
    public Integer call() throws Exception {
        return 42;
    }
}

// Method 4: Lambda expressions (Java 8+)
Runnable r = () -> System.out.println("Lambda thread");

// Usage
public class ThreadDemo {
    public static void main(String[] args) throws Exception {
        // Method 1
        Thread t1 = new MyThread();
        t1.start();
        
        // Method 2
        Thread t2 = new Thread(new MyRunnable());
        t2.start();
        
        // Method 3
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<Integer> future = executor.submit(new MyCallable());
        System.out.println("Callable result: " + future.get());
        executor.shutdown();
        
        // Method 4
        new Thread(() -> System.out.println("Lambda")).start();
    }
}
```

---

## Thread Lifecycle and States

### Thread State Diagram

```
                          ┌─────────────────────────────────────────┐
                          │                                         │
                          ▼                                         │
┌───────┐  start()   ┌─────────┐   scheduler    ┌─────────┐        │
│  NEW  │ ─────────► │RUNNABLE │ ◄────────────► │ RUNNING │        │
└───────┘            └────┬────┘   dispatch     └────┬────┘        │
                          │                          │             │
                          │                          │             │
         ┌────────────────┼──────────────────────────┼─────────────┘
         │                │                          │
         │   wait()       │   sleep()/join()         │  run() completes
         │   Lock.lock()  │   I/O blocking           │  or exception
         ▼                ▼                          ▼
    ┌─────────┐     ┌──────────┐              ┌────────────┐
    │ WAITING │     │ TIMED_   │              │ TERMINATED │
    │         │     │ WAITING  │              │            │
    └────┬────┘     └────┬─────┘              └────────────┘
         │               │
         │ notify()      │ timeout expires
         │ notifyAll()   │ sleep completes
         │               │
         └───────────────┴──────► Back to RUNNABLE
```

### Thread States in Code

```java
public class ThreadStateDemo {
    public static void main(String[] args) throws InterruptedException {
        Object lock = new Object();
        
        Thread t = new Thread(() -> {
            synchronized (lock) {
                try {
                    lock.wait();  // WAITING state
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        });
        
        System.out.println("After creation: " + t.getState());  // NEW
        
        t.start();
        Thread.sleep(100);
        System.out.println("After start (waiting): " + t.getState());  // WAITING
        
        synchronized (lock) {
            lock.notify();
        }
        t.join();
        System.out.println("After completion: " + t.getState());  // TERMINATED
    }
}
```

---

## Synchronization Internals

### Object Monitor Structure (HotSpot JVM)

Every Java object has an associated monitor. The object header contains mark word that stores lock state.

```
Object Header Layout (64-bit JVM):
┌────────────────────────────────────────────────────────────────────────┐
│                            Mark Word (64 bits)                         │
├────────────────────────────────────────────────────────────────────────┤
│ Unlocked:     │ identity_hashcode:31│ unused:1 │ age:4 │ biased:1│ 01 │
├────────────────────────────────────────────────────────────────────────┤
│ Biased:       │ thread_id:54 │ epoch:2 │ unused:1 │ age:4 │ biased:1│ 01│
├────────────────────────────────────────────────────────────────────────┤
│ Lightweight:  │            ptr_to_lock_record:62                │ 00 │
├────────────────────────────────────────────────────────────────────────┤
│ Heavyweight:  │            ptr_to_heavyweight_monitor:62        │ 10 │
├────────────────────────────────────────────────────────────────────────┤
│ GC Marked:    │                    (GC specific)                │ 11 │
└────────────────────────────────────────────────────────────────────────┘
│                        Class Pointer (32/64 bits)                      │
└────────────────────────────────────────────────────────────────────────┘
```

### Lock Escalation Path

```
┌──────────────┐     contention     ┌─────────────────┐     contention
│   No Lock    │ ─────────────────► │ Biased Locking  │ ───────────────►
│   (Fastest)  │                    │ (Single Thread) │
└──────────────┘                    └─────────────────┘
                                                              │
                                                              ▼
┌──────────────────┐     contention     ┌─────────────────────────────┐
│ Heavyweight Lock │ ◄───────────────── │ Lightweight Lock (CAS/Spin) │
│ (OS Mutex)       │                    │ (Stack-based lock record)   │
└──────────────────┘                    └─────────────────────────────┘
```

### synchronized Block Bytecode

```java
// Source code
public void syncMethod() {
    synchronized (this) {
        // critical section
    }
}

// Bytecode (simplified)
public void syncMethod();
  Code:
    0: aload_0           // Load 'this'
    1: dup               // Duplicate for exception handler
    2: astore_1          // Store lock reference
    3: monitorenter      // ◄── Acquire monitor
    4: aload_1           
    5: monitorexit       // ◄── Release monitor (normal path)
    6: goto 14
    9: astore_2          // Exception handler
   10: aload_1
   11: monitorexit       // ◄── Release monitor (exception path)
   12: aload_2
   13: athrow
   14: return
```

---

## volatile Keyword

### What volatile Guarantees

```java
// volatile provides:
// 1. Visibility: Changes visible to all threads immediately
// 2. Ordering: Prevents instruction reordering (memory barrier)

// volatile does NOT provide:
// 1. Atomicity for compound operations (i++, check-then-act)

public class VolatileDemo {
    private volatile boolean running = true;
    private volatile int counter = 0;

    // CORRECT: Simple flag
    public void stop() {
        running = false;  // Immediately visible to other threads
    }

    public void runLoop() {
        while (running) {  // Always reads fresh value
            doWork();
        }
    }

    // INCORRECT: volatile doesn't make i++ atomic!
    public void increment() {
        counter++;  // NOT ATOMIC! Read-Modify-Write
    }

    // CORRECT: Use AtomicInteger instead
    private AtomicInteger atomicCounter = new AtomicInteger(0);
    public void safeIncrement() {
        atomicCounter.incrementAndGet();  // Atomic CAS operation
    }
}
```

### Memory Barriers

```
volatile write inserts:    volatile read inserts:
┌───────────────────┐      ┌───────────────────┐
│   StoreStore      │      │   LoadLoad        │
│   barrier         │      │   barrier         │
├───────────────────┤      ├───────────────────┤
│   VOLATILE WRITE  │      │   VOLATILE READ   │
├───────────────────┤      ├───────────────────┤
│   StoreLoad       │      │   LoadStore       │
│   barrier         │      │   barrier         │
└───────────────────┘      └───────────────────┘

Barriers prevent reordering across the barrier point.
```

### Double-Checked Locking Pattern

```java
// Singleton with proper double-checked locking
public class Singleton {
    // volatile prevents instruction reordering
    private static volatile Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {                 // First check (no locking)
            synchronized (Singleton.class) {
                if (instance == null) {         // Second check (with lock)
                    instance = new Singleton(); // Safe with volatile
                }
            }
        }
        return instance;
    }
}

// Why volatile is needed:
// Without volatile, this can happen:
// 1. Memory allocated for Singleton
// 2. instance assigned to memory address  ← Other thread sees non-null!
// 3. Constructor executes                 ← But object not initialized!
// volatile prevents steps 2 and 3 from being reordered
```

---

## Locks and Monitors

### ReentrantLock vs synchronized

```java
import java.util.concurrent.locks.*;

public class LockComparison {

    // synchronized - implicit lock
    private final Object lock = new Object();

    public void synchronizedMethod() {
        synchronized (lock) {
            // critical section
        }
    }

    // ReentrantLock - explicit lock with more features
    private final ReentrantLock reentrantLock = new ReentrantLock();

    public void reentrantLockMethod() {
        reentrantLock.lock();
        try {
            // critical section
        } finally {
            reentrantLock.unlock();  // ALWAYS in finally!
        }
    }

    // ReentrantLock advanced features
    public void advancedFeatures() throws InterruptedException {
        // 1. Try lock with timeout
        if (reentrantLock.tryLock(1, TimeUnit.SECONDS)) {
            try {
                // Got the lock within 1 second
            } finally {
                reentrantLock.unlock();
            }
        } else {
            // Couldn't get lock, do something else
        }

        // 2. Interruptible lock acquisition
        reentrantLock.lockInterruptibly();  // Can be interrupted while waiting

        // 3. Check if lock is held
        boolean isHeld = reentrantLock.isLocked();
        boolean isHeldByMe = reentrantLock.isHeldByCurrentThread();
        int holdCount = reentrantLock.getHoldCount();  // For reentrant locks
    }
}
```

### Comparison Table

| Feature | synchronized | ReentrantLock |
|---------|-------------|---------------|
| Automatic release | Yes | No (finally required) |
| Try with timeout | No | Yes (tryLock) |
| Interruptible | No | Yes (lockInterruptibly) |
| Fair locking | No | Yes (optional) |
| Multiple conditions | No (1 wait set) | Yes (multiple Conditions) |
| Performance | Similar (JDK 6+) | Similar |

### ReentrantLock Internals (AbstractQueuedSynchronizer)

```
ReentrantLock uses AQS (AbstractQueuedSynchronizer):

┌───────────────────────────────────────────────────────────────────────┐
│                     AbstractQueuedSynchronizer                        │
├───────────────────────────────────────────────────────────────────────┤
│  state: int (volatile)                                                │
│  - 0 = unlocked                                                       │
│  - 1+ = locked (count for reentrant)                                  │
│                                                                       │
│  exclusiveOwnerThread: Thread                                         │
│  - Reference to thread holding lock                                   │
│                                                                       │
│  Wait Queue (CLH variant):                                            │
│  head ──► [Node] ──► [Node] ──► [Node] ──► tail                       │
│           Thread1    Thread2    Thread3                               │
│           WAITING    WAITING    WAITING                               │
└───────────────────────────────────────────────────────────────────────┘

Lock acquisition:
1. CAS to change state from 0 to 1
2. If successful, set exclusiveOwnerThread
3. If failed, enqueue in wait queue, park thread

Unlock:
1. Set state to 0, clear exclusiveOwnerThread
2. Unpark head of wait queue
```

### ReadWriteLock

```java
public class ReadWriteLockDemo {
    private final ReadWriteLock rwLock = new ReentrantReadWriteLock();
    private final Lock readLock = rwLock.readLock();
    private final Lock writeLock = rwLock.writeLock();

    private Map<String, Object> cache = new HashMap<>();

    // Multiple readers can access simultaneously
    public Object read(String key) {
        readLock.lock();
        try {
            return cache.get(key);
        } finally {
            readLock.unlock();
        }
    }

    // Writers have exclusive access
    public void write(String key, Object value) {
        writeLock.lock();
        try {
            cache.put(key, value);
        } finally {
            writeLock.unlock();
        }
    }
}
```

### StampedLock (Java 8+)

```java
public class StampedLockDemo {
    private final StampedLock sl = new StampedLock();
    private double x, y;

    // Optimistic read (no blocking!)
    public double distanceFromOrigin() {
        // Try optimistic read first
        long stamp = sl.tryOptimisticRead();
        double currentX = x, currentY = y;

        // Validate that no write occurred
        if (!sl.validate(stamp)) {
            // Optimistic read failed, use regular read lock
            stamp = sl.readLock();
            try {
                currentX = x;
                currentY = y;
            } finally {
                sl.unlockRead(stamp);
            }
        }
        return Math.sqrt(currentX * currentX + currentY * currentY);
    }

    // Write lock
    public void move(double deltaX, double deltaY) {
        long stamp = sl.writeLock();
        try {
            x += deltaX;
            y += deltaY;
        } finally {
            sl.unlockWrite(stamp);
        }
    }
}
```

---

## Thread Pools and Executors

### Executor Framework Hierarchy

```
                         Executor (interface)
                              │
                              ▼
                    ExecutorService (interface)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    AbstractExecutorService   │    ScheduledExecutorService
              │               │               │
              ▼               │               ▼
    ThreadPoolExecutor ◄──────┘   ScheduledThreadPoolExecutor
              │                               │
              └───────────────────────────────┘
                              ▲
                              │
                    ForkJoinPool (work-stealing)
```

### ThreadPoolExecutor Parameters

```java
public ThreadPoolExecutor(
    int corePoolSize,        // Min threads kept alive
    int maximumPoolSize,     // Max threads allowed
    long keepAliveTime,      // Idle thread timeout
    TimeUnit unit,           // Time unit for keepAlive
    BlockingQueue<Runnable> workQueue,  // Task queue
    ThreadFactory threadFactory,        // Creates new threads
    RejectedExecutionHandler handler    // Rejection policy
);
```

### Task Execution Flow

```
Task Submission Flow:
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  execute(task)                                                             │
│       │                                                                    │
│       ▼                                                                    │
│  ┌─────────────────┐  Yes   ┌──────────────────┐                          │
│  │ Workers < core? │───────►│ Create new thread│                          │
│  └────────┬────────┘        └──────────────────┘                          │
│           │ No                                                             │
│           ▼                                                                │
│  ┌─────────────────┐  Yes   ┌──────────────────┐                          │
│  │ Queue not full? │───────►│ Add to queue     │                          │
│  └────────┬────────┘        └──────────────────┘                          │
│           │ No                                                             │
│           ▼                                                                │
│  ┌─────────────────┐  Yes   ┌──────────────────┐                          │
│  │ Workers < max?  │───────►│ Create new thread│                          │
│  └────────┬────────┘        └──────────────────┘                          │
│           │ No                                                             │
│           ▼                                                                │
│  ┌─────────────────┐                                                       │
│  │ Reject task     │  (RejectedExecutionHandler)                          │
│  └─────────────────┘                                                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Common Thread Pools

```java
public class ThreadPoolExamples {

    // Fixed thread pool - bounded, fixed size
    ExecutorService fixed = Executors.newFixedThreadPool(4);
    // Uses LinkedBlockingQueue (unbounded) - can cause OOM!

    // Cached thread pool - grows as needed
    ExecutorService cached = Executors.newCachedThreadPool();
    // Uses SynchronousQueue - no capacity, creates new threads
    // Can create unlimited threads!

    // Single thread - sequential execution
    ExecutorService single = Executors.newSingleThreadExecutor();

    // Scheduled - delayed/periodic tasks
    ScheduledExecutorService scheduled = Executors.newScheduledThreadPool(2);
    scheduled.scheduleAtFixedRate(() -> doTask(), 0, 1, TimeUnit.SECONDS);

    // Work-stealing (Java 8+) - ForkJoinPool
    ExecutorService workStealing = Executors.newWorkStealingPool();

    // Custom thread pool (RECOMMENDED for production)
    ExecutorService custom = new ThreadPoolExecutor(
        4,                    // corePoolSize
        16,                   // maximumPoolSize
        60L, TimeUnit.SECONDS, // keepAliveTime
        new ArrayBlockingQueue<>(100),  // Bounded queue!
        new ThreadPoolExecutor.CallerRunsPolicy()  // Rejection policy
    );
}
```

### Rejection Policies

```java
// When pool and queue are full:

// 1. AbortPolicy (default) - throws RejectedExecutionException
new ThreadPoolExecutor.AbortPolicy();

// 2. CallerRunsPolicy - caller thread runs the task
new ThreadPoolExecutor.CallerRunsPolicy();

// 3. DiscardPolicy - silently discard task
new ThreadPoolExecutor.DiscardPolicy();

// 4. DiscardOldestPolicy - discard oldest in queue
new ThreadPoolExecutor.DiscardOldestPolicy();

// 5. Custom policy
RejectedExecutionHandler custom = (r, executor) -> {
    // Log, persist, or handle rejection
    logger.warn("Task rejected: " + r.toString());
};
```

---

## Concurrent Collections

### ConcurrentHashMap Internals

```
ConcurrentHashMap (Java 8+):
┌──────────────────────────────────────────────────────────────────────┐
│  Node<K,V>[] table  (volatile)                                       │
├──────────────────────────────────────────────────────────────────────┤
│  [0] ──► Node ──► Node ──► Node   (linked list if < 8)              │
│  [1] ──► null                                                        │
│  [2] ──► TreeNode ──► TreeNode    (red-black tree if >= 8)          │
│  [3] ──► Node ──► Node                                               │
│  ...                                                                 │
└──────────────────────────────────────────────────────────────────────┘

Key features:
- No segment locks (unlike Java 7)
- Per-bucket synchronization using CAS + synchronized
- Lock-free reads using volatile
- Treeify threshold: 8 nodes → red-black tree
- Untreeify threshold: 6 nodes → linked list
```

### ConcurrentHashMap Operations

```java
public class ConcurrentHashMapDemo {
    private ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();

    // Atomic compound operations
    public void atomicOperations() {
        // putIfAbsent - only puts if key doesn't exist
        map.putIfAbsent("key", 1);

        // compute - atomic read-modify-write
        map.compute("key", (k, v) -> v == null ? 1 : v + 1);

        // computeIfAbsent - lazy initialization
        map.computeIfAbsent("key", k -> expensiveComputation(k));

        // merge - combine old and new values
        map.merge("key", 1, Integer::sum);  // Increment or set to 1

        // replace - conditional replace
        map.replace("key", 1, 2);  // Only if value is 1
    }

    // Bulk operations (Java 8+)
    public void bulkOperations() {
        // forEach with parallelism threshold
        map.forEach(2, (k, v) -> System.out.println(k + "=" + v));

        // search - find first matching entry
        String found = map.search(2, (k, v) -> v > 10 ? k : null);

        // reduce - aggregate values
        int sum = map.reduceValues(2, Integer::sum);
    }
}
```

### CopyOnWriteArrayList

```java
// Best for read-heavy, write-rare scenarios
public class CopyOnWriteDemo {
    private CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();

    // Write creates new array copy (expensive!)
    public void add(String item) {
        list.add(item);  // O(n) - copies entire array
    }

    // Reads never block, always see consistent snapshot
    public void iterate() {
        // Iterator uses snapshot - won't see concurrent modifications
        for (String item : list) {
            // Never throws ConcurrentModificationException
            System.out.println(item);
        }
    }
}
```

### BlockingQueue Implementations

```java
public class BlockingQueueDemo {

    // ArrayBlockingQueue - bounded, array-backed
    BlockingQueue<String> array = new ArrayBlockingQueue<>(100);

    // LinkedBlockingQueue - optionally bounded, linked nodes
    BlockingQueue<String> linked = new LinkedBlockingQueue<>(100);

    // PriorityBlockingQueue - unbounded, priority-ordered
    BlockingQueue<Task> priority = new PriorityBlockingQueue<>();

    // DelayQueue - elements become available after delay
    BlockingQueue<DelayedTask> delay = new DelayQueue<>();

    // SynchronousQueue - no capacity, direct handoff
    BlockingQueue<String> sync = new SynchronousQueue<>();
}
```

---

## Common Concurrency Patterns

### 1. Producer-Consumer

```java
public class ProducerConsumer {
    private final BlockingQueue<Task> queue = new ArrayBlockingQueue<>(10);
    private volatile boolean running = true;

    // Producer
    class Producer implements Runnable {
        @Override
        public void run() {
            while (running) {
                Task task = generateTask();
                try {
                    queue.put(task);  // Blocks if full
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
    }

    // Consumer
    class Consumer implements Runnable {
        @Override
        public void run() {
            while (running || !queue.isEmpty()) {
                try {
                    Task task = queue.poll(100, TimeUnit.MILLISECONDS);
                    if (task != null) {
                        process(task);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
    }
}
```

### 2. CountDownLatch (Wait for N events)

```java
public class CountDownLatchDemo {
    public void parallelStartup() throws InterruptedException {
        int serviceCount = 5;
        CountDownLatch latch = new CountDownLatch(serviceCount);

        for (int i = 0; i < serviceCount; i++) {
            new Thread(() -> {
                try {
                    initializeService();
                } finally {
                    latch.countDown();  // Decrement count
                }
            }).start();
        }

        latch.await();  // Wait until count reaches 0
        System.out.println("All services initialized!");
    }
}
```

### 3. CyclicBarrier (Wait for all threads at barrier)

```java
public class CyclicBarrierDemo {
    public void parallelPhases() {
        int threadCount = 4;
        CyclicBarrier barrier = new CyclicBarrier(threadCount,
            () -> System.out.println("Phase complete!"));  // Barrier action

        for (int i = 0; i < threadCount; i++) {
            new Thread(() -> {
                try {
                    phase1();
                    barrier.await();  // Wait for all threads

                    phase2();
                    barrier.await();  // Barrier is reusable!

                    phase3();
                } catch (Exception e) {
                    Thread.currentThread().interrupt();
                }
            }).start();
        }
    }
}
```

### 4. Semaphore (Limit concurrent access)

```java
public class SemaphoreDemo {
    private final Semaphore semaphore = new Semaphore(3);  // 3 permits

    public void accessResource() {
        try {
            semaphore.acquire();  // Block until permit available
            try {
                useResource();  // Only 3 threads can be here
            } finally {
                semaphore.release();  // Return permit
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

### 5. CompletableFuture (Async programming)

```java
public class CompletableFutureDemo {

    public void asyncOperations() {
        // Run async task
        CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
            return fetchData();
        });

        // Transform result
        CompletableFuture<Integer> transformed = future
            .thenApply(String::length)
            .thenApply(len -> len * 2);

        // Combine multiple futures
        CompletableFuture<String> combined = future
            .thenCombine(CompletableFuture.supplyAsync(() -> fetchMoreData()),
                (data1, data2) -> data1 + data2);

        // Handle errors
        CompletableFuture<String> withErrorHandling = future
            .exceptionally(ex -> "Default value")
            .thenApply(String::toUpperCase);

        // Wait for all
        CompletableFuture<Void> all = CompletableFuture.allOf(
            CompletableFuture.runAsync(() -> task1()),
            CompletableFuture.runAsync(() -> task2()),
            CompletableFuture.runAsync(() -> task3())
        );

        // Wait for any
        CompletableFuture<Object> any = CompletableFuture.anyOf(
            CompletableFuture.supplyAsync(() -> fastService()),
            CompletableFuture.supplyAsync(() -> slowService())
        );
    }
}
```

---

## Interview Questions

### Q1: What is the difference between wait() and sleep()?

| wait() | sleep() |
|--------|---------|
| Object method | Thread method |
| Releases lock | Holds lock |
| Must be in synchronized | No requirement |
| Woken by notify/notifyAll | Wakes after time |
| Used for inter-thread communication | Used for pause |

### Q2: How to prevent deadlock?

```java
// Deadlock conditions (all 4 must be present):
// 1. Mutual Exclusion
// 2. Hold and Wait
// 3. No Preemption
// 4. Circular Wait

// Prevention strategies:
// 1. Lock ordering - always acquire locks in same order
// 2. Lock timeout - tryLock with timeout
// 3. Deadlock detection - use tryLock, back off on failure
// 4. Single lock - use one lock instead of multiple
```

### Q3: Explain thread-safety of HashMap vs ConcurrentHashMap

```java
// HashMap - NOT thread-safe
// - Concurrent modification can corrupt internal structure
// - Can cause infinite loops during resize

// ConcurrentHashMap - Thread-safe
// - Lock-free reads (volatile)
// - Fine-grained locking for writes (per-bucket)
// - No null keys or values (prevents NPE ambiguity)
// - Weakly consistent iterators
```

### Q4: What is the happens-before relationship?

**Happens-before** guarantees that memory writes by one statement are visible to another statement. Key rules:
1. Program order within thread
2. Monitor unlock → subsequent lock
3. Volatile write → subsequent read
4. Thread start → first statement in thread
5. Thread actions → join returns
6. Transitivity

### Q5: Thread Local Usage

```java
public class ThreadLocalDemo {
    // Each thread has its own copy
    private static ThreadLocal<SimpleDateFormat> dateFormat =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

    public String formatDate(Date date) {
        return dateFormat.get().format(date);  // Thread-safe!
    }

    // IMPORTANT: Clean up in thread pools!
    public void cleanup() {
        dateFormat.remove();  // Prevent memory leaks
    }
}
```

### Q6: Fork/Join Framework

```java
public class ForkJoinDemo extends RecursiveTask<Long> {
    private final long[] numbers;
    private final int start, end;
    private static final int THRESHOLD = 10_000;

    public ForkJoinDemo(long[] numbers, int start, int end) {
        this.numbers = numbers;
        this.start = start;
        this.end = end;
    }

    @Override
    protected Long compute() {
        if (end - start <= THRESHOLD) {
            // Base case: compute directly
            long sum = 0;
            for (int i = start; i < end; i++) {
                sum += numbers[i];
            }
            return sum;
        } else {
            // Recursive case: split
            int mid = start + (end - start) / 2;
            ForkJoinDemo left = new ForkJoinDemo(numbers, start, mid);
            ForkJoinDemo right = new ForkJoinDemo(numbers, mid, end);

            left.fork();  // Submit to pool
            long rightResult = right.compute();  // Compute right in current thread
            long leftResult = left.join();  // Wait for left

            return leftResult + rightResult;
        }
    }

    public static void main(String[] args) {
        long[] numbers = new long[1_000_000];
        ForkJoinPool pool = ForkJoinPool.commonPool();
        long sum = pool.invoke(new ForkJoinDemo(numbers, 0, numbers.length));
    }
}
```
