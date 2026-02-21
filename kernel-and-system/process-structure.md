# The Structure of a Process

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Process Data Structures, Memory Layout, Context, and Kernel Representation

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [What is a Process?](#what-is-a-process)
   - [Process vs Program](#process-vs-program)
   - [Historical Context](#historical-context)

2. [Process Data Structures](#2-process-data-structures)
   - [The Process Table](#the-process-table)
   - [The U-Area (User Area)](#the-u-area-user-area)
   - [Process Table Entry vs U-Area](#process-table-entry-vs-u-area)
   - [The Task Structure (Modern Linux)](#the-task-structure-modern-linux)

3. [Process Memory Layout](#3-process-memory-layout)
   - [Regions and the Region Table](#regions-and-the-region-table)
   - [Text Region](#text-region)
   - [Data Region](#data-region)
   - [Stack Region](#stack-region)
   - [The Per-Process Region Table](#the-per-process-region-table)

4. [Process Context](#4-process-context)
   - [User-Level Context](#user-level-context)
   - [Register Context](#register-context)
   - [System-Level Context](#system-level-context)
   - [Context Switching](#context-switching)

5. [Process States](#5-process-states)
   - [State Diagram](#state-diagram)
   - [State Transitions](#state-transitions)
   - [Sleep and Wakeup](#sleep-and-wakeup)
   - [Zombie State](#zombie-state)

6. [Process Credentials](#6-process-credentials)
   - [User and Group IDs](#user-and-group-ids)
   - [Real vs Effective IDs](#real-vs-effective-ids)
   - [Saved Set-User-ID](#saved-set-user-id)
   - [Supplementary Groups](#supplementary-groups)

7. [Process Relationships](#7-process-relationships)
   - [Parent-Child Relationship](#parent-child-relationship)
   - [Process Groups](#process-groups)
   - [Sessions](#sessions)
   - [Controlling Terminal](#controlling-terminal)

8. [File Descriptor Table](#8-file-descriptor-table)
   - [Per-Process File Table](#per-process-file-table)
   - [System File Table](#system-file-table)
   - [Inode Table](#inode-table)
   - [File Sharing Across fork()](#file-sharing-across-fork)

9. [Signal Handling](#9-signal-handling)
   - [Signal Disposition](#signal-disposition)
   - [Signal Mask](#signal-mask)
   - [Pending Signals](#pending-signals)

10. [Process Creation and Termination](#10-process-creation-and-termination)
    - [The fork() System Call](#the-fork-system-call)
    - [The exec() Family](#the-exec-family)
    - [Process Termination](#process-termination)
    - [The wait() System Call](#the-wait-system-call)

11. [Modern Linux: task_struct](#11-modern-linux-task_struct)
    - [Thread Group and TGID](#thread-group-and-tgid)
    - [Namespaces](#namespaces)
    - [Control Groups (cgroups)](#control-groups-cgroups)

12. [Summary and Appendix](#12-summary-and-appendix)
    - [Process Structure Quick Reference](#process-structure-quick-reference)
    - [The Big Picture](#the-big-picture)

13. [References](#13-references)

---

## 1. Introduction

### What is a Process?

In the Unix operating system, a **process** is the fundamental unit of execution. It represents a program in execution—not merely the static code stored on disk, but a living entity with its own memory space, execution state, and system resources.

Maurice Bach defines a process as:

> "A process is the execution of a program and consists of a pattern of bytes that the CPU interprets as machine instructions (called 'text'), data, and a stack. Many processes appear to execute simultaneously as the kernel schedules them for execution, and several processes may be instances of one program."

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE ESSENCE OF A PROCESS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A PROGRAM is a passive entity:                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │    /bin/ls                                                          │ │
│   │    ┌──────────────────────────────────────────────────────────┐    │ │
│   │    │  ELF Header  │  .text  │  .data  │  .rodata  │  .bss    │    │ │
│   │    └──────────────────────────────────────────────────────────┘    │ │
│   │                                                                      │ │
│   │    Static bytes on disk. Does nothing by itself.                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   A PROCESS is an active entity:                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │    Process executing /bin/ls (PID 1234)                             │ │
│   │    ┌────────────────────────────────────────────────────────────┐  │ │
│   │    │                                                             │  │ │
│   │    │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │  │ │
│   │    │   │  TEXT   │  │  DATA   │  │  HEAP   │  │    STACK    │  │  │ │
│   │    │   │ (code)  │  │ (vars)  │  │(dynamic)│  │ (local vars)│  │  │ │
│   │    │   └─────────┘  └─────────┘  └─────────┘  └─────────────┘  │  │ │
│   │    │                                                             │  │ │
│   │    │   + CPU registers (PC, SP, etc.)                           │  │ │
│   │    │   + Open file descriptors                                   │  │ │
│   │    │   + Signal handlers                                         │  │ │
│   │    │   + Current working directory                               │  │ │
│   │    │   + User/group credentials                                  │  │ │
│   │    │   + Resource limits                                         │  │ │


### Process vs Program

Understanding the distinction between a process and a program is fundamental:

```
```

┌───────────────────────────────────────────────────────────────────────────┐
│                    PROGRAM vs PROCESS                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────┐    ┌─────────────────────────────────┐  │
│   │         PROGRAM             │    │           PROCESS               │  │
│   ├─────────────────────────────┤    ├─────────────────────────────────┤  │
│   │                             │    │                                 │  │
│   │  • Passive entity          │    │  • Active entity                │  │
│   │  • Stored on disk          │    │  • Exists in memory             │  │
│   │  • No state                │    │  • Has execution state          │  │
│   │  • No resources            │    │  • Owns resources               │  │
│   │  • Eternal (until deleted) │    │  • Finite lifetime              │  │
│   │  • One copy                │    │  • Many instances possible      │  │
│   │                             │    │                                 │  │
│   └─────────────────────────────┘    └─────────────────────────────────┘  │
│                                                                            │
│   ANALOGY:                                                                │
│   ─────────                                                                │
│                                                                            │
│   Program : Process  ::  Recipe : Cooking                                 │
│                                                                            │
│   A recipe (program) is a set of instructions on paper.                   │
│   Cooking (process) is the act of following those instructions,           │
│   with ingredients (data), utensils (resources), and a cook (CPU).        │
│                                                                            │
│   Multiple cooks can follow the same recipe simultaneously,               │
│   each with their own ingredients and progress.                           │
│                                                                            │
│   MULTIPLE PROCESSES, ONE PROGRAM:                                        │
│   ─────────────────────────────────                                        │
│                                                                            │
│        /bin/bash (on disk)                                                │
│              │                                                             │
│              ├──────────────────┬──────────────────┐                      │
│              │                  │                  │                      │
│              ▼                  ▼                  ▼                      │
│        ┌──────────┐       ┌──────────┐       ┌──────────┐                │
│        │ Process  │       │ Process  │       │ Process  │                │
│        │ PID 1001 │       │ PID 1002 │       │ PID 1003 │                │
│        │ (user A) │       │ (user B) │       │ (user C) │                │
│        └──────────┘       └──────────┘       └──────────┘                │
│                                                                            │
│   Each process has:                                                       │
│   • Its own virtual address space                                         │
│   • Its own file descriptors                                              │
│   • Its own current directory                                             │
│   • Its own environment variables                                         │
│   • Its own CPU register state                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

The concept of a process evolved from early batch processing systems:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF PROCESS CONCEPT                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1950s - BATCH PROCESSING:                                               │
│   ─────────────────────────                                                │
│   • One job at a time                                                     │
│   • No concept of "process"                                               │
│   • Job = program + data loaded into memory                               │
│                                                                            │
│   1960s - MULTIPROGRAMMING:                                               │
│   ──────────────────────────                                               │
│   • Multiple jobs in memory simultaneously                                │
│   • Need to track state of each job                                       │
│   • Birth of "process" concept (Multics, 1964)                            │
│                                                                            │
│   1969-1971 - UNIX AT BELL LABS:                                          │
│   ──────────────────────────────                                           │
│   • Ken Thompson and Dennis Ritchie                                       │
│   • Lightweight process model                                             │
│   • Process table + u-area design                                         │
│   • fork()/exec() paradigm                                                │
│                                                                            │
│   1980s - BSD AND SYSTEM V:                                               │
│   ─────────────────────────                                                │
│   • Job control (process groups, sessions)                                │
│   • Virtual memory (demand paging)                                        │
│   • Signals refined                                                       │
│                                                                            │
│   1990s - LINUX:                                                          │
│   ──────────────                                                           │
│   • task_struct replaces proc + u-area                                    │
│   • Threads as lightweight processes                                      │
│   • clone() system call                                                   │
│                                                                            │
│   2000s - MODERN LINUX:                                                   │
│   ─────────────────────                                                    │
│   • Namespaces (process isolation)                                        │
│   • Control groups (resource limits)                                      │
│   • Containers built on process abstraction                               │
│                                                                            │
│   TIMELINE:                                                               │
│   ─────────                                                                │
│                                                                            │
│   1960      1970      1980      1990      2000      2010      2020        │
│     │         │         │         │         │         │         │         │
│     ▼         ▼         ▼         ▼         ▼         ▼         ▼         │
│   ──┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬──       │
│     │         │         │         │         │         │         │         │
│   Multics   Unix     BSD 4.x   Linux    Namespaces  cgroups  Containers  │
│   (process  (fork/   (job      (task_   (isolation) (limits) (Docker,    │
│    concept)  exec)   control)   struct)                       K8s)       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Process Data Structures

The kernel maintains several data structures to represent and manage processes. In traditional Unix (as described by Bach), these are primarily the **process table** and the **u-area**.

### The Process Table

The process table is an array of **process table entries** (also called **proc structures**), one for each process in the system. This table resides in kernel memory and is always accessible to the kernel.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE PROCESS TABLE                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The process table is a fixed-size array in kernel memory:               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     KERNEL MEMORY                                    │ │
│   │                                                                      │ │
│   │   process_table[NPROC]                                              │ │
│   │   ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐    │ │
│   │   │ proc[0] │ proc[1] │ proc[2] │ proc[3] │   ...   │proc[N-1]│    │ │
│   │   │ (init)  │ (shell) │ (user)  │ (free)  │         │         │    │ │
│   │   └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘    │ │
│   │       │                                                              │ │
│   │       ▼                                                              │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │              struct proc (Process Table Entry)               │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │                                                              │   │ │
│   │   │   p_stat      - Process state (SRUN, SSLEEP, SZOMB, etc.)   │   │ │
│   │   │   p_flag      - Flags (SLOAD, SSYS, STRC, etc.)             │   │ │
│   │   │   p_pri       - Scheduling priority                          │   │ │
│   │   │   p_sig       - Pending signals (bitmask)                    │   │ │
│   │   │   p_uid       - Real user ID                                 │   │ │
│   │   │   p_suid      - Saved set-user-ID                            │   │ │
│   │   │   p_pid       - Process ID                                   │   │ │
│   │   │   p_ppid      - Parent process ID                            │   │ │
│   │   │   p_pgrp      - Process group ID                             │   │ │
│   │   │   p_cpu       - CPU usage (for scheduling)                   │   │ │
│   │   │   p_nice      - Nice value (-20 to +19)                      │   │ │
│   │   │   p_wchan     - Wait channel (sleep address)                 │   │ │
│   │   │   p_textp     - Pointer to text structure                    │   │ │
│   │   │   p_addr      - Address of u-area (swappable)                │   │ │
│   │   │   p_size      - Size of swappable image                      │   │ │
│   │   │   p_time      - Resident time (for swapper)                  │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY CHARACTERISTICS:                                                    │
│   ────────────────────                                                     │
│   • Always in memory (never swapped out)                                  │
│   • Accessible even when process is not running                           │
│   • Contains information needed by scheduler                              │
│   • Fixed size, determined at system configuration                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### The U-Area (User Area)

The **u-area** (or **user area**) contains process information that is only needed when the process is running. Unlike the process table entry, the u-area can be swapped out to disk when the process is not in memory.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE U-AREA (USER AREA)                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The u-area is part of the process's swappable image:                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │              struct user (U-Area Contents)                           │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                      │ │
│   │   PROCESS IDENTIFICATION:                                           │ │
│   │   ───────────────────────                                            │ │
│   │   u_uid       - Effective user ID                                   │ │
│   │   u_gid       - Effective group ID                                  │ │
│   │   u_ruid      - Real user ID                                        │ │
│   │   u_rgid      - Real group ID                                       │ │
│   │                                                                      │ │
│   │   FILE SYSTEM CONTEXT:                                              │ │
│   │   ────────────────────                                               │ │
│   │   u_ofile[]   - Open file descriptor table                          │ │
│   │   u_pofile[]  - Per-fd flags (close-on-exec)                        │ │
│   │   u_cdir      - Current directory (inode pointer)                   │ │
│   │   u_rdir      - Root directory (for chroot)                         │ │
│   │   u_cmask     - File creation mask (umask)                          │ │
│   │                                                                      │ │
│   │   EXECUTION STATE:                                                  │ │
│   │   ────────────────                                                   │ │
│   │   u_procp     - Pointer back to proc table entry                    │ │
│   │   u_ar0       - Pointer to saved registers                          │ │
│   │   u_base      - Base address for I/O                                │ │
│   │   u_count     - Bytes remaining for I/O                             │ │
│   │   u_offset    - File offset for I/O                                 │ │
│   │   u_error     - Error code from last system call                    │ │
│   │   u_rval1     - Return value from system call                       │ │
│   │                                                                      │ │
│   │   SIGNAL HANDLING:                                                  │ │
│   │   ────────────────                                                   │ │
│   │   u_signal[]  - Signal disposition array                            │ │
│   │   u_sigmask[] - Signal masks for each handler                       │ │
│   │                                                                      │ │
│   │   RESOURCE LIMITS:                                                  │ │
│   │   ────────────────                                                   │ │
│   │   u_rlimit[]  - Resource limits (CPU, memory, files, etc.)          │ │
│   │                                                                      │ │
│   │   TIMING:                                                           │ │
│   │   ───────                                                            │ │
│   │   u_utime     - User CPU time                                       │ │
│   │   u_stime     - System CPU time                                     │ │
│   │   u_cutime    - Children's user time                                │ │
│   │   u_cstime    - Children's system time                              │ │
│   │                                                                      │ │
│   │   KERNEL STACK:                                                     │ │
│   │   ─────────────                                                      │ │
│   │   u_stack[]   - Kernel stack for this process                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY CHARACTERISTICS:                                                    │
│   ────────────────────                                                     │
│   • Can be swapped out when process is not running                        │
│   • Contains information only needed during execution                     │
│   • Includes the kernel stack for this process                            │
│   • Accessed via the "u" variable when process is running                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Process Table Entry vs U-Area

Why split process information between two structures? The answer lies in memory management and swapping:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROC TABLE vs U-AREA: WHY TWO STRUCTURES?              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE DESIGN RATIONALE:                                                   │
│   ─────────────────────                                                    │
│                                                                            │
│   In early Unix, memory was scarce. The kernel needed to:                 │
│   1. Keep some process info always in memory (for scheduling)             │
│   2. Allow other info to be swapped out (to save memory)                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ALWAYS IN MEMORY              CAN BE SWAPPED OUT                  │ │
│   │   (Process Table Entry)         (U-Area + Data + Stack)             │ │
│   │                                                                      │ │
│   │   ┌─────────────────┐          ┌─────────────────────────────────┐ │ │
│   │   │                 │          │                                  │ │ │
│   │   │  • PID          │          │  • Open file table              │ │ │
│   │   │  • State        │          │  • Current directory            │ │ │
│   │   │  • Priority     │          │  • Signal handlers              │ │ │
│   │   │  • Signals      │          │  • Resource limits              │ │ │
│   │   │  • UID          │          │  • Kernel stack                 │ │ │
│   │   │  • Wait channel │          │  • CPU times                    │ │ │
│   │   │  • Pointers     │          │  • I/O parameters               │ │ │
│   │   │                 │          │                                  │ │ │
│   │   └─────────────────┘          └─────────────────────────────────┘ │ │
│   │          │                                    │                     │ │
│   │          │                                    │                     │ │
│   │          ▼                                    ▼                     │ │
│   │   Needed by scheduler            Only needed when process          │ │
│   │   even when process              is actually running               │ │
│   │   is swapped out                                                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE SCENARIO:                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   System has 10 processes, but only 3 can fit in memory:                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   MEMORY:                                                           │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │  Process Table (all 10 entries - always resident)           │  │ │
│   │   │  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐       │  │ │
│   │   │  │ P0 │ P1 │ P2 │ P3 │ P4 │ P5 │ P6 │ P7 │ P8 │ P9 │       │  │ │
│   │   │  └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘       │  │ │
│   │   │                                                              │  │ │
│   │   │  U-Areas + Process Images (only 3 in memory):               │  │ │
│   │   │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │  │ │
│   │   │  │ P0: u-area   │ │ P3: u-area   │ │ P7: u-area   │        │  │ │
│   │   │  │     text     │ │     text     │ │     text     │        │  │ │
│   │   │  │     data     │ │     data     │ │     data     │        │  │ │
│   │   │  │     stack    │ │     stack    │ │     stack    │        │  │ │
│   │   │  └──────────────┘ └──────────────┘ └──────────────┘        │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   │   SWAP SPACE:                                                       │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │  P1, P2, P4, P5, P6, P8, P9: u-areas + images              │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   The scheduler can examine ALL process table entries to decide           │
│   which process to run next, then swap in that process's u-area.         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Task Structure (Modern Linux)

Modern Linux combines the process table entry and u-area into a single structure called `task_struct`. This is the most important data structure in the Linux kernel:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX task_struct                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   In Linux, task_struct contains ALL process information:                 │
│                                                                            │
│   struct task_struct {                                                    │
│       /* Scheduler state */                                               │
│       volatile long state;           /* -1 unrunnable, 0 runnable, >0 stopped */
│       void *stack;                   /* Kernel stack pointer */           │
│       unsigned int flags;            /* Per-process flags */              │
│       int prio, static_prio;         /* Priority values */                │
│       struct sched_entity se;        /* Scheduler entity */               │
│                                                                            │
│       /* Process identification */                                        │
│       pid_t pid;                     /* Process ID */                     │
│       pid_t tgid;                    /* Thread group ID */                │
│                                                                            │
│       /* Process relationships */                                         │
│       struct task_struct *parent;    /* Parent process */                 │
│       struct list_head children;     /* List of children */               │
│       struct list_head sibling;      /* Linkage in parent's children */   │
│                                                                            │
│       /* Credentials */                                                   │
│       const struct cred *cred;       /* Effective credentials */          │
│       const struct cred *real_cred;  /* Objective credentials */          │
│                                                                            │
│       /* File system info */                                              │
│       struct fs_struct *fs;          /* Filesystem info (cwd, root) */    │
│       struct files_struct *files;    /* Open file table */                │
│                                                                            │
│       /* Signal handling */                                               │
│       struct signal_struct *signal;  /* Signal handlers */                │
│       struct sighand_struct *sighand;/* Signal handler functions */       │
│       sigset_t blocked;              /* Blocked signals */                │
│       struct sigpending pending;     /* Pending signals */                │
│                                                                            │
│       /* Memory management */                                             │
│       struct mm_struct *mm;          /* Memory descriptor */              │
│       struct mm_struct *active_mm;   /* Active memory descriptor */       │
│                                                                            │
│       /* Namespaces */                                                    │
│       struct nsproxy *nsproxy;       /* Namespace proxy */                │
│                                                                            │
│       /* ... many more fields ... */                                      │
│   };                                                                       │
│                                                                            │
│   SIZE: task_struct is large (~6KB on 64-bit systems)                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION: TRADITIONAL UNIX → LINUX                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TRADITIONAL UNIX (Bach):              MODERN LINUX:                     │
│   ────────────────────────              ─────────────                      │
│                                                                            │
│   ┌─────────────────────┐              ┌─────────────────────────────┐   │
│   │   Process Table     │              │                              │   │
│   │   ┌───────────────┐ │              │       task_struct           │   │
│   │   │ struct proc   │ │              │                              │   │
│   │   │  (always in   │ │              │  ┌─────────────────────────┐│   │
│   │   │   memory)     │ │              │  │ All process info in    ││   │
│   │   └───────┬───────┘ │              │  │ one structure          ││   │
│   │           │         │              │  │                         ││   │
│   │           │ p_addr  │              │  │ • State & scheduling   ││   │
│   │           ▼         │              │  │ • PIDs & relationships ││   │
│   │   ┌───────────────┐ │              │  │ • Credentials          ││   │
│   │   │   U-Area      │ │              │  │ • Files (via pointer)  ││   │
│   │   │  (swappable)  │ │              │  │ • Memory (via pointer) ││   │
│   │   │               │ │              │  │ • Signals              ││   │
│   │   │ • Files       │ │      ═══►    │  │ • Namespaces           ││   │
│   │   │ • Signals     │ │              │  │ • cgroups              ││   │
│   │   │ • Limits      │ │              │  │                         ││   │
│   │   │ • Kernel stack│ │              │  └─────────────────────────┘│   │
│   │   └───────────────┘ │              │                              │   │
│   └─────────────────────┘              │  Kernel stack is separate   │   │
│                                         │  (THREAD_SIZE, usually 16KB)│   │
│                                         └─────────────────────────────┘   │
│                                                                            │
│   WHY THE CHANGE?                                                         │
│   ───────────────                                                          │
│   • Modern systems have abundant RAM (no need for swapping u-area)        │
│   • Demand paging replaced whole-process swapping                         │
│   • Simpler code with single structure                                    │
│   • Better cache locality                                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Process Memory Layout

A process's memory is organized into distinct **regions** (also called **segments**). Each region has specific characteristics and purposes.

### Regions and the Region Table

In traditional Unix, the kernel maintains a **region table** that describes all memory regions in the system. Each process has a **per-process region table** that maps virtual addresses to regions.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS MEMORY REGIONS                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A process's virtual address space is divided into regions:              │
│                                                                            │
│   HIGH MEMORY                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   0xFFFFFFFF  ┌─────────────────────────────────────────────────┐   │ │
│   │   (or higher  │                                                  │   │ │
│   │    on 64-bit) │              KERNEL SPACE                        │   │ │
│   │               │         (not accessible to process)              │   │ │
│   │               │                                                  │   │ │
│   │   ────────────├─────────────────────────────────────────────────┤   │ │
│   │               │                                                  │   │ │
│   │               │              STACK                               │   │ │
│   │               │         (grows downward ↓)                       │   │ │
│   │               │                                                  │   │ │
│   │               │   • Local variables                              │   │ │
│   │               │   • Function parameters                          │   │ │
│   │               │   • Return addresses                             │   │ │
│   │               │                                                  │   │ │
│   │               ├─────────────────────────────────────────────────┤   │ │
│   │               │              ↓ ↓ ↓                               │   │ │
│   │               │                                                  │   │ │
│   │               │         (unmapped region)                        │   │ │
│   │               │                                                  │   │ │
│   │               │              ↑ ↑ ↑                               │   │ │
│   │               ├─────────────────────────────────────────────────┤   │ │
│   │               │                                                  │   │ │
│   │               │              HEAP                                │   │ │
│   │               │         (grows upward ↑)                         │   │ │
│   │               │                                                  │   │ │
│   │               │   • malloc()'d memory                            │   │ │
│   │               │   • Dynamic allocations                          │   │ │
│   │               │                                                  │   │ │
│   │               ├─────────────────────────────────────────────────┤   │ │
│   │               │              BSS                                 │   │ │
│   │               │   • Uninitialized global variables               │   │ │
│   │               │   • Zero-filled on program start                 │   │ │
│   │               ├─────────────────────────────────────────────────┤   │ │
│   │               │              DATA                                │   │ │
│   │               │   • Initialized global variables                 │   │ │
│   │               │   • Static variables                             │   │ │
│   │               ├─────────────────────────────────────────────────┤   │ │
│   │               │              TEXT                                │   │ │
│   │               │   • Program code (machine instructions)          │   │ │
│   │               │   • Read-only, executable                        │   │ │
│   │               │   • Shareable between processes                  │   │ │
│   │   0x00000000  └─────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│   LOW MEMORY                                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```




### Text Region

The **text region** contains the executable code of the program. It has special properties that enable sharing and protection:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TEXT REGION (CODE SEGMENT)                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CHARACTERISTICS:                                                        │
│   ────────────────                                                         │
│   • Read-only (cannot be modified by the process)                         │
│   • Executable (CPU can fetch and execute instructions)                   │
│   • Shareable (multiple processes can share same physical pages)          │
│   • Fixed size (determined at compile/link time)                          │
│                                                                            │
│   TEXT SHARING:                                                           │
│   ─────────────                                                            │
│                                                                            │
│   When multiple processes run the same program, they share the text:      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A              Process B              Process C           │ │
│   │   (running /bin/ls)      (running /bin/ls)      (running /bin/ls)   │ │
│   │                                                                      │ │
│   │   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐    │ │
│   │   │ Virtual     │        │ Virtual     │        │ Virtual     │    │ │
│   │   │ Address     │        │ Address     │        │ Address     │    │ │
│   │   │ Space       │        │ Space       │        │ Space       │    │ │
│   │   │             │        │             │        │             │    │ │
│   │   │ ┌─────────┐ │        │ ┌─────────┐ │        │ ┌─────────┐ │    │ │
│   │   │ │  TEXT   │─┼────────┼─┤  TEXT   │─┼────────┼─┤  TEXT   │ │    │ │
│   │   │ └─────────┘ │        │ └─────────┘ │        │ └─────────┘ │    │ │
│   │   │      │      │        │      │      │        │      │      │    │ │
│   │   │ ┌─────────┐ │        │ ┌─────────┐ │        │ ┌─────────┐ │    │ │
│   │   │ │  DATA   │ │        │ │  DATA   │ │        │ │  DATA   │ │    │ │
│   │   │ │(private)│ │        │ │(private)│ │        │ │(private)│ │    │ │
│   │   │ └─────────┘ │        │ └─────────┘ │        │ └─────────┘ │    │ │
│   │   │ ┌─────────┐ │        │ ┌─────────┐ │        │ ┌─────────┐ │    │ │
│   │   │ │  STACK  │ │        │ │  STACK  │ │        │ │  STACK  │ │    │ │
│   │   │ │(private)│ │        │ │(private)│ │        │ │(private)│ │    │ │
│   │   │ └─────────┘ │        │ └─────────┘ │        │ └─────────┘ │    │ │
│   │   └─────────────┘        └─────────────┘        └─────────────┘    │ │
│   │          │                      │                      │           │ │
│   │          └──────────────────────┼──────────────────────┘           │ │
│   │                                 │                                   │ │
│   │                                 ▼                                   │ │
│   │                    ┌─────────────────────────┐                     │ │
│   │                    │   PHYSICAL MEMORY       │                     │ │
│   │                    │                         │                     │ │
│   │                    │   ┌─────────────────┐   │                     │ │
│   │                    │   │  /bin/ls TEXT   │   │  ◄── ONE COPY      │ │
│   │                    │   │  (shared)       │   │      IN MEMORY     │ │
│   │                    │   └─────────────────┘   │                     │ │
│   │                    │                         │                     │ │
│   │                    └─────────────────────────┘                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MEMORY SAVINGS:                                                         │
│   ───────────────                                                          │
│   If /bin/ls is 100KB and 100 users run it:                               │
│   • Without sharing: 100 × 100KB = 10MB                                   │
│   • With sharing:    1 × 100KB = 100KB (text) + private data/stack        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Data Region

The **data region** contains the process's global and static variables:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DATA REGION                                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The data region is divided into sub-sections:                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                         HEAP                                 │   │ │
│   │   │                    (grows upward ↑)                          │   │ │
│   │   │                                                              │   │ │
│   │   │   • Dynamically allocated memory (malloc, new)               │   │ │
│   │   │   • Managed by brk()/sbrk() system calls                     │   │ │
│   │   │   • Or mmap() for large allocations                          │   │ │
│   │   │                                                              │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │                         BSS                                  │   │ │
│   │   │              (Block Started by Symbol)                       │   │ │
│   │   │                                                              │   │ │
│   │   │   • Uninitialized global/static variables                    │   │ │
│   │   │   • Zero-filled by kernel on exec()                          │   │ │
│   │   │   • NOT stored in executable file (saves space)              │   │ │
│   │   │                                                              │   │ │
│   │   │   Example:                                                   │   │ │
│   │   │     int large_array[1000000];  /* 4MB, but 0 bytes in file */│   │ │
│   │   │                                                              │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │                    INITIALIZED DATA                          │   │ │
│   │   │                                                              │   │ │
│   │   │   • Global variables with initial values                     │   │ │
│   │   │   • Static variables with initial values                     │   │ │
│   │   │   • Stored in executable file                                │   │ │
│   │   │                                                              │   │ │
│   │   │   Example:                                                   │   │ │
│   │   │     int counter = 42;                                        │   │ │
│   │   │     char *message = "Hello";                                 │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CHARACTERISTICS:                                                        │
│   ────────────────                                                         │
│   • Read-write (process can modify)                                       │
│   • Not executable (on modern systems with NX bit)                        │
│   • Private to each process (not shared)                                  │
│   • Copy-on-write after fork()                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Stack Region

The **stack region** is used for function calls, local variables, and control flow:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    STACK REGION                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The stack grows DOWNWARD (toward lower addresses):                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   HIGH ADDRESS                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                    STACK BASE                                │   │ │
│   │   │   (set by kernel at exec() time)                             │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │   Environment variables (envp[])                             │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │   Command-line arguments (argv[])                            │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │   argc                                                       │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │                                                              │   │ │
│   │   │   main()'s stack frame                                       │   │ │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │ │
│   │   │   │ Return address                                       │   │   │ │
│   │   │   │ Saved frame pointer                                  │   │   │ │
│   │   │   │ Local variables                                      │   │   │ │
│   │   │   └─────────────────────────────────────────────────────┘   │   │ │
│   │   │                                                              │   │ │
│   │   │   func1()'s stack frame                                      │   │ │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │ │
│   │   │   │ Return address (back to main)                        │   │   │ │
│   │   │   │ Saved frame pointer                                  │   │   │ │
│   │   │   │ Local variables                                      │   │   │ │
│   │   │   │ Function arguments                                   │   │   │ │
│   │   │   └─────────────────────────────────────────────────────┘   │   │ │
│   │   │                                                              │   │ │
│   │   │   func2()'s stack frame                                      │   │ │
│   │   │   ┌─────────────────────────────────────────────────────┐   │   │ │
│   │   │   │ Return address (back to func1)                       │   │   │ │
│   │   │   │ Saved frame pointer                                  │   │   │ │
│   │   │   │ Local variables                                      │   │   │ │
│   │   │   └─────────────────────────────────────────────────────┘   │   │ │
│   │   │                         │                                    │   │ │
│   │   │                         ▼                                    │   │ │
│   │   │                    (grows down)                              │   │ │
│   │   │                                                              │   │ │
│   │   │   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─    │   │ │
│   │   │                    STACK LIMIT                               │   │ │
│   │   │              (ulimit -s, typically 8MB)                      │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │   LOW ADDRESS                                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STACK FRAME CONTENTS:                                                   │
│   ─────────────────────                                                    │
│   • Return address (where to continue after function returns)             │
│   • Saved frame pointer (previous stack frame base)                       │
│   • Local variables                                                       │
│   • Function arguments (some passed in registers on modern ABIs)          │
│   • Saved registers (callee-saved registers)                              │
│                                                                            │
│   STACK OVERFLOW:                                                         │
│   ───────────────                                                          │
│   If stack grows beyond limit → SIGSEGV (segmentation fault)              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### The Per-Process Region Table

Each process has a **per-process region table** (pregion table) that connects virtual addresses to regions:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PER-PROCESS REGION TABLE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The pregion table maps virtual addresses to region table entries:       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   PROCESS                              SYSTEM                       │ │
│   │   ───────                              ──────                        │ │
│   │                                                                      │ │
│   │   ┌─────────────────┐                  ┌─────────────────────┐      │ │
│   │   │   proc table    │                  │    Region Table     │      │ │
│   │   │   entry         │                  │                     │      │ │
│   │   │                 │                  │  ┌───────────────┐  │      │ │
│   │   │  p_region ──────┼──┐               │  │ Region 0      │  │      │ │
│   │   │                 │  │               │  │ (text)        │  │      │ │
│   │   └─────────────────┘  │               │  │ r_refcnt: 3   │◄─┼──┐   │ │
│   │                        │               │  │ r_size: 100KB │  │  │   │ │
│   │                        ▼               │  │ r_iptr: ...   │  │  │   │ │
│   │   ┌─────────────────────────────┐      │  └───────────────┘  │  │   │ │
│   │   │   Per-Process Region Table  │      │                     │  │   │ │
│   │   │   (pregion)                 │      │  ┌───────────────┐  │  │   │ │
│   │   │                             │      │  │ Region 1      │  │  │   │ │
│   │   │  ┌──────────────────────┐   │      │  │ (data)        │  │  │   │ │
│   │   │  │ entry 0: TEXT       │───┼──────────┼─► r_refcnt: 1 │  │  │   │ │
│   │   │  │  p_regva: 0x0       │   │      │  │ r_size: 50KB  │  │  │   │ │
│   │   │  │  p_type: PT_TEXT    │   │      │  └───────────────┘  │  │   │ │
│   │   │  └──────────────────────┘   │      │                     │  │   │ │
│   │   │  ┌──────────────────────┐   │      │  ┌───────────────┐  │  │   │ │
│   │   │  │ entry 1: DATA       │───┼──────────┼─► Region 2    │  │  │   │ │
│   │   │  │  p_regva: 0x100000  │   │      │  │ (stack)       │  │  │   │ │
│   │   │  │  p_type: PT_DATA    │   │      │  │ r_refcnt: 1   │  │  │   │ │
│   │   │  └──────────────────────┘   │      │  │ r_size: 8KB   │  │  │   │ │
│   │   │  ┌──────────────────────┐   │      │  └───────────────┘  │  │   │ │
│   │   │  │ entry 2: STACK      │───┼──────────┼─► ...           │  │   │ │
│   │   │  │  p_regva: 0x7FFF... │   │      │  │                  │  │   │ │
│   │   │  │  p_type: PT_STACK   │   │      │  └──────────────────┘  │   │ │
│   │   │  └──────────────────────┘   │      │                        │   │ │
│   │   │                             │      └────────────────────────┘   │ │
│   │   └─────────────────────────────┘                                   │ │
│   │                                                                      │ │
│   │   The text region has r_refcnt=3 because 3 processes share it       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Process Context

The **process context** is all the information the kernel needs to run a process. Bach divides this into three parts:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE THREE PARTS OF PROCESS CONTEXT                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. USER-LEVEL CONTEXT                                             │ │
│   │      ───────────────────                                             │ │
│   │      • Text (code)                                                   │ │
│   │      • Data (global variables)                                       │ │
│   │      • User stack                                                    │ │
│   │      • Shared memory regions                                         │ │
│   │                                                                      │ │
│   │   2. REGISTER CONTEXT                                                │ │
│   │      ────────────────                                                │ │
│   │      • Program Counter (PC) - next instruction                       │ │
│   │      • Stack Pointer (SP) - top of stack                             │ │
│   │      • Processor Status Word (PSW) - flags, mode                     │ │
│   │      • General-purpose registers                                     │ │
│   │      • Floating-point registers                                      │ │
│   │                                                                      │ │
│   │   3. SYSTEM-LEVEL CONTEXT                                            │ │
│   │      ─────────────────────                                           │ │
│   │      • Process table entry (struct proc)                             │ │
│   │      • U-area (struct user)                                          │ │
│   │      • Per-process region table                                      │ │
│   │      • Kernel stack                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### User-Level Context

The user-level context is the process's memory as seen from user space:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    USER-LEVEL CONTEXT                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   This is the process's view of its own address space:                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   COMPONENT          DESCRIPTION                                    │ │
│   │   ─────────          ───────────                                    │ │
│   │                                                                      │ │
│   │   Text region        Machine code instructions                      │ │
│   │                      Read-only, possibly shared                     │ │
│   │                                                                      │ │
│   │   Data region        Global/static variables (initialized + BSS)    │ │
│   │                      Read-write, private                            │ │
│   │                                                                      │ │
│   │   Heap               malloc()'d memory                              │ │
│   │                      Dynamic, grows upward                          │ │
│   │                                                                      │ │
│   │   User stack         Local variables, function calls                │ │
│   │                      Dynamic, grows downward                        │ │
│   │                                                                      │ │
│   │   Shared memory      System V or POSIX shared memory                │ │
│   │                      Mapped into address space                      │ │
│   │                                                                      │ │
│   │   Memory-mapped      mmap()'d files or anonymous memory            │ │
│   │   regions            Can be anywhere in address space               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Register Context

The register context contains the CPU state needed to resume execution:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REGISTER CONTEXT                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When a process is not running, its registers are saved:                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   REGISTER           PURPOSE                                        │ │
│   │   ────────           ───────                                         │ │
│   │                                                                      │ │
│   │   Program Counter    Address of next instruction to execute         │ │
│   │   (PC/IP/RIP)        "Where am I in the code?"                      │ │
│   │                                                                      │ │
│   │   Stack Pointer      Top of the stack                               │ │
│   │   (SP/RSP)           "Where is my stack?"                           │ │
│   │                                                                      │ │
│   │   Frame Pointer      Base of current stack frame                    │ │
│   │   (FP/RBP)           "Where does this function's data start?"       │ │
│   │                                                                      │ │
│   │   Processor Status   Condition codes, interrupt enable, mode        │ │
│   │   Word (PSW/FLAGS)   "Am I in user mode or kernel mode?"            │ │
│   │                                                                      │ │
│   │   General Purpose    RAX, RBX, RCX, RDX, RSI, RDI, R8-R15 (x86-64) │ │
│   │   Registers          Computation, function arguments                │ │
│   │                                                                      │ │
│   │   Floating Point     XMM0-XMM15, FPU stack                          │ │
│   │   Registers          Floating-point and SIMD operations             │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHERE ARE REGISTERS SAVED?                                              │
│   ───────────────────────────                                              │
│   In traditional Unix: saved in u-area (u.u_ar0 points to saved regs)    │
│   In modern Linux: saved on kernel stack or thread_struct                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### System-Level Context

The system-level context is what the kernel maintains for each process:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM-LEVEL CONTEXT                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   COMPONENT             CONTENTS                                    │ │
│   │   ─────────             ────────                                    │ │
│   │                                                                      │ │
│   │   Process table entry   State, priority, PIDs, signals, pointers   │ │
│   │   (struct proc)         Always in memory, accessed by scheduler    │ │
│   │                                                                      │ │
│   │   U-Area                Open files, signal handlers, limits        │ │
│   │   (struct user)         Current directory, accounting info         │ │
│   │                                                                      │ │
│   │   Per-process           Maps virtual addresses to regions          │ │
│   │   region table          Text, data, stack, shared memory           │ │
│   │                                                                      │ │
│   │   Kernel stack          Used when process is in kernel mode        │ │
│   │                         System call execution, interrupt handling   │ │
│   │                         Separate from user stack for security      │ │
│   │                                                                      │ │
│   │   Context layers        Stack of saved contexts for nested calls   │ │
│   │                         Each system call/interrupt adds a layer    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONTEXT LAYERS (Bach's concept):                                        │
│   ─────────────────────────────────                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Kernel Stack of Process                                           │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ Layer 0: User-level context                                  │   │ │
│   │   │          (process running in user mode)                      │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │ Layer 1: System call (e.g., read())                          │   │ │
│   │   │          Saved user registers, in kernel mode                │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │ Layer 2: Interrupt during syscall (e.g., disk interrupt)     │   │ │
│   │   │          Saved syscall context, handling interrupt           │   │ │
│   │   ├─────────────────────────────────────────────────────────────┤   │ │
│   │   │ Layer 3: Another interrupt (e.g., clock tick)                │   │ │
│   │   │          Nested interrupt handling                           │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │   Each layer saves the context of the previous layer               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Context Switching

A **context switch** occurs when the kernel stops running one process and starts running another:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT SWITCH                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHEN DOES A CONTEXT SWITCH HAPPEN?                                      │
│   ───────────────────────────────────                                      │
│   • Process blocks (e.g., waiting for I/O)                                │
│   • Process voluntarily yields (sleep, pause)                             │
│   • Time slice expires (preemption)                                       │
│   • Higher priority process becomes runnable                              │
│   • Process terminates                                                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   THE CONTEXT SWITCH ALGORITHM (simplified):                        │ │
│   │   ──────────────────────────────────────────                        │ │
│   │                                                                      │ │
│   │   algorithm context_switch                                          │ │
│   │   input:  none (implicit: current process, selected next process)   │ │
│   │   output: none (execution continues in new process)                 │ │
│   │   {                                                                  │ │
│   │       /* Step 1: Save current process state */                      │ │
│   │       save all general-purpose registers to kernel stack;           │ │
│   │       save stack pointer in process table entry;                    │ │
│   │       save program counter (return address);                        │ │
│   │                                                                      │ │
│   │       /* Step 2: Select next process to run */                      │ │
│   │       next = scheduler();  /* pick highest priority runnable */     │ │
│   │                                                                      │ │
│   │       /* Step 3: Switch address space */                            │ │
│   │       if (current->mm != next->mm)                                  │ │
│   │       {                                                              │ │
│   │           load new page table base register (CR3 on x86);           │ │
│   │           flush TLB (or use ASID/PCID);                             │ │
│   │       }                                                              │ │
│   │                                                                      │ │
│   │       /* Step 4: Switch kernel stack */                             │ │
│   │       switch stack pointer to next process's kernel stack;          │ │
│   │                                                                      │ │
│   │       /* Step 5: Restore next process state */                      │ │
│   │       restore registers from next process's kernel stack;           │ │
│   │       return; /* returns to where next process left off */          │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONTEXT SWITCH VISUALIZATION:                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   Process A (running)                    Process B (ready)                │
│   ─────────────────────                  ───────────────────               │
│                                                                            │
│   Time ─────────────────────────────────────────────────────────────────► │
│                                                                            │
│   │ Process A │                         │ Process B │                     │
│   │ executing │                         │ (waiting) │                     │
│   │           │                         │           │                     │
│   │           ▼                         │           │                     │
│   │   ┌───────────────┐                 │           │                     │
│   │   │ SAVE A's      │                 │           │                     │
│   │   │ registers     │                 │           │                     │
│   │   │ to A's stack  │                 │           │                     │
│   │   └───────┬───────┘                 │           │                     │
│   │           │                         │           │                     │
│   │           ▼                         │           │                     │
│   │   ┌───────────────┐                 │           │                     │
│   │   │ Switch page   │                 │           │                     │
│   │   │ tables        │                 │           │                     │
│   │   │ (A→B)         │                 │           │                     │
│   │   └───────┬───────┘                 │           │                     │
│   │           │                         │           │                     │
│   │           ▼                         ▼           │                     │
│   │   ┌───────────────┐         ┌───────────────┐   │                     │
│   │   │ Switch kernel │ ──────► │ RESTORE B's   │   │                     │
│   │   │ stack (A→B)   │         │ registers     │   │                     │
│   │   └───────────────┘         │ from B's stack│   │                     │
│   │                             └───────┬───────┘   │                     │
│   │                                     │           │                     │
│   │                                     ▼           ▼                     │
│   │                             │ Process B │                             │
│   │                             │ executing │                             │
│   │                             │           │                             │
│                                                                            │
│   CONTEXT SWITCH COST:                                                    │
│   ────────────────────                                                     │
│   • Direct cost: ~1-10 microseconds (save/restore registers)              │
│   • Indirect cost: TLB flush, cache pollution (can be much larger)        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Process States

A process moves through various **states** during its lifetime. Bach defines several states:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS STATES (Traditional Unix)                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Bach defines these process states:                                      │
│                                                                            │
│   STATE              VALUE     MEANING                                    │
│   ─────              ─────     ───────                                    │
│   SIDL               1         Process is being created (fork)           │
│   SRUN               2         Process is runnable (ready to run)        │
│   SSLEEP             3         Process is sleeping (waiting for event)   │
│   SSTOP              4         Process is stopped (job control)          │
│   SZOMB              5         Process is zombie (terminated, not reaped)│
│                                                                            │
│   Additional states in some systems:                                      │
│   SONPROC            6         Process is currently running on CPU       │
│   SWAIT              7         Process waiting for CPU after interrupt   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Process State Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS STATE TRANSITIONS                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │                          fork()                                     │ │
│   │                            │                                         │ │
│   │                            ▼                                         │ │
│   │                     ┌─────────────┐                                  │ │
│   │                     │    SIDL     │                                  │ │
│   │                     │  (created)  │                                  │ │
│   │                     └──────┬──────┘                                  │ │
│   │                            │ enough memory                           │ │
│   │                            ▼                                         │ │
│   │                     ┌─────────────┐                                  │ │
│   │    ┌───────────────►│    SRUN     │◄────────────────┐               │ │
│   │    │  wakeup()      │  (runnable) │   preemption    │               │ │
│   │    │                └──────┬──────┘                 │               │ │
│   │    │                       │                        │               │ │
│   │    │                       │ scheduled              │               │ │
│   │    │                       ▼                        │               │ │
│   │    │                ┌─────────────┐                 │               │ │
│   │    │                │  RUNNING    │─────────────────┘               │ │
│   │    │                │  (on CPU)   │   time slice expired            │ │
│   │    │                └──────┬──────┘                                  │ │
│   │    │                       │                                         │ │
│   │    │          ┌────────────┼────────────┐                           │ │
│   │    │          │            │            │                           │ │
│   │    │          ▼            ▼            ▼                           │ │
│   │    │    ┌──────────┐ ┌──────────┐ ┌──────────┐                      │ │
│   │    │    │  SSLEEP  │ │  SSTOP   │ │  exit()  │                      │ │
│   │    │    │(sleeping)│ │(stopped) │ │          │                      │ │
│   │    │    └────┬─────┘ └────┬─────┘ │          │                      │ │
│   │    │         │            │       ▼          │                      │ │
│   │    └─────────┘            │ ┌──────────┐     │                      │ │
│   │        event              │ │  SZOMB   │     │                      │ │
│   │        occurs             │ │ (zombie) │◄────┘                      │ │
│   │                           │ └────┬─────┘                            │ │
│   │                           │      │                                   │ │
│   │            SIGCONT        │      │ parent calls wait()              │ │
│   │           ┌───────────────┘      │                                   │ │
│   │           │                      ▼                                   │ │
│   │           │               ┌──────────┐                               │ │
│   │           └───────────────► REMOVED  │                               │ │
│   │                           │ from     │                               │ │
│   │                           │ system   │                               │ │
│   │                           └──────────┘                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LINUX TASK STATES (for comparison):                                     │
│   ───────────────────────────────────                                      │
│   TASK_RUNNING         - Runnable or actually running                     │
│   TASK_INTERRUPTIBLE   - Sleeping, can be woken by signals               │
│   TASK_UNINTERRUPTIBLE - Sleeping, cannot be interrupted                  │
│   __TASK_STOPPED       - Stopped by signal                                │
│   __TASK_TRACED        - Being traced (debugged)                          │
│   EXIT_ZOMBIE          - Terminated, waiting for parent                   │
│   EXIT_DEAD            - Final state before removal                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Sleep and Wakeup

Processes **sleep** when waiting for events and are **woken up** when events occur:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SLEEP AND WAKEUP MECHANISM                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SLEEP (process voluntarily gives up CPU):                               │
│   ─────────────────────────────────────────                                │
│                                                                            │
│   algorithm sleep(event, priority)                                        │
│   {                                                                        │
│       raise processor priority to block interrupts;                       │
│       set process state to SSLEEP;                                        │
│       set p_wchan = event;  /* what we're waiting for */                  │
│       set p_pri = priority;                                               │
│                                                                            │
│       if (priority > PZERO)  /* interruptible sleep */                    │
│       {                                                                    │
│           if (signal pending)                                             │
│           {                                                                │
│               restore state to SRUN;                                      │
│               return;  /* don't sleep, handle signal */                   │
│           }                                                                │
│       }                                                                    │
│                                                                            │
│       call context_switch();  /* switch to another process */             │
│       /* we return here when woken up */                                  │
│       restore processor priority;                                         │
│   }                                                                        │
│                                                                            │
│   WAKEUP (makes sleeping processes runnable):                             │
│   ───────────────────────────────────────────                              │
│                                                                            │
│   algorithm wakeup(event)                                                 │
│   {                                                                        │
│       raise processor priority to block interrupts;                       │
│       for each process p in process table:                                │
│       {                                                                    │
│           if (p->p_stat == SSLEEP && p->p_wchan == event)                │
│           {                                                                │
│               p->p_stat = SRUN;      /* make runnable */                 │
│               p->p_wchan = NULL;     /* not waiting anymore */           │
│               add p to run queue;                                         │
│           }                                                                │
│       }                                                                    │
│       restore processor priority;                                         │
│   }                                                                        │
│                                                                            │
│   VISUALIZATION:                                                          │
│   ──────────────                                                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A calls read() on empty pipe                              │ │
│   │                                                                      │ │
│   │   read() ───► sleep(addr_of_pipe, PPIPE)                            │ │
│   │                     │                                                │ │
│   │                     ▼                                                │ │
│   │              ┌─────────────┐                                        │ │
│   │              │  Process A  │                                        │ │
│   │              │  SSLEEP     │                                        │ │
│   │              │  wchan=pipe │                                        │ │
│   │              └─────────────┘                                        │ │
│   │                                                                      │ │
│   │   Later: Process B writes to pipe                                   │ │
│   │                                                                      │ │
│   │   write() ───► wakeup(addr_of_pipe)                                 │ │
│   │                     │                                                │ │
│   │                     ▼                                                │ │
│   │              ┌─────────────┐                                        │ │
│   │              │  Process A  │                                        │ │
│   │              │  SRUN       │ ──► Can now be scheduled              │ │
│   │              │  wchan=NULL │                                        │ │
│   │              └─────────────┘                                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SLEEP PRIORITIES:                                                       │
│   ─────────────────                                                        │
│   PSWP      0     Swapper process                                         │
│   PINOD    10     Waiting for inode                                       │
│   PRIBIO   20     Waiting for buffer I/O                                  │
│   PZERO    25     Dividing line: above=interruptible, below=not          │
│   PWAIT    30     Waiting for child                                       │
│   PLOCK    35     Waiting for lock                                        │
│   PPIPE    40     Waiting for pipe                                        │
│   PTTY     50     Waiting for terminal I/O                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 6. Process Credentials

Every process has **credentials** that determine what it can access:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS CREDENTIALS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CREDENTIAL          STORED IN        PURPOSE                      │ │
│   │   ──────────          ─────────        ───────                      │ │
│   │                                                                      │ │
│   │   Real UID (RUID)     proc/u-area     Who actually started process │ │
│   │   Effective UID       proc/u-area     Used for permission checks   │ │
│   │   (EUID)                                                            │ │
│   │   Saved set-UID       u-area          Saved EUID from exec         │ │
│   │                                                                      │ │
│   │   Real GID (RGID)     proc/u-area     Primary group of user        │ │
│   │   Effective GID       proc/u-area     Used for permission checks   │ │
│   │   (EGID)                                                            │ │
│   │   Saved set-GID       u-area          Saved EGID from exec         │ │
│   │                                                                      │ │
│   │   Supplementary       u-area          Additional groups user       │ │
│   │   Groups                              belongs to                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY THREE UIDs?                                                         │
│   ───────────────                                                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Real UID:                                                         │ │
│   │   • Identifies who the user really is                               │ │
│   │   • Set at login, rarely changed                                    │ │
│   │   • Used for accounting, signals between processes                  │ │
│   │                                                                      │ │
│   │   Effective UID:                                                    │ │
│   │   • Used for ALL permission checks                                  │ │
│   │   • File access, creating files, sending signals                    │ │
│   │   • Can be different from Real UID (setuid programs)                │ │
│   │                                                                      │ │
│   │   Saved set-user-ID:                                                │ │
│   │   • Saved copy of EUID from exec of setuid program                  │ │
│   │   • Allows program to temporarily drop privileges                   │ │
│   │   • And regain them later                                           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SETUID PROGRAM EXAMPLE:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   File: /usr/bin/passwd (owned by root, setuid bit set)             │ │
│   │   $ ls -l /usr/bin/passwd                                           │ │
│   │   -rwsr-xr-x 1 root root 68208 passwd                               │ │
│   │       ^                                                              │ │
│   │       └─── 's' = setuid bit                                         │ │
│   │                                                                      │ │
│   │   User "alice" (UID=1000) executes passwd:                          │ │
│   │                                                                      │ │
│   │   BEFORE exec():           AFTER exec():                            │ │
│   │   ──────────────           ─────────────                             │ │
│   │   RUID = 1000 (alice)      RUID = 1000 (alice)  ← unchanged        │ │
│   │   EUID = 1000 (alice)      EUID = 0 (root)      ← changed!         │ │
│   │   saved = 1000             saved = 0            ← saved EUID       │ │
│   │                                                                      │ │
│   │   Now passwd can modify /etc/shadow (root-only file)                │ │
│   │   Because EUID=0, permission checks pass                            │ │
│   │   But signals from alice processes use RUID for checks              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DROPPING AND REGAINING PRIVILEGES:                                      ││
│   ──────────────────────────────────                                       │
│                                                                            │
│   A setuid program can temporarily drop privileges:                       │
│                                                                            │
│   /* Start: RUID=1000, EUID=0, saved=0 */                                 │
│                                                                            │
│   seteuid(getuid());  /* Set EUID to RUID */                              │
│   /* Now: RUID=1000, EUID=1000, saved=0 */                                │
│   /* Running as normal user */                                            │
│                                                                            │
│   seteuid(0);         /* Regain root via saved-set-uid */                 │
│   /* Now: RUID=1000, EUID=0, saved=0 */                                   │
│   /* Running as root again */                                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Process Relationships

Processes exist in a hierarchy and can be organized into groups and sessions:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS RELATIONSHIPS                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PARENT-CHILD RELATIONSHIP:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   Every process (except init/PID 1) has a parent:                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   fork() creates parent-child relationship:                         │ │
│   │                                                                      │ │
│   │              ┌────────────────┐                                     │ │
│   │              │  Parent (bash) │                                     │ │
│   │              │  PID: 1234     │                                     │ │
│   │              │  PPID: 1       │                                     │ │
│   │              └───────┬────────┘                                     │ │
│   │                      │ fork()                                        │ │
│   │                      │                                               │ │
│   │          ┌───────────┴───────────┐                                  │ │
│   │          │                       │                                   │ │
│   │          ▼                       ▼                                   │ │
│   │   ┌──────────────┐       ┌──────────────┐                           │ │
│   │   │ Child 1 (ls) │       │ Child 2 (cat)│                           │ │
│   │   │ PID: 1235    │       │ PID: 1236    │                           │ │
│   │   │ PPID: 1234   │       │ PPID: 1234   │                           │ │
│   │   └──────────────┘       └──────────────┘                           │ │
│   │                                                                      │ │
│   │   Child inherits:                                                   │ │
│   │   • Copy of address space (text shared, data/stack COW)             │ │
│   │   • Open file descriptors                                           │ │
│   │   • Signal handlers                                                 │ │
│   │   • Environment variables                                           │ │
│   │   • Current working directory                                       │ │
│   │   • UIDs/GIDs                                                       │ │
│   │   • Process group and session                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ORPHAN PROCESSES:                                                       │
│   ─────────────────                                                        │
│   When parent exits before child, init (PID 1) adopts the child          │
│   Child's PPID becomes 1                                                  │
│                                                                            │
│   PROCESS GROUPS:                                                         │
│   ───────────────                                                          │
│                                                                            │
│   A process group is a collection of related processes:                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   $ ls | grep foo | wc -l                                           │ │
│   │                                                                      │ │
│   │   Creates a PROCESS GROUP:                                          │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │           Process Group (PGID = 5000)                        │   │ │
│   │   │                                                              │   │ │
│   │   │   ┌─────────┐     ┌──────────┐     ┌─────────┐              │   │ │
│   │   │   │   ls    │────►│   grep   │────►│   wc    │              │   │ │
│   │   │   │PID=5000 │     │ PID=5001 │     │PID=5002 │              │   │ │
│   │   │   │PGID=5000│     │PGID=5000 │     │PGID=5000│              │   │ │
│   │   │   └─────────┘     └──────────┘     └─────────┘              │   │ │
│   │   │        ▲                                                     │   │ │
│   │   │        │                                                     │   │ │
│   │   │   Process Group Leader (PID == PGID)                        │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │   Process group fields in struct proc:                              │ │
│   │   • p_pgrp  - Process group ID                                      │ │
│   │   • p_pid   - Process ID (equals PGID if group leader)              │ │
│   │                                                                      │ │
│   │   Key operations:                                                   │ │
│   │   • setpgid(pid, pgid) - Set process group                          │ │
│   │   • getpgrp()          - Get process group ID                       │ │
│   │   • kill(-pgid, sig)   - Send signal to entire group                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SESSIONS:                                                               │
│   ─────────                                                                │
│                                                                            │
│   A session is a collection of process groups (typically a login):        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                SESSION (SID = 1000)                          │   │ │
│   │   │                                                              │   │ │
│   │   │  Session Leader: bash (PID=1000, SID=1000)                  │   │ │
│   │   │                                                              │   │ │
│   │   │  ┌────────────────────────────────────────────────────────┐ │   │ │
│   │   │  │  FOREGROUND Process Group (PGID=5000)                  │ │   │ │
│   │   │  │     ls | grep foo | wc                                 │ │   │ │
│   │   │  │     (receives terminal signals: Ctrl-C, Ctrl-Z)        │ │   │ │
│   │   │  └────────────────────────────────────────────────────────┘ │   │ │
│   │   │                                                              │   │ │
│   │   │  ┌────────────────────────────────────────────────────────┐ │   │ │
│   │   │  │  BACKGROUND Process Group (PGID=4500)                  │ │   │ │
│   │   │  │     make &                                             │ │   │ │
│   │   │  │     (doesn't receive terminal signals)                 │ │   │ │
│   │   │  └────────────────────────────────────────────────────────┘ │   │ │
│   │   │                                                              │   │ │
│   │   │  ┌────────────────────────────────────────────────────────┐ │   │ │
│   │   │  │  BACKGROUND Process Group (PGID=4200)                  │ │   │ │
│   │   │  │     vim &  (stopped)                                   │ │   │ │
│   │   │  └────────────────────────────────────────────────────────┘ │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │   Session operations:                                               │ │
│   │   • setsid() - Create new session (process becomes session leader) │ │
│   │   • getsid() - Get session ID                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONTROLLING TERMINAL:                                                   │
│   ──────────────────────                                                   │
│                                                                            │
│   Each session can have ONE controlling terminal:                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────────────────┐                                               │ │
│   │   │   /dev/tty1     │◄──── Controlling Terminal                     │ │
│   │   │   (terminal)    │                                               │ │
│   │   └────────┬────────┘                                               │ │
│   │            │                                                         │ │
│   │            │ signals                                                 │ │
│   │            ▼                                                         │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │              SESSION                                         │   │ │
│   │   │                                                              │   │ │
│   │   │   Ctrl-C  ───► SIGINT  to foreground process group          │   │ │
│   │   │   Ctrl-Z  ───► SIGTSTP to foreground process group          │   │ │
│   │   │   Ctrl-\  ───► SIGQUIT to foreground process group          │   │ │
│   │   │   Hangup  ───► SIGHUP  to session leader                    │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │   Terminal field in u-area:                                         │ │
│   │   • u_ttyd  - Device number of controlling terminal                 │ │
│   │   • u_ttyp  - Pointer to tty structure                              │ │
│   │                                                                      │ │
│   │   Daemon processes call setsid() to:                                │ │
│   │   • Create new session (no controlling terminal)                    │ │
│   │   • Prevent terminal signals from affecting the daemon              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 8. File Descriptor Table

Each process has its own **file descriptor table** linking it to open files:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILE DESCRIPTOR TABLE                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THREE-LEVEL TABLE STRUCTURE:                                            │
│   ────────────────────────────                                             │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Per-Process         System-Wide           System-Wide             │ │
│   │   FD Table            File Table            Inode Table             │ │
│   │   (in u-area)         (kernel)              (kernel)                │ │
│   │                                                                      │ │
│   │   ┌─────────────┐     ┌─────────────┐      ┌─────────────┐         │ │
│   │   │ u_ofile[0] ─┼────►│ file struct │─────►│ inode       │         │ │
│   │   │ (stdin)     │     │  f_flag     │      │  i_mode     │         │ │
│   │   ├─────────────┤     │  f_offset   │      │  i_nlink    │         │ │
│   │   │ u_ofile[1] ─┼──┐  │  f_count=1  │      │  i_uid      │         │ │
│   │   │ (stdout)    │  │  │  f_inode ───┼──────►  i_gid      │         │ │
│   │   ├─────────────┤  │  └─────────────┘      │  i_size     │         │ │
│   │   │ u_ofile[2] ─┼──┤                       │  i_count=2  │         │ │
│   │   │ (stderr)    │  │  ┌─────────────┐      │  ...        │         │ │
│   │   ├─────────────┤  └─►│ file struct │──┐   └─────────────┘         │ │
│   │   │ u_ofile[3] ─┼──┐  │  f_flag     │  │                           │ │
│   │   │             │  │  │  f_offset   │  │   ┌─────────────┐         │ │
│   │   ├─────────────┤  │  │  f_count=2  │  └──►│ inode       │         │ │
│   │   │ u_ofile[4]  │  │  │  f_inode ───┼─────►│  (another   │         │ │
│   │   │ (NULL)      │  │  └─────────────┘      │   file)     │         │ │
│   │   ├─────────────┤  │                       │  i_count=1  │         │ │
│   │   │    ...      │  │  ┌─────────────┐      └─────────────┘         │ │
│   │   └─────────────┘  └─►│ file struct │                              │ │
│   │                       │  f_flag     │                              │ │
│   │                       │  f_offset   │                              │ │
│   │   u_ofile[] is in     │  f_count=1  │                              │ │
│   │   the u-area          └─────────────┘                              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY THREE LEVELS?                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   1. Per-process FD table: Each process needs its own fd numbers         │
│   2. System file table: Tracks file offset and flags per open()          │
│   3. Inode table: One entry per actual file (shared by all opens)        │
│                                                                            │
│   FILE TABLE ENTRY (struct file):                                         │
│   ─────────────────────────────────                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct file {                                                      │ │
│   │       short    f_flag;     /* O_RDONLY, O_WRONLY, O_RDWR, etc. */   │ │
│   │       short    f_count;    /* Reference count */                    │ │
│   │       struct inode *f_inode; /* Pointer to inode */                 │ │
│   │       off_t    f_offset;   /* Current file position */              │ │
│   │   };                                                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### File Descriptor Sharing After fork()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILE SHARING AFTER FORK                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When fork() is called, child inherits copies of file descriptors:       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   PARENT                           CHILD                            │ │
│   │   ┌─────────────┐                  ┌─────────────┐                 │ │
│   │   │ u_ofile[0] ─┼──────┐    ┌──────┼─ u_ofile[0] │                 │ │
│   │   │ u_ofile[1] ─┼────┐ │    │ ┌────┼─ u_ofile[1] │                 │ │
│   │   │ u_ofile[2] ─┼──┐ │ │    │ │ ┌──┼─ u_ofile[2] │                 │ │
│   │   │ u_ofile[3] ─┼┐ │ │ │    │ │ │ ┌┼─ u_ofile[3] │                 │ │
│   │   └─────────────┘│ │ │ │    │ │ │ │└─────────────┘                 │ │
│   │                  │ │ │ │    │ │ │ │                                 │ │
│   │                  │ │ │ └────┴─┴─┴─┼──────┐                         │ │
│   │                  │ │ │            │      ▼                          │ │
│   │                  │ │ │            │   ┌──────────────┐              │ │
│   │                  │ │ └────────────┼──►│ file struct  │              │ │
│   │                  │ │              │   │ f_count = 2  │  ◄── Both    │ │
│   │                  │ └──────────────┼──►│ f_offset=100 │      share!  │ │
│   │                  │                │   └──────────────┘              │ │
│   │                  └────────────────┼──►┌──────────────┐              │ │
│   │                                   └──►│ file struct  │              │ │
│   │                                       │ f_count = 2  │              │ │
│   │                                       └──────────────┘              │ │
│   │                                                                      │ │
│   │   IMPORTANT: Parent and child SHARE file offsets!                   │ │
│   │   If parent reads 100 bytes, child's offset moves too.             │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   AFTER INDEPENDENT open() (no sharing):                                  │
│   ───────────────────────────────────────                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A                        Process B                        │ │
│   │   ┌─────────────┐                  ┌─────────────┐                 │ │
│   │   │ u_ofile[3] ─┼──┐               │ u_ofile[3] ─┼──┐              │ │
│   │   └─────────────┘  │               └─────────────┘  │              │ │
│   │                    │                                │              │ │
│   │                    ▼                                ▼              │ │
│   │              ┌──────────────┐              ┌──────────────┐        │ │
│   │              │ file struct  │              │ file struct  │        │ │
│   │              │ f_count = 1  │              │ f_count = 1  │        │ │
│   │              │ f_offset=500 │              │ f_offset=0   │        │ │
│   │              └──────┬───────┘              └──────┬───────┘        │ │
│   │                     │                             │                │ │
│   │                     │      ┌──────────────┐      │                │ │
│   │                     └─────►│    inode     │◄─────┘                │ │
│   │                            │  i_count = 2 │                        │ │
│   │                            │  (same file) │                        │ │
│   │                            └──────────────┘                        │ │
│   │                                                                      │ │
│   │   Each has SEPARATE offset, but shares inode (same file)           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### dup() and dup2()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DUP AND DUP2                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   dup() creates a copy of a file descriptor:                              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   int new_fd = dup(old_fd);                                         │ │
│   │                                                                      │ │
│   │   BEFORE dup(3):                   AFTER dup(3):                    │ │
│   │   ┌─────────────┐                  ┌─────────────┐                 │ │
│   │   │ u_ofile[0]  │                  │ u_ofile[0]  │                 │ │
│   │   │ u_ofile[1]  │                  │ u_ofile[1]  │                 │ │
│   │   │ u_ofile[2]  │                  │ u_ofile[2]  │                 │ │
│   │   │ u_ofile[3] ─┼──┐               │ u_ofile[3] ─┼──┐              │ │
│   │   │ u_ofile[4]  │  │               │ u_ofile[4] ─┼──┤ new!        │ │
│   │   └─────────────┘  │               └─────────────┘  │              │ │
│   │                    │                                │              │ │
│   │                    ▼                                ▼              │ │
│   │              ┌──────────────┐              ┌──────────────┐        │ │
│   │              │ file struct  │              │ file struct  │        │ │
│   │              │ f_count = 1  │              │ f_count = 2  │ ◄──    │ │
│   │              └──────────────┘              └──────────────┘        │ │
│   │                                                                      │ │
│   │   dup(old_fd) returns lowest available fd                          │ │
│   │   Both fds share the same file table entry (same offset!)          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   dup2() redirects to a specific fd (used for I/O redirection):          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   /* Redirect stdout to a file */                                   │ │
│   │   int fd = open("output.txt", O_WRONLY);                            │ │
│   │   dup2(fd, 1);    /* fd 1 (stdout) now points to file */           │ │
│   │   close(fd);      /* original fd no longer needed */                │ │
│   │                                                                      │ │
│   │   BEFORE:                          AFTER dup2(fd, 1):               │ │
│   │   ┌─────────────┐                  ┌─────────────┐                 │ │
│   │   │ u_ofile[0]──┼──►stdin          │ u_ofile[0]──┼──►stdin         │ │
│   │   │ u_ofile[1]──┼──►terminal       │ u_ofile[1]──┼──►output.txt   │ │
│   │   │ u_ofile[2]──┼──►terminal       │ u_ofile[2]──┼──►terminal     │ │
│   │   │ u_ofile[3]──┼──►output.txt     │ u_ofile[3]  │  (closed)      │ │
│   │   └─────────────┘                  └─────────────┘                 │ │
│   │                                                                      │ │
│   │   printf("hello") now writes to output.txt!                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 9. Signal Handling

Signals are software interrupts that notify processes of events:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL HANDLING                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SIGNAL STORAGE IN PROCESS:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct proc (always in memory):                                   │ │
│   │   ┌────────────────────────────────────────────────────────────┐   │ │
│   │   │ p_sig     - Bitmap of pending signals (one bit per signal) │   │ │
│   │   │             Must be checked even when process is swapped   │   │ │
│   │   └────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │   u-area (swappable):                                               │ │
│   │   ┌────────────────────────────────────────────────────────────┐   │ │
│   │   │ u_signal[]  - Array of signal handlers (one per signal)    │   │ │
│   │   │               SIG_DFL (0) = default action                 │   │ │
│   │   │               SIG_IGN (1) = ignore signal                  │   │ │
│   │   │               address    = user-defined handler            │   │ │
│   │   │                                                             │   │ │
│   │   │ u_sigmask[] - Per-signal mask (signals blocked during      │   │ │
│   │   │               execution of handler)                        │   │ │
│   │   └────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SIGNAL DISPOSITION:                                                     │
│   ───────────────────                                                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   DISPOSITION      MEANING                                          │ │
│   │   ───────────      ───────                                          │ │
│   │   SIG_DFL          Take default action for this signal             │ │
│   │                    (terminate, ignore, stop, or continue)          │ │
│   │                                                                      │ │
│   │   SIG_IGN          Ignore the signal                                │ │
│   │                    (cannot ignore SIGKILL or SIGSTOP)              │ │
│   │                                                                      │ │
│   │   handler_func     Call user-defined function                       │ │
│   │                    (cannot catch SIGKILL or SIGSTOP)               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON SIGNALS:                                                         │
│   ───────────────                                                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   SIGNAL    NUM    DEFAULT     SOURCE                               │ │
│   │   ──────    ───    ───────     ──────                               │ │
│   │   SIGHUP     1     Terminate   Terminal hangup                     │ │
│   │   SIGINT     2     Terminate   Ctrl-C                              │ │
│   │   SIGQUIT    3     Core dump   Ctrl-\                              │ │
│   │   SIGILL     4     Core dump   Illegal instruction                 │ │
│   │   SIGKILL    9     Terminate   Cannot be caught or ignored         │ │
│   │   SIGSEGV   11     Core dump   Invalid memory reference            │ │
│   │   SIGPIPE   13     Terminate   Write to pipe with no reader        │ │
│   │   SIGALRM   14     Terminate   alarm() timer expired               │ │
│   │   SIGTERM   15     Terminate   Termination request                 │ │
│   │   SIGCHLD   17     Ignore      Child stopped or terminated         │ │
│   │   SIGCONT   18     Continue    Continue if stopped                 │ │
│   │   SIGSTOP   19     Stop        Cannot be caught or ignored         │ │
│   │   SIGTSTP   20     Stop        Ctrl-Z                              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Signal Delivery

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL DELIVERY MECHANISM                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHEN ARE SIGNALS CHECKED?                                               │
│   ─────────────────────────                                                │
│                                                                            │
│   Signals are checked at these points:                                    │
│   1. When returning from kernel to user mode (after syscall)             │
│   2. When returning from interrupt handler                                │
│   3. When waking up from interruptible sleep                              │
│                                                                            │
│   SIGNAL DELIVERY ALGORITHM:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   algorithm issig()   /* check for pending signals */               │ │
│   │   {                                                                  │ │
│   │       while (p_sig != 0)  /* any pending signals? */                │ │
│   │       {                                                              │ │
│   │           sig = find_lowest_bit_set(p_sig);                         │ │
│   │                                                                      │ │
│   │           if (u_signal[sig] == SIG_IGN)                             │ │
│   │           {                                                          │ │
│   │               clear_bit(p_sig, sig);  /* ignore it */               │ │
│   │               continue;                                              │ │
│   │           }                                                          │ │
│   │                                                                      │ │
│   │           if (sig == SIGCHLD && u_signal[sig] == SIG_DFL)           │ │
│   │           {                                                          │ │
│   │               clear_bit(p_sig, sig);  /* default for SIGCHLD */     │ │
│   │               continue;               /* is to ignore */            │ │
│   │           }                                                          │ │
│   │                                                                      │ │
│   │           return sig;  /* found a signal to deliver */              │ │
│   │       }                                                              │ │
│   │       return 0;  /* no signals */                                   │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CALLING USER SIGNAL HANDLER:                                            │
│   ─────────────────────────────                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. Kernel saves current user context to user stack               │ │
│   │                                                                      │ │
│   │      User Stack:                                                    │ │
│   │      ┌─────────────────┐                                            │ │
│   │      │  Saved PC       │  ◄── Return to here after handler         │ │
│   │      │  Saved PSW      │      (where signal interrupted)           │ │
│   │      │  Saved regs     │                                            │ │
│   │      │  Signal number  │                                            │ │
│   │      ├─────────────────┤                                            │ │
│   │      │  (previous      │                                            │ │
│   │      │   stack data)   │                                            │ │
│   │      └─────────────────┘                                            │ │
│   │                                                                      │ │
│   │   2. Kernel modifies return address to handler function            │ │
│   │                                                                      │ │
│   │   3. Return to user mode (now executing handler)                   │ │
│   │                                                                      │ │
│   │   4. Handler calls sigreturn() to restore context                  │ │
│   │                                                                      │ │
│   │   VISUALIZATION:                                                    │ │
│   │                                                                      │ │
│   │   ┌────────────┐   signal   ┌────────────┐  return   ┌───────────┐ │ │
│   │   │ User code  │──arrives──►│  Handler   │──────────►│User code  │ │ │
│   │   │ (syscall)  │            │  function  │           │(continues)│ │ │
│   │   └────────────┘            └────────────┘           └───────────┘ │ │
│   │         │                         │                        │       │ │
│   │         │                         │                        │       │ │
│   │         ▼                         ▼                        ▼       │ │
│   │   ┌─────────────────────────────────────────────────────────────┐ │ │
│   │   │                       KERNEL                                 │ │ │
│   │   └─────────────────────────────────────────────────────────────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 10. Process Creation and Termination

### The fork() System Call

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FORK() SYSTEM CALL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   fork() creates a new process by duplicating the calling process:        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   algorithm fork()                                                  │ │
│   │   {                                                                  │ │
│   │       check if system process table has free slot;                  │ │
│   │       check if user has not exceeded process limit;                 │ │
│   │                                                                      │ │
│   │       allocate free proc table slot for child;                      │ │
│   │       allocate unique PID for child;                                │ │
│   │                                                                      │ │
│   │       /* Copy parent's context */                                   │ │
│   │       copy parent's proc table entry to child;                      │ │
│   │       set child p_ppid = parent's PID;                              │ │
│   │       set child p_stat = SIDL;  /* being created */                 │ │
│   │                                                                      │ │
│   │       /* Copy memory regions */                                     │ │
│   │       for each region attached to parent:                           │ │
│   │       {                                                              │ │
│   │           if (region is shareable)  /* text */                      │ │
│   │               increment region reference count;                     │ │
│   │           else  /* data, stack */                                   │ │
│   │               allocate new region, copy contents;                   │ │
│   │               (or use copy-on-write)                                │ │
│   │           attach region to child;                                   │ │
│   │       }                                                              │ │
│   │                                                                      │ │
│   │       /* Copy u-area */                                             │ │
│   │       allocate u-area for child;                                    │ │
│   │       copy parent's u-area to child;                                │ │
│   │       increment file table reference counts;                        │ │
│   │                                                                      │ │
│   │       /* Set up return values */                                    │ │
│   │       child u-area return value = 0;                                │ │
│   │       parent return value = child's PID;                            │ │
│   │                                                                      │ │
│   │       set child p_stat = SRUN;  /* ready to run */                  │ │
│   │       return;                                                       │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FORK VISUALIZATION:                                                     │
│   ───────────────────                                                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BEFORE fork():                                                    │ │
│   │   ┌─────────────────────┐                                           │ │
│   │   │      PARENT         │                                           │ │
│   │   │  ┌──────────────┐   │                                           │ │
│   │   │  │ Text  (code) │   │                                           │ │
│   │   │  ├──────────────┤   │                                           │ │
│   │   │  │ Data  (heap) │   │                                           │ │
│   │   │  ├──────────────┤   │                                           │ │
│   │   │  │ Stack        │   │                                           │ │
│   │   │  └──────────────┘   │                                           │ │
│   │   └─────────────────────┘                                           │ │
│   │                                                                      │ │
│   │   AFTER fork():                                                     │ │
│   │   ┌─────────────────────┐      ┌─────────────────────┐             │ │
│   │   │      PARENT         │      │       CHILD         │             │ │
│   │   │  ┌──────────────┐   │      │  ┌──────────────┐   │             │ │
│   │   │  │ Text  (code)─┼───┼──────┼──│ Text (shared)│   │             │ │
│   │   │  ├──────────────┤   │      │  ├──────────────┤   │             │ │
│   │   │  │ Data  (heap) │   │      │  │ Data  (COW)  │   │             │ │
│   │   │  ├──────────────┤   │      │  ├──────────────┤   │             │ │
│   │   │  │ Stack        │   │      │  │ Stack (COW)  │   │             │ │
│   │   │  └──────────────┘   │      │  └──────────────┘   │             │ │
│   │   │  returns: child_pid │      │  returns: 0        │             │ │
│   │   └─────────────────────┘      └─────────────────────┘             │ │
│   │                                                                      │ │
│   │   COW = Copy-On-Write: Physical pages shared until modified        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The exec() System Call

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EXEC() SYSTEM CALL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   exec() replaces the current process image with a new program:           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   algorithm exec(filename, argv, envp)                              │ │
│   │   {                                                                  │ │
│   │       get inode of filename;                                        │ │
│   │       verify file is executable and user has permission;            │ │
│   │                                                                      │ │
│   │       read executable header;                                       │ │
│   │       /* header contains: text size, data size, entry point */      │ │
│   │                                                                      │ │
│   │       /* Detach old regions */                                      │ │
│   │       for each region attached to process:                          │ │
│   │           detach region;                                            │ │
│   │           if (region reference count == 0)                          │ │
│   │               free region;                                          │ │
│   │                                                                      │ │
│   │       /* Allocate new regions */                                    │ │
│   │       allocate and attach text region;                              │ │
│   │       allocate and attach data region;                              │ │
│   │       allocate and attach stack region;                             │ │
│   │                                                                      │ │
│   │       /* Load program */                                            │ │
│   │       copy text from file to text region;                           │ │
│   │       copy initialized data from file to data region;               │ │
│   │       zero BSS portion of data region;                              │ │
│   │                                                                      │ │
│   │       /* Set up stack */                                            │ │
│   │       copy argv and envp to stack;                                  │ │
│   │       set argc, argv, envp pointers;                                │ │
│   │                                                                      │ │
│   │       /* Handle setuid/setgid */                                    │ │
│   │       if (file has setuid bit)                                      │ │
│   │           set effective UID = file owner;                           │ │
│   │       if (file has setgid bit)                                      │ │
│   │           set effective GID = file group;                           │ │
│   │                                                                      │ │
│   │       /* Reset signals */                                           │ │
│   │       for each caught signal:                                       │ │
│   │           set signal handler to SIG_DFL;                            │ │
│   │                                                                      │ │
│   │       initialize PC to entry point of program;                      │ │
│   │       return to user mode;                                          │ │
│   │       /* exec never returns on success */                           │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EXEC FAMILY:                                                            │
│   ────────────                                                             │
│   execl, execv, execle, execve, execlp, execvp                           │
│   (differ in how arguments and environment are passed)                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### The exit() and wait() System Calls

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EXIT() AND WAIT()                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   EXIT() - Process termination:                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   algorithm exit(status)                                            │ │
│   │   {                                                                  │ │
│   │       ignore all signals;                                           │ │
│   │       close all open files;                                         │ │
│   │                                                                      │ │
│   │       /* Release memory regions */                                  │ │
│   │       for each region attached to process:                          │ │
│   │       {                                                              │ │
│   │           detach region;                                            │ │
│   │           if (region reference count == 0)                          │ │
│   │               free region;                                          │ │
│   │       }                                                              │ │
│   │                                                                      │ │
│   │       /* Store exit status for parent */                            │ │
│   │       save status in proc table entry;                              │ │
│   │                                                                      │ │
│   │       /* Orphan children to init */                                 │ │
│   │       for each child process:                                       │ │
│   │           set child's parent = init (PID 1);                        │ │
│   │                                                                      │ │
│   │       /* Send signal to parent */                                   │ │
│   │       send SIGCHLD to parent;                                       │ │
│   │                                                                      │ │
│   │       /* Become zombie */                                           │ │
│   │       set process state = SZOMB;                                    │ │
│   │       release u-area;                                               │ │
│   │       context switch;  /* never returns */                          │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WAIT() - Parent waits for child:                                        │
│   ────────────────────────────────                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   algorithm wait(status_ptr)                                        │ │
│   │   {                                                                  │ │
│   │   loop:                                                              │ │
│   │       for each child process:                                       │ │
│   │       {                                                              │ │
│   │           if (child state == SZOMB)                                 │ │
│   │           {                                                          │ │
│   │               /* Found zombie child */                              │ │
│   │               copy child's exit status to status_ptr;              │ │
│   │               free child's proc table entry;                       │ │
│   │               return child's PID;                                   │ │
│   │           }                                                          │ │
│   │       }                                                              │ │
│   │                                                                      │ │
│   │       if (no children exist)                                        │ │
│   │           return -1;  /* ECHILD error */                            │ │
│   │                                                                      │ │
│   │       sleep(event: child status change);                            │ │
│   │       goto loop;                                                    │ │
│   │   }                                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ZOMBIE STATE VISUALIZATION:                                             │
│   ───────────────────────────                                              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   RUNNING PROCESS:        ZOMBIE PROCESS:          REAPED:         │ │
│   │   ┌────────────────┐      ┌────────────────┐       ┌────────────┐  │ │
│   │   │ proc entry     │      │ proc entry     │       │ proc entry │  │ │
│   │   │ u-area         │  ──► │ (status only)  │  ──►  │ (freed)    │  │ │
│   │   │ memory regions │      │ NO u-area      │       └────────────┘  │ │
│   │   │ file desc      │      │ NO memory      │                       │ │
│   │   └────────────────┘      └────────────────┘       wait() called  │ │
│   │                                                                      │ │
│   │   • Zombie holds: PID, exit status, resource usage                  │ │
│   │   • Zombie releases: memory, u-area, file descriptors              │ │
│   │   • Zombie persists until parent calls wait()                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Modern Linux: task_struct

Modern Linux uses a unified structure called `task_struct`:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MODERN LINUX: task_struct                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   EVOLUTION: proc + u-area → task_struct                                  │
│   ──────────────────────────────────────                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Traditional UNIX:                Modern Linux:                    │ │
│   │   ┌──────────────────┐             ┌──────────────────────────────┐│ │
│   │   │   struct proc    │             │      struct task_struct      ││ │
│   │   │   (always in     │             │      (~6 KB, always in       ││ │
│   │   │    memory)       │             │       memory - no swapping)  ││ │
│   │   └────────┬─────────┘             │                              ││ │
│   │            │                       │  • Process identification    ││ │
│   │            │                       │  • Scheduling info           ││ │
│   │   ┌────────▼─────────┐             │  • Memory management         ││ │
│   │   │   struct user    │             │  • File descriptors          ││ │
│   │   │   (u-area,       │      ──►    │  • Signal handling           ││ │
│   │   │    swappable)    │             │  • Credentials               ││ │
│   │   └──────────────────┘             │  • Resource limits           ││ │
│   │                                    │  • Namespaces                ││ │
│   │                                    │  • Control groups            ││ │
│   │                                    └──────────────────────────────┘│ │
│   │                                                                      │ │
│   │   Why the change?                                                   │ │
│   │   • Virtual memory eliminated need for swapping process metadata   │ │
│   │   • Single structure is simpler and more efficient                 │ │
│   │   • Modern servers have abundant RAM                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY task_struct FIELDS:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct task_struct {                                              │ │
│   │       /* Process State */                                           │ │
│   │       volatile long state;        /* TASK_RUNNING, etc. */         │ │
│   │       void *stack;                /* Kernel stack */               │ │
│   │                                                                      │ │
│   │       /* Process Identification */                                  │ │
│   │       pid_t pid;                  /* Process ID */                 │ │
│   │       pid_t tgid;                 /* Thread Group ID */            │ │
│   │       struct task_struct *parent; /* Parent process */             │ │
│   │       struct list_head children;  /* List of children */           │ │
│   │                                                                      │ │
│   │       /* Credentials */                                             │ │
│   │       const struct cred *cred;    /* Credentials pointer */        │ │
│   │                                                                      │ │
│   │       /* Memory */                                                  │ │
│   │       struct mm_struct *mm;       /* Memory descriptor */          │ │
│   │                                                                      │ │
│   │       /* Files */                                                   │ │
│   │       struct files_struct *files; /* Open file table */            │ │
│   │                                                                      │ │
│   │       /* Filesystem */                                              │ │
│   │       struct fs_struct *fs;       /* Filesystem info */            │ │
│   │                                                                      │ │
│   │       /* Signals */                                                 │ │
│   │       struct signal_struct *signal; /* Signal handlers */          │ │
│   │       sigset_t blocked;             /* Blocked signals */          │ │
│   │       sigset_t pending;             /* Pending signals */          │ │
│   │                                                                      │ │
│   │       /* Scheduling */                                              │ │
│   │       int prio;                   /* Dynamic priority */           │ │
│   │       int static_prio;            /* Static priority (nice) */     │ │
│   │       unsigned int policy;        /* Scheduling policy */          │ │
│   │       ...                                                           │ │
│   │   };                                                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Thread Groups and TGID

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREAD GROUPS AND TGID                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   In Linux, threads are implemented as processes that share resources:    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   TRADITIONAL UNIX:          LINUX THREADS:                         │ │
│   │   ─────────────────          ──────────────                          │ │
│   │   Process = heavy            Thread = lightweight process            │ │
│   │   Thread = user-level        (kernel-level, via clone())            │ │
│   │                                                                      │ │
│   │   THREAD GROUP:                                                      │ │
│   │   ┌────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   Thread Group (TGID = 1000)                               │   │ │
│   │   │   ┌──────────────────────────────────────────────────────┐ │   │ │
│   │   │   │                                                       │ │   │ │
│   │   │   │  Main Thread         Thread 1          Thread 2      │ │   │ │
│   │   │   │  ┌───────────┐      ┌───────────┐    ┌───────────┐  │ │   │ │
│   │   │   │  │task_struct│      │task_struct│    │task_struct│  │ │   │ │
│   │   │   │  │pid=1000   │      │pid=1001   │    │pid=1002   │  │ │   │ │
│   │   │   │  │tgid=1000  │      │tgid=1000  │    │tgid=1000  │  │ │   │ │
│   │   │   │  └─────┬─────┘      └─────┬─────┘    └─────┬─────┘  │ │   │ │
│   │   │   │        │                  │                │        │ │   │ │
│   │   │   │        └──────────────────┼────────────────┘        │ │   │ │
│   │   │   │                           │                          │ │   │ │
│   │   │   │                           ▼                          │ │   │ │
│   │   │   │              ┌────────────────────────┐             │ │   │ │
│   │   │   │              │   SHARED RESOURCES:    │             │ │   │ │
│   │   │   │              │   • mm (memory)        │             │ │   │ │
│   │   │   │              │   • files (fd table)   │             │ │   │ │
│   │   │   │              │   • fs (cwd, root)     │             │ │   │ │
│   │   │   │              │   • signal handlers    │             │ │   │ │
│   │   │   │              └────────────────────────┘             │ │   │ │
│   │   │   │                                                       │ │   │ │
│   │   │   └──────────────────────────────────────────────────────┘ │   │ │
│   │   │                                                             │   │ │
│   │   └────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   │   PID vs TGID:                                                      │ │
│   │   ┌────────────────────────────────────────────────────────────┐   │ │
│   │   │ Field │ Meaning                      │ getpid() returns   │   │ │
│   │   ├───────┼──────────────────────────────┼────────────────────┤   │ │
│   │   │ pid   │ Unique per task_struct       │ (not this)         │   │ │
│   │   │       │ (kernel's view)              │                    │   │ │
│   │   ├───────┼──────────────────────────────┼────────────────────┤   │ │
│   │   │ tgid  │ Same for all threads in      │ YES                │   │ │
│   │   │       │ process (user's view of PID) │                    │   │ │
│   │   └───────┴──────────────────────────────┴────────────────────┘   │ │
│   │                                                                      │ │
│   │   • getpid() returns tgid (process ID as user expects)             │ │
│   │   • gettid() returns pid (actual thread ID)                        │ │
│   │   • For single-threaded: pid == tgid                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   clone() FLAGS FOR RESOURCE SHARING:                                     │
│   ────────────────────────────────────                                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Flag           │ Effect                                             │ │
│   ├────────────────┼───────────────────────────────────────────────────┤ │
│   │ CLONE_VM       │ Share memory space                                │ │
│   │ CLONE_FS       │ Share filesystem info (cwd, root, umask)          │ │
│   │ CLONE_FILES    │ Share file descriptor table                       │ │
│   │ CLONE_SIGHAND  │ Share signal handlers                             │ │
│   │ CLONE_THREAD   │ Same thread group (same tgid)                     │ │
│   │ CLONE_PARENT   │ Share same parent                                 │ │
│   │ CLONE_NEWPID   │ New PID namespace (containers)                    │ │
│   │ CLONE_NEWNS    │ New mount namespace                               │ │
│   └────────────────┴───────────────────────────────────────────────────┘ │
│                                                                            │
│   fork():   clone() with no sharing flags → new process                  │
│   pthread:  clone(CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_THREAD|...)       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Namespaces

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX NAMESPACES                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Namespaces provide isolation of system resources:                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Without Namespaces:              With Namespaces:                 │ │
│   │   ┌──────────────────────┐        ┌──────────────────────┐         │ │
│   │   │      KERNEL          │        │      KERNEL          │         │ │
│   │   │  ┌──────────────┐    │        │  ┌──────────────┐    │         │ │
│   │   │  │ Global PIDs  │    │        │  │ PID NS 1     │    │         │ │
│   │   │  │ 1, 2, 3...   │    │        │  │ PIDs: 1,2,3  │    │         │ │
│   │   │  └──────────────┘    │        │  └──────────────┘    │         │ │
│   │   │                      │        │  ┌──────────────┐    │         │ │
│   │   │  All processes see   │        │  │ PID NS 2     │    │         │ │
│   │   │  same PID space      │        │  │ PIDs: 1,2,3  │    │         │ │
│   │   │                      │        │  └──────────────┘    │         │ │
│   │   └──────────────────────┘        │  Each container has │         │ │
│   │                                    │  own PID 1 (init)   │         │ │
│   │                                    └──────────────────────┘         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NAMESPACE TYPES:                                                        │
│   ────────────────                                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Namespace │ Isolates                    │ Example Use              │ │
│   ├───────────┼─────────────────────────────┼──────────────────────────┤ │
│   │ PID       │ Process IDs                 │ Container has own init  │ │
│   │ Mount     │ Mount points                │ Container filesystem    │ │
│   │ Network   │ Network stack (interfaces,  │ Virtual network for     │ │
│   │           │ routing, iptables)          │ container               │ │
│   │ UTS       │ Hostname and domain name    │ Container hostname      │ │
│   │ IPC       │ System V IPC, POSIX queues  │ Isolated shared memory  │ │
│   │ User      │ UID/GID mappings            │ Root in container =     │ │
│   │           │                             │ non-root on host        │ │
│   │ Cgroup    │ Cgroup root directory       │ Resource limit views    │ │
│   │ Time      │ System clocks (Linux 5.6+)  │ Container time offset   │ │
│   └───────────┴─────────────────────────────┴──────────────────────────┘ │
│                                                                            │
│   NAMESPACE IN task_struct:                                               │
│   ─────────────────────────                                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct task_struct {                                              │ │
│   │       ...                                                           │ │
│   │       struct nsproxy *nsproxy;  /* Namespace proxy */              │ │
│   │       ...                                                           │ │
│   │   };                                                                 │ │
│   │                                                                      │ │
│   │   struct nsproxy {                                                  │ │
│   │       struct uts_namespace  *uts_ns;   /* Hostname */              │ │
│   │       struct ipc_namespace  *ipc_ns;   /* IPC */                   │ │
│   │       struct mnt_namespace  *mnt_ns;   /* Mount points */          │ │
│   │       struct pid_namespace  *pid_ns;   /* Process IDs */           │ │
│   │       struct net            *net_ns;   /* Network */               │ │
│   │       struct cgroup_namespace *cgroup_ns;                          │ │
│   │   };                                                                 │ │
│   │                                                                      │ │
│   │   Container = Process with separate nsproxy                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Control Groups (cgroups)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONTROL GROUPS (cgroups)                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Cgroups limit, account, and isolate resource usage:                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CGROUP HIERARCHY:                                                 │ │
│   │                                                                      │ │
│   │                    ┌────────────────┐                               │ │
│   │                    │  Root cgroup   │                               │ │
│   │                    │  (all system   │                               │ │
│   │                    │   resources)   │                               │ │
│   │                    └───────┬────────┘                               │ │
│   │                            │                                         │ │
│   │              ┌─────────────┼─────────────┐                          │ │
│   │              │             │             │                          │ │
│   │              ▼             ▼             ▼                          │ │
│   │        ┌─────────┐   ┌─────────┐   ┌─────────┐                     │ │
│   │        │ web     │   │ database│   │ batch   │                     │ │
│   │        │ CPU:50% │   │ CPU:30% │   │ CPU:20% │                     │ │
│   │        │ MEM:4GB │   │ MEM:8GB │   │ MEM:2GB │                     │ │
│   │        └────┬────┘   └─────────┘   └─────────┘                     │ │
│   │             │                                                       │ │
│   │        ┌────┴────┐                                                  │ │
│   │        │ nginx   │                                                  │ │
│   │        │ workers │                                                  │ │
│   │        └─────────┘                                                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CGROUP CONTROLLERS (SUBSYSTEMS):                                        │
│   ────────────────────────────────                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Controller │ What It Controls                                       │ │
│   ├────────────┼───────────────────────────────────────────────────────┤ │
│   │ cpu        │ CPU time scheduling weight                            │ │
│   │ cpuset     │ Which CPUs/memory nodes can be used                   │ │
│   │ memory     │ Memory usage limits (RSS, swap)                       │ │
│   │ blkio      │ Block I/O bandwidth limits                            │ │
│   │ pids       │ Number of processes limit                             │ │
│   │ devices    │ Device access control                                 │ │
│   │ net_cls    │ Network packet classification                         │ │
│   │ freezer    │ Suspend/resume process groups                         │ │
│   └────────────┴───────────────────────────────────────────────────────┘ │
│                                                                            │
│   CGROUP IN task_struct:                                                  │
│   ──────────────────────                                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct task_struct {                                              │ │
│   │       ...                                                           │ │
│   │       struct css_set *cgroups;  /* Cgroup subsystem state */       │ │
│   │       ...                                                           │ │
│   │   };                                                                 │ │
│   │                                                                      │ │
│   │   /* When process tries to allocate memory */                       │ │
│   │   if (current->cgroups->memory_limit_exceeded)                     │ │
│   │       trigger_oom_killer_for_cgroup();                             │ │
│   │                                                                      │ │
│   │   /* When process is scheduled */                                   │ │
│   │   cpu_shares = current->cgroups->cpu_shares;                       │ │
│   │   /* Scheduler uses shares to allocate time */                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CGROUPS + NAMESPACES = CONTAINERS:                                      │
│   ──────────────────────────────────                                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Docker/Kubernetes Container:                                      │ │
│   │   ┌──────────────────────────────────────────────────────────────┐ │ │
│   │   │                                                               │ │ │
│   │   │   NAMESPACES (Isolation):    CGROUPS (Resource Limits):      │ │ │
│   │   │   • PID namespace            • CPU: 1 core                   │ │ │
│   │   │   • Network namespace        • Memory: 512MB                 │ │ │
│   │   │   • Mount namespace          • Disk I/O: 100MB/s             │ │ │
│   │   │   • User namespace           • PIDs: 100                     │ │ │
│   │   │                                                               │ │ │
│   │   │   Container = Process with special namespaces + cgroups      │ │ │
│   │   │                                                               │ │ │
│   │   └──────────────────────────────────────────────────────────────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Summary and Appendix

### Quick Reference: struct proc Fields

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    STRUCT PROC QUICK REFERENCE                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Field     │ Type     │ Description                                  │ │
│   ├───────────┼──────────┼──────────────────────────────────────────────┤ │
│   │ p_stat    │ char     │ Process state (SIDL, SRUN, SSLEEP, etc.)    │ │
│   │ p_flag    │ int      │ Flags (SLOAD, SSYS, SLOCK, STRC)            │ │
│   │ p_pri     │ char     │ Current scheduling priority                 │ │
│   │ p_sig     │ int      │ Pending signal bitmap                       │ │
│   │ p_uid     │ ushort   │ Real user ID                                │ │
│   │ p_suid    │ ushort   │ Set-user-ID (saved effective UID)          │ │
│   │ p_pid     │ int      │ Process ID                                  │ │
│   │ p_ppid    │ int      │ Parent process ID                           │ │
│   │ p_pgrp    │ int      │ Process group ID                            │ │
│   │ p_cpu     │ char     │ CPU usage for scheduling decay              │ │
│   │ p_nice    │ char     │ Nice value (-20 to +19)                     │ │
│   │ p_wchan   │ caddr_t  │ Sleep address (wait channel)                │ │
│   │ p_textp   │ struct*  │ Pointer to text structure                   │ │
│   │ p_addr    │ struct*  │ Pointer to u-area                           │ │
│   │ p_size    │ size_t   │ Process size in clicks                      │ │
│   └───────────┴──────────┴──────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Quick Reference: struct user Fields

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    STRUCT USER (U-AREA) QUICK REFERENCE                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Field      │ Type      │ Description                                │ │
│   ├────────────┼───────────┼────────────────────────────────────────────┤ │
│   │ u_uid      │ ushort    │ Effective user ID                         │ │
│   │ u_gid      │ ushort    │ Effective group ID                        │ │
│   │ u_ruid     │ ushort    │ Real user ID                              │ │
│   │ u_rgid     │ ushort    │ Real group ID                             │ │
│   │ u_ofile[]  │ struct*[] │ Open file descriptors (NOFILE entries)    │ │
│   │ u_cdir     │ struct*   │ Current working directory inode           │ │
│   │ u_rdir     │ struct*   │ Root directory inode                      │ │
│   │ u_cmask    │ int       │ File creation mask (umask)                │ │
│   │ u_procp    │ struct*   │ Pointer to proc table entry               │ │
│   │ u_ar0      │ int*      │ Pointer to saved registers                │ │
│   │ u_signal[] │ func*[]   │ Signal handler array                      │ │
│   │ u_sigmask[]│ int[]     │ Signal mask per signal                    │ │
│   │ u_rlimit[] │ struct[]  │ Resource limits (RLIMIT_*)               │ │
│   │ u_utime    │ time_t    │ User CPU time                             │ │
│   │ u_stime    │ time_t    │ System CPU time                           │ │
│   │ u_start    │ time_t    │ Process start time                        │ │
│   │ u_stack[]  │ char[]    │ Kernel stack                              │ │
│   └────────────┴───────────┴────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Quick Reference: Process States

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS STATES QUICK REFERENCE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ State   │ Value │ Description                                       │ │
│   ├─────────┼───────┼───────────────────────────────────────────────────┤ │
│   │ SIDL    │ 1     │ Process being created                            │ │
│   │ SRUN    │ 2     │ Runnable (ready to execute or executing)         │ │
│   │ SSLEEP  │ 3     │ Sleeping (waiting for event)                     │ │
│   │ SSTOP   │ 4     │ Stopped (SIGSTOP, job control)                   │ │
│   │ SZOMB   │ 5     │ Zombie (terminated, waiting for parent)          │ │
│   └─────────┴───────┴───────────────────────────────────────────────────┘ │
│                                                                            │
│   Modern Linux States (task_struct->state):                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ TASK_RUNNING          │ On run queue or executing on CPU           │ │
│   │ TASK_INTERRUPTIBLE    │ Sleeping, can be woken by signal           │ │
│   │ TASK_UNINTERRUPTIBLE  │ Sleeping, cannot be interrupted            │ │
│   │ __TASK_STOPPED        │ Stopped by signal                          │ │
│   │ __TASK_TRACED         │ Stopped by debugger (ptrace)               │ │
│   │ EXIT_ZOMBIE           │ Terminated, waiting for wait()             │ │
│   │ EXIT_DEAD             │ Final state, being removed                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Comparison: Traditional UNIX vs Modern Linux

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL UNIX vs MODERN LINUX                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Aspect              │ Traditional UNIX     │ Modern Linux           │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Main structure      │ struct proc +        │ struct task_struct    │ │
│   │                     │ struct user          │ (unified)              │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Size                │ ~100 bytes + 1KB     │ ~6 KB                  │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Swappability        │ u-area swappable     │ Always in memory       │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Threads             │ Not native           │ Native (clone())       │ │
│   │                     │ (user-level)         │ TGID + PID             │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Process table       │ Fixed-size array     │ Hash tables + lists    │ │
│   │                     │ (NPROC limit)        │ (dynamic)              │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Memory regions      │ Region table         │ vm_area_struct list    │ │
│   │                     │                      │ in mm_struct           │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Credentials         │ In proc/u-area       │ Separate struct cred   │ │
│   │                     │                      │ (RCU protected)        │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Isolation           │ UID-based only       │ Namespaces + cgroups   │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Resource limits     │ Per-process rlimit   │ Cgroups (hierarchical) │ │
│   ├─────────────────────┼──────────────────────┼────────────────────────┤ │
│   │ Scheduler           │ Simple priority      │ CFS (Completely Fair   │ │
│   │                     │ decay                │ Scheduler)             │ │
│   └─────────────────────┴──────────────────────┴────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture: Process Structure Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE BIG PICTURE: PROCESS STRUCTURE                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │                         PROCESS                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                                                              │  │ │
│   │   │  ╔═══════════════════════════════════════════════════════╗  │  │ │
│   │   │  ║          KERNEL DATA STRUCTURES                        ║  │  │ │
│   │   │  ╠═══════════════════════════════════════════════════════╣  │  │ │
│   │   │  ║                                                        ║  │  │ │
│   │   │  ║  ┌──────────────────┐    ┌──────────────────────────┐ ║  │  │ │
│   │   │  ║  │ Process Table    │    │ U-Area (struct user)     │ ║  │  │ │
│   │   │  ║  │ (struct proc)    │    │                          │ ║  │  │ │
│   │   │  ║  │                  │    │ • File descriptors       │ ║  │  │ │
│   │   │  ║  │ • State (p_stat) │───►│ • Signal handlers        │ ║  │  │ │
│   │   │  ║  │ • PID, PPID      │    │ • Current/root directory │ ║  │  │ │
│   │   │  ║  │ • Priority       │    │ • Resource limits        │ ║  │  │ │
│   │   │  ║  │ • Signals pending│    │ • Kernel stack           │ ║  │  │ │
│   │   │  ║  │ • Sleep address  │    │ • CPU time accounting    │ ║  │  │ │
│   │   │  ║  └──────────────────┘    └──────────────────────────┘ ║  │  │ │
│   │   │  ║           │                          │                 ║  │  │ │
│   │   │  ╚═══════════╪══════════════════════════╪═════════════════╝  │  │ │
│   │   │              │                          │                    │  │ │
│   │   │              ▼                          ▼                    │  │ │
│   │   │  ╔═══════════════════════════════════════════════════════╗  │  │ │
│   │   │  ║              VIRTUAL ADDRESS SPACE                     ║  │  │ │
│   │   │  ╠═══════════════════════════════════════════════════════╣  │  │ │
│   │   │  ║                                                        ║  │  │ │
│   │   │  ║  High ┌────────────────────────────────────────┐      ║  │  │ │
│   │   │  ║       │         KERNEL SPACE                   │      ║  │  │ │
│   │   │  ║       │    (kernel code, kernel data,          │      ║  │  │ │
│   │   │  ║       │     process tables, u-areas)           │      ║  │  │ │
│   │   │  ║       ├────────────────────────────────────────┤      ║  │  │ │
│   │   │  ║       │                                        │      ║  │  │ │
│   │   │  ║       │         STACK REGION                   │ ↓    ║  │  │ │
│   │   │  ║       │    (grows downward)                    │      ║  │  │ │
│   │   │  ║       │                                        │      ║  │  │ │
│   │   │  ║       ├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤      ║  │  │ │
│   │   │  ║       │         (unmapped space)               │      ║  │  │ │
│   │   │  ║       ├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤      ║  │  │ │
│   │   │  ║       │                                        │      ║  │  │ │
│   │   │  ║       │         HEAP                           │ ↑    ║  │  │ │
│   │   │  ║       │    (grows upward via brk/sbrk)         │      ║  │  │ │
│   │   │  ║       │                                        │      ║  │  │ │
│   │   │  ║       ├────────────────────────────────────────┤      ║  │  │ │
│   │   │  ║       │         BSS (uninitialized data)       │      ║  │  │ │
│   │   │  ║       ├────────────────────────────────────────┤      ║  │  │ │
│   │   │  ║       │         DATA (initialized data)        │      ║  │  │ │
│   │   │  ║       ├────────────────────────────────────────┤      ║  │  │ │
│   │   │  ║       │         TEXT (code)                    │      ║  │  │ │
│   │   │  ║       │    (read-only, shareable)              │      ║  │  │ │
│   │   │  ║  Low  └────────────────────────────────────────┘      ║  │  │ │
│   │   │  ║                                                        ║  │  │ │
│   │   │  ╚═══════════════════════════════════════════════════════╝  │  │ │
│   │   │                                                              │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   │   CONTEXT = User Context + Register Context + System Context        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 13. References

### Books

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED READING                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PRIMARY SOURCE:                                                          │
│   ────────────────                                                          │
│   • Maurice J. Bach, "The Design of the UNIX Operating System"            │
│     Prentice Hall, 1986                                                   │
│     - Chapter 6: The Structure of Processes                               │
│     - Chapter 7: Process Control                                          │
│     - Chapter 8: Process Scheduling and Time                              │
│     - The definitive reference for traditional UNIX process structures    │
│                                                                            │
│   UNIX PROGRAMMING:                                                        │
│   ─────────────────                                                         │
│   • W. Richard Stevens, "Advanced Programming in the UNIX Environment"   │
│     Addison-Wesley, 3rd Edition (with Stephen Rago)                       │
│     - Process environment, process control, signals                       │
│     - Practical programming perspective                                    │
│                                                                            │
│   LINUX KERNEL:                                                            │
│   ─────────────                                                             │
│   • Robert Love, "Linux Kernel Development"                               │
│     Addison-Wesley, 3rd Edition                                           │
│     - Chapter 3: Process Management                                       │
│     - Modern Linux task_struct and process implementation                 │
│                                                                            │
│   • Daniel P. Bovet & Marco Cesati, "Understanding the Linux Kernel"     │
│     O'Reilly, 3rd Edition                                                 │
│     - Chapter 3: Processes                                                │
│     - Deep dive into Linux process implementation                         │
│                                                                            │
│   LINUX PROGRAMMING:                                                       │
│   ──────────────────                                                        │
│   • Michael Kerrisk, "The Linux Programming Interface"                    │
│     No Starch Press, 2010                                                 │
│     - Chapters 24-28: Process creation, termination, signals             │
│     - Chapter 30: Thread groups, namespaces                               │
│     - The modern POSIX/Linux programming bible                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Source Files

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL SOURCE FILES                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TRADITIONAL UNIX (System V):                                            │
│   ────────────────────────────                                              │
│   • /usr/include/sys/proc.h     - struct proc definition                 │
│   • /usr/include/sys/user.h     - struct user (u-area) definition         │
│   • /usr/src/uts/*/os/fork.c    - fork() implementation                   │
│   • /usr/src/uts/*/os/exec.c    - exec() implementation                   │
│   • /usr/src/uts/*/os/exit.c    - exit() implementation                   │
│   • /usr/src/uts/*/os/sig.c     - Signal handling                         │
│                                                                            │
│   MODERN LINUX:                                                            │
│   ─────────────                                                             │
│   • include/linux/sched.h       - struct task_struct definition           │
│   • include/linux/cred.h        - struct cred (credentials)               │
│   • include/linux/mm_types.h    - struct mm_struct (memory)               │
│   • include/linux/fdtable.h     - struct files_struct (file descriptors) │
│   • include/linux/fs_struct.h   - struct fs_struct (filesystem info)     │
│   • include/linux/signal.h      - Signal definitions                      │
│   • include/linux/nsproxy.h     - struct nsproxy (namespaces)             │
│   • include/linux/cgroup.h      - Control groups                          │
│                                                                            │
│   • kernel/fork.c               - fork(), clone() implementation          │
│   • kernel/exec.c               - execve() implementation                 │
│   • kernel/exit.c               - exit(), wait() implementation           │
│   • kernel/signal.c             - Signal delivery                         │
│   • kernel/sched/core.c         - Scheduler core                          │
│   • kernel/pid.c                - PID allocation and management           │
│   • kernel/cred.c               - Credential management                   │
│   • kernel/nsproxy.c            - Namespace management                    │
│                                                                            │
│   View online at: https://elixir.bootlin.com/linux/latest/source         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Man Pages

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MAN PAGES                                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SYSTEM CALLS (Section 2):                                               │
│   ─────────────────────────                                                 │
│   • fork(2)      - Create child process                                   │
│   • clone(2)     - Create child process (Linux, with options)             │
│   • execve(2)    - Execute program                                        │
│   • _exit(2)     - Terminate process                                      │
│   • wait(2)      - Wait for child process                                 │
│   • waitpid(2)   - Wait for specific child                                │
│   • getpid(2)    - Get process ID                                         │
│   • getppid(2)   - Get parent process ID                                  │
│   • getpgrp(2)   - Get process group                                      │
│   • setpgid(2)   - Set process group                                      │
│   • getsid(2)    - Get session ID                                         │
│   • setsid(2)    - Create session                                         │
│   • getuid(2)    - Get user IDs                                           │
│   • setuid(2)    - Set user IDs                                           │
│   • signal(2)    - Signal handling (deprecated)                           │
│   • sigaction(2) - Signal handling (preferred)                            │
│   • kill(2)      - Send signal to process                                 │
│   • setrlimit(2) - Set resource limits                                    │
│   • unshare(2)   - Create new namespaces                                  │
│   • setns(2)     - Join namespace                                         │
│                                                                            │
│   LIBRARY FUNCTIONS (Section 3):                                          │
│   ──────────────────────────────                                            │
│   • exec(3)      - exec family functions                                  │
│   • exit(3)      - Exit process                                           │
│   • wait(3)      - Wait functions                                         │
│   • signal(3)    - Signal functions                                       │
│   • pthread_create(3) - Create thread                                     │
│                                                                            │
│   SPECIAL FILES (Section 5):                                              │
│   ──────────────────────────                                                │
│   • proc(5)      - /proc filesystem                                       │
│                                                                            │
│   OVERVIEW (Section 7):                                                   │
│   ─────────────────────                                                     │
│   • signal(7)    - Signal overview                                        │
│   • credentials(7) - Process credentials                                  │
│   • namespaces(7)  - Namespace overview                                   │
│   • cgroups(7)     - Control groups overview                              │
│   • pid_namespaces(7) - PID namespace details                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Online Resources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ONLINE RESOURCES                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   LINUX KERNEL:                                                            │
│   ─────────────                                                             │
│   • Linux Cross Reference (Elixir)                                        │
│     https://elixir.bootlin.com/linux/latest/source                        │
│     - Browse kernel source with cross-references                          │
│                                                                            │
│   • Linux Kernel Documentation                                            │
│     https://www.kernel.org/doc/html/latest/                               │
│     - Official kernel documentation                                        │
│                                                                            │
│   • LWN.net                                                                │
│     https://lwn.net/                                                       │
│     - In-depth Linux kernel news and analysis                             │
│                                                                            │
│   CONTAINERS:                                                              │
│   ───────────                                                               │
│   • Namespaces and cgroups: How containers work                           │
│     https://man7.org/linux/man-pages/man7/namespaces.7.html               │
│     https://man7.org/linux/man-pages/man7/cgroups.7.html                  │
│                                                                            │
│   HISTORICAL:                                                              │
│   ───────────                                                               │
│   • The Unix Heritage Society                                             │
│     https://www.tuhs.org/                                                  │
│     - Historical UNIX source code and documentation                       │
│                                                                            │
│   • Lions' Commentary on UNIX 6th Edition                                 │
│     - Classic source code walkthrough                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   "A process is an instance of a program in execution."                   │
│                                                                            │
│                                        — Maurice J. Bach, 1986            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```
