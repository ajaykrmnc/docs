# Java Interview Questions and Competitive Programming Patterns

## Table of Contents
1. [Core Java Interview Questions](#core-java-questions)
2. [OOP and Design Questions](#oop-design-questions)
3. [Multithreading Interview Questions](#multithreading-questions)
4. [Collections and Data Structures](#collections-questions)
5. [Competitive Programming Templates](#cp-templates)
6. [Common Algorithmic Patterns](#algorithm-patterns)
7. [System Design Considerations](#system-design)
8. [Tricky Questions and Gotchas](#tricky-questions)

---

## Core Java Interview Questions

### Q1: Explain the difference between == and equals()

```java
public class EqualsDemo {
    public static void main(String[] args) {
        // == compares references (memory addresses)
        // equals() compares content (if properly overridden)
        
        String s1 = new String("hello");
        String s2 = new String("hello");
        String s3 = "hello";
        String s4 = "hello";
        
        System.out.println(s1 == s2);        // false (different objects)
        System.out.println(s1.equals(s2));   // true (same content)
        System.out.println(s3 == s4);        // true (String pool)
        System.out.println(s3.equals(s4));   // true
        
        // Integer caching (-128 to 127)
        Integer i1 = 100;
        Integer i2 = 100;
        Integer i3 = 200;
        Integer i4 = 200;
        
        System.out.println(i1 == i2);  // true (cached)
        System.out.println(i3 == i4);  // false (not cached)
    }
}
```

### Q2: What is the contract between hashCode() and equals()?

```java
public class HashCodeEqualsContract {
    /*
     * CONTRACT:
     * 1. If equals() returns true, hashCode() MUST return same value
     * 2. If hashCode() returns different values, equals() MUST return false
     * 3. If hashCode() returns same value, equals() MAY return true or false
     * 4. hashCode() should be consistent for same object during execution
     */
    
    private int id;
    private String name;
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        HashCodeEqualsContract that = (HashCodeEqualsContract) o;
        return id == that.id && Objects.equals(name, that.name);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id, name);  // Use same fields as equals()
    }
}

// What happens if contract is violated?
class BadHashCode {
    private int id;
    
    @Override
    public boolean equals(Object o) {
        if (!(o instanceof BadHashCode)) return false;
        return this.id == ((BadHashCode) o).id;
    }
    
    // Missing hashCode() override!
    // HashMap/HashSet will NOT work correctly
    
    public static void main(String[] args) {
        Set<BadHashCode> set = new HashSet<>();
        BadHashCode b1 = new BadHashCode(1);
        BadHashCode b2 = new BadHashCode(1);
        
        set.add(b1);
        System.out.println(set.contains(b2));  // Might be false!
        // Because b1 and b2 have different hashCodes (Object.hashCode)
    }
}
```

### Q3: Explain String immutability and String Pool

```java
public class StringInternals {
    public static void main(String[] args) {
        // String Pool (in Metaspace since Java 8)
        String s1 = "hello";           // Goes to pool
        String s2 = "hello";           // Same reference from pool
        String s3 = new String("hello"); // New object in heap
        String s4 = s3.intern();       // Returns pooled reference
        
        System.out.println(s1 == s2);  // true
        System.out.println(s1 == s3);  // false
        System.out.println(s1 == s4);  // true
        
        // Why immutable?
        // 1. Security: Strings used in class loading, network, files
        // 2. Thread Safety: No synchronization needed
        // 3. Caching: hashCode can be cached
        // 4. String Pool: Possible only with immutability
        
        // String concatenation optimization
        String result = "a" + "b" + "c";  // Compiled to "abc"
        
        // But in loops, use StringBuilder
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 1000; i++) {
            sb.append(i);
        }
    }
}
```

### Q4: Explain final, finally, and finalize

```java
public class FinalKeywords {
    
    // final variable - constant
    private final int MAX_SIZE = 100;
    
    // final reference - can modify object, not reference
    private final List<String> list = new ArrayList<>();
    
    // final method - cannot be overridden
    public final void cannotOverride() { }
    
    // final class - cannot be extended
    // public final class String { }
    
    // finally - always executes (almost)
    public void finallyDemo() {
        try {
            riskyOperation();
        } catch (Exception e) {
            handleError(e);
        } finally {
            cleanup();  // Always runs
        }
    }
    
    // When finally DOESN'T execute:
    // 1. System.exit() called
    // 2. JVM crashes
    // 3. Infinite loop in try/catch
    // 4. Thread killed
    
    // finalize() - DEPRECATED in Java 9
    @Override
    protected void finalize() throws Throwable {
        // DON'T USE! Unpredictable, slow, not guaranteed
        // Use try-with-resources and Cleaner API instead
    }
}
```

---

## Competitive Programming Templates

### Fast I/O Template

```java
import java.io.*;
import java.util.*;

public class FastIO {
    static BufferedReader br;
    static StringTokenizer st;
    static PrintWriter out;
    
    public static void main(String[] args) throws IOException {
        br = new BufferedReader(new InputStreamReader(System.in));
        out = new PrintWriter(new BufferedOutputStream(System.out));
        
        int t = nextInt();
        while (t-- > 0) {
            solve();
        }
        
        out.flush();
        out.close();
    }
    
    static void solve() throws IOException {
        int n = nextInt();
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) {
            arr[i] = nextInt();
        }
        // Your solution here
        out.println("Answer");
    }
    
    static String next() throws IOException {
        while (st == null || !st.hasMoreTokens())
            st = new StringTokenizer(br.readLine());
        return st.nextToken();
    }
    
    static int nextInt() throws IOException { return Integer.parseInt(next()); }
    static long nextLong() throws IOException { return Long.parseLong(next()); }
    static double nextDouble() throws IOException { return Double.parseDouble(next()); }
    static String nextLine() throws IOException { return br.readLine(); }
}
```

### Common Data Structures for CP

```java
// 1. Priority Queue (Min/Max Heap)
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Collections.reverseOrder());
PriorityQueue<int[]> customHeap = new PriorityQueue<>((a, b) -> a[0] - b[0]);

// 2. TreeMap/TreeSet (Balanced BST)
TreeMap<Integer, Integer> map = new TreeMap<>();
map.floorKey(k);    // Greatest key <= k
map.ceilingKey(k);  // Smallest key >= k
map.lowerKey(k);    // Greatest key < k
map.higherKey(k);   // Smallest key > k

// 3. Deque for sliding window
Deque<Integer> deque = new ArrayDeque<>();
deque.offerFirst(x);   // Add to front
deque.offerLast(x);    // Add to back
deque.pollFirst();     // Remove from front
deque.pollLast();      // Remove from back

// 4. BitSet for space-efficient boolean array
BitSet bitset = new BitSet(1_000_000);
bitset.set(i);          // Set bit i
bitset.get(i);          // Get bit i
bitset.nextSetBit(i);   // Next set bit >= i
```

---

## Common Algorithmic Patterns

### Binary Search Variations

```java
public class BinarySearchPatterns {

    // Find first occurrence
    public int findFirst(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        int result = -1;

        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) {
                result = mid;
                right = mid - 1;  // Continue searching left
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return result;
    }

    // Find last occurrence
    public int findLast(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        int result = -1;

        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) {
                result = mid;
                left = mid + 1;  // Continue searching right
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return result;
    }

    // Binary search on answer (minimize/maximize)
    public int minCapacity(int[] weights, int days) {
        int left = Arrays.stream(weights).max().getAsInt();
        int right = Arrays.stream(weights).sum();

        while (left < right) {
            int mid = left + (right - left) / 2;
            if (canShip(weights, days, mid)) {
                right = mid;  // Try smaller capacity
            } else {
                left = mid + 1;
            }
        }
        return left;
    }

    private boolean canShip(int[] weights, int days, int capacity) {
        int daysNeeded = 1, currentLoad = 0;
        for (int w : weights) {
            if (currentLoad + w > capacity) {
                daysNeeded++;
                currentLoad = 0;
            }
            currentLoad += w;
        }
        return daysNeeded <= days;
    }
}
```

### Union-Find (Disjoint Set)

```java
public class UnionFind {
    private int[] parent;
    private int[] rank;
    private int count;  // Number of components

    public UnionFind(int n) {
        parent = new int[n];
        rank = new int[n];
        count = n;
        for (int i = 0; i < n; i++) {
            parent[i] = i;
        }
    }

    // Find with path compression
    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // Path compression
        }
        return parent[x];
    }

    // Union by rank
    public boolean union(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);

        if (rootX == rootY) return false;

        if (rank[rootX] < rank[rootY]) {
            parent[rootX] = rootY;
        } else if (rank[rootX] > rank[rootY]) {
            parent[rootY] = rootX;
        } else {
            parent[rootY] = rootX;
            rank[rootX]++;
        }
        count--;
        return true;
    }

    public boolean connected(int x, int y) {
        return find(x) == find(y);
    }

    public int getCount() {
        return count;
    }
}
```

### Segment Tree

```java
public class SegmentTree {
    private int[] tree;
    private int n;

    public SegmentTree(int[] arr) {
        n = arr.length;
        tree = new int[4 * n];
        build(arr, 0, 0, n - 1);
    }

    private void build(int[] arr, int node, int start, int end) {
        if (start == end) {
            tree[node] = arr[start];
        } else {
            int mid = (start + end) / 2;
            build(arr, 2 * node + 1, start, mid);
            build(arr, 2 * node + 2, mid + 1, end);
            tree[node] = tree[2 * node + 1] + tree[2 * node + 2];
        }
    }

    public void update(int idx, int val) {
        update(0, 0, n - 1, idx, val);
    }

    private void update(int node, int start, int end, int idx, int val) {
        if (start == end) {
            tree[node] = val;
        } else {
            int mid = (start + end) / 2;
            if (idx <= mid) {
                update(2 * node + 1, start, mid, idx, val);
            } else {
                update(2 * node + 2, mid + 1, end, idx, val);
            }
            tree[node] = tree[2 * node + 1] + tree[2 * node + 2];
        }
    }

    public int query(int left, int right) {
        return query(0, 0, n - 1, left, right);
    }

    private int query(int node, int start, int end, int left, int right) {
        if (right < start || left > end) {
            return 0;  // Out of range
        }
        if (left <= start && end <= right) {
            return tree[node];  // Fully in range
        }
        int mid = (start + end) / 2;
        return query(2 * node + 1, start, mid, left, right) +
               query(2 * node + 2, mid + 1, end, left, right);
    }
}
```

### Trie (Prefix Tree)

```java
public class Trie {
    private TrieNode root;

    public Trie() {
        root = new TrieNode();
    }

    public void insert(String word) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            if (!node.children.containsKey(c)) {
                node.children.put(c, new TrieNode());
            }
            node = node.children.get(c);
        }
        node.isEndOfWord = true;
    }

    public boolean search(String word) {
        TrieNode node = searchPrefix(word);
        return node != null && node.isEndOfWord;
    }

    public boolean startsWith(String prefix) {
        return searchPrefix(prefix) != null;
    }

    private TrieNode searchPrefix(String prefix) {
        TrieNode node = root;
        for (char c : prefix.toCharArray()) {
            if (!node.children.containsKey(c)) {
                return null;
            }
            node = node.children.get(c);
        }
        return node;
    }

    class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;
    }
}
```

---

## OOP and Design Questions

### Q5: Explain Immutable Class Design

```java
public final class ImmutablePerson {  // 1. Class is final
    private final String name;         // 2. All fields are final
    private final int age;
    private final List<String> hobbies;

    public ImmutablePerson(String name, int age, List<String> hobbies) {
        this.name = name;
        this.age = age;
        this.hobbies = List.copyOf(hobbies);  // 3. Defensive copy
    }

    public String getName() { return name; }
    public int getAge() { return age; }

    public List<String> getHobbies() {
        return hobbies;  // Already immutable from List.copyOf
        // Or: return Collections.unmodifiableList(new ArrayList<>(hobbies));
    }

    // 4. No setters
}
```

### Q6: When to use Interface vs Abstract Class?

```java
// Use INTERFACE when:
// - Defining a contract/capability
// - Multiple inheritance needed
// - No shared state required

interface Flyable {
    void fly();
    default void land() {
        System.out.println("Landing...");
    }
}

interface Swimmable {
    void swim();
}

class Duck implements Flyable, Swimmable {
    public void fly() { }
    public void swim() { }
}

// Use ABSTRACT CLASS when:
// - Shared code/state among subclasses
// - Template method pattern
// - Controlled extension (protected members)

abstract class Animal {
    protected String name;  // Shared state

    public Animal(String name) {
        this.name = name;
    }

    // Template method
    public final void eat() {
        find();
        consume();
        digest();
    }

    protected abstract void find();
    protected abstract void consume();

    protected void digest() {
        System.out.println("Digesting...");
    }
}
```

---

## Multithreading Interview Questions

### Q7: Implement a Thread-Safe Singleton

```java
// Best approach: Enum singleton
public enum Singleton {
    INSTANCE;

    public void doSomething() { }
}

// Why enum is best:
// - Thread-safe by JVM
// - Prevents reflection attacks
// - Handles serialization
// - Lazy initialization
```

### Q8: Difference between synchronized and Lock

```java
public class LockVsSynchronized {
    private final Object lock = new Object();
    private final ReentrantLock reentrantLock = new ReentrantLock();

    // synchronized: simpler but less flexible
    public synchronized void method1() { }

    public void method2() {
        synchronized (lock) {
            // critical section
        }
    }

    // Lock: more features
    public void method3() {
        reentrantLock.lock();
        try {
            // critical section
        } finally {
            reentrantLock.unlock();  // Must be in finally!
        }
    }

    // Lock advantages:
    // - tryLock() with timeout
    // - lockInterruptibly()
    // - Multiple conditions
    // - Fair locking option
}
```

### Q9: How to avoid deadlock?

```java
public class DeadlockPrevention {

    private final Object lockA = new Object();
    private final Object lockB = new Object();

    // DEADLOCK-PRONE
    public void method1() {
        synchronized (lockA) {
            synchronized (lockB) {
                // Thread 1: lockA -> lockB
            }
        }
    }

    public void method2() {
        synchronized (lockB) {
            synchronized (lockA) {
                // Thread 2: lockB -> lockA  -- DEADLOCK!
            }
        }
    }

    // SOLUTION 1: Lock ordering
    public void safeMethod1() {
        synchronized (lockA) {  // Always lock A first
            synchronized (lockB) {
            }
        }
    }

    public void safeMethod2() {
        synchronized (lockA) {  // Always lock A first
            synchronized (lockB) {
            }
        }
    }

    // SOLUTION 2: Lock timeout
    private final Lock lock1 = new ReentrantLock();
    private final Lock lock2 = new ReentrantLock();

    public void tryLockApproach() {
        while (true) {
            if (lock1.tryLock()) {
                try {
                    if (lock2.tryLock()) {
                        try {
                            // Critical section
                            return;
                        } finally {
                            lock2.unlock();
                        }
                    }
                } finally {
                    lock1.unlock();
                }
            }
            // Back off and retry
            Thread.sleep(10);
        }
    }
}
```

---

## Tricky Questions and Gotchas

### Q10: What will this code print?

```java
public class TrickyQuestions {

    // Question 1: Integer caching
    public static void question1() {
        Integer a = 127;
        Integer b = 127;
        Integer c = 128;
        Integer d = 128;

        System.out.println(a == b);  // true (cached)
        System.out.println(c == d);  // false (not cached)
    }

    // Question 2: String operations
    public static void question2() {
        String s1 = "hello";
        String s2 = "hel" + "lo";
        String s3 = "hel";
        String s4 = s3 + "lo";

        System.out.println(s1 == s2);  // true (compile-time constant)
        System.out.println(s1 == s4);  // false (runtime concatenation)
        System.out.println(s1 == s4.intern());  // true
    }

    // Question 3: finally return
    public static int question3() {
        try {
            return 1;
        } finally {
            return 2;  // This overwrites the return!
        }
    }
    // Returns 2!

    // Question 4: Short-circuit evaluation
    public static void question4() {
        int i = 0;
        boolean result = true || (++i > 0);
        System.out.println(i);  // 0 (second part not evaluated)
    }

    // Question 5: Array covariance
    public static void question5() {
        Object[] objects = new String[3];
        objects[0] = "Hello";
        objects[1] = 123;  // ArrayStoreException at runtime!
    }
}
```

### Q11: Memory Leaks in Java

```java
public class MemoryLeakExamples {

    // Leak 1: Static collection growing forever
    private static List<Object> cache = new ArrayList<>();

    public void addToCache(Object obj) {
        cache.add(obj);  // Never removed = memory leak
    }

    // Leak 2: Listener not unregistered
    public class EventListener {
        public void register() {
            EventManager.addListener(this);  // Strong reference
        }
        // Missing: unregister() in lifecycle methods
    }

    // Leak 3: ThreadLocal in thread pool
    private static final ThreadLocal<byte[]> BUFFER =
        ThreadLocal.withInitial(() -> new byte[1024 * 1024]);

    public void processWithLeak() {
        byte[] buffer = BUFFER.get();
        // ... use buffer
        // Thread returns to pool, but ThreadLocal remains!
    }

    public void processCorrectly() {
        try {
            byte[] buffer = BUFFER.get();
            // ... use buffer
        } finally {
            BUFFER.remove();  // Clean up!
        }
    }

    // Leak 4: Inner class holding reference to outer
    public class Outer {
        private byte[] data = new byte[10_000_000];

        public Runnable createTask() {
            return new Runnable() {  // Holds reference to Outer
                @Override
                public void run() {
                    // Even if we don't use 'data', Outer can't be GC'd
                }
            };
        }

        // Fix: Use static inner class or lambda
        public Runnable createTaskFixed() {
            return () -> { };  // No implicit reference
        }
    }
}
```

---

## System Design Considerations

### Choosing the Right Data Structure

```
Use Case → Data Structure:
- Fast lookup by key → HashMap (O(1))
- Sorted order needed → TreeMap (O(log n))
- Insertion order → LinkedHashMap
- Thread-safe map → ConcurrentHashMap
- High read, low write → CopyOnWriteArrayList
- Producer-consumer → BlockingQueue
- Priority processing → PriorityQueue
- Unique elements → HashSet/TreeSet
- Range queries → TreeMap (subMap, headMap, tailMap)
- LRU cache → LinkedHashMap with removeEldestEntry()
```

### LRU Cache Implementation

```java
public class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    public LRUCache(int capacity) {
        super(capacity, 0.75f, true);  // accessOrder = true
        this.capacity = capacity;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
}

// Thread-safe version
public class ConcurrentLRUCache<K, V> {
    private final Map<K, V> cache;
    private final ReadWriteLock lock = new ReentrantReadWriteLock();

    public ConcurrentLRUCache(int capacity) {
        this.cache = new LinkedHashMap<K, V>(capacity, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
                return size() > capacity;
            }
        };
    }

    public V get(K key) {
        lock.readLock().lock();
        try {
            return cache.get(key);
        } finally {
            lock.readLock().unlock();
        }
    }

    public void put(K key, V value) {
        lock.writeLock().lock();
        try {
            cache.put(key, value);
        } finally {
            lock.writeLock().unlock();
        }
    }
}
```
