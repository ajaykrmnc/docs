# CAP Theorem & Consistency Models


> The fundamental theorem that defines the trade-offs in distributed systems.

**Previous:** [RPi Setup](../01-setup/rpi-setup.md) | **Next:** [Consensus Algorithms](./consensus-algorithms.md)

---

## The CAP Theorem

The CAP theorem states that a distributed system can only guarantee **two out of three** properties:

```
                         CONSISTENCY
                              ▲
                             /│\
                            / │ \
                           /  │  \
                          /   │   \
                         / CP │ CA \
                        /     │     \
                       /      │      \
                      /       │       \
                     ▼────────┴────────▼
              PARTITION              AVAILABILITY
              TOLERANCE

        You can only pick TWO:
        
        CP = Consistent + Partition Tolerant (sacrifice Availability)
        CA = Consistent + Available (sacrifice Partition Tolerance) ← NOT REALISTIC
        AP = Available + Partition Tolerant (sacrifice Consistency)
```

### Definitions

| Property | Definition | Example |
|----------|------------|---------|
| **Consistency** | All nodes see the same data at the same time | Read after write returns latest value |
| **Availability** | Every request receives a response | System never refuses queries |
| **Partition Tolerance** | System continues despite network failures | Nodes can't communicate but still work |

---

## Why You Must Choose

### Network Partitions Are Inevitable

```
Normal Operation:
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Node A  │◄───►│ Node B  │◄───►│ Node C  │
└─────────┘     └─────────┘     └─────────┘

Network Partition:
┌─────────┐     ┌─────────┐  ✗  ┌─────────┐
│ Node A  │◄───►│ Node B  │  ✗  │ Node C  │
└─────────┘     └─────────┘  ✗  └─────────┘
                   Partition ─────┘
```

When a partition happens, you must choose:
- **CP**: Refuse writes to maintain consistency (unavailable)
- **AP**: Accept writes on both sides (inconsistent)

---

## Real-World Examples

### CP Systems (Consistency + Partition Tolerance)

| System | Use Case | Trade-off |
|--------|----------|-----------|
| **MongoDB** (majority) | Financial data | May reject writes during partition |
| **etcd** | Configuration | Leader election, waits for consensus |
| **Zookeeper** | Coordination | Stops serving during leader loss |

### AP Systems (Availability + Partition Tolerance)

| System | Use Case | Trade-off |
|--------|----------|-----------|
| **Cassandra** | High-write loads | Eventual consistency |
| **DynamoDB** | Shopping carts | Last-write-wins possible |
| **CouchDB** | Offline-first apps | Conflicts must be resolved |

### CA Systems (Not Practical)

Single-node databases (PostgreSQL, MySQL) are technically CA, but they don't tolerate partitions because there's no distribution!

---

## Consistency Models

Different levels of consistency you can implement:

### Strong Consistency

```
Write(x=1) ────► Node A ────► Node B ────► Node C
                  │            │            │
                  ▼            ▼            ▼
Read(x) always returns 1 on all nodes after write completes
```

- **Guarantee**: All reads see the latest write
- **Cost**: Higher latency, requires consensus
- **Use for**: Banking, inventory, leader election

### Eventual Consistency

```
Write(x=1) ────► Node A
                  │
                  │ (propagates over time)
                  ▼
               Node B ─────► Node C
                  │            │
                  ▼            ▼
            Eventually x=1 on all nodes
```

- **Guarantee**: Given enough time, all replicas converge
- **Cost**: Temporary inconsistency
- **Use for**: Social media feeds, analytics, caches

### Causal Consistency

```
Write(x=1) by User A
       │
       ▼
Write(y=2) by User A (depends on x=1)
       │
       ▼
All nodes see x=1 before y=2 (causal order preserved)
```

- **Guarantee**: Causally related operations are seen in order
- **Cost**: Must track dependencies
- **Use for**: Collaborative editing, messaging

---

## For Your Setup

### Recommended Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR DISTRIBUTED LAB                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   For Learning:  Start with CP (using Raft)                 │
│   For Sync:      Use AP with CRDTs (see crdt.md)           │
│                                                             │
│   RPi (Leader) ─── Strong Consistency for writes            │
│        │                                                    │
│        ▼                                                    │
│   Laptops (Followers) ─── Eventually consistent reads OK   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Design Questions

When designing your sync system, ask:

1. **What happens when RPi is offline?**
   - CP: Laptops can't write
   - AP: Laptops write locally, merge later

2. **What if laptops edit the same file?**
   - CP: One write wins (rejected or queued)
   - AP: Both succeed, conflict resolution needed

3. **How stale can data be?**
   - Strong: Never stale
   - Eventual: Seconds to minutes acceptable?

---

## Practical Exercise

Simulate partition and observe behavior:

```bash
# On RPi, block traffic from one laptop
sudo iptables -A INPUT -s 192.168.1.101 -j DROP

# Try to write from blocked laptop
# Observe: Does write succeed? Is data consistent?

# Remove block
sudo iptables -D INPUT -s 192.168.1.101 -j DROP

# Check: How did system recover?
```

---

## Key Takeaways

1. **You can't have it all** - Accept the trade-off
2. **Network partitions happen** - Design for them
3. **Choose based on use case** - Financial = CP, Social = AP
4. **Your lab**: Perfect for experimenting with both!

---

**Next:** [Consensus Algorithms →](./consensus-algorithms.md)

