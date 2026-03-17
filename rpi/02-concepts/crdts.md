# CRDTs - Conflict-free Replicated Data Types

> Data structures that can be replicated across nodes and merged without conflicts.

**Previous:** [Consensus Algorithms](./consensus-algorithms.md) | **Next:** [Vector Clocks](./vector-clocks.md)

---

## Why CRDTs?

Traditional approach to sync:
```
Node A: x = 1    Node B: x = 2
         \        /
          \      /
           ▼    ▼
         CONFLICT!
         Which wins?
```

CRDT approach:
```
Node A: counter += 1    Node B: counter += 1
              \              /
               \            /
                ▼          ▼
              Merge: counter = 2
              NO CONFLICT!
```

---

## Types of CRDTs

### State-based CRDTs (CvRDTs)

- Send full state between nodes
- Merge states using a merge function
- Requires more bandwidth

```
Node A state: {a: 1, b: 2}
Node B state: {b: 3, c: 4}
                  │
                  ▼
Merge: {a: 1, b: max(2,3), c: 4} = {a: 1, b: 3, c: 4}
```

### Operation-based CRDTs (CmRDTs)

- Send operations between nodes
- Apply operations in causal order
- Requires reliable broadcast

```
Node A: increment(counter)  →  broadcast to all
Node B: increment(counter)  →  broadcast to all
All nodes apply both operations
```

---

## Common CRDT Types

### 1. G-Counter (Grow-only Counter)

Each node has its own counter; sum gives total.

```
┌─────────────────────────────────────┐
│           G-COUNTER                 │
├─────────────────────────────────────┤
│                                     │
│   Node A: 5                         │
│   Node B: 3                         │
│   Node C: 2                         │
│   ─────────                         │
│   Total:  10                        │
│                                     │
│   Merge: max(local, remote) per node│
└─────────────────────────────────────┘
```

```python
class GCounter:
    def __init__(self, node_id, nodes):
        self.node_id = node_id
        self.counts = {n: 0 for n in nodes}
    
    def increment(self):
        self.counts[self.node_id] += 1
    
    def value(self):
        return sum(self.counts.values())
    
    def merge(self, other):
        for node in self.counts:
            self.counts[node] = max(
                self.counts[node], 
                other.counts.get(node, 0)
            )
```

### 2. PN-Counter (Positive-Negative Counter)

Two G-Counters: one for increments, one for decrements.

```python
class PNCounter:
    def __init__(self, node_id, nodes):
        self.p = GCounter(node_id, nodes)  # Positive
        self.n = GCounter(node_id, nodes)  # Negative
    
    def increment(self):
        self.p.increment()
    
    def decrement(self):
        self.n.increment()
    
    def value(self):
        return self.p.value() - self.n.value()
    
    def merge(self, other):
        self.p.merge(other.p)
        self.n.merge(other.n)
```

### 3. G-Set (Grow-only Set)

Elements can only be added, never removed.

```python
class GSet:
    def __init__(self):
        self.elements = set()
    
    def add(self, element):
        self.elements.add(element)
    
    def lookup(self, element):
        return element in self.elements
    
    def merge(self, other):
        self.elements = self.elements.union(other.elements)
```

### 4. 2P-Set (Two-Phase Set)

Add-only set + remove-only set. Once removed, can't re-add.

```python
class TwoPhaseSet:
    def __init__(self):
        self.added = set()
        self.removed = set()
    
    def add(self, element):
        if element not in self.removed:
            self.added.add(element)
    
    def remove(self, element):
        if element in self.added:
            self.removed.add(element)
    
    def lookup(self, element):
        return element in self.added and element not in self.removed
    
    def merge(self, other):
        self.added = self.added.union(other.added)
        self.removed = self.removed.union(other.removed)
```

### 5. LWW-Register (Last-Writer-Wins Register)

Simple value with timestamp; highest timestamp wins.

```python
class LWWRegister:
    def __init__(self):
        self.value = None
        self.timestamp = 0
    
    def set(self, value, timestamp):
        if timestamp > self.timestamp:
            self.value = value
            self.timestamp = timestamp
    
    def get(self):
        return self.value
    
    def merge(self, other):
        if other.timestamp > self.timestamp:
            self.value = other.value
            self.timestamp = other.timestamp
```

### 6. OR-Set (Observed-Remove Set)

Add and remove elements multiple times. Uses unique tags.

```python
class ORSet:
    def __init__(self, node_id):
        self.node_id = node_id
        self.elements = {}  # element -> set of (node, counter)
        self.counter = 0
    
    def add(self, element):
        self.counter += 1
        tag = (self.node_id, self.counter)
        if element not in self.elements:
            self.elements[element] = set()
        self.elements[element].add(tag)
    
    def remove(self, element):
        if element in self.elements:
            del self.elements[element]
    
    def lookup(self, element):
        return element in self.elements and len(self.elements[element]) > 0
    
    def merge(self, other):
        # Union of all elements and their tags
        for elem, tags in other.elements.items():
            if elem not in self.elements:
                self.elements[elem] = set()
            self.elements[elem] = self.elements[elem].union(tags)
```

---

## For Your File Sync

### Using CRDTs for File Metadata

```
┌─────────────────────────────────────────────────────────┐
│               FILE SYNC WITH CRDTs                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  File List:     OR-Set  (add/remove files)             │
│  File Content:  LWW-Register (last edit wins)          │
│  Edit Count:    G-Counter (track changes)              │
│  Deleted Files: 2P-Set (no resurrection)               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

See implementation: [CRDT Implementation Guide](../04-implementation/crdt-implementation.md)

---

## Practical Exercise

1. Implement G-Counter on all 3 nodes
2. Each node increments locally
3. Sync states periodically
4. Verify all nodes converge to same value

---

**Next:** [Vector Clocks →](./vector-clocks.md)

