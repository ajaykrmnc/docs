# Vector Clocks

> Tracking causality and ordering events in distributed systems without a global clock.

**Previous:** [CRDTs](./crdts.md) | **Next:** [Gossip Protocol](./gossip-protocol.md)

---

## The Problem: No Global Time

In distributed systems, we can't rely on wall clocks:

```
Node A clock: 10:00:00.000
Node B clock: 10:00:00.500  ← 500ms drift!
Node C clock: 09:59:59.800  ← Behind!

If Node C writes at its 10:00:00,
which happened "first" - A, B, or C?
```

---

## Lamport Clocks (Simple Version)

Each event gets a logical timestamp:

```
Rules:
1. Before each event: counter++
2. Send: include counter in message
3. Receive: counter = max(local, received) + 1

Node A: ─[1]──[2]──────[3]──────────[6]──►
              │send                  ▲recv
              │                      │
Node B: ─[1]──▼[3]──[4]──[5]send────────►
                          │
                          │
Node C: ─[1]──[2]──[3]────▼[6]──[7]─────►
```

**Limitation**: Can't determine if events are concurrent or causally related.

---

## Vector Clocks (Full Solution)

Each node maintains a vector of counters, one per node.

```
┌─────────────────────────────────────────────────────────┐
│                    VECTOR CLOCK                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   3 nodes: A, B, C                                      │
│   Vector: [A_count, B_count, C_count]                   │
│                                                         │
│   Node A's view: [3, 0, 0]  ← A did 3 events           │
│   Node B's view: [1, 2, 0]  ← B saw A's 1, did 2       │
│   Node C's view: [1, 2, 3]  ← C saw A's 1, B's 2       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Rules

1. **Initial**: All zeros `[0, 0, 0]`
2. **Local event**: Increment own position
3. **Send**: Increment own position, attach vector
4. **Receive**: Merge vectors (element-wise max), then increment own

### Example

```
Node A [1,0,0]    Node B [0,0,0]    Node C [0,0,0]
    │                 │                 │
    │ (local event)   │                 │
    ▼                 ▼                 │
[2,0,0]           [0,1,0]              │
    │                 │                 │
    │ ──send──────────►                 │
    │                 │                 │
    │             merge:                │
    │             max([0,1,0],[2,0,0])  │
    │             = [2,1,0] + inc B    │
    │                 │                 │
    │             [2,2,0]               │
    │                 │                 │
    │                 │ ──send──────────►
    │                 │                 │
    │                 │             merge:
    │                 │             [2,2,1]
    │                 │                 │
```

---

## Comparing Vector Clocks

### Ordering Rules

```python
def compare(vc1, vc2):
    """
    Returns:
      'before'     if vc1 < vc2 (vc1 happened before vc2)
      'after'      if vc1 > vc2 (vc1 happened after vc2)
      'concurrent' if neither (vc1 || vc2)
    """
    less = False
    greater = False
    
    for i in range(len(vc1)):
        if vc1[i] < vc2[i]:
            less = True
        elif vc1[i] > vc2[i]:
            greater = True
    
    if less and not greater:
        return 'before'
    elif greater and not less:
        return 'after'
    else:
        return 'concurrent'
```

### Examples

```
[1, 2, 0] vs [2, 2, 0]  →  'before'   (first happened before second)
[2, 3, 1] vs [1, 2, 0]  →  'after'    (first happened after second)
[1, 2, 0] vs [0, 1, 3]  →  'concurrent' (neither caused the other)
```

---

## Implementation

```python
class VectorClock:
    def __init__(self, node_id, num_nodes):
        self.node_id = node_id
        self.clock = [0] * num_nodes
    
    def increment(self):
        """Call before any local event or send."""
        self.clock[self.node_id] += 1
        return self.clock.copy()
    
    def receive(self, other_clock):
        """Call when receiving a message."""
        # Merge: element-wise maximum
        for i in range(len(self.clock)):
            self.clock[i] = max(self.clock[i], other_clock[i])
        # Then increment own
        self.clock[self.node_id] += 1
        return self.clock.copy()
    
    def compare(self, other_clock):
        """Compare this clock to another."""
        less = any(self.clock[i] < other_clock[i] 
                   for i in range(len(self.clock)))
        greater = any(self.clock[i] > other_clock[i] 
                      for i in range(len(self.clock)))
        
        if less and not greater:
            return 'before'
        elif greater and not less:
            return 'after'
        else:
            return 'concurrent'
    
    def __repr__(self):
        return f"VC{self.clock}"
```

---

## Use Cases

### 1. Conflict Detection

```python
# File sync scenario
file_a_vc = [3, 1, 0]  # Last edit on Node A
file_b_vc = [2, 0, 2]  # Last edit on Node C

result = compare(file_a_vc, file_b_vc)
# result = 'concurrent' → CONFLICT! Both edited independently
```

### 2. Causal Ordering

```python
# Ensure messages are applied in causal order
messages = [
    {'vc': [1, 0, 0], 'data': 'create file'},
    {'vc': [2, 0, 0], 'data': 'edit file'},    # depends on create
    {'vc': [2, 1, 0], 'data': 'rename file'},  # depends on edit
]

# Must apply in order: create → edit → rename
```

### 3. Detecting Missing Updates

```python
local_vc  = [2, 3, 1]
remote_vc = [2, 5, 1]  # Remote has more from Node B

# We're missing 2 updates from Node B!
missing = remote_vc[1] - local_vc[1]  # = 2
```

---

## For Your Setup

```
┌─────────────────────────────────────────────────────────┐
│              VECTOR CLOCKS IN YOUR LAB                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Node Mapping:                                         │
│     Position 0: RPi                                     │
│     Position 1: Office Laptop                           │
│     Position 2: Personal Laptop                         │
│                                                         │
│   Example file metadata:                                │
│     {                                                   │
│       "path": "/docs/notes.txt",                        │
│       "vector_clock": [5, 3, 2],                        │
│       "content_hash": "abc123..."                       │
│     }                                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Comparison with Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Wall clock** | Simple | Clock drift, NTP issues |
| **Lamport** | Single counter | Can't detect concurrency |
| **Vector clock** | Full causality | Size grows with nodes |
| **Version vectors** | Like VC for replicas | Same trade-offs |
| **Hybrid logical** | Best of both | More complex |

---

**Next:** [Gossip Protocol →](./gossip-protocol.md)

