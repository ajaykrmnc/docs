# Semaphores in Unix Systems

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Kernel Internals, Process Synchronization, Concurrency Control, and IPC

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The Fundamental Synchronization Problem](#the-fundamental-synchronization-problem)
   - [Historical Context](#historical-context)
   - [Document Organization](#document-organization)

2. [Fundamental Concepts](#2-fundamental-concepts)
   - [What is a Semaphore?](#what-is-a-semaphore)
   - [The Railroad Analogy](#the-railroad-analogy)
   - [Atomic Operations](#atomic-operations)
   - [Critical Sections](#critical-sections)

3. [Types of Semaphores](#3-types-of-semaphores)
   - [Binary Semaphores (Mutexes)](#binary-semaphores-mutexes)
   - [Counting Semaphores](#counting-semaphores)
   - [Named vs Unnamed Semaphores](#named-vs-unnamed-semaphores)

4. [Semaphore Operations](#4-semaphore-operations)
   - [P Operation (Wait/Down/Acquire)](#p-operation-waitdownacquire)
   - [V Operation (Signal/Up/Release)](#v-operation-signaluprelease)
   - [The Atomicity Requirement](#the-atomicity-requirement)

5. [Kernel Implementation](#5-kernel-implementation)
   - [Semaphore Data Structures](#semaphore-data-structures)
   - [Wait Queues and Blocking](#wait-queues-and-blocking)
   - [The sys_semop Algorithm](#the-sys_semop-algorithm)
   - [Handling Process Termination](#handling-process-termination)

6. [POSIX Semaphores](#6-posix-semaphores)
   - [Unnamed Semaphores (sem_init)](#unnamed-semaphores-sem_init)
   - [Named Semaphores (sem_open)](#named-semaphores-sem_open)
   - [API Reference](#api-reference)
   - [Error Handling](#error-handling)

7. [System V Semaphores](#7-system-v-semaphores)
   - [Semaphore Sets](#semaphore-sets)
   - [semget, semop, semctl](#semget-semop-semctl)
   - [Semaphore Adjustment Values](#semaphore-adjustment-values)
   - [SEM_UNDO and Process Crash Recovery](#sem_undo-and-process-crash-recovery)

8. [Classic Synchronization Problems](#8-classic-synchronization-problems)
   - [Producer-Consumer Problem](#producer-consumer-problem)
   - [Readers-Writers Problem](#readers-writers-problem)
   - [Dining Philosophers Problem](#dining-philosophers-problem)
   - [Bounded Buffer Problem](#bounded-buffer-problem)

9. [Advanced Topics](#9-advanced-topics)
   - [Priority Inversion](#priority-inversion)
   - [Deadlock Detection and Prevention](#deadlock-detection-and-prevention)
   - [Semaphores vs Mutexes vs Condition Variables](#semaphores-vs-mutexes-vs-condition-variables)
   - [Lock-Free Alternatives](#lock-free-alternatives)

10. [Practical Implementation](#10-practical-implementation)
    - [Common Patterns](#common-patterns)
    - [Performance Considerations](#performance-considerations)
    - [Debugging Semaphore Issues](#debugging-semaphore-issues)
    - [Best Practices](#best-practices)

11. [Summary and Reference](#11-summary-and-reference)
    - [Quick Reference](#quick-reference)
    - [System Call Reference](#system-call-reference)
    - [Error Codes](#error-codes)

---

## 1. Introduction

### The Fundamental Synchronization Problem

When multiple processes or threads access shared resources, chaos ensues without coordination:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE RACE CONDITION PROBLEM                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Two processes trying to increment a shared counter:                      │
│                                                                            │
│   SHARED MEMORY:  counter = 5                                              │
│                                                                            │
│   EXPECTED RESULT: counter = 7 (after both increment)                      │
│                                                                            │
│   WHAT ACTUALLY HAPPENS (Race Condition):                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A                         Process B                       │ │
│   │   ─────────                         ─────────                       │ │
│   │   1. READ counter (5)                                               │ │
│   │                                     2. READ counter (5)             │ │
│   │   3. ADD 1 (6)                                                      │ │
│   │                                     4. ADD 1 (6)                    │ │
│   │   5. WRITE counter (6)                                              │ │
│   │                                     6. WRITE counter (6)            │ │
│   │                                                                     │ │
│   │   FINAL RESULT: counter = 6  ← WRONG! Lost an increment!            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   The problem: READ-MODIFY-WRITE is NOT atomic!                            │
│   Between reading and writing, another process can interfere.              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "counter++" in C compiles to multiple CPU instructions:           │ │
│   │                                                                     │ │
│   │   MOV  EAX, [counter]    ; Load counter into register               │ │
│   │   ADD  EAX, 1            ; Increment register                       │ │
│   │   MOV  [counter], EAX    ; Store back to memory                     │ │
│   │                                                                     │ │
│   │   A context switch can happen between ANY of these instructions!    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

The solution? **Synchronization primitives** that ensure only one process accesses the shared resource at a time. The semaphore is one of the most fundamental and versatile of these primitives.

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HISTORY OF SEMAPHORES                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1965: Edsger W. Dijkstra invents the semaphore                          │
│         - Introduced in "Cooperating Sequential Processes"                 │
│         - Named P and V operations (Dutch: Proberen, Verhogen)            │
│         - Revolutionary concept for process synchronization                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "The semaphore is a non-negative integer variable that, apart     │ │
│   │    from initialization, is only accessed through two standard       │ │
│   │    atomic operations: P (wait) and V (signal)."                     │ │
│   │                                                                     │ │
│   │                                    — Edsger W. Dijkstra, 1965        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TIMELINE:                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1965  Dijkstra invents semaphores                                 │ │
│   │   1971  THE/Technische Hogeschool Eindhoven OS uses semaphores      │ │
│   │   1983  System V IPC introduces semaphore sets (semget/semop)       │ │
│   │   1993  POSIX.1b standardizes sem_init/sem_wait/sem_post            │ │
│   │   2000s Futex-based implementations for efficiency                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY "P" AND "V"?                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   P = "Proberen" (Dutch: "to test" or "to try")                     │ │
│   │       Also: "Passeren" (to pass), "Pakken" (to grab)                │ │
│   │       Modern names: wait(), down(), acquire(), lock()               │ │
│   │                                                                     │ │
│   │   V = "Verhogen" (Dutch: "to increment" or "to raise")              │ │
│   │       Also: "Vrijgeven" (to release), "Verlaten" (to leave)         │ │
│   │       Modern names: signal(), up(), release(), unlock()             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Document Organization

This document follows the structure established by Maurice Bach, proceeding from fundamental concepts through kernel implementation to practical application:

1. **Fundamentals**: What semaphores are and why they exist
2. **Types**: Binary vs counting, named vs unnamed
3. **Operations**: P and V in detail
4. **Kernel Implementation**: How the kernel implements semaphores
5. **APIs**: POSIX and System V interfaces
6. **Classic Problems**: Producer-consumer, readers-writers, etc.
7. **Advanced Topics**: Priority inversion, deadlock, alternatives
8. **Practical Patterns**: Real-world usage and best practices

---

## 2. Fundamental Concepts

### What is a Semaphore?

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE DEFINITION                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A semaphore is:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. A NON-NEGATIVE INTEGER variable                                │ │
│   │   2. Accessed ONLY through TWO atomic operations:                   │ │
│   │      • P (wait/down): Decrement, block if would go negative         │ │
│   │      • V (signal/up): Increment, wake blocked processes             │ │
│   │   3. Has an associated WAIT QUEUE for blocked processes             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONCEPTUAL MODEL:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct semaphore {                                                │ │
│   │       int value;              /* Current count (≥ 0) */             │ │
│   │       wait_queue_t wait_list; /* Processes waiting */               │ │
│   │       spinlock_t lock;        /* Protects the structure */          │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   INTERPRETATION OF VALUE:                                          │ │
│   │   • value > 0:  Resources available, P() will succeed immediately   │ │
│   │   • value = 0:  No resources, P() will block                        │ │
│   │   • value < 0:  (In some implementations) |value| = waiting count   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL REPRESENTATION:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Semaphore with value = 3:                                         │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────┐                       │ │
│   │   │  VALUE: 3                               │                       │ │
│   │   │  ┌───┬───┬───┐                          │                       │ │
│   │   │  │ ● │ ● │ ● │  ← 3 "permits" available │                       │ │
│   │   │  └───┴───┴───┘                          │                       │ │
│   │   │                                         │                       │ │
│   │   │  WAIT QUEUE: (empty)                    │                       │ │
│   │   └─────────────────────────────────────────┘                       │ │
│   │                                                                     │ │
│   │   After 4 processes call P():                                       │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────┐                       │ │
│   │   │  VALUE: 0                               │                       │ │
│   │   │  ┌───┬───┬───┐                          │                       │ │
│   │   │  │   │   │   │  ← All permits taken     │                       │ │
│   │   │  └───┴───┴───┘                          │                       │ │
│   │   │                                         │                       │ │
│   │   │  WAIT QUEUE: [Process D] ← 4th blocked! │                       │ │
│   │   └─────────────────────────────────────────┘                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Railroad Analogy

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE RAILROAD SEMAPHORE ANALOGY                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The term "semaphore" comes from railroad signaling systems:              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   RAILROAD TRACK (Single-Track Section):                            │ │
│   │                                                                     │ │
│   │        Train A                  Single Track             Train B    │ │
│   │        ──────►                  ============             ◄──────    │ │
│   │                                                                     │ │
│   │   PROBLEM: Only ONE train can use the single track at a time!       │ │
│   │                                                                     │ │
│   │   SOLUTION: Semaphore signals at each end:                          │ │
│   │                                                                     │ │
│   │        │                                              │             │ │
│   │       ─┼─ (RED = STOP)           ═══════════        ─┼─ (RED)       │ │
│   │        │                                              │             │ │
│   │                                                                     │ │
│   │   When a train enters:                                              │ │
│   │   1. Check semaphore (GREEN = proceed, RED = wait)                  │ │
│   │   2. If GREEN: set to RED, enter track                              │ │
│   │   3. When exiting: set other semaphore to GREEN                     │ │
│   │                                                                     │ │
│   │   This is EXACTLY how software semaphores work!                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MAPPING TO SOFTWARE:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Railroad Concept        │   Software Semaphore                    │ │
│   │   ────────────────────────┼──────────────────────────               │ │
│   │   Single track            │   Critical section / shared resource    │ │
│   │   Trains                  │   Processes / threads                   │ │
│   │   Semaphore signal        │   Semaphore variable                    │ │
│   │   GREEN (proceed)         │   value > 0 (resource available)        │ │
│   │   RED (stop)              │   value = 0 (must wait)                 │ │
│   │   Check & set signal      │   P() operation                         │ │
│   │   Clear signal on exit    │   V() operation                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COUNTING SEMAPHORES (Multiple Tracks):                                   │ │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   If there are 3 parallel tracks, 3 trains can pass simultaneously: │ │
│   │                                                                     │ │
│   │        ═══════════  Track 1                                         │ │
│   │        ═══════════  Track 2                                         │ │
│   │        ═══════════  Track 3                                         │ │
│   │                                                                     │ │
│   │   Semaphore value = 3 (number of available tracks)                  │ │
│   │   Each P() decrements: 3 → 2 → 1 → 0 → (block)                      │ │
│   │   Each V() increments: 0 → 1 (wake a waiting train)                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Atomic Operations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ATOMIC OPERATIONS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DEFINITION: An operation is ATOMIC if it completes entirely without      │
│   interruption, or does not happen at all. No intermediate state is        │
│   ever visible to other processes.                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   NON-ATOMIC (Dangerous):              ATOMIC (Safe):               │ │
│   │   ────────────────────────             ──────────────               │ │
│   │                                                                     │ │
│   │   if (sem.value > 0) {       ←→       atomic {                      │ │
│   │       // Context switch                   if (sem.value > 0) {      │ │
│   │       // can happen here!                     sem.value--;          │ │
│   │       sem.value--;                        } else {                  │ │
│   │   }                                           block();              │ │
│   │                                           }                         │ │
│   │   RACE CONDITION!                     }   // Cannot be interrupted  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY ATOMICITY MATTERS:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WITHOUT atomicity, two processes both see value=1:                │ │
│   │                                                                     │ │
│   │   Time    Process A              Process B           sem.value     │ │
│   │   ─────   ─────────────────      ─────────────────   ──────────    │ │
│   │   t1      if (value > 0)                              1            │ │
│   │   t2      // yes, it's 1!        if (value > 0)       1            │ │
│   │   t3                             // yes, it's 1!      1            │ │
│   │   t4      value--                                     0            │ │
│   │   t5                             value--              -1 ← ERROR!  │ │
│   │   t6      enter critical                                           │ │
│   │   t7                             enter critical       BOTH IN!     │ │
│   │                                                                     │ │
│   │   Both processes entered the critical section!                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HOW THE KERNEL ACHIEVES ATOMICITY:                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. DISABLE INTERRUPTS (uniprocessor):                             │ │
│   │      cli();           // Disable interrupts                         │ │
│   │      // Critical operation                                          │ │
│   │      sti();           // Enable interrupts                          │ │
│   │                                                                     │ │
│   │   2. SPINLOCKS (multiprocessor):                                    │ │
│   │      spin_lock(&sem->lock);                                         │ │
│   │      // Critical operation                                          │ │
│   │      spin_unlock(&sem->lock);                                       │ │
│   │                                                                     │ │
│   │   3. ATOMIC CPU INSTRUCTIONS:                                       │ │
│   │      LOCK CMPXCHG  (compare-and-swap)                               │ │
│   │      LOCK XADD     (atomic add)                                     │ │
│   │      LOCK BTS      (test-and-set)                                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Critical Sections

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CRITICAL SECTIONS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DEFINITION: A critical section is a code segment that accesses shared    │
│   resources and MUST NOT be executed by more than one process/thread       │
│   simultaneously.                                                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ANATOMY OF CRITICAL SECTION PROTECTION:                           │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────┐           │ │
│   │   │                                                     │           │ │
│   │   │   /* Non-critical section - parallel OK */          │           │ │
│   │   │   prepare_data();                                   │           │ │
│   │   │                                                     │           │ │
│   │   │   ┌─────────────────────────────────────────┐       │           │ │
│   │   │   │  P(semaphore);   /* ENTRY SECTION */    │       │           │ │
│   │   │   └─────────────────────────────────────────┘       │           │ │
│   │   │                                                     │           │ │
│   │   │   ┌─────────────────────────────────────────┐       │           │ │
│   │   │   │  /* CRITICAL SECTION */                 │       │           │ │
│   │   │   │  shared_counter++;                      │       │           │ │
│   │   │   │  shared_buffer[i] = data;               │       │           │ │
│   │   │   └─────────────────────────────────────────┘       │           │ │
│   │   │                                                     │           │ │
│   │   │   ┌─────────────────────────────────────────┐       │           │ │
│   │   │   │  V(semaphore);   /* EXIT SECTION */     │       │           │ │
│   │   │   └─────────────────────────────────────────┘       │           │ │
│   │   │                                                     │           │ │
│   │   │   /* Non-critical section - parallel OK */          │           │ │
│   │   │   process_result();                                 │           │ │
│   │   │                                                     │           │ │
│   │   └─────────────────────────────────────────────────────┘           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FOUR REQUIREMENTS FOR CORRECT CRITICAL SECTION SOLUTION:                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. MUTUAL EXCLUSION:                                              │ │
│   │      At most ONE process in critical section at any time.           │ │
│   │                                                                     │ │
│   │   2. PROGRESS:                                                      │ │
│   │      If no process is in critical section and some want to enter,   │ │
│   │      one of them MUST eventually be allowed in.                     │ │
│   │      (No deadlock in entry protocol)                                │ │
│   │                                                                     │ │
│   │   3. BOUNDED WAITING:                                               │ │
│   │      A process waiting to enter will eventually get in.             │ │
│   │      (No starvation)                                                │ │
│   │                                                                     │ │
│   │   4. NO ASSUMPTIONS ABOUT SPEED:                                    │ │
│   │      Solution must work regardless of relative process speeds       │ │
│   │      or number of CPUs.                                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SEMAPHORES SATISFY ALL FOUR REQUIREMENTS (when used correctly)           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Types of Semaphores

### Binary Semaphores (Mutexes)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BINARY SEMAPHORES                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A binary semaphore has only two values: 0 or 1                           │
│   It provides MUTUAL EXCLUSION - exactly like a lock.                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   STATES:                                                           │ │
│   │   ┌─────────────────┐        ┌─────────────────┐                    │ │
│   │   │   VALUE = 1     │        │   VALUE = 0     │                    │ │
│   │   │   ───────────   │        │   ───────────   │                    │ │
│   │   │   UNLOCKED      │   P()  │   LOCKED        │                    │ │
│   │   │   Available     │ ─────► │   Unavailable   │                    │ │
│   │   │   🟢 GREEN      │        │   🔴 RED        │                    │ │
│   │   └─────────────────┘        └─────────────────┘                    │ │
│   │           ▲                           │                             │ │
│   │           │         V()               │                             │ │
│   │           └───────────────────────────┘                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   USAGE PATTERN:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sem_t mutex;                                                      │ │
│   │   sem_init(&mutex, 0, 1);    /* Initialize to 1 (unlocked) */       │ │
│   │                                                                     │ │
│   │   /* Process A */             /* Process B */                       │ │
│   │   sem_wait(&mutex);  ─────►  sem_wait(&mutex);  // BLOCKS!          │ │
│   │   /* critical section */                                            │ │
│   │   shared_data = 42;                                                 │ │
│   │   sem_post(&mutex);  ─────►  // Now B unblocks                      │ │
│   │                              /* critical section */                 │ │
│   │                              shared_data = 99;                      │ │
│   │                              sem_post(&mutex);                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BINARY SEMAPHORE vs MUTEX:                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Feature            │  Binary Semaphore  │  Mutex                  │ │
│   │   ───────────────────┼────────────────────┼──────────────────       │ │
│   │   Ownership          │  No owner          │  Has owner              │ │
│   │   Release by other   │  YES (anyone)      │  NO (only owner)        │ │
│   │   Priority inherit.  │  Usually no        │  Usually yes            │ │
│   │   Recursive locking  │  No                │  Optional               │ │
│   │   Use case           │  Signaling         │  Mutual exclusion       │ │
│   │                                                                     │ │
│   │   KEY INSIGHT: A binary semaphore CAN be released by a different    │ │
│   │   process than acquired it. A mutex CANNOT.                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Counting Semaphores

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COUNTING SEMAPHORES                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A counting semaphore can have any non-negative integer value.            │
│   It represents the number of available resources.                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   EXAMPLE: Database Connection Pool (5 connections)                 │ │
│   │                                                                     │ │
│   │   sem_t conn_pool;                                                  │ │
│   │   sem_init(&conn_pool, 0, 5);  /* 5 connections available */        │ │
│   │                                                                     │ │
│   │   Initial state:                                                    │ │
│   │   ┌───┬───┬───┬───┬───┐                                             │ │
│   │   │ 1 │ 2 │ 3 │ 4 │ 5 │  VALUE = 5                                  │ │
│   │   └───┴───┴───┴───┴───┘                                             │ │
│   │                                                                     │ │
│   │   After 3 processes call sem_wait():                                │ │
│   │   ┌───┬───┬───┬───┬───┐                                             │ │
│   │   │ X │ X │ X │ 4 │ 5 │  VALUE = 2                                  │ │
│   │   └───┴───┴───┴───┴───┘                                             │ │
│   │     ↑   ↑   ↑                                                       │ │
│   │    P1  P2  P3 (using connections)                                   │ │
│   │                                                                     │ │
│   │   After 2 more processes call sem_wait():                           │ │
│   │   ┌───┬───┬───┬───┬───┐                                             │ │
│   │   │ X │ X │ X │ X │ X │  VALUE = 0                                  │ │
│   │   └───┴───┴───┴───┴───┘                                             │ │
│   │                                                                     │ │
│   │   6th process calls sem_wait(): BLOCKS! (waits for connection)      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON USE CASES:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. RESOURCE POOLS:                                                │ │
│   │      - Database connections                                         │ │
│   │      - Thread pool workers                                          │ │
│   │      - Memory buffers                                               │ │
│   │      - File handles                                                 │ │
│   │                                                                     │ │
│   │   2. PRODUCER-CONSUMER BUFFERS:                                     │ │
│   │      - empty_slots semaphore (counts empty buffer slots)            │ │
│   │      - full_slots semaphore (counts filled buffer slots)            │ │
│   │                                                                     │ │
│   │   3. RATE LIMITING:                                                 │ │
│   │      - Limit concurrent operations to N                             │ │
│   │      - Throttle requests                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Named vs Unnamed Semaphores

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NAMED vs UNNAMED SEMAPHORES                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   UNNAMED SEMAPHORES (Memory-Based):                                │ │
│   │   ──────────────────────────────────                                │ │
│   │                                                                     │ │
│   │   sem_t sem;                                                        │ │
│   │   sem_init(&sem, pshared, initial_value);                           │ │
│   │                                                                     │ │
│   │   • Live in process memory (stack, heap, or shared memory)          │ │
│   │   • pshared = 0: threads within same process                        │ │
│   │   • pshared = 1: processes (must be in shared memory!)              │ │
│   │   • No name, no filesystem presence                                 │ │
│   │   • Destroyed with sem_destroy()                                    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────┐               │ │
│   │   │  Process A                                      │               │ │
│   │   │  ┌────────────────────────────┐                 │               │ │
│   │   │  │  Shared Memory             │                 │               │ │
│   │   │  │  ┌─────────────────────┐   │                 │               │ │
│   │   │  │  │  sem_t unnamed_sem  │◄──┼─────────────────┼───┐           │ │
│   │   │  │  └─────────────────────┘   │                 │   │           │ │
│   │   │  └────────────────────────────┘                 │   │           │ │
│   │   └─────────────────────────────────────────────────┘   │           │ │
│   │                                                         │           │ │
│   │   ┌─────────────────────────────────────────────────┐   │           │ │
│   │   │  Process B (maps same shared memory) ───────────┼───┘           │ │
│   │   └─────────────────────────────────────────────────┘               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   NAMED SEMAPHORES (Filesystem-Based):                              │ │
│   │   ────────────────────────────────────                              │ │
│   │                                                                     │ │
│   │   sem_t *sem = sem_open("/my_semaphore", O_CREAT, 0644, 1);         │ │
│   │                                                                     │ │
│   │   • Have a name (like "/my_semaphore")                              │ │
│   │   • Persist in the filesystem (typically /dev/shm/)                 │ │
│   │   • Multiple unrelated processes can open by name                   │ │
│   │   • Persist until explicitly unlinked with sem_unlink()             │ │
│   │   • Survive process termination (until unlinked)                    │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────┐               │ │
│   │   │  Filesystem: /dev/shm/sem.my_semaphore          │               │ │
│   │   │  ┌─────────────────────────────────────────┐    │               │ │
│   │   │  │  Named Semaphore Object                 │    │               │ │
│   │   │  │  Name: "/my_semaphore"                  │    │               │ │
│   │   │  │  Value: 1                               │    │               │ │
│   │   │  └─────────────────────────────────────────┘    │               │ │
│   │   └─────────────────────────────────────────────────┘               │ │
│   │            ▲                    ▲                                   │ │
│   │            │                    │                                   │ │
│   │      ┌─────┴─────┐        ┌─────┴─────┐                             │ │
│   │      │ Process A │        │ Process B │  (completely separate)      │ │
│   │      │ sem_open()│        │ sem_open()│                             │ │
│   │      └───────────┘        └───────────┘                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMPARISON:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Feature              │  Unnamed            │  Named               │ │
│   │   ─────────────────────┼─────────────────────┼────────────────────  │ │
│   │   Creation             │  sem_init()         │  sem_open()          │ │
│   │   Destruction          │  sem_destroy()      │  sem_close() +       │ │
│   │                        │                     │  sem_unlink()        │ │
│   │   Sharing (threads)    │  Easy               │  Easy                │ │
│   │   Sharing (processes)  │  Requires shm       │  Easy (by name)      │ │
│   │   Persistence          │  Dies with memory   │  Until unlinked      │ │
│   │   Overhead             │  Lower              │  Higher              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Semaphore Operations

### P Operation (Wait/Down/Acquire)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    P OPERATION (WAIT/DOWN/ACQUIRE)                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The P operation (from Dutch "Proberen" - to test/try) DECREMENTS the     │
│   semaphore value, blocking if the result would be negative.               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ALGORITHM (Conceptual):                                           │ │
│   │                                                                     │ │
│   │   P(semaphore S):                                                   │ │
│   │       ATOMIC {                                                      │ │
│   │           while (S.value <= 0) {                                    │ │
│   │               // Add this process to S.wait_queue                   │ │
│   │               // Block (sleep)                                      │ │
│   │           }                                                         │ │
│   │           S.value = S.value - 1;                                    │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │   ALTERNATIVE FORMULATION (Dijkstra's original):                    │ │
│   │                                                                     │ │
│   │   P(semaphore S):                                                   │ │
│   │       ATOMIC {                                                      │ │
│   │           S.value = S.value - 1;                                    │ │
│   │           if (S.value < 0) {                                        │ │
│   │               // Add this process to S.wait_queue                   │ │
│   │               // Block (sleep)                                      │ │
│   │           }                                                         │ │
│   │       }                                                             │ │
│   │       // |S.value| = number of waiting processes                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL FLOW:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                    ┌─────────────────────┐                          │ │
│   │                    │    P(semaphore)     │                          │ │
│   │                    └──────────┬──────────┘                          │ │
│   │                               │                                     │ │
│   │                               ▼                                     │ │
│   │                    ┌─────────────────────┐                          │ │
│   │                    │   value > 0?        │                          │ │
│   │                    └──────────┬──────────┘                          │ │
│   │                       YES │         │ NO                            │ │
│   │                           ▼         ▼                               │ │
│   │              ┌──────────────┐    ┌──────────────────┐               │ │
│   │              │  value--     │    │  Add to wait     │               │ │
│   │              │  Continue    │    │  queue, SLEEP    │               │ │
│   │              └──────────────┘    └────────┬─────────┘               │ │
│   │                                           │                         │ │
│   │                                           ▼                         │ │
│   │                               ┌─────────────────────┐               │ │
│   │                               │  (Woken by V())     │               │ │
│   │                               │  value--, Continue  │               │ │
│   │                               └─────────────────────┘               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VARIANTS:                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. sem_wait()      - Blocking wait (standard)                     │ │
│   │   2. sem_trywait()   - Non-blocking (returns EAGAIN if would block) │ │
│   │   3. sem_timedwait() - Wait with timeout                            │ │
│   │                                                                     │ │
│   │   /* Non-blocking example */                                        │ │
│   │   if (sem_trywait(&sem) == -1) {                                    │ │
│   │       if (errno == EAGAIN) {                                        │ │
│   │           printf("Semaphore busy, doing something else\n");         │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Timed wait example */                                          │ │
│   │   struct timespec ts;                                               │ │
│   │   clock_gettime(CLOCK_REALTIME, &ts);                               │ │
│   │   ts.tv_sec += 5;  /* 5 second timeout */                           │ │
│   │   if (sem_timedwait(&sem, &ts) == -1) {                             │ │
│   │       if (errno == ETIMEDOUT) {                                     │ │
│   │           printf("Timeout waiting for semaphore\n");                │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### V Operation (Signal/Up/Release)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    V OPERATION (SIGNAL/UP/RELEASE)                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The V operation (from Dutch "Verhogen" - to increment) INCREMENTS the    │
│   semaphore value, potentially waking a blocked process.                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ALGORITHM:                                                        │ │
│   │                                                                     │ │
│   │   V(semaphore S):                                                   │ │
│   │       ATOMIC {                                                      │ │
│   │           S.value = S.value + 1;                                    │ │
│   │           if (S.wait_queue is not empty) {                          │ │
│   │               // Remove one process from S.wait_queue               │ │
│   │               // Wake that process (make it runnable)               │ │
│   │           }                                                         │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │   NOTE: V() NEVER blocks! It always succeeds immediately.           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL FLOW:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                    ┌─────────────────────┐                          │ │
│   │                    │    V(semaphore)     │                          │ │
│   │                    └──────────┬──────────┘                          │ │
│   │                               │                                     │ │
│   │                               ▼                                     │ │
│   │                    ┌─────────────────────┐                          │ │
│   │                    │     value++         │                          │ │
│   │                    └──────────┬──────────┘                          │ │
│   │                               │                                     │ │
│   │                               ▼                                     │ │
│   │                    ┌─────────────────────┐                          │ │
│   │                    │ Waiters queued?     │                          │ │
│   │                    └──────────┬──────────┘                          │ │
│   │                       YES │         │ NO                            │ │
│   │                           ▼         ▼                               │ │
│   │              ┌──────────────┐    ┌──────────────┐                   │ │
│   │              │  Wake ONE    │    │   Done       │                   │ │
│   │              │  waiter      │    │   (return)   │                   │ │
│   │              └──────────────┘    └──────────────┘                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WAKEUP POLICIES:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   When multiple processes are waiting, which one gets woken?        │ │
│   │                                                                     │ │
│   │   1. FIFO (First In, First Out):                                    │ │
│   │      - Most common, fair                                            │ │
│   │      - Prevents starvation                                          │ │
│   │      - Processes wake in the order they blocked                     │ │
│   │                                                                     │ │
│   │   2. Priority-Based:                                                │ │
│   │      - Higher priority processes wake first                         │ │
│   │      - Can cause starvation of low-priority processes               │ │
│   │      - Used in real-time systems                                    │ │
│   │                                                                     │ │
│   │   3. Random/Arbitrary:                                              │ │
│   │      - No guarantees                                                │ │
│   │      - Simplest to implement                                        │ │
│   │      - May cause starvation                                         │ │
│   │                                                                     │ │
│   │   POSIX does NOT specify which policy! Implementation-defined.      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Atomicity Requirement

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE ATOMICITY REQUIREMENT                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   P() and V() MUST be atomic - they cannot be interrupted midway.          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WHY ATOMICITY IS CRITICAL:                                        │ │
│   │                                                                     │ │
│   │   Consider non-atomic P():                                          │ │
│   │                                                                     │ │
│   │   P(S):                            Time  Process A     Process B    │ │
│   │     if (S.value > 0) {             ────  ──────────    ──────────   │ │
│   │         S.value--;                 t1    if(val>0)     ...          │ │
│   │     } else {                       t2    ...           if(val>0)    │ │
│   │         block();                   t3    val--         ...          │ │
│   │     }                              t4    ...           val--        │ │
│   │                                                                     │ │
│   │   If S.value was 1, both processes see value > 0 and decrement!     │ │
│   │   Result: S.value = -1 (INVALID!) and both in critical section!     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL IMPLEMENTATION OF ATOMICITY:                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Linux kernel semaphore P() - simplified */                     │ │
│   │                                                                     │ │
│   │   void down(struct semaphore *sem)                                  │ │
│   │   {                                                                 │ │
│   │       unsigned long flags;                                          │ │
│   │                                                                     │ │
│   │       raw_spin_lock_irqsave(&sem->lock, flags);  /* ATOMIC START */ │ │
│   │                                                                     │ │
│   │       if (likely(sem->count > 0)) {                                 │ │
│   │           sem->count--;                                             │ │
│   │       } else {                                                      │ │
│   │           __down(sem);  /* Add to wait queue, sleep */              │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │       raw_spin_unlock_irqrestore(&sem->lock, flags); /* ATOMIC END */│ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   KEY POINTS:                                                       │ │
│   │   • Spinlock protects the semaphore structure                       │ │
│   │   • Interrupts disabled to prevent preemption                       │ │
│   │   • The test-and-decrement is now atomic                            │ │
│   │   • Sleep happens with spinlock released (but state is consistent)  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Kernel Implementation

### Semaphore Data Structures

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL SEMAPHORE DATA STRUCTURES                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   LINUX KERNEL SEMAPHORE (include/linux/semaphore.h):               │ │
│   │                                                                     │ │
│   │   struct semaphore {                                                │ │
│   │       raw_spinlock_t      lock;       /* Protects count & wait_list*/│ │
│   │       unsigned int        count;      /* Resource count            */│ │
│   │       struct list_head    wait_list;  /* List of waiting tasks     */│ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   MEMORY LAYOUT:                                                    │ │
│   │   ┌────────────────────────────────────────────┐                    │ │
│   │   │  struct semaphore                          │                    │ │
│   │   │  ┌──────────────────────────────────────┐  │                    │ │
│   │   │  │  raw_spinlock_t lock                 │  │  ← Mutual exclusion│ │
│   │   │  │  ┌───────────────────┐               │  │    for the struct │ │
│   │   │  │  │  raw_lock = 0/1   │               │  │                    │ │
│   │   │  │  └───────────────────┘               │  │                    │ │
│   │   │  ├──────────────────────────────────────┤  │                    │ │
│   │   │  │  unsigned int count = N              │  │  ← Available count │ │
│   │   │  ├──────────────────────────────────────┤  │                    │ │
│   │   │  │  struct list_head wait_list          │  │  ← Blocked tasks   │ │
│   │   │  │  ┌───────────────────┐               │  │                    │ │
│   │   │  │  │  next ──────────────────┐         │  │                    │ │
│   │   │  │  │  prev ◄─────────────────┼─┐       │  │                    │ │
│   │   │  │  └───────────────────┘     │ │       │  │                    │ │
│   │   │  └────────────────────────────┼─┼───────┘  │                    │ │
│   │   └───────────────────────────────┼─┼──────────┘                    │ │
│   │                                   │ │                               │ │
│   │                                   ▼ │                               │ │
│   │   ┌───────────────────────────────┴─┴──────────────────────┐        │ │
│   │   │  struct semaphore_waiter (per blocked task)            │        │ │
│   │   │  ┌──────────────────────────────────────────────────┐  │        │ │
│   │   │  │  struct list_head list;  /* Links to wait_list   */│  │        │ │
│   │   │  │  struct task_struct *task; /* Pointer to task    */│  │        │ │
│   │   │  │  bool up;                 /* Woken by up()?      */│  │        │ │
│   │   │  └──────────────────────────────────────────────────┘  │        │ │
│   │   └────────────────────────────────────────────────────────┘        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Wait Queues and Blocking

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WAIT QUEUES AND BLOCKING                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When a process blocks on a semaphore, it's added to the wait queue:      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   BLOCKING SEQUENCE:                                                │ │
│   │                                                                     │ │
│   │   1. Process calls down() / sem_wait()                              │ │
│   │   2. Kernel acquires semaphore spinlock                             │ │
│   │   3. Check: count > 0?                                              │ │
│   │      • YES: Decrement count, release lock, return                   │ │
│   │      • NO:  Continue to step 4...                                   │ │
│   │   4. Allocate semaphore_waiter structure on kernel stack            │ │
│   │   5. Add waiter to wait_list (FIFO order)                           │ │
│   │   6. Set task state to TASK_UNINTERRUPTIBLE or TASK_INTERRUPTIBLE   │ │
│   │   7. Release spinlock                                               │ │
│   │   8. Call schedule() - context switch to another process            │ │
│   │   9. [Process is now sleeping...]                                   │ │
│   │                                                                     │ │
│   │   WAKE SEQUENCE (when another process calls up()/sem_post()):       │ │
│   │                                                                     │ │
│   │   1. Process calls up() / sem_post()                                │ │
│   │   2. Kernel acquires semaphore spinlock                             │ │
│   │   3. Increment count                                                │ │
│   │   4. Check: wait_list empty?                                        │ │
│   │      • YES: Release lock, return                                    │ │
│   │      • NO:  Continue to step 5...                                   │ │
│   │   5. Remove first waiter from wait_list                             │ │
│   │   6. Set waiter->up = true                                          │ │
│   │   7. wake_up_process(waiter->task) - make runnable                  │ │
│   │   8. Release spinlock                                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL: WAIT QUEUE OPERATIONS                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Initial: count=0, three processes waiting                         │ │
│   │                                                                     │ │
│   │   ┌─────────────────┐                                               │ │
│   │   │  SEMAPHORE      │                                               │ │
│   │   │  count = 0      │                                               │ │
│   │   │  wait_list ─────┼──► [P1] ──► [P2] ──► [P3] ──► (end)           │ │
│   │   └─────────────────┘     ▲                                         │ │
│   │                           │ First to wake                           │ │
│   │                                                                     │ │
│   │   After V() (sem_post):                                             │ │
│   │                                                                     │ │
│   │   ┌─────────────────┐                                               │ │
│   │   │  SEMAPHORE      │     [P1] ──► RUNNING!                         │ │
│   │   │  count = 0      │      ↑                                        │ │
│   │   │  wait_list ─────┼──► [P2] ──► [P3] ──► (end)                    │ │
│   │   └─────────────────┘                                               │ │
│   │                                                                     │ │
│   │   Note: count stays 0 because P1 immediately "consumes" the signal  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   INTERRUPTIBLE vs UNINTERRUPTIBLE SLEEP:                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TASK_UNINTERRUPTIBLE:                                             │ │
│   │   • Cannot be woken by signals                                      │ │
│   │   • Shows as 'D' in ps (uninterruptible sleep)                      │ │
│   │   • Used by: sem_wait() [typically]                                 │ │
│   │   • Problem: unkillable processes if semaphore never signaled       │ │
│   │                                                                     │ │
│   │   TASK_INTERRUPTIBLE:                                               │ │
│   │   • Can be woken by signals (returns -EINTR)                        │ │
│   │   • Shows as 'S' in ps (sleeping)                                   │ │
│   │   • Used by: down_interruptible()                                   │ │
│   │   • Must check return value and handle interruption                 │ │
│   │                                                                     │ │
│   │   if (down_interruptible(&sem)) {                                   │ │
│   │       return -ERESTARTSYS;  /* Signal received, retry or abort */   │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The sys_semop Algorithm

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE sys_semop ALGORITHM                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   sys_semop() is the System V system call for semaphore operations.        │
│   It can perform MULTIPLE operations ATOMICALLY on a semaphore SET.        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SYSTEM CALL SIGNATURE:                                            │ │
│   │                                                                     │ │
│   │   int semop(int semid,        /* Semaphore set ID */                │ │
│   │             struct sembuf *ops, /* Array of operations */           │ │
│   │             size_t nops);       /* Number of operations */          │ │
│   │                                                                     │ │
│   │   struct sembuf {                                                   │ │
│   │       unsigned short sem_num;   /* Semaphore index in set */        │ │
│   │       short          sem_op;    /* Operation value */               │ │
│   │       short          sem_flg;   /* Flags (IPC_NOWAIT, SEM_UNDO) */  │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   OPERATION VALUES (sem_op):                                        │ │
│   │   • sem_op > 0:  Add to semaphore value (like V())                  │ │
│   │   • sem_op < 0:  Subtract from value, block if result < 0 (like P())│ │
│   │   • sem_op = 0:  Wait until semaphore value becomes 0               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ALGORITHM OVERVIEW:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sys_semop(semid, ops, nops):                                      │ │
│   │                                                                     │ │
│   │   1. Validate semid, get semaphore set                              │ │
│   │   2. Lock the semaphore set                                         │ │
│   │                                                                     │ │
│   │   3. TRY_AGAIN:                                                     │ │
│   │      for each operation op in ops:                                  │ │
│   │          if (operation would block) {                               │ │
│   │              if (IPC_NOWAIT) return -EAGAIN                         │ │
│   │              add to wait queue                                      │ │
│   │              unlock, sleep, relock                                  │ │
│   │              goto TRY_AGAIN   /* Retry ALL operations */            │ │
│   │          }                                                          │ │
│   │                                                                     │ │
│   │   4. All operations can proceed:                                    │ │
│   │      for each operation op in ops:                                  │ │
│   │          apply operation to semaphore                               │ │
│   │          if (SEM_UNDO) record adjustment value                      │ │
│   │                                                                     │ │
│   │   5. Wake any processes that can now proceed                        │ │
│   │   6. Unlock, return success                                         │ │
│   │                                                                     │ │
│   │   KEY INSIGHT: ALL operations must succeed, or NONE do.             │ │
│   │   This enables complex atomic multi-semaphore transactions.         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Handling Process Termination

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HANDLING PROCESS TERMINATION                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   What happens if a process holding a semaphore dies?                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   THE PROBLEM:                                                      │ │
│   │                                                                     │ │
│   │   Process A:                              Semaphore:                │ │
│   │   ──────────                              ──────────                │ │
│   │   sem_wait(&sem);  // value: 1 → 0                                  │ │
│   │   /* In critical section */                                         │ │
│   │   /* CRASH! */             💥                                       │ │
│   │   /* sem_post() never called! */                                    │ │
│   │                                           value = 0 FOREVER!        │ │
│   │                                                                     │ │
│   │   Process B: sem_wait(&sem);  // BLOCKS FOREVER (DEADLOCK!)         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SYSTEM V SOLUTION: SEM_UNDO                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct sembuf op = {                                              │ │
│   │       .sem_num = 0,                                                 │ │
│   │       .sem_op  = -1,                                                │ │
│   │       .sem_flg = SEM_UNDO    /* ← THE MAGIC FLAG */                 │ │
│   │   };                                                                │ │
│   │   semop(semid, &op, 1);                                             │ │
│   │                                                                     │ │
│   │   HOW IT WORKS:                                                     │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │                                                           │     │ │
│   │   │   1. Kernel tracks "adjustment value" per process/sem     │     │ │
│   │   │   2. When op=-1 with SEM_UNDO: adjustment += 1            │     │ │
│   │   │   3. When op=+1 with SEM_UNDO: adjustment -= 1            │     │ │
│   │   │   4. On process exit: semaphore += adjustment             │     │ │
│   │   │                                                           │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                                                                     │ │
│   │   EXAMPLE:                                                          │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │                                                           │     │ │
│   │   │   Process A:                adjustment   sem.value        │     │ │
│   │   │   ──────────────────────    ──────────   ─────────        │     │ │
│   │   │   semop(..., -1, SEM_UNDO)    +1           0              │     │ │
│   │   │   /* CRASH! */                                            │     │ │
│   │   │   /* exit() called by kernel */                           │     │ │
│   │   │   /* kernel: sem += adjustment (+1) */                    │     │ │
│   │   │                                 0           1 ← RECOVERED! │     │ │
│   │   │                                                           │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   POSIX SEMAPHORES: NO AUTOMATIC RECOVERY!                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   POSIX named/unnamed semaphores have NO equivalent to SEM_UNDO.    │ │
│   │   If a process dies holding a POSIX semaphore, it stays locked!     │ │
│   │                                                                     │ │
│   │   SOLUTIONS:                                                        │ │
│   │   1. Use robust mutexes instead (pthread_mutexattr_setrobust)       │ │
│   │   2. Use file-based locking with automatic cleanup (flock/fcntl)    │ │
│   │   3. Use System V semaphores with SEM_UNDO                          │ │
│   │   4. Implement application-level recovery/timeout mechanisms        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. POSIX Semaphores

### Unnamed Semaphores (sem_init)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX UNNAMED SEMAPHORES                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   INITIALIZATION:                                                   │ │
│   │                                                                     │ │
│   │   #include <semaphore.h>                                            │ │
│   │                                                                     │ │
│   │   sem_t sem;                                                        │ │
│   │                                                                     │ │
│   │   int sem_init(sem_t *sem,      /* Pointer to semaphore */          │ │
│   │                int pshared,      /* 0=threads, 1=processes */       │ │
│   │                unsigned value);  /* Initial value */                │ │
│   │                                                                     │ │
│   │   RETURNS: 0 on success, -1 on error (check errno)                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   USAGE EXAMPLES:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Example 1: Thread synchronization (mutex-like) */              │ │
│   │                                                                     │ │
│   │   sem_t mutex;                                                      │ │
│   │   int shared_counter = 0;                                           │ │
│   │                                                                     │ │
│   │   int main() {                                                      │ │
│   │       sem_init(&mutex, 0, 1);  /* pshared=0, value=1 */             │ │
│   │                                                                     │ │
│   │       /* Create threads... */                                       │ │
│   │       pthread_create(&t1, NULL, worker, NULL);                      │ │
│   │       pthread_create(&t2, NULL, worker, NULL);                      │ │
│   │                                                                     │ │
│   │       /* Wait for threads... */                                     │ │
│   │       pthread_join(t1, NULL);                                       │ │
│   │       pthread_join(t2, NULL);                                       │ │
│   │                                                                     │ │
│   │       sem_destroy(&mutex);                                          │ │
│   │       return 0;                                                     │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void *worker(void *arg) {                                         │ │
│   │       for (int i = 0; i < 100000; i++) {                            │ │
│   │           sem_wait(&mutex);      /* P() - acquire */                │ │
│   │           shared_counter++;      /* Critical section */             │ │
│   │           sem_post(&mutex);      /* V() - release */                │ │
│   │       }                                                             │ │
│   │       return NULL;                                                  │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Named Semaphores (sem_open)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX NAMED SEMAPHORES                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CREATING/OPENING:                                                 │ │
│   │                                                                     │ │
│   │   #include <fcntl.h>                                                │ │
│   │   #include <semaphore.h>                                            │ │
│   │                                                                     │ │
│   │   /* Create new or open existing */                                 │ │
│   │   sem_t *sem = sem_open(const char *name,  /* "/name" format */     │ │
│   │                         int oflag,          /* O_CREAT, O_EXCL */   │ │
│   │                         mode_t mode,        /* Permissions */       │ │
│   │                         unsigned value);    /* Initial value */     │ │
│   │                                                                     │ │
│   │   /* Open existing only */                                          │ │
│   │   sem_t *sem = sem_open("/my_sem", 0);  /* No creation flags */     │ │
│   │                                                                     │ │
│   │   RETURNS: Pointer to sem_t on success, SEM_FAILED on error         │ │
│   │                                                                     │ │
│   │   NAME RULES:                                                       │ │
│   │   • Must begin with '/'                                             │ │
│   │   • No other '/' allowed (implementation-defined)                   │ │
│   │   • Maximum length: NAME_MAX - 4 (typically 251 chars)              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMPLETE EXAMPLE: Inter-Process Synchronization                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* === producer.c === */                                          │ │
│   │   #include <stdio.h>                                                │ │
│   │   #include <fcntl.h>                                                │ │
│   │   #include <semaphore.h>                                            │ │
│   │   #include <sys/mman.h>                                             │ │
│   │                                                                     │ │
│   │   #define SEM_NAME "/my_sem"                                        │ │
│   │   #define SHM_NAME "/my_shm"                                        │ │
│   │                                                                     │ │
│   │   int main() {                                                      │ │
│   │       /* Create semaphore (initially 0 - nothing produced yet) */   │ │
│   │       sem_t *sem = sem_open(SEM_NAME, O_CREAT, 0644, 0);            │ │
│   │       if (sem == SEM_FAILED) { perror("sem_open"); return 1; }      │ │
│   │                                                                     │ │
│   │       /* Create shared memory for data */                           │ │
│   │       int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0644);          │ │
│   │       ftruncate(fd, sizeof(int));                                   │ │
│   │       int *shared = mmap(NULL, sizeof(int), PROT_READ|PROT_WRITE,   │ │
│   │                          MAP_SHARED, fd, 0);                        │ │
│   │                                                                     │ │
│   │       /* Produce data */                                            │ │
│   │       *shared = 42;                                                 │ │
│   │       printf("Produced: %d\n", *shared);                            │ │
│   │                                                                     │ │
│   │       /* Signal consumer */                                         │ │
│   │       sem_post(sem);                                                │ │
│   │                                                                     │ │
│   │       sem_close(sem);                                               │ │
│   │       return 0;                                                     │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* === consumer.c === */                                          │ │
│   │   int main() {                                                      │ │
│   │       sem_t *sem = sem_open(SEM_NAME, 0);  /* Open existing */      │ │
│   │       int fd = shm_open(SHM_NAME, O_RDONLY, 0);                     │ │
│   │       int *shared = mmap(NULL, sizeof(int), PROT_READ,              │ │
│   │                          MAP_SHARED, fd, 0);                        │ │
│   │                                                                     │ │
│   │       /* Wait for producer */                                       │ │
│   │       sem_wait(sem);                                                │ │
│   │                                                                     │ │
│   │       printf("Consumed: %d\n", *shared);                            │ │
│   │                                                                     │ │
│   │       sem_close(sem);                                               │ │
│   │       sem_unlink(SEM_NAME);  /* Clean up */                         │ │
│   │       shm_unlink(SHM_NAME);                                         │ │
│   │       return 0;                                                     │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### API Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX SEMAPHORE API REFERENCE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   FUNCTION          │ DESCRIPTION                                   │ │
│   │   ──────────────────┼─────────────────────────────────────────────  │ │
│   │   sem_init()        │ Initialize unnamed semaphore                  │ │
│   │   sem_destroy()     │ Destroy unnamed semaphore                     │ │
│   │   sem_open()        │ Open/create named semaphore                   │ │
│   │   sem_close()       │ Close named semaphore                         │ │
│   │   sem_unlink()      │ Remove named semaphore from filesystem        │ │
│   │   sem_wait()        │ P() - decrement, block if 0                   │ │
│   │   sem_trywait()     │ P() - non-blocking, returns EAGAIN            │ │
│   │   sem_timedwait()   │ P() - with timeout                            │ │
│   │   sem_post()        │ V() - increment, wake waiter                  │ │
│   │   sem_getvalue()    │ Get current value (snapshot only!)            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DETAILED SIGNATURES:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int sem_wait(sem_t *sem);                                         │ │
│   │       /* Blocks until semaphore > 0, then decrements               */│ │
│   │       /* Returns: 0 on success, -1 on error                        */│ │
│   │                                                                     │ │
│   │   int sem_trywait(sem_t *sem);                                      │ │
│   │       /* Non-blocking: returns immediately                         */│ │
│   │       /* Returns: 0 if decremented, -1 with errno=EAGAIN if not    */│ │
│   │                                                                     │ │
│   │   int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout);│ │
│   │       /* Blocks until semaphore > 0 OR timeout expires             */│ │
│   │       /* Returns: 0 on success, -1 with errno=ETIMEDOUT on timeout */│ │
│   │       /* NOTE: abs_timeout is ABSOLUTE time (CLOCK_REALTIME)       */│ │
│   │                                                                     │ │
│   │   int sem_post(sem_t *sem);                                         │ │
│   │       /* Increments semaphore, wakes one waiter if any             */│ │
│   │       /* NEVER blocks                                              */│ │
│   │       /* Returns: 0 on success, -1 on error                        */│ │
│   │                                                                     │ │
│   │   int sem_getvalue(sem_t *sem, int *sval);                          │ │
│   │       /* Gets current value (for debugging/monitoring)             */│ │
│   │       /* WARNING: Value may change immediately after call!         */│ │
│   │       /* Returns: 0 on success, -1 on error                        */│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Error Handling

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX SEMAPHORE ERROR HANDLING                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   COMMON ERRORS:                                                    │ │
│   │                                                                     │ │
│   │   errno         │ Meaning                     │ Function(s)         │ │
│   │   ──────────────┼─────────────────────────────┼─────────────────    │ │
│   │   EINVAL        │ Invalid semaphore           │ All                 │ │
│   │   EAGAIN        │ Would block (trywait)       │ sem_trywait         │ │
│   │   ETIMEDOUT     │ Timeout expired             │ sem_timedwait       │ │
│   │   EINTR         │ Interrupted by signal       │ sem_wait/timedwait  │ │
│   │   EOVERFLOW     │ Value would exceed SEM_VALUE_MAX │ sem_post       │ │
│   │   EACCES        │ Permission denied           │ sem_open            │ │
│   │   EEXIST        │ Exists (O_CREAT|O_EXCL)     │ sem_open            │ │
│   │   ENOENT        │ Doesn't exist (no O_CREAT)  │ sem_open            │ │
│   │   ENOMEM        │ Out of memory               │ sem_open/init       │ │
│   │   ENOSYS        │ Not supported               │ sem_init (pshared)  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ROBUST ERROR HANDLING PATTERN:                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Safe wait with signal handling */                              │ │
│   │   int safe_sem_wait(sem_t *sem) {                                   │ │
│   │       while (1) {                                                   │ │
│   │           if (sem_wait(sem) == 0) {                                 │ │
│   │               return 0;  /* Success */                              │ │
│   │           }                                                         │ │
│   │           if (errno != EINTR) {                                     │ │
│   │               return -1;  /* Real error */                          │ │
│   │           }                                                         │ │
│   │           /* EINTR: interrupted by signal, retry */                 │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Safe wait with timeout */                                      │ │
│   │   int sem_wait_timeout_ms(sem_t *sem, int timeout_ms) {             │ │
│   │       struct timespec ts;                                           │ │
│   │       clock_gettime(CLOCK_REALTIME, &ts);                           │ │
│   │       ts.tv_sec  += timeout_ms / 1000;                              │ │
│   │       ts.tv_nsec += (timeout_ms % 1000) * 1000000;                  │ │
│   │       if (ts.tv_nsec >= 1000000000) {                               │ │
│   │           ts.tv_sec++;                                              │ │
│   │           ts.tv_nsec -= 1000000000;                                 │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │       while (1) {                                                   │ │
│   │           if (sem_timedwait(sem, &ts) == 0) return 0;               │ │
│   │           if (errno == ETIMEDOUT) return -1;  /* Timeout */         │ │
│   │           if (errno != EINTR) return -2;      /* Error */           │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. System V Semaphores

### Semaphore Sets

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM V SEMAPHORE SETS                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   System V IPC provides semaphores as SETS - arrays of semaphores that     │
│   can be operated on atomically as a group.                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   KEY DIFFERENCES FROM POSIX:                                       │ │
│   │                                                                     │ │
│   │   Feature           │ POSIX            │ System V                   │ │
│   │   ──────────────────┼──────────────────┼──────────────────────────  │ │
│   │   Basic unit        │ Single semaphore │ Set of semaphores          │ │
│   │   Identification    │ Name or pointer  │ Integer ID (semid)         │ │
│   │   Multiple ops      │ No               │ Yes (atomic)               │ │
│   │   SEM_UNDO          │ No               │ Yes                        │ │
│   │   Persistence       │ Name-based       │ Until explicitly removed   │ │
│   │   Overhead          │ Lower            │ Higher                     │ │
│   │   Interface         │ Simple           │ Complex                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SEMAPHORE SET STRUCTURE:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Semaphore Set (semid = 12345)                                     │ │
│   │   ┌─────────────────────────────────────────────────────────┐       │ │
│   │   │                                                         │       │ │
│   │   │   sem[0]     sem[1]     sem[2]     sem[3]                │       │ │
│   │   │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐              │       │ │
│   │   │  │ val=3 │  │ val=1 │  │ val=0 │  │ val=5 │              │       │ │
│   │   │  └───────┘  └───────┘  └───────┘  └───────┘              │       │ │
│   │   │                                                         │       │ │
│   │   │   Each semaphore has:                                   │       │ │
│   │   │   • semval  - current value                             │       │ │
│   │   │   • sempid  - PID of last operation                     │       │ │
│   │   │   • semncnt - count of processes waiting for increase   │       │ │
│   │   │   • semzcnt - count of processes waiting for zero       │       │ │
│   │   │                                                         │       │ │
│   │   └─────────────────────────────────────────────────────────┘       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### semget, semop, semctl

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM V SEMAPHORE SYSTEM CALLS                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. semget() - CREATE OR ACCESS A SEMAPHORE SET                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   #include <sys/types.h>                                            │ │
│   │   #include <sys/ipc.h>                                              │ │
│   │   #include <sys/sem.h>                                              │ │
│   │                                                                     │ │
│   │   int semget(key_t key,      /* IPC key or IPC_PRIVATE */           │ │
│   │              int nsems,      /* Number of semaphores in set */      │ │
│   │              int semflg);    /* IPC_CREAT, IPC_EXCL, permissions */ │ │
│   │                                                                     │ │
│   │   RETURNS: semaphore set ID on success, -1 on error                 │ │
│   │                                                                     │ │
│   │   CREATING A KEY:                                                   │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   /* Method 1: Use ftok() to generate key from file path */ │   │ │
│   │   │   key_t key = ftok("/tmp/myapp", 'S');                      │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Method 2: Use a hardcoded key (risky!) */              │   │ │
│   │   │   key_t key = 0x12345678;                                   │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Method 3: IPC_PRIVATE for related processes */         │   │ │
│   │   │   int semid = semget(IPC_PRIVATE, 3, 0644);                 │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   EXAMPLE - Creating/Opening:                                       │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   key_t key = ftok("/tmp/myapp", 'S');                      │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Create new semaphore set with 3 semaphores */          │   │ │
│   │   │   int semid = semget(key, 3, IPC_CREAT | IPC_EXCL | 0644);  │   │ │
│   │   │   if (semid == -1) {                                        │   │ │
│   │   │       if (errno == EEXIST) {                                │   │ │
│   │   │           /* Already exists, open existing */               │   │ │
│   │   │           semid = semget(key, 0, 0);                        │   │ │
│   │   │       } else {                                              │   │ │
│   │   │           perror("semget");                                 │   │ │
│   │   │           exit(1);                                          │   │ │
│   │   │       }                                                     │   │ │
│   │   │   }                                                         │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   2. semop() - PERFORM OPERATIONS ON SEMAPHORES                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int semop(int semid,              /* Semaphore set ID */          │ │
│   │             struct sembuf *sops,    /* Array of operations */       │ │
│   │             size_t nsops);          /* Number of operations */      │ │
│   │                                                                     │ │
│   │   struct sembuf {                                                   │ │
│   │       unsigned short sem_num;  /* Semaphore index in set */         │ │
│   │       short          sem_op;   /* Operation (see below) */          │ │
│   │       short          sem_flg;  /* IPC_NOWAIT, SEM_UNDO */           │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   OPERATION VALUES (sem_op):                                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   sem_op > 0:  ADD to semaphore value (V operation)         │   │ │
│   │   │                semval += sem_op                             │   │ │
│   │   │                Never blocks                                 │   │ │
│   │   │                                                             │   │ │
│   │   │   sem_op < 0:  SUBTRACT from semaphore (P operation)        │   │ │
│   │   │                If semval >= |sem_op|: semval -= |sem_op|    │   │ │
│   │   │                If semval < |sem_op|:  BLOCK until possible  │   │ │
│   │   │                                                             │   │ │
│   │   │   sem_op = 0:  WAIT FOR ZERO                                │   │ │
│   │   │                Block until semval becomes 0                 │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   ATOMIC MULTIPLE OPERATIONS:                                       │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   /* Acquire TWO resources atomically */                    │   │ │
│   │   │   struct sembuf ops[2] = {                                  │   │ │
│   │   │       { .sem_num = 0, .sem_op = -1, .sem_flg = 0 },         │   │ │
│   │   │       { .sem_num = 1, .sem_op = -1, .sem_flg = 0 }          │   │ │
│   │   │   };                                                        │   │ │
│   │   │                                                             │   │ │
│   │   │   /* This blocks until BOTH semaphores can be decremented */│   │ │
│   │   │   /* Either both succeed or neither - prevents deadlock!  */│   │ │
│   │   │   if (semop(semid, ops, 2) == -1) {                         │   │ │
│   │   │       perror("semop");                                      │   │ │
│   │   │   }                                                         │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   3. semctl() - CONTROL OPERATIONS                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int semctl(int semid,       /* Semaphore set ID */                │ │
│   │              int semnum,      /* Semaphore index (cmd dependent) */ │ │
│   │              int cmd,         /* Command */                         │ │
│   │              ...);            /* Optional union semun arg */        │ │
│   │                                                                     │ │
│   │   /* Must define this union yourself! */                            │ │
│   │   union semun {                                                     │ │
│   │       int              val;    /* Value for SETVAL */               │ │
│   │       struct semid_ds *buf;    /* Buffer for IPC_STAT, IPC_SET */   │ │
│   │       unsigned short  *array;  /* Array for GETALL, SETALL */       │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   COMMON COMMANDS:                                                  │ │
│   │   ┌────────────────┬────────────────────────────────────────────┐   │ │
│   │   │ SETVAL         │ Set single semaphore value                 │   │ │
│   │   │ GETVAL         │ Get single semaphore value                 │   │ │
│   │   │ SETALL         │ Set all semaphore values                   │   │ │
│   │   │ GETALL         │ Get all semaphore values                   │   │ │
│   │   │ IPC_RMID       │ Remove semaphore set                       │   │ │
│   │   │ IPC_STAT       │ Get semaphore set info                     │   │ │
│   │   │ GETPID         │ Get PID of last semop                      │   │ │
│   │   │ GETNCNT        │ Get count waiting for increase             │   │ │
│   │   │ GETZCNT        │ Get count waiting for zero                 │   │ │
│   │   └────────────────┴────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   EXAMPLE - Initialize and Remove:                                  │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   union semun arg;                                          │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Initialize single semaphore */                         │   │ │
│   │   │   arg.val = 1;                                              │   │ │
│   │   │   semctl(semid, 0, SETVAL, arg);  /* sem[0] = 1 */          │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Initialize all at once */                              │   │ │
│   │   │   unsigned short init_vals[] = {1, 5, 10};                  │   │ │
│   │   │   arg.array = init_vals;                                    │   │ │
│   │   │   semctl(semid, 0, SETALL, arg);  /* sem[0]=1,1,2=10 */     │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Get current value */                                   │   │ │
│   │   │   int val = semctl(semid, 0, GETVAL);                       │   │ │
│   │   │                                                             │   │ │
│   │   │   /* Remove semaphore set */                                │   │ │
│   │   │   semctl(semid, 0, IPC_RMID);  /* semnum ignored */         │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```




### SEM_UNDO and Process Crash Recovery

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEM_UNDO: AUTOMATIC CLEANUP ON EXIT                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM: What happens if a process crashes while holding a          │
│   semaphore? The resource is locked forever!                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A              Semaphore              Process B           │ │
│   │   ┌────────┐             ┌───────┐              ┌────────┐          │ │
│   │   │        │─ P() ─────▶│ 1→0  │              │        │          │ │
│   │   │        │             │       │              │        │          │ │
│   │   │ CRASH! │             │       │◀─ P() ──────│ WAIT   │          │ │
│   │   │   ✗    │             │       │   blocks    │   .    │          │ │
│   │   └────────┘             │       │              │   .    │          │ │
│   │                          │val=0  │              │   .    │          │ │
│   │   Process A is gone      │       │              │forever │          │ │
│   │   but semaphore          └───────┘              │blocked │          │ │
│   │   stays at 0!                                   └────────┘          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE SOLUTION: SEM_UNDO                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   When a process performs semop() with SEM_UNDO flag, the kernel    │ │
│   │   maintains an "adjustment value" for that process. When the        │ │
│   │   process terminates (normally OR abnormally), the kernel           │ │
│   │   automatically reverses all SEM_UNDO operations.                   │ │
│   │                                                                     │ │
│   │   Process A              Kernel                 Semaphore           │ │
│   │   ┌────────┐             ┌─────────────────┐    ┌───────┐           │ │
│   │   │        │─ P() with ─▶│ semadj[A] = +1  │───▶│ 1→0  │           │ │
│   │   │        │  SEM_UNDO   │                 │    │       │           │ │
│   │   │ CRASH! │             │                 │    │       │           │ │
│   │   │   ✗    │             │                 │    │       │           │ │
│   │   └────────┘             │ Exit handler:   │    │       │           │ │
│   │                          │ semval += semadj│───▶│ 0→1  │ Restored! │ │
│   │                          │ (0 + 1 = 1)     │    │       │           │ │
│   │                          └─────────────────┘    └───────┘           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HOW SEM_UNDO WORKS:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   For each (process, semaphore) pair, kernel maintains:             │ │
│   │                                                                     │ │
│   │   struct sem_undo {                                                 │ │
│   │       struct sem_undo *proc_next;  /* per-process list */           │ │
│   │       struct sem_undo *id_next;    /* per-semaphore-set list */     │ │
│   │       int              semid;                                       │ │
│   │       short           *semadj;     /* adjustment per semaphore */   │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   ADJUSTMENT RULES:                                                 │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  Operation      │ semval change │ semadj change             │   │ │
│   │   │  ───────────────┼───────────────┼─────────────────────────  │   │ │
│   │   │  P() (sem_op<0) │ semval -= N   │ semadj += N               │   │ │
│   │   │  V() (sem_op>0) │ semval += N   │ semadj -= N               │   │ │
│   │   │  On exit        │ semval +=semadj│ (adjustment applied)     │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE: Safe Lock/Unlock with SEM_UNDO                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int safe_lock(int semid, int semnum) {                            │ │
│   │       struct sembuf op = {                                          │ │
│   │           .sem_num = semnum,                                        │ │
│   │           .sem_op  = -1,                                            │ │
│   │           .sem_flg = SEM_UNDO  /* <-- Key flag! */                  │ │
│   │       };                                                            │ │
│   │       return semop(semid, &op, 1);                                  │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   int safe_unlock(int semid, int semnum) {                          │ │
│   │       struct sembuf op = {                                          │ │
│   │           .sem_num = semnum,                                        │ │
│   │           .sem_op  = +1,                                            │ │
│   │           .sem_flg = SEM_UNDO  /* Must match! */                    │ │
│   │       };                                                            │ │
│   │       return semop(semid, &op, 1);                                  │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   /* Usage */                                                       │ │
│   │   safe_lock(semid, 0);                                              │ │
│   │   /* Critical section - even if we crash here, lock is released */ │ │
│   │   safe_unlock(semid, 0);                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WARNING: SEM_UNDO limitations                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • semadj can overflow (ERANGE) if too many operations             │ │
│   │   • Does NOT work across exec() - adjustments are cleared           │ │
│   │   • Does NOT work with fork() - child gets fresh semadj             │ │
│   │   • Adds kernel memory overhead per process per semaphore           │ │
│   │   • Undo may cause semval to exceed SEMVMX (implementation varies)  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Classic Synchronization Problems

### Producer-Consumer Problem

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE PRODUCER-CONSUMER PROBLEM                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Also known as the "bounded buffer problem" - one of the most            │
│   fundamental synchronization challenges in concurrent programming.        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   PRODUCER(s)              BUFFER                 CONSUMER(s)       │ │
│   │   ┌─────────┐         ┌───────────────┐           ┌─────────┐       │ │
│   │   │ Generate│         │ ┌─┬─┬─┬─┬─┬─┐ │           │ Process │       │ │
│   │   │  Data   │────────▶│ │█│█│█│ │ │ │ │──────────▶│  Data   │       │ │
│   │   │         │  put()  │ └─┴─┴─┴─┴─┴─┘ │   get()   │         │       │ │
│   │   └─────────┘         │  (bounded)     │           └─────────┘       │ │
│   │                       └───────────────┘                              │ │
│   │                                                                     │ │
│   │   CONSTRAINTS:                                                      │ │
│   │   • Producer must wait if buffer is FULL                            │ │
│   │   • Consumer must wait if buffer is EMPTY                           │ │
│   │   • Only ONE process can access buffer at a time (mutual exclusion) │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SEMAPHORE SOLUTION:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Three semaphores needed:                                          │ │
│   │                                                                     │ │
│   │   ┌──────────────┬────────────────────────────────────────────┐     │ │
│   │   │ Semaphore    │ Purpose                                    │     │ │
│   │   │──────────────┼────────────────────────────────────────────│     │ │
│   │   │ mutex = 1    │ Mutual exclusion for buffer access         │     │ │
│   │   │ empty = N    │ Count of empty slots (N = buffer size)     │     │ │
│   │   │ full  = 0    │ Count of full slots (items available)      │     │ │
│   │   └──────────────┴────────────────────────────────────────────┘     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IMPLEMENTATION:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sem_t mutex, empty, full;                                         │ │
│   │   #define BUFFER_SIZE 10                                            │ │
│   │   int buffer[BUFFER_SIZE];                                          │ │
│   │   int in = 0, out = 0;                                              │ │
│   │                                                                     │ │
│   │   void init() {                                                     │ │
│   │       sem_init(&mutex, 0, 1);           /* Binary semaphore */      │ │
│   │       sem_init(&empty, 0, BUFFER_SIZE); /* N empty slots */         │ │
│   │       sem_init(&full,  0, 0);           /* 0 full slots */          │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void producer() {                                                 │ │
│   │       while (1) {                                                   │ │
│   │           int item = produce_item();                                │ │
│   │                                                                     │ │
│   │           sem_wait(&empty);     /* Wait for empty slot */           │ │
│   │           sem_wait(&mutex);     /* Enter critical section */        │ │
│   │                                                                     │ │
│   │           buffer[in] = item;    /* Add to buffer */                 │ │
│   │           in = (in + 1) % BUFFER_SIZE;                              │ │
│   │                                                                     │ │
│   │           sem_post(&mutex);     /* Exit critical section */         │ │
│   │           sem_post(&full);      /* Signal item available */         │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void consumer() {                                                 │ │
│   │       while (1) {                                                   │ │
│   │           sem_wait(&full);      /* Wait for item */                 │ │
│   │           sem_wait(&mutex);     /* Enter critical section */        │ │
│   │                                                                     │ │
│   │           int item = buffer[out]; /* Remove from buffer */          │ │
│   │           out = (out + 1) % BUFFER_SIZE;                            │ │
│   │                                                                     │ │
│   │           sem_post(&mutex);     /* Exit critical section */         │ │
│   │           sem_post(&empty);     /* Signal slot available */         │ │
│   │                                                                     │ │
│   │           consume_item(item);                                       │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CRITICAL: Order of sem_wait() calls matters!                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG (causes deadlock):         CORRECT:                         │ │
│   │   ┌─────────────────────────┐      ┌─────────────────────────┐      │ │
│   │   │                         │      │                         │      │ │
│   │   │  sem_wait(&mutex);      │      │  sem_wait(&empty);      │      │ │
│   │   │  sem_wait(&empty); ←BUG │      │  sem_wait(&mutex);      │      │ │
│   │   │  ...                    │      │  ...                    │      │ │
│   │   │                         │      │                         │      │ │
│   │   └─────────────────────────┘      └─────────────────────────┘      │ │
│   │                                                                     │ │
│   │   If producer holds mutex and waits for empty, but consumer         │ │
│   │   needs mutex to free a slot → DEADLOCK!                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Readers-Writers Problem

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE READERS-WRITERS PROBLEM                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Multiple readers can read simultaneously, but writers need exclusive     │
│   access. This is the basis for read-write locks (rwlocks).                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌─────────┐                              ┌─────────┐              │ │
│   │   │ Reader 1│──read──┐                     │ Writer  │              │ │
│   │   └─────────┘        │    ┌──────────┐     └────┬────┘              │ │
│   │   ┌─────────┐        ├───▶│ RESOURCE │◀────────┘                   │ │
│   │   │ Reader 2│──read──┘    └──────────┘     write (exclusive)        │ │
│   │   └─────────┘ (concurrent)                                          │ │
│   │                                                                     │ │
│   │   RULES:                                                            │ │
│   │   • Multiple readers can read simultaneously                        │ │
│   │   • Writers need exclusive access (no readers, no other writers)    │ │
│   │   • Various policies for fairness                                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTION 1: Readers Preference (Writers may starve)                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sem_t mutex = 1;      /* Protects reader_count */                 │ │
│   │   sem_t wrt = 1;        /* Writer access / reader blocking */       │ │
│   │   int reader_count = 0;                                             │ │
│   │                                                                     │ │
│   │   void reader() {                                                   │ │
│   │       sem_wait(&mutex);                                             │ │
│   │       reader_count++;                                               │ │
│   │       if (reader_count == 1)                                        │ │
│   │           sem_wait(&wrt);     /* First reader blocks writers */     │ │
│   │       sem_post(&mutex);                                             │ │
│   │                                                                     │ │
│   │       /* === READING (concurrent with other readers) === */         │ │
│   │       read_data();                                                  │ │
│   │                                                                     │ │
│   │       sem_wait(&mutex);                                             │ │
│   │       reader_count--;                                               │ │
│   │       if (reader_count == 0)                                        │ │
│   │           sem_post(&wrt);     /* Last reader unblocks writers */    │ │
│   │       sem_post(&mutex);                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void writer() {                                                   │ │
│   │       sem_wait(&wrt);         /* Exclusive access */                │ │
│   │                                                                     │ │
│   │       /* === WRITING (exclusive) === */                             │ │
│   │       write_data();                                                 │ │
│   │                                                                     │ │
│   │       sem_post(&wrt);                                               │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   PROBLEM: Continuous readers can starve writers forever!           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTION 2: Writers Preference (Readers may starve)                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sem_t mutex1 = 1, mutex2 = 1, mutex3 = 1;                         │ │
│   │   sem_t wrt = 1, read_try = 1;                                      │ │
│   │   int reader_count = 0, writer_count = 0;                           │ │
│   │                                                                     │ │
│   │   void reader() {                                                   │ │
│   │       sem_wait(&mutex3);                                            │ │
│   │       sem_wait(&read_try);    /* Block if writer waiting */         │ │
│   │       sem_wait(&mutex1);                                            │ │
│   │       reader_count++;                                               │ │
│   │       if (reader_count == 1) sem_wait(&wrt);                        │ │
│   │       sem_post(&mutex1);                                            │ │
│   │       sem_post(&read_try);                                          │ │
│   │       sem_post(&mutex3);                                            │ │
│   │                                                                     │ │
│   │       read_data();                                                  │ │
│   │                                                                     │ │
│   │       sem_wait(&mutex1);                                            │ │
│   │       reader_count--;                                               │ │
│   │       if (reader_count == 0) sem_post(&wrt);                        │ │
│   │       sem_post(&mutex1);                                            │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void writer() {                                                   │ │
│   │       sem_wait(&mutex2);                                            │ │
│   │       writer_count++;                                               │ │
│   │       if (writer_count == 1) sem_wait(&read_try); /* Block readers*/│ │
│   │       sem_post(&mutex2);                                            │ │
│   │                                                                     │ │
│   │       sem_wait(&wrt);         /* Exclusive write access */          │ │
│   │       write_data();                                                 │ │
│   │       sem_post(&wrt);                                               │ │
│   │                                                                     │ │
│   │       sem_wait(&mutex2);                                            │ │
│   │       writer_count--;                                               │ │
│   │       if (writer_count == 0) sem_post(&read_try);                   │ │
│   │       sem_post(&mutex2);                                            │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```




### Dining Philosophers Problem

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE DINING PHILOSOPHERS PROBLEM                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Five philosophers sit at a round table. Each needs TWO forks to eat.    │
│   There are only five forks (one between each pair of philosophers).       │
│   This problem demonstrates deadlock and starvation issues.                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                          [P0]                                       │ │
│   │                       /       \                                     │ │
│   │                    f4           f0                                  │ │
│   │                    /             \                                  │ │
│   │                 [P4]             [P1]                               │ │
│   │                  |                 |                                │ │
│   │                 f3               f1                                 │ │
│   │                  |                 |                                │ │
│   │                 [P3]─────f2─────[P2]                               │ │
│   │                                                                     │ │
│   │   Pi = Philosopher i                                                │ │
│   │   fi = Fork i (between Pi and P(i+1)%5)                             │ │
│   │                                                                     │ │
│   │   Each philosopher alternates:                                      │ │
│   │   1. THINK (doesn't need forks)                                     │ │
│   │   2. Get hungry                                                     │ │
│   │   3. Pick up both forks                                             │ │
│   │   4. EAT                                                            │ │
│   │   5. Put down both forks                                            │ │
│   │   6. Repeat                                                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NAIVE SOLUTION (CAUSES DEADLOCK!):                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sem_t fork[5];  /* All initialized to 1 */                        │ │
│   │                                                                     │ │
│   │   void philosopher(int id) {                                        │ │
│   │       while (1) {                                                   │ │
│   │           think();                                                  │ │
│   │                                                                     │ │
│   │           sem_wait(&fork[id]);         /* Pick up left fork */      │ │
│   │           sem_wait(&fork[(id+1) % 5]); /* Pick up right fork */     │ │
│   │                                                                     │ │
│   │           eat();                                                    │ │
│   │                                                                     │ │
│   │           sem_post(&fork[id]);         /* Put down left fork */     │ │
│   │           sem_post(&fork[(id+1) % 5]); /* Put down right fork */    │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   DEADLOCK SCENARIO:                                                │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   P0 picks up f0, P1 picks up f1, P2 picks up f2,           │   │ │
│   │   │   P3 picks up f3, P4 picks up f4                            │   │ │
│   │   │                                                             │   │ │
│   │   │   Now everyone is holding their left fork and waiting       │   │ │
│   │   │   for their right fork → CIRCULAR WAIT → DEADLOCK!          │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTION 1: Limit Concurrent Diners                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Only allow 4 philosophers to try eating at once */             │ │
│   │   sem_t fork[5];     /* All = 1 */                                  │ │
│   │   sem_t room = 4;    /* Max 4 can try to eat */                     │ │
│   │                                                                     │ │
│   │   void philosopher(int id) {                                        │ │
│   │       while (1) {                                                   │ │
│   │           think();                                                  │ │
│   │                                                                     │ │
│   │           sem_wait(&room);             /* Enter dining room */      │ │
│   │           sem_wait(&fork[id]);                                      │ │
│   │           sem_wait(&fork[(id+1) % 5]);                              │ │
│   │                                                                     │ │
│   │           eat();                                                    │ │
│   │                                                                     │ │
│   │           sem_post(&fork[id]);                                      │ │
│   │           sem_post(&fork[(id+1) % 5]);                              │ │
│   │           sem_post(&room);             /* Leave dining room */      │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTION 2: Asymmetric (Odd picks left first, even picks right first)    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   void philosopher(int id) {                                        │ │
│   │       int left = id, right = (id + 1) % 5;                          │ │
│   │       while (1) {                                                   │ │
│   │           think();                                                  │ │
│   │                                                                     │ │
│   │           if (id % 2 == 0) {                                        │ │
│   │               /* Even: pick right first, then left */               │ │
│   │               sem_wait(&fork[right]);                               │ │
│   │               sem_wait(&fork[left]);                                │ │
│   │           } else {                                                  │ │
│   │               /* Odd: pick left first, then right */                │ │
│   │               sem_wait(&fork[left]);                                │ │
│   │               sem_wait(&fork[right]);                               │ │
│   │           }                                                         │ │
│   │                                                                     │ │
│   │           eat();                                                    │ │
│   │                                                                     │ │
│   │           sem_post(&fork[left]);                                    │ │
│   │           sem_post(&fork[right]);                                   │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   This breaks circular wait - adjacent philosophers pick forks      │ │
│   │   in opposite order.                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Advanced Topics

### Priority Inversion

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PRIORITY INVERSION                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A dangerous situation where a high-priority task is blocked waiting     │
│   for a low-priority task, which is itself preempted by medium-priority   │
│   tasks. The classic example crashed the Mars Pathfinder mission in 1997! │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   THREE TASKS:                                                      │ │
│   │   • High priority (H) - Critical task                               │ │
│   │   • Medium priority (M) - Less critical                             │ │
│   │   • Low priority (L) - Background task                              │ │
│   │                                                                     │ │
│   │   TIMELINE:                                                         │ │
│   │                                                                     │ │
│   │   Time ─────────────────────────────────────────────────────────▶   │ │
│   │                                                                     │ │
│   │   L: [acquire lock]────────────────[preempted]................      │ │
│   │                                           │                         │ │
│   │   M:                   [runs]─────────────┼───────────────────▶     │ │
│   │                                           │                         │ │
│   │   H:               [needs lock]───────────┤                         │ │
│   │                    ↓ BLOCKED              │                         │ │
│   │                    waiting for L          │                         │ │
│   │                    but L can't run        │                         │ │
│   │                    because M is running!  │                         │ │
│   │                                           │                         │ │
│   │   RESULT: High priority H is effectively blocked by medium M!       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTION 1: Priority Inheritance                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   When H blocks waiting for L's lock, temporarily boost L's         │ │
│   │   priority to match H. Now L won't be preempted by M!               │ │
│   │                                                                     │ │
│   │   L: [acquire lock]────────────[priority boosted]────[release]      │ │
│   │                                       ↑                  ↓          │ │
│   │   H:               [needs lock]───────┼──────────────[runs]────▶    │ │
│   │                                       │                             │ │
│   │   M:                   [ready]        │                             │ │
│   │                        but can't run  │                             │ │
│   │                        (L has higher  │                             │ │
│   │                         priority now) ▼                             │ │
│   │                                                                     │ │
│   │   Linux: Use pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_     │ │
│   │          INHERIT) for priority inheritance mutexes                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTION 2: Priority Ceiling                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Each lock has a "ceiling" priority. When ANY task acquires the    │ │
│   │   lock, it runs at the ceiling priority (highest of all potential   │ │
│   │   users). Prevents the problem entirely but reduces concurrency.    │ │
│   │                                                                     │ │
│   │   Linux: pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_PROTECT) │ │
│   │          pthread_mutexattr_setprioceiling(&attr, MAX_PRIO)          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NOTE: POSIX semaphores do NOT support priority inheritance!              │
│   Use pthread_mutex with PTHREAD_PRIO_INHERIT for real-time systems.       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Deadlock Detection and Prevention

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEADLOCK WITH SEMAPHORES                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FOUR CONDITIONS FOR DEADLOCK (Coffman conditions - ALL must be true):    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. MUTUAL EXCLUSION                                               │ │
│   │      Resources cannot be shared (e.g., binary semaphore)            │ │
│   │                                                                     │ │
│   │   2. HOLD AND WAIT                                                  │ │
│   │      Process holds resources while waiting for others               │ │
│   │                                                                     │ │
│   │   3. NO PREEMPTION                                                  │ │
│   │      Resources cannot be forcibly taken from processes              │ │
│   │                                                                     │ │
│   │   4. CIRCULAR WAIT                                                  │ │
│   │      P1 waits for P2, P2 waits for P3, ... Pn waits for P1          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PREVENTION STRATEGIES:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   BREAK HOLD-AND-WAIT:                                              │ │
│   │   • Acquire all semaphores at once (atomic with System V)           │ │
│   │   • Release all if any acquisition fails, then retry               │ │
│   │                                                                     │ │
│   │   struct sembuf ops[2] = {                                          │ │
│   │       { 0, -1, IPC_NOWAIT },  /* Try sem 0 */                       │ │
│   │       { 1, -1, IPC_NOWAIT }   /* Try sem 1 */                       │ │
│   │   };                                                                │ │
│   │   /* Atomic: either BOTH succeed or NEITHER */                      │ │
│   │   if (semop(semid, ops, 2) == -1 && errno == EAGAIN) {              │ │
│   │       /* Couldn't get both - try again later */                     │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │                                                                     │ │
│   │   BREAK CIRCULAR WAIT (Resource ordering):                          │ │
│   │   • Always acquire semaphores in a fixed global order               │ │
│   │   • If you need sem[3] and sem[1], ALWAYS get sem[1] first          │ │
│   │                                                                     │ │
│   │   void acquire_multiple(int *sems, int n) {                         │ │
│   │       /* Sort semaphore indices */                                  │ │
│   │       qsort(sems, n, sizeof(int), compare_int);                     │ │
│   │       /* Acquire in order */                                        │ │
│   │       for (int i = 0; i < n; i++) {                                 │ │
│   │           sem_wait(&semaphores[sems[i]]);                           │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   ─────────────────────────────────────────────────────────────     │ │
│   │                                                                     │ │
│   │   USE TIMEOUTS (sem_timedwait):                                     │ │
│   │   • Don't wait forever - detect potential deadlock                  │ │
│   │                                                                     │ │
│   │   struct timespec ts = { .tv_sec = time(NULL) + 5 };  /* 5 sec */   │ │
│   │   if (sem_timedwait(&sem, &ts) == -1 && errno == ETIMEDOUT) {       │ │
│   │       /* Possible deadlock - release held resources and retry */    │ │
│   │       release_held_resources();                                     │ │
│   │       handle_timeout();                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Semaphores vs Mutexes vs Condition Variables

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYNCHRONIZATION PRIMITIVES COMPARISON                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Feature          │ Semaphore │ Mutex     │ Cond Var               │ │
│   │  ─────────────────┼───────────┼───────────┼───────────────────     │ │
│   │  Purpose          │ Counting/ │ Mutual    │ Wait for               │ │
│   │                   │ signaling │ exclusion │ condition              │ │
│   │                   │           │           │                        │ │
│   │  Ownership        │ None      │ Yes       │ N/A                    │ │
│   │                   │           │ (thread)  │                        │ │
│   │                   │           │           │                        │ │
│   │  Who can release? │ Anyone    │ Owner only│ N/A (signal)           │ │
│   │                   │           │           │                        │ │
│   │  Initial value    │ Any ≥ 0   │ 1 (locked)│ N/A                    │ │
│   │                   │           │           │                        │ │
│   │  Can count?       │ Yes       │ No        │ No                     │ │
│   │                   │           │           │                        │ │
│   │  Priority inherit │ No        │ Yes*      │ Via mutex              │ │
│   │                   │           │           │                        │ │
│   │  Recursive?       │ N/A       │ Optional  │ N/A                    │ │
│   │                   │           │           │                        │ │
│   │  * With PTHREAD_PRIO_INHERIT                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHEN TO USE WHAT:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   USE MUTEX WHEN:                                                   │ │
│   │   • Protecting a critical section                                   │ │
│   │   • You need ownership (only locker can unlock)                     │ │
│   │   • You need priority inheritance                                   │ │
│   │   • You need recursive locking                                      │ │
│   │                                                                     │ │
│   │   USE SEMAPHORE WHEN:                                               │ │
│   │   • Counting resources (connection pool, buffer slots)              │ │
│   │   • Signaling between threads/processes                             │ │
│   │   • One thread signals, different thread waits                      │ │
│   │   • Inter-process synchronization (named semaphores)                │ │
│   │                                                                     │ │
│   │   USE CONDITION VARIABLE WHEN:                                      │ │
│   │   • Waiting for a complex condition                                 │ │
│   │   • Producer-consumer with pthread_mutex                            │ │
│   │   • Need to broadcast to multiple waiters                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PRODUCER-CONSUMER: Semaphore vs Condition Variable                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* SEMAPHORE VERSION */          /* CONDVAR VERSION */            │ │
│   │                                                                     │ │
│   │   sem_t empty, full, mutex;        pthread_mutex_t mutex;           │ │
│   │                                    pthread_cond_t not_empty;        │ │
│   │                                    pthread_cond_t not_full;         │ │
│   │                                    int count = 0;                   │ │
│   │                                                                     │ │
│   │   /* Producer */                   /* Producer */                   │ │
│   │   sem_wait(&empty);                pthread_mutex_lock(&mutex);      │ │
│   │   sem_wait(&mutex);                while (count == MAX)             │ │
│   │   /* add item */                     pthread_cond_wait(&not_full,   │ │
│   │   sem_post(&mutex);                                    &mutex);     │ │
│   │   sem_post(&full);                 /* add item */                   │ │
│   │                                    count++;                         │ │
│   │                                    pthread_cond_signal(&not_empty); │ │
│   │                                    pthread_mutex_unlock(&mutex);    │ │
│   │                                                                     │ │
│   │   Semaphore: Simpler, works       Condvar: More flexible,          │ │
│   │   inter-process                   handles complex conditions        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Practical Implementation

### Common Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE USAGE PATTERNS                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PATTERN 1: Resource Pool                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Connection pool with max 10 connections */                     │ │
│   │   sem_t pool_sem;                                                   │ │
│   │   connection_t connections[10];                                     │ │
│   │   pthread_mutex_t pool_mutex;                                       │ │
│   │                                                                     │ │
│   │   void init_pool() {                                                │ │
│   │       sem_init(&pool_sem, 0, 10);  /* 10 available */               │ │
│   │       pthread_mutex_init(&pool_mutex, NULL);                        │ │
│   │       for (int i = 0; i < 10; i++)                                  │ │
│   │           connections[i].in_use = 0;                                │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   connection_t *get_connection() {                                  │ │
│   │       sem_wait(&pool_sem);     /* Wait for available */             │ │
│   │       pthread_mutex_lock(&pool_mutex);                              │ │
│   │       for (int i = 0; i < 10; i++) {                                │ │
│   │           if (!connections[i].in_use) {                             │ │
│   │               connections[i].in_use = 1;                            │ │
│   │               pthread_mutex_unlock(&pool_mutex);                    │ │
│   │               return &connections[i];                               │ │
│   │           }                                                         │ │
│   │       }                                                             │ │
│   │       pthread_mutex_unlock(&pool_mutex);                            │ │
│   │       return NULL; /* Should never happen */                        │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void release_connection(connection_t *conn) {                     │ │
│   │       pthread_mutex_lock(&pool_mutex);                              │ │
│   │       conn->in_use = 0;                                             │ │
│   │       pthread_mutex_unlock(&pool_mutex);                            │ │
│   │       sem_post(&pool_sem);     /* Signal available */               │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PATTERN 2: Rate Limiter                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* Allow max 100 requests per second */                           │ │
│   │   sem_t rate_sem;                                                   │ │
│   │                                                                     │ │
│   │   void *refill_thread(void *arg) {                                  │ │
│   │       while (1) {                                                   │ │
│   │           usleep(10000);  /* Every 10ms */                          │ │
│   │           int val;                                                  │ │
│   │           sem_getvalue(&rate_sem, &val);                            │ │
│   │           if (val < 100) sem_post(&rate_sem);  /* Add token */      │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   void process_request() {                                          │ │
│   │       sem_wait(&rate_sem);  /* Consume token */                     │ │
│   │       do_work();                                                    │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PATTERN 3: Barrier (Rendezvous Point)                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   /* All N threads must arrive before any can proceed */            │ │
│   │   sem_t barrier_mutex, barrier1, barrier2;                          │ │
│   │   int barrier_count = 0;                                            │ │
│   │   int N;  /* Number of threads */                                   │ │
│   │                                                                     │ │
│   │   void barrier() {                                                  │ │
│   │       /* Phase 1: Wait for all to arrive */                         │ │
│   │       sem_wait(&barrier_mutex);                                     │ │
│   │       barrier_count++;                                              │ │
│   │       if (barrier_count == N) {                                     │ │
│   │           /* Last one: release all */                               │ │
│   │           for (int i = 0; i < N; i++) sem_post(&barrier1);          │ │
│   │       }                                                             │ │
│   │       sem_post(&barrier_mutex);                                     │ │
│   │       sem_wait(&barrier1);  /* Wait until all arrived */            │ │
│   │                                                                     │ │
│   │       /* Phase 2: Reset for reuse */                                │ │
│   │       sem_wait(&barrier_mutex);                                     │ │
│   │       barrier_count--;                                              │ │
│   │       if (barrier_count == 0) {                                     │ │
│   │           /* Last one: ready barrier for reuse */                   │ │
│   │       }                                                             │ │
│   │       sem_post(&barrier_mutex);                                     │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Performance Considerations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE PERFORMANCE                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   OVERHEAD COMPARISON:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Operation              │ Typical latency (uncontended)            │ │
│   │   ───────────────────────┼─────────────────────────────────────     │ │
│   │   Atomic increment       │ ~10-50 ns                                │ │
│   │   Spinlock               │ ~20-100 ns                               │ │
│   │   POSIX sem_wait/post    │ ~100-500 ns (uncontended)                │ │
│   │   System V semop         │ ~1-5 µs (syscall overhead)               │ │
│   │   Named semaphore        │ ~1-10 µs (filesystem lookup)             │ │
│   │                                                                     │ │
│   │   CONTENDED cases add context switch time: ~1-10 µs                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   OPTIMIZATION TIPS:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. MINIMIZE CRITICAL SECTION SIZE                                 │ │
│   │      • Don't do I/O while holding semaphore                         │ │
│   │      • Don't call functions that might block                        │ │
│   │      • Prepare data before, process after                           │ │
│   │                                                                     │ │
│   │      BAD:                         GOOD:                             │ │
│   │      sem_wait(&sem);              data = prepare_data();            │ │
│   │      data = prepare_data();       sem_wait(&sem);                   │ │
│   │      shared = data;               shared = data;                    │ │
│   │      log_to_file(data);           sem_post(&sem);                   │ │
│   │      sem_post(&sem);              log_to_file(data);                │ │
│   │                                                                     │ │
│   │   2. USE UNNAMED SEMAPHORES OVER NAMED (if possible)                │ │
│   │      • Named semaphores have filesystem overhead                    │ │
│   │      • Unnamed in shared memory is faster                           │ │
│   │                                                                     │ │
│   │   3. BATCH OPERATIONS WITH SYSTEM V                                 │ │
│   │      • One semop() with multiple operations                         │ │
│   │      • Better than multiple semop() calls                           │ │
│   │                                                                     │ │
│   │   4. CONSIDER ALTERNATIVES FOR HOT PATHS                            │ │
│   │      • Read-mostly: use rwlock                                      │ │
│   │      • Simple counters: use atomic operations                       │ │
│   │      • Single producer/consumer: lock-free queue                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Debugging Semaphore Issues

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEBUGGING SEMAPHORES                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   COMMON BUGS:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. FORGETTING TO POST (resource leak)                             │ │
│   │      sem_wait(&sem);                                                │ │
│   │      if (error) return;  /* BUG: sem_post never called */           │ │
│   │      sem_post(&sem);                                                │ │
│   │                                                                     │ │
│   │      FIX: Use RAII pattern or goto cleanup                          │ │
│   │                                                                     │ │
│   │   2. DOUBLE POST (count overflow)                                   │ │
│   │      sem_post(&sem);                                                │ │
│   │      sem_post(&sem);  /* Now value > 1! */                          │ │
│   │                                                                     │ │
│   │   3. WRONG SEMAPHORE                                                │ │
│   │      sem_wait(&sem_a);                                              │ │
│   │      sem_post(&sem_b);  /* Oops! */                                 │ │
│   │                                                                     │ │
│   │   4. USING DESTROYED SEMAPHORE                                      │ │
│   │      sem_destroy(&sem);                                             │ │
│   │      sem_wait(&sem);  /* Undefined behavior! */                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DEBUGGING TOOLS:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   INSPECT SYSTEM V SEMAPHORES:                                      │ │
│   │   $ ipcs -s                  # List all semaphore sets              │ │
│   │   $ ipcs -s -i <semid>       # Details of specific set              │ │
│   │   $ ipcrm -s <semid>         # Remove semaphore set                 │ │
│   │                                                                     │ │
│   │   INSPECT POSIX NAMED SEMAPHORES (Linux):                           │ │
│   │   $ ls -la /dev/shm/sem.*    # Named semaphores                     │ │
│   │                                                                     │ │
│   │   RUNTIME DEBUGGING:                                                │ │
│   │   /* Get current value */                                           │ │
│   │   int val;                                                          │ │
│   │   sem_getvalue(&sem, &val);                                         │ │
│   │   printf("sem value: %d\n", val);                                   │ │
│   │                                                                     │ │
│   │   TRACE WITH GDB:                                                   │ │
│   │   (gdb) break sem_wait                                              │ │
│   │   (gdb) break sem_post                                              │ │
│   │   (gdb) info threads          # Check thread states                 │ │
│   │                                                                     │ │
│   │   VALGRIND/HELGRIND:                                                │ │
│   │   $ valgrind --tool=helgrind ./program                              │ │
│   │   Detects lock order violations, data races                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Best Practices

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE BEST PRACTICES                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   DO:                                                               │ │
│   │   ✓ Always pair sem_wait with sem_post                              │ │
│   │   ✓ Use SEM_UNDO with System V for crash recovery                   │ │
│   │   ✓ Check return values of all semaphore operations                 │ │
│   │   ✓ Handle EINTR (signal interruption)                              │ │
│   │   ✓ Use named semaphores for inter-process, unnamed for threads     │ │
│   │   ✓ Document semaphore purpose and initial value                    │ │
│   │   ✓ Clean up: sem_destroy/sem_unlink when done                      │ │
│   │   ✓ Use consistent lock ordering to prevent deadlock                │ │
│   │   ✓ Keep critical sections short                                    │ │
│   │                                                                     │ │
│   │   DON'T:                                                            │ │
│   │   ✗ Call sem_wait/sem_post from signal handlers                     │ │
│   │   ✗ Hold semaphores across fork() (undefined behavior)              │ │
│   │   ✗ Assume sem_getvalue is accurate (use for debugging only)        │ │
│   │   ✗ Mix POSIX and System V semaphores in same sync protocol         │ │
│   │   ✗ Use semaphores when atomic operations suffice                   │ │
│   │   ✗ Forget to initialize before use                                 │ │
│   │   ✗ Call sem_destroy while threads are waiting                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CHOOSING BETWEEN POSIX AND SYSTEM V:                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Use POSIX semaphores when:                                        │ │
│   │   • Simple counting/signaling                                       │ │
│   │   • Thread synchronization                                          │ │
│   │   • Portability matters                                             │ │
│   │   • Lower overhead needed                                           │ │
│   │                                                                     │ │
│   │   Use System V semaphores when:                                     │ │
│   │   • Need atomic operations on multiple semaphores                   │ │
│   │   • Need SEM_UNDO for crash recovery                                │ │
│   │   • Legacy code compatibility                                       │ │
│   │   • Need semaphore set features                                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Summary and Reference

### Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE QUICK REFERENCE                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CONCEPT SUMMARY:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Semaphore = Integer counter + Wait queue + Atomic operations      │ │
│   │                                                                     │ │
│   │   P() / wait / down:   if (sem > 0) sem--; else BLOCK;              │ │
│   │   V() / post / up:     sem++; WAKE one waiter;                      │ │
│   │                                                                     │ │
│   │   Binary semaphore:    Value 0 or 1 (like mutex, no ownership)      │ │
│   │   Counting semaphore:  Value 0 to N (resource counting)             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   POSIX SEMAPHORES CHEAT SHEET:                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   #include <semaphore.h>                                            │ │
│   │   Link with: -pthread (or -lrt on older systems)                    │ │
│   │                                                                     │ │
│   │   UNNAMED:                                                          │ │
│   │   sem_t sem;                                                        │ │
│   │   sem_init(&sem, 0, initial_value);  /* 0 = thread-shared */        │ │
│   │   sem_wait(&sem);                    /* P() - may block */          │ │
│   │   sem_trywait(&sem);                 /* P() - never blocks */       │ │
│   │   sem_timedwait(&sem, &timeout);     /* P() - blocks with timeout */│ │
│   │   sem_post(&sem);                    /* V() - never blocks */       │ │
│   │   sem_getvalue(&sem, &val);          /* Get current value */        │ │
│   │   sem_destroy(&sem);                 /* Cleanup */                  │ │
│   │                                                                     │ │
│   │   NAMED:                                                            │ │
│   │   sem_t *sem = sem_open("/name", O_CREAT, 0644, initial_value);     │ │
│   │   sem_close(sem);                    /* Close this process's ref */ │ │
│   │   sem_unlink("/name");               /* Remove from filesystem */   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SYSTEM V SEMAPHORES CHEAT SHEET:                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   #include <sys/sem.h>                                              │ │
│   │                                                                     │ │
│   │   key_t key = ftok("/path", 'S');                                   │ │
│   │   int semid = semget(key, num_sems, IPC_CREAT | 0644);              │ │
│   │                                                                     │ │
│   │   /* Initialize */                                                  │ │
│   │   union semun { int val; } arg = { .val = 1 };                      │ │
│   │   semctl(semid, sem_num, SETVAL, arg);                              │ │
│   │                                                                     │ │
│   │   /* Operations */                                                  │ │
│   │   struct sembuf op = { sem_num, -1, SEM_UNDO };  /* P() */          │ │
│   │   semop(semid, &op, 1);                                             │ │
│   │   op.sem_op = 1;                                  /* V() */         │ │
│   │   semop(semid, &op, 1);                                             │ │
│   │                                                                     │ │
│   │   /* Remove */                                                      │ │
│   │   semctl(semid, 0, IPC_RMID);                                       │ │
│   │                                                                     │ │
│   │   /* List/remove from shell */                                      │ │
│   │   $ ipcs -s                                                         │ │
│   │   $ ipcrm -s <semid>                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Error Codes Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE ERROR CODES                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   POSIX SEMAPHORE ERRORS:                                           │ │
│   │                                                                     │ │
│   │   errno        │ Meaning                          │ Functions       │ │
│   │   ─────────────┼──────────────────────────────────┼───────────────  │ │
│   │   EINVAL       │ Invalid semaphore / bad param    │ All             │ │
│   │   EAGAIN       │ Would block (trywait)            │ sem_trywait     │ │
│   │   ETIMEDOUT    │ Timeout expired                  │ sem_timedwait   │ │
│   │   EINTR        │ Interrupted by signal            │ sem_wait/timed  │ │
│   │   EOVERFLOW    │ sem > SEM_VALUE_MAX              │ sem_post        │ │
│   │   ENOSYS       │ pshared not supported            │ sem_init        │ │
│   │   EACCES       │ Permission denied                │ sem_open        │ │
│   │   EEXIST       │ Already exists (O_EXCL)          │ sem_open        │ │
│   │   ENOENT       │ Doesn't exist (no O_CREAT)       │ sem_open        │ │
│   │   ENAMETOOLONG │ Name too long                    │ sem_open        │ │
│   │   EMFILE       │ Too many open files (process)    │ sem_open        │ │
│   │   ENFILE       │ Too many open files (system)     │ sem_open        │ │
│   │                                                                     │ │
│   │   SYSTEM V SEMAPHORE ERRORS:                                        │ │
│   │                                                                     │ │
│   │   errno        │ Meaning                          │ Functions       │ │
│   │   ─────────────┼──────────────────────────────────┼───────────────  │ │
│   │   EACCES       │ Permission denied                │ semget/semop    │ │
│   │   EEXIST       │ Already exists (IPC_EXCL)        │ semget          │ │
│   │   EINVAL       │ Invalid semid or params          │ All             │ │
│   │   ENOENT       │ Doesn't exist (no IPC_CREAT)     │ semget          │ │
│   │   ENOMEM       │ Insufficient memory              │ semget          │ │
│   │   ENOSPC       │ System limit reached             │ semget          │ │
│   │   EAGAIN       │ Would block (IPC_NOWAIT)         │ semop           │ │
│   │   EFBIG        │ sem_op too large                 │ semop           │ │
│   │   EIDRM        │ Semaphore set removed            │ semop           │ │
│   │   EINTR        │ Interrupted by signal            │ semop           │ │
│   │   ERANGE       │ semadj would overflow            │ semop           │ │
│   │   E2BIG        │ Too many operations              │ semop           │ │
│   │   EPERM        │ Not owner (IPC_RMID/IPC_SET)     │ semctl          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context and Further Reading

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HISTORICAL CONTEXT                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1965: Edsger Dijkstra invents semaphores at Technische Hogeschool       │
│         Eindhoven while working on the THE multiprogramming system.        │
│                                                                            │
│   The original Dutch names:                                                │
│   • P = "Proberen" (to try) or "Prolaag" (try-and-decrease)               │
│   • V = "Verhogen" (to increase) or "Vrijgave" (release)                  │
│                                                                            │
│   System V IPC semaphores: Introduced in Unix System V (1983)              │
│   POSIX semaphores: Standardized in POSIX.1b (1993)                        │
│                                                                            │
│   FURTHER READING:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • "The Design of the UNIX Operating System" - Maurice Bach        │ │
│   │   • "Operating System Concepts" - Silberschatz, Galvin, Gagne       │ │
│   │   • "The Little Book of Semaphores" - Allen Downey (free online)    │ │
│   │   • "Programming with POSIX Threads" - David Butenhof               │ │
│   │   • "Unix Network Programming Vol 2: IPC" - W. Richard Stevens      │ │
│   │                                                                     │ │
│   │   Man pages:                                                        │ │
│   │   • man 7 sem_overview    (POSIX semaphores overview)               │ │
│   │   • man 7 sysvipc         (System V IPC overview)                   │ │
│   │   • man 2 semget/semop/semctl                                       │ │
│   │   • man 3 sem_init/sem_wait/sem_post                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

**END OF DOCUMENT**

