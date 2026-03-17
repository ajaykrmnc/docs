# Consensus Algorithms

> How distributed nodes agree on a single value or leader.

**Previous:** [CAP Theorem](./cap-theorem.md) | **Next:** [CRDTs](./crdts.md)

---

## The Consensus Problem

How do multiple nodes agree on something when:
- Nodes can fail
- Messages can be lost or delayed
- There's no global clock

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Node A  │     │ Node B  │     │ Node C  │
│  "Yes"  │     │  "No"   │     │  "Yes"  │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     └───────────────┴───────────────┘
                     │
                     ▼
              What's the answer?
```

---

## Leader Election

Before consensus, nodes often elect a leader to coordinate decisions.

### The Bully Algorithm

Simple leader election where highest ID wins:

```
Step 1: Node detects leader failure
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Node 1  │     │ Node 2  │     │ Node 3  │
│         │     │ Timeout │     │ (Dead)  │
└─────────┘     └────┬────┘     └─────────┘
                     │
                     ▼
            "Leader 3 is dead!"

Step 2: Start election (send to higher IDs)
┌─────────┐     ┌─────────┐
│ Node 1  │◄────│ Node 2  │──── Election(2) ───► (No higher node)
│ Alive   │     │         │
└─────────┘     └─────────┘

Step 3: Node 2 becomes leader (no higher response)
```

#### Implementation Pseudocode

```python
class BullyElection:
    def __init__(self, node_id, all_nodes):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.leader = None
    
    def start_election(self):
        higher_nodes = [n for n in self.all_nodes if n > self.node_id]
        
        if not higher_nodes:
            # I am the highest, I am leader
            self.declare_victory()
            return
        
        # Send election messages to higher nodes
        responses = []
        for node in higher_nodes:
            response = self.send_election(node)
            if response:
                responses.append(response)
        
        if not responses:
            # No higher node responded, I win
            self.declare_victory()
    
    def declare_victory(self):
        self.leader = self.node_id
        for node in self.all_nodes:
            self.send_coordinator(node, self.node_id)
```

---

## Raft Consensus

The most understandable consensus algorithm. Used by etcd, Consul, etc.

### Core Concepts

```
┌──────────────────────────────────────────────────────────────┐
│                         RAFT ROLES                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   FOLLOWER ──(timeout)──► CANDIDATE ──(wins)──► LEADER      │
│       ▲                        │                    │        │
│       │                        │                    │        │
│       └────────────────────────┴────────────────────┘        │
│                     (loses/timeout)                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Raft Phases

#### 1. Leader Election

```
Term 1: All start as Followers
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Follower    │  │ Follower    │  │ Follower    │
│ Timeout: 5s │  │ Timeout: 3s │  │ Timeout: 4s │
└─────────────┘  └─────────────┘  └─────────────┘

Node B times out first, becomes Candidate:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Follower    │◄─│ Candidate   │─►│ Follower    │
│             │  │ "Vote me"   │  │             │
└──────┬──────┘  └─────────────┘  └──────┬──────┘
       │                Vote Yes          │
       └──────────────────────────────────┘

Node B gets majority, becomes Leader:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Follower    │◄─│   LEADER    │─►│ Follower    │
│             │  │ Heartbeats  │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

#### 2. Log Replication

```
Client Request: SET x = 5
         │
         ▼
    ┌─────────┐
    │ LEADER  │
    │ Log: [1]│──── AppendEntries ────►┌─────────┐
    └─────────┘                        │Follower │
         │                             │ Log: [1]│
         │                             └─────────┘
         │
         └──── AppendEntries ────►┌─────────┐
                                  │Follower │
                                  │ Log: [1]│
                                  └─────────┘
         │
         ▼
    Majority ACK received
    Commit entry, respond to client
```

#### 3. Safety

- Only one leader per term
- Leaders never overwrite their logs
- If logs differ, follower's log is overwritten

---

## Raft Implementation Outline

See detailed implementation: [Raft Implementation Guide](../04-implementation/raft-implementation.md)

```go
type RaftNode struct {
    id          int
    state       State  // Follower, Candidate, Leader
    currentTerm int
    votedFor    int
    log         []LogEntry
    
    // Volatile state
    commitIndex int
    lastApplied int
    
    // Leader state
    nextIndex   map[int]int
    matchIndex  map[int]int
}

type LogEntry struct {
    Term    int
    Command interface{}
}
```

---

## Paxos (Brief Overview)

Older, more complex consensus algorithm.

| Aspect | Raft | Paxos |
|--------|------|-------|
| Understandability | High | Low |
| Leader | Single, stable | Can have conflicts |
| Phases | 2 (election + replication) | 3 (prepare, accept, learn) |
| Use cases | etcd, Consul | Chubby, Spanner |

---

## For Your Setup

### 3-Node Raft Cluster

```
┌─────────────────────────────────────────────────────────────┐
│                   YOUR RAFT CLUSTER                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   RPi (ID: 3)      Office (ID: 1)     Personal (ID: 2)     │
│   Preferred        Lower priority      Medium priority      │
│   Leader                                                    │
│                                                             │
│   Quorum Size: 2 (majority of 3)                           │
│   Can tolerate: 1 node failure                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Tips

1. **Give RPi highest priority** - Lower election timeout
2. **Use 3 nodes for quorum** - Need 2/3 for consensus
3. **Heartbeat interval**: 150ms
4. **Election timeout**: 300-500ms (randomized)

---

## Practical Exercise

1. Implement leader election with the Bully algorithm
2. Test by killing the leader node
3. Observe new leader election
4. Progress to full Raft implementation

---

**Next:** [CRDTs →](./crdts.md)

