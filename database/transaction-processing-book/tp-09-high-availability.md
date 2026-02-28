# High Availability

## Overview

High availability (HA) is the ability of a system to remain operational despite failures. Jim Gray was a pioneer in fault-tolerant computing, contributing both theoretical foundations (the distinction between fail-fast and fail-operational systems) and practical systems (Tandem NonStop).

---

## Failure Models

### Types of Failures

```
┌─────────────────────────────────────────────────────────────────┐
│                      FAILURE TAXONOMY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TRANSIENT FAILURES                                          │
│     • Temporary glitches                                        │
│     • Often fixed by retry                                      │
│     • Examples: network timeout, cosmic ray bit flip            │
│                                                                 │
│  2. INTERMITTENT FAILURES                                       │
│     • Come and go unpredictably                                 │
│     • Hard to diagnose                                          │
│     • Examples: loose connection, overheating                   │
│                                                                 │
│  3. PERMANENT FAILURES                                          │
│     • Require repair or replacement                             │
│     • Examples: disk crash, memory failure                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mean Time Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                    AVAILABILITY METRICS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MTTF (Mean Time To Failure):                                   │
│  Average time a system runs before failure                      │
│                                                                 │
│  MTTR (Mean Time To Repair):                                    │
│  Average time to restore service after failure                  │
│                                                                 │
│  MTBF (Mean Time Between Failures):                             │
│  MTBF = MTTF + MTTR                                             │
│                                                                 │
│                                                                 │
│  Availability = MTTF / (MTTF + MTTR)                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ Availability │ Downtime/Year │ Name                   │     │
│  ├──────────────┼───────────────┼────────────────────────┤     │
│  │ 99%          │ 3.65 days     │ Two nines              │     │
│  │ 99.9%        │ 8.76 hours    │ Three nines            │     │
│  │ 99.99%       │ 52.6 minutes  │ Four nines             │     │
│  │ 99.999%      │ 5.26 minutes  │ Five nines             │     │
│  │ 99.9999%     │ 31.5 seconds  │ Six nines              │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fault Tolerance Strategies

### Fail-Fast vs Fail-Operational

```
┌─────────────────────────────────────────────────────────────────┐
│                 FAIL-FAST SYSTEMS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Philosophy: Detect failures quickly, stop cleanly              │
│                                                                 │
│  ┌───────────┐     Failure      ┌───────────┐                  │
│  │  Running  │ ───────────────► │  Stopped  │                  │
│  │  (Good)   │    detected      │  (Clean)  │                  │
│  └───────────┘                  └───────────┘                  │
│                                                                 │
│  Benefits:                                                      │
│  • No corruption propagation                                    │
│  • Clean recovery point                                         │
│  • Simpler error handling                                       │
│                                                                 │
│  Used by: Most modern databases                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               FAIL-OPERATIONAL SYSTEMS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Philosophy: Continue operating despite failures                │
│                                                                 │
│  ┌───────────┐     Failure      ┌───────────┐                  │
│  │  Running  │ ───────────────► │  Degraded │                  │
│  │  (Full)   │    detected      │  (Partial)│                  │
│  └───────────┘                  └───────────┘                  │
│                                                                 │
│  Requirements:                                                  │
│  • Redundant components                                         │
│  • Automatic failover                                           │
│  • More complex design                                          │
│                                                                 │
│  Used by: Tandem NonStop, airline systems                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Redundancy Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                   REDUNDANCY TYPES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. HARDWARE REDUNDANCY                                         │
│     ┌────────────────────────────────────────────────────┐     │
│     │ • Dual/Triple power supplies                       │     │
│     │ • RAID disk arrays                                 │     │
│     │ • Redundant network paths                          │     │
│     │ • Hot-spare processors                             │     │
│     └────────────────────────────────────────────────────┘     │
│                                                                 │
│  2. SOFTWARE REDUNDANCY                                         │


┌─────────────────────────────────────────────────────────────────┐
│              ASYNCHRONOUS REPLICATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Primary              Secondary                                 │
│  ┌─────────┐          ┌─────────┐                              │
│  │ Write   │          │         │                              │
│  │ Data    │───────►  │ Queue   │  (background)                │
│  │         │          │         │                              │
│  │ Commit  │          │  Apply  │                              │
│  └─────────┘          └─────────┘                              │
│      │                    │                                     │
│      │ Returns            │ Applies later                       │
│      ▼ immediately        ▼                                     │
│                                                                 │
│  Properties:                                                    │
│  ✓ Low latency commits                                          │
│  ✓ Primary independent of secondary                             │
│  ✗ Potential data loss (RPO > 0)                                │
│  ✗ Replication lag                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Replication Comparison

| Property | Synchronous | Asynchronous |
|----------|-------------|--------------|
| Data Loss Risk | None (RPO=0) | Possible (RPO>0) |
| Commit Latency | High (network RTT) | Low |
| Throughput | Lower | Higher |
| Distance | Limited by latency | Unlimited |
| Failover Complexity | Simple | Complex (data reconciliation) |

---

## Process Pairs (Tandem Approach)

### Overview

Jim Gray worked at Tandem Computers, which pioneered the **process pair** architecture for fault tolerance.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESS PAIRS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐              ┌────────────────┐            │
│  │    PRIMARY     │              │    BACKUP      │            │
│  │    PROCESS     │◄────────────►│    PROCESS     │            │
│  │   (Active)     │  Checkpoint  │   (Standby)    │            │
│  └───────┬────────┘   Messages   └───────┬────────┘            │
│          │                               │                      │
│          ▼                               ▼                      │
│  ┌────────────────┐              ┌────────────────┐            │
│  │    CPU A       │              │    CPU B       │            │
│  │  (Different    │              │  (Different    │            │
│  │   hardware)    │              │   hardware)    │            │
│  └────────────────┘              └────────────────┘            │
│                                                                 │
│  On Primary Failure:                                            │
│  1. Backup detects failure (heartbeat timeout)                  │
│  2. Backup becomes new primary                                  │
│  3. New backup started on another CPU                           │
│  4. Service continues with minimal interruption                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpoint Messages

```
┌─────────────────────────────────────────────────────────────────┐
│                  CHECKPOINTING PROTOCOL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Primary Process Activity:                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  Request → Process → Checkpoint → Response          │       │
│  │              │                                       │       │
│  │              └──► State sent to backup              │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  Checkpoint contains:                                           │
│  • Current state variables                                      │
│  • Open file/resource handles                                   │
│  • Transaction context                                          │
│  • Message queue state                                          │
│                                                                 │
│  Trade-off: More frequent checkpoints = faster recovery         │
│             but higher overhead                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failover Mechanisms

### Automatic Failover

```
┌─────────────────────────────────────────────────────────────────┐
│                   AUTOMATIC FAILOVER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Normal Operation:                                              │
│                                                                 │
│       Clients                                                   │
│          │                                                      │
│          ▼                                                      │
│  ┌───────────────┐    heartbeat    ┌───────────────┐           │
│  │    PRIMARY    │◄───────────────►│   STANDBY     │           │
│  │   (Active)    │                 │   (Passive)   │           │
│  └───────────────┘                 └───────────────┘           │
│                                                                 │
│  After Failover:                                                │
│                                                                 │
│       Clients (reconnect to new primary)                        │
│          │                                                      │
│          ▼                                                      │
│  ┌───────────────┐                 ┌───────────────┐           │
│  │    FAILED     │                 │  NEW PRIMARY  │           │
│  │   (Down)      │                 │   (Active)    │           │
│  └───────────────┘                 └───────────────┘           │
│                                                                 │
│  Steps:                                                         │
│  1. Detect failure (heartbeat timeout)                          │
│  2. Verify failure (avoid split-brain)                          │
│  3. Promote standby to primary                                  │
│  4. Redirect client connections                                 │
│  5. Perform recovery (if needed)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Split-Brain Problem

```
┌─────────────────────────────────────────────────────────────────┐
│                   SPLIT-BRAIN SCENARIO                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Network partition causes both nodes to think they're primary:  │
│                                                                 │
│  ┌───────────────┐      X      ┌───────────────┐               │
│  │   Node A      │◄────X──────►│   Node B      │               │
│  │ "I'm Primary" │    X        │ "I'm Primary" │               │
│  └───────────────┘    X        └───────────────┘               │
│         │          (Network          │                          │
│         │           Down)            │                          │
│         ▼                            ▼                          │
│    Accepts writes              Accepts writes                   │
│    (DIVERGENCE!)               (DIVERGENCE!)                    │
│                                                                 │
│  Solutions:                                                     │
│  • Quorum-based decisions (odd number of nodes)                 │
│  • STONITH (Shoot The Other Node In The Head)                   │
│  • Witness/arbitrator node                                      │
│  • Fencing (disable I/O from failed node)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```


---

## Cluster Architectures

### Shared-Nothing vs Shared-Disk

```
┌─────────────────────────────────────────────────────────────────┐
│                   SHARED-NOTHING ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Node 1     │  │   Node 2     │  │   Node 3     │          │
│  │   CPU/Mem    │  │   CPU/Mem    │  │   CPU/Mem    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Disk 1     │  │   Disk 2     │  │   Disk 3     │          │
│  │ (Partition A)│  │ (Partition B)│  │ (Partition C)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  • Each node owns its data partition                            │
│  • No shared storage                                            │
│  • Scales linearly                                              │
│  • Examples: Teradata, Google Spanner                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SHARED-DISK ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Node 1     │  │   Node 2     │  │   Node 3     │          │
│  │   CPU/Mem    │  │   CPU/Mem    │  │   CPU/Mem    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────────┬────┴─────────────────┘                   │
│                      │                                          │
│                      ▼                                          │
│         ┌────────────────────────────┐                          │
│         │      SHARED STORAGE        │                          │
│         │      (SAN / NAS)           │                          │
│         └────────────────────────────┘                          │
│                                                                 │
│  • All nodes access same storage                                │
│  • Requires distributed lock manager                            │
│  • Easier failover                                              │
│  • Examples: Oracle RAC, IBM Db2 pureScale                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Availability** is measured as MTTF / (MTTF + MTTR)
2. **Fail-fast** systems stop quickly on errors; **fail-operational** continue with degraded service
3. **Process pairs** (Tandem) provide sub-second failover through checkpointing
4. **Synchronous replication** guarantees zero data loss but adds latency
5. **Asynchronous replication** provides better performance but risks data loss
6. **Split-brain** is the critical challenge in automatic failover
7. **Shared-nothing** scales better; **shared-disk** simplifies failover

---

## References

- Gray, J. & Reuter, A. (1993). Chapter 8: "Fault Tolerance"
- Gray, J. (1990). "A Census of Tandem System Availability Between 1985 and 1990"
- Gray, J. & Siewiorek, D. (1991). "High-Availability Computer Systems"
- Tandem NonStop System Documentation
- Patterson, D. et al. (1988). "A Case for Redundant Arrays of Inexpensive Disks (RAID)"