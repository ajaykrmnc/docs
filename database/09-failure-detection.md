# Chapter 9: Failure Detection

## Table of Contents
- [Introduction](#introduction)
- [Failure Models](#failure-models)
- [Heartbeat-Based Detection](#heartbeat-based-detection)
- [Timeout Strategies](#timeout-strategies)
- [Phi-Accrual Failure Detector](#phi-accrual-failure-detector)
- [Gossip Protocols](#gossip-protocols)
- [SWIM Protocol](#swim-protocol)
- [Summary](#summary)

---

## Introduction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FAILURE DETECTION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "In a distributed system, knowing whether a node has failed is            │
│   impossible to determine with certainty - we can only suspect."           │
│                                                                             │
│  THE FUNDAMENTAL PROBLEM                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Cannot distinguish between:                                          │  │
│  │                                                                       │  │
│  │  1. Node has crashed                                                  │  │
│  │  2. Network partition                                                 │  │
│  │  3. Node is very slow                                                 │  │
│  │  4. Network is very slow                                              │  │
│  │                                                                       │  │
│  │  ┌─────────────┐                    ┌─────────────┐                   │  │
│  │  │   Node A    │─ ─ ─ ─ ? ─ ─ ─ ─ ─ │   Node B    │                   │  │
│  │  │             │                    │ (crashed?)  │                   │  │
│  │  │  "Is B      │                    │ (slow?)     │                   │  │
│  │  │   alive?"   │                    │ (network?)  │                   │  │
│  │  └─────────────┘                    └─────────────┘                   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  WHY IT MATTERS                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Accurate failure detection is critical for:                          │  │
│  │                                                                       │  │
│  │  • Leader Election: Need to know when leader fails                    │  │
│  │  • Replication: Know when to failover to replica                      │  │
│  │  • Membership: Know which nodes are in the cluster                    │  │
│  │  • Load Balancing: Don't send requests to dead nodes                  │  │
│  │  • Garbage Collection: Clean up resources for failed nodes            │  │
│  │                                                                       │  │
│  │  Too Aggressive → False positives (unnecessary failovers)             │  │
│  │  Too Conservative → Slow detection (prolonged unavailability)         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FAILURE DETECTOR PROPERTIES                                                │
│  ═══════════════════════════                                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Completeness: Every crashed node is eventually suspected             │  │
│  │                                                                       │  │
│  │  Accuracy: No correct node is ever suspected                          │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Perfect Failure Detector: Both complete and accurate           │  │  │
│  │  │                            (IMPOSSIBLE in async systems)        │  │  │
│  │  │                                                                 │  │  │
│  │  │  Eventually Perfect (◇P): Eventually becomes accurate           │  │  │
│  │  │                                                                 │  │  │
│  │  │  In practice: Trade off between completeness and accuracy       │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Failure Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FAILURE MODELS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Different systems assume different failure behaviors:                       │
│                                                                             │
│  CRASH-STOP (Fail-Stop)                                                     │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Node crashes and never recovers                                      │  │
│  │                                                                       │  │
│  │  Time ─────────────────────────────────────────────────────────▶     │  │
│  │                                                                       │  │
│  │  Node:  ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░      │  │
│  │                                    ▲                                  │  │
│  │                                  Crash                                │  │
│  │                                (permanent)                            │  │
│  │                                                                       │  │
│  │  Assumptions:                                                         │  │
│  │  • Once failed, stays failed                                          │  │
│  │  • No Byzantine (malicious) behavior                                  │  │
│  │  • Simplest model to handle                                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  CRASH-RECOVERY (Fail-Recover)                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Node crashes but may recover                                         │  │
│  │                                                                       │  │
│  │  Time ─────────────────────────────────────────────────────────▶     │  │
│  │                                                                       │  │
│  │  Node:  ████████████░░░░░░░░░████████████░░░░░░████████████████      │  │
│  │                    ▲         ▲           ▲     ▲                      │  │
│  │                  Crash    Recover      Crash Recover                  │  │
│  │                                                                       │  │
│  │  Requirements:                                                        │  │
│  │  • Must handle transient failures                                     │  │
│  │  • Need stable storage for recovery                                   │  │
│  │  • Most realistic for practical systems                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  OMISSION FAILURES                                                          │
│  ═════════════════                                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Messages may be lost (send or receive omission)                      │  │
│  │                                                                       │  │
│  │  ┌─────────────┐       msg1        ┌─────────────┐                   │  │
│  │  │   Node A    │─────────────────▶│   Node B    │                   │  │
│  │  │             │       msg2   ✗    │             │                   │  │
│  │  │             │──────────────    │             │                   │  │
│  │  │             │       msg3        │             │                   │  │
│  │  │             │─────────────────▶│             │                   │  │
│  │  └─────────────┘                   └─────────────┘                   │  │
│  │                                                                       │  │
│  │  Types:                                                               │  │
│  │  • Send omission: Message not sent                                    │  │
│  │  • Receive omission: Message not received                             │  │
│  │  • General omission: Either                                           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  BYZANTINE FAILURES                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Node behaves arbitrarily (including maliciously)                     │  │
│  │                                                                       │  │
│  │  ┌─────────────┐                   ┌─────────────┐                   │  │
│  │  │   Node A    │───"value = 5"───▶│             │                   │  │
│  │  │ (Byzantine) │                   │   Node C    │                   │  │
│  │  │             │───"value = 7"───▶│             │                   │  │
│  │  └─────────────┘                   └─────────────┘                   │  │
│  │        │                                  ▲                          │  │
│  │        │                                  │                          │  │
│  │        └─────────────"value = 3"──────────┘                          │  │
│  │                                                                       │  │
│  │  Characteristics:                                                     │  │
│  │  • Can send conflicting messages                                      │  │
│  │  • Can lie about its state                                            │  │
│  │  • Can collude with other Byzantine nodes                             │  │
│  │  • Requires f < n/3 for tolerance (3f+1 nodes needed)                │  │
│  │                                                                       │  │
│  │  Used in: Blockchain, systems exposed to adversaries                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FAILURE MODEL COMPARISON                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌─────────────────┬────────────────────┬──────────────────────────────┐   │
│  │ Model           │ Behavior           │ Tolerance                    │   │
│  ├─────────────────┼────────────────────┼──────────────────────────────┤   │
│  │ Crash-Stop      │ Stop permanently   │ f < n/2 (majority needed)    │   │
│  │ Crash-Recovery  │ Crash and recover  │ f < n/2 with stable storage  │   │
│  │ Omission        │ Lose messages      │ f < n/2 (depends on type)    │   │
│  │ Byzantine       │ Arbitrary behavior │ f < n/3 (3f+1 nodes needed)  │   │
│  └─────────────────┴────────────────────┴──────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Heartbeat-Based Detection

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HEARTBEAT-BASED DETECTION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The most common approach: nodes periodically signal they're alive          │
│                                                                             │
│  PING-BASED (Pull Model)                                                    │
│  ═══════════════════════                                                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Monitor actively checks target nodes                                 │  │
│  │                                                                       │  │
│  │  ┌─────────────┐         ping          ┌─────────────┐               │  │
│  │  │   Monitor   │─────────────────────▶│   Node A    │               │  │
│  │  │             │◀─────────────────────│             │               │  │
│  │  │             │         pong          │             │               │  │
│  │  │             │                       └─────────────┘               │  │
│  │  │             │         ping          ┌─────────────┐               │  │
│  │  │             │─────────────────────▶│   Node B    │               │  │
│  │  │             │◀─────────────────────│             │               │  │
│  │  │             │         pong          │             │               │  │
│  │  └─────────────┘                       └─────────────┘               │  │
│  │                                                                       │  │
│  │  Pros: Centralized control, predictable timing                        │  │
│  │  Cons: Monitor is single point of failure, scalability issues         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HEARTBEAT-BASED (Push Model)                                               │
│  ════════════════════════════                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Nodes proactively send heartbeats                                    │  │
│  │                                                                       │  │
│  │  ┌─────────────┐                       ┌─────────────┐               │  │
│  │  │   Node A    │───── heartbeat ─────▶│             │               │  │
│  │  └─────────────┘                       │             │               │  │
│  │  ┌─────────────┐                       │   Monitor   │               │  │
│  │  │   Node B    │───── heartbeat ─────▶│             │               │  │
│  │  └─────────────┘                       │             │               │  │
│  │  ┌─────────────┐                       │             │               │  │
│  │  │   Node C    │───── heartbeat ─────▶│             │               │  │
│  │  └─────────────┘                       └─────────────┘               │  │
│  │                                                                       │  │
│  │  Heartbeat interval: Typically 1-10 seconds                           │  │
│  │  Failure threshold: Usually 3-5 missed heartbeats                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ALL-TO-ALL HEARTBEATS                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Every node sends heartbeats to every other node                      │  │
│  │                                                                       │  │
│  │         ┌─────────────┐                                               │  │
│  │         │   Node A    │                                               │  │
│  │         └──────┬──────┘                                               │  │
│  │           ╱    │    ╲                                                 │  │
│  │          ╱     │     ╲                                                │  │
│  │         ▼      ▼      ▼                                               │  │
│  │  ┌──────────┐     ┌──────────┐                                        │  │
│  │  │  Node B  │◀───▶│  Node C  │                                        │  │
│  │  └──────────┘     └──────────┘                                        │  │
│  │                                                                       │  │
│  │  Message complexity: O(n²) per interval                               │  │
│  │  Pros: Fast detection, no single point of failure                     │  │
│  │  Cons: Doesn't scale well (n² messages)                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Timeout Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIMEOUT STRATEGIES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Choosing the right timeout is critical for failure detection               │
│                                                                             │
│  FIXED TIMEOUT                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Simple approach: fail if no response within T seconds               │  │
│  │                                                                       │  │
│  │  Time ────────────────────────────────────────────────────────▶      │  │
│  │       │                           │                                   │  │
│  │       ├─────── Timeout = 5s ──────┤                                   │  │
│  │       │                           │                                   │  │
│  │  Send │                           │ No response                       │  │
│  │  ping │                           │ → Mark FAILED                     │  │
│  │       ▼                           ▼                                   │  │
│  │                                                                       │  │
│  │  Problem: Network latency varies!                                     │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Timeout too short → False positives (healthy nodes marked dead)│  │  │
│  │  │  Timeout too long  → Slow detection (dead nodes stay "alive")   │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ADAPTIVE TIMEOUT                                                           │
│  ════════════════                                                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Dynamically adjust timeout based on observed latency                 │  │
│  │                                                                       │  │
│  │  Algorithm (similar to TCP):                                          │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  For each response:                                             │  │  │
│  │  │    RTT = measured round-trip time                               │  │  │
│  │  │    SRTT = α × SRTT + (1-α) × RTT        (smoothed RTT)         │  │  │
│  │  │    RTTVAR = β × RTTVAR + (1-β) × |RTT - SRTT|  (variance)      │  │  │
│  │  │                                                                 │  │  │
│  │  │  Timeout = SRTT + 4 × RTTVAR                                    │  │  │
│  │  │                                                                 │  │  │
│  │  │  Typical values: α = 0.875, β = 0.75                           │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Example:                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  RTT samples: 10ms, 12ms, 15ms, 11ms, 50ms, 13ms               │  │  │
│  │  │                                                                 │  │  │
│  │  │  SRTT ≈ 15ms (smoothed average)                                │  │  │
│  │  │  RTTVAR ≈ 8ms (variance captures spike)                        │  │  │
│  │  │  Timeout = 15 + 4×8 = 47ms                                      │  │  │
│  │  │                                                                 │  │  │
│  │  │  Adapts to network conditions automatically                     │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phi-Accrual Failure Detector

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHI-ACCRUAL FAILURE DETECTOR                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Instead of binary (alive/dead), provides a suspicion level                 │
│                                                                             │
│  THE PROBLEM WITH BINARY DETECTION                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Traditional: alive ──────────────────▶ dead                         │  │
│  │                        (single threshold)                             │  │
│  │                                                                       │  │
│  │  Problem: Different applications need different tradeoffs             │  │
│  │                                                                       │  │
│  │  • Real-time game: Want fast detection, accept false positives        │  │
│  │  • Banking system: Prefer slow detection, avoid false positives       │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PHI (φ) ACCRUAL APPROACH                                                   │
│  ════════════════════════                                                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Output: Suspicion level (φ) instead of binary                        │  │
│  │                                                                       │  │
│  │  φ = -log₁₀(P(node is alive | time since last heartbeat))            │  │
│  │                                                                       │  │
│  │  Interpretation:                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  φ = 1  →  10% chance of mistake (node probably alive)          │  │  │
│  │  │  φ = 2  →   1% chance of mistake                                │  │  │
│  │  │  φ = 3  →  0.1% chance of mistake                               │  │  │
│  │  │  φ = 8  →  0.000001% chance (node almost certainly dead)        │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Application chooses threshold based on its needs!                    │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  HOW PHI IS CALCULATED                                                      │
│  ═════════════════════                                                      │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Maintain a sliding window of inter-arrival times                  │  │
│  │                                                                       │  │
│  │     Heartbeats:  ──●────●─────●───●────────●──────●──                │  │
│  │     Intervals:      T1   T2    T3   T4      T5                        │  │
│  │                                                                       │  │
│  │  2. Assume normal distribution of arrival times                       │  │
│  │                                                                       │  │
│  │     Mean (μ) = average of intervals                                   │  │
│  │     Variance (σ²) = variance of intervals                             │  │
│  │                                                                       │  │
│  │  3. Calculate probability that next heartbeat is late                 │  │
│  │                                                                       │  │
│  │     t_now = time since last heartbeat                                 │  │
│  │     P(late) = P(next > t_now) = 1 - CDF(t_now)                       │  │
│  │                                                                       │  │
│  │  4. Convert to φ                                                      │  │
│  │                                                                       │  │
│  │     φ = -log₁₀(P(late))                                              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  VISUALIZATION                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  φ                                                                    │  │
│  │  ▲                                                                    │  │
│  │  │                                              ╱                     │  │
│  │  │                                            ╱                       │  │
│  │  8├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╱─ ─ Very suspicious      │  │
│  │  │                                       ╱                            │  │
│  │  │                                     ╱                              │  │
│  │  │                                   ╱                                │  │
│  │  4├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╱─ ─ ─ ─ Somewhat suspicious       │  │
│  │  │                              ╱                                     │  │
│  │  │                           ╱                                        │  │
│  │  │                        ╱                                           │  │
│  │  1├─ ─ ─ ─ ─ ─ ─ ─ ─ ─╱─ ─ ─ ─ ─ ─ ─ ─ ─ Probably alive             │  │
│  │  │               ╱╱                                                   │  │
│  │  │          ╱╱╱                                                       │  │
│  │  └──────────────────────────────────────────────▶ Time since HB      │  │
│  │                                                                       │  │
│  │  Used by: Cassandra, Akka                                             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Gossip Protocols

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GOSSIP PROTOCOLS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Also called "epidemic protocols" - information spreads like a rumor        │
│                                                                             │
│  BASIC GOSSIP                                                               │
│  ════════════                                                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each round, every node:                                              │  │
│  │  1. Selects k random peers (fanout)                                   │  │
│  │  2. Sends its current state to them                                   │  │
│  │  3. Merges received state with local state                            │  │
│  │                                                                       │  │
│  │  Round 1:          Round 2:          Round 3:                         │  │
│  │                                                                       │  │
│  │    ●───────●         ●───────●         ●───────●                      │  │
│  │    │ INFO  │         │       │         │       │                      │  │
│  │    │       │         │       │         │       │                      │  │
│  │    ●       ●         ●───────●         ●───────●                      │  │
│  │                      │ INFO            │ INFO  │                      │  │
│  │    ●       ●         ●       ●         ●───────●                      │  │
│  │                              INFO              INFO                   │  │
│  │                                                                       │  │
│  │  Information reaches all nodes in O(log n) rounds                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FAILURE DETECTION WITH GOSSIP                                              │
│  ═════════════════════════════                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each node maintains:                                                 │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │ Node  │ Heartbeat Counter │ Local Timestamp │ Status         │   │  │
│  │  ├───────┼───────────────────┼─────────────────┼────────────────┤   │  │
│  │  │ A     │ 105               │ 12:00:01        │ ALIVE          │   │  │
│  │  │ B     │ 203               │ 12:00:02        │ ALIVE          │   │  │
│  │  │ C     │ 87                │ 11:59:50        │ SUSPECTED      │   │  │
│  │  │ D     │ 156               │ 12:00:00        │ ALIVE          │   │  │
│  │  └───────┴───────────────────┴─────────────────┴────────────────┘   │  │
│  │                                                                       │  │
│  │  Rules:                                                               │  │
│  │  • Each node increments its own heartbeat counter                     │  │
│  │  • Gossip exchanges membership lists                                  │  │
│  │  • If heartbeat doesn't increase for T seconds → suspect             │  │
│  │  • If suspected for T_fail seconds → mark as failed                  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  PROPERTIES                                                                 │
│  ══════════                                                                 │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ✓ Scalable: O(n × k) messages per round (k = fanout, usually 2-4)   │  │
│  │  ✓ Fault-tolerant: No single point of failure                        │  │
│  │  ✓ Eventually consistent: All nodes converge                         │  │
│  │                                                                       │  │
│  │  ✗ Probabilistic: Not guaranteed deterministic behavior              │  │
│  │  ✗ Convergence time varies                                           │  │
│  │                                                                       │  │
│  │  Used by: Cassandra, Riak, Consul, Serf                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SWIM Protocol

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SWIM PROTOCOL                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Scalable Weakly-consistent Infection-style Membership                       │
│  Efficient failure detection + dissemination                                 │
│                                                                             │
│  THE PROBLEM WITH BASIC APPROACHES                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  All-to-all heartbeats:  O(n²) messages → doesn't scale              │  │
│  │  Basic gossip:           Slow failure detection                       │  │
│  │                                                                       │  │
│  │  SWIM combines: Direct probing + Indirect probing + Gossip           │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SWIM FAILURE DETECTION                                                     │
│  ══════════════════════                                                     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Each protocol period, node Mi:                                       │  │
│  │                                                                       │  │
│  │  Step 1: Direct Probe                                                 │  │
│  │  ──────────────────────                                               │  │
│  │                                                                       │  │
│  │  Mi ─────── ping ──────▶ Mj (randomly selected)                      │  │
│  │  Mi ◀────── ack ─────── Mj                                           │  │
│  │                                                                       │  │
│  │  If ack received → Mj is alive, done                                  │  │
│  │                                                                       │  │
│  │  Step 2: Indirect Probe (if direct fails)                             │  │
│  │  ────────────────────────────────────────                             │  │
│  │                                                                       │  │
│  │  ┌─────┐                ┌─────┐                ┌─────┐               │  │
│  │  │ Mi  │──ping-req(Mj)─▶│ Mk₁ │────ping────▶│ Mj  │               │  │
│  │  │     │                │     │◀────ack─────│     │               │  │
│  │  │     │◀─────ack──────│     │                │     │               │  │
│  │  └─────┘                └─────┘                └─────┘               │  │
│  │     │                   ┌─────┐                  ▲                   │  │
│  │     └───ping-req(Mj)──▶│ Mk₂ │────ping──────────┘                   │  │
│  │                         └─────┘                                       │  │
│  │                                                                       │  │
│  │  If any indirect probe returns ack → Mj is alive                      │  │
│  │  If all fail → Mj is suspected                                        │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SWIM DISSEMINATION                                                         │
│  ══════════════════                                                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Piggyback membership updates on ping/ack messages                    │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                 │  │  │
│  │  │  Ping/Ack message:                                              │  │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐   │  │  │
│  │  │  │ Probe Data │ Membership Update 1 │ Membership Update 2  │   │  │  │
│  │  │  │            │ (Node X failed)     │ (Node Y joined)      │   │  │  │
│  │  │  └─────────────────────────────────────────────────────────┘   │  │  │
│  │  │                                                                 │  │  │
│  │  │  No extra messages needed for dissemination!                    │  │  │
│  │  │                                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Infection-style: Each update piggybacked λ×log(n) times             │  │
│  │  Then dropped (infection count exhausted)                             │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SWIM PROPERTIES                                                            │
│  ═══════════════                                                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Property              │ Value                                  │  │  │
│  │  ├───────────────────────┼────────────────────────────────────────┤  │  │
│  │  │ Message complexity    │ O(n) per period (constant per member)  │  │  │
│  │  │ Detection time        │ O(log n) expected                      │  │  │
│  │  │ False positive rate   │ Tunable via timeout                    │  │  │
│  │  │ Dissemination time    │ O(log n) protocol periods              │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  Compared to all-to-all heartbeats:                                   │  │
│  │  • 1000 nodes: 1M msgs/period → 1K msgs/period (1000x reduction)     │  │
│  │                                                                       │  │
│  │  Used by: HashiCorp Serf, Consul, Memberlist                          │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHAPTER 9 SUMMARY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FAILURE DETECTION FUNDAMENTALS                                             │
│  ══════════════════════════════                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Core Challenge: Cannot distinguish crash from slow/partitioned       │  │
│  │                                                                       │  │
│  │  Properties:                                                          │  │
│  │  • Completeness: Eventually suspect all failed nodes                  │  │
│  │  • Accuracy: Don't suspect healthy nodes                              │  │
│  │                                                                       │  │
│  │  Trade-off: Fast detection ←→ Few false positives                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  FAILURE MODELS                                                             │
│  ══════════════                                                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  Crash-Stop:     Node fails permanently                               │  │
│  │  Crash-Recovery: Node fails and may recover                           │  │
│  │  Omission:       Messages may be lost                                 │  │
│  │  Byzantine:      Arbitrary (malicious) behavior                       │  │
│  │                                                                       │  │
│  │  Most systems assume crash-stop or crash-recovery                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  DETECTION APPROACHES                                                       │
│  ════════════════════                                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Heartbeats                                                        │  │
│  │     • Pull (ping): Monitor checks nodes                               │  │
│  │     • Push: Nodes send periodic signals                               │  │
│  │     • All-to-all: O(n²) messages                                      │  │
│  │                                                                       │  │
│  │  2. Timeouts                                                          │  │
│  │     • Fixed: Simple but inflexible                                    │  │
│  │     • Adaptive: Adjusts based on network conditions                   │  │
│  │                                                                       │  │
│  │  3. Phi-Accrual                                                       │  │
│  │     • Outputs suspicion level instead of binary                       │  │
│  │     • Application chooses threshold                                   │  │
│  │     • Used by Cassandra, Akka                                         │  │
│  │                                                                       │  │
│  │  4. Gossip-based                                                      │  │
│  │     • Scalable O(n × k) messages                                      │  │
│  │     • Information spreads epidemically                                │  │
│  │     • Eventually consistent                                           │  │
│  │                                                                       │  │
│  │  5. SWIM Protocol                                                     │  │
│  │     • Direct + indirect probing                                       │  │
│  │     • Piggyback dissemination                                         │  │
│  │     • O(n) messages, O(log n) detection                               │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  KEY TAKEAWAYS                                                              │
│  ═════════════                                                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  1. Perfect failure detection is impossible in async systems          │  │
│  │  2. Choose detection speed vs accuracy based on application needs     │  │
│  │  3. Use adaptive timeouts to handle varying network conditions        │  │
│  │  4. Gossip and SWIM scale well for large clusters                     │  │
│  │  5. Consider using suspicion levels (phi-accrual) for flexibility     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Next Chapter: [Chapter 10: Leader Election](./10-leader-election.md)**

**Previous Chapter: [Chapter 8: Distributed Systems Introduction](./08-distributed-systems-intro.md)**