# Java Collections Framework - Deep Internals

## Table of Contents
1. [Collections Hierarchy](#collections-hierarchy)
2. [ArrayList Internals](#arraylist-internals)
3. [LinkedList Internals](#linkedlist-internals)
4. [HashMap Internals](#hashmap-internals)
5. [TreeMap and Red-Black Trees](#treemap-internals)
6. [ConcurrentHashMap Internals](#concurrenthashmap-internals)
7. [HashSet Internals](#hashset-internals)
8. [PriorityQueue and Heaps](#priorityqueue-internals)
9. [Interview Questions](#interview-questions)

---

## Collections Hierarchy

```
                                    Iterable<E>
                                        │
                                    Collection<E>
                         ┌──────────────┼──────────────┐
                         │              │              │
                      List<E>        Set<E>        Queue<E>
                         │              │              │
              ┌──────────┼────────┐    │        ┌─────┴─────┐
              │          │        │    │        │           │
          ArrayList  LinkedList Vector│      Deque<E>  PriorityQueue
              │          │        │    │        │
              │          │    Stack ┌──┴───┐    │
              │          │         │       │    │
                              HashSet TreeSet ArrayDeque
                                 │       │
                           LinkedHashSet  │
                                         │
                                    NavigableSet<E>

                                    Map<K,V>
                         ┌──────────────┼──────────────┐
                         │              │              │
                     HashMap       TreeMap      LinkedHashMap
                         │              │
                   WeakHashMap    NavigableMap<K,V>
                         │
                  IdentityHashMap
                         │
                 ConcurrentHashMap
```

---

## ArrayList Internals

### Internal Structure

ArrayList is backed by a **dynamic array** (Object[]).

```java
public class ArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, java.io.Serializable {
    
    // The array buffer where elements are stored
    transient Object[] elementData;  // non-private for nested class access
    
    // The size of the ArrayList (number of elements)
    private int size;
    
    // Default initial capacity
    private static final int DEFAULT_CAPACITY = 10;
    
    // Shared empty array for empty instances
    private static final Object[] EMPTY_ELEMENTDATA = {};
    
    // Shared empty array for default sized empty instances
    private static final Object[] DEFAULTCAPACITY_EMPTY_ELEMENTDATA = {};
}
```

### Growth Strategy (Amortized O(1) Add)

```java
// When capacity is exceeded, ArrayList grows by 50%
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    
    // New capacity = old capacity + old capacity / 2 (1.5x growth)
    int newCapacity = oldCapacity + (oldCapacity >> 1);
    
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    
    if (newCapacity - MAX_ARRAY_SIZE > 0)
        newCapacity = hugeCapacity(minCapacity);
    
    // Copy elements to new array
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

### Why 1.5x Growth Factor?

| Growth Factor | Memory Waste | Reallocations for N elements |
|--------------|--------------|------------------------------|
| 2x (doubling) | Up to 50% | O(log N) |
| 1.5x | Up to 33% | O(log N) but more copies |
| 1.25x | Up to 20% | More frequent copies |

**Trade-off**: 1.5x balances memory efficiency with copy overhead.

### Time Complexity Analysis

| Operation | Average Case | Worst Case | Notes |
|-----------|--------------|------------|-------|
| get(i) | O(1) | O(1) | Direct array access |
| add(E) | O(1)* | O(n) | Amortized; worst when resize |
| add(i, E) | O(n) | O(n) | Shift elements right |
| remove(i) | O(n) | O(n) | Shift elements left |
| contains() | O(n) | O(n) | Linear search |
| indexOf() | O(n) | O(n) | Linear search |

### Memory Layout

```
ArrayList object:
┌─────────────────────────────────┐
│ Object Header (12-16 bytes)    │
├─────────────────────────────────┤
│ elementData reference (4-8 B)  │ ──────►  Object[] array
├─────────────────────────────────┤          ┌────┬────┬────┬────┬────┐
│ size (4 bytes)                 │          │ E0 │ E1 │ E2 │null│null│
├─────────────────────────────────┤          └────┴────┴────┴────┴────┘
│ modCount (4 bytes)             │          (capacity may > size)
└─────────────────────────────────┘
```

---

## LinkedList Internals

### Internal Structure (Doubly Linked List)

```java
public class LinkedList<E> extends AbstractSequentialList<E>
        implements List<E>, Deque<E>, Cloneable, java.io.Serializable {
    
    transient int size = 0;
    transient Node<E> first;  // Pointer to first node
    transient Node<E> last;   // Pointer to last node
    
    // Node inner class
    private static class Node<E> {
        E item;
        Node<E> next;
        Node<E> prev;
        
        Node(Node<E> prev, E element, Node<E> next) {
            this.item = element;
            this.next = next;
            this.prev = prev;
        }
    }
}
```

### Memory Layout

```
LinkedList object:
┌──────────────────────┐
│ Object Header        │
├──────────────────────┤
│ size                 │
├──────────────────────┤
│ first ───────────────┼──►┌──────────┐   ┌──────────┐   ┌──────────┐
├──────────────────────┤   │ prev=null│◄──│ prev     │◄──│ prev     │
│ last ────────────────┼──►│ item: E0 │   │ item: E1 │   │ item: E2 │
└──────────────────────┘   │ next ────┼──►│ next ────┼──►│ next=null│
                           └──────────┘   └──────────┘   └──────────┘
```

### Time Complexity Comparison

| Operation | ArrayList | LinkedList |
|-----------|-----------|------------|
| get(i) | O(1) | O(n) |
| add(E) at end | O(1)* | O(1) |
| add(i, E) | O(n) | O(n)† |
| remove(i) | O(n) | O(n)† |
| contains() | O(n) | O(n) |
| Iterator.remove() | O(n) | O(1) |

*Amortized †Traversal + O(1) operation

---

## HashMap Internals

### Structure (Java 8+)

```java
public class HashMap<K,V> extends AbstractMap<K,V>
        implements Map<K,V>, Cloneable, Serializable {

    // The table, resized as necessary. Length MUST be power of two.
    transient Node<K,V>[] table;

    // Number of key-value mappings
    transient int size;

    // Threshold for resizing (capacity * loadFactor)
    int threshold;

    // Load factor (default 0.75)
    final float loadFactor;

    // Modification count for fail-fast iterators
    transient int modCount;

    // Constants
    static final int DEFAULT_INITIAL_CAPACITY = 16;  // Must be power of 2
    static final float DEFAULT_LOAD_FACTOR = 0.75f;
    static final int TREEIFY_THRESHOLD = 8;   // Convert to tree
    static final int UNTREEIFY_THRESHOLD = 6;  // Convert back to list
    static final int MIN_TREEIFY_CAPACITY = 64;

    // Node structure (linked list node)
    static class Node<K,V> implements Map.Entry<K,V> {
        final int hash;
        final K key;
        V value;
        Node<K,V> next;
    }

    // TreeNode structure (red-black tree node)
    static final class TreeNode<K,V> extends LinkedHashMap.Entry<K,V> {
        TreeNode<K,V> parent;
        TreeNode<K,V> left;
        TreeNode<K,V> right;
        TreeNode<K,V> prev;
        boolean red;
    }
}
```

### HashMap Visual Layout (Java 8+)

```
HashMap Internal Structure:
┌─────────────────────────────────────────────────────────────────────────┐
│                              HashMap                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  table[] (Node array, length = power of 2)                              │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                     │
│  │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │ ...                 │
│  └──┬──┴──┬──┴─────┴─────┴──┬──┴─────┴──┬──┴─────┘                     │
│     │     │                 │           │                               │
│     ▼     ▼                 ▼           ▼                               │
│   ┌───┐ ┌───┐             ┌───┐       ┌───┐                            │
│   │K:A│ │K:B│             │K:E│       │K:H│                            │
│   │V:1│ │V:2│             │V:5│       │V:8│                            │
│   └─┬─┘ └───┘             └─┬─┘       └─┬─┘                            │
│     │                       │           │                               │
│     ▼                       ▼           ▼                               │
│   ┌───┐                   ┌───┐    ┌────────────┐                       │
│   │K:C│                   │K:F│    │ TreeNode   │ (if chain >= 8)      │
│   │V:3│                   │V:6│    │ Red-Black  │                       │
│   └─┬─┘                   └─┬─┘    │   Tree     │                       │
│     │                       │      └────────────┘                       │
│     ▼                       ▼                                           │
│   ┌───┐                   ┌───┐                                        │
│   │K:D│                   │K:G│                                        │
│   │V:4│                   │V:7│                                        │
│   └───┘                   └───┘                                        │
│                                                                          │
│  Linked List (hash collision) → Red-Black Tree (when chain ≥ 8)        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Hash Function and Index Calculation

```java
// How HashMap computes bucket index

static final int hash(Object key) {
    int h;
    // XOR high bits with low bits (spread hash codes)
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}

// Bucket index calculation
// Using bitwise AND (much faster than modulo)
int index = (n - 1) & hash;  // where n = table.length (power of 2)

// Example:
// hash = 0b10110101_11001010_00110011_11110000
// n = 16, n-1 = 15 = 0b00001111
// index = hash & 0b00001111 = 0b00000000 = 0 (uses only last 4 bits)

// Why XOR with h >>> 16?
// Without: only low bits determine bucket (many collisions)
// With XOR: high bits influence low bits (better distribution)
```

### Put Operation Internals

```java
// Simplified put() implementation
final V putVal(int hash, K key, V value, boolean onlyIfAbsent, boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;

    // 1. Initialize table if empty
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;

    // 2. If bucket is empty, create new node
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);
    else {
        Node<K,V> e; K k;

        // 3. Check if first node matches key
        if (p.hash == hash && ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;

        // 4. If tree node, use tree insertion
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);

        // 5. Traverse linked list
        else {
            for (int binCount = 0; ; ++binCount) {
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);
                    // Convert to tree if threshold reached
                    if (binCount >= TREEIFY_THRESHOLD - 1)
                        treeifyBin(tab, hash);
                    break;
                }
                if (e.hash == hash && ((k = e.key) == key || (key != null && key.equals(k))))
                    break;
                p = e;
            }
        }

        // 6. Update existing value
        if (e != null) {
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            return oldValue;
        }
    }

    // 7. Check if resize needed
    if (++size > threshold)
        resize();
    return null;
}
```

### Resize Operation

```java
// HashMap doubles in size when size > capacity * loadFactor

final Node<K,V>[] resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;

    // Double capacity
    if (oldCap > 0) {
        newCap = oldCap << 1;  // Double
        newThr = oldThr << 1;
    }

    // Rehash all entries
    Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
    table = newTab;

    // Clever rehashing: entry goes to same index OR index + oldCap
    // Based on one bit: (hash & oldCap) == 0 ? same : same + oldCap
    for (int j = 0; j < oldCap; ++j) {
        Node<K,V> e;
        if ((e = oldTab[j]) != null) {
            oldTab[j] = null;
            if (e.next == null)
                newTab[e.hash & (newCap - 1)] = e;
            else {
                // Split bucket into two lists: lo (same index), hi (index + oldCap)
                Node<K,V> loHead = null, loTail = null;
                Node<K,V> hiHead = null, hiTail = null;
                Node<K,V> next;
                do {
                    next = e.next;
                    if ((e.hash & oldCap) == 0) {
                        // Stays in same bucket
                        if (loTail == null) loHead = e;
                        else loTail.next = e;
                        loTail = e;
                    } else {
                        // Moves to bucket + oldCap
                        if (hiTail == null) hiHead = e;
                        else hiTail.next = e;
                        hiTail = e;
                    }
                } while ((e = next) != null);

                if (loTail != null) {
                    loTail.next = null;
                    newTab[j] = loHead;
                }
                if (hiTail != null) {
                    hiTail.next = null;
                    newTab[j + oldCap] = hiHead;
                }
            }
        }
    }
    return newTab;
}
```

---

## TreeMap Internals

### Red-Black Tree Properties

```
Red-Black Tree Rules:
1. Every node is either RED or BLACK
2. Root is always BLACK
3. Every leaf (NIL) is BLACK
4. If a node is RED, both children are BLACK
5. Every path from root to leaves has same number of BLACK nodes

Visual Example:
                    ┌───────────────┐
                    │     50 (B)    │  ← Root always BLACK
                    └───────┬───────┘
              ┌─────────────┴─────────────┐
              ▼                           ▼
        ┌───────────┐               ┌───────────┐
        │   25 (R)  │               │   75 (R)  │
        └─────┬─────┘               └─────┬─────┘
        ┌─────┴─────┐               ┌─────┴─────┐
        ▼           ▼               ▼           ▼
    ┌───────┐   ┌───────┐       ┌───────┐   ┌───────┐
    │10 (B) │   │30 (B) │       │60 (B) │   │90 (B) │
    └───────┘   └───────┘       └───────┘   └───────┘

Black Height: Every path has exactly 2 black nodes (excluding root)
Height: At most 2*log(n+1) → O(log n) operations guaranteed
```

### TreeMap Implementation

```java
public class TreeMap<K,V> extends AbstractMap<K,V>
        implements NavigableMap<K,V>, Cloneable, java.io.Serializable {

    private final Comparator<? super K> comparator;
    private transient Entry<K,V> root;
    private transient int size = 0;

    static final class Entry<K,V> implements Map.Entry<K,V> {
        K key;
        V value;
        Entry<K,V> left;
        Entry<K,V> right;
        Entry<K,V> parent;
        boolean color = BLACK;  // New nodes start as BLACK
    }

    // All operations O(log n):
    // get(), put(), remove(), containsKey()
    // firstKey(), lastKey(), higherKey(), lowerKey()
    // subMap(), headMap(), tailMap()
}
```

---

## ConcurrentHashMap Internals

### Java 8+ Implementation (Lock Striping → CAS + synchronized)

```
ConcurrentHashMap Structure (Java 8+):
┌─────────────────────────────────────────────────────────────────────────┐
│                          ConcurrentHashMap                               │
├─────────────────────────────────────────────────────────────────────────┤
│  Node[] table (volatile)                                                 │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                     │
│  │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │                     │
│  └──┬──┴──┬──┴─────┴──┬──┴─────┴─────┴─────┴─────┘                     │
│     │     │           │                                                  │
│     │     │ CAS for   │ synchronized on                                 │
│     │     │ empty     │ first node                                      │
│     │     │ bucket    │ for insertion                                   │
│     │     │           │                                                  │
│     ▼     ▼           ▼                                                 │
│   ┌───┐ ┌───┐       ┌───┐──►┌───┐──►┌───┐                              │
│   │K:A│ │K:B│       │K:E│   │K:F│   │K:G│                              │
│   └───┘ └───┘       └───┘   └───┘   └───┘                              │
│                                                                          │
│  No Segment locks! Uses:                                                │
│  1. CAS for empty bucket insertion                                      │
│  2. synchronized on first node of bucket                                │
│  3. volatile reads for thread visibility                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Operations

```java
// put() - Uses CAS for empty bucket, synchronized for non-empty
final V putVal(K key, V value, boolean onlyIfAbsent) {
    int hash = spread(key.hashCode());
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();  // CAS-based lazy init
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            // CAS to insert into empty bucket
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break;
        }
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);  // Help with resize
        else {
            // synchronized on first node only
            synchronized (f) {
                // Insert into chain/tree
            }
        }
    }
}

// get() - Lock-free! Uses volatile reads
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {  // volatile read
        // Traverse without locking
    }
    return null;
}
```

---

## PriorityQueue and Heaps

### Binary Heap Implementation

```java
public class PriorityQueue<E> extends AbstractQueue<E> {
    transient Object[] queue;  // Binary heap stored in array
    private int size = 0;
    private final Comparator<? super E> comparator;

    // Parent/child relationships (0-indexed)
    // Parent of node i: (i - 1) / 2
    // Left child of i:  2 * i + 1
    // Right child of i: 2 * i + 2
}
```

### Heap Visual Representation

```
Binary Min-Heap:
                    ┌───┐
                    │ 1 │  ← Root (minimum)
                    └─┬─┘
              ┌───────┴───────┐
              ▼               ▼
            ┌───┐           ┌───┐
            │ 3 │           │ 2 │
            └─┬─┘           └─┬─┘
         ┌───┴───┐       ┌───┴───┐
         ▼       ▼       ▼       ▼
       ┌───┐   ┌───┐   ┌───┐   ┌───┐
       │ 5 │   │ 4 │   │ 7 │   │ 6 │
       └───┘   └───┘   └───┘   └───┘

Array representation:
Index:    0    1    2    3    4    5    6
Value:  [ 1 ][ 3 ][ 2 ][ 5 ][ 4 ][ 7 ][ 6 ]

Operations:
- offer(E): O(log n) - Add at end, sift up
- poll():   O(log n) - Remove root, move last to root, sift down
- peek():   O(1)     - Return root
```

---

## Interview Questions

### Q1: Why does HashMap require capacity to be power of 2?

**Answer**: For fast index calculation using bitwise AND:
- `index = hash & (capacity - 1)` is equivalent to `hash % capacity`
- Bitwise AND is much faster than modulo division
- Only works when capacity is power of 2

### Q2: HashMap vs TreeMap vs LinkedHashMap?

| Feature | HashMap | TreeMap | LinkedHashMap |
|---------|---------|---------|---------------|
| Order | None | Sorted by keys | Insertion order |
| Get/Put | O(1) | O(log n) | O(1) |
| Null keys | 1 allowed | Not allowed | 1 allowed |
| Iteration | Unpredictable | Sorted | Predictable |
| Implementation | Hash table | Red-Black Tree | Hash + Linked List |

### Q3: When does ArrayList.add() become O(n)?

**Answer**: When the internal array needs to be resized (capacity exceeded). This involves creating a new array 1.5x larger and copying all elements. However, this is rare (amortized O(1)).

### Q4: How does ConcurrentHashMap achieve thread-safety without blocking reads?

**Answer**:
1. Volatile reads of table array
2. Volatile writes when updating nodes
3. CAS for empty bucket insertion
4. Fine-grained synchronization only on bucket's first node
5. Safe publication through volatile variables


