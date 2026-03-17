# Distributed Computing Learning Project

## Setup Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Office Laptop  │◄───►│ Personal Laptop │◄───►│   Raspberry Pi  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                    ┌────▼────┐
                                                    │   SSD   │
                                                    │ (nginx) │
                                                    └─────────┘
```

**Devices:**
- Office Laptop
- Personal Laptop  
- Raspberry Pi + SSD (running nginx, data storage)

**Goal:** Learn distributed computing by implementing sync across all devices.

---

## Learning Approaches (Simple → Complex)

### 1. Start Simple: Syncthing (P2P Sync)

Decentralized file sync - great for understanding what sync should do.

```bash
# macOS
brew install syncthing

# Raspberry Pi
sudo apt install syncthing
```

### 2. Build Your Own: rsync + File Watching

Learn about file change detection and delta sync.

```bash
# Watch for changes and sync to RPi
fswatch -o /path/to/folder | xargs -n1 -I{} rsync -avz /local/path user@rpi:/ssd/path
```

### 3. Distributed Computing Concepts to Implement

| Concept              | Description                                      |
|----------------------|--------------------------------------------------|
| **Leader Election**  | Bully algorithm, Raft leader election            |
| **Consensus**        | Raft/Paxos - how nodes agree on state            |
| **CRDTs**            | Conflict-free replicated data types              |
| **Vector Clocks**    | Ordering events across distributed nodes         |
| **Gossip Protocol**  | Epidemic information spreading                   |
| **Consistent Hashing** | Distributing data across nodes                 |

---

## Project Ideas

### A) Distributed Key-Value Store

```
RPi (Leader) ←→ Office Laptop ←→ Personal Laptop
     ↓
   SSD Storage
```

- Implement Raft for consensus
- Handle reads/writes across nodes
- Learn about replication lag, consistency

### B) Event-Sourced Sync System

- Each device logs changes as events
- Sync events, not files
- Replay events to reconstruct state

### C) P2P File Sync from Scratch

- Use libp2p or build your own protocol
- Implement chunk-based sync (like rsync)
- Handle conflict resolution (last-write-wins, merge, etc.)

---

## Recommended Learning Path

| Week   | Task                                              |
|--------|---------------------------------------------------|
| 1-2    | Use Syncthing to understand sync behavior         |
| 3-4    | Build simple sync with rsync + file watching      |
| 5-8    | Implement basic Raft consensus in Python/Go       |
| 9+     | Build distributed KV store or file sync with Raft |

---

## Language Recommendations

- **Go** - Built for distributed systems (goroutines, channels)
- **Python** - Fast prototyping, good for learning
- **Rust** - If you want systems programming too

---

## Key Resources

- [Raft Consensus Visualization](https://raft.github.io/)
- [Designing Data-Intensive Applications](https://dataintensive.net/) (Book)
- [MIT 6.824: Distributed Systems](https://pdos.csail.mit.edu/6.824/)
- [CRDTs Explained](https://crdt.tech/)

---

## RPi-Specific Setup

### nginx Configuration (already running)

Data stored on SSD - this becomes the "source of truth" or leader node.

### Network Setup Checklist

- [ ] Static IP for RPi on local network
- [ ] SSH keys configured for passwordless access
- [ ] Firewall rules for sync ports
- [ ] mDNS/Avahi for easy discovery (rpi.local)

---

## Next Steps

1. Choose a starting approach (Syncthing recommended for Week 1)
2. Pick a programming language
3. Decide on first concept to implement

