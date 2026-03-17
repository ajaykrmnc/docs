# Gossip Protocol

> Epidemic-style information spreading across distributed nodes.

**Previous:** [Vector Clocks](./vector-clocks.md) | **Next:** [Project 1: Syncthing](../03-projects/project-1-syncthing.md)

---

## How Gossip Works

Like rumors spreading in a social network:

```
Time 0: Only Node A has information
┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
│ A │   │ B │   │ C │   │ D │   │ E │
│ ★ │   │   │   │   │   │   │   │   │
└───┘   └───┘   └───┘   └───┘   └───┘

Time 1: A gossips to B (random selection)
┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
│ A │──►│ B │   │ C │   │ D │   │ E │
│ ★ │   │ ★ │   │   │   │   │   │   │
└───┘   └───┘   └───┘   └───┘   └───┘

Time 2: A→D, B→C (each infected node gossips)
┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
│ A │   │ B │──►│ C │   │ D │   │ E │
│ ★ │──────────────────►│ ★ │   │   │
└───┘   └───┘   │ ★ │   └───┘   └───┘
                └───┘

Time 3: Everyone knows (exponential spread)
┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
│ ★ │   │ ★ │   │ ★ │   │ ★ │   │ ★ │
└───┘   └───┘   └───┘   └───┘   └───┘
```

---

## Key Properties

| Property | Description |
|----------|-------------|
| **Scalable** | O(log N) rounds to reach all nodes |
| **Fault-tolerant** | No single point of failure |
| **Eventually consistent** | All nodes converge |
| **Probabilistic** | Guarantees are probabilistic, not absolute |
| **Simple** | Easy to implement |

---

## Gossip Styles

### 1. Push Gossip

Node sends its data to randomly selected peers.

```python
def push_gossip(self, data):
    peers = random.sample(self.known_nodes, k=self.fanout)
    for peer in peers:
        self.send(peer, data)
```

### 2. Pull Gossip

Node requests data from randomly selected peers.

```python
def pull_gossip(self):
    peers = random.sample(self.known_nodes, k=self.fanout)
    for peer in peers:
        data = self.request(peer)
        self.merge(data)
```

### 3. Push-Pull Gossip

Combination: send your data, receive theirs.

```python
def push_pull_gossip(self):
    peers = random.sample(self.known_nodes, k=self.fanout)
    for peer in peers:
        their_data = self.exchange(peer, my_data=self.data)
        self.merge(their_data)
```

---

## Anti-Entropy Protocol

Full synchronization between nodes:

```
┌─────────────────────────────────────────────────────────┐
│                  ANTI-ENTROPY SYNC                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Node A                          Node B                 │
│  ─────                           ─────                  │
│  {key1: v1}                      {key2: v2}             │
│      │                               │                  │
│      │ ──── send digest ───────────► │                  │
│      │      [key1: hash1]            │                  │
│      │                               │                  │
│      │ ◄─── need key1, here's key2 ──│                  │
│      │      {key2: v2}               │                  │
│      │                               │                  │
│      │ ──── here's key1 ───────────► │                  │
│      │      {key1: v1}               │                  │
│      │                               │                  │
│  {key1: v1,                      {key1: v1,             │
│   key2: v2}                       key2: v2}             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation

```python
import random
import hashlib
import threading
import time

class GossipNode:
    def __init__(self, node_id, peers, fanout=2, interval=1.0):
        self.node_id = node_id
        self.peers = peers  # List of peer addresses
        self.fanout = fanout  # Number of peers to contact each round
        self.interval = interval  # Gossip interval in seconds
        
        self.data = {}  # Key-value store
        self.versions = {}  # Version vectors for each key
        self.running = False
    
    def start(self):
        """Start the gossip background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._gossip_loop)
        self.thread.start()
    
    def stop(self):
        """Stop the gossip background thread."""
        self.running = False
        self.thread.join()
    
    def _gossip_loop(self):
        """Main gossip loop."""
        while self.running:
            self._do_gossip()
            time.sleep(self.interval)
    
    def _do_gossip(self):
        """Perform one round of gossip."""
        if not self.peers:
            return
        
        # Select random peers
        selected = random.sample(
            self.peers, 
            min(self.fanout, len(self.peers))
        )
        
        for peer in selected:
            self._exchange_with(peer)
    
    def _exchange_with(self, peer):
        """Exchange data with a peer."""
        # Send our digest
        digest = self._create_digest()
        
        # In real impl, this would be network call
        peer_digest = peer.receive_digest(digest)
        
        # Determine what to send/request
        to_send = []
        for key, version in peer_digest.items():
            if key in self.data:
                if self.versions[key] > version:
                    to_send.append((key, self.data[key]))
        
        # Send missing data
        peer.receive_data(to_send)
    
    def _create_digest(self):
        """Create digest of current state."""
        return {k: self._hash(v) for k, v in self.data.items()}
    
    def _hash(self, value):
        """Create hash of value."""
        return hashlib.md5(str(value).encode()).hexdigest()[:8]
    
    def set(self, key, value):
        """Set a key-value pair."""
        self.data[key] = value
        self.versions[key] = time.time()
    
    def get(self, key):
        """Get a value by key."""
        return self.data.get(key)
    
    def receive_data(self, items):
        """Receive data from a peer."""
        for key, value in items:
            # Simple last-write-wins
            self.data[key] = value
```

---

## Parameters to Tune

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Fanout** | Peers contacted per round | 2-3 |
| **Interval** | Time between gossip rounds | 1-5 seconds |
| **TTL** | Rounds before stopping propagation | log(N) + buffer |

---

## For Your Setup

```
┌─────────────────────────────────────────────────────────┐
│              GOSSIP IN YOUR 3-NODE LAB                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   With only 3 nodes, gossip is simple:                  │
│                                                         │
│        RPi ◄──────► Office                              │
│         ▲              ▲                                │
│         │              │                                │
│         └──► Personal ◄┘                                │
│                                                         │
│   Config:                                               │
│     fanout: 2 (contact both other nodes)                │
│     interval: 1 second                                  │
│     Full mesh: everyone talks to everyone               │
│                                                         │
│   Perfect for learning! Later, scale to more nodes      │
│   to see gossip's real advantages.                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Comparison with Other Approaches

| Approach | Propagation | Consistency | Overhead |
|----------|-------------|-------------|----------|
| **Gossip** | O(log N) | Eventual | Low |
| **Broadcast** | O(1) | Immediate | High |
| **Consensus** | O(rounds) | Strong | Medium |
| **Primary-backup** | O(1) | Sequential | Low |

---

**Next:** [Project 1: Syncthing Setup →](../03-projects/project-1-syncthing.md)

