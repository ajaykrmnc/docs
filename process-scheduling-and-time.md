# Process Scheduling and Time

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** CPU Scheduling, Time Management, Scheduler Algorithms, and Real-Time Systems

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [What is Process Scheduling?](#what-is-process-scheduling)
   - [The Scheduling Problem](#the-scheduling-problem)
   - [Historical Context](#historical-context)

2. [Scheduling Fundamentals](#2-scheduling-fundamentals)
   - [CPU-Bound vs I/O-Bound Processes](#cpu-bound-vs-io-bound-processes)
   - [Preemptive vs Non-Preemptive Scheduling](#preemptive-vs-non-preemptive-scheduling)
   - [Scheduling Criteria](#scheduling-criteria)
   - [The Dispatcher](#the-dispatcher)

3. [Process Priorities](#3-process-priorities)
   - [Priority Calculation in Traditional Unix](#priority-calculation-in-traditional-unix)
   - [The nice Value](#the-nice-value)
   - [Dynamic Priority Adjustment](#dynamic-priority-adjustment)
   - [Priority Inversion](#priority-inversion)

4. [The Traditional Unix Scheduler](#4-the-traditional-unix-scheduler)
   - [Multilevel Feedback Queues](#multilevel-feedback-queues)
   - [The Scheduling Algorithm](#the-scheduling-algorithm)
   - [Kernel Algorithm for Scheduling](#kernel-algorithm-for-scheduling)
   - [Context Switching](#context-switching)

5. [Time in Unix](#5-time-in-unix)
   - [Hardware Clocks](#hardware-clocks)
   - [The Clock Interrupt](#the-clock-interrupt)
   - [System Time vs Process Time](#system-time-vs-process-time)
   - [Time-of-Day Clock](#time-of-day-clock)

6. [The Clock Handler](#6-the-clock-handler)
   - [Clock Interrupt Processing](#clock-interrupt-processing)
   - [Kernel Algorithm for Clock Handler](#kernel-algorithm-for-clock-handler)
   - [Callouts and Timeouts](#callouts-and-timeouts)
   - [Profiling](#profiling)

7. [Interval Timers](#7-interval-timers)
   - [The setitimer() System Call](#the-setitimer-system-call)
   - [ITIMER_REAL, ITIMER_VIRTUAL, ITIMER_PROF](#itimer_real-itimer_virtual-itimer_prof)
   - [The alarm() System Call](#the-alarm-system-call)
   - [High-Resolution Timers](#high-resolution-timers)

8. [Sleep and Wakeup](#8-sleep-and-wakeup)
   - [The sleep() Mechanism](#the-sleep-mechanism)
   - [Sleep Queues and Wait Channels](#sleep-queues-and-wait-channels)
   - [Kernel Algorithm for Sleep](#kernel-algorithm-for-sleep)
   - [Wakeup and Thundering Herd](#wakeup-and-thundering-herd)

9. [Modern Linux Schedulers](#9-modern-linux-schedulers)
   - [The O(1) Scheduler](#the-o1-scheduler)
   - [The Completely Fair Scheduler (CFS)](#the-completely-fair-scheduler-cfs)
   - [Red-Black Trees and Virtual Runtime](#red-black-trees-and-virtual-runtime)
   - [Scheduling Classes](#scheduling-classes)

10. [Real-Time Scheduling](#10-real-time-scheduling)
    - [Hard vs Soft Real-Time](#hard-vs-soft-real-time)
    - [SCHED_FIFO and SCHED_RR](#sched_fifo-and-sched_rr)
    - [SCHED_DEADLINE](#sched_deadline)
    - [Real-Time Priority Levels](#real-time-priority-levels)

11. [Multiprocessor Scheduling](#11-multiprocessor-scheduling)
    - [SMP Scheduling Challenges](#smp-scheduling-challenges)
    - [CPU Affinity](#cpu-affinity)
    - [Load Balancing](#load-balancing)
    - [NUMA Considerations](#numa-considerations)

12. [Summary and Appendix](#12-summary-and-appendix)
    - [Scheduling System Calls Quick Reference](#scheduling-system-calls-quick-reference)
    - [Time System Calls Quick Reference](#time-system-calls-quick-reference)
    - [The Big Picture](#the-big-picture)

13. [References](#13-references)

---

## 1. Introduction

### What is Process Scheduling?

Process scheduling is the mechanism by which the operating system decides which process runs on the CPU at any given moment. In a multiprogramming environment where multiple processes compete for the CPU, the scheduler acts as the arbiter, ensuring fair and efficient use of this precious resource.

Maurice Bach describes scheduling as:

> "The scheduler is the component of the kernel that selects which process should run next. The scheduler must balance the competing goals of response time, throughput, and fairness while ensuring that no process starves."

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SCHEDULING PROBLEM                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   GIVEN:                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A ────────────────────────────────────────────────────    │ │
│   │   Process B ────────────────────────────────────────────────────    │ │
│   │   Process C ────────────────────────────────────────────────────    │ │
│   │   Process D ────────────────────────────────────────────────────    │ │
│   │   Process E ────────────────────────────────────────────────────    │ │
│   │                                                                      │ │
│   │   All want to run, but there's only ONE CPU!                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE SCHEDULER MUST DECIDE:                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │



The illusion of simultaneous execution is created by rapidly switching between processes:

```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE ILLUSION OF MULTITASKING                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   REALITY (Single CPU):                                                   │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Time:  0    10   20   30   40   50   60   70   80   90   100 ms        │
│          │    │    │    │    │    │    │    │    │    │    │             │
│   CPU:   ├─A──┼─B──┼─A──┼─C──┼─A──┼─B──┼─C──┼─A──┼─B──┼─C──┤             │
│          │    │    │    │    │    │    │    │    │    │    │             │
│                                                                            │
│   Each process gets a "time slice" (quantum) of CPU time                  │
│                                                                            │
│                                                                            │
│   PERCEPTION (From each process's view):                                  │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Process A thinks: "I'm running continuously!"                           │
│   Process B thinks: "I'm running continuously!"                           │
│   Process C thinks: "I'm running continuously!"                           │
│                                                                            │
│   (Just slower than if they had the CPU to themselves)                   │
│                                                                            │
│                                                                            │
│   THE MAGIC:                                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   • Context switches happen so fast (microseconds) that humans           │
│     perceive all processes as running simultaneously                      │
│                                                                            │
│   • The scheduler makes ~100-1000 decisions per second                   │
│                                                                            │
│   • Each process is unaware it's being interrupted                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Scheduling Problem

The scheduler must balance multiple competing objectives:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING OBJECTIVES                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   FAIRNESS ◄─────────────────────────────────────────► PRIORITY    │ │
│   │                                                                      │ │
│   │   "Every process should      vs    "Important processes            │ │
│   │    get its fair share"              should run first"              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   THROUGHPUT ◄───────────────────────────────────► RESPONSE TIME   │ │
│   │                                                                      │ │
│   │   "Maximize total work       vs    "Minimize time to               │ │
│   │    completed per unit time"         first response"                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   EFFICIENCY ◄───────────────────────────────────► PREDICTABILITY  │ │
│   │                                                                      │ │
│   │   "Minimize scheduler        vs    "Guarantee timing               │ │
│   │    overhead"                        constraints"                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THE FUNDAMENTAL TRADEOFFS:                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   1. Short time slices → Better response time, but more overhead         │
│   2. Long time slices  → Better throughput, but worse response time      │
│   3. Strict priorities → Fast important tasks, but possible starvation   │
│   4. Pure fairness     → No starvation, but no priority                  │
│                                                                            │
│   There is NO perfect scheduler - only tradeoffs appropriate for         │
│   the workload!                                                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

The evolution of process scheduling reflects the changing nature of computing:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF SCHEDULING                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1950s: BATCH PROCESSING                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│   • No scheduling needed - one job at a time                             │
│   • Jobs submitted on punch cards                                         │
│   • Run to completion, then next job                                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Job 1 ──────────────────────────────────────────────────────────  │ │
│   │                                          Job 2 ───────────────────  │ │
│   │                                                         Job 3 ────  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   1960s: MULTIPROGRAMMING                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Multiple jobs in memory simultaneously                               │
│   • When one job waits for I/O, run another                              │
│   • First schedulers: simple priority queues                             │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Job 1 ────────┐         ┌────────────┐         ┌────────────────  │ │
│   │                 │ (I/O)   │            │ (I/O)   │                  │ │
│   │   Job 2         └─────────┘            └─────────┘                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   1970s: TIME-SHARING (Unix)                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Interactive users at terminals                                        │
│   • Round-robin with priorities                                           │
│   • Preemptive multitasking                                               │
│   • The birth of the Unix scheduler                                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   User 1 ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─  │ │
│   │   User 2 ─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─  │ │
│   │   (Rapid switching creates illusion of simultaneous access)         │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   1990s-2000s: SMP AND REAL-TIME                                          │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Multiple CPUs require load balancing                                  │
│   • Real-time constraints for multimedia                                  │
│   • O(1) scheduler (Linux 2.6)                                            │
│   • Completely Fair Scheduler (Linux 2.6.23)                              │
│                                                                            │
│                                                                            │
│   2010s-Present: HETEROGENEOUS AND POWER-AWARE                           │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Big.LITTLE architectures (fast + efficient cores)                    │
│   • Energy-aware scheduling                                               │
│   • Container and VM scheduling                                           │
│   • NUMA-aware scheduling                                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Scheduling Fundamentals

### CPU-Bound vs I/O-Bound Processes

Understanding process behavior is crucial for effective scheduling:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CPU-BOUND vs I/O-BOUND PROCESSES                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CPU-BOUND PROCESS:                                                       │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Spends most time computing                                            │
│   • Rarely blocks for I/O                                                 │
│   • Examples: video encoding, scientific computation, compilation        │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────►   │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │████████████████████████████████████████████████████████████████│   │
│   │                        CPU USAGE                                │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   Wants: Long time slices, minimal context switches                      │
│                                                                            │
│                                                                            │
│   I/O-BOUND PROCESS:                                                       │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Spends most time waiting for I/O                                      │
│   • Short CPU bursts between I/O operations                              │
│   • Examples: text editor, shell, web server                             │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────►   │
│                                                                            │
│   ┌──┐    ┌──┐    ┌──┐    ┌──┐    ┌──┐    ┌──┐    ┌──┐    ┌──┐         │
│   │██│    │██│    │██│    │██│    │██│    │██│    │██│    │██│         │
│   └──┘    └──┘    └──┘    └──┘    └──┘    └──┘    └──┘    └──┘         │
│      ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼          │
│    (I/O)   (I/O)   (I/O)   (I/O)   (I/O)   (I/O)   (I/O)   (I/O)        │
│                                                                            │
│   Wants: Quick response when ready, doesn't need long slices            │
│                                                                            │
│                                                                            │
│   MIXED WORKLOAD (Reality):                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Most systems have BOTH types running simultaneously.                   │
│   The scheduler must favor I/O-bound processes for responsiveness       │
│   while ensuring CPU-bound processes make progress.                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Preemptive vs Non-Preemptive Scheduling

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PREEMPTIVE vs NON-PREEMPTIVE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NON-PREEMPTIVE (Cooperative):                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Process runs until it:                                                  │
│   • Voluntarily yields the CPU                                            │
│   • Blocks for I/O                                                        │
│   • Terminates                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A ─────────────────────────────────────────────────────►  │ │
│   │                                                    │                 │ │
│   │                                                    │ "I'm done,     │ │
│   │                                                    │  you can run"  │ │
│   │                                                    ▼                 │ │
│   │   Process B                                        ─────────────►   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Problem: A malicious or buggy process can hog the CPU forever!         │
│                                                                            │
│                                                                            │
│   PREEMPTIVE:                                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   The kernel can FORCIBLY take the CPU away from a process:              │
│   • When time slice expires                                               │
│   • When higher priority process becomes ready                           │
│   • On return from interrupt/system call                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A ──────────┐                    ┌──────────┐             │ │
│   │                       │ PREEMPTED!         │          │             │ │
│   │                       ▼                    │          ▼             │ │
│   │   Process B           ──────────────────────          ──────────►  │ │
│   │                                                                      │ │
│   │   (Kernel forces context switch when time slice expires)            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Unix/Linux: PREEMPTIVE in user mode, traditionally non-preemptive     │
│               in kernel mode (changed in modern kernels)                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Scheduling Criteria

Different metrics for evaluating scheduler performance:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING METRICS                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process arrives ──► Starts running ──► Completes                  │ │
│   │        │                    │                 │                      │ │
│   │        │◄── Wait Time ────►│                 │                      │ │
│   │        │                    │◄─ Burst Time ─►│                      │ │
│   │        │◄────────── Turnaround Time ────────►│                      │ │
│   │        │◄─ Response ─►│                                              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   METRIC DEFINITIONS:                                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ Metric             │ Definition                                     │ │
│   ├────────────────────┼────────────────────────────────────────────────┤ │
│   │ CPU Utilization    │ % of time CPU is busy (goal: 40-90%)          │ │
│   │ Throughput         │ Processes completed per unit time             │ │
│   │ Turnaround Time    │ Total time from submission to completion      │ │
│   │ Waiting Time       │ Time spent in ready queue                     │ │
│   │ Response Time      │ Time from submission to first response        │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   OPTIMIZATION GOALS BY SYSTEM TYPE:                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Batch Systems:                                                          │
│   • Maximize throughput                                                   │
│   • Maximize CPU utilization                                              │
│   • Minimize turnaround time                                              │
│                                                                            │
│   Interactive Systems (Desktop):                                          │
│   • Minimize response time                                                │
│   • Proportionality (meet user expectations)                             │
│                                                                            │
│   Real-Time Systems:                                                       │
│   • Meet deadlines                                                        │
│   • Predictability                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Dispatcher

The dispatcher is the component that actually performs the context switch:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE DISPATCHER                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The SCHEDULER decides WHICH process to run next.                        │
│   The DISPATCHER actually SWITCHES to that process.                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌──────────────┐                      ┌──────────────┐            │ │
│   │   │  SCHEDULER   │                      │  DISPATCHER  │            │ │
│   │   │              │                      │              │            │ │
│   │   │  "Process B  │ ──────────────────► │  "Okay, I'll │            │ │
│   │   │   should run │                      │   switch to  │            │ │
│   │   │   next"      │                      │   Process B" │            │ │
│   │   │              │                      │              │            │ │
│   │   └──────────────┘                      └──────────────┘            │ │
│   │                                                │                     │ │
│   │                                                ▼                     │ │
│   │                                    ┌───────────────────────┐        │ │
│   │                                    │ 1. Save state of A    │        │ │
│   │                                    │ 2. Load state of B    │        │ │
│   │                                    │ 3. Jump to B's code   │        │ │
│   │                                    └───────────────────────┘        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   DISPATCH LATENCY:                                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Time from scheduler decision to process actually running:              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Scheduler  ──► Save ──► Restore ──► Mode ──► Jump to             │ │
│   │   Decision       Regs      Regs       Switch    User Code           │ │
│   │                                                                      │ │
│   │   │◄──────────── Dispatch Latency ──────────────►│                  │ │
│   │                                                                      │ │
│   │   Typical: 1-10 microseconds on modern systems                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Process Priorities

### Priority Calculation in Traditional Unix

In traditional Unix, process priority is a dynamic value that changes based on process behavior:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX PRIORITY SYSTEM                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PRIORITY NUMBER CONVENTION:                                             │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   In traditional Unix: LOWER number = HIGHER priority                    │
│                                                                            │
│   Priority:  0 ◄─────────────────────────────────────────────────► 127   │
│              │                                                       │    │
│              │                                                       │    │
│           HIGHEST                                                 LOWEST  │
│           (runs first)                                      (runs last)   │
│                                                                            │
│                                                                            │
│   PRIORITY RANGES (Traditional Unix):                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   0-49:   KERNEL PRIORITIES (sleeping in kernel)                   │ │
│   │           ├── 0-19:  Swapper, disk I/O                             │ │
│   │           ├── 20-24: Disk buffer                                    │ │
│   │           ├── 25-29: Terminal I/O                                   │ │
│   │           └── 30-49: Other kernel waits                            │ │
│   │                                                                      │ │
│   │   50-127: USER PRIORITIES                                           │ │
│   │           ├── 50:    Base user priority                            │ │
│   │           └── 127:   Lowest priority                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THE PRIORITY FORMULA (Bach):                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   priority = cpu_usage + base_priority + nice_value                      │
│                                                                            │
│   Where:                                                                   │
│   • cpu_usage:     Recent CPU consumption (decays over time)             │
│   • base_priority: Starting priority (usually 50 for user processes)    │
│   • nice_value:    User-adjustable (-20 to +19)                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The nice Value

The `nice` value allows users to voluntarily lower their process priority:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE NICE VALUE                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   "nice" = How NICE you are to other users                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   nice value:  -20 ◄────────────────────────────────────────► +19  │ │
│   │                 │                    │                          │   │ │
│   │                 │                    │                          │   │ │
│   │              SELFISH              NORMAL                    NICE    │ │
│   │           (high priority)     (default = 0)          (low priority) │ │
│   │                                                                      │ │
│   │   Only root can set negative nice values (be "not nice")           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SYSTEM CALLS:                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   nice(increment)     - Add to current nice value                        │
│   getpriority(which, who) - Get nice value                               │
│   setpriority(which, who, prio) - Set nice value                         │
│                                                                            │
│                                                                            │
│   COMMAND LINE:                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   $ nice -n 10 ./my_program    # Start with nice +10                     │
│   $ renice -n 5 -p 1234        # Change PID 1234 to nice +5              │
│   $ sudo nice -n -10 ./urgent  # Start with nice -10 (needs root)        │
│                                                                            │
│                                                                            │
│   EXAMPLE SCENARIO:                                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A: nice = 0   (normal)                                    │ │
│   │   Process B: nice = 10  (background compilation)                    │ │
│   │   Process C: nice = -5  (important server, root-owned)              │ │
│   │                                                                      │ │
│   │   CPU allocation (approximately):                                   │ │
│   │                                                                      │ │
│   │   C: ████████████████████████████████████  (most CPU)              │ │
│   │   A: ████████████████████                  (normal share)           │ │
│   │   B: ████████                              (least CPU)              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Dynamic Priority Adjustment

The kernel recalculates process priorities periodically to ensure fairness:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DYNAMIC PRIORITY ADJUSTMENT                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHY DYNAMIC PRIORITIES?                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Problem: A CPU-bound process would run forever if priority was static   │
│                                                                            │
│   Solution: The more CPU a process uses, the WORSE its priority becomes   │
│             (priority number increases = lower priority)                  │
│                                                                            │
│                                                                            │
│   CPU USAGE DECAY:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Every clock tick (typically 10ms or 100Hz):                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   if (current_process is in user mode)                              │ │
│   │       current_process->p_cpu++;    /* Increment CPU usage */        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Every second (on clock interrupt):                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   for each process:                                                  │ │
│   │       p_cpu = p_cpu * decay_factor;  /* Typically decay/2 */        │ │
│   │       priority = p_cpu/4 + base_priority + nice;                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   VISUALIZATION OF CPU DECAY:                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   p_cpu                                                                    │
│     ▲                                                                      │
│   100│    ┌───┐                                                            │
│     │    │   │                                                             │
│    75│    │   └───┐                                                        │
│     │    │       │                                                         │
│    50│    │       └───┐                                                    │
│     │    │           │                                                     │
│    25│    │           └───┐                                                │
│     │    │               └───┐                                             │
│     0└───┴───────────────────└─────────────────────▶ Time (seconds)       │
│         Running   Sleeping (CPU usage decays exponentially)               │
│                                                                            │
│                                                                            │
│   EFFECT ON SCHEDULING:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CPU-Bound Process:                                                 │ │
│   │   ───────────────────                                                │ │
│   │   • Uses lots of CPU → p_cpu grows                                  │ │
│   │   • Priority number increases (gets worse)                          │ │
│   │   • Eventually preempted by other processes                         │ │
│   │   • While sleeping/waiting: p_cpu decays → priority improves        │ │
│   │                                                                      │ │
│   │   I/O-Bound Process:                                                 │ │
│   │   ──────────────────                                                 │ │
│   │   • Frequently blocks for I/O → p_cpu stays low                     │ │
│   │   • Priority remains good (low number)                              │ │
│   │   • Gets CPU quickly when I/O completes                             │ │
│   │   • Results in good interactive response                            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Priority Inversion

A classic scheduling problem that can cause system hangs:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PRIORITY INVERSION                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   A HIGH priority task is blocked by a LOW priority task, while a        │
│   MEDIUM priority task runs instead.                                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Three processes:                                                   │ │
│   │   • H (High priority)   - needs a lock                              │ │
│   │   • M (Medium priority) - CPU-bound, no locks needed                │ │
│   │   • L (Low priority)    - holds the lock H needs                    │ │
│   │                                                                      │ │
│   │   Time ─────────────────────────────────────────────────────────►   │ │
│   │                                                                      │ │
│   │   L: ████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │
│   │            ▲        │                                                │ │
│   │            │        │  L is preempted by M (not by H!)              │ │
│   │       L acquires    │                                                │ │
│   │       lock          ▼                                                │ │
│   │   M:                ████████████████████████████████████████████████ │ │
│   │                     ▲                                                │ │
│   │                     │  M runs forever, L can't release lock!        │ │
│   │                                                                      │ │
│   │   H:            ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│   │             ▲   │                                                    │ │
│   │        H wakes, │  H is BLOCKED waiting for lock held by L          │ │
│   │        needs    │  But L can't run because M has higher priority!   │ │
│   │        lock     │                                                    │ │
│   │                                                                      │ │
│   │   ████ = Running    ░░░░ = Blocked/Waiting                          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Result: HIGH priority task H is effectively stuck at LOW priority!     │
│                                                                            │
│                                                                            │
│   REAL-WORLD EXAMPLE: Mars Pathfinder (1997)                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   The Mars Pathfinder spacecraft experienced repeated system resets      │
│   due to priority inversion between the bus management task and         │
│   meteorological data gathering task.                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

Solutions to Priority Inversion:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SOLUTIONS TO PRIORITY INVERSION                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. PRIORITY INHERITANCE:                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   When H blocks on a lock held by L, temporarily RAISE L's priority      │
│   to match H's priority.                                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Before:  L has priority 100 (low)                                 │ │
│   │            H has priority 10  (high), blocks on L's lock            │ │
│   │                                                                      │ │
│   │   After:   L inherits priority 10 from H                            │ │
│   │            L can now preempt M                                       │ │
│   │            L releases lock → L returns to priority 100              │ │
│   │            H acquires lock and runs                                  │ │
│   │                                                                      │ │
│   │   Time ─────────────────────────────────────────────────────────►   │ │
│   │                                                                      │ │
│   │   L: ██████████████████████████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒          │ │
│   │                  ▲                   ▲    ▲                          │ │
│   │        L acquires lock       L inherits   L releases lock           │ │
│   │                              H's priority                            │ │
│   │                                                                      │ │
│   │   H:                                       ██████████████████████   │ │
│   │                                            ▲                         │ │
│   │                                       H gets lock, runs              │ │
│   │                                                                      │ │
│   │   M: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │
│   │      (M can't preempt L because L now has H's high priority)        │ │
│   │                                                                      │ │
│   │   ██ = Running    ▒▒ = Running with inherited priority              │ │
│   │   ░░ = Ready but not running                                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   2. PRIORITY CEILING:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Each lock has a "ceiling" priority = highest priority of any task      │
│   that might acquire it. When a task acquires the lock, its priority    │
│   is immediately raised to the ceiling.                                   │
│                                                                            │
│   Advantage: Prevents priority inversion before it happens               │
│   Disadvantage: Requires knowing all potential lock users in advance     │
│                                                                            │
│                                                                            │
│   3. DISABLING INTERRUPTS (simple but dangerous):                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Critical sections disable interrupts entirely, preventing preemption.  │
│   Only suitable for very short critical sections in kernel code.         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Traditional Unix Scheduler

### Multilevel Feedback Queues

Traditional Unix uses multilevel feedback queues to organize runnable processes:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MULTILEVEL FEEDBACK QUEUES                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Processes are organized into multiple queues based on priority:        │
│                                                                            │
│   Priority                                                                 │
│   ────────                                                                 │
│                                                                            │
│   0-3   ┌─────────────────────────────────────────────────────────────┐   │
│         │ Swapper, Pager  →  [proc]→[proc]→[proc]→NULL               │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   4-7   ┌─────────────────────────────────────────────────────────────┐   │
│         │ Disk I/O        →  [proc]→[proc]→NULL                      │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   8-11  ┌─────────────────────────────────────────────────────────────┐   │
│         │ Buffer Cache    →  [proc]→NULL                              │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   12-15 ┌─────────────────────────────────────────────────────────────┐   │
│         │ TTY Input       →  [proc]→[proc]→[proc]→[proc]→NULL        │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   16-19 ┌─────────────────────────────────────────────────────────────┐   │
│         │ TTY Output      →  [proc]→NULL                              │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│         ═══════════════════ KERNEL / USER BOUNDARY ═══════════════════   │
│                                                                            │
│   20-23 ┌─────────────────────────────────────────────────────────────┐   │
│         │ User priority 0 →  [proc]→[proc]→NULL                      │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   24-27 ┌─────────────────────────────────────────────────────────────┐   │
│         │ User priority 1 →  [proc]→[proc]→[proc]→NULL               │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   28-31 ┌─────────────────────────────────────────────────────────────┐   │
│         │ User priority 2 →  [proc]→NULL                              │   │
│         └─────────────────────────────────────────────────────────────┘   │
│                                                                            │
│    ...  (continues to lowest priority)                                    │
│                                                                            │
│                                                                            │
│   QUEUE SELECTION:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   queue_index = priority / 4    (group similar priorities)               │
│                                                                            │
│   The scheduler always picks from the LOWEST numbered non-empty queue   │
│   (highest priority processes)                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Scheduling Algorithm

How the traditional Unix scheduler selects the next process:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX SCHEDULING ALGORITHM                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm schedule_process                                              │
│   input:  none                                                             │
│   output: none (switches to selected process)                             │
│   {                                                                        │
│       while (no process selected to run)                                  │
│       {                                                                    │
│           /* Scan queues from highest to lowest priority */               │
│           for (queue = 0; queue < NUM_QUEUES; queue++)                   │
│           {                                                                │
│               if (queue is not empty)                                     │
│               {                                                            │
│                   /* Remove first process from queue */                   │
│                   selected = dequeue(queue);                              │
│                   break;                                                   │
│               }                                                            │
│           }                                                                │
│                                                                            │
│           if (no process found)                                           │
│           {                                                                │
│               /* System is idle - run idle loop */                        │
│               /* Wait for interrupt to wake a process */                  │
│               idle();                                                      │
│           }                                                                │
│       }                                                                    │
│                                                                            │
│       /* Context switch to selected process */                            │
│       if (selected != current_process)                                    │
│       {                                                                    │
│           context_switch(current_process, selected);                      │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### When Scheduling Occurs

The scheduler is invoked at specific points:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING DECISION POINTS                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The scheduler runs when:                                                 │
│                                                                            │
│   1. PROCESS BLOCKS                                                        │
│      ┌─────────────────────────────────────────────────────────────────┐  │
│      │ Process calls sleep() waiting for:                              │  │
│      │ • I/O completion                                                 │  │
│      │ • Lock/semaphore                                                 │  │
│      │ • Pipe data                                                      │  │
│      │ • Signal                                                         │  │
│      └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   2. PROCESS TERMINATES                                                    │
│      ┌─────────────────────────────────────────────────────────────────┐  │
│      │ Process calls exit() - must select another process              │  │
│      └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   3. RETURN FROM KERNEL MODE (Preemption Check)                           │
│      ┌─────────────────────────────────────────────────────────────────┐  │
│      │ After system call or interrupt, check if:                       │  │
│      │ • A higher priority process is ready                            │  │
│      │ • Current process has used its time slice                       │  │
│      │                                                                  │  │
│      │ if (runrun flag is set)                                         │  │
│      │     call scheduler                                               │  │
│      └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   4. CLOCK INTERRUPT (Every tick)                                         │
│      ┌─────────────────────────────────────────────────────────────────┐  │
│      │ • Increment current process CPU usage                           │  │
│      │ • Every second: recalculate all priorities                      │  │
│      │ • Set runrun flag if needed                                     │  │
│      └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   THE RUNRUN FLAG:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   runrun = 0;   /* No reschedule needed */                          │ │
│   │                                                                      │ │
│   │   /* Set when: */                                                    │ │
│   │   • Higher priority process becomes runnable (wakeup)              │ │
│   │   • Current process priority drops below another                   │ │
│   │   • Time quantum expires                                            │ │
│   │                                                                      │ │
│   │   /* Checked when: */                                                │ │
│   │   • Returning from system call to user mode                         │ │
│   │   • Returning from interrupt to user mode                           │ │
│   │                                                                      │ │
│   │   if (runrun && returning_to_user_mode)                             │ │
│   │       schedule();                                                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Time in Unix

### Hardware Clocks

Unix systems rely on several hardware timing mechanisms:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HARDWARE CLOCKS                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. REAL-TIME CLOCK (RTC)                                          │ │
│   │   ────────────────────────                                           │ │
│   │   • Battery-backed clock chip                                        │ │
│   │   • Maintains time when system is powered off                        │ │
│   │   • Low resolution (typically 1 second)                              │ │
│   │   • Read at boot to initialize system time                           │ │
│   │                                                                      │ │
│   │                  ┌─────────────┐                                     │ │
│   │                  │    RTC      │                                     │ │
│   │                  │  ┌───────┐  │                                     │ │
│   │                  │  │ 🔋    │  │  ◄─── Battery keeps time            │ │
│   │                  │  └───────┘  │       when system is off            │ │
│   │                  └─────────────┘                                     │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   2. PROGRAMMABLE INTERVAL TIMER (PIT) - Traditional                │ │
│   │   ───────────────────────────────────────────────────                │ │
│   │   • Intel 8254 chip (or compatible)                                  │ │
│   │   • Generates periodic interrupts                                    │ │
│   │   • Typical frequency: 100 Hz (10ms tick) or 1000 Hz (1ms tick)     │ │
│   │   • Limited precision                                                │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   3. TIME STAMP COUNTER (TSC) - Modern                              │ │
│   │   ────────────────────────────────────                               │ │
│   │   • CPU register that counts clock cycles                           │ │
│   │   • Very high resolution (nanoseconds)                              │ │
│   │   • Read with RDTSC instruction                                      │ │
│   │   • Issues: varies with CPU frequency, not synchronized across CPUs │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   4. HIGH PRECISION EVENT TIMER (HPET) - Modern                     │ │
│   │   ──────────────────────────────────────────────                     │ │
│   │   • Replacement for PIT                                              │ │
│   │   • Multiple independent timers                                      │ │
│   │   • Higher precision than PIT                                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### System Time vs Process Time

Unix maintains several different notions of time:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TYPES OF TIME IN UNIX                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. WALL CLOCK TIME (Real Time)                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Actual elapsed time                                                   │
│   • Seconds since January 1, 1970 00:00:00 UTC (the "Epoch")             │
│   • Stored in kernel variable: time_t                                    │
│   • Can be adjusted (NTP, manual changes)                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   time_t now = time(NULL);                                          │ │
│   │   // Returns seconds since epoch                                     │ │
│   │                                                                      │ │
│   │   struct timeval tv;                                                 │ │
│   │   gettimeofday(&tv, NULL);                                          │ │
│   │   // tv.tv_sec  = seconds                                            │ │
│   │   // tv.tv_usec = microseconds                                       │ │
│   │                                                                      │ │
│   │   struct timespec ts;                                                │ │
│   │   clock_gettime(CLOCK_REALTIME, &ts);                               │ │
│   │   // ts.tv_sec  = seconds                                            │ │
│   │   // ts.tv_nsec = nanoseconds                                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   2. PROCESS CPU TIME                                                      │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Time spent executing the process (not including time sleeping):        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │           Total CPU Time = User Time + System Time            │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                      │ │
│   │   User Time:   Time executing user-mode code                        │ │
│   │   System Time: Time executing kernel code on behalf of process     │ │
│   │                                                                      │ │
│   │   Example:                                                           │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │ $ time ./myprogram                                         │    │ │
│   │   │ real    0m5.032s    ◄── Wall clock time                    │    │ │
│   │   │ user    0m3.456s    ◄── User CPU time                      │    │ │
│   │   │ sys     0m0.789s    ◄── System CPU time                    │    │ │
│   │   │                                                             │    │ │
│   │   │ Note: real > user + sys because process was sleeping       │    │ │
│   │   │       or waiting for I/O part of the time                  │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   3. MONOTONIC TIME                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Always increases, never adjusted                                      │
│   • Good for measuring elapsed time                                       │
│   • Not affected by NTP or manual clock changes                          │
│                                                                            │
│   clock_gettime(CLOCK_MONOTONIC, &ts);                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Clock Tick

The fundamental unit of time in the kernel:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE CLOCK TICK (HZ)                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   HZ: Number of clock interrupts per second                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Historical values:                                                 │ │
│   │   • BSD/early Unix: 100 Hz (10ms tick)                              │ │
│   │   • Linux default:  100 Hz → 250 Hz → 1000 Hz (configurable)        │ │
│   │   • Modern "tickless" kernels can vary                              │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                              │   │ │
│   │   │   HZ = 100:  Each tick = 10 milliseconds                    │   │ │
│   │   │   HZ = 250:  Each tick = 4 milliseconds                     │   │ │
│   │   │   HZ = 1000: Each tick = 1 millisecond                      │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   TRADEOFF:                                                          │ │
│   │                                                                      │ │
│   │   Higher HZ:                                                         │ │
│   │   ✓ Better timer resolution                                         │ │
│   │   ✓ More responsive scheduling                                      │ │
│   │   ✗ More interrupt overhead                                         │ │
│   │   ✗ Higher power consumption                                        │ │
│   │                                                                      │ │
│   │   Lower HZ:                                                          │ │
│   │   ✓ Less overhead                                                   │ │
│   │   ✓ Better for batch/server workloads                               │ │
│   │   ✗ Less responsive interactive performance                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   JIFFIES (Linux):                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Kernel counter that increments every clock tick:                        │
│                                                                            │
│   unsigned long jiffies;   /* Wraps around eventually */                 │
│                                                                            │
│   To convert between jiffies and real time:                              │
│   • milliseconds = jiffies * 1000 / HZ                                   │
│   • jiffies = milliseconds * HZ / 1000                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. The Clock Handler

### Clock Interrupt Processing

The clock handler is one of the most frequently executed pieces of kernel code:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE CLOCK INTERRUPT                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Every 10ms (at HZ=100), hardware triggers clock interrupt:             │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────►    │
│         │      │      │      │      │      │      │      │      │         │
│         ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼         │
│        ┌┴┐    ┌┴┐    ┌┴┐    ┌┴┐    ┌┴┐    ┌┴┐    ┌┴┐    ┌┴┐    ┌┴┐        │
│        │ │    │ │    │ │    │ │    │ │    │ │    │ │    │ │    │ │        │
│        └─┘    └─┘    └─┘    └─┘    └─┘    └─┘    └─┘    └─┘    └─┘        │
│        10ms   20ms   30ms   40ms   50ms   60ms   70ms   80ms   90ms       │
│                                                                            │
│   Each tick, the clock handler:                                           │
│   • Updates system time                                                   │
│   • Updates process CPU usage                                             │
│   • Decrements time slice counter                                         │
│   • Handles alarms and timeouts                                           │
│   • Triggers scheduler if needed                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Algorithm for Clock Handler

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CLOCK HANDLER ALGORITHM                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm clock_handler                                                  │
│   input:  none                                                             │
│   output: none                                                             │
│   {                                                                        │
│       /* 1. Restart clock (for next interrupt) */                         │
│       restart_clock();                                                     │
│                                                                            │
│       /* 2. If process was in user mode, charge user time */              │
│       if (previous_mode == USER_MODE)                                      │
│       {                                                                    │
│           current_process->p_utime++;  /* user CPU time */                │
│           current_process->p_cpu++;    /* for priority decay */           │
│       }                                                                    │
│       else  /* kernel mode */                                              │
│       {                                                                    │
│           current_process->p_stime++;  /* system CPU time */              │
│       }                                                                    │
│                                                                            │
│       /* 3. Update system time */                                          │
│       if (--lbolt == 0)   /* once per second */                           │
│       {                                                                    │
│           lbolt = HZ;                                                      │
│           time++;         /* increment time-of-day */                     │
│           wakeup(one_second_event);                                        │
│                                                                            │
│           /* Recalculate priorities for all processes */                  │
│           for each process p                                               │
│           {                                                                │
│               /* Decay CPU usage */                                        │
│               p->p_cpu = decay(p->p_cpu);                                 │
│               /* Recalculate priority */                                  │
│               p->p_pri = p->p_cpu/4 + PUSER + p->p_nice;                 │
│           }                                                                │
│       }                                                                    │
│                                                                            │
│       /* 4. Process callouts (timeouts) */                                 │
│       for each callout c                                                   │
│       {                                                                    │
│           if (--c->time <= 0)                                              │
│           {                                                                │
│               /* Time expired - call the function */                       │
│               remove_callout(c);                                           │
│               (*c->function)(c->argument);                                │
│           }                                                                │
│       }                                                                    │
│                                                                            │
│       /* 5. Handle alarms for current process */                          │
│       if (current_process->p_alarm)                                        │
│       {                                                                    │
│           if (--current_process->p_alarm == 0)                             │
│               send_signal(current_process, SIGALRM);                      │
│       }                                                                    │
│                                                                            │
│       /* 6. Check if rescheduling needed */                                │
│       if (--current_process->p_quantum <= 0)                               │
│       {                                                                    │
│           current_process->p_quantum = default_quantum;                   │
│           runrun = 1;    /* request reschedule */                         │
│       }                                                                    │
│                                                                            │
│       /* 7. Handle profiling if enabled */                                 │
│       if (profiling_enabled)                                               │
│           profile_tick();                                                  │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Callouts and Timeouts

The kernel maintains a list of functions to call at specific times:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CALLOUT TABLE                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct callout {                                                         │
│       int         c_time;      /* ticks until expiration */               │
│       void       (*c_func)();  /* function to call */                     │
│       caddr_t     c_arg;       /* argument to function */                 │
│       struct callout *c_next;  /* next in list */                         │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   CALLOUT LIST (sorted by time):                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐                   │
│   │ time: 3 │──►│ time: 5 │──►│ time: 12│──►│ time: 47│──► NULL          │
│   │ func: A │   │ func: B │   │ func: C │   │ func: D │                   │
│   └─────────┘   └─────────┘   └─────────┘   └─────────┘                   │
│                                                                            │
│   On each clock tick, decrement first entry's time.                       │
│   When it reaches 0, call the function and remove entry.                  │
│                                                                            │
│                                                                            │
│   COMMON USES:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • TCP retransmission timers                                             │
│   • Device driver timeouts                                                │
│   • Watchdog timers                                                       │
│   • Delayed work                                                          │
│                                                                            │
│                                                                            │
│   MODERN LINUX: Timer Wheel                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Instead of a sorted list, Linux uses a hierarchical timer wheel:       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Level 0: 256 slots, 1 tick each    (0-255 ticks)                  │ │
│   │   Level 1: 64 slots, 256 ticks each  (256-16K ticks)                │ │
│   │   Level 2: 64 slots, 16K ticks each  (16K-1M ticks)                 │ │
│   │   ...                                                                │ │
│   │                                                                      │ │
│   │   O(1) insertion and deletion!                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Interval Timers

### The setitimer() System Call

Processes can request periodic or one-shot timer notifications:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERVAL TIMERS                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/time.h>                                                   │
│                                                                            │
│   struct itimerval {                                                       │
│       struct timeval it_interval;  /* timer interval (for periodic) */    │
│       struct timeval it_value;     /* current value (time remaining) */   │
│   };                                                                       │
│                                                                            │
│   struct timeval {                                                         │
│       time_t      tv_sec;    /* seconds */                                │
│       suseconds_t tv_usec;   /* microseconds */                           │
│   };                                                                       │
│                                                                            │
│   int setitimer(int which, const struct itimerval *new_value,             │
│                 struct itimerval *old_value);                              │
│                                                                            │
│   int getitimer(int which, struct itimerval *curr_value);                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Timer Types

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREE TYPES OF INTERVAL TIMERS                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. ITIMER_REAL                                                    │ │
│   │   ──────────────────────────────────────────────────────────────     │ │
│   │                                                                      │ │
│   │   • Decrements in real (wall clock) time                            │ │
│   │   • Generates SIGALRM when expired                                  │ │
│   │   • Counts even when process is not running                         │ │
│   │                                                                      │ │
│   │   Wall Clock: ═════════════════════════════════════════════════►    │ │
│   │               ▲                              ▲                       │ │
│   │               │                              │                       │ │
│   │           Set timer                      SIGALRM                    │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   2. ITIMER_VIRTUAL                                                 │ │
│   │   ──────────────────────────────────────────────────────────────     │ │
│   │                                                                      │ │
│   │   • Decrements only in user CPU time                                │ │
│   │   • Generates SIGVTALRM when expired                                │ │
│   │   • Does NOT count kernel time or sleep time                        │ │
│   │                                                                      │ │
│   │   Process:    [user][sys][sleep][user][sys][user][sleep][user]     │ │
│   │   Timer runs:  ████            ████      ████       ████           │ │
│   │                (only during user mode execution)                    │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   3. ITIMER_PROF                                                    │ │
│   │   ──────────────────────────────────────────────────────────────     │ │
│   │                                                                      │ │
│   │   • Decrements in user + system CPU time                            │ │
│   │   • Generates SIGPROF when expired                                  │ │
│   │   • Useful for profiling                                            │ │
│   │                                                                      │ │
│   │   Process:    [user][sys][sleep][user][sys][user][sleep][user]     │ │
│   │   Timer runs:  ████ ███       ████ ███ ████       ████            │ │
│   │                (during user + system mode execution)                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The alarm() System Call

A simpler interface for real-time alarms:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE alarm() SYSTEM CALL                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   unsigned int alarm(unsigned int seconds);                               │
│                                                                            │
│   • Sets a timer for 'seconds' seconds                                    │
│   • When timer expires, SIGALRM is delivered                              │
│   • Returns remaining time from previous alarm (or 0)                     │
│   • alarm(0) cancels any pending alarm                                    │
│                                                                            │
│                                                                            │
│   EXAMPLE: Simple timeout                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   void timeout_handler(int sig) {                                          │
│       printf("Operation timed out!\n");                                   │
│       exit(1);                                                             │
│   }                                                                        │
│                                                                            │
│   int main() {                                                             │
│       signal(SIGALRM, timeout_handler);                                   │
│       alarm(5);    /* 5 second timeout */                                 │
│                                                                            │
│       /* Do some potentially long operation */                            │
│       do_something_slow();                                                 │
│                                                                            │
│       alarm(0);    /* Cancel alarm if we finished in time */              │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   RELATIONSHIP TO setitimer():                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   alarm() is equivalent to:                                               │
│                                                                            │
│   struct itimerval it;                                                     │
│   it.it_value.tv_sec = seconds;                                           │
│   it.it_value.tv_usec = 0;                                                │
│   it.it_interval.tv_sec = 0;    /* one-shot, not periodic */             │
│   it.it_interval.tv_usec = 0;                                             │
│   setitimer(ITIMER_REAL, &it, NULL);                                      │
│                                                                            │
│   WARNING: alarm() and setitimer(ITIMER_REAL) share the same timer!      │
│   Using one cancels the other.                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Implementation of Interval Timers

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERVAL TIMER KERNEL DATA STRUCTURES                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   In the process's u-area (or task_struct in Linux):                      │
│                                                                            │
│   struct proc {                                                            │
│       ...                                                                  │
│       struct itimerval p_realtimer;   /* ITIMER_REAL */                   │
│       struct itimerval p_virtimer;    /* ITIMER_VIRTUAL */                │
│       struct itimerval p_proftimer;   /* ITIMER_PROF */                   │
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   HOW TIMERS ARE DECREMENTED:                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ITIMER_REAL:                                                      │ │
│   │   • Added to callout table (or timer wheel)                         │ │
│   │   • Kernel handles timeout automatically                            │ │
│   │                                                                      │ │
│   │   ITIMER_VIRTUAL:                                                   │ │
│   │   • Decremented in clock handler when process in USER mode          │ │
│   │   • Only current running process is checked                         │ │
│   │                                                                      │ │
│   │   ITIMER_PROF:                                                      │ │
│   │   • Decremented in clock handler when process is running            │ │
│   │   • Counts both user and kernel time                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   algorithm setitimer                                                      │
│   input:  which_timer, new_value, old_value                               │
│   output: 0 on success, -1 on error                                       │
│   {                                                                        │
│       /* Save old value if requested */                                   │
│       if (old_value != NULL)                                               │
│           *old_value = process->timers[which_timer];                      │
│                                                                            │
│       /* For ITIMER_REAL, interact with callout table */                  │
│       if (which_timer == ITIMER_REAL)                                      │
│       {                                                                    │
│           /* Remove existing callout if present */                        │
│           cancel_callout(process->real_timer_callout);                    │
│                                                                            │
│           /* Schedule new callout if value is non-zero */                 │
│           if (new_value->it_value != 0)                                    │
│               schedule_callout(new_value->it_value,                       │
│                               realtime_expire, process);                  │
│       }                                                                    │
│                                                                            │
│       /* Store new timer value */                                          │
│       process->timers[which_timer] = *new_value;                          │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### POSIX High-Resolution Timers

Modern systems provide more sophisticated timer interfaces:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX TIMERS (timer_create)                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Advantages over setitimer():                                            │
│   • Multiple timers per process (not just 3)                              │
│   • Nanosecond resolution (vs microsecond)                                │
│   • Can deliver signals to specific threads                               │
│   • More clock sources available                                          │
│                                                                            │
│                                                                            │
│   CREATING A TIMER:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   #include <signal.h>                                                      │
│   #include <time.h>                                                        │
│                                                                            │
│   timer_t timerid;                                                         │
│   struct sigevent sev;                                                     │
│                                                                            │
│   /* Configure notification method */                                      │
│   sev.sigev_notify = SIGEV_SIGNAL;   /* or SIGEV_THREAD */                │
│   sev.sigev_signo = SIGRTMIN;        /* signal to deliver */              │
│   sev.sigev_value.sival_ptr = &timerid;                                   │
│                                                                            │
│   timer_create(CLOCK_REALTIME, &sev, &timerid);                           │
│                                                                            │
│                                                                            │
│   ARMING A TIMER:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   struct itimerspec its;                                                   │
│                                                                            │
│   /* First expiration */                                                   │
│   its.it_value.tv_sec = 2;                                                │
│   its.it_value.tv_nsec = 500000000;  /* 2.5 seconds */                    │
│                                                                            │
│   /* Interval for periodic timer (0 = one-shot) */                        │
│   its.it_interval.tv_sec = 1;                                             │
│   its.it_interval.tv_nsec = 0;       /* 1 second interval */              │
│                                                                            │
│   timer_settime(timerid, 0, &its, NULL);                                  │
│                                                                            │
│                                                                            │
│   AVAILABLE CLOCKS:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CLOCK_REALTIME         System-wide real-time clock               │ │
│   │   CLOCK_MONOTONIC        Cannot be set, always increases           │ │
│   │   CLOCK_PROCESS_CPUTIME_ID  Process CPU time                       │ │
│   │   CLOCK_THREAD_CPUTIME_ID   Thread CPU time                        │ │
│   │   CLOCK_BOOTTIME         Like MONOTONIC, includes suspend time     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Sleep and Wakeup

### The sleep() Mechanism

When a process needs to wait for an event:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS SLEEPING AND WAKING                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When a process cannot proceed (waiting for I/O, resource, etc.):       │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A wants to read from disk:                                │ │
│   │                                                                      │ │
│   │   1. Issue I/O request to disk controller                          │ │
│   │   2. Data not ready yet - what to do?                              │ │
│   │                                                                      │ │
│   │   Option 1: Busy wait (BAD)              Option 2: Sleep (GOOD)    │ │
│   │   ────────────────────────               ─────────────────────────  │ │
│   │                                                                      │ │
│   │   while (!data_ready) {                  sleep(buffer_address);    │ │
│   │       /* waste CPU cycles */             /* Let other processes    │ │
│   │   }                                         run until data ready */│ │
│   │                                                                      │ │
│   │   • Wastes CPU time                      • CPU available for       │ │
│   │   • Prevents other processes               other processes         │ │
│   │     from running                         • Efficient use of        │ │
│   │                                            resources               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THE SLEEP/WAKEUP DANCE:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│                   Process A                      Kernel                   │
│                   ─────────                      ──────                   │
│                       │                                                   │
│                       │ read(fd, buf, n)                                  │
│                       ├─────────────────────────────►                     │
│                       │                             │                     │
│                       │                      [Issue I/O to disk]         │
│                       │                             │                     │
│                       │                      [Data not ready]            │
│                       │                             │                     │
│                       │◄── sleep(wait_channel) ─────┤                     │
│                       │                             │                     │
│                    [SLEEPING]                [Run other processes]       │
│                       .                             .                     │
│                       .                             .                     │
│                       .                      [Disk interrupt!]           │
│                       .                      [Data now ready]            │
│                       │                             │                     │
│                       │◄── wakeup(wait_channel) ────┤                     │
│                       │                             │                     │
│                    [RUNNABLE]               [Schedule process A]         │
│                       │                             │                     │
│                       │◄─── read() returns ─────────┤                     │
│                       │                                                   │
│                       ▼                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Sleep Queues and Wait Channels

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SLEEP QUEUES                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Processes sleeping on the same "wait channel" (event) are grouped:      │
│                                                                            │
│   WAIT CHANNEL: Usually the address of a kernel data structure            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Hash Table of Sleep Queues:                                       │ │
│   │                                                                      │ │
│   │   Bucket 0: ──► [Proc 3] ──► [Proc 7] ──► NULL                     │ │
│   │                 (waiting on buffer 0x1234)                          │ │
│   │                                                                      │ │
│   │   Bucket 1: ──► [Proc 12] ──► NULL                                 │ │
│   │                 (waiting on inode 0x5678)                           │ │
│   │                                                                      │ │
│   │   Bucket 2: ──► NULL                                                │ │
│   │                                                                      │ │
│   │   Bucket 3: ──► [Proc 1] ──► [Proc 5] ──► [Proc 9] ──► NULL       │ │
│   │                 (waiting on pipe 0x9ABC)                            │ │
│   │                                                                      │ │
│   │   ...                                                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   struct proc {                                                            │
│       ...                                                                  │
│       caddr_t p_wchan;      /* wait channel (what we're waiting for) */   │
│       int     p_stat;       /* process state (SSLEEP, etc.) */            │
│       int     p_pri;        /* sleep priority */                          │
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Algorithm for Sleep

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL SLEEP ALGORITHM                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm sleep                                                          │
│   input:  wait_channel    (address to sleep on)                           │
│           priority        (sleep priority, may be interruptible)          │
│   output: 0 on normal wakeup, -1 if interrupted by signal                 │
│   {                                                                        │
│       /* Raise processor priority to block interrupts */                  │
│       old_priority = spl6();                                               │
│                                                                            │
│       /* Record what we're waiting for */                                 │
│       current_process->p_wchan = wait_channel;                            │
│       current_process->p_stat = SSLEEP;                                   │
│       current_process->p_pri = priority;                                  │
│                                                                            │
│       /* Add to sleep queue */                                            │
│       hash_bucket = HASH(wait_channel);                                   │
│       add_to_queue(sleep_queue[hash_bucket], current_process);            │
│                                                                            │
│       /* If interruptible sleep and signal pending, don't sleep */        │
│       if (priority > PZERO && signal_pending(current_process))            │
│       {                                                                    │
│           /* Remove from sleep queue */                                   │
│           remove_from_queue(current_process);                             │
│           current_process->p_wchan = 0;                                   │
│           current_process->p_stat = SRUN;                                 │
│           splx(old_priority);                                              │
│           return -1;   /* interrupted */                                  │
│       }                                                                    │
│                                                                            │
│       /* Context switch to another process */                             │
│       swtch();                                                             │
│                                                                            │
│       /* We return here after being woken up */                           │
│       splx(old_priority);                                                  │
│                                                                            │
│       /* Check if we were woken by a signal */                            │
│       if (priority > PZERO && signal_pending(current_process))            │
│           return -1;   /* interrupted by signal */                        │
│                                                                            │
│       return 0;        /* normal wakeup */                                │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   SLEEP PRIORITY (traditional Unix):                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   priority <= PZERO:  Non-interruptible sleep                       │ │
│   │                       Process cannot be killed by signals           │ │
│   │                       Used for critical I/O (disk reads)            │ │
│   │                                                                      │ │
│   │   priority > PZERO:   Interruptible sleep                           │ │
│   │                       Can be woken by signals                       │ │
│   │                       Used for user-level waits                     │ │
│   │                                                                      │ │
│   │   Common values:                                                     │ │
│   │     PRIBIO (20)   - Block I/O priority                              │ │
│   │     PZERO  (25)   - Threshold for signals                           │ │
│   │     PWAIT  (40)   - Waiting for child                               │
│   │     PLOCK  (35)   - Waiting for lock                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Wakeup

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL WAKEUP ALGORITHM                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm wakeup                                                         │
│   input:  wait_channel    (address to wake up)                            │
│   output: none                                                             │
│   {                                                                        │
│       old_priority = spl6();                                               │
│                                                                            │
│       /* Find all processes sleeping on this channel */                   │
│       hash_bucket = HASH(wait_channel);                                   │
│                                                                            │
│       for each process p in sleep_queue[hash_bucket]                      │
│       {                                                                    │
│           if (p->p_wchan == wait_channel)                                 │
│           {                                                                │
│               /* Remove from sleep queue */                               │
│               remove_from_queue(p);                                       │
│               p->p_wchan = 0;                                             │
│                                                                            │
│               /* Make process runnable */                                 │
│               p->p_stat = SRUN;                                           │
│                                                                            │
│               /* Add to run queue */                                      │
│               add_to_run_queue(p);                                        │
│                                                                            │
│               /* Check if we should preempt current process */            │
│               if (p->p_pri < current_process->p_pri)                      │
│                   runrun = 1;   /* request reschedule */                  │
│           }                                                                │
│       }                                                                    │
│                                                                            │
│       splx(old_priority);                                                  │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Thundering Herd Problem

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE THUNDERING HERD PROBLEM                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROBLEM:                                                                 │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│   When multiple processes wait on the same resource, wakeup() wakes       │
│   ALL of them, but only ONE can proceed:                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   10 processes waiting for a lock:                                  │ │
│   │                                                                      │ │
│   │   [P1]──┐                                                           │ │
│   │   [P2]──┤                                                           │ │
│   │   [P3]──┤     ┌─────────────────────────┐                          │ │
│   │   [P4]──┼────►│   Sleeping on lock      │                          │ │
│   │   [P5]──┤     └─────────────────────────┘                          │ │
│   │   ...   │                 │                                         │ │
│   │   [P10]─┘                 │                                         │ │
│   │                           ▼                                         │ │
│   │                    Lock released!                                   │ │
│   │                    wakeup(lock_addr)                                │ │
│   │                           │                                         │ │
│   │                           ▼                                         │ │
│   │   ALL 10 wake up ────► [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10]   │ │
│   │                                         │                           │ │
│   │                                         ▼                           │ │
│   │   Only P1 gets the lock!                                           │ │
│   │   P2-P10 must go back to sleep                                     │ │
│   │                                                                      │ │
│   │   WASTE: 9 unnecessary context switches                            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SOLUTIONS:                                                               │
│   ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│   1. wakeup_one(): Wake only one process                                  │
│      • Some BSD systems added this                                        │
│      • Linux uses wake_up_interruptible() vs wake_up_all()               │
│                                                                            │
│   2. Wait queues with exclusive waiters                                   │
│      • Mark some waiters as "exclusive"                                   │
│      • Wakeup stops after waking one exclusive waiter                    │
│                                                                            │
│   3. Per-CPU wait queues                                                  │
│      • Reduces contention on SMP systems                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Modern Linux Schedulers

### The O(1) Scheduler (Linux 2.6 - 2.6.22)

The O(1) scheduler replaced the O(n) scheduler in Linux 2.6:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE O(1) SCHEDULER                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROBLEM WITH TRADITIONAL SCHEDULER:                                      │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Traditional Unix scheduler scans ALL runnable processes each time:      │
│                                                                            │
│   for each process p                          O(n) time complexity!       │
│       if (p->priority < best->priority)       n = number of processes    │
│           best = p;                                                       │
│                                                                            │
│   With thousands of processes, this becomes slow.                         │
│                                                                            │
│                                                                            │
│   O(1) SOLUTION: Two Arrays + Bitmap                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ACTIVE ARRAY                      EXPIRED ARRAY                   │ │
│   │   ────────────────                  ────────────────                │ │
│   │                                                                      │ │
│   │   Bitmap: 0001001010...             Bitmap: 0000100000...           │ │
│   │           ↓  ↓  ↓                           ↓                       │ │
│   │                                                                      │ │
│   │   [0] ──► NULL                      [0] ──► NULL                    │ │
│   │   [1] ──► NULL                      [1] ──► NULL                    │ │
│   │   [2] ──► NULL                      [2] ──► NULL                    │ │
│   │   [3] ──► P1 ──► P4 ──► NULL       [3] ──► NULL                    │ │
│   │   [4] ──► NULL                      [4] ──► NULL                    │ │
│   │   [5] ──► NULL                      [5] ──► P2 ──► NULL            │ │
│   │   [6] ──► P3 ──► NULL              [6] ──► NULL                    │ │
│   │   ...                               ...                              │ │
│   │   [139] ──► NULL                    [139] ──► NULL                  │ │
│   │                                                                      │ │
│   │   140 priority levels (0-139)                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   1. Find highest priority: scan bitmap for first set bit     O(1)       │
│   2. Get process from that queue                               O(1)       │
│   3. Run process until timeslice expires                                  │
│   4. When expired, move process to EXPIRED array at same priority        │
│   5. When ACTIVE array is empty, swap pointers:                          │
│      active = expired; expired = active;                      O(1)       │
│                                                                            │
│   Total: O(1) for ALL scheduling decisions!                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### O(1) Scheduler Priority Mapping

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    O(1) PRIORITY LEVELS                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   140 Priority Levels:                                                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   0-99:    Real-time priorities (SCHED_FIFO, SCHED_RR)             │ │
│   │            Lower number = higher priority                           │ │
│   │                                                                      │ │
│   │   100-139: Normal (SCHED_OTHER) priorities                          │ │
│   │            Maps from nice values:                                   │ │
│   │            nice -20 → priority 100 (highest normal)                │ │
│   │            nice  0  → priority 120 (default)                       │ │
│   │            nice +19 → priority 139 (lowest)                        │ │
│   │                                                                      │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │                                                                │ │ │
│   │   │   Priority 0   ←── Most urgent (real-time)                    │ │ │
│   │   │   Priority 1                                                   │ │ │
│   │   │   ...                                                          │ │ │
│   │   │   Priority 99  ←── Least urgent real-time                     │ │ │
│   │   │   ─────────────── BOUNDARY ──────────────────                 │ │ │
│   │   │   Priority 100 ←── nice -20 (highest normal)                  │ │ │
│   │   │   ...                                                          │ │ │
│   │   │   Priority 120 ←── nice 0 (default)                           │ │ │
│   │   │   ...                                                          │ │ │
│   │   │   Priority 139 ←── nice +19 (lowest)                          │ │ │
│   │   │                                                                │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Completely Fair Scheduler (CFS)

Introduced in Linux 2.6.23, CFS replaced O(1) for normal processes:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE COMPLETELY FAIR SCHEDULER (CFS)                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PHILOSOPHY:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   "Model an ideal, perfectly fair, multitasking CPU"                      │
│                                                                            │
│   On such a CPU, with N processes, each would get exactly 1/N of CPU.    │
│   CFS tries to approximate this ideal.                                    │
│                                                                            │
│                                                                            │
│   KEY CONCEPT: Virtual Runtime (vruntime)                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Each task tracks how much CPU time it has received:                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   vruntime = actual_runtime * (NICE_0_WEIGHT / task_weight)        │ │
│   │                                                                      │ │
│   │   • Higher nice value → higher vruntime (punished)                 │ │
│   │   • Lower nice value → lower vruntime (rewarded)                   │ │
│   │                                                                      │ │
│   │   CFS always picks the task with LOWEST vruntime to run next.      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   DATA STRUCTURE: Red-Black Tree                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Tasks ordered by vruntime in a self-balancing red-black tree:           │
│                                                                            │
│                            [vruntime: 500]                                 │
│                            /              \                                │
│                     [vruntime: 300]    [vruntime: 800]                    │
│                     /          \       /            \                     │
│              [vruntime: 200]  [350]  [700]    [vruntime: 1000]           │
│                                                                            │
│   Leftmost node = lowest vruntime = next task to run                      │
│                                                                            │
│   Operations:                                                              │
│   • Find leftmost:  O(1)  [cached pointer]                                │
│   • Insert:         O(log n)                                              │
│   • Remove:         O(log n)                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### CFS Weight and Time Slice Calculation

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CFS WEIGHT TABLE                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Nice values map to weights (approximate 1.25x per nice level):          │
│                                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │   Nice   Weight     Nice   Weight     Nice   Weight              │   │
│   │   ────   ──────     ────   ──────     ────   ──────              │   │
│   │   -20    88761       -6    3121        7       272               │   │
│   │   -19    71755       -5    2501        8       215               │   │
│   │   -18    56483       -4    1991        9       172               │   │
│   │   -17    46273       -3    1586       10       137               │   │
│   │   -16    36291       -2    1277       11       110               │   │
│   │   -15    29154       -1    1024       12        87               │   │
│   │   -14    23254        0    820        13        70               │   │
│   │   -13    18705        1    655        14        56               │   │
│   │   -12    14949        2    526        15        45               │   │
│   │   -11    11916        3    423        16        36               │   │
│   │   -10     9548        4    335        17        29               │   │
│   │    -9     7620        5    272        18        23               │   │
│   │    -8     6100        6    215        19        18               │   │
│   │    -7     4904                                                    │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   TIME SLICE CALCULATION:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   time_slice = target_latency * (task_weight / total_weight)       │ │
│   │                                                                      │ │
│   │   Example: 2 tasks, nice 0 and nice 5                               │ │
│   │   • nice 0 weight: 1024                                             │ │
│   │   • nice 5 weight: 335                                              │ │
│   │   • Total weight: 1359                                              │ │
│   │   • Target latency: 6ms (default)                                   │ │
│   │                                                                      │ │
│   │   nice 0 gets: 6ms * (1024/1359) = 4.52ms                          │ │
│   │   nice 5 gets: 6ms * (335/1359)  = 1.48ms                          │ │
│   │                                                                      │ │
│   │   Ratio: 4.52/1.48 ≈ 3:1 (nice 0 gets 3x more CPU)                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Scheduling Classes

Linux uses a modular scheduling framework:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING CLASSES                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Linux scheduler is organized into pluggable scheduling classes:         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   PRIORITY ORDER (highest to lowest):                               │ │
│   │                                                                      │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │  stop_sched_class                                            │  │ │
│   │   │  ───────────────────────────────────────────────────────────  │  │ │
│   │   │  • Highest priority                                          │  │ │
│   │   │  • Used for migration/stop_machine                           │  │ │
│   │   │  • Cannot be preempted                                       │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                         │                                           │ │
│   │                         ▼                                           │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │  dl_sched_class (SCHED_DEADLINE)                             │  │ │
│   │   │  ───────────────────────────────────────────────────────────  │  │ │
│   │   │  • Earliest deadline first scheduling                        │  │ │
│   │   │  • For hard real-time tasks                                  │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                         │                                           │ │
│   │                         ▼                                           │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │  rt_sched_class (SCHED_FIFO, SCHED_RR)                       │  │ │
│   │   │  ───────────────────────────────────────────────────────────  │  │ │
│   │   │  • Fixed priority real-time scheduling                       │  │ │
│   │   │  • 100 priority levels (1-99)                                │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                         │                                           │ │
│   │                         ▼                                           │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │  fair_sched_class (SCHED_OTHER, SCHED_BATCH, SCHED_IDLE)    │  │ │
│   │   │  ───────────────────────────────────────────────────────────  │  │ │
│   │   │  • CFS - normal time-sharing tasks                           │  │ │
│   │   │  • Most processes use this                                   │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                         │                                           │ │
│   │                         ▼                                           │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │  idle_sched_class                                            │  │ │
│   │   │  ───────────────────────────────────────────────────────────  │  │ │
│   │   │  • Lowest priority                                           │  │ │
│   │   │  • Runs only when nothing else can run                       │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SCHEDULER PICKS NEXT TASK:                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   for each sched_class (highest to lowest):                               │
│       task = sched_class->pick_next_task()                                │
│       if (task != NULL)                                                    │
│           return task;                                                     │
│   return idle_task;                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Real-Time Scheduling

### Hard vs Soft Real-Time

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME SYSTEMS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   HARD REAL-TIME:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Missing a deadline is a SYSTEM FAILURE.                                 │
│                                                                            │
│   Examples:                                                                │
│   • Aircraft flight control systems                                        │
│   • Medical devices (pacemakers)                                           │
│   • Industrial robot controllers                                           │
│   • Anti-lock braking systems (ABS)                                        │
│   • Nuclear reactor control                                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Deadline                                                           │ │
│   │      │                                                               │ │
│   │      ▼                                                               │ │
│   │   ───┬───────────────────────────────┬───────────────────────────   │ │
│   │      │◄── VALID ──►│                 │◄── CATASTROPHIC ──►         │ │
│   │                    │                                                │ │
│   │                 Deadline                                            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SOFT REAL-TIME:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Missing a deadline degrades quality but system continues.               │
│                                                                            │
│   Examples:                                                                │
│   • Video playback (dropped frames)                                        │
│   • Audio streaming (glitches)                                             │
│   • Video conferencing                                                     │
│   • Online gaming                                                          │
│   • Stock trading (latency matters but not catastrophic)                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Value                                                              │ │
│   │     │                                                                │ │
│   │   1 ├────────────┐                                                   │ │
│   │     │            │                                                   │ │
│   │     │            └─────────────────────                             │ │
│   │   0 └──────────────────────────────────────► Time                   │ │
│   │                  │                                                   │ │
│   │               Deadline    (value degrades but doesn't go to 0)      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### SCHED_FIFO and SCHED_RR

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX REAL-TIME SCHEDULING POLICIES                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCHED_FIFO (First-In-First-Out):                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Task runs until it:                                                    │
│     - Blocks (I/O, sleep, mutex)                                          │
│     - Yields explicitly (sched_yield)                                     │
│     - Is preempted by higher-priority task                                │
│                                                                            │
│   • NO time slicing within same priority level                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Priority 50 queue:  [Task A] ──► [Task B] ──► [Task C]           │ │
│   │                                                                      │ │
│   │   Task A runs until it blocks or exits.                             │ │
│   │   Then Task B runs. Then Task C.                                    │ │
│   │   B and C NEVER run while A is runnable.                            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SCHED_RR (Round-Robin):                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Like SCHED_FIFO but WITH time slicing                                 │
│   • Tasks at same priority get equal time slices                          │
│   • When timeslice expires, task goes to end of queue                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Priority 50 queue:  [Task A] ──► [Task B] ──► [Task C]           │ │
│   │                                                                      │ │
│   │   Time slice = 100ms (default)                                       │ │
│   │                                                                      │ │
│   │   t=0ms:    A runs                                                   │ │
│   │   t=100ms:  A → back of queue, B runs                               │ │
│   │   t=200ms:  B → back of queue, C runs                               │ │
│   │   t=300ms:  C → back of queue, A runs again                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   COMPARISON:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌──────────────────┬─────────────────────┬─────────────────────┐        │
│   │   Attribute      │   SCHED_FIFO        │   SCHED_RR          │        │
│   ├──────────────────┼─────────────────────┼─────────────────────┤        │
│   │   Time slicing   │   No                │   Yes               │        │
│   │   Preemption     │   Higher prio only  │   Higher prio or    │        │
│   │                  │                     │   timeslice expiry  │        │
│   │   Fairness       │   None (at prio)    │   Fair (at prio)    │        │
│   │   Use case       │   Single critical   │   Multiple equal    │        │
│   │                  │   task per prio     │   priority tasks    │        │
│   └──────────────────┴─────────────────────┴─────────────────────┘        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Priority Levels

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME PRIORITY LEVELS                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Linux real-time priorities: 1-99 (higher number = higher priority)     │
│   (Note: opposite of nice values!)                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   RT Priority 99 ◄── Highest real-time priority                     │ │
│   │   RT Priority 98                                                     │ │
│   │   RT Priority 97                                                     │ │
│   │   ...                                                                │ │
│   │   RT Priority 50 ◄── Common for audio applications                  │ │
│   │   ...                                                                │ │
│   │   RT Priority 2                                                      │ │
│   │   RT Priority 1  ◄── Lowest real-time priority                      │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │   Normal tasks (nice -20 to +19)                                    │ │
│   │                                                                      │ │
│   │   ANY real-time task preempts ALL normal tasks                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SETTING REAL-TIME PRIORITY:                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   struct sched_param param;                                                │
│   param.sched_priority = 50;  /* 1-99 */                                  │
│                                                                            │
│   /* Set this process to SCHED_FIFO with priority 50 */                   │
│   sched_setscheduler(0, SCHED_FIFO, &param);                              │
│                                                                            │
│   /* Or use pthread_setschedparam for threads */                          │
│   pthread_setschedparam(thread, SCHED_RR, &param);                        │
│                                                                            │
│                                                                            │
│   PRIORITY MAPPING TO KERNEL:                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Internal kernel priority = 99 - rt_priority                             │
│                                                                            │
│   rt_priority 99 → kernel priority 0  (highest)                          │
│   rt_priority 1  → kernel priority 98 (lowest RT)                        │
│   normal nice -20 → kernel priority 100                                   │
│   normal nice +19 → kernel priority 139                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### SCHED_DEADLINE (Earliest Deadline First)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHED_DEADLINE (Linux 3.14+)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Earliest Deadline First (EDF) scheduling algorithm.                     │
│   Task with earliest deadline runs first.                                  │
│                                                                            │
│   THREE PARAMETERS:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Runtime:  How much CPU time task needs per period                     │
│   • Period:   How often the task needs to run                             │
│   • Deadline: When task must complete (relative to period start)          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                                                               │  │ │
│   │   │   │◄─────────── Period ──────────────►│                      │  │ │
│   │   │   │                                    │                      │  │ │
│   │   │   │◄─ Runtime ─►│    │◄── Deadline ──►│                      │  │ │
│   │   │   │             │    │                │                      │  │ │
│   │   │   ▼             ▼    ▼                ▼                      │  │ │
│   │   │   ┬─────────────┬────┬────────────────┬──────────────────    │  │ │
│   │   │   │  EXECUTE    │REST│    SLACK       │  NEXT PERIOD...     │  │ │
│   │   │   └─────────────┴────┴────────────────┘                      │  │ │
│   │   │                                                               │  │ │
│   │   │   Typically: Runtime ≤ Deadline ≤ Period                    │  │ │
│   │   │                                                               │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLE: Video encoding task                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Must encode 30 frames per second                                       │
│   • Each frame takes at most 10ms of CPU                                   │
│   • Each frame must be ready within 33ms                                   │
│                                                                            │
│   struct sched_attr attr;                                                  │
│   attr.sched_policy = SCHED_DEADLINE;                                      │
│   attr.sched_runtime  = 10 * 1000 * 1000;   /* 10ms in nanoseconds */     │
│   attr.sched_deadline = 33 * 1000 * 1000;   /* 33ms */                    │
│   attr.sched_period   = 33 * 1000 * 1000;   /* 33ms */                    │
│                                                                            │
│   sched_setattr(0, &attr, 0);                                              │
│                                                                            │
│                                                                            │
│   EDF ALGORITHM:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Task A: deadline = t+10ms                                          │ │
│   │   Task B: deadline = t+5ms   ◄── Runs first!                        │ │
│   │   Task C: deadline = t+20ms                                          │ │
│   │                                                                      │ │
│   │   Scheduler always picks task with NEAREST absolute deadline.       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Throttling

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME THROTTLING                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROBLEM: A runaway real-time task can starve ALL normal tasks!          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   while (1) {                                                        │ │
│   │       /* Infinite loop in SCHED_FIFO task */                        │ │
│   │       /* System becomes completely unresponsive! */                 │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SOLUTION: Real-Time Throttling (RT bandwidth limiting)                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Default: RT tasks limited to 95% of CPU time per second                 │
│                                                                            │
│   /proc/sys/kernel/sched_rt_period_us   = 1000000 (1 second)             │
│   /proc/sys/kernel/sched_rt_runtime_us  = 950000  (950ms = 95%)          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   │◄─────────────── 1 second ───────────────────►│                  │ │
│   │   │                                               │                  │ │
│   │   │◄── RT tasks get 950ms ──►│◄── 50ms for ──►  │                  │ │
│   │   │                           │   normal tasks   │                  │ │
│   │   │                           │                  │                  │ │
│   │   ├───────────────────────────┼──────────────────┤                  │ │
│   │   │      SCHED_FIFO/RR        │   SCHED_OTHER    │                  │ │
│   │   │                           │   can run here   │                  │ │
│   │   │                           │                  │                  │ │
│   │   └───────────────────────────┴──────────────────┘                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   DISABLE THROTTLING (dangerous!):                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   echo -1 > /proc/sys/kernel/sched_rt_runtime_us                          │
│                                                                            │
│   Warning: A buggy RT task can now completely hang the system!            │
│                                                                            │
│                                                                            │
│   PER-CGROUP RT BANDWIDTH:                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Each cgroup can have its own RT bandwidth limit:                        │
│                                                                            │
│   /sys/fs/cgroup/cpu/mygroup/cpu.rt_period_us                             │
│   /sys/fs/cgroup/cpu/mygroup/cpu.rt_runtime_us                            │
│                                                                            │
│   This allows isolating RT tasks to specific resource limits.             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Multiprocessor Scheduling

### SMP Scheduling Challenges

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SMP SCHEDULING CHALLENGES                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SMP = Symmetric Multi-Processing (multiple identical CPUs)              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐                            │ │
│   │   │ CPU │   │ CPU │   │ CPU │   │ CPU │                            │ │
│   │   │  0  │   │  1  │   │  2  │   │  3  │                            │ │
│   │   └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘                            │ │
│   │      │         │         │         │                                │ │
│   │      └─────────┴────┬────┴─────────┘                                │ │
│   │                     │                                                │ │
│   │              ┌──────┴──────┐                                         │ │
│   │              │  Shared     │                                         │ │
│   │              │  Memory     │                                         │ │
│   │              └─────────────┘                                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KEY CHALLENGES:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   1. CACHE AFFINITY                                                        │
│      Moving a task between CPUs invalidates warm cache → performance hit  │
│                                                                            │
│   2. LOAD BALANCING                                                        │
│      Distributing work evenly across all CPUs                             │
│                                                                            │
│   3. CACHE COHERENCY                                                       │
│      Keeping shared data consistent across CPU caches                     │
│                                                                            │
│   4. LOCK CONTENTION                                                       │
│      A single run queue lock becomes a bottleneck                         │
│                                                                            │
│   5. NUMA TOPOLOGY                                                         │
│      Some memory is "closer" to certain CPUs                              │
│                                                                            │
│                                                                            │
│   SOLUTION: Per-CPU Run Queues                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │ │
│   │   │   CPU 0     │   │   CPU 1     │   │   CPU 2     │              │ │
│   │   ├─────────────┤   ├─────────────┤   ├─────────────┤              │ │
│   │   │ Run Queue 0 │   │ Run Queue 1 │   │ Run Queue 2 │              │ │
│   │   │ [P1][P4][P7]│   │ [P2][P5]    │   │ [P3][P6]    │              │ │
│   │   └─────────────┘   └─────────────┘   └─────────────┘              │ │
│   │                                                                      │ │
│   │   Each CPU has its own lock → no global contention!                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### CPU Affinity

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CPU AFFINITY                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CPU affinity binds a task to specific CPU(s).                           │
│                                                                            │
│   WHY USE AFFINITY:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Cache warmth: Keep task on same CPU for hot cache                     │
│   • NUMA locality: Keep task near its memory                              │
│   • Isolation: Dedicate CPUs to specific tasks                            │
│   • Predictability: Reduce scheduling jitter                              │
│                                                                            │
│                                                                            │
│   AFFINITY MASK:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   cpu_set_t mask;                                                    │ │
│   │                                                                      │ │
│   │   Bitmask: 0 0 0 0 0 0 1 1                                          │ │
│   │            │ │ │ │ │ │ │ │                                          │ │
│   │            │ │ │ │ │ │ │ └── CPU 0: allowed                        │ │
│   │            │ │ │ │ │ │ └──── CPU 1: allowed                        │ │
│   │            │ │ │ │ │ └────── CPU 2: not allowed                    │ │
│   │            │ │ │ │ └──────── CPU 3: not allowed                    │ │
│   │            ...                                                       │ │
│   │                                                                      │ │
│   │   Task can only run on CPUs 0 and 1.                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   API:                                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   #define _GNU_SOURCE                                                      │
│   #include <sched.h>                                                       │
│                                                                            │
│   cpu_set_t mask;                                                          │
│   CPU_ZERO(&mask);              /* Clear all bits */                      │
│   CPU_SET(0, &mask);            /* Allow CPU 0 */                         │
│   CPU_SET(1, &mask);            /* Allow CPU 1 */                         │
│                                                                            │
│   /* Set affinity for current process */                                   │
│   sched_setaffinity(0, sizeof(mask), &mask);                              │
│                                                                            │
│   /* Get current affinity */                                               │
│   sched_getaffinity(0, sizeof(mask), &mask);                              │
│                                                                            │
│   /* Check if CPU 0 is in mask */                                          │
│   if (CPU_ISSET(0, &mask)) { ... }                                        │
│                                                                            │
│                                                                            │
│   COMMAND LINE:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Run process on CPUs 0,1 only                                           │
│   taskset -c 0,1 ./myprogram                                               │
│                                                                            │
│   # Show affinity of PID 1234                                              │
│   taskset -p 1234                                                          │
│                                                                            │
│   # Set affinity of running process                                        │
│   taskset -p -c 2,3 1234                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Load Balancing

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCING                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   With per-CPU run queues, CPUs can become imbalanced:                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BEFORE BALANCING:                                                  │ │
│   │                                                                      │ │
│   │   CPU 0: [P1][P2][P3][P4][P5][P6]   ← Overloaded!                  │ │
│   │   CPU 1: [P7]                        ← Underloaded                  │ │
│   │   CPU 2: []                          ← Idle!                        │ │
│   │   CPU 3: [P8][P9]                                                   │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   AFTER BALANCING:                                                   │ │
│   │                                                                      │ │
│   │   CPU 0: [P1][P2][P3]                                               │ │
│   │   CPU 1: [P7][P4]                    ← P4 migrated                  │ │
│   │   CPU 2: [P5][P6]                    ← P5, P6 migrated              │ │
│   │   CPU 3: [P8][P9]                                                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   LINUX SCHEDULING DOMAINS:                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Hierarchical structure for balancing decisions:                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │              NUMA Domain (cross-node)                       │    │ │
│   │   │   Balance interval: 64ms                                    │    │ │
│   │   │                                                             │    │ │
│   │   │   ┌──────────────────────┐  ┌──────────────────────┐       │    │ │
│   │   │   │  MC Domain (socket)  │  │  MC Domain (socket)  │       │    │ │
│   │   │   │  Balance: 4ms        │  │  Balance: 4ms        │       │    │ │
│   │   │   │                      │  │                      │       │    │ │
│   │   │   │  ┌────┐    ┌────┐   │  │  ┌────┐    ┌────┐   │       │    │ │
│   │   │   │  │CPU0│    │CPU1│   │  │  │CPU2│    │CPU3│   │       │    │ │
│   │   │   │  └────┘    └────┘   │  │  └────┘    └────┘   │       │    │ │
│   │   │   └──────────────────────┘  └──────────────────────┘       │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WHEN BALANCING OCCURS:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   1. Periodic balancing (based on domain intervals)                       │
│   2. When a CPU goes idle (pull tasks from busy CPUs)                     │
│   3. When a new task is created (decide placement)                        │
│   4. When a task wakes up (decide where to run)                           │
│                                                                            │
│                                                                            │
│   MIGRATION COST:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Moving a task has costs:                                                 │
│   • Cache invalidation (task's data not in new CPU's cache)               │
│   • TLB flush                                                              │
│   • Migration thread overhead                                              │
│                                                                            │
│   Scheduler only migrates if imbalance exceeds threshold.                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### NUMA Considerations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NUMA (Non-Uniform Memory Access)                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   In NUMA systems, memory access time depends on which CPU accesses it.  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────────────┐        ┌─────────────────────┐            │ │
│   │   │      Node 0         │        │      Node 1         │            │ │
│   │   │                     │        │                     │            │ │
│   │   │  ┌─────┐  ┌─────┐  │        │  ┌─────┐  ┌─────┐  │            │ │
│   │   │  │CPU 0│  │CPU 1│  │        │  │CPU 2│  │CPU 3│  │            │ │
│   │   │  └──┬──┘  └──┬──┘  │        │  └──┬──┘  └──┬──┘  │            │ │
│   │   │     │        │     │        │     │        │     │            │ │
│   │   │     └───┬────┘     │        │     └───┬────┘     │            │ │
│   │   │         │          │        │         │          │            │ │
│   │   │   ┌─────┴─────┐   │        │   ┌─────┴─────┐   │            │ │
│   │   │   │  Memory   │   │        │   │  Memory   │   │            │ │
│   │   │   │  (Local)  │   │════════│   │  (Local)  │   │            │ │
│   │   │   └───────────┘   │  QPI   │   └───────────┘   │            │ │
│   │   │                   │  link  │                   │            │ │
│   │   └─────────────────────┘        └─────────────────────┘            │ │
│   │                                                                      │ │
│   │   CPU 0 accessing Node 0 memory: ~100ns (local)                     │ │
│   │   CPU 0 accessing Node 1 memory: ~300ns (remote, 3x slower!)       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   NUMA-AWARE SCHEDULING:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   1. Prefer to run tasks on the node where their memory is allocated     │
│   2. Allocate memory on the node where the task runs                      │
│   3. Avoid migrating tasks across NUMA nodes                              │
│   4. Balance within nodes before balancing across nodes                   │
│                                                                            │
│                                                                            │
│   NUMA MEMORY POLICIES:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   #include <numaif.h>                                                      │
│                                                                            │
│   /* Allocate memory on specific node */                                   │
│   set_mempolicy(MPOL_BIND, nodemask, maxnode);                            │
│                                                                            │
│   /* Prefer a node but allow others */                                     │
│   set_mempolicy(MPOL_PREFERRED, nodemask, maxnode);                       │
│                                                                            │
│   /* Interleave across nodes (for bandwidth) */                            │
│   set_mempolicy(MPOL_INTERLEAVE, nodemask, maxnode);                      │
│                                                                            │
│                                                                            │
│   COMMAND LINE:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Show NUMA topology                                                     │
│   numactl --hardware                                                       │
│                                                                            │
│   # Run on specific NUMA node                                              │
│   numactl --cpunodebind=0 --membind=0 ./myprogram                         │
│                                                                            │
│   # Show NUMA statistics                                                   │
│   numastat                                                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Summary and Appendix

### Scheduling System Calls Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING SYSTEM CALLS                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PRIORITY AND NICE VALUES:                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   nice(increment)           - Adjust nice value                           │
│   getpriority(which, who)   - Get scheduling priority                     │
│   setpriority(which, who, prio) - Set scheduling priority                 │
│                                                                            │
│                                                                            │
│   SCHEDULING POLICY:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   sched_setscheduler(pid, policy, param)  - Set scheduler and priority   │
│   sched_getscheduler(pid)                  - Get current scheduler        │
│   sched_setparam(pid, param)               - Set scheduling parameters   │
│   sched_getparam(pid, param)               - Get scheduling parameters   │
│   sched_setattr(pid, attr, flags)          - Extended scheduler config   │
│   sched_getattr(pid, attr, size, flags)    - Get extended config         │
│                                                                            │
│                                                                            │
│   YIELDING AND AFFINITY:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   sched_yield()                            - Voluntarily give up CPU     │
│   sched_setaffinity(pid, size, mask)       - Set CPU affinity mask       │
│   sched_getaffinity(pid, size, mask)       - Get CPU affinity mask       │
│                                                                            │
│                                                                            │
│   INFORMATION:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   sched_get_priority_max(policy)  - Get max priority for policy          │
│   sched_get_priority_min(policy)  - Get min priority for policy          │
│   sched_rr_get_interval(pid, tp)  - Get SCHED_RR time quantum            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Time System Calls Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TIME SYSTEM CALLS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   GETTING TIME:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   time(tloc)                         - Get time in seconds (epoch)        │
│   gettimeofday(tv, tz)               - Get time with microseconds        │
│   clock_gettime(clockid, tp)         - High-res time (nanoseconds)       │
│   clock_getres(clockid, res)         - Get clock resolution              │
│                                                                            │
│   Clock IDs:                                                               │
│   • CLOCK_REALTIME      - System-wide wall clock                          │
│   • CLOCK_MONOTONIC     - Monotonic since boot (for intervals)           │
│   • CLOCK_PROCESS_CPUTIME_ID - Process CPU time                          │
│   • CLOCK_THREAD_CPUTIME_ID  - Thread CPU time                           │
│                                                                            │
│                                                                            │
│   SLEEPING:                                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   sleep(seconds)                     - Sleep for seconds                  │
│   usleep(usec)                       - Sleep for microseconds            │
│   nanosleep(req, rem)                - Sleep for nanoseconds             │
│   clock_nanosleep(clockid, flags, req, rem) - High-res sleep             │
│                                                                            │
│                                                                            │
│   TIMERS:                                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   alarm(seconds)                     - Schedule SIGALRM                   │
│   setitimer(which, new, old)         - Set interval timer                │
│   getitimer(which, curr)             - Get interval timer                │
│   timer_create(clockid, evp, timerid)    - Create POSIX timer           │
│   timer_settime(timerid, flags, new, old) - Arm/disarm timer            │
│   timer_gettime(timerid, curr)            - Get timer remaining         │
│   timer_delete(timerid)                   - Delete timer                │
│                                                                            │
│                                                                            │
│   PROCESS TIME:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   times(buf)                         - Get process times (user/sys)      │
│   getrusage(who, usage)              - Get resource usage statistics     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Scheduling Policies Comparison

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCHEDULING POLICIES COMPARISON                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌──────────────┬────────────┬───────────┬─────────────┬──────────────┐ │
│   │   Policy     │  Priority  │ Time Slice│  Preemption │  Use Case    │ │
│   ├──────────────┼────────────┼───────────┼─────────────┼──────────────┤ │
│   │SCHED_DEADLINE│ (deadline) │ runtime   │By deadline  │Hard real-time│ │
│   │              │            │ parameter │             │              │ │
│   ├──────────────┼────────────┼───────────┼─────────────┼──────────────┤ │
│   │SCHED_FIFO    │  1-99      │ None      │Higher prio  │RT, single    │ │
│   │              │            │ (infinite)│only         │critical task │ │
│   ├──────────────┼────────────┼───────────┼─────────────┼──────────────┤ │
│   │SCHED_RR      │  1-99      │ Default   │Higher prio  │RT, multiple  │ │
│   │              │            │ 100ms     │or timeslice │equal tasks   │ │
│   ├──────────────┼────────────┼───────────┼─────────────┼──────────────┤ │
│   │SCHED_OTHER   │nice -20/+19│ Dynamic   │Yes (CFS)    │Normal tasks  │ │
│   │              │            │ (CFS)     │             │              │ │
│   ├──────────────┼────────────┼───────────┼─────────────┼──────────────┤ │
│   │SCHED_BATCH   │nice -20/+19│ Dynamic   │Yes (CFS)    │Batch jobs    │ │
│   │              │            │           │             │(CPU-bound)   │ │
│   ├──────────────┼────────────┼───────────┼─────────────┼──────────────┤ │
│   │SCHED_IDLE    │ Lowest     │ Dynamic   │Yes          │Background    │ │
│   │              │            │           │             │tasks only    │ │
│   └──────────────┴────────────┴───────────┴─────────────┴──────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│              PROCESS SCHEDULING AND TIME: THE BIG PICTURE                  │
│                                                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                     HARDWARE LAYER                                │    │
│   │                                                                   │    │
│   │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐         │    │
│   │   │   RTC   │   │   PIT   │   │   TSC   │   │  HPET   │         │    │
│   │   │ Battery │   │ Timer   │   │ Counter │   │ Hi-Res  │         │    │
│   │   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘         │    │
│   │        │             │             │             │               │    │
│   └────────┼─────────────┼─────────────┼─────────────┼───────────────┘    │
│            │             │             │             │                     │
│            ▼             ▼             ▼             ▼                     │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                      CLOCK HANDLER                                │    │
│   │                                                                   │    │
│   │   Every tick (HZ times/second):                                  │    │
│   │   • Update jiffies                                               │    │
│   │   • Charge CPU time to current process                          │    │
│   │   • Decay priorities                                             │    │
│   │   • Process callouts/timers                                      │    │
│   │   • Set runrun flag if quantum expired                          │    │
│   │                                                                   │    │
│   └───────────────────────────┬──────────────────────────────────────┘    │
│                               │                                            │
│                               ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                       SCHEDULER                                   │    │
│   │                                                                   │    │
│   │   ┌─────────────────────────────────────────────────────────┐    │    │
│   │   │              SCHEDULING CLASSES                          │    │    │
│   │   │                                                          │    │    │
│   │   │   stop_sched_class (highest)                            │    │    │
│   │   │         ▼                                                │    │    │
│   │   │   dl_sched_class (SCHED_DEADLINE)                       │    │    │
│   │   │         ▼                                                │    │    │
│   │   │   rt_sched_class (SCHED_FIFO, SCHED_RR)                 │    │    │
│   │   │         ▼                                                │    │    │
│   │   │   fair_sched_class (SCHED_OTHER - CFS)                  │    │    │
│   │   │         ▼                                                │    │    │
│   │   │   idle_sched_class (lowest)                             │    │    │
│   │   │                                                          │    │    │
│   │   └─────────────────────────────────────────────────────────┘    │    │
│   │                                                                   │    │
│   └───────────────────────────┬──────────────────────────────────────┘    │
│                               │                                            │
│                               ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                    PER-CPU RUN QUEUES                             │    │
│   │                                                                   │    │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │    │
│   │   │  CPU 0   │    │  CPU 1   │    │  CPU 2   │    │  CPU 3   │  │    │
│   │   │          │    │          │    │          │    │          │  │    │
│   │   │ CFS Tree │    │ CFS Tree │    │ CFS Tree │    │ CFS Tree │  │    │
│   │   │ RT Queue │    │ RT Queue │    │ RT Queue │    │ RT Queue │  │    │
│   │   │ DL Queue │    │ DL Queue │    │ DL Queue │    │ DL Queue │  │    │
│   │   │          │    │          │    │          │    │          │  │    │
│   │   └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │    │
│   │        │               │               │               │         │    │
│   │        └───────────────┴───────┬───────┴───────────────┘         │    │
│   │                                │                                  │    │
│   │                    LOAD BALANCER                                 │    │
│   │                    (migrate tasks between CPUs)                  │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   WHEN SCHEDULING HAPPENS:                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────┐                                                 │
│   │ • Process calls sleep/wait                                            │
│   │ • Process makes system call                                           │
│   │ • Clock interrupt (quantum expired)                                   │
│   │ • Higher priority process becomes runnable                            │
│   │ • Process exits                                                       │
│   │ • Process yields (sched_yield)                                        │
│   └─────────────────────┘                                                 │
│              │                                                             │
│              ▼                                                             │
│   ┌─────────────────────┐       ┌─────────────────────┐                   │
│   │   CONTEXT SWITCH    │ ───► │  NEW PROCESS RUNS   │                   │
│   │   • Save registers  │       │  on selected CPU    │                   │
│   │   • Switch stack    │       │                     │                   │
│   │   • Load new state  │       │                     │                   │
│   └─────────────────────┘       └─────────────────────┘                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 13. References

### Books

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ESSENTIAL READING                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PRIMARY SOURCE:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Maurice J. Bach                                                          │
│   "The Design of the UNIX Operating System"                               │
│   Prentice Hall, 1986                                                      │
│   ISBN: 0-13-201799-7                                                      │
│   Chapters 8 (Process Scheduling and Time) - The foundation of this doc  │
│                                                                            │
│                                                                            │
│   LINUX KERNEL:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Robert Love                                                              │
│   "Linux Kernel Development" (3rd Edition)                                │
│   Addison-Wesley, 2010                                                     │
│   ISBN: 978-0-672-32946-3                                                  │
│   Chapters 4 (Process Scheduling), 11 (Timers and Time Management)        │
│                                                                            │
│   Daniel P. Bovet & Marco Cesati                                          │
│   "Understanding the Linux Kernel" (3rd Edition)                          │
│   O'Reilly, 2005                                                           │
│   ISBN: 978-0-596-00565-8                                                  │
│   Chapters 7 (Process Scheduling), 6 (Timing Measurements)                │
│                                                                            │
│                                                                            │
│   SYSTEMS PROGRAMMING:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   W. Richard Stevens & Stephen A. Rago                                    │
│   "Advanced Programming in the UNIX Environment" (3rd Edition)            │
│   Addison-Wesley, 2013                                                     │
│   ISBN: 978-0-321-63773-4                                                  │
│   Chapters on Process Control, Signals, Time                              │
│                                                                            │
│   Michael Kerrisk                                                          │
│   "The Linux Programming Interface"                                       │
│   No Starch Press, 2010                                                    │
│   ISBN: 978-1-59327-220-3                                                  │
│   Chapters 35 (Process Priorities), 23 (Timers and Sleeping)             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Source Files

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX KERNEL SOURCE                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCHEDULER:                                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   kernel/sched/core.c         - Core scheduler implementation             │
│   kernel/sched/fair.c         - CFS (Completely Fair Scheduler)           │
│   kernel/sched/rt.c           - Real-time scheduler                       │
│   kernel/sched/deadline.c     - SCHED_DEADLINE implementation             │
│   kernel/sched/idle.c         - Idle task scheduling                      │
│   kernel/sched/sched.h        - Scheduler internal data structures        │
│   include/linux/sched.h       - task_struct definition                    │
│   include/linux/sched/prio.h  - Priority definitions                      │
│                                                                            │
│                                                                            │
│   TIME AND TIMERS:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   kernel/time/timer.c         - Timer wheel implementation                │
│   kernel/time/hrtimer.c       - High-resolution timers                    │
│   kernel/time/posix-timers.c  - POSIX timer implementation               │
│   kernel/time/time.c          - Time-related system calls                 │
│   kernel/time/clocksource.c   - Clock source abstraction                  │
│   kernel/time/tick-common.c   - Periodic tick handling                    │
│   include/linux/time.h        - Time structures                           │
│   include/linux/jiffies.h     - Jiffies definitions                       │
│                                                                            │
│                                                                            │
│   SMP AND LOAD BALANCING:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   kernel/sched/topology.c     - Scheduling domains                        │
│   kernel/sched/loadavg.c      - Load average calculation                  │
│   include/linux/cpumask.h     - CPU affinity masks                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Man Pages

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MAN PAGES                                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCHEDULING:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   sched(7)              - Overview of CPU scheduling                       │
│   sched_setscheduler(2) - Set scheduling policy and parameters            │
│   sched_setaffinity(2)  - Set CPU affinity mask                           │
│   nice(2)               - Change process priority                         │
│   setpriority(2)        - Set/get scheduling priority                     │
│   sched_yield(2)        - Yield the processor                             │
│                                                                            │
│                                                                            │
│   TIME:                                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   time(7)               - Overview of time and timers                      │
│   clock_gettime(2)      - Clock and time functions                        │
│   nanosleep(2)          - High-resolution sleep                           │
│   timer_create(2)       - Create a POSIX timer                            │
│   setitimer(2)          - Set interval timer                              │
│   alarm(2)              - Schedule SIGALRM signal                         │
│   times(2)              - Get process times                               │
│   getrusage(2)          - Get resource usage                              │
│                                                                            │
│                                                                            │
│   COMMANDS:                                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   nice(1)               - Run with modified scheduling priority           │
│   renice(1)             - Alter priority of running processes             │
│   chrt(1)               - Manipulate real-time attributes                 │
│   taskset(1)            - Set/retrieve CPU affinity                       │
│   numactl(8)            - Control NUMA policy                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Online Resources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ONLINE RESOURCES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KERNEL DOCUMENTATION:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Documentation/scheduler/sched-design-CFS.rst                            │
│   - CFS design document                                                   │
│                                                                            │
│   Documentation/scheduler/sched-deadline.rst                              │
│   - SCHED_DEADLINE documentation                                          │
│                                                                            │
│   Documentation/scheduler/sched-domains.rst                               │
│   - Scheduling domains explanation                                        │
│                                                                            │
│   Documentation/timers/                                                    │
│   - Timer subsystem documentation                                         │
│                                                                            │
│                                                                            │
│   ARTICLES AND PAPERS:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   "Inside the Linux 2.6 Completely Fair Scheduler"                        │
│   - IBM developerWorks (M. Tim Jones)                                     │
│                                                                            │
│   "The Linux Scheduler: A Decade of Wasted Cores"                         │
│   - EuroSys '16 (Lozi et al.)                                             │
│                                                                            │
│   "Earliest Deadline First Scheduling for Linux"                          │
│   - Real-Time Linux Kernel documentation                                  │
│                                                                            │
│   "EEVDF Scheduler" (kernel 6.6+)                                         │
│   - Latest fair scheduling algorithm                                      │
│                                                                            │
│                                                                            │
│   LWN.NET ARTICLES:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   "Scheduling in the kernel" series                                       │
│   "The BFS scheduler"                                                      │
│   "Deadline scheduling parts 1-3"                                         │
│   "CFS scheduler updates"                                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

_This document follows the pedagogical approach of Maurice J. Bach's "The Design of the UNIX Operating System", explaining process scheduling and time management from first principles through to modern implementations._
