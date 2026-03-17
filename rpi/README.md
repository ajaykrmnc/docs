# Distributed Computing Learning Lab

> A hands-on learning project to master distributed systems using real hardware: Office Laptop, Personal Laptop, and Raspberry Pi with SSD.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DISTRIBUTED SYNC NETWORK                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐     │
│    │   OFFICE    │◄───────►│  PERSONAL   │◄───────►│ RASPBERRY   │     │
│    │   LAPTOP    │         │   LAPTOP    │         │     PI      │     │
│    │             │         │             │         │             │     │
│    │  • Node A   │         │  • Node B   │         │  • Node C   │     │
│    │  • Worker   │         │  • Worker   │         │  • Leader   │     │
│    └─────────────┘         └─────────────┘         └──────┬──────┘     │
│           │                       │                       │            │
│           └───────────────────────┼───────────────────────┘            │
│                                   │                                    │
│                          ┌────────▼────────┐                           │
│                          │    NGINX + SSD   │                          │
│                          │  (Data Storage)  │                          │
│                          │  (API Gateway)   │                          │
│                          └─────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Documentation Structure

### 📚 Setup Guides
- [Device Prerequisites](./01-setup/device-prerequisites.md) - Software requirements for all devices
- [Network Configuration](./01-setup/network-configuration.md) - Setting up secure communication
- [Raspberry Pi Setup](./01-setup/rpi-setup.md) - Complete RPi configuration with SSD and nginx

### 🧠 Core Concepts
- [CAP Theorem & Consistency Models](./02-concepts/cap-theorem.md) - Foundation of distributed systems
- [Consensus Algorithms](./02-concepts/consensus-algorithms.md) - Raft, Paxos, and leader election
- [CRDTs](./02-concepts/crdts.md) - Conflict-free Replicated Data Types
- [Vector Clocks](./02-concepts/vector-clocks.md) - Ordering events in distributed systems
- [Gossip Protocol](./02-concepts/gossip-protocol.md) - Epidemic information spreading

### 🔨 Hands-on Projects
- [Project 1: Syncthing Setup](./03-projects/project-1-syncthing.md) - P2P sync understanding
- [Project 2: Custom rsync Watcher](./03-projects/project-2-rsync-watcher.md) - File change detection
- [Project 3: Distributed KV Store](./03-projects/project-3-distributed-kv-store.md) - Build your own Redis
- [Project 4: P2P File Sync](./03-projects/project-4-p2p-file-sync.md) - Full custom implementation

### 💻 Implementation Guides
- [Implementing Raft Consensus](./04-implementation/raft-implementation.md) - Step-by-step Raft
- [Building CRDTs](./04-implementation/crdt-implementation.md) - Practical CRDT examples

### 📖 Additional Resources
- [Learning Resources](./resources.md) - Books, courses, papers, and tools

## Learning Roadmap

```
Week 1-2          Week 3-4           Week 5-8              Week 9-12
   │                 │                  │                     │
   ▼                 ▼                  ▼                     ▼
┌──────┐         ┌──────┐          ┌──────┐             ┌──────┐
│Setup │────────►│Basic │─────────►│Raft  │────────────►│Full  │
│Sync  │         │Watch │          │Impl  │             │P2P   │
└──────┘         └──────┘          └──────┘             └──────┘
Syncthing        rsync+fswatch     Consensus            Custom Sync
```

## Quick Start

```bash
# Clone this documentation
cd ~/docs/rpi

# Start with device setup
open 01-setup/device-prerequisites.md

# Then follow the numbered progression
```

## Goals

By the end of this learning path, you will:

1. ✅ Understand core distributed systems concepts (CAP, consensus, replication)
2. ✅ Implement leader election and Raft consensus from scratch
3. ✅ Build conflict-free data structures (CRDTs)
4. ✅ Create a working distributed key-value store
5. ✅ Design and implement a custom P2P file synchronization system

---

**Next:** [Start with Device Prerequisites →](./01-setup/device-prerequisites.md)

