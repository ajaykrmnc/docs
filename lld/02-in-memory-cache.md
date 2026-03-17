# Design an In-Memory Cache with LRU Eviction
**Difficulty:** Hard | **Companies:** Google, Amazon, Redis, Meta

---

## Problem Statement

Design a thread-safe, high-performance in-memory cache that supports multiple eviction policies (LRU, LFU, TTL-based) with O(1) get/put operations.

---

## Requirements

### Functional Requirements
1. Get and Put operations with O(1) time complexity
2. Support multiple eviction policies: LRU, LFU, TTL-based
3. Maximum capacity with automatic eviction
4. Support for cache statistics (hits, misses, evictions)
5. Write-through and write-back policies for persistence

### Non-Functional Requirements
1. Thread-safe with minimal lock contention
2. High throughput under concurrent access
3. Memory efficient
4. Support for different key-value types (generic)

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cache<K, V>                                │
├─────────────────────────────────────────────────────────────────┤
│ - store: ConcurrentHashMap<K, CacheEntry<V>>                    │
│ - evictionPolicy: EvictionPolicy<K>                             │
│ - capacity: int                                                 │
│ - statistics: CacheStatistics                                   │
│ - writePolicy: WritePolicy<K, V>                                │
├─────────────────────────────────────────────────────────────────┤
│ + get(key: K): Optional<V>                                      │
│ + put(key: K, value: V): void                                   │
│ + put(key: K, value: V, ttl: Duration): void                    │
│ + remove(key: K): boolean                                       │
│ + clear(): void                                                 │
│ + size(): int                                                   │
│ + getStatistics(): CacheStatistics                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      CacheEntry<V>                              │
├─────────────────────────────────────────────────────────────────┤
│ - value: V                                                      │
│ - createdAt: Instant                                            │
│ - lastAccessedAt: Instant                                       │
│ - accessCount: AtomicLong                                       │
│ - expiresAt: Instant                                            │
├─────────────────────────────────────────────────────────────────┤
│ + isExpired(): boolean                                          │
│ + recordAccess(): void                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  <<interface>>                                  │
│                  EvictionPolicy<K>                              │
├─────────────────────────────────────────────────────────────────┤
│ + onAccess(key: K): void                                        │
│ + onInsert(key: K): void                                        │
│ + evict(): K                                                    │
│ + remove(key: K): void                                          │
└─────────────────────────────────────────────────────────────────┘
         △
         │
   ┌─────┴─────┬────────────────┐
   │           │                │
┌──┴───┐  ┌────┴────┐    ┌──────┴──────┐
│ LRU  │  │   LFU   │    │     TTL     │
│Policy│  │  Policy │    │   Policy    │
└──────┘  └─────────┘    └─────────────┘
```

---

## Class Implementations

### 1. CacheEntry
```java
public class CacheEntry<V> {
    private final V value;
    private final Instant createdAt;
    private volatile Instant lastAccessedAt;
    private final AtomicLong accessCount;
    private final Instant expiresAt;  // null means no expiration
    
    public CacheEntry(V value, Duration ttl) {
        this.value = value;
        this.createdAt = Instant.now();
        this.lastAccessedAt = this.createdAt;
        this.accessCount = new AtomicLong(1);
        this.expiresAt = ttl != null ? createdAt.plus(ttl) : null;
    }
    
    public boolean isExpired() {
        return expiresAt != null && Instant.now().isAfter(expiresAt);
    }
    
    public void recordAccess() {
        this.lastAccessedAt = Instant.now();
        this.accessCount.incrementAndGet();
    }
    
    public V getValue() { return value; }
    public Instant getLastAccessedAt() { return lastAccessedAt; }
    public long getAccessCount() { return accessCount.get(); }
}
```

### 2. LRU Eviction Policy (using Doubly Linked List + HashMap)
```java
public class LRUEvictionPolicy<K> implements EvictionPolicy<K> {
    private final Map<K, Node<K>> nodeMap;
    private final DoublyLinkedList<K> accessOrder;
    private final ReentrantLock lock;
    
    public LRUEvictionPolicy() {
        this.nodeMap = new HashMap<>();
        this.accessOrder = new DoublyLinkedList<>();
        this.lock = new ReentrantLock();
    }
    
    @Override
    public void onAccess(K key) {
        lock.lock();
        try {
            Node<K> node = nodeMap.get(key);
            if (node != null) {
                accessOrder.moveToFront(node);
            }
        } finally {
            lock.unlock();
        }
    }
    
    @Override
    public void onInsert(K key) {
        lock.lock();
        try {
            Node<K> node = new Node<>(key);
            nodeMap.put(key, node);
            accessOrder.addToFront(node);
        } finally {
            lock.unlock();
        }
    }
    
    @Override
    public K evict() {
        lock.lock();
        try {
            Node<K> lru = accessOrder.removeLast();
            if (lru != null) {
                nodeMap.remove(lru.key);
                return lru.key;
            }
            return null;
        } finally {
            lock.unlock();
        }
    }
    
    @Override
    public void remove(K key) {
        lock.lock();
        try {
            Node<K> node = nodeMap.remove(key);
            if (node != null) {
                accessOrder.remove(node);
            }
        } finally {
            lock.unlock();
        }
    }
}
```

### 3. Doubly Linked List Helper
```java
class DoublyLinkedList<K> {
    private Node<K> head;
    private Node<K> tail;
    
    public DoublyLinkedList() {
        head = new Node<>(null);  // dummy head
        tail = new Node<>(null);  // dummy tail
        head.next = tail;
        tail.prev = head;
    }
    
    public void addToFront(Node<K> node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }
    
    public void remove(Node<K> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
    
    public void moveToFront(Node<K> node) {
        remove(node);
        addToFront(node);
    }
    
    public Node<K> removeLast() {
        if (tail.prev == head) return null;
        Node<K> last = tail.prev;
        remove(last);
        return last;
    }
}

class Node<K> {
    K key;
    Node<K> prev, next;
    Node(K key) { this.key = key; }
}
```

