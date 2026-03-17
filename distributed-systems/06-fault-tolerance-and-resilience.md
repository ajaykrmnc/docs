# Fault Tolerance and Resilience in Distributed Systems

## Table of Contents
1. [Introduction to Fault Tolerance](#introduction-to-fault-tolerance)
2. [Types of Failures](#types-of-failures)
3. [Failure Detection](#failure-detection)
4. [Recovery Strategies](#recovery-strategies)
5. [Resilience Patterns](#resilience-patterns)
6. [Chaos Engineering](#chaos-engineering)
7. [Real-World Systems](#real-world-systems)
8. [Interview Questions](#interview-questions)

---

## Introduction to Fault Tolerance

### What is Fault Tolerance?

**Fault tolerance** is the ability of a system to continue operating correctly even when some of its components fail.

```
┌─────────────────────────────────────────────────────────────────┐
│              FAULT TOLERANCE HIERARCHY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FAULT → ERROR → FAILURE                                       │
│                                                                 │
│  FAULT:   The cause (bug, hardware defect, cosmic ray)        │
│           "Something is wrong in the system"                   │
│                                                                 │
│  ERROR:   The manifestation (incorrect state)                  │
│           "The system is in an invalid state"                  │
│                                                                 │
│  FAILURE: The consequence (system doesn't work)                │
│           "The system cannot provide correct service"          │
│                                                                 │
│  Example:                                                      │
│  Fault:   Disk sector goes bad                                │
│  Error:   Corrupted data in memory                            │
│  Failure: Application crashes                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Availability Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│              AVAILABILITY CALCULATIONS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Availability = Uptime / (Uptime + Downtime)                   │
│                                                                 │
│  "Nines" of availability:                                      │
│                                                                 │
│  │ Nines │ Availability │ Downtime/Year │ Downtime/Month │    │
│  │───────│──────────────│───────────────│────────────────│    │
│  │   2   │    99%       │   3.65 days   │    7.2 hours   │    │
│  │   3   │    99.9%     │   8.76 hours  │   43.2 minutes │    │
│  │   4   │    99.99%    │  52.6 minutes │   4.32 minutes │    │
│  │   5   │    99.999%   │   5.26 minutes│  25.9 seconds  │    │
│  │   6   │    99.9999%  │  31.5 seconds │   2.59 seconds │    │
│                                                                 │
│  MTBF (Mean Time Between Failures)                             │
│  MTTR (Mean Time To Recovery)                                  │
│                                                                 │
│  Availability = MTBF / (MTBF + MTTR)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Design for Failure

> "Everything fails, all the time." - Werner Vogels, Amazon CTO

```
┌─────────────────────────────────────────────────────────────────┐
│              DESIGN PRINCIPLES                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ASSUME FAILURE                                             │
│     • Hardware will fail                                       │
│     • Software will have bugs                                  │
│     • Networks will partition                                  │
│     • Humans will make mistakes                                │
│                                                                 │
│  2. DESIGN FOR RECOVERY                                        │
│     • Redundancy at every level                                │
│     • Automatic failover                                       │
│     • Data replication                                         │
│     • Graceful degradation                                     │
│                                                                 │
│  3. CONTAIN FAILURES                                           │
│     • Bulkheads (isolation)                                    │
│     • Circuit breakers                                         │
│     • Timeouts                                                 │
│     • Blast radius reduction                                   │
│                                                                 │
│  4. DETECT QUICKLY                                             │
│     • Health checks                                            │
│     • Monitoring and alerting                                  │
│     • Distributed tracing                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Types of Failures

### Failure Classification

```
┌─────────────────────────────────────────────────────────────────┐
│              FAILURE TYPES                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CRASH FAILURE (Fail-Stop)                                  │
│     ─────────────────────────                                  │
│     • Node stops working completely                            │
│     • No more responses                                        │
│     • Easiest to detect                                        │
│                                                                 │
│     ┌────────┐                                                 │
│     │ Node X │ ──────────────► 💀 (dead)                      │
│     └────────┘                                                 │
│                                                                 │
│  2. OMISSION FAILURE                                           │
│     ─────────────────                                          │
│     • Node fails to send or receive messages                   │
│     • Still alive but dropping messages                        │
│                                                                 │
│     ┌────────┐         ┌────────┐                             │
│     │ Node A │ ──XXX──►│ Node B │  (message lost)             │
│     └────────┘         └────────┘                             │
│                                                                 │
│  3. TIMING FAILURE                                             │
│     ────────────────                                           │
│     • Response outside expected time bound                     │
│     • Too slow to be useful                                    │
│                                                                 │
│     Request ──────────────────────────────────► Response       │
│                                                 (too late!)    │
│                                                                 │
│  4. BYZANTINE FAILURE                                          │
│     ───────────────────                                        │
│     • Node behaves arbitrarily (malicious or buggy)           │
│     • May send wrong or conflicting information                │
│     • Hardest to handle                                        │
│                                                                 │


---

## Failure Detection

### The Challenge

In distributed systems, it's hard to distinguish between:
- A failed node
- A slow node
- A network partition

### Failure Detector Properties

```
┌─────────────────────────────────────────────────────────────────┐
│              FAILURE DETECTOR PROPERTIES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  COMPLETENESS:                                                 │
│  • Every failed node is eventually detected                    │
│  • "No false negatives forever"                                │
│                                                                 │
│  ACCURACY:                                                     │
│  • No healthy node is incorrectly suspected                   │
│  • "No false positives"                                        │
│                                                                 │
│  Trade-off: Can't have both perfectly!                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │            COMPLETENESS                                  │  │
│  │                 ▲                                        │  │
│  │                 │                                        │  │
│  │    Perfect      │      Impossible                       │  │
│  │  Completeness   │      (in async system)                │  │
│  │                 │                                        │  │
│  │                 │                                        │  │
│  │─────────────────┼────────────────────► ACCURACY         │  │
│  │                 │                                        │  │
│  │   Practical     │      Perfect                          │  │
│  │   (eventually   │      Accuracy                         │  │
│  │    accurate)    │                                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Heartbeat Mechanisms

```
┌─────────────────────────────────────────────────────────────────┐
│              HEARTBEAT PATTERNS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PUSH-BASED (Node sends heartbeats)                        │
│                                                                 │
│     ┌────────┐    heartbeat    ┌────────────┐                 │
│     │  Node  │────────────────►│  Monitor   │                 │
│     └────────┘    (periodic)   └────────────┘                 │
│                                                                 │
│     • Node actively sends "I'm alive" messages                │
│     • Monitor marks node failed if no heartbeat for timeout   │
│                                                                 │
│  2. PULL-BASED (Monitor pings nodes)                          │
│                                                                 │
│     ┌────────────┐    ping     ┌────────┐                     │
│     │  Monitor   │────────────►│  Node  │                     │
│     └────────────┘◄────────────└────────┘                     │
│                       pong                                     │
│                                                                 │
│     • Monitor actively checks node health                     │
│     • No response = potential failure                         │
│                                                                 │
│  3. GOSSIP-BASED (Decentralized)                              │
│                                                                 │
│     ┌────────┐◄────────►┌────────┐                           │
│     │ Node A │          │ Node B │                           │
│     └────────┘          └────────┘                           │
│          │                  │                                  │
│          └────────┬─────────┘                                  │
│                   ▼                                            │
│              ┌────────┐                                        │
│              │ Node C │                                        │
│              └────────┘                                        │
│                                                                 │
│     • Nodes share failure information                         │
│     • No single point of failure                              │
│     • Eventual consistency of failure detection               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phi Accrual Failure Detector

```
┌─────────────────────────────────────────────────────────────────┐
│              PHI ACCRUAL FAILURE DETECTOR                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Instead of binary (alive/dead), outputs probability:          │
│                                                                 │
│  φ (phi) = suspicion level                                     │
│                                                                 │
│  φ = 1  → 10% chance of failure                               │
│  φ = 2  → 1% chance of failure                                │
│  φ = 3  → 0.1% chance of failure                              │
│  ...                                                           │
│                                                                 │
│  Based on historical heartbeat intervals:                      │
│                                                                 │
│  Time since last heartbeat                                     │
│  ──────────────────────────────────────────►                   │
│       │     │     │     │           │                          │
│      HB    HB    HB    HB          now                        │
│                                     │                          │
│                         φ increases as time passes            │
│                                                                 │
│  Advantages:                                                   │
│  • Adaptive to network conditions                             │
│  • No fixed timeout                                           │
│  • Application chooses threshold                              │
│                                                                 │
│  Used in: Cassandra, Akka                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recovery Strategies

### Redundancy Types

```
┌─────────────────────────────────────────────────────────────────┐
│              REDUNDANCY STRATEGIES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ACTIVE REPLICATION (State Machine Replication)            │
│                                                                 │
│     Request ──┬───► Replica 1 ───┐                            │
│               ├───► Replica 2 ───┼───► Response               │
│               └───► Replica 3 ───┘                            │
│                                                                 │
│     • All replicas process every request                      │
│     • Fastest response wins (or majority)                     │
│     • High resource usage                                      │
│                                                                 │
│  2. PASSIVE REPLICATION (Primary-Backup)                      │
│                                                                 │
│     Request ───► Primary ───► Response                        │
│                     │                                          │
│                     ├──sync──► Backup 1                       │
│                     └──sync──► Backup 2                       │
│                                                                 │
│     • Only primary handles requests                           │
│     • Backups take over on failure                            │
│     • More efficient resource usage                           │
│                                                                 │
│  3. SEMI-ACTIVE REPLICATION                                   │
│                                                                 │
│     Request ───► Primary ───► Response                        │
│         │                                                      │
│         └───► Backups (process but don't respond)             │
│                                                                 │
│     • Backups ready to take over immediately                  │
│     • Warm standby                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Failover Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│              FAILOVER TYPES                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  COLD STANDBY:                                                 │
│  • Backup starts from scratch when primary fails              │
│  • Slowest recovery                                           │
│  • Cheapest                                                    │
│                                                                 │
│  WARM STANDBY:                                                 │
│  • Backup has recent state (async replication)                │
│  • Medium recovery time                                        │
│  • Some data loss possible                                     │
│                                                                 │
│  HOT STANDBY:                                                  │
│  • Backup fully synchronized (sync replication)               │
│  • Fastest failover                                           │
│  • Most expensive                                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │        Cold        │       Warm       │       Hot      │    │
│  ├────────────────────┼──────────────────┼────────────────│    │
│  │  Recovery: Hours   │  Recovery: Mins  │ Recovery: Secs │    │
│  │  Data loss: High   │  Data loss: Some │ Data loss: None│    │
│  │  Cost: Low         │  Cost: Medium    │ Cost: High     │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Checkpointing and Recovery

```
┌─────────────────────────────────────────────────────────────────┐
│              CHECKPOINTING                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Save state periodically to enable recovery:                   │
│                                                                 │
│  Time ─────────────────────────────────────────────────►       │
│                                                                 │
│       │         │         │         │                          │
│       ▼         ▼         ▼         ▼                          │
│     [CP1]     [CP2]     [CP3]     [CP4]                       │
│       │         │         │    crash │                         │
│       │         │         │         💥                         │
│       │         │         │                                    │
│       │         │         └────► Recover from CP3             │
│       │         │                (lose work since CP3)        │
│                                                                 │
│  COORDINATED CHECKPOINTING:                                    │
│  • All processes checkpoint at same "virtual time"            │
│  • Consistent global state                                     │
│  • Requires coordination (expensive)                          │
│                                                                 │
│  UNCOORDINATED CHECKPOINTING:                                  │
│  • Each process checkpoints independently                     │
│  • May need rollback cascade (domino effect)                  │
│  • Less coordination overhead                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Resilience Patterns

### Circuit Breaker Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│              CIRCUIT BREAKER                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌──────────┐                                │
│               ┌────│  CLOSED  │◄───┐                           │
│               │    └────┬─────┘    │                           │
│               │         │          │                            │
│               │    failure count   │ success                   │
│               │    exceeds         │ (reset)                   │
│               │    threshold       │                            │
│               │         │          │                            │
│               │         ▼          │                            │
│               │    ┌──────────┐    │                           │
│               │    │   OPEN   │────┘                           │
│               │    └────┬─────┘                                │
│               │         │                                       │
│               │    timeout                                     │
│               │    expires                                     │
│               │         │                                       │
│               │         ▼                                       │
│               │    ┌──────────────┐                            │
│               └────│  HALF-OPEN   │                            │
│                    └──────────────┘                            │
│                                                                 │
│  CLOSED: Normal operation, requests flow through              │
│  OPEN: Fail fast, no requests to downstream                   │
│  HALF-OPEN: Test with limited requests                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Bulkhead Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│              BULKHEAD PATTERN                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Isolate components to prevent cascading failures:             │
│                                                                 │
│  WITHOUT BULKHEAD:                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │             SHARED THREAD POOL (100 threads)             │  │
│  │                                                           │  │
│  │  Service A █████████████████████████████████████████     │  │
│  │  Service B ██████ (starved!)                             │  │
│  │  Service C ████   (starved!)                             │  │
│  │                                                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  WITH BULKHEAD:                                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Service A Pool │ │  Service B Pool │ │  Service C Pool │ │
│  │   (50 threads)  │ │   (30 threads)  │ │   (20 threads)  │ │
│  │  █████████████  │ │  ██████████     │ │  ████████       │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                                 │
│  Service A issues won't affect B or C!                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Retry with Backoff

```
┌─────────────────────────────────────────────────────────────────┐
│              RETRY STRATEGIES                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. IMMEDIATE RETRY (Bad for thundering herd)                 │
│     Request → Fail → Retry → Fail → Retry                     │
│                                                                 │
│  2. FIXED DELAY                                                │
│     Request → Fail → [1s] → Retry → Fail → [1s] → Retry       │
│                                                                 │
│  3. EXPONENTIAL BACKOFF                                        │
│     Request → Fail → [1s] → Retry → Fail → [2s] → [4s] → ... │
│                                                                 │
│     delay = base * 2^attempt                                  │
│                                                                 │
│  4. EXPONENTIAL BACKOFF + JITTER (Best)                       │
│     Request → Fail → [1s ± random] → Retry → [2s ± random]   │
│                                                                 │
│     delay = base * 2^attempt + random(0, base)                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐│
│  │  Attempt  │ Fixed │ Exponential │ Exp + Jitter           ││
│  │───────────┼───────┼─────────────┼────────────────────────││
│  │     1     │  1s   │     1s      │    0.5s - 1.5s         ││
│  │     2     │  1s   │     2s      │    1.5s - 2.5s         ││
│  │     3     │  1s   │     4s      │    3.5s - 4.5s         ││
│  │     4     │  1s   │     8s      │    7.5s - 8.5s         ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Rate Limiting

```
┌─────────────────────────────────────────────────────────────────┐
│              RATE LIMITING ALGORITHMS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TOKEN BUCKET                                               │
│                                                                 │
│     ┌────────────────┐                                         │
│     │    🪣 Bucket    │ ← Tokens added at fixed rate          │
│     │  ● ● ● ● ●     │   (e.g., 10 tokens/second)            │
│     └───────┬────────┘                                         │
│             │                                                   │
│        Each request                                            │
│        takes 1 token                                           │
│             │                                                   │
│     Empty bucket = reject request                              │
│                                                                 │
│  2. LEAKY BUCKET                                               │
│                                                                 │
│     Requests ─┐    ┌────────────┐                             │
│               │    │   🪣       │    Processed at            │
│               └───►│  ● ● ●    │───► fixed rate              │
│                    │  ● ● ●    │                              │
│                    └────────────┘                              │
│                                                                 │
│  3. SLIDING WINDOW                                             │
│                                                                 │
│     Track requests in time window, reject if over limit        │
│                                                                 │
│     │──────────60 seconds──────────│                          │
│     │ req req req req req          │ (5 requests, limit = 10) │
│     │                              │ → ALLOW                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Chaos Engineering

### Principles

```
┌─────────────────────────────────────────────────────────────────┐
│              CHAOS ENGINEERING                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "Thoughtful, planned experiments to uncover system            │
│   weaknesses before they cause customer-facing issues"         │
│                                                                 │
│  PRINCIPLES:                                                   │
│  ──────────                                                    │
│  1. Build hypothesis around steady state                       │
│  2. Vary real-world events (failures, latency, etc.)          │
│  3. Run experiments in production                              │
│  4. Automate experiments to run continuously                   │
│  5. Minimize blast radius                                      │
│                                                                 │
│  NETFLIX CHAOS MONKEY:                                         │
│  • Randomly terminates instances in production                 │
│  • Runs during business hours                                  │
│  • Forces engineers to build resilient systems                │
│                                                                 │
│  SIMIAN ARMY:                                                  │
│  • Chaos Monkey: Kills instances                              │
│  • Latency Monkey: Adds network delays                        │
│  • Chaos Gorilla: Kills entire AZ                             │
│  • Chaos Kong: Kills entire region                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Interview Questions

### Conceptual Questions

**Q1: Explain the difference between crash failure and Byzantine failure.**

| Aspect | Crash Failure | Byzantine Failure |
|--------|--------------|-------------------|
| Behavior | Node stops completely | Node behaves arbitrarily |
| Detection | Easier (no response) | Harder (may lie) |
| Nodes needed | 2f+1 for f failures | 3f+1 for f failures |
| Examples | Power failure, crash | Bug, malicious actor |

**Q2: How does a circuit breaker improve system resilience?**

Circuit breaker prevents cascading failures by:
1. **Monitoring** failure rate to downstream service
2. **Opening** when failures exceed threshold (fail fast)
3. **Testing** periodically with limited requests (half-open)
4. **Closing** when downstream recovers

Benefits:
- Fails fast, doesn't waste resources
- Gives downstream time to recover
- Prevents resource exhaustion

**Q3: What's the difference between failover and failback?**

- **Failover**: Switching to backup when primary fails
- **Failback**: Returning to primary after it recovers

### Design Questions

**Q4: Design a fault-tolerant payment processing system.**

```
Architecture:
├── Idempotency keys (prevent duplicate charges)
├── Saga pattern (compensating transactions)
├── Multiple payment providers (fallback)
├── Circuit breakers per provider
├── At-least-once delivery with deduplication
├── Synchronous replication for critical data
└── Comprehensive audit logging
```

**Q5: How would you handle a thundering herd problem?**

Solutions:
1. **Exponential backoff with jitter**: Spread out retries
2. **Request coalescing**: Combine duplicate requests
3. **Cache stampede prevention**: Lock on cache miss
4. **Circuit breaker**: Limit concurrent requests
5. **Queue-based load leveling**: Buffer requests

---

## Summary

### Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│         FAULT TOLERANCE CHEAT SHEET                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FAILURE TYPES:                                                │
│  • Crash: Node stops                                           │
│  • Omission: Messages lost                                     │
│  • Timing: Response too slow                                   │
│  • Byzantine: Arbitrary behavior                               │
│                                                                 │
│  FAILURE DETECTION:                                            │
│  • Heartbeat (push/pull)                                       │
│  • Gossip protocol                                             │
│  • Phi accrual detector                                        │
│                                                                 │
│  RESILIENCE PATTERNS:                                          │
│  • Circuit breaker: Fail fast                                  │
│  • Bulkhead: Isolate failures                                  │
│  • Retry + backoff: Handle transient failures                 │
│  • Rate limiting: Prevent overload                            │
│                                                                 │
│  REDUNDANCY:                                                   │
│  • Cold standby: Cheapest, slowest recovery                   │
│  • Warm standby: Balance cost/recovery                        │
│  • Hot standby: Expensive, fastest recovery                   │
│                                                                 │
│  AVAILABILITY FORMULA:                                         │
│  • A = MTBF / (MTBF + MTTR)                                   │
│  • 99.9% = 8.76 hours downtime/year                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

