# Service Discovery and Coordination

## Table of Contents
1. [Introduction to Service Discovery](#introduction-to-service-discovery)
2. [Service Discovery Patterns](#service-discovery-patterns)
3. [Load Balancing](#load-balancing)
4. [Distributed Coordination](#distributed-coordination)
5. [ZooKeeper Deep Dive](#zookeeper-deep-dive)
6. [etcd and Consul](#etcd-and-consul)
7. [Interview Questions](#interview-questions)

---

## Introduction to Service Discovery

### The Problem

```
┌─────────────────────────────────────────────────────────────────┐
│              WHY SERVICE DISCOVERY?                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Traditional (Static Configuration):                           │
│  ─────────────────────────────────────                         │
│  Service A config: "Service B is at 10.0.0.5:8080"            │
│                                                                 │
│  Problems:                                                     │
│  • What if Service B moves?                                    │
│  • What if Service B scales to 10 instances?                  │
│  • What if Service B instance fails?                          │
│  • Manual config updates = downtime                           │
│                                                                 │
│  Dynamic Service Discovery:                                    │
│  ──────────────────────────                                    │
│  ┌───────────┐     ┌──────────────────┐     ┌───────────┐     │
│  │ Service A │────►│ Service Registry │◄────│ Service B │     │
│  └───────────┘     │  "B is at..."    │     │ (register)│     │
│       │            └──────────────────┘     └───────────┘     │
│       │                                                        │
│       └──────────────────────────────────────►Service B       │
│                                                                 │
│  Benefits:                                                     │
│  • Automatic discovery                                         │
│  • Dynamic scaling                                             │
│  • Automatic failover                                          │
│  • No manual config                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

```
┌─────────────────────────────────────────────────────────────────┐
│              SERVICE DISCOVERY COMPONENTS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. SERVICE REGISTRY                                           │
│     • Database of available services                           │
│     • Stores: service name → [instances]                      │
│     • Must be highly available                                 │
│                                                                 │
│  2. SERVICE REGISTRATION                                       │
│     • Services register on startup                             │
│     • Deregister on shutdown                                   │
│     • Health checks for liveness                               │
│                                                                 │
│  3. SERVICE DISCOVERY                                          │
│     • Clients query registry                                   │
│     • Get list of healthy instances                           │
│     • Choose one (load balancing)                             │
│                                                                 │
│  4. HEALTH CHECKING                                            │
│     • Periodic health checks                                   │
│     • Remove unhealthy instances                               │
│     • TTL-based or active probing                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Discovery Patterns

### Client-Side Discovery

```
┌─────────────────────────────────────────────────────────────────┐
│              CLIENT-SIDE DISCOVERY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client queries registry and does load balancing:              │
│                                                                 │
│  ┌──────────────┐                                              │
│  │   Client     │                                              │
│  │  ┌────────┐  │    1. Query    ┌──────────────────┐         │
│  │  │  LB    │──┼───────────────►│ Service Registry │         │
│  │  └────────┘  │◄───────────────│ [B1, B2, B3]     │         │
│  └──────┬───────┘    2. Response └──────────────────┘         │
│         │                                                       │
│         │ 3. Direct call                                       │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │  Service B   │                                              │
│  │  (instance)  │                                              │
│  └──────────────┘                                              │
│                                                                 │
│  Pros:                                                         │
│  • No extra hop                                                │
│  • Client controls LB strategy                                │
│  • Works offline (cached)                                      │
│                                                                 │
│  Cons:                                                         │
│  • Client complexity                                           │
│  • Language-specific implementation                           │
│  • Tight coupling to registry                                 │
│                                                                 │
│  Examples: Netflix Eureka + Ribbon, gRPC                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Server-Side Discovery

```
┌─────────────────────────────────────────────────────────────────┐
│              SERVER-SIDE DISCOVERY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Load balancer queries registry:                               │
│                                                                 │
│  ┌──────────────┐                                              │
│  │   Client     │                                              │
│  └──────┬───────┘                                              │
│         │ 1. Request to LB                                     │
│         ▼                                                       │
│  ┌──────────────┐    2. Query    ┌──────────────────┐         │
│  │ Load Balancer│───────────────►│ Service Registry │         │
│  └──────┬───────┘◄───────────────│ [B1, B2, B3]     │         │
│         │            3. Response └──────────────────┘         │
│         │ 4. Forward                                           │
│         ▼                                                       │
│  ┌──────────────┐                                              │
│  │  Service B   │                                              │
│  └──────────────┘                                              │
│                                                                 │
│  Pros:                                                         │
│  • Simple clients                                              │
│  • Language agnostic                                           │
│  • Centralized LB logic                                       │


---

## Load Balancing

### Load Balancing Algorithms

```
┌─────────────────────────────────────────────────────────────────┐
│              LOAD BALANCING ALGORITHMS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ROUND ROBIN                                                │
│     Request 1 → Server A                                       │
│     Request 2 → Server B                                       │
│     Request 3 → Server C                                       │
│     Request 4 → Server A (cycle)                              │
│                                                                 │
│     Pros: Simple, even distribution                           │
│     Cons: Ignores server capacity/load                        │
│                                                                 │
│  2. WEIGHTED ROUND ROBIN                                       │
│     Server A (weight=3): gets 3 requests                      │
│     Server B (weight=1): gets 1 request                       │
│                                                                 │
│     Pros: Accounts for different capacities                   │
│     Cons: Static weights                                       │
│                                                                 │
│  3. LEAST CONNECTIONS                                          │
│     Route to server with fewest active connections            │
│                                                                 │
│     Server A: 10 connections ←                                │
│     Server B: 25 connections                                   │
│     Server C: 15 connections                                   │
│                                                                 │
│     Pros: Adapts to actual load                               │
│     Cons: Doesn't account for request complexity              │
│                                                                 │
│  4. LEAST RESPONSE TIME                                        │
│     Route to server with fastest response                     │
│                                                                 │
│     Pros: Optimizes for latency                               │
│     Cons: Requires response time tracking                     │
│                                                                 │
│  5. RANDOM                                                     │
│     Randomly select a server                                   │
│                                                                 │
│     Pros: Simple, no state needed                             │
│     Cons: May not distribute evenly                           │
│                                                                 │
│  6. IP HASH                                                    │
│     hash(client_ip) % num_servers                             │
│                                                                 │
│     Pros: Session affinity (same client → same server)       │
│     Cons: Uneven if client IPs clustered                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Consistent Hashing for Load Balancing

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSISTENT HASHING                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hash ring with servers and requests:                          │
│                                                                 │
│                    Server A                                    │
│                       ●                                         │
│                   ╱       ╲                                     │
│                 ╱           ╲                                   │
│               ╱               ╲                                 │
│  Server D   ●                   ●  Server B                    │
│               ╲               ╱                                 │
│                 ╲           ╱                                   │
│                   ╲       ╱                                     │
│                       ●                                         │
│                    Server C                                    │
│                                                                 │
│  Request routing:                                              │
│  • hash(request_key) → position on ring                       │
│  • Walk clockwise to find first server                        │
│                                                                 │
│  Adding/removing server:                                       │
│  • Only affects adjacent segment                              │
│  • Minimal redistribution                                      │
│                                                                 │
│  Virtual nodes:                                                │
│  • Each server has multiple positions                         │
│  • Better distribution                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Distributed Coordination

### Coordination Primitives

```
┌─────────────────────────────────────────────────────────────────┐
│              COORDINATION PRIMITIVES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DISTRIBUTED LOCKS                                          │
│     • Mutual exclusion across nodes                           │
│     • Only one holder at a time                               │
│     • Used for: leader election, resource access              │
│                                                                 │
│  2. LEADER ELECTION                                            │
│     • Choose one node as leader                               │
│     • Others are followers                                     │
│     • Re-elect on leader failure                              │
│                                                                 │
│  3. BARRIERS                                                   │
│     • Synchronization point                                    │
│     • All nodes wait until all arrive                         │
│     • Used for: distributed computation phases                │
│                                                                 │
│  4. CONFIGURATION MANAGEMENT                                   │
│     • Centralized config storage                              │
│     • Watch for changes                                        │
│     • Consistent view across nodes                            │
│                                                                 │
│  5. GROUP MEMBERSHIP                                           │
│     • Track which nodes are alive                             │
│     • Notify on join/leave                                    │
│     • Used for: cluster management                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Distributed Locks

```
┌─────────────────────────────────────────────────────────────────┐
│              DISTRIBUTED LOCK IMPLEMENTATION                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Requirements:                                                 │
│  • Mutual exclusion: Only one holder                          │
│  • Deadlock-free: Lock eventually released                    │
│  • Fault-tolerant: Works despite failures                     │
│                                                                 │
│  REDIS REDLOCK ALGORITHM:                                      │
│  ─────────────────────────                                     │
│  1. Get current time                                           │
│  2. Try to acquire lock on N/2+1 Redis instances              │
│  3. Calculate elapsed time                                     │
│  4. Lock valid if:                                             │
│     • Acquired on majority                                     │
│     • Elapsed time < lock TTL                                 │
│  5. If failed, release all locks                              │
│                                                                 │
│  ZOOKEEPER LOCK:                                               │
│  ───────────────                                               │
│  1. Create ephemeral sequential node: /lock/lock-000001       │
│  2. Get all children of /lock                                 │
│  3. If my node is lowest, I have lock                         │
│  4. Else, watch node just before mine                         │
│  5. On watch trigger, check again                             │
│                                                                 │
│  Ephemeral nodes auto-delete on session end!                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Leader Election

```
┌─────────────────────────────────────────────────────────────────┐
│              LEADER ELECTION                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BULLY ALGORITHM:                                              │
│  ────────────────                                              │
│  • Highest ID wins                                             │
│  • On detecting leader failure:                               │
│    1. Send ELECTION to all higher IDs                         │
│    2. If no response, become leader                           │
│    3. If response, wait for COORDINATOR message               │
│                                                                 │
│  ZOOKEEPER LEADER ELECTION:                                    │
│  ──────────────────────────                                    │
│  1. All candidates create ephemeral sequential nodes          │
│     /election/candidate-000001                                │
│     /election/candidate-000002                                │
│                                                                 │
│  2. Lowest sequence number is leader                          │
│                                                                 │
│  3. Others watch the node just before them                    │
│                                                                 │
│  4. On leader failure (ephemeral node deleted):               │
│     Next in line becomes leader                               │
│                                                                 │
│  Benefits:                                                     │
│  • No split-brain (ZK consensus)                              │
│  • Automatic failover                                          │
│  • Herd effect avoided (watch predecessor only)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ZooKeeper Deep Dive

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              ZOOKEEPER ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   ZOOKEEPER ENSEMBLE                     │   │
│  │                                                           │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐            │   │
│  │  │ Server 1 │   │ Server 2 │   │ Server 3 │            │   │
│  │  │ (Leader) │◄─►│(Follower)│◄─►│(Follower)│            │   │
│  │  └──────────┘   └──────────┘   └──────────┘            │   │
│  │       │              │              │                    │   │
│  │       └──────────────┼──────────────┘                    │   │
│  │                      │                                    │   │
│  │              ZAB Protocol (consensus)                    │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│              ┌───────────┼───────────┐                         │
│              ▼           ▼           ▼                         │
│          Client 1    Client 2    Client 3                      │
│                                                                 │
│  • Writes go through leader                                    │
│  • Reads can go to any server                                 │
│  • Majority quorum for writes (2f+1 tolerates f failures)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ZooKeeper Data Model

```
┌─────────────────────────────────────────────────────────────────┐
│              ZOOKEEPER DATA MODEL                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hierarchical namespace (like filesystem):                     │
│                                                                 │
│  /                                                             │
│  ├── /services                                                 │
│  │   ├── /services/web                                        │
│  │   │   ├── /services/web/instance-001                       │
│  │   │   └── /services/web/instance-002                       │
│  │   └── /services/api                                        │
│  ├── /config                                                   │
│  │   └── /config/database                                     │
│  └── /locks                                                    │
│      └── /locks/resource-1                                    │
│                                                                 │
│  Node Types:                                                   │
│  ───────────                                                   │
│  • PERSISTENT: Survives client disconnect                     │
│  • EPHEMERAL: Deleted when client session ends               │
│  • SEQUENTIAL: Auto-incrementing suffix                       │
│  • PERSISTENT_SEQUENTIAL                                       │
│  • EPHEMERAL_SEQUENTIAL                                        │
│                                                                 │
│  Each znode has:                                               │
│  • Data (up to 1MB)                                           │
│  • ACL (access control)                                       │
│  • Stat (version, timestamps, etc.)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ZooKeeper Watches

```
┌─────────────────────────────────────────────────────────────────┐
│              ZOOKEEPER WATCHES                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Clients can watch for changes:                                │
│                                                                 │
│  Client                          ZooKeeper                     │
│    │                                │                          │
│    │── getData(/config, watch) ───►│                          │
│    │◄── data + set watch ──────────│                          │
│    │                                │                          │
│    │    ... time passes ...         │                          │
│    │                                │                          │
│    │◄── WATCH EVENT ───────────────│ (data changed)           │
│    │                                │                          │
│    │── getData(/config, watch) ───►│ (re-register)            │
│    │                                │                          │
│                                                                 │
│  Watch Types:                                                  │
│  • Data watches: getData(), exists()                          │
│  • Child watches: getChildren()                               │
│                                                                 │
│  Important:                                                    │
│  • Watches are ONE-TIME triggers                              │
│  • Must re-register after each event                          │
│  • May miss events between trigger and re-register            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## etcd and Consul

### etcd Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              ETCD                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Distributed key-value store (used by Kubernetes)              │
│                                                                 │
│  Features:                                                     │
│  • Raft consensus                                              │
│  • Strong consistency                                          │
│  • Watch support                                               │
│  • TTL for keys                                                │
│  • Transactions                                                │
│                                                                 │
│  API:                                                          │
│  • PUT /v3/kv/put                                             │
│  • GET /v3/kv/range                                           │
│  • DELETE /v3/kv/deleterange                                  │
│  • WATCH /v3/watch                                            │
│                                                                 │
│  Use cases:                                                    │
│  • Kubernetes cluster state                                   │
│  • Service discovery                                          │
│  • Distributed locking                                        │
│  • Configuration management                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Consul Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSUL                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Service mesh and service discovery platform                   │
│                                                                 │
│  Features:                                                     │
│  • Service discovery (DNS + HTTP API)                         │
│  • Health checking                                             │
│  • KV store                                                    │
│  • Multi-datacenter                                            │
│  • Service mesh (Connect)                                     │
│                                                                 │
│  Architecture:                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    CONSUL CLUSTER                        │  │
│  │  ┌────────┐   ┌────────┐   ┌────────┐                  │  │
│  │  │ Server │   │ Server │   │ Server │  (Raft)         │  │
│  │  └────────┘   └────────┘   └────────┘                  │  │
│  │       │            │            │                       │  │
│  │       └────────────┼────────────┘                       │  │
│  │                    │                                     │  │
│  │  ┌────────┐   ┌────────┐   ┌────────┐                  │  │
│  │  │ Agent  │   │ Agent  │   │ Agent  │  (on each node) │  │
│  │  └────────┘   └────────┘   └────────┘                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison

| Feature | ZooKeeper | etcd | Consul |
|---------|-----------|------|--------|
| **Consensus** | ZAB | Raft | Raft |
| **Data Model** | Hierarchical | Flat KV | Flat KV + Services |
| **Watch** | One-time | Continuous | Continuous |
| **Health Check** | Session-based | TTL | Active probing |
| **DNS** | No | No | Yes |
| **Multi-DC** | No | No | Yes |
| **Use Case** | Coordination | K8s, config | Service mesh |

---

## Interview Questions

### Conceptual Questions

**Q1: What's the difference between client-side and server-side service discovery?**

| Aspect | Client-Side | Server-Side |
|--------|-------------|-------------|
| LB location | In client | Separate component |
| Client complexity | Higher | Lower |
| Network hops | Fewer | More |
| Language support | Per-language | Universal |
| Examples | Eureka+Ribbon | AWS ELB, K8s |

**Q2: How does ZooKeeper handle leader election?**

1. Candidates create ephemeral sequential znodes
2. Lowest sequence number becomes leader
3. Others watch predecessor (not leader)
4. On leader failure, ephemeral node deleted
5. Next in sequence becomes leader
6. No thundering herd (watch predecessor only)

**Q3: What are ephemeral nodes in ZooKeeper?**

- Automatically deleted when client session ends
- Used for: service registration, locks, leader election
- Session = heartbeat-based connection
- Session timeout → node deleted → triggers watches

### Design Questions

**Q4: Design a service discovery system.**

```
Components:
├── Service Registry (ZK/etcd/Consul)
├── Registration
│   ├── Self-registration on startup
│   ├── Heartbeat/TTL for liveness
│   └── Deregistration on shutdown
├── Discovery
│   ├── Client queries registry
│   ├── Caching with TTL
│   └── Watch for changes
└── Health Checking
    ├── Active probing (HTTP/TCP)
    └── Passive (heartbeat timeout)
```

**Q5: How would you implement distributed locking?**

```
ZooKeeper approach:
1. Create ephemeral sequential node: /locks/resource/lock-
2. Get all children, sort by sequence
3. If my node is lowest → I have lock
4. Else watch node just before mine
5. On watch trigger, repeat from step 2
6. Release: delete my node

Key properties:
• Ephemeral = auto-release on failure
• Sequential = fair ordering
• Watch predecessor = no herd effect
```

---

## Summary

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         SERVICE DISCOVERY CHEAT SHEET                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DISCOVERY PATTERNS:                                           │
│  • Client-side: Client queries registry, does LB              │
│  • Server-side: LB queries registry, routes request           │
│  • DNS-based: Use DNS for discovery                           │
│                                                                 │
│  LOAD BALANCING:                                               │
│  • Round robin: Simple rotation                               │
│  • Least connections: Route to least busy                     │
│  • Consistent hashing: Minimal redistribution                 │
│                                                                 │
│  COORDINATION PRIMITIVES:                                      │
│  • Distributed locks                                           │
│  • Leader election                                             │
│  • Configuration management                                    │
│  • Group membership                                            │
│                                                                 │
│  ZOOKEEPER:                                                    │
│  • Hierarchical namespace                                      │
│  • Ephemeral nodes (auto-delete on disconnect)                │
│  • Sequential nodes (auto-increment)                          │
│  • One-time watches                                            │
│                                                                 │
│  ETCD:                                                         │
│  • Flat key-value                                              │
│  • Raft consensus                                              │
│  • Used by Kubernetes                                          │
│                                                                 │
│  CONSUL:                                                       │
│  • Service discovery + mesh                                    │
│  • Built-in health checking                                   │
│  • Multi-datacenter support                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

