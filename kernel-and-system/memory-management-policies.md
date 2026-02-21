# Memory Management Policies

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Swapping, Demand Paging, Page Replacement, Memory Allocation, and Virtual Memory

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The Memory Hierarchy](#the-memory-hierarchy)
   - [Why Memory Management?](#why-memory-management)
   - [Historical Context](#historical-context)

2. [Swapping](#2-swapping)
   - [What is Swapping?](#what-is-swapping)
   - [The Swapper Process](#the-swapper-process)
   - [Swap Space Management](#swap-space-management)
   - [When Swapping Occurs](#when-swapping-occurs)

3. [Demand Paging](#3-demand-paging)
   - [The Concept of Paging](#the-concept-of-paging)
   - [Page Tables](#page-tables)
   - [Page Faults](#page-faults)
   - [Demand Paging vs Swapping](#demand-paging-vs-swapping)

4. [The Page Cache](#4-the-page-cache)
   - [What is the Page Cache?](#what-is-the-page-cache)
   - [Page Cache Operations](#page-cache-operations)
   - [Dirty Pages and Writeback](#dirty-pages-and-writeback)

5. [Page Replacement Algorithms](#5-page-replacement-algorithms)
   - [The Page Replacement Problem](#the-page-replacement-problem)
   - [FIFO (First-In, First-Out)](#fifo-first-in-first-out)
   - [Optimal Algorithm](#optimal-algorithm)
   - [LRU (Least Recently Used)](#lru-least-recently-used)
   - [Clock Algorithm (Second Chance)](#clock-algorithm-second-chance)
   - [Linux Page Reclaim](#linux-page-reclaim)

6. [Working Set Model](#6-working-set-model)
   - [Locality of Reference](#locality-of-reference)
   - [Working Set Definition](#working-set-definition)
   - [Thrashing](#thrashing)

7. [Memory Allocation](#7-memory-allocation)
   - [Kernel Memory Allocation](#kernel-memory-allocation)
   - [The Buddy System](#the-buddy-system)
   - [Slab Allocator](#slab-allocator)
   - [User Space Allocation (malloc)](#user-space-allocation-malloc)

8. [Virtual Memory Implementation](#8-virtual-memory-implementation)
   - [Address Translation](#address-translation)
   - [Multi-Level Page Tables](#multi-level-page-tables)
   - [Translation Lookaside Buffer (TLB)](#translation-lookaside-buffer-tlb)
   - [Huge Pages](#huge-pages)

9. [Memory Mapped Files](#9-memory-mapped-files)
   - [The mmap() System Call](#the-mmap-system-call)
   - [Private vs Shared Mappings](#private-vs-shared-mappings)
   - [Copy-on-Write](#copy-on-write)

10. [Memory Protection](#10-memory-protection)
    - [Page Protection Bits](#page-protection-bits)
    - [Segmentation Faults](#segmentation-faults)
    - [Address Space Layout Randomization (ASLR)](#address-space-layout-randomization-aslr)

11. [Modern Memory Management](#11-modern-memory-management)
    - [NUMA Memory Policies](#numa-memory-policies)
    - [Memory Cgroups](#memory-cgroups)
    - [Transparent Huge Pages](#transparent-huge-pages)
    - [Memory Compaction](#memory-compaction)

12. [Summary and Appendix](#12-summary-and-appendix)
    - [Memory System Calls Quick Reference](#memory-system-calls-quick-reference)
    - [The Big Picture](#the-big-picture)

13. [References](#13-references)

---

## 1. Introduction

### The Memory Hierarchy

In any computer system, memory exists in a hierarchy—from fast, expensive, and small (CPU registers, cache) to slow, cheap, and large (disk, tape). The operating system's memory management subsystem bridges this gap, creating the illusion of abundant, fast memory.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE MEMORY HIERARCHY                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                        ┌─────────────┐                                     │
│                        │  Registers  │  ← Fastest (< 1ns)                 │
│                        │   (~1 KB)   │    Managed by compiler             │
│                        └──────┬──────┘                                     │
│                               │                                            │
│                        ┌──────▼──────┐                                     │
│                        │  L1 Cache   │  ← Very fast (~1ns)                │
│                        │  (32-64 KB) │    Managed by hardware             │
│                        └──────┬──────┘                                     │
│                               │                                            │
│                        ┌──────▼──────┐                                     │
│                        │  L2 Cache   │  ← Fast (~4ns)                     │
│                        │ (256KB-1MB) │    Managed by hardware             │
│                        └──────┬──────┘                                     │
│                               │                                            │
│                        ┌──────▼──────┐                                     │
│                        │  L3 Cache   │  ← Moderate (~10ns)                │
│                        │  (8-64 MB)  │    Shared across cores             │
│                        └──────┬──────┘                                     │
│                               │                                            │
│                        ┌──────▼──────┐                                     │
│                        │ Main Memory │  ← Slower (~100ns)                 │
│                        │  (GB-TB)    │    MANAGED BY OS ◄──────────────┐  │
│                        └──────┬──────┘                                 │  │
│                               │                                        │  │
│                        ┌──────▼──────┐                                 │  │
│                        │  Swap/Disk  │  ← Slowest (~10ms)              │  │
│                        │  (TB-PB)    │    MANAGED BY OS ◄──────────────┘  │
│                        └─────────────┘                                     │
│                                                                            │
│   The OS memory management subsystem manages the boundary between         │


```

### Why Memory Management?

The fundamental challenge of memory management stems from a simple reality: **there is never enough physical
memory**. Even with modern systems having gigabytes of RAM, the combined memory demands of all processes
typically exceed available physical memory.

```

┌───────────────────────────────────────────────────────────────────────────┐
│                    THE MEMORY MANAGEMENT PROBLEM                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO: System with 8 GB Physical RAM                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A (Web Browser)     : 2.5 GB                              │ │
│   │   Process B (IDE)             : 1.8 GB                              │ │
│   │   Process C (Database)        : 3.2 GB                              │ │
│   │   Process D (Email Client)    : 0.8 GB                              │ │
│   │   Process E (Slack)           : 1.2 GB                              │ │
│   │   Kernel + System             : 1.5 GB                              │ │
│   │   ─────────────────────────────────────                             │ │
│   │   TOTAL DEMAND                : 11.0 GB                             │ │
│   │                                                                      │ │
│   │   PHYSICAL MEMORY             : 8.0 GB                              │ │
│   │                                                                      │ │
│   │   SHORTFALL                   : 3.0 GB  ← Must be managed!         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MEMORY MANAGEMENT GOALS:                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   1. TRANSPARENCY                                                          │
│      Each process believes it has its own private address space           │
│      Processes don't know about physical memory limitations               │
│                                                                            │
│   2. EFFICIENCY                                                            │
│      Maximize memory utilization                                          │
│      Minimize wasted space (fragmentation)                                │
│                                                                            │
│   3. PROTECTION                                                            │
│      Processes cannot access each other's memory                          │
│      Kernel memory protected from user processes                          │
│                                                                            │
│   4. SHARING                                                               │
│      Allow controlled sharing (shared libraries, IPC)                     │
│      Share read-only code between processes                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

Maurice Bach describes the memory management challenge:

> "The memory management policies determine which processes reside in main memory so that they can execute, and they manage the parts of the virtual address space of a process that are not core resident."

### Historical Context

Memory management has evolved dramatically since the early days of computing:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF MEMORY MANAGEMENT                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1950s: NO MEMORY MANAGEMENT                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│   • One program at a time                                                  │
│   • Program loaded at fixed address                                        │
│   • Direct physical memory access                                          │
│   • No protection between programs                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Physical Memory                                                    │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                    Single Program                            │   │ │
│   │   │                    (owns all memory)                         │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   1960s: FIXED PARTITIONS                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│   • Memory divided into fixed-size partitions                             │
│   • One process per partition                                              │
│   • Internal fragmentation (wasted space within partitions)               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Physical Memory                                                    │ │
│   │   ┌───────────┬───────────┬───────────┬───────────┐                 │ │
│   │   │ Partition │ Partition │ Partition │ Partition │                 │ │
│   │   │     1     │     2     │     3     │     4     │                 │ │
│   │   │  (256KB)  │  (256KB)  │  (512KB)  │  (1MB)    │                 │ │
│   │   └───────────┴───────────┴───────────┴───────────┘                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   1970s: SWAPPING (Traditional UNIX)                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│   • Entire processes swapped to/from disk                                 │
│   • Variable-size partitions                                               │
│   • External fragmentation (holes between processes)                      │
│   • Process must fit entirely in memory to run                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Physical Memory                                                    │ │
│   │   ┌───────┬────┬──────────┬────┬─────────────┬────┬───────┐        │ │
│   │   │ Proc  │hole│  Proc    │hole│    Proc     │hole│ Proc  │        │ │
│   │   │   A   │    │    B     │    │      C      │    │   D   │        │ │
│   │   └───────┴────┴──────────┴────┴─────────────┴────┴───────┘        │ │
│   │                                                                      │ │
│   │   Swap Space (Disk)                                                  │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  Proc E  │  Proc F  │  Proc G  │  (free)  │  (free)  │      │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   1980s: DEMAND PAGING (BSD, System V)                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│   • Memory divided into fixed-size pages (typically 4KB)                  │
│   • Only needed pages loaded into memory                                  │
│   • Virtual memory: address space larger than physical memory             │
│   • Page replacement algorithms                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Virtual Address Space (per process)                                │ │
│   │   ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐    │ │
│   │   │ P0 │ P1 │ P2 │ P3 │ P4 │ P5 │ P6 │ P7 │ P8 │ P9 │P10 │P11 │    │ │
│   │   └──┬─┴──┬─┴──┬─┴────┴──┬─┴────┴──┬─┴────┴──┬─┴────┴──┬─┴────┘    │ │
│   │      │    │    │         │         │         │         │            │ │
│   │      │    │    │         │         │         │         │            │ │
│   │      ▼    ▼    ▼         ▼         ▼         ▼         ▼            │ │
│   │   Physical Memory (frames)                                           │ │
│   │   ┌────┬────┬────┬────┬────┬────┬────┬────┐                         │ │
│   │   │ F0 │ F1 │ F2 │ F3 │ F4 │ F5 │ F6 │ F7 │                         │ │
│   │   └────┴────┴────┴────┴────┴────┴────┴────┘                         │ │
│   │                                                                      │ │
│   │   Pages not in memory → Page Fault → Load from disk                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   2000s-Present: ADVANCED VIRTUAL MEMORY                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│   • Huge pages (2MB, 1GB)                                                  │
│   • NUMA-aware allocation                                                  │
│   • Memory cgroups for containers                                          │
│   • Transparent huge pages                                                 │
│   • Memory compaction                                                      │
│   • KSM (Kernel Same-page Merging)                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Swapping

### What is Swapping?

In traditional UNIX systems, **swapping** is the mechanism by which the kernel moves entire processes between main memory and secondary storage (the swap device). When memory becomes scarce, the kernel selects processes to swap out, freeing their memory for other processes.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SWAPPING CONCEPT                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SWAP OUT: Move process from memory to disk                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Main Memory                          Swap Device (Disk)                  │
│   ┌─────────────────────┐              ┌─────────────────────┐            │
│   │                     │              │                     │            │
│   │   ┌─────────────┐   │              │                     │            │
│   │   │  Process A  │───┼──────────────┼──►┌─────────────┐   │            │
│   │   │  (sleeping) │   │   SWAP OUT   │   │  Process A  │   │            │
│   │   └─────────────┘   │              │   │   (image)   │   │            │
│   │         ↓           │              │   └─────────────┘   │            │
│   │   ┌─────────────┐   │              │                     │            │
│   │   │    FREE     │   │              │                     │            │
│   │   │   MEMORY    │   │              │                     │            │
│   │   └─────────────┘   │              │                     │            │
│   │                     │              │                     │            │
│   └─────────────────────┘              └─────────────────────┘            │
│                                                                            │
│                                                                            │
│   SWAP IN: Move process from disk to memory                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Main Memory                          Swap Device (Disk)                  │
│   ┌─────────────────────┐              ┌─────────────────────┐            │
│   │                     │              │                     │            │
│   │   ┌─────────────┐   │              │   ┌─────────────┐   │            │
│   │   │  Process A  │◄──┼──────────────┼───│  Process A  │   │            │
│   │   │  (runnable) │   │   SWAP IN    │   │   (image)   │   │            │
│   │   └─────────────┘   │              │   └─────────────┘   │            │
│   │                     │              │         ↓           │            │
│   │                     │              │   ┌─────────────┐   │            │
│   │                     │              │   │    FREE     │   │            │
│   │                     │              │   │    SPACE    │   │            │
│   │                     │              │   └─────────────┘   │            │
│   └─────────────────────┘              └─────────────────────┘            │
│                                                                            │
│                                                                            │
│   KEY CHARACTERISTICS:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • ENTIRE process is moved (text, data, stack)                           │
│   • Process cannot run while swapped out                                  │
│   • Swap space must be large enough for all swapped processes             │
│   • Swapping is expensive (disk I/O is slow)                              │
│   • Used in early UNIX (PDP-11, VAX)                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Swapper Process

In traditional UNIX, process 0 (the **swapper** or **sched**) is responsible for managing the swapping of processes. It runs in kernel mode and never exits.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SWAPPER (PROCESS 0)                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KERNEL ALGORITHM: swapper                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   algorithm swapper                                                        │
│   input:  none                                                             │
│   output: none                                                             │
│   {                                                                        │
│       loop:                                                                │
│           /* SWAP IN: Find process to bring into memory */                │
│           for (all swapped out processes that are ready to run)           │
│               pick process swapped out longest;                           │
│                                                                            │
│           if (no such process)                                             │
│           {                                                                │
│               sleep (event: must swap in);                                 │
│               goto loop;                                                   │
│           }                                                                │
│                                                                            │
│           if (enough memory for process)                                   │
│           {                                                                │
│               swap process in;                                             │
│               goto loop;                                                   │
│           }                                                                │
│                                                                            │
│           /* SWAP OUT: Need to free memory */                              │
│           for (all processes loaded in main memory, not zombie, not locked)│
│           {                                                                │
│               if (process sleeping)                                        │
│                   choose process sleeping longest;                         │
│               else                                                         │
│                   choose process with lowest priority;                     │
│           }                                                                │
│                                                                            │
│           if (chosen process not sleeping or                               │
│               chosen process resident less than 2 seconds)                 │
│           {                                                                │
│               sleep (event: must swap process out);                        │
│               goto loop;                                                   │
│           }                                                                │
│                                                                            │
│           swap out chosen process;                                         │
│           goto loop;                                                       │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   SWAPPER STATE DIAGRAM:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│                    ┌─────────────────────────────────────┐                 │
│                    │                                     │                 │
│                    ▼                                     │                 │
│   ┌─────────────────────────────┐                       │                 │
│   │  Look for process to       │                       │                 │
│   │  swap in                   │                       │                 │
│   └─────────────┬───────────────┘                       │                 │
│                 │                                       │                 │
│        ┌────────┴────────┐                              │                 │
│        │                 │                              │                 │
│        ▼                 ▼                              │                 │
│   ┌─────────┐      ┌─────────────┐                     │                 │
│   │  None   │      │   Found     │                     │                 │
│   │  found  │      │  process    │                     │                 │
│   └────┬────┘      └──────┬──────┘                     │                 │
│        │                  │                             │                 │
│        ▼                  ▼                             │                 │
│   ┌─────────┐      ┌─────────────┐                     │                 │
│   │  Sleep  │      │ Enough      │──Yes──► Swap In ────┘                 │
│   │         │      │ memory?     │                                        │
│   └─────────┘      └──────┬──────┘                                        │
│                           │ No                                             │
│                           ▼                                                │
│                    ┌─────────────┐                                         │
│                    │ Find process│                                         │
│                    │ to swap out │                                         │
│                    └──────┬──────┘                                         │
│                           │                                                │
│                           ▼                                                │
│                    ┌─────────────┐                                         │
│                    │  Swap Out   │─────────────────────────────────────┐   │
│                    └─────────────┘                                     │   │
│                                                                        │   │
│                    ┌───────────────────────────────────────────────────┘   │
│                    │                                                       │
│                    └───────────────────────────────────────────────────────┘
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Swap Space Management

The kernel manages swap space on disk, allocating and freeing regions as processes are swapped out and in.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SWAP SPACE MANAGEMENT                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SWAP MAP (Traditional UNIX):                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   The kernel maintains a map of swap space allocation:                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Swap Device                                                        │ │
│   │   ┌────────┬────────┬────────┬────────┬────────┬────────┬────────┐  │ │
│   │   │ Block  │ Block  │ Block  │ Block  │ Block  │ Block  │ Block  │  │ │
│   │   │   0    │   1    │   2    │   3    │   4    │   5    │   6    │  │ │
│   │   └────────┴────────┴────────┴────────┴────────┴────────┴────────┘  │ │
│   │      ↑        ↑        ↑        ↑        ↑        ↑        ↑        │ │
│   │      │        │        │        │        │        │        │        │ │
│   │   ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐   │ │
│   │   │Proc │  │Proc │  │Proc │  │FREE │  │Proc │  │Proc │  │FREE │   │ │
│   │   │  A  │  │  A  │  │  B  │  │     │  │  B  │  │  C  │  │     │   │ │
│   │   └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Swap Map (in kernel):                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Index │ Address │ Size  │ Status                                  │ │
│   │   ──────┼─────────┼───────┼────────                                 │ │
│   │     0   │    0    │   2   │ Allocated (Process A)                   │ │
│   │     1   │    2    │   1   │ Allocated (Process B)                   │ │
│   │     2   │    3    │   1   │ Free                                    │ │
│   │     3   │    4    │   2   │ Allocated (Process B, C)                │ │
│   │     4   │    6    │   1   │ Free                                    │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   LINUX SWAP MANAGEMENT:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Modern Linux uses a more sophisticated approach:                        │
│                                                                            │
│   • Multiple swap devices with priorities                                  │
│   • Swap files (not just partitions)                                      │
│   • Per-page swap tracking                                                 │
│   • Swap cache for recently swapped pages                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   # View swap configuration                                          │ │
│   │   $ swapon --show                                                    │ │
│   │   NAME      TYPE      SIZE   USED  PRIO                             │ │
│   │   /dev/sda2 partition 8G     1.2G  -2                               │ │
│   │   /swapfile file      4G     0B    -3                               │ │
│   │                                                                      │ │
│   │   # Add swap file                                                    │ │
│   │   $ dd if=/dev/zero of=/swapfile bs=1G count=4                      │ │
│   │   $ mkswap /swapfile                                                 │ │
│   │   $ swapon /swapfile                                                 │ │
│   │                                                                      │ │
│   │   # View swap usage                                                  │ │
│   │   $ free -h                                                          │ │
│   │                 total   used   free   shared  buff/cache  available │ │
│   │   Mem:          16Gi   8.2Gi  2.1Gi   512Mi      5.7Gi      7.1Gi  │ │
│   │   Swap:         12Gi   1.2Gi  10.8Gi                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### When Swapping Occurs

The kernel decides to swap processes based on memory pressure and process state:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SWAPPING DECISIONS                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SWAP OUT CRITERIA (Traditional UNIX):                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Priority for swapping OUT (highest to lowest):                          │
│                                                                            │
│   1. Sleeping processes (longest sleep time first)                        │
│   2. Stopped processes                                                     │
│   3. Ready-to-run processes (lowest priority first)                       │
│   4. Recently loaded processes (avoid thrashing)                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process Selection Formula:                                         │ │
│   │                                                                      │ │
│   │   swap_priority = (time_sleeping * 2) + nice_value                  │ │
│   │                                                                      │ │
│   │   Higher swap_priority → More likely to be swapped out              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SWAP IN CRITERIA:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Priority for swapping IN (highest to lowest):                           │
│                                                                            │
│   1. Processes swapped out longest                                        │
│   2. Higher priority processes                                             │
│   3. Processes with pending signals                                        │
│                                                                            │
│                                                                            │
│   LINUX SWAPPINESS:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Modern Linux uses the "swappiness" parameter (0-100):                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   swappiness = 0   → Avoid swapping, prefer dropping file cache     │ │
│   │   swappiness = 60  → Default balance                                 │ │
│   │   swappiness = 100 → Aggressively swap anonymous pages              │ │
│   │                                                                      │ │
│   │   # View current swappiness                                          │ │
│   │   $ cat /proc/sys/vm/swappiness                                      │ │
│   │   60                                                                 │ │
│   │                                                                      │ │
│   │   # Set swappiness (temporary)                                       │ │
│   │   $ echo 10 > /proc/sys/vm/swappiness                               │ │
│   │                                                                      │ │
│   │   # Set swappiness (permanent)                                       │ │
│   │   $ echo "vm.swappiness=10" >> /etc/sysctl.conf                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Demand Paging

### The Concept of Paging

**Demand paging** revolutionized memory management by allowing processes to run without having their entire address space in memory. Instead, memory is divided into fixed-size units called **pages**, and only the pages currently needed are loaded.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGING FUNDAMENTALS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KEY CONCEPTS:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   PAGE:   Fixed-size block of virtual memory (typically 4KB)              │
│   FRAME:  Fixed-size block of physical memory (same size as page)         │
│   PAGE TABLE: Maps virtual pages to physical frames                       │
│                                                                            │
│                                                                            │
│   VIRTUAL ADDRESS STRUCTURE (32-bit, 4KB pages):                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   31                    12 11                    0                   │ │
│   │   ┌────────────────────────┬────────────────────────┐               │ │
│   │   │     Page Number        │     Page Offset        │               │ │
│   │   │      (20 bits)         │      (12 bits)         │               │ │
│   │   └────────────────────────┴────────────────────────┘               │ │
│   │                                                                      │ │
│   │   Page Number: Which page (2^20 = 1M pages possible)                │ │
│   │   Page Offset: Byte within page (2^12 = 4096 bytes)                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   ADDRESS TRANSLATION:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Virtual Address: 0x00403ABC                                       │ │
│   │                                                                      │ │
│   │   ┌────────────────────────┬────────────────────────┐               │ │
│   │   │   Page Number: 0x403   │   Offset: 0xABC        │               │ │
│   │   └───────────┬────────────┴────────────────────────┘               │ │
│   │               │                                                      │ │
│   │               ▼                                                      │ │
│   │   ┌─────────────────────────────────────────────────┐               │ │
│   │   │              PAGE TABLE                          │               │ │
│   │   │   ┌───────────┬───────────────────────────────┐ │               │ │
│   │   │   │   Index   │   Frame Number + Flags        │ │               │ │
│   │   │   ├───────────┼───────────────────────────────┤ │               │ │
│   │   │   │   0x403   │   0x7F2 | Present | RW        │ │               │ │
│   │   │   └───────────┴───────────────────────────────┘ │               │ │
│   │   └───────────┬─────────────────────────────────────┘               │ │
│   │               │                                                      │ │
│   │               ▼                                                      │ │
│   │   Physical Address: 0x7F2ABC                                        │ │
│   │   (Frame 0x7F2, Offset 0xABC)                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Page Tables

The **page table** is the data structure that maps virtual pages to physical frames. Each process has its own page table, providing memory isolation.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE TABLE STRUCTURE                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PAGE TABLE ENTRY (PTE) - 32-bit System:                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ 31                           12 11  9 8 7 6 5 4 3 2 1 0           │  │
│   │ ┌──────────────────────────────┬─────┬─┬─┬─┬─┬─┬─┬─┬─┬─┐          │  │
│   │ │    Frame Number (20 bits)    │ AVL │G│0│D│A│C│W│U│R│P│          │  │
│   │ └──────────────────────────────┴─────┴─┴─┴─┴─┴─┴─┴─┴─┴─┘          │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   Flag bits:                                                               │
│   ┌─────────┬────────────────────────────────────────────────────────────┐│
│   │  Bit    │  Meaning                                                   ││
│   ├─────────┼────────────────────────────────────────────────────────────┤│
│   │  P (0)  │  Present: Page is in physical memory                      ││
│   │  R (1)  │  Read/Write: 0=read-only, 1=read-write                    ││
│   │  U (2)  │  User/Supervisor: 0=kernel only, 1=user accessible        ││
│   │  W (3)  │  Write-Through: Cache write policy                        ││
│   │  C (4)  │  Cache Disable: Don't cache this page                     ││
│   │  A (5)  │  Accessed: Page has been read                             ││
│   │  D (6)  │  Dirty: Page has been written to                          ││
│   │  G (8)  │  Global: Don't flush from TLB on context switch           ││
│   │  AVL    │  Available for OS use                                      ││
│   └─────────┴────────────────────────────────────────────────────────────┘│
│                                                                            │
│                                                                            │
│   PROCESS PAGE TABLES:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A                           Process B                     │ │
│   │   ┌─────────────┐                     ┌─────────────┐               │ │
│   │   │ Page Table  │                     │ Page Table  │               │ │
│   │   ├─────────────┤                     ├─────────────┤               │ │
│   │   │ VP 0 → F 5  │                     │ VP 0 → F 12 │               │ │
│   │   │ VP 1 → F 8  │                     │ VP 1 → F 3  │               │ │
│   │   │ VP 2 → F 2  │                     │ VP 2 → F 8  │ ← Shared!     │ │
│   │   │ VP 3 → SWAP │                     │ VP 3 → F 15 │               │ │
│   │   └─────────────┘                     └─────────────┘               │ │
│   │         │                                   │                        │ │
│   │         │                                   │                        │ │
│   │         ▼                                   ▼                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                    PHYSICAL MEMORY                          │   │ │
│   │   │   ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐      │   │ │
│   │   │   │ F0 │ F1 │ F2 │ F3 │ F4 │ F5 │ F6 │ F7 │ F8 │... │      │   │ │
│   │   │   └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘      │   │ │
│   │   │         ↑ A        ↑ B        ↑ A             ↑ A,B         │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Page Faults

A **page fault** occurs when a process accesses a page that is not currently in physical memory. The kernel must handle this by loading the page from disk.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE FAULT HANDLING                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TYPES OF PAGE FAULTS:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   MINOR PAGE FAULT (Soft Fault):                                    │ │
│   │   • Page is in memory but not mapped in page table                  │ │
│   │   • Example: Copy-on-Write, shared library already loaded           │ │
│   │   • Resolution: Update page table, no disk I/O                      │ │
│   │   • Cost: ~1-10 microseconds                                         │ │
│   │                                                                      │ │
│   │   MAJOR PAGE FAULT (Hard Fault):                                    │ │
│   │   • Page must be loaded from disk (swap or file)                    │ │
│   │   • Resolution: Read from disk, update page table                   │ │
│   │   • Cost: ~1-10 milliseconds (1000x slower!)                        │ │
│   │                                                                      │ │
│   │   INVALID PAGE FAULT:                                               │ │
│   │   • Access to unmapped or protected memory                          │ │
│   │   • Resolution: SIGSEGV signal (segmentation fault)                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KERNEL ALGORITHM: page_fault_handler                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   algorithm page_fault_handler                                             │
│   input:  faulting_address, error_code                                    │
│   output: none (process resumes or receives signal)                       │
│   {                                                                        │
│       vma = find_vma(current->mm, faulting_address);                      │
│                                                                            │
│       if (vma == NULL || faulting_address < vma->vm_start)                │
│       {                                                                    │
│           /* Invalid access - no VMA covers this address */               │
│           send_signal(SIGSEGV, current);                                  │
│           return;                                                          │
│       }                                                                    │
│                                                                            │
│       if (access_violation(vma, error_code))                              │
│       {                                                                    │
│           /* Permission denied (e.g., write to read-only) */              │
│           send_signal(SIGSEGV, current);                                  │
│           return;                                                          │
│       }                                                                    │
│                                                                            │
│       /* Valid page fault - handle it */                                  │
│       if (page_in_swap(vma, faulting_address))                            │
│       {                                                                    │
│           /* Major fault: read from swap */                               │
│           page = alloc_page();                                             │
│           read_swap(swap_entry, page);                                    │
│           install_page(vma, faulting_address, page);                      │
│       }                                                                    │
│       else if (file_backed(vma))                                          │
│       {                                                                    │
│           /* Major fault: read from file */                               │
│           page = alloc_page();                                             │
│           read_file(vma->vm_file, offset, page);                          │
│           install_page(vma, faulting_address, page);                      │
│       }                                                                    │
│       else                                                                 │
│       {                                                                    │
│           /* Anonymous page: allocate zero-filled page */                 │
│           page = alloc_zero_page();                                       │
│           install_page(vma, faulting_address, page);                      │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Demand Paging vs Swapping

Understanding the difference between traditional swapping and demand paging is crucial:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SWAPPING vs DEMAND PAGING                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   TRADITIONAL SWAPPING:                                              │ │
│   │   ─────────────────────────────────────────────────────────────────  │ │
│   │                                                                      │ │
│   │   • Entire process moved to/from disk                               │ │
│   │   • All-or-nothing approach                                          │ │
│   │   • Simple implementation                                            │ │
│   │   • Expensive context switches                                       │ │
│   │   • Used in early UNIX (PDP-11, VAX)                                │ │
│   │                                                                      │ │
│   │   ┌───────────┐                        ┌───────────┐                │ │
│   │   │  Process  │◄─────SWAP OUT──────────│  Memory   │                │ │
│   │   │ (on disk) │──────SWAP IN──────────►│           │                │ │
│   │   └───────────┘                        └───────────┘                │ │
│   │   (Entire process)                     (All pages at once)          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   DEMAND PAGING:                                                     │ │
│   │   ─────────────────────────────────────────────────────────────────  │ │
│   │                                                                      │ │
│   │   • Individual pages moved to/from disk                             │ │
│   │   • Load only what's needed (lazy loading)                          │ │
│   │   • More complex implementation                                      │ │
│   │   • Efficient memory usage                                           │ │
│   │   • Used in modern systems (Linux, BSD, Windows)                    │ │
│   │                                                                      │ │
│   │   ┌───────────┐                        ┌───────────┐                │ │
│   │   │   Swap    │◄─────PAGE OUT──────────│  Memory   │                │ │
│   │   │  Space    │──────PAGE IN───────────►│           │                │ │
│   │   └───────────┘                        └───────────┘                │ │
│   │   (One page)                           (Individual pages)           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   COMPARISON TABLE:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌────────────────────┬─────────────────────┬────────────────────────┐   │
│   │  Aspect            │  Swapping           │  Demand Paging         │   │
│   ├────────────────────┼─────────────────────┼────────────────────────┤   │
│   │  Unit of transfer  │  Entire process     │  Single page (4KB)     │   │
│   │  Memory overhead   │  High               │  Low                    │   │
│   │  Startup time      │  Must load all      │  Start with few pages   │   │
│   │  Granularity       │  Coarse             │  Fine                   │   │
│   │  Thrashing risk    │  Lower              │  Higher                 │   │
│   │  Implementation    │  Simple             │  Complex                │   │
│   │  Hardware need     │  None special       │  MMU with page tables   │   │
│   └────────────────────┴─────────────────────┴────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Page Cache

### What is the Page Cache?

The **page cache** (also called buffer cache in traditional UNIX) is an in-memory cache of file data. When reading from or writing to files, the kernel first checks the page cache.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE PAGE CACHE                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PURPOSE:                                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Speed up file access by caching disk data in memory                  │
│   • Reduce disk I/O (reads and writes)                                   │
│   • Share file data between processes                                     │
│   • Support memory-mapped files                                           │
│                                                                            │
│                                                                            │
│   PAGE CACHE ARCHITECTURE:                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A          Process B          Process C                   │ │
│   │      │                  │                   │                        │ │
│   │      │  read()          │  mmap()           │  read()               │ │
│   │      │                  │                   │                        │ │
│   │      ▼                  ▼                   ▼                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                      VFS LAYER                               │   │ │
│   │   └───────────────────────────┬─────────────────────────────────┘   │ │
│   │                               │                                      │ │
│   │                               ▼                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                     PAGE CACHE                               │   │ │
│   │   │   ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐        │   │ │
│   │   │   │Page 0│Page 1│Page 2│Page 3│Page 4│Page 5│ ...  │        │   │ │
│   │   │   │File A│File A│File B│File A│File C│File B│      │        │   │ │
│   │   │   └──────┴──────┴──────┴──────┴──────┴──────┴──────┘        │   │ │
│   │   │                                                              │   │ │
│   │   │   Indexed by: (inode, offset)                               │   │ │
│   │   └───────────────────────────┬─────────────────────────────────┘   │ │
│   │                               │ cache miss                           │ │
│   │                               ▼                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                      DISK                                    │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Page Cache Operations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE CACHE OPERATIONS                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   READ OPERATION:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   read(fd, buf, count)                                              │ │
│   │         │                                                            │ │
│   │         ▼                                                            │ │
│   │   ┌─────────────────────────┐                                       │ │
│   │   │ Check page cache        │                                       │ │
│   │   │ for (inode, offset)     │                                       │ │
│   │   └───────────┬─────────────┘                                       │ │
│   │               │                                                      │ │
│   │         ┌─────┴─────┐                                               │ │
│   │         │           │                                               │ │
│   │    Cache Hit   Cache Miss                                           │ │
│   │         │           │                                               │ │
│   │         │           ▼                                               │ │
│   │         │    ┌─────────────────────┐                                │ │
│   │         │    │ Allocate page       │                                │ │
│   │         │    │ Read from disk      │                                │ │
│   │         │    │ Add to page cache   │                                │ │
│   │         │    └──────────┬──────────┘                                │ │
│   │         │               │                                            │ │
│   │         ▼               ▼                                            │ │
│   │   ┌─────────────────────────┐                                       │ │
│   │   │ Copy data to user buf   │                                       │ │
│   │   └─────────────────────────┘                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WRITE OPERATION:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   write(fd, buf, count)                                             │ │
│   │         │                                                            │ │
│   │         ▼                                                            │ │
│   │   ┌─────────────────────────┐                                       │ │
│   │   │ Find/create page in     │                                       │ │
│   │   │ page cache              │                                       │ │
│   │   └───────────┬─────────────┘                                       │ │
│   │               │                                                      │ │
│   │               ▼                                                      │ │
│   │   ┌─────────────────────────┐                                       │ │
│   │   │ Copy data from user buf │                                       │ │
│   │   │ Mark page as DIRTY      │                                       │ │
│   │   └───────────┬─────────────┘                                       │ │
│   │               │                                                      │ │
│   │               ▼                                                      │ │
│   │   ┌─────────────────────────┐                                       │ │
│   │   │ Return to user          │                                       │ │
│   │   │ (write complete)        │                                       │ │
│   │   └─────────────────────────┘                                       │ │
│   │               │                                                      │ │
│   │               │ Later (async)...                                    │ │
│   │               ▼                                                      │ │
│   │   ┌─────────────────────────┐                                       │ │
│   │   │ pdflush/writeback       │                                       │ │
│   │   │ thread writes to disk   │                                       │ │
│   │   └─────────────────────────┘                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Dirty Pages and Writeback

**Dirty pages** are cached pages that have been modified but not yet written to disk. The kernel periodically flushes dirty pages through the writeback mechanism.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DIRTY PAGES AND WRITEBACK                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PAGE STATES:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CLEAN:  Page matches disk content                                 │ │
│   │           Can be reclaimed immediately                              │ │
│   │                                                                      │ │
│   │   DIRTY:  Page modified, not yet written to disk                   │ │
│   │           Must be written before reclaiming                        │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                              │   │ │
│   │   │   ┌─────────┐       write()       ┌─────────┐               │   │ │
│   │   │   │  CLEAN  │────────────────────►│  DIRTY  │               │   │ │
│   │   │   │         │◄────────────────────│         │               │   │ │
│   │   │   └─────────┘     writeback       └─────────┘               │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WRITEBACK TRIGGERS:                                                      │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Periodic (every 5 seconds by default)                                 │
│   • When dirty pages exceed threshold (dirty_ratio)                       │
│   • When dirty pages exceed background threshold (dirty_background_ratio) │
│   • Explicit sync() or fsync() call                                       │
│   • File close or unmount                                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   # View dirty page settings                                        │ │
│   │   $ cat /proc/sys/vm/dirty_ratio                                    │ │
│   │   20                                                                │ │
│   │                                                                      │ │
│   │   $ cat /proc/sys/vm/dirty_background_ratio                         │ │
│   │   10                                                                │ │
│   │                                                                      │ │
│   │   $ cat /proc/sys/vm/dirty_expire_centisecs                         │ │
│   │   3000    # 30 seconds                                              │ │
│   │                                                                      │ │
│   │   # View current dirty pages                                        │ │
│   │   $ grep -i dirty /proc/meminfo                                     │ │
│   │   Dirty:              1234 kB                                       │ │
│   │   Writeback:           567 kB                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Page Replacement Algorithms

### The Page Replacement Problem

When physical memory is full and a new page must be loaded, the kernel must choose a **victim page** to evict. The choice of page replacement algorithm significantly affects system performance.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE REPLACEMENT ALGORITHMS                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FIFO (First-In, First-Out):                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Evict the page that has been in memory longest                        │
│   • Simple to implement (just a queue)                                    │
│   • Poor performance (ignores actual usage)                               │
│   • Suffers from Bélády's anomaly                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Reference: A B C D A B E A B C D E                                │ │
│   │   Frames: 3                                                          │ │
│   │                                                                      │ │
│   │   [A][ ][ ] → [A][B][ ] → [A][B][C] → [D][B][C] → [D][A][C]        │ │
│   │     ↑           ↑   ↑       ↑              ↑            ↑            │ │
│   │    load        load load   evict A       evict B                    │ │
│   │                                                                      │ │
│   │   Page faults: 9                                                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   OPTIMAL (OPT):                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Evict page that won't be used for longest time in future             │
│   • Impossible to implement (requires future knowledge!)                  │
│   • Used as theoretical benchmark                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Reference: A B C D A B E A B C D E                                │ │
│   │   Frames: 3                                                          │ │
│   │                                                                      │ │
│   │   [A][ ][ ] → [A][B][ ] → [A][B][C] → [A][B][D] → [E][B][D]        │ │
│   │                                 ↑             ↑                      │ │
│   │                           evict C (used last)   evict A             │ │
│   │                                                                      │ │
│   │   Page faults: 7 (minimum possible)                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   LRU (Least Recently Used):                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Evict page that hasn't been used for longest time                    │
│   • Good approximation of optimal                                         │
│   • Exploits temporal locality                                            │
│   • Expensive to implement perfectly (need timestamps or stack)          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Reference: A B C D A B E A B C D E                                │ │
│   │   Frames: 3                                                          │ │
│   │                                                                      │ │
│   │   Usage tracking: Most recent ←→ Least recent                       │ │
│   │                                                                      │ │
│   │   [A][ ][ ] → [A][B][ ] → [A][B][C] → [D][B][C] → [D][A][C]        │ │
│   │                                 ↑                                    │ │
│   │                           evict A (LRU)                              │ │
│   │                                                                      │ │
│   │   Page faults: 8                                                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Clock Algorithm (Second Chance)

The **Clock algorithm** is a practical approximation of LRU used by most operating systems, including Linux.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CLOCK ALGORITHM (SECOND CHANCE)                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CONCEPT:                                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Pages arranged in circular buffer (clock)                             │
│   • Each page has a "reference bit" (R bit)                               │
│   • R bit set to 1 when page is accessed                                  │
│   • Clock hand points to oldest page                                      │
│                                                                            │
│   ALGORITHM:                                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   When page fault occurs:                                                  │
│   1. Check page at clock hand                                             │
│   2. If R=0: Evict this page                                              │
│   3. If R=1: Clear R bit, advance hand, goto 1                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │                        CLOCK                                         │ │
│   │                                                                      │ │
│   │                     ┌─────┐                                          │ │
│   │                     │  A  │ R=1                                      │ │
│   │                ┌────┴─────┴────┐                                     │ │
│   │                │               │                                      │ │
│   │           ┌────┴┐           ┌─┴────┐                                 │ │
│   │           │  H  │ R=0       │  B  │ R=1                              │ │
│   │           └────┬┘           └─┬────┘                                 │ │
│   │                │               │                                      │ │
│   │           ┌────┴┐           ┌─┴────┐                                 │ │
│   │           │  G  │ R=1       │  C  │ R=0 ◄── Clock hand              │ │
│   │           └────┬┘           └─┬────┘                                 │ │
│   │                │               │                                      │ │
│   │                └────┬─────┬────┘                                     │ │
│   │                ┌────┴┐   ┌┴────┐                                     │ │
│   │                │  F  │   │  D  │                                     │ │
│   │                │ R=0 │   │ R=1 │                                     │ │
│   │                └─────┘   └─────┘                                     │ │
│   │                     │                                                │ │
│   │                 ┌───┴───┐                                            │ │
│   │                 │   E   │ R=1                                        │ │
│   │                 └───────┘                                            │ │
│   │                                                                      │ │
│   │   On page fault: C has R=0, evict C!                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Linux Page Reclaim

Linux uses a sophisticated page reclaim system with **kswapd** for background reclaim and **direct reclaim** when memory is critically low.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX PAGE RECLAIM                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   LRU LISTS (Linux uses multiple LRU lists):                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Active Anonymous:   Recently accessed anonymous pages             │ │
│   │   Inactive Anonymous: Candidates for swap out                       │ │
│   │                                                                      │ │
│   │   Active File:        Recently accessed file-backed pages           │ │
│   │   Inactive File:      Candidates for reclaim                        │ │
│   │                                                                      │ │
│   │   Unevictable:        mlock'd pages, never reclaim                 │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   ┌─────────────┐         ┌─────────────┐                          │ │
│   │   │   Active    │◄───────►│  Inactive   │                          │ │
│   │   │    List     │ promote │    List     │                          │ │
│   │   │             │ demote  │             │                          │ │
│   │   └─────────────┘         └──────┬──────┘                          │ │
│   │                                  │                                   │ │
│   │                                  ▼                                   │ │
│   │                           ┌─────────────┐                           │ │
│   │                           │   Reclaim   │                           │ │
│   │                           │  (free or   │                           │ │
│   │                           │  write out) │                           │ │
│   │                           └─────────────┘                           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   RECLAIM TRIGGERS:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Memory Watermarks:                                                │ │
│   │                                                                      │ │
│   │   ┌────────────────────────────────────────────────────────────┐    │ │
│   │   │ HIGH ─────────────────────────────────────────────────────│    │ │
│   │   │        kswapd stops                                       │    │ │
│   │   │ LOW  ─────────────────────────────────────────────────────│    │ │
│   │   │        kswapd starts (background reclaim)                 │    │ │
│   │   │ MIN  ─────────────────────────────────────────────────────│    │ │
│   │   │        Direct reclaim (synchronous, blocks allocator)     │    │ │
│   │   │                                                           │    │ │
│   │   │ 0    ─────────────────────────────────────────────────────│    │ │
│   │   │        OOM killer invoked                                 │    │ │
│   │   └────────────────────────────────────────────────────────────┘    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MONITORING RECLAIM:                                                      │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   # View LRU list sizes                                             │ │
│   │   $ cat /proc/meminfo | grep -E "Active|Inactive"                   │ │
│   │   Active:           4521984 kB                                      │ │
│   │   Inactive:         2341232 kB                                      │ │
│   │   Active(anon):     1234567 kB                                      │ │
│   │   Inactive(anon):    567890 kB                                      │ │
│   │   Active(file):     3287417 kB                                      │ │
│   │   Inactive(file):   1773342 kB                                      │ │
│   │                                                                      │ │
│   │   # View reclaim statistics                                         │ │
│   │   $ cat /proc/vmstat | grep -E "pgsteal|pgscan"                     │ │
│   │   pgscan_kswapd 1234567                                             │ │
│   │   pgscan_direct 12345                                               │ │
│   │   pgsteal_kswapd 1200000                                            │ │
│   │   pgsteal_direct 12000                                              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Working Set Model

### Locality of Reference

Programs exhibit **locality of reference**: they tend to access the same memory locations (or nearby locations) repeatedly over short periods of time.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LOCALITY OF REFERENCE                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TEMPORAL LOCALITY:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   If a memory location is accessed, it's likely to be accessed            │
│   again soon.                                                              │
│                                                                            │
│   Examples:                                                                │
│   • Loop variables (for i = 0; i < n; i++)                                │
│   • Stack variables in active functions                                   │
│   • Frequently called functions                                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Time ──────────────────────────────────────────────────────────►  │ │
│   │                                                                      │ │
│   │   Address X accessed:  *    *    *    *    *    *    *    *        │ │
│   │                                                                      │ │
│   │   Same location accessed repeatedly over time                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SPATIAL LOCALITY:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   If a memory location is accessed, nearby locations are likely to       │
│   be accessed soon.                                                        │
│                                                                            │
│   Examples:                                                                │
│   • Array traversal (a[0], a[1], a[2], ...)                              │
│   • Sequential instruction execution                                      │
│   • Struct field access                                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Memory addresses:                                                  │ │
│   │                                                                      │ │
│   │   ┌────┬────┬────┬────┬────┬────┬────┬────┐                        │ │
│   │   │ 0  │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │                        │ │
│   │   └────┴────┴────┴────┴────┴────┴────┴────┘                        │ │
│   │     ↑    ↑    ↑    ↑    ↑                                           │ │
│   │    t=1  t=2  t=3  t=4  t=5                                          │ │
│   │                                                                      │ │
│   │   Sequential access pattern                                          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Working Set

The **working set** of a process at time t is the set of pages it has referenced during the past Δ time units (the working set window).

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE WORKING SET                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DEFINITION:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   W(t, Δ) = set of pages referenced in interval (t - Δ, t]               │
│                                                                            │
│   Where:                                                                   │
│   • t = current time                                                      │
│   • Δ = working set window (time interval)                                │
│   • |W(t, Δ)| = working set size                                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Page References Over Time:                                        │ │
│   │                                                                      │ │
│   │   Time: 1  2  3  4  5  6  7  8  9  10 11 12 13 14 15               │ │
│   │   Page: A  B  C  B  A  D  E  D  E  A  B  C  D  E  A                │ │
│   │                                                                      │ │
│   │   With Δ = 5:                                                        │ │
│   │                                                                      │ │
│   │   At t=10: W(10, 5) = {A, D, E}                                     │ │
│   │            (pages referenced from t=6 to t=10)                       │ │
│   │            |W| = 3                                                   │ │
│   │                                                                      │ │
│   │   At t=15: W(15, 5) = {A, B, C, D, E}                               │ │
│   │            (pages referenced from t=11 to t=15)                      │ │
│   │            |W| = 5                                                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WORKING SET SIZE OVER TIME:                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   |W(t)|                                                             │ │
│   │     ▲                                                                │ │
│   │     │     ┌───┐                                                     │ │
│   │   5 │     │   │     ┌───────────┐                                   │ │
│   │     │ ┌───┤   │     │           │                                   │ │
│   │   4 │ │   │   │ ┌───┤           │                                   │ │
│   │     │ │   │   │ │   │           │                                   │ │
│   │   3 │ │   │   └─┤   │           └───┐                               │ │
│   │     │ │   │     │   │               │                               │ │
│   │   2 ├─┘   │     └───┘               │                               │ │
│   │     │     │                          │                               │ │
│   │   1 │     │                          └───────────                   │ │
│   │     │                                                                │ │
│   │     └───────────────────────────────────────────────────────────►   │ │
│   │                         Time                                         │ │
│   │                                                                      │ │
│   │   Working set size changes as process moves between phases          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Thrashing

**Thrashing** occurs when a process spends more time paging than executing. This happens when the sum of all working sets exceeds available physical memory.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THRASHING                                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CAUSE:                                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Σ |W(i)| > Physical Memory                                              │
│                                                                            │
│   When the total working set of all processes exceeds physical memory,   │
│   the system thrashes:                                                     │
│                                                                            │
│   1. Process needs page → Page fault                                      │
│   2. Must evict page from another process's working set                  │
│   3. That process now faults to get its page back                        │
│   4. Evicts page from first process                                       │
│   5. Cycle continues → No useful work done                                │
│                                                                            │
│                                                                            │
│   CPU UTILIZATION VS DEGREE OF MULTIPROGRAMMING:                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CPU                                                                │ │
│   │   Utilization                                                        │ │
│   │     ▲                                                                │ │
│   │     │         ╭────────╮                                            │ │
│   │ 100%│        ╱          ╲                                           │ │
│   │     │       ╱            ╲                                          │ │
│   │     │      ╱              ╲                                         │ │
│   │     │     ╱                ╲                                        │ │
│   │     │    ╱                  ╲   ◄── Thrashing begins                │ │
│   │     │   ╱                    ╲                                      │ │
│   │     │  ╱                      ╲                                     │ │
│   │     │ ╱                        ╲                                    │ │
│   │     │╱                          ╲                                   │ │
│   │   0 └───────────────────────────────────────────────────────────►   │ │
│   │                Degree of Multiprogramming                            │ │
│   │                (Number of processes)                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SYMPTOMS OF THRASHING:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • High page fault rate                                                  │
│   • Low CPU utilization despite high load                                 │
│   • Disk constantly active (swap I/O)                                     │
│   • System becomes unresponsive                                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   # Detect thrashing                                                │ │
│   │   $ vmstat 1                                                        │ │
│   │   procs -----------memory---------- ---swap-- -----io---- -system-- │ │
│   │    r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs │ │
│   │   15  8 2048000 12340  1234 234567  9999 9999  9999  9999 1234 5678 │ │
│   │                                     ↑    ↑                          │ │
│   │                              High swap in/out = thrashing           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SOLUTIONS:                                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Add more physical memory                                              │
│   • Reduce degree of multiprogramming (suspend processes)                 │
│   • Use working set model for scheduling                                  │
│   • Implement page fault frequency (PFF) control                         │
│   • Use memory cgroups to limit process memory                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Memory Allocation

### Kernel Memory Allocation

The kernel needs to allocate memory for its own data structures (process descriptors, buffers, etc.). This allocation must be efficient and avoid fragmentation.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL MEMORY ALLOCATION                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CHALLENGES:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Kernel cannot page fault (must have memory immediately)               │
│   • Some allocations require physically contiguous memory (DMA)           │
│   • Must be fast (kernel is latency-sensitive)                            │
│   • Must avoid fragmentation                                               │
│                                                                            │
│   ALLOCATION HIERARCHY:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                    User Space malloc()                        │  │ │
│   │   │              (glibc, jemalloc, tcmalloc)                     │  │ │
│   │   └──────────────────────────┬───────────────────────────────────┘  │ │
│   │                              │ brk() / mmap()                        │ │
│   │   ┌──────────────────────────▼───────────────────────────────────┐  │ │
│   │   │                    kmalloc() / vmalloc()                      │  │ │
│   │   │                   (Kernel allocators)                         │  │ │
│   │   └──────────────────────────┬───────────────────────────────────┘  │ │
│   │                              │                                       │ │
│   │   ┌──────────────────────────▼───────────────────────────────────┐  │ │
│   │   │                    Slab Allocator                             │  │ │
│   │   │              (Object caching layer)                           │  │ │
│   │   └──────────────────────────┬───────────────────────────────────┘  │ │
│   │                              │                                       │ │
│   │   ┌──────────────────────────▼───────────────────────────────────┐  │ │
│   │   │                    Buddy Allocator                            │  │ │
│   │   │               (Page-level allocation)                         │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Buddy System

The **Buddy System** allocates memory in power-of-2 sized blocks, enabling efficient splitting and coalescing.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE BUDDY SYSTEM                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CONCEPT:                                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Memory divided into blocks of 2^n pages                               │
│   • Free blocks maintained in separate lists by size                      │
│   • When block needed, split larger block in half (buddies)               │
│   • When block freed, merge with buddy if buddy also free                 │
│                                                                            │
│   ALLOCATION EXAMPLE (need 2 pages):                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Initial state: 16-page block                                      │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                        16 pages                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                              │                                       │ │
│   │                              ▼ Split                                 │ │
│   │   ┌──────────────────────────┬──────────────────────────────────┐   │ │
│   │   │         8 pages          │          8 pages (buddy)         │   │ │
│   │   └──────────────────────────┴──────────────────────────────────┘   │ │
│   │              │                                                       │ │
│   │              ▼ Split                                                 │ │
│   │   ┌───────────┬──────────────┬──────────────────────────────────┐   │ │
│   │   │  4 pages  │  4 (buddy)   │          8 pages                  │   │ │
│   │   └───────────┴──────────────┴──────────────────────────────────┘   │ │
│   │        │                                                             │ │
│   │        ▼ Split                                                       │ │
│   │   ┌─────┬─────┬──────────────┬──────────────────────────────────┐   │ │
│   │   │  2  │ 2   │    4 pages   │          8 pages                  │   │ │
│   │   │ ███ │(bdy)│              │                                   │   │ │
│   │   └─────┴─────┴──────────────┴──────────────────────────────────┘   │ │
│   │     ↑                                                                │ │
│   │   Allocated!                                                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   FREE LISTS BY ORDER:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Order 0 (1 page):   [ ]──►[ ]──►[ ]──►NULL                       │ │
│   │   Order 1 (2 pages):  [ ]──►[ ]──►NULL                              │ │
│   │   Order 2 (4 pages):  [ ]──►NULL                                    │ │
│   │   Order 3 (8 pages):  [ ]──►NULL                                    │ │
│   │   Order 4 (16 pages): NULL                                          │ │
│   │   ...                                                                │ │
│   │   Order 10 (1024 pages = 4MB): [...]                                │ │
│   │                                                                      │ │
│   │   # View buddy info                                                 │ │
│   │   $ cat /proc/buddyinfo                                             │ │
│   │   Node 0, zone   Normal  1234  567  234  123  45  12  8  4  2  1  0 │ │
│   │                           ↑     ↑    ↑                              │ │
│   │                         order0 order1 order2  ...                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Slab Allocator

The **Slab Allocator** provides efficient allocation of frequently-used kernel objects by caching them.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SLAB ALLOCATOR                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MOTIVATION:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Kernel allocates/frees same object types repeatedly                   │
│   • Object initialization is expensive (constructors)                     │
│   • Buddy allocator wastes memory for small objects                       │
│                                                                            │
│   SOLUTION:                                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Cache frequently-allocated objects                                     │
│   • Keep freed objects initialized for reuse                              │
│   • Group same-size objects in "slabs" (pages from buddy)                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   SLAB CACHE STRUCTURE:                                              │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                    kmem_cache                                │   │ │
│   │   │         (e.g., "task_struct" cache)                          │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │ object_size: 4096                                            │   │ │
│   │   │ objects_per_slab: 8                                          │   │ │
│   │   │ flags: SLAB_HWCACHE_ALIGN                                   │   │ │
│   │   └────────────────┬────────────────────────────────────────────┘   │ │
│   │                    │                                                 │ │
│   │        ┌───────────┼───────────┐                                    │ │
│   │        ▼           ▼           ▼                                    │ │
│   │   ┌────────┐  ┌────────┐  ┌────────┐                               │ │
│   │   │ SLAB 1 │  │ SLAB 2 │  │ SLAB 3 │                               │ │
│   │   │ (full) │  │(partial)│  │(empty) │                               │ │
│   │   └────────┘  └────────┘  └────────┘                               │ │
│   │                    │                                                 │ │
│   │                    ▼                                                 │ │
│   │   ┌────┬────┬────┬────┬────┬────┬────┬────┐                        │ │
│   │   │████│████│████│    │    │    │    │    │                        │ │
│   │   │obj │obj │obj │free│free│free│free│free│                        │ │
│   │   └────┴────┴────┴────┴────┴────┴────┴────┘                        │ │
│   │     ↑                 ↑                                             │ │
│   │   allocated         free list                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   COMMON SLAB CACHES:                                                      │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   # View slab caches                                                │ │
│   │   $ cat /proc/slabinfo                                              │ │
│   │   # name            <active_objs> <num_objs> <objsize>              │ │
│   │   task_struct          1234        1500       4192                  │ │
│   │   mm_struct             567         600       1088                  │ │
│   │   files_cache           890        1000        704                  │ │
│   │   dentry              45678       50000        192                  │ │
│   │   inode_cache         12345       15000        608                  │ │
│   │                                                                      │ │
│   │   # Or use slabtop                                                  │ │
│   │   $ slabtop                                                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   VARIANTS:                                                                │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • SLAB:  Original implementation (complex, many features)               │
│   • SLUB:  Simplified, better for modern systems (Linux default)          │
│   • SLOB:  Simple, for memory-constrained embedded systems                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### User Space Memory Allocation

User space programs use malloc() and related functions, which internally use brk() or mmap() system calls.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    USER SPACE MEMORY ALLOCATION                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE MALLOC() FAMILY:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   void *malloc(size_t size);        // Allocate size bytes               │
│   void *calloc(size_t n, size_t s); // Allocate n*s bytes, zero-filled   │
│   void *realloc(void *p, size_t s); // Resize allocation                 │
│   void free(void *ptr);              // Free allocation                   │
│                                                                            │
│                                                                            │
│   UNDERLYING SYSTEM CALLS:                                                 │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   brk() / sbrk():                                                   │ │
│   │   ─────────────────────────────────────────────────────────────────  │ │
│   │   • Adjusts the program "break" (end of data segment)              │ │
│   │   • Used for small allocations (< MMAP_THRESHOLD)                  │ │
│   │   • Contiguous heap growth                                          │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │        Process Address Space                                 │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │   Stack                                                      │   │ │
│   │   │     ↓                                                        │   │ │
│   │   │   ~~~~ (unmapped) ~~~~                                      │   │ │
│   │   │     ↑                                                        │   │ │
│   │   │   Heap ◄── brk() adjusts this boundary                      │   │ │
│   │   │   ─────────────────── program break                         │   │ │
│   │   │   BSS (uninitialized data)                                  │   │ │
│   │   │   Data (initialized)                                         │   │ │
│   │   │   Text (code)                                                │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   mmap():                                                           │ │
│   │   ─────────────────────────────────────────────────────────────────  │ │
│   │   • Creates memory mappings anywhere in address space              │ │
│   │   • Used for large allocations (≥ MMAP_THRESHOLD, default 128KB)   │ │
│   │   • Can be returned to OS immediately on free()                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MODERN ALLOCATORS:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • glibc malloc (ptmalloc2): Default Linux allocator                    │
│   • jemalloc: Used by FreeBSD, Firefox, Redis                            │
│   • tcmalloc (Google): Thread-caching malloc                              │
│   • mimalloc (Microsoft): High-performance allocator                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Virtual Memory Implementation

### Multi-Level Page Tables

For 64-bit address spaces, a flat page table would be enormous. Multi-level page tables solve this by using a hierarchical structure.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MULTI-LEVEL PAGE TABLES                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM WITH FLAT PAGE TABLES:                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   32-bit address space, 4KB pages:                                        │
│   • 2^32 / 2^12 = 2^20 = 1M entries                                       │
│   • 4 bytes per entry = 4MB per process                                   │
│   • Manageable, but wasteful for sparse address spaces                    │
│                                                                            │
│   64-bit address space, 4KB pages:                                        │
│   • 2^64 / 2^12 = 2^52 entries                                            │
│   • 8 bytes per entry = 32 PB per process!                                │
│   • Completely impossible                                                  │
│                                                                            │
│                                                                            │
│   THE SOLUTION: HIERARCHICAL PAGE TABLES                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   x86-64 4-Level Page Tables (48-bit virtual addresses):           │ │
│   │                                                                      │ │
│   │   Virtual Address (48 bits used):                                   │ │
│   │   ┌─────┬─────┬─────┬─────┬────────────┐                           │ │
│   │   │ PML4│ PDPT│  PD │  PT │   Offset   │                           │ │
│   │   │9 bit│9 bit│9 bit│9 bit│  12 bits   │                           │ │
│   │   └──┬──┴──┬──┴──┬──┴──┬──┴─────┬──────┘                           │ │
│   │      │     │     │     │        │                                   │ │
│   │      │     │     │     │        │                                   │ │
│   │      ▼     │     │     │        │                                   │ │
│   │   ┌─────┐  │     │     │        │                                   │ │
│   │   │PML4 │  │     │     │        │                                   │ │
│   │   │Table│──┼─────┼─────┼────────┼────────────────────┐             │ │
│   │   └─────┘  │     │     │        │                    │             │ │
│   │      │     ▼     │     │        │                    │             │ │
│   │      │  ┌─────┐  │     │        │                    │             │ │
│   │      └─►│PDPT │  │     │        │                    │             │ │
│   │         │Table│──┼─────┼────────┼───────────┐        │             │ │
│   │         └─────┘  │     │        │           │        │             │ │
│   │            │     ▼     │        │           │        │             │ │
│   │            │  ┌─────┐  │        │           │        │             │ │
│   │            └─►│ PD  │  │        │           │        │             │ │
│   │               │Table│──┼────────┼──────┐    │        │             │ │
│   │               └─────┘  │        │      │    │        │             │ │
│   │                  │     ▼        │      │    │        │             │ │
│   │                  │  ┌─────┐     │      │    │        │             │ │
│   │                  └─►│ PT  │     │      ▼    ▼        ▼             │ │
│   │                     │Table│─────┼──►┌──────────────────┐           │ │
│   │                     └─────┘     │   │  Physical Page   │           │ │
│   │                                 └──►│    (4KB)         │           │ │
│   │                                     └──────────────────┘           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Translation Lookaside Buffer (TLB)

The **TLB** is a hardware cache that stores recent virtual-to-physical address translations, avoiding the expensive page table walk.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TRANSLATION LOOKASIDE BUFFER (TLB)                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   4-level page table walk = 4 memory accesses per translation!            │
│   Every memory access requires translation → 5x slowdown!                 │
│                                                                            │
│                                                                            │
│   THE SOLUTION: CACHE TRANSLATIONS IN TLB                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────────┐         ┌─────────────────────────────────┐   │ │
│   │   │ Virtual Address │────────►│            TLB                   │   │ │
│   │   └─────────────────┘         │   (typically 64-1024 entries)   │   │ │
│   │                               └───────────────┬─────────────────┘   │ │
│   │                                   │           │                      │ │
│   │                              TLB Hit      TLB Miss                   │ │
│   │                                   │           │                      │ │
│   │                                   ▼           ▼                      │ │
│   │                     ┌─────────────────┐  ┌─────────────────────┐    │ │
│   │                     │ Physical Address │  │ Page Table Walk    │    │ │
│   │                     │ (1 cycle)        │  │ (100-1000 cycles)  │    │ │
│   │                     └─────────────────┘  └──────────┬──────────┘    │ │
│   │                                                     │                │ │
│   │                                                     ▼                │ │
│   │                                          ┌─────────────────────┐    │ │
│   │                                          │ Update TLB entry   │    │ │
│   │                                          └─────────────────────┘    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   TLB STRUCTURE:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌──────────────┬────────────────┬───────────────────────────┐     │ │
│   │   │ Virtual Page │ Physical Frame │ Flags (Valid, R/W, User)  │     │ │
│   │   ├──────────────┼────────────────┼───────────────────────────┤     │ │
│   │   │ 0x00401      │ 0x12345        │ V=1, R/W=1, U=1           │     │ │
│   │   │ 0x7fffd      │ 0xABCDE        │ V=1, R/W=1, U=1           │     │ │
│   │   │ 0xffff8      │ 0x00010        │ V=1, R/W=0, U=0           │     │ │
│   │   │ ...          │ ...            │ ...                        │     │ │
│   │   └──────────────┴────────────────┴───────────────────────────┘     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   TLB SHOOTDOWN:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   When page tables change, TLB entries may become stale.                  │
│   On SMP systems, must invalidate TLB on ALL CPUs:                        │
│                                                                            │
│   1. CPU 0 changes page table entry                                       │
│   2. CPU 0 sends IPI (Inter-Processor Interrupt) to other CPUs           │
│   3. All CPUs flush relevant TLB entries                                  │
│   4. CPU 0 waits for acknowledgment                                       │
│                                                                            │
│   This is expensive! Minimize page table changes.                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Huge Pages

**Huge Pages** reduce TLB pressure by using larger page sizes (2MB or 1GB instead of 4KB).

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HUGE PAGES                                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHY HUGE PAGES?                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Problem: Large memory → Many pages → TLB cannot cover working set       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1GB of memory with 4KB pages = 262,144 pages                      │ │
│   │   TLB has ~1024 entries                                              │ │
│   │   TLB can only cover 4MB!                                            │ │
│   │                                                                      │ │
│   │   1GB of memory with 2MB pages = 512 pages                          │ │
│   │   TLB can cover entire 1GB!                                          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   PAGE SIZES ON x86-64:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────┬───────────────┬────────────────────────────────────┐   │
│   │ Page Size   │ Offset Bits   │ Use Case                            │   │
│   ├─────────────┼───────────────┼────────────────────────────────────┤   │
│   │ 4KB         │ 12 bits       │ Default, general purpose           │   │
│   │ 2MB         │ 21 bits       │ Databases, JVM, large applications │   │
│   │ 1GB         │ 30 bits       │ Memory-intensive HPC, virtualization│   │
│   └─────────────┴───────────────┴────────────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   USING HUGE PAGES:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   # Reserve huge pages at boot                                      │ │
│   │   $ echo 1024 > /proc/sys/vm/nr_hugepages                           │ │
│   │                                                                      │ │
│   │   # View huge page info                                             │ │
│   │   $ cat /proc/meminfo | grep Huge                                   │ │
│   │   HugePages_Total:    1024                                          │ │
│   │   HugePages_Free:      512                                          │ │
│   │   Hugepagesize:       2048 kB                                       │ │
│   │                                                                      │ │
│   │   # Use in application                                              │ │
│   │   void *p = mmap(NULL, size, PROT_READ|PROT_WRITE,                 │ │
│   │                  MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0);    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Memory Mapped Files

### The mmap() System Call

**Memory mapping** allows files or devices to be mapped directly into a process's address space, enabling file 
I/O through memory operations.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMORY MAPPED FILES (mmap)                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE CONCEPT:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Instead of:  read(fd, buffer, size);  // Copy file → buffer → use      │
│   Use:         ptr = mmap(..., fd, ...); // Map file directly into memory │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   TRADITIONAL I/O:                                                  │ │
│   │                                                                      │ │
│   │   ┌──────────┐    read()    ┌──────────┐   copy   ┌──────────┐    │ │
│   │   │   File   │─────────────►│ Kernel   │─────────►│ User     │    │ │
│   │   │ (disk)   │              │ Buffer   │          │ Buffer   │    │ │
│   │   └──────────┘              └──────────┘          └──────────┘    │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   MEMORY MAPPED I/O:                                                │ │
│   │                                                                      │ │
│   │   ┌──────────┐   page fault  ┌──────────────────────────────────┐  │ │
│   │   │   File   │──────────────►│ Page Cache (shared with process) │  │ │
│   │   │ (disk)   │               └──────────────────────────────────┘  │ │
│   │   └──────────┘                        ▲                             │ │
│   │                                       │                             │ │
│   │                              Process accesses directly              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THE MMAP() SYSTEM CALL:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   void *mmap(void *addr, size_t length, int prot, int flags,             │
│              int fd, off_t offset);                                        │
│                                                                            │
│   Parameters:                                                              │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ addr        │ Suggested address (usually NULL = kernel chooses)   │   │
│   │ length      │ Size of mapping                                     │   │
│   │ prot        │ Protection: PROT_READ, PROT_WRITE, PROT_EXEC       │   │
│   │ flags       │ MAP_SHARED, MAP_PRIVATE, MAP_ANONYMOUS, etc.       │   │
│   │ fd          │ File descriptor (-1 for anonymous)                  │   │
│   │ offset      │ Offset in file (must be page-aligned)              │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Private vs Shared Mappings

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PRIVATE VS SHARED MAPPINGS                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MAP_SHARED:                                                              │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Changes are visible to other processes mapping the same file          │
│   • Changes are written back to the underlying file                       │
│   • Used for: IPC, shared memory, file I/O                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A        Shared Mapping         Process B                 │ │
│   │   ┌───────┐        ┌───────────┐         ┌───────┐                 │ │
│   │   │       │───────►│ Physical  │◄────────│       │                 │ │
│   │   │ VAddr │        │   Page    │         │ VAddr │                 │ │
│   │   └───────┘        └─────┬─────┘         └───────┘                 │ │
│   │                          │                                          │ │
│   │                          ▼                                          │ │
│   │                    ┌───────────┐                                    │ │
│   │                    │   File    │                                    │ │
│   │                    │  (disk)   │                                    │ │
│   │                    └───────────┘                                    │ │
│   │                                                                      │ │
│   │   A writes → B sees the change → File is updated                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MAP_PRIVATE:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Creates a private copy-on-write mapping                               │
│   • Changes are NOT visible to other processes                            │
│   • Changes are NOT written to the file                                   │
│   • Used for: Loading executables, private data                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A         Initial State         Process B                 │ │
│   │   ┌───────┐        ┌───────────┐         ┌───────┐                 │ │
│   │   │       │───────►│ Physical  │◄────────│       │                 │ │
│   │   │ VAddr │        │   Page    │         │ VAddr │                 │ │
│   │   └───────┘        └───────────┘         └───────┘                 │ │
│   │              (read-only, shared)                                    │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   Process A          After A Writes        Process B                │ │
│   │   ┌───────┐        ┌───────────┐         ┌───────┐                 │ │
│   │   │       │───────►│ Private   │         │       │                 │ │
│   │   │ VAddr │        │   Copy    │         │ VAddr │                 │ │
│   │   └───────┘        └───────────┘         └───┬───┘                 │ │
│   │                                              │                      │ │
│   │                                              ▼                      │ │
│   │                                        ┌───────────┐                │ │
│   │                                        │ Original  │                │ │
│   │                                        │   Page    │                │ │
│   │                                        └───────────┘                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Copy-on-Write (COW)

**Copy-on-Write** is an optimization that defers copying memory until a write occurs.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COPY-ON-WRITE (COW)                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE CONCEPT:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Don't copy pages until they are modified                              │
│   • Share read-only pages between processes                               │
│   • Copy only when a write occurs (triggered by page fault)              │
│                                                                            │
│                                                                            │
│   COW IN FORK():                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BEFORE FORK:                                                      │ │
│   │                                                                      │ │
│   │   Parent Process                                                    │ │
│   │   ┌─────────────────┐         ┌─────────────────┐                  │ │
│   │   │ Page Table      │         │ Physical Memory │                  │ │
│   │   ├─────────────────┤         ├─────────────────┤                  │ │
│   │   │ VPN 0 → PFN 100 │────────►│ Frame 100: "ABC"│                  │ │
│   │   │ VPN 1 → PFN 200 │────────►│ Frame 200: "XYZ"│                  │ │
│   │   └─────────────────┘         └─────────────────┘                  │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   AFTER FORK (before any writes):                                   │ │
│   │                                                                      │ │
│   │   Parent Process              Child Process                         │ │
│   │   ┌─────────────────┐         ┌─────────────────┐                  │ │
│   │   │ VPN 0 → PFN 100 │    ┌───►│ VPN 0 → PFN 100 │                  │ │
│   │   │ (read-only)     │────┤    │ (read-only)     │                  │ │
│   │   │ VPN 1 → PFN 200 │    │    │ VPN 1 → PFN 200 │                  │ │
│   │   │ (read-only)     │────┼───►│ (read-only)     │                  │ │
│   │   └─────────────────┘    │    └─────────────────┘                  │ │
│   │                          │                                          │ │
│   │                          ▼    Physical Memory                       │ │
│   │                    ┌─────────────────┐                              │ │
│   │                    │ Frame 100: "ABC"│ ◄── Shared (refcount=2)     │ │
│   │                    │ Frame 200: "XYZ"│ ◄── Shared (refcount=2)     │ │
│   │                    └─────────────────┘                              │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   AFTER CHILD WRITES TO VPN 0:                                      │ │
│   │                                                                      │ │
│   │   1. Page fault (write to read-only page)                          │ │
│   │   2. Kernel allocates new frame (300)                               │ │
│   │   3. Copy content from frame 100 to frame 300                      │ │
│   │   4. Update child's page table: VPN 0 → PFN 300 (read-write)       │ │
│   │   5. Decrement refcount of frame 100                                │ │
│   │                                                                      │ │
│   │   Parent Process              Child Process                         │ │
│   │   ┌─────────────────┐         ┌─────────────────┐                  │ │
│   │   │ VPN 0 → PFN 100 │         │ VPN 0 → PFN 300 │                  │ │
│   │   │ (read-write)    │         │ (read-write)    │                  │ │
│   │   └─────────────────┘         └─────────────────┘                  │ │
│   │           │                           │                             │ │
│   │           ▼                           ▼                             │ │
│   │   ┌──────────────┐            ┌──────────────┐                     │ │
│   │   │Frame 100:"ABC"│           │Frame 300:"DEF"│ ◄── Modified copy  │ │
│   │   └──────────────┘            └──────────────┘                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THE KERNEL ALGORITHM:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   algorithm handle_cow_fault                                              │
│   input:  faulting_address                                                │
│   output: none                                                            │
│   {                                                                       │
│       pte = get_pte(current->mm, faulting_address);                       │
│       old_page = pte_to_page(pte);                                        │
│                                                                           │
│       if (page_count(old_page) == 1) {                                    │
│           /* We're the only user, just make it writable */                │
│           set_pte_writable(pte);                                          │
│           flush_tlb_page(faulting_address);                               │
│           return;                                                         │
│       }                                                                   │
│                                                                           │
│       /* Multiple users, need to copy */                                  │
│       new_page = alloc_page();                                            │
│       copy_page(new_page, old_page);                                      │
│       put_page(old_page);         /* Decrement refcount */               │
│       set_pte(pte, new_page, WRITABLE);                                   │
│       flush_tlb_page(faulting_address);                                   │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Anonymous Mappings

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ANONYMOUS MAPPINGS                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Anonymous mappings are memory regions not backed by a file.             │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   // Anonymous private mapping (for heap, stack)                    │ │
│   │   void *p = mmap(NULL, size, PROT_READ|PROT_WRITE,                 │ │
│   │                  MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);                 │ │
│   │                                                                      │ │
│   │   // Anonymous shared mapping (for IPC)                             │ │
│   │   void *shm = mmap(NULL, size, PROT_READ|PROT_WRITE,               │ │
│   │                    MAP_SHARED|MAP_ANONYMOUS, -1, 0);                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   ZERO PAGE OPTIMIZATION:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   Anonymous pages are initially mapped to a shared "zero page":           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   mmap() returns         On first read:         On first write:     │ │
│   │                                                                      │ │
│   │   VPN → not present      VPN → zero_page        VPN → new_page      │ │
│   │                          (read-only)            (with zeros)         │ │
│   │                                                                      │ │
│   │   Memory used: 0         Memory used: 0         Memory used: 4KB    │ │
│   │                          (shared zero page)     (private page)       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Memory Protection

### Page Protection Bits

Each page has associated protection bits that control access permissions.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE PROTECTION BITS                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PAGE TABLE ENTRY FLAGS:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   x86-64 Page Table Entry:                                          │ │
│   │                                                                      │ │
│   │   63        52 51      12 11    9 8 7 6 5 4 3 2 1 0                │ │
│   │   ┌─────────┬───────────┬───────┬─┬─┬─┬─┬─┬─┬─┬─┬─┐               │ │
│   │   │   NX    │  Frame #  │ Avail │G│S│D│A│C│W│U│R│P│               │ │
│   │   └─────────┴───────────┴───────┴─┴─┴─┴─┴─┴─┴─┴─┴─┘               │ │
│   │                                                                      │ │
│   │   P  = Present          (0 = not in memory)                        │ │
│   │   R  = Read/Write       (0 = read-only, 1 = read-write)            │ │
│   │   U  = User/Supervisor  (0 = kernel only, 1 = user accessible)     │ │
│   │   W  = Write-Through    (cache policy)                              │ │
│   │   C  = Cache Disable    (for memory-mapped I/O)                    │ │
│   │   A  = Accessed         (set by CPU on access)                     │ │
│   │   D  = Dirty            (set by CPU on write)                      │ │
│   │   S  = Page Size        (0 = 4KB, 1 = large page)                  │ │
│   │   G  = Global           (don't flush from TLB on context switch)   │ │
│   │   NX = No Execute       (prevent code execution)                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MPROTECT() SYSTEM CALL:                                                  │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   int mprotect(void *addr, size_t len, int prot);                         │
│                                                                            │
│   prot values:                                                             │
│   ┌─────────────────┬─────────────────────────────────────────────────┐   │
│   │ PROT_NONE       │ No access allowed                               │   │
│   │ PROT_READ       │ Read access                                     │   │
│   │ PROT_WRITE      │ Write access                                    │   │
│   │ PROT_EXEC       │ Execute access                                  │   │
│   └─────────────────┴─────────────────────────────────────────────────┘   │
│                                                                            │
│   Example: Make code read-only after loading                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   // Make page executable but not writable                         │ │
│   │   mprotect(code_page, PAGE_SIZE, PROT_READ | PROT_EXEC);           │ │
│   │                                                                      │ │
│   │   // Create a guard page                                            │ │
│   │   mprotect(guard_page, PAGE_SIZE, PROT_NONE);                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Segmentation Faults

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEGMENTATION FAULTS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A segmentation fault (SIGSEGV) occurs when a process accesses          │
│   memory it's not allowed to access.                                      │
│                                                                            │
│                                                                            │
│   CAUSES OF SEGFAULTS:                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. NULL POINTER DEREFERENCE:                                      │ │
│   │      int *p = NULL;                                                 │ │
│   │      *p = 42;     // SIGSEGV: accessing unmapped page 0            │ │
│   │                                                                      │ │
│   │   2. ACCESSING UNMAPPED MEMORY:                                     │ │
│   │      int *p = (int *)0xDEADBEEF;                                   │ │
│   │      *p = 42;     // SIGSEGV: address not in process's VMA         │ │
│   │                                                                      │ │
│   │   3. WRITING TO READ-ONLY MEMORY:                                   │ │
│   │      char *s = "hello";  // String literal in read-only section    │ │
│   │      s[0] = 'H';         // SIGSEGV: write to read-only page      │ │
│   │                                                                      │ │
│   │   4. EXECUTING NON-EXECUTABLE MEMORY:                               │ │
│   │      void (*func)() = (void(*)())data_buffer;                      │ │
│   │      func();             // SIGSEGV: NX bit set on data pages      │ │
│   │                                                                      │ │
│   │   5. STACK OVERFLOW:                                                │ │
│   │      void recurse() { char buf[10000]; recurse(); }                │ │
│   │      recurse();          // SIGSEGV: exceeded stack limit          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KERNEL HANDLING:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   algorithm handle_page_fault                                             │
│   input:  fault_address, error_code                                       │
│   {                                                                        │
│       vma = find_vma(current->mm, fault_address);                         │
│                                                                            │
│       if (vma == NULL || fault_address < vma->vm_start) {                 │
│           /* Address not in any VMA - invalid access */                  │
│           send_signal(SIGSEGV, current);                                  │
│           return;                                                          │
│       }                                                                    │
│                                                                            │
│       if ((error_code & WRITE) && !(vma->vm_flags & VM_WRITE)) {         │
│           /* Write to read-only region */                                 │
│           send_signal(SIGSEGV, current);                                  │
│           return;                                                          │
│       }                                                                    │
│                                                                            │
│       /* Legitimate page fault - handle it */                             │
│       handle_mm_fault(vma, fault_address);                                │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Address Space Layout Randomization (ASLR)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ADDRESS SPACE LAYOUT RANDOMIZATION (ASLR)               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ASLR randomizes the memory layout of a process to make exploits        │
│   harder by preventing attackers from predicting addresses.               │
│                                                                            │
│                                                                            │
│   WITHOUT ASLR:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Every run:                                                        │ │
│   │                                                                      │ │
│   │   0xFFFFFFFF ┌──────────────┐                                       │ │
│   │              │ Kernel       │                                       │ │
│   │   0xC0000000 ├──────────────┤                                       │ │
│   │              │ Stack        │ ← Always at 0xBFFFFFFF               │ │
│   │              │    ↓         │                                       │ │
│   │              │              │                                       │ │
│   │              │    ↑         │                                       │ │
│   │              │ Heap         │ ← Always at 0x08050000               │ │
│   │   0x08048000 │ Text         │ ← Always at 0x08048000               │ │
│   │   0x00000000 └──────────────┘                                       │ │
│   │                                                                      │ │
│   │   Attacker can hardcode addresses in exploit!                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WITH ASLR:                                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Run 1:              Run 2:              Run 3:                    │ │
│   │                                                                      │ │
│   │   ┌──────────┐       ┌──────────┐        ┌──────────┐              │ │
│   │   │ Stack    │       │ Stack    │        │ Stack    │              │ │
│   │   │ @ 0xBF...│       │ @ 0x7F...│        │ @ 0xAE...│              │ │
│   │   │          │       │          │        │          │              │ │
│   │   │ Heap     │       │ Heap     │        │ Heap     │              │ │
│   │   │ @ 0x09...│       │ @ 0x55...│        │ @ 0x0A...│              │ │
│   │   │ Text     │       │ Text     │        │ Text     │              │ │
│   │   │ @ 0x08...│       │ @ 0x56...│        │ @ 0x55...│              │ │
│   │   └──────────┘       └──────────┘        └──────────┘              │ │
│   │                                                                      │ │
│   │   Addresses change every execution!                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   LINUX ASLR LEVELS:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Check current level                                                    │
│   $ cat /proc/sys/kernel/randomize_va_space                               │
│                                                                            │
│   ┌───────┬─────────────────────────────────────────────────────────────┐ │
│   │ Value │ Description                                                  │ │
│   ├───────┼─────────────────────────────────────────────────────────────┤ │
│   │ 0     │ Disabled                                                    │ │
│   │ 1     │ Stack, VDSO, shared libraries randomized                   │ │
│   │ 2     │ Above + heap (brk) randomized (full ASLR)                  │ │
│   └───────┴─────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Stack Protection

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    STACK PROTECTION                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Multiple mechanisms protect against stack-based attacks.                │
│                                                                            │
│                                                                            │
│   STACK CANARIES:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Stack frame with canary:                                          │ │
│   │                                                                      │ │
│   │   Higher addresses                                                  │ │
│   │   ┌─────────────────────┐                                           │ │
│   │   │ Return Address      │ ◄── Target of buffer overflow            │ │
│   │   ├─────────────────────┤                                           │ │
│   │   │ Saved Frame Pointer │                                           │ │
│   │   ├─────────────────────┤                                           │ │
│   │   │ CANARY              │ ◄── Random value, checked before return  │ │
│   │   ├─────────────────────┤                                           │ │
│   │   │ Local Variables     │ ◄── Overflow starts here                 │ │
│   │   │ (buffer)            │                                           │ │
│   │   └─────────────────────┘                                           │ │
│   │   Lower addresses                                                   │ │
│   │                                                                      │ │
│   │   If canary is modified → stack_chk_fail() → abort                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   NON-EXECUTABLE STACK:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • NX (No-Execute) bit marks stack pages as non-executable              │
│   • Prevents shellcode injection into stack                               │
│   • Hardware enforced (DEP on Windows, NX on Linux)                      │
│                                                                            │
│                                                                            │
│   GUARD PAGES:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌───────────────────┐                                             │ │
│   │   │ Stack grows down  │                                             │ │
│   │   │        ↓          │                                             │ │
│   │   ├───────────────────┤                                             │ │
│   │   │ GUARD PAGE        │ ◄── PROT_NONE (no access)                  │ │
│   │   │ (triggers SIGSEGV)│     Prevents stack clash attacks            │ │
│   │   ├───────────────────┤                                             │ │
│   │   │ Other memory      │                                             │ │
│   │   └───────────────────┘                                             │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Modern Memory Management

### NUMA Memory Policies

**Non-Uniform Memory Access (NUMA)** systems have memory attached to different CPU nodes with varying access latencies.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NUMA MEMORY POLICIES                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NUMA ARCHITECTURE:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────────┐         ┌─────────────────┐                  │ │
│   │   │    Node 0       │         │    Node 1       │                  │ │
│   │   │  ┌─────┬─────┐  │         │  ┌─────┬─────┐  │                  │ │
│   │   │  │CPU 0│CPU 1│  │         │  │CPU 2│CPU 3│  │                  │ │
│   │   │  └──┬──┴──┬──┘  │         │  └──┬──┴──┬──┘  │                  │ │
│   │   │     │     │     │         │     │     │     │                  │ │
│   │   │  ┌──┴─────┴──┐  │◄───────►│  ┌──┴─────┴──┐  │                  │ │
│   │   │  │ Memory 0  │  │Interconnect │ Memory 1  │  │                  │ │
│   │   │  │ (local)   │  │ (slower) │  │ (local)   │  │                  │ │
│   │   │  └───────────┘  │         │  └───────────┘  │                  │ │
│   │   └─────────────────┘         └─────────────────┘                  │ │
│   │                                                                      │ │
│   │   Access to local memory:  ~100ns                                   │ │
│   │   Access to remote memory: ~150-300ns                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   NUMA POLICIES:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌───────────────────┬─────────────────────────────────────────────────┐ │
│   │ Policy            │ Description                                      │ │
│   ├───────────────────┼─────────────────────────────────────────────────┤ │
│   │ MPOL_DEFAULT      │ Allocate on the local node                     │ │
│   │ MPOL_BIND         │ Allocate only from specified nodes             │ │
│   │ MPOL_INTERLEAVE   │ Round-robin across specified nodes             │ │
│   │ MPOL_PREFERRED    │ Prefer specified node, fallback to others      │ │
│   └───────────────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   NUMACTL EXAMPLES:                                                        │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Run on specific node                                                   │
│   $ numactl --cpunodebind=0 --membind=0 ./application                     │
│                                                                            │
│   # Interleave memory across all nodes                                    │
│   $ numactl --interleave=all ./application                                │
│                                                                            │
│   # View NUMA statistics                                                   │
│   $ numastat                                                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Memory Cgroups

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMORY CGROUPS                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Memory cgroups allow limiting and tracking memory usage per group       │
│   of processes (used heavily by containers).                               │
│                                                                            │
│                                                                            │
│   HIERARCHY:                                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   /sys/fs/cgroup/memory/                                            │ │
│   │   ├── memory.limit_in_bytes    (hard limit)                        │ │
│   │   ├── memory.usage_in_bytes   (current usage)                      │ │
│   │   ├── memory.max_usage_in_bytes                                    │ │
│   │   ├── memory.soft_limit_in_bytes                                   │ │
│   │   ├── memory.oom_control                                           │ │
│   │   ├── container1/                                                   │ │
│   │   │   ├── memory.limit_in_bytes = 512M                             │ │
│   │   │   ├── cgroup.procs = 1234, 1235, 1236                         │ │
│   │   │   └── ...                                                       │ │
│   │   └── container2/                                                   │ │
│   │       ├── memory.limit_in_bytes = 1G                               │ │
│   │       └── ...                                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MEMORY ACCOUNTING:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   • Anonymous pages (heap, stack)                                         │
│   • File-backed pages (page cache for files used by cgroup)              │
│   • Kernel memory (optional: kmem accounting)                             │
│   • Swap usage (memory.memsw.limit_in_bytes)                             │
│                                                                            │
│                                                                            │
│   CGROUP V2 (UNIFIED):                                                     │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Set memory limit                                                       │
│   $ echo "512M" > /sys/fs/cgroup/mygroup/memory.max                       │
│                                                                            │
│   # View current usage                                                     │
│   $ cat /sys/fs/cgroup/mygroup/memory.current                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Transparent Huge Pages (THP)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TRANSPARENT HUGE PAGES (THP)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THP automatically promotes regular 4KB pages to 2MB huge pages          │
│   without application changes.                                             │
│                                                                            │
│                                                                            │
│   HOW THP WORKS:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Without THP:                                                      │ │
│   │   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐│ │
│   │   │4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│4KB│...││ │
│   │   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘│ │
│   │   512 PTEs needed for 2MB region                                   │ │
│   │                                                                      │ │
│   │   With THP:                                                         │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                     2MB Huge Page                            │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │   1 PTE needed for 2MB region                                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THP MODES:                                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Check current mode                                                     │
│   $ cat /sys/kernel/mm/transparent_hugepage/enabled                       │
│   [always] madvise never                                                   │
│                                                                            │
│   ┌─────────────────┬───────────────────────────────────────────────────┐ │
│   │ Mode            │ Description                                        │ │
│   ├─────────────────┼───────────────────────────────────────────────────┤ │
│   │ always          │ THP enabled for all mappings                      │ │
│   │ madvise         │ Only where application requests (MADV_HUGEPAGE)   │ │
│   │ never           │ THP completely disabled                           │ │
│   └─────────────────┴───────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KHUGEPAGED DAEMON:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   khugepaged scans process memory looking for opportunities        │ │
│   │   to collapse 512 contiguous 4KB pages into 2MB huge pages.        │ │
│   │                                                                      │ │
│   │   Before:                After khugepaged:                         │ │
│   │   ┌─┬─┬─┬─┬─┬─┬─┬─┐      ┌─────────────────┐                       │ │
│   │   │4│4│4│4│4│4│4│4│ ──►  │   2MB Huge Page │                       │ │
│   │   │K│K│K│K│K│K│K│K│      │                 │                       │ │
│   │   │B│B│B│B│B│B│B│B│      └─────────────────┘                       │ │
│   │   └─┴─┴─┴─┴─┴─┴─┴─┘                                                │ │
│   │   (×512)                                                            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   DEFRAG MODES:                                                            │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   $ cat /sys/kernel/mm/transparent_hugepage/defrag                        │
│                                                                            │
│   ┌─────────────────┬───────────────────────────────────────────────────┐ │
│   │ Mode            │ Behavior                                           │ │
│   ├─────────────────┼───────────────────────────────────────────────────┤ │
│   │ always          │ Synchronous compaction on fault (may stall)       │ │
│   │ defer           │ Async compaction, khugepaged will collapse later  │ │
│   │ defer+madvise   │ Like defer, sync only for MADV_HUGEPAGE regions   │ │
│   │ madvise         │ Sync compaction only for MADV_HUGEPAGE            │ │
│   │ never           │ Never perform compaction                          │ │
│   └─────────────────┴───────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Memory Compaction

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMORY COMPACTION                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Memory compaction moves pages around to create contiguous free regions  │
│   needed for huge pages and high-order allocations.                        │
│                                                                            │
│                                                                            │
│   THE FRAGMENTATION PROBLEM:                                               │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Fragmented Memory:                                                │ │
│   │   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐│ │
│   │   │ U │ F │ U │ F │ U │ F │ U │ F │ U │ F │ U │ F │ U │ F │ U │ F ││ │
│   │   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘│ │
│   │   U = Used, F = Free                                                │ │
│   │   Cannot allocate contiguous 2MB despite 50% memory being free!    │ │
│   │                                                                      │ │
│   │   After Compaction:                                                 │ │
│   │   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐│ │
│   │   │ U │ U │ U │ U │ U │ U │ U │ U │ F │ F │ F │ F │ F │ F │ F │ F ││ │
│   │   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘│ │
│   │   Now we can allocate huge pages!                                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   COMPACTION ALGORITHM:                                                    │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌──────────────────────────────────────────────────────────────┐ │ │
│   │   │                   Physical Memory Zone                        │ │ │
│   │   │   ┌──────────────────────────────────────────────────────┐   │ │ │
│   │   │   │  ↓ Migration Scanner (finds movable pages)           │   │ │ │
│   │   │   │                                                       │   │ │ │
│   │   │   │  [U][F][U][F][U][F][U][F][U][F][U][F][U][F][U][F]   │   │ │ │
│   │   │   │                                                       │   │ │ │
│   │   │   │                    Free Scanner (finds holes) ↑       │   │ │ │
│   │   │   └───────────────────────────────────────────────────────┘   │ │ │
│   │   │                                                               │ │ │
│   │   │   Scanners move toward each other, migrating pages.          │ │ │
│   │   │                                                               │ │ │
│   │   └──────────────────────────────────────────────────────────────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   TRIGGERING COMPACTION:                                                   │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Manual compaction (for debugging/testing)                             │
│   $ echo 1 > /proc/sys/vm/compact_memory                                  │
│                                                                            │
│   # View compaction statistics                                            │
│   $ cat /proc/vmstat | grep compact                                       │
│   compact_migrate_scanned 123456                                          │
│   compact_free_scanned 234567                                             │
│   compact_success 1234                                                    │
│   compact_fail 12                                                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### KSM (Kernel Same-page Merging)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KSM (KERNEL SAME-PAGE MERGING)                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KSM scans memory looking for pages with identical content and          │
│   merges them using copy-on-write. Essential for VM density.              │
│                                                                            │
│                                                                            │
│   HOW KSM WORKS:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Before KSM:                                                       │ │
│   │                                                                      │ │
│   │   VM 1 Memory:        VM 2 Memory:        VM 3 Memory:              │ │
│   │   ┌───────────┐       ┌───────────┐       ┌───────────┐             │ │
│   │   │ Kernel    │       │ Kernel    │       │ Kernel    │             │ │
│   │   │ (same)    │       │ (same)    │       │ (same)    │             │ │
│   │   ├───────────┤       ├───────────┤       ├───────────┤             │ │
│   │   │ Libraries │       │ Libraries │       │ Libraries │             │ │
│   │   │ (same)    │       │ (same)    │       │ (same)    │             │ │
│   │   ├───────────┤       ├───────────┤       ├───────────┤             │ │
│   │   │ App Data  │       │ App Data  │       │ App Data  │             │ │
│   │   │ (different)│       │ (different)│       │ (different)│             │ │
│   │   └───────────┘       └───────────┘       └───────────┘             │ │
│   │                                                                      │ │
│   │   Physical memory used: 3× kernel + 3× libraries + 3× data         │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   After KSM:                                                        │ │
│   │                                                                      │ │
│   │   VM 1          VM 2          VM 3           Physical Memory        │ │
│   │   ┌─────┐       ┌─────┐       ┌─────┐        ┌─────────────┐        │ │
│   │   │  ●──┼───────┼──●──┼───────┼──●  │───────►│   Kernel    │        │ │
│   │   ├─────┤       ├─────┤       ├─────┤        │   (shared)  │        │ │
│   │   │  ●──┼───────┼──●──┼───────┼──●  │───────►├─────────────┤        │ │
│   │   ├─────┤       ├─────┤       ├─────┤        │  Libraries  │        │ │
│   │   │  ●  │       │  ●  │       │  ●  │        │   (shared)  │        │ │
│   │   └──┼──┘       └──┼──┘       └──┼──┘        ├─────────────┤        │ │
│   │      │             │             │           │ VM1 Data    │        │ │
│   │      └─────────────┼─────────────┼──────────►├─────────────┤        │ │
│   │                    │             │           │ VM2 Data    │        │ │
│   │                    └─────────────┼──────────►├─────────────┤        │ │
│   │                                  │           │ VM3 Data    │        │ │
│   │                                  └──────────►└─────────────┘        │ │
│   │                                                                      │ │
│   │   Physical memory used: 1× kernel + 1× libraries + 3× data         │ │
│   │   (Significant savings when running multiple similar VMs!)          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KSM PROCESS:                                                             │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   1. Application marks regions with madvise(MADV_MERGEABLE)              │
│   2. ksmd daemon scans marked pages                                        │
│   3. Pages are compared by content hash                                    │
│   4. Identical pages are merged with COW mapping                          │
│   5. If a process writes to merged page → COW creates private copy       │
│                                                                            │
│                                                                            │
│   KSM CONFIGURATION:                                                       │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   # Enable KSM                                                             │
│   $ echo 1 > /sys/kernel/mm/ksm/run                                       │
│                                                                            │
│   # How many pages to scan before sleeping                                 │
│   $ echo 100 > /sys/kernel/mm/ksm/pages_to_scan                           │
│                                                                            │
│   # Sleep interval between scans (milliseconds)                           │
│   $ echo 200 > /sys/kernel/mm/ksm/sleep_millisecs                         │
│                                                                            │
│                                                                            │
│   KSM STATISTICS:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   $ cat /sys/kernel/mm/ksm/pages_shared     # Merged pages               │
│   $ cat /sys/kernel/mm/ksm/pages_sharing    # COW references             │
│   $ cat /sys/kernel/mm/ksm/pages_unshared   # Unique pages scanned       │
│                                                                            │
│   Memory saved = (pages_sharing - pages_shared) × page_size              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Summary and Appendix

### Memory System Calls Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM CALLS QUICK REFERENCE                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MEMORY MAPPING:                                                          │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────┬─────────────────────────────────────────────┐   │
│   │ System Call         │ Description                                  │   │
│   ├─────────────────────┼─────────────────────────────────────────────┤   │
│   │ mmap()              │ Map files or devices into memory           │   │
│   │ munmap()            │ Unmap memory regions                        │   │
│   │ mprotect()          │ Change memory protection                    │   │
│   │ msync()             │ Sync memory mapping with file               │   │
│   │ madvise()           │ Advise kernel about memory usage patterns  │   │
│   │ mremap()            │ Resize a memory mapping                     │   │
│   │ mlock() / munlock() │ Lock/unlock pages in memory                │   │
│   │ mlockall()          │ Lock all mapped pages                       │   │
│   └─────────────────────┴─────────────────────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   HEAP MANAGEMENT:                                                         │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────┬─────────────────────────────────────────────┐   │
│   │ System Call         │ Description                                  │   │
│   ├─────────────────────┼─────────────────────────────────────────────┤   │
│   │ brk()               │ Change data segment size (heap)            │   │
│   │ sbrk()              │ Increment data segment (library wrapper)   │   │
│   └─────────────────────┴─────────────────────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   SHARED MEMORY:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────┬─────────────────────────────────────────────┐   │
│   │ System Call         │ Description                                  │   │
│   ├─────────────────────┼─────────────────────────────────────────────┤   │
│   │ shmget()            │ Allocate System V shared memory segment    │   │
│   │ shmat()             │ Attach shared memory segment                │   │
│   │ shmdt()             │ Detach shared memory segment                │   │
│   │ shmctl()            │ Shared memory control operations           │   │
│   │ shm_open()          │ Open POSIX shared memory object            │   │
│   │ shm_unlink()        │ Unlink POSIX shared memory object          │   │
│   └─────────────────────┴─────────────────────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   MADVISE FLAGS:                                                           │
│   ───────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   ┌─────────────────────┬─────────────────────────────────────────────┐   │
│   │ Flag                │ Meaning                                      │   │
│   ├─────────────────────┼─────────────────────────────────────────────┤   │
│   │ MADV_NORMAL         │ No special treatment (default)              │   │
│   │ MADV_RANDOM         │ Expect random access pattern                │   │
│   │ MADV_SEQUENTIAL     │ Expect sequential access                    │   │
│   │ MADV_WILLNEED       │ Pages will be needed soon (prefetch)       │   │
│   │ MADV_DONTNEED       │ Pages won't be needed (can discard)        │   │
│   │ MADV_FREE           │ Pages can be freed (lazy reclaim)          │   │
│   │ MADV_HUGEPAGE       │ Use huge pages for this region             │   │
│   │ MADV_NOHUGEPAGE     │ Don't use huge pages                        │   │
│   │ MADV_MERGEABLE      │ Enable KSM merging for this region         │   │
│   │ MADV_UNMERGEABLE    │ Disable KSM merging                         │   │
│   └─────────────────────┴─────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE BIG PICTURE: MEMORY MANAGEMENT                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         USER SPACE                                   │ │
│   │                                                                      │ │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │ │
│   │   │  Process 1  │   │  Process 2  │   │  Process 3  │              │ │
│   │   │ ┌─────────┐ │   │ ┌─────────┐ │   │ ┌─────────┐ │              │ │
│   │   │ │ Stack   │ │   │ │ Stack   │ │   │ │ Stack   │ │              │ │
│   │   │ │ Heap    │ │   │ │ Heap    │ │   │ │ Heap    │ │              │ │
│   │   │ │ Data    │ │   │ │ Data    │ │   │ │ Data    │ │              │ │
│   │   │ │ Text    │ │   │ │ Text    │ │   │ │ Text    │ │              │ │
│   │   │ └─────────┘ │   │ └─────────┘ │   │ └─────────┘ │              │ │
│   │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │ │
│   │          │                 │                 │                      │ │
│   │          └─────────────────┼─────────────────┘                      │ │
│   │                            │                                        │ │
│   │                    Virtual Addresses                                │ │
│   │                            │                                        │ │
│   └────────────────────────────┼────────────────────────────────────────┘ │
│                                │                                          │
│                                ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         KERNEL                                       │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                    MMU / Page Tables                         │  │ │
│   │   │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │ │
│   │   │  │  PGD       │─►│  PUD       │─►│  PMD       │─►┌────────┐ │  │ │
│   │   │  └────────────┘  └────────────┘  └────────────┘  │  PTE   │ │  │ │
│   │   │                                                   └────┬───┘ │  │ │
│   │   └───────────────────────────────────────────────────────┼─────┘  │ │
│   │                                                            │        │ │
│   │   ┌──────────────────┐    ┌─────────────────────────┐     │        │ │
│   │   │  TLB Cache       │◄───│  TLB Shootdown (SMP)    │     │        │ │
│   │   └──────────────────┘    └─────────────────────────┘     │        │ │
│   │                                                            │        │ │
│   │   ┌────────────────────────────────────────────────────────┼──────┐│ │
│   │   │                     Page Fault Handler                 │      ││ │
│   │   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ▼      ││ │
│   │   │  │Minor Fault  │ │Major Fault  │ │Invalid Fault│  ┌───────┐ ││ │
│   │   │  │(zero fill)  │ │(disk read)  │ │(SIGSEGV)    │  │Frame #│ ││ │
│   │   │  └─────────────┘ └─────────────┘ └─────────────┘  └───────┘ ││ │
│   │   └─────────────────────────────────────────────────────────────┘│ │
│   │                                                                   │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                      PAGE CACHE                                      │ │
│   │                                                                      │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  (inode, offset) ──► Page                                     │ │ │
│   │   │                                                                │ │ │
│   │   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │ │ │
│   │   │  │Clean│ │Dirty│ │Clean│ │Dirty│ │Clean│ │Clean│ │Dirty│   │ │ │
│   │   │  └─────┘ └──┬──┘ └─────┘ └──┬──┘ └─────┘ └─────┘ └──┬──┘   │ │ │
│   │   │             │               │                        │       │ │ │
│   │   │             └───────────────┼────────────────────────┘       │ │ │
│   │   │                             │                                 │ │ │
│   │   │                       Writeback threads                      │ │ │
│   │   │                             │                                 │ │ │
│   │   └─────────────────────────────┼─────────────────────────────────┘ │ │
│   └─────────────────────────────────┼───────────────────────────────────┘ │
│                                     ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     PAGE RECLAIM SUBSYSTEM                           │ │
│   │                                                                      │ │
│   │   ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐  │ │
│   │   │   kswapd      │  │ Direct Reclaim│  │    OOM Killer         │  │ │
│   │   │ (background)  │  │ (synchronous) │  │  (last resort)        │  │ │
│   │   └───────┬───────┘  └───────┬───────┘  └───────────────────────┘  │ │
│   │           │                  │                                      │ │
│   │           └──────────────────┘                                      │ │
│   │                    │                                                 │ │
│   │                    ▼                                                 │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                LRU Lists                                     │  │ │
│   │   │  Active Anon ◄─► Inactive Anon ─► Swap Out                  │  │ │
│   │   │  Active File ◄─► Inactive File ─► Drop / Writeback          │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └──────────────────────────────────────────────────────────────────────┘│
│                                ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                      PHYSICAL MEMORY                                 │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │  Zone DMA   │  Zone DMA32  │  Zone Normal  │  Zone Movable  │  │ │
│   │   ├─────────────┴──────────────┴───────────────┴────────────────┤  │ │
│   │   │                                                              │  │ │
│   │   │   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐        │  │ │
│   │   │   │Frame│Frame│Frame│Frame│Frame│Frame│Frame│Frame│ ...   │  │ │
│   │   │   │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │        │  │ │
│   │   │   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘        │  │ │
│   │   │                                                              │  │ │
│   │   │   Buddy System: Free lists for orders 0, 1, 2, ... 10       │  │ │
│   │   │   Slab Allocator: kmem_caches for kernel objects            │  │ │
│   │   │                                                              │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └──────────────────────────────────────────────────────────────────────┘│
│                                │                                          │
│                                ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                      SWAP / STORAGE                                  │ │
│   │                                                                      │ │
│   │   ┌───────────────────┐    ┌───────────────────┐                   │ │
│   │   │    Swap Device    │    │    Swap File      │                   │ │
│   │   │    /dev/sda2      │    │    /swapfile      │                   │ │
│   │   └───────────────────┘    └───────────────────┘                   │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                    Filesystem / Block Layer                  │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 13. References

### Books

- **Bach, Maurice J.** - _The Design of the UNIX Operating System_ (1986)
  - Chapters 6-9: Memory management fundamentals, swapping, demand paging
  - The foundational text for understanding traditional Unix memory management

- **Stevens, W. Richard; Rago, Stephen A.** - _Advanced Programming in the UNIX Environment_ (3rd ed., 2013)
  - Chapter 14: Advanced I/O (memory-mapped I/O)
  - Practical programming perspective on memory management

- **Kerrisk, Michael** - _The Linux Programming Interface_ (2010)
  - Chapters 49-50: Memory mappings
  - Chapter 48: Virtual memory operations
  - Comprehensive Linux-specific coverage

- **Love, Robert** - _Linux Kernel Development_ (3rd ed., 2010)
  - Chapter 12: Memory Management
  - Chapter 15: The Page Cache and Page Writeback
  - Modern Linux kernel implementation details

- **Bovet, Daniel P.; Cesati, Marco** - _Understanding the Linux Kernel_ (3rd ed., 2005)
  - Chapter 8: Memory Management
  - Chapter 17: Page Frame Reclaiming
  - Deep dive into Linux kernel internals

- **Gorman, Mel** - _Understanding the Linux Virtual Memory Manager_ (2004)
  - Complete reference for Linux VM subsystem
  - Available online at kernel.org

### Kernel Source Files

```
Key files for memory management in Linux:

mm/                          # Memory management subsystem
├── memory.c                 # Page fault handling
├── mmap.c                   # Memory mapping implementation
├── page_alloc.c             # Buddy allocator
├── slab.c                   # SLAB allocator
├── slub.c                   # SLUB allocator (default)
├── vmscan.c                 # Page reclaim (kswapd)
├── swap.c                   # Swap operations
├── oom_kill.c               # Out-of-memory killer
├── huge_memory.c            # Transparent huge pages
├── compaction.c             # Memory compaction
├── ksm.c                    # Kernel same-page merging
├── mprotect.c               # Memory protection
├── madvise.c                # madvise() implementation
├── memcontrol.c             # Memory cgroups
└── page_io.c                # Page I/O (swap read/write)

include/linux/
├── mm.h                     # Memory management declarations
├── mm_types.h               # Core MM data structures
├── mmzone.h                 # Memory zones
├── page-flags.h             # Page flag definitions
├── swap.h                   # Swap declarations
└── slab.h                   # Slab allocator interface

arch/x86/mm/                 # x86-specific memory management
├── fault.c                  # x86 page fault handler
├── pageattr.c               # Page attribute management
└── tlb.c                    # TLB operations
```

### Man Pages

```
Section 2 (System Calls):
    mmap(2)      - Map files or devices into memory
    munmap(2)    - Unmap a memory region
    mprotect(2)  - Set protection on a region of memory
    madvise(2)   - Give advice about use of memory
    msync(2)     - Synchronize a file with a memory map
    mlock(2)     - Lock pages in memory
    brk(2)       - Change data segment size
    shmget(2)    - Allocates a shared memory segment
    shmat(2)     - Attaches a shared memory segment

Section 5 (File Formats):
    proc(5)      - Process information pseudo-filesystem
                   /proc/meminfo, /proc/vmstat, /proc/[pid]/maps

Section 7 (Miscellaneous):
    numa(7)      - Overview of NUMA architecture
    cgroups(7)   - Linux control groups

Section 8 (Administration):
    swapon(8)    - Enable swap area
    vmstat(8)    - Report virtual memory statistics
    numactl(8)   - Control NUMA policy
```

### Online Resources

- **Linux Kernel Documentation**
  - https://www.kernel.org/doc/html/latest/admin-guide/mm/
  - https://www.kernel.org/doc/html/latest/mm/

- **LWN.net Articles on Memory Management**
  - Excellent ongoing coverage of Linux VM development

- **Brendan Gregg's Blog**
  - Performance analysis including memory subsystem
  - http://www.brendangregg.com/

- **Linux Memory Management at Scale (Facebook)**
  - Practical insights from production deployments

---

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   "The process abstraction provides each program with the illusion       │
│    that it has exclusive use of memory."                                  │
│                                                                            │
│                                           — Maurice J. Bach, 1986         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

