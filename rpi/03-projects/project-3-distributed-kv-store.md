# Project 3: Distributed Key-Value Store

> Build a distributed key-value store with Raft consensus.

**Previous:** [Project 2: rsync Watcher](./project-2-rsync-watcher.md) | **Next:** [Project 4: P2P File Sync](./project-4-p2p-file-sync.md)

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────┐
│                 DISTRIBUTED KEY-VALUE STORE                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Client Request                                             │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐                                           │
│  │   LEADER    │ ◄──── Raft Consensus ────►┌───────────┐   │
│  │    (RPi)    │                           │ FOLLOWER  │   │
│  │             │                           │ (Office)  │   │
│  │  Data: SSD  │                           │           │   │
│  └──────┬──────┘                           └───────────┘   │
│         │                                         ▲        │
│         │         ┌───────────┐                   │        │
│         └────────►│ FOLLOWER  │◄──────────────────┘        │
│                   │ (Personal)│                            │
│                   └───────────┘                            │
│                                                             │
│  Operations: GET, SET, DELETE                              │
│  Consistency: Strong (linearizable)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Components

### 1. Storage Engine

```python
# storage.py
import json
import os
from threading import Lock

class Storage:
    """Simple file-based key-value storage."""
    
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "kv_data.json")
        self.lock = Lock()
        self._load()
    
    def _load(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}
    
    def _save(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f)
    
    def get(self, key):
        with self.lock:
            return self.data.get(key)
    
    def set(self, key, value):
        with self.lock:
            self.data[key] = value
            self._save()
    
    def delete(self, key):
        with self.lock:
            if key in self.data:
                del self.data[key]
                self._save()
    
    def all(self):
        with self.lock:
            return dict(self.data)
```

### 2. Raft Log Entry

```python
# raft_log.py
from dataclasses import dataclass
from enum import Enum
from typing import Any

class Operation(Enum):
    SET = "SET"
    DELETE = "DELETE"

@dataclass
class LogEntry:
    term: int
    index: int
    operation: Operation
    key: str
    value: Any = None
    
    def to_dict(self):
        return {
            "term": self.term,
            "index": self.index,
            "operation": self.operation.value,
            "key": self.key,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            term=data["term"],
            index=data["index"],
            operation=Operation(data["operation"]),
            key=data["key"],
            value=data.get("value")
        )
```

### 3. Raft Node State

```python
# raft_node.py
from enum import Enum
import random
import time

class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class RaftNode:
    def __init__(self, node_id, peers, storage):
        self.node_id = node_id
        self.peers = peers  # List of (host, port)
        self.storage = storage
        
        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log = []
        
        # Volatile state
        self.state = NodeState.FOLLOWER
        self.commit_index = 0
        self.last_applied = 0
        
        # Leader state
        self.next_index = {}
        self.match_index = {}
        
        # Timing
        self.election_timeout = self._random_timeout()
        self.last_heartbeat = time.time()
    
    def _random_timeout(self):
        """Random election timeout between 150-300ms."""
        return random.uniform(0.15, 0.30)
    
    def check_election_timeout(self):
        """Check if we should start an election."""
        if self.state == NodeState.LEADER:
            return False
        
        elapsed = time.time() - self.last_heartbeat
        return elapsed > self.election_timeout
    
    def start_election(self):
        """Transition to candidate and request votes."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.election_timeout = self._random_timeout()
        
        # Request votes from all peers
        votes = 1  # Vote for self
        
        for peer in self.peers:
            vote_granted = self.request_vote(peer)
            if vote_granted:
                votes += 1
        
        # Check if we won
        if votes > len(self.peers) // 2:
            self.become_leader()
        else:
            self.state = NodeState.FOLLOWER
    
    def become_leader(self):
        """Transition to leader state."""
        self.state = NodeState.LEADER
        
        # Initialize leader state
        for peer in self.peers:
            self.next_index[peer] = len(self.log) + 1
            self.match_index[peer] = 0
        
        print(f"[Node {self.node_id}] Became leader for term {self.current_term}")
```

---

## API Server

```python
# api_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)
raft_node = None  # Initialized at startup

@app.route('/get/<key>', methods=['GET'])
def get_key(key):
    if raft_node.state != NodeState.LEADER:
        leader = raft_node.get_leader()
        return jsonify({"error": "not leader", "leader": leader}), 307
    
    value = raft_node.storage.get(key)
    if value is None:
        return jsonify({"error": "key not found"}), 404
    return jsonify({"key": key, "value": value})

@app.route('/set', methods=['POST'])
def set_key():
    if raft_node.state != NodeState.LEADER:
        leader = raft_node.get_leader()
        return jsonify({"error": "not leader", "leader": leader}), 307
    
    data = request.json
    key, value = data['key'], data['value']
    
    # Append to log and replicate
    entry = LogEntry(
        term=raft_node.current_term,
        index=len(raft_node.log) + 1,
        operation=Operation.SET,
        key=key,
        value=value
    )
    
    success = raft_node.replicate(entry)
    if success:
        return jsonify({"status": "ok", "key": key})
    return jsonify({"error": "replication failed"}), 500

@app.route('/delete/<key>', methods=['DELETE'])
def delete_key(key):
    if raft_node.state != NodeState.LEADER:
        return jsonify({"error": "not leader"}), 307
    
    entry = LogEntry(
        term=raft_node.current_term,
        index=len(raft_node.log) + 1,
        operation=Operation.DELETE,
        key=key
    )
    
    success = raft_node.replicate(entry)
    if success:
        return jsonify({"status": "ok"})
    return jsonify({"error": "replication failed"}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "node_id": raft_node.node_id,
        "state": raft_node.state.value,
        "term": raft_node.current_term,
        "log_length": len(raft_node.log),
        "commit_index": raft_node.commit_index
    })
```

---

## Deployment

### Node Configuration

```yaml
# config.yaml
nodes:
  rpi:
    host: "192.168.1.100"
    port: 8000
    data_dir: "/mnt/ssd/distributed-lab/kv-store"
  
  office:
    host: "192.168.1.101"
    port: 8001
    data_dir: "~/distributed-lab/kv-store"
  
  personal:
    host: "192.168.1.102"
    port: 8002
    data_dir: "~/distributed-lab/kv-store"
```

### Start Nodes

```bash
# On RPi
python3 kv_server.py --node-id rpi --config config.yaml

# On Office Laptop
python3 kv_server.py --node-id office --config config.yaml

# On Personal Laptop
python3 kv_server.py --node-id personal --config config.yaml
```

---

## Testing

```bash
# Set a value (will redirect to leader if needed)
curl -X POST http://rpi-sync.local:8000/set \
  -H "Content-Type: application/json" \
  -d '{"key": "hello", "value": "world"}'

# Get a value
curl http://rpi-sync.local:8000/get/hello

# Check cluster status
curl http://rpi-sync.local:8000/status
curl http://office-laptop.local:8001/status
curl http://personal-laptop.local:8002/status
```

---

## Implementation Guide

For complete Raft implementation details, see:
- [Raft Implementation Guide](../04-implementation/raft-implementation.md)

---

**Next:** [Project 4: P2P File Sync →](./project-4-p2p-file-sync.md)

