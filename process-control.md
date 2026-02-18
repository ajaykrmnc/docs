# Process Control

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Process Creation, Execution, Termination, Signals, and System Initialization

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [What is Process Control?](#what-is-process-control)
   - [The Process Control Subsystem](#the-process-control-subsystem)
   - [Historical Context](#historical-context)

2. [Process Creation: fork()](#2-process-creation-fork)
   - [The fork() System Call](#the-fork-system-call)
   - [Kernel Algorithm for fork()](#kernel-algorithm-for-fork)
   - [Copy-on-Write Optimization](#copy-on-write-optimization)
   - [vfork(): A Lightweight Alternative](#vfork-a-lightweight-alternative)
   - [clone(): The Linux Generalization](#clone-the-linux-generalization)

3. [Signals](#3-signals)
   - [What are Signals?](#what-are-signals)
   - [Signal Types and Sources](#signal-types-and-sources)
   - [Sending Signals: kill()](#sending-signals-kill)
   - [Signal Handling](#signal-handling)
   - [Kernel Algorithm for Signal Delivery](#kernel-algorithm-for-signal-delivery)
   - [Reliable Signals: sigaction()](#reliable-signals-sigaction)
   - [Signal Sets and Blocking](#signal-sets-and-blocking)

4. [Program Execution: exec()](#4-program-execution-exec)
   - [The exec() Family](#the-exec-family)
   - [Kernel Algorithm for exec()](#kernel-algorithm-for-exec)
   - [Executable File Formats](#executable-file-formats)
   - [The execve() Implementation](#the-execve-implementation)
   - [Environment and Arguments](#environment-and-arguments)

5. [Process Termination: exit()](#5-process-termination-exit)
   - [Voluntary vs Involuntary Termination](#voluntary-vs-involuntary-termination)
   - [The exit() System Call](#the-exit-system-call)
   - [Kernel Algorithm for exit()](#kernel-algorithm-for-exit)
   - [Resource Cleanup](#resource-cleanup)
   - [The Zombie State](#the-zombie-state)

6. [Awaiting Processes: wait()](#6-awaiting-processes-wait)
   - [The wait() System Call](#the-wait-system-call)
   - [Kernel Algorithm for wait()](#kernel-algorithm-for-wait)
   - [Wait Options and Variants](#wait-options-and-variants)
   - [Orphan Processes and init](#orphan-processes-and-init)

7. [Process Memory Management: brk()](#7-process-memory-management-brk)
   - [The Data Segment and Heap](#the-data-segment-and-heap)
   - [The brk() and sbrk() System Calls](#the-brk-and-sbrk-system-calls)
   - [Kernel Algorithm for brk()](#kernel-algorithm-for-brk)
   - [Modern Memory Allocation: mmap()](#modern-memory-allocation-mmap)

8. [The Shell](#8-the-shell)
   - [Shell Architecture](#shell-architecture)
   - [Command Execution](#command-execution)
   - [Pipelines](#pipelines)
   - [Job Control](#job-control)
   - [Background Processes](#background-processes)
   - [I/O Redirection](#io-redirection)

9. [System Initialization](#9-system-initialization)
   - [The Boot Process](#the-boot-process)
   - [Process 0: The Swapper/Scheduler](#process-0-the-swapperscheduler)
   - [Process 1: init](#process-1-init)
   - [The init Process Responsibilities](#the-init-process-responsibilities)
   - [Modern Init Systems: systemd](#modern-init-systems-systemd)

10. [Advanced Topics](#10-advanced-topics)
    - [Process Accounting](#process-accounting)
    - [setuid and setgid Programs](#setuid-and-setgid-programs)
    - [Process Limits: setrlimit()](#process-limits-setrlimit)
    - [Daemon Processes](#daemon-processes)

11. [Summary and Appendix](#11-summary-and-appendix)
    - [System Call Quick Reference](#system-call-quick-reference)
    - [Signal Quick Reference](#signal-quick-reference)
    - [The Big Picture](#the-big-picture)

12. [References](#12-references)

---

## 1. Introduction

### What is Process Control?

Process Control encompasses the mechanisms by which the Unix kernel creates, manages, transforms, and terminates processes. While "The Structure of a Process" describes what a process IS, Process Control describes what a process DOES—and what the kernel does to processes.

Maurice Bach describes process control as:

> "The kernel provides a set of system calls that allow processes to create new processes, execute programs, terminate, and synchronize with the termination of other processes."

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS CONTROL: THE LIFECYCLE                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │                         fork()                                      │ │
│   │                           │                                          │ │
│   │                           ▼                                          │ │
│   │    ┌──────────┐      ┌──────────┐      ┌──────────┐                │ │
│   │    │  Parent  │      │  Child   │      │  Child   │                │ │
│   │    │ Process  │─────►│ (copy)   │─────►│ (new     │                │ │
│   │    │          │      │          │      │ program) │                │ │
│   │    └──────────┘      └──────────┘      └──────────┘                │ │
│   │         │                                    │                      │ │
│   │         │                exec()              │                      │ │
│   │         │                                    │                      │ │
│   │         │            ┌──────────┐           │                      │ │
│   │         │            │  Zombie  │◄──────────┘                      │ │
│   │         │            │          │     exit()                       │ │
│   │         │            └──────────┘                                  │ │
│   │         │                  │                                        │ │
│   │         │                  │                                        │ │
│   │         └──────────────────┼────────────────────────────────────── │ │
│   │                            │ wait()                                 │ │
│   │                            ▼                                        │ │
│   │                     ┌──────────┐                                   │ │
│   │                     │ Reaped   │                                   │ │
│   │                     │ (gone)   │                                   │ │
│   │                     └──────────┘                                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Key System Calls:                                                       │
│   • fork()  - Create a new process (copy of parent)                       │
│   • exec()  - Replace process image with new program                      │
│   • exit()  - Terminate process, become zombie                            │
│   • wait()  - Reap zombie child, get exit status                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```





### The Process Control Subsystem

The process control subsystem is one of the three major subsystems of the Unix kernel (along with the file subsystem and the memory management subsystem). It manages:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX KERNEL ARCHITECTURE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                            USER PROGRAMS                                   │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                          SYSTEM CALL INTERFACE                             │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│                              KERNEL                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌──────────────────┐   ┌──────────────────────────────────────┐  │ │
│   │   │                  │   │                                       │  │ │
│   │   │   FILE           │   │   PROCESS CONTROL                    │  │ │
│   │   │   SUBSYSTEM      │◄─►│   SUBSYSTEM                          │  │ │
│   │   │                  │   │                                       │  │ │
│   │   │  • File I/O      │   │   • Process creation (fork)          │  │ │
│   │   │  • Buffers       │   │   • Process termination (exit)       │  │ │
│   │   │  • Inodes        │   │   • Program execution (exec)         │  │ │
│   │   │  • Directories   │   │   • Process synchronization (wait)   │  │ │
│   │   │                  │   │   • Signal handling                   │  │ │
│   │   └──────────────────┘   │   • Scheduling                        │  │ │
│   │            │             │                                       │  │ │
│   │            │             └──────────────────────────────────────┘  │ │
│   │            │                              │                         │ │
│   │            │                              │                         │ │
│   │            │          ┌───────────────────┘                        │ │
│   │            │          │                                             │ │
│   │            ▼          ▼                                             │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                                                              │  │ │
│   │   │              MEMORY MANAGEMENT SUBSYSTEM                    │  │ │
│   │   │                                                              │  │ │
│   │   │   • Page tables          • Demand paging                    │  │ │
│   │   │   • Swapping             • Memory allocation                │  │ │
│   │   │   • Region management    • Copy-on-write                    │  │ │
│   │   │                                                              │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                              HARDWARE                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

The process control subsystem interacts heavily with both other subsystems:
- **File Subsystem**: Processes inherit file descriptors, exec() reads executable files
- **Memory Management**: fork() duplicates address space, exec() creates new one, brk() extends it

### Historical Context

The evolution of process control mechanisms in Unix:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS CONTROL EVOLUTION                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1969-1971: FIRST EDITION UNIX (PDP-7, PDP-11)                          │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Basic fork() and exec() - Ken Thompson                                │
│   • Simple process table                                                  │
│   • No memory protection between processes                                │
│   • exit() and wait() for synchronization                                 │
│                                                                            │
│   1973-1975: FIFTH/SIXTH EDITION                                         │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Memory management improvements (swapping)                             │
│   • Signals introduced (simple version)                                   │
│   • Named pipes (FIFOs)                                                   │
│   • Lions' Commentary documents the source                                │
│                                                                            │
│   1979-1983: SEVENTH EDITION / SYSTEM III / BSD                          │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Berkeley job control (process groups, SIGTSTP)                        │
│   • vfork() for efficiency                                                │
│   • Demand paging replaces swapping (3BSD)                                │
│   • Reliable signals (4.2BSD)                                             │
│                                                                            │
│   1983-1985: SYSTEM V RELEASE 2/3                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   • Copy-on-Write optimization                                            │
│   • POSIX signals (sigaction)                                             │
│   • Session/process group refinements                                     │
│   • Maurice Bach documents the design                                     │
│                                                                            │
│   1990s: POSIX AND MODERN UNIX                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│   • POSIX.1 standardizes process control                                  │
│   • waitpid() for flexible child waiting                                  │
│   • Real-time signals                                                     │
│   • POSIX threads (pthreads)                                              │
│                                                                            │
│   2000s-PRESENT: LINUX EXTENSIONS                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   • clone() system call (configurable sharing)                            │
│   • Namespaces and cgroups                                                │
│   • signalfd(), pidfd (file descriptor APIs)                              │
│   • io_uring for async process control                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Process Creation: fork()

### The fork() System Call

The `fork()` system call creates a new process by duplicating the calling process. The new process, called the **child**, is an almost exact copy of the calling process, called the **parent**.

```c
#include <unistd.h>

pid_t fork(void);
```

**Return Values:**
- In **parent**: Returns child's PID (positive integer)
- In **child**: Returns 0
- On **error**: Returns -1 (only in parent, no child created)


```
┌───────────────────────────────────────────────────────────────────────────┐
│                    fork() RETURN VALUE MAGIC                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                        BEFORE fork()                                      │
│                                                                            │
│                      ┌─────────────┐                                      │
│                      │   Parent    │                                      │
│                      │   PID=100   │                                      │
│                      │             │                                      │
│                      │  pid = fork()                                      │
│                      │             │                                      │
│                      └──────┬──────┘                                      │
│                             │                                              │
│                        fork() called                                       │
│                             │                                              │
│                             ▼                                              │
│                                                                            │
│                        AFTER fork()                                       │
│                                                                            │
│            ┌─────────────────┴─────────────────┐                          │
│            │                                   │                          │
│            ▼                                   ▼                          │
│      ┌─────────────┐                    ┌─────────────┐                  │
│      │   Parent    │                    │    Child    │                  │
│      │   PID=100   │                    │   PID=101   │                  │
│      │             │                    │             │                  │
│      │  pid = 101  │ ◄─returns 101      │  pid = 0    │ ◄─returns 0     │
│      │  (child pid)│                    │             │                  │
│      └─────────────┘                    └─────────────┘                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Typical Usage Pattern:**

```c
pid_t pid = fork();

if (pid == -1) {
    /* Error - fork failed */
    perror("fork");
    exit(1);
}
else if (pid == 0) {
    /* Child process */
    printf("I am the child, my PID is %d\n", getpid());
    exec(...);  /* Usually replace with new program */
}
else {
    /* Parent process */
    printf("I am the parent, child PID is %d\n", pid);
    wait(NULL);  /* Wait for child to terminate */
}
```

**What is INHERITED by the child:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    fork() INHERITANCE                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   INHERITED (COPIED):                     NOT INHERITED (DIFFERENT):      │
│   ─────────────────────                   ──────────────────────────      │
│                                                                            │
│   • User and group IDs                    • Process ID (new PID)          │
│     (real, effective, saved)              • Parent PID (set to parent's)  │
│                                           • Return value from fork()      │
│   • Process group ID                        (0 in child, child PID in     │
│   • Session ID                               parent)                       │
│                                                                            │
│   • Controlling terminal                  • Pending signals (cleared)     │
│                                                                            │
│   • Current working directory             • File locks (NOT inherited)    │
│   • Root directory                                                         │
│                                           • CPU time counters (reset)     │
│   • File mode creation mask (umask)                                       │
│                                           • Pending alarms (cleared)      │
│   • Signal mask and signal dispositions                                    │
│                                           • Memory locks                   │
│   • File descriptors (pointing to                                          │
│     same open file descriptions)          • Pending asynchronous I/O      │
│                                                                            │
│   • Environment variables                                                  │
│                                                                            │
│   • Memory mappings (text, data, stack)                                   │
│                                                                            │
│   • Resource limits                                                        │
│                                                                            │
│   • Nice value                                                             │
│                                                                            │
│   • Attached shared memory segments                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Algorithm for fork()

Maurice Bach describes the fork() algorithm in detail. Here is the kernel's procedure:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ALGORITHM: fork()                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm fork                                                          │
│   input:  none                                                            │
│   output: to parent process - child PID                                   │
│           to child process  - 0                                           │
│                                                                            │
│   {                                                                        │
│       check for available kernel resources (process table slot);          │
│       check that user not running too many processes;                     │
│                                                                            │
│       get free proc table slot and unique PID;                            │
│       mark child state as "being created" (SIDL);                         │
│                                                                            │
│       copy data from parent proc table entry to child;                    │
│           /* p_pid, p_ppid, p_uid, p_stat, etc. */                       │
│                                                                            │
│       increment reference counts on:                                       │
│           current directory inode;                                         │
│           root directory inode;                                            │
│           parent's open files;                                             │
│                                                                            │
│       duplicate context of parent:                                         │
│           /* This is the expensive part */                                │
│           for each region attached to parent process                       │
│               if (region is shareable - like text)                        │
│                   increment region reference count;                        │
│                   attach child to region;                                  │
│               else  /* data, stack - need copy */                         │
│                   allocate new region for child;                           │
│                   attach child to new region;                              │
│                   copy region contents from parent;                        │
│                   /* OR: set up copy-on-write (modern) */                 │
│                                                                            │
│       push dummy system call layer onto child kernel stack;               │
│           /* So child can "return" from fork() */                         │
│                                                                            │
│       change child state to "ready to run" (SRUN);                        │
│                                                                            │
│       if (executing process is parent)                                    │
│           return(child PID);                                               │
│       else  /* executing process is child */                              │
│           initialize CPU time counters to 0;                               │
│           return(0);                                                       │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

The visual representation of the kernel data structures:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    fork() KERNEL DATA STRUCTURE CHANGES                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BEFORE fork():                                                          │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   PROCESS TABLE               USER AREA           MEMORY REGIONS          │
│   ┌─────────────┐           ┌───────────┐        ┌──────────────┐        │
│   │ proc[100]   │──────────►│ u-area    │        │ Text Region  │        │
│   │ p_pid=100   │           │ u_ofile[] │        │ ref_count=1  │        │
│   │ p_stat=SRUN │           │ u_cdir    │        └──────────────┘        │
│   │ p_uid=1000  │           │ u_signal[]│        ┌──────────────┐        │
│   └─────────────┘           └───────────┘        │ Data Region  │        │
│                                                   │ ref_count=1  │        │
│   ┌─────────────┐                                └──────────────┘        │
│   │ proc[???]   │                                ┌──────────────┐        │
│   │ (free slot) │                                │ Stack Region │        │
│   │             │                                │ ref_count=1  │        │
│   └─────────────┘                                └──────────────┘        │
│                                                                            │
│                                                                            │
│   AFTER fork():                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   PROCESS TABLE               USER AREAS          MEMORY REGIONS          │
│   ┌─────────────┐           ┌───────────┐        ┌──────────────┐        │
│   │ proc[100]   │──────────►│ parent    │   ┌──►│ Text Region  │◄──┐    │
│   │ p_pid=100   │           │ u-area    │   │   │ ref_count=2  │   │    │
│   │ p_stat=SRUN │           └───────────┘   │   └──────────────┘   │    │
│   │ p_uid=1000  │                │          │                       │    │
│   └─────────────┘                │          │   ┌──────────────┐   │    │
│         │                        │          ├──►│ Data (parent)│   │    │
│         │                        │          │   │ ref_count=1  │   │    │
│         ▼                        ▼          │   └──────────────┘   │    │
│   ┌─────────────┐           ┌───────────┐   │                       │    │
│   │ proc[101]   │──────────►│ child     │   │   ┌──────────────┐   │    │
│   │ p_pid=101   │           │ u-area    │   │   │ Data (child) │   │    │
│   │ p_ppid=100  │           │ (copy)    │   │   │ ref_count=1  │   │    │
│   │ p_stat=SRUN │           └───────────┘   │   └──────────────┘   │    │
│   │ p_uid=1000  │                │          │                       │    │
│   └─────────────┘                │          │   (similar for stack) │    │
│                                  │          │                       │    │
│                                  └──────────┴───────────────────────┘    │
│                                                                            │
│   Note: Text region is SHARED (read-only code)                            │
│         Data and stack regions are COPIED (or COW)                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Copy-on-Write Optimization

Traditional Unix systems physically copied the entire address space during fork(). This was expensive, especially since most fork() calls are immediately followed by exec(), which discards the copied memory anyway.

**Copy-on-Write (COW)** is an optimization that avoids unnecessary copying:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COPY-ON-WRITE (COW) MECHANISM                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STEP 1: After fork() - PAGES ARE SHARED, MARKED READ-ONLY              │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   PARENT                              CHILD                               │
│   Page Table                          Page Table                          │
│   ┌────────────────┐                 ┌────────────────┐                  │
│   │ VA 0x1000 → R  │────┐       ┌────│ VA 0x1000 → R  │                  │
│   │ VA 0x2000 → R  │───┐│       │┌───│ VA 0x2000 → R  │                  │
│   │ VA 0x3000 → R  │──┐││       │││┌─│ VA 0x3000 → R  │                  │
│   └────────────────┘  │││       ││││ └────────────────┘                  │
│                       │││       ││││                                      │
│                       ▼▼▼       ▼▼▼▼                                      │
│                     PHYSICAL MEMORY                                       │
│                   ┌──────────────────┐                                   │
│                   │ Page A (data)    │ ref_count = 2                     │
│                   │ Page B (data)    │ ref_count = 2                     │
│                   │ Page C (stack)   │ ref_count = 2                     │
│                   └──────────────────┘                                   │
│                                                                            │
│   Both processes point to SAME physical pages (read-only)                │
│   NO COPYING HAS OCCURRED YET                                             │
│                                                                            │
│                                                                            │
│   STEP 2: Child writes to page B - PAGE FAULT TRIGGERS COPY              │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   1. Child tries to write to VA 0x2000                                   │
│   2. Page is read-only → PAGE FAULT                                       │
│   3. Kernel sees this is a COW page (ref_count > 1)                       │
│   4. Kernel allocates NEW physical page                                   │
│   5. Kernel copies contents of Page B to new page                        │
│   6. Updates child's page table to point to new page (read-write)        │
│   7. Decrements ref_count on original page                                │
│   8. Child's write proceeds                                               │
│                                                                            │
│   PARENT                              CHILD                               │
│   Page Table                          Page Table                          │
│   ┌────────────────┐                 ┌────────────────┐                  │
│   │ VA 0x1000 → R  │────┐            │ VA 0x1000 → R  │────┐             │
│   │ VA 0x2000 → R  │────┼────────────┼────────────────┤    │             │
│   │ VA 0x3000 → R  │──┐ │            │ VA 0x2000 → RW │──┐ │             │
│   └────────────────┘  │ │            │ VA 0x3000 → R  │─┐│ │             │
│                       │ │            └────────────────┘ ││ │             │
│                       │ │                               ││ │             │
│                       ▼ ▼                               ▼▼ ▼             │
│                     PHYSICAL MEMORY                                       │
│                   ┌──────────────────┐                                   │
│                   │ Page A (shared)  │ ref_count = 2                     │
│                   │ Page B (parent)  │ ref_count = 1                     │
│                   │ Page B' (child)  │ ref_count = 1  ◄─NEW COPY         │
│                   │ Page C (shared)  │ ref_count = 2                     │
│                   └──────────────────┘                                   │
│                                                                            │
│   Only the MODIFIED page was copied. Unmodified pages remain shared.     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Why COW matters:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    fork() + exec() PATTERN                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SHELL EXECUTING A COMMAND:                                              │
│                                                                            │
│   $ ls -l /home                                                           │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                                                                   │   │
│   │   Shell (bash)                                                   │   │
│   │   Memory: 50 MB                                                  │   │
│   │                                                                   │   │
│   │   ┌────────────────────────────────────────────────────────────┐│   │
│   │   │ pid = fork();                                              ││   │
│   │   │ if (pid == 0) {                                            ││   │
│   │   │     exec("/bin/ls", "ls", "-l", "/home", NULL);            ││   │
│   │   │     /* ls is 100 KB, replaces entire address space */     ││   │
│   │   │ }                                                          ││   │
│   │   └────────────────────────────────────────────────────────────┘│   │
│   │                                                                   │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   WITHOUT COW:                          WITH COW:                         │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. fork() copies 50 MB               1. fork() creates page tables only│
│   2. exec() discards 50 MB             2. exec() discards references     │
│   3. exec() loads 100 KB               3. exec() loads 100 KB            │
│                                                                            │
│   WASTED: 50 MB copy                   WASTED: ~nothing (a few pages)    │
│   TIME: O(memory_size)                 TIME: O(page_table_size)          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### vfork(): A Lightweight Alternative

Before COW was widely implemented, BSD introduced `vfork()` as an optimization for the fork+exec pattern:

```c
#include <unistd.h>

pid_t vfork(void);
```

**vfork() characteristics:**
- Child **shares** parent's address space (no copy at all)
- Parent is **suspended** until child calls exec() or _exit()
- Child must NOT modify any data (undefined behavior)
- Child must NOT return from the function calling vfork()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    vfork() vs fork() COMPARISON                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   vfork():                                                                │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   1. Parent calls vfork()                                                 │
│      ┌─────────┐                                                          │
│      │ Parent  │ ─────►  SUSPENDED                                        │
│      │ memory  │                                                          │
│      └────┬────┘                                                          │
│           │                                                                │
│           │ SHARES (not copies)                                           │
│           │                                                                │
│           ▼                                                                │
│      ┌─────────┐                                                          │
│      │ Child   │ ─────►  RUNS (using parent's memory!)                    │
│      │ (no own │                                                          │
│      │ memory) │                                                          │
│      └─────────┘                                                          │
│                                                                            │
│   2. Child calls exec() or _exit()                                        │
│      - Child gets new address space (exec) or terminates (_exit)          │
│      - Parent resumes                                                      │
│                                                                            │
│   DANGER: If child modifies stack or data, it corrupts parent!           │
│                                                                            │
│   MODERN RECOMMENDATION:                                                   │
│   ─────────────────────────────────────────────────────────────────────── │
│   With COW-optimized fork(), vfork() offers little benefit and is        │
│   dangerous. Use fork() unless you have a specific reason not to.        │
│   POSIX.1-2008 marked vfork() as obsolete.                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### clone(): The Linux Generalization

Linux introduces `clone()` as a generalized process/thread creation system call. It allows fine-grained control over what is shared between parent and child:

```c
#include <sched.h>

int clone(int (*fn)(void *), void *stack, int flags, void *arg, ...);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    clone() FLAGS                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Flag               │ Effect                                             │
│   ───────────────────┼──────────────────────────────────────────────────  │
│   CLONE_VM           │ Share virtual memory (address space)               │
│   CLONE_FS           │ Share filesystem info (cwd, root, umask)          │
│   CLONE_FILES        │ Share file descriptor table                        │
│   CLONE_SIGHAND      │ Share signal handlers                              │
│   CLONE_THREAD       │ Same thread group (share PID externally)          │
│   CLONE_PARENT       │ Same parent as caller                              │
│   CLONE_NEWNS        │ New mount namespace                                 │
│   CLONE_NEWPID       │ New PID namespace                                   │
│   CLONE_NEWNET       │ New network namespace                               │
│   CLONE_NEWUSER      │ New user namespace                                  │
│                                                                            │
│   RELATIONSHIP TO fork() AND THREADS:                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   fork()  ≈  clone(0)                                                     │
│              No flags = copy everything (separate process)                │
│                                                                            │
│   pthread_create()  ≈  clone(CLONE_VM | CLONE_FS | CLONE_FILES |         │
│                              CLONE_SIGHAND | CLONE_THREAD)                │
│                        Share everything = thread                          │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │              THE clone() SPECTRUM                                   │ │
│   │                                                                      │ │
│   │   FULL PROCESS                                    FULL THREAD      │ │
│   │   (fork)                                          (pthread)        │ │
│   │      │                                                │             │ │
│   │      ▼                                                ▼             │ │
│   │   ┌──────────────────────────────────────────────────────────┐     │ │
│   │   │  ◄───────────────────────────────────────────────────►  │     │ │
│   │   │                                                          │     │ │
│   │   │  0 flags                               ALL sharing flags│     │ │
│   │   │  (copy all)                            (share all)      │     │ │
│   │   │                                                          │     │ │
│   │   │        Any combination in between is possible           │     │ │
│   │   │                                                          │     │ │
│   │   └──────────────────────────────────────────────────────────┘     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Signals

### What are Signals?

Signals are **software interrupts** that provide a mechanism for handling asynchronous events. They can be sent by the kernel, by another process, or by the process itself.

Maurice Bach describes signals as:

> "Signals inform processes of asynchronous events. Processes may send signals to each other via the kill system call, or the kernel may send signals internally."

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALS: SOFTWARE INTERRUPTS                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   SIGNAL SOURCES:                                                   │ │
│   │                                                                      │ │
│   │   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │ │
│   │   │   KERNEL    │     │   OTHER     │     │    SELF     │          │ │
│   │   │             │     │  PROCESS    │     │             │          │ │
│   │   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘          │ │
│   │          │                   │                   │                  │ │
│   │          │                   │                   │                  │ │
│   │          ▼                   ▼                   ▼                  │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │                                                                ││ │
│   │   │   SIGKILL    SIGINT (^C)    SIGTERM    SIGALRM    SIGUSR1    ││ │
│   │   │   SIGSEGV    SIGQUIT        SIGSTOP    SIGCHLD    SIGUSR2    ││ │
│   │   │   SIGFPE     SIGTSTP (^Z)   SIGCONT    SIGPIPE    ...        ││ │
│   │   │                                                                ││ │
│   │   └───────────────────────────────────────────────────────────────┘│ │
│   │                              │                                      │ │
│   │                              ▼                                      │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │                      TARGET PROCESS                            ││ │
│   │   │                                                                ││ │
│   │   │   Process handles signal in one of three ways:                ││ │
│   │   │                                                                ││ │
│   │   │   1. DEFAULT ACTION - terminate, core dump, ignore, stop      ││ │
│   │   │   2. IGNORE - signal discarded                                ││ │
│   │   │   3. CATCH - user-defined handler function called             ││ │
│   │   │                                                                ││ │
│   │   └───────────────────────────────────────────────────────────────┘│ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Signal Types and Sources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL TABLE                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Signal    │ Number │ Default   │ Source / Cause                        │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGHUP    │ 1      │ Terminate │ Terminal hangup or controlling       │
│             │        │           │ process death                          │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGINT    │ 2      │ Terminate │ Interrupt from keyboard (Ctrl+C)      │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGQUIT   │ 3      │ Core dump │ Quit from keyboard (Ctrl+\)           │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGILL    │ 4      │ Core dump │ Illegal instruction                    │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGTRAP   │ 5      │ Core dump │ Trace/breakpoint trap (debugger)      │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGABRT   │ 6      │ Core dump │ Abort signal from abort()             │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGBUS    │ 7      │ Core dump │ Bus error (bad memory access)         │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGFPE    │ 8      │ Core dump │ Floating-point exception              │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGKILL   │ 9      │ Terminate │ Kill signal (cannot be caught)        │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGUSR1   │ 10     │ Terminate │ User-defined signal 1                 │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGSEGV   │ 11     │ Core dump │ Segmentation fault (invalid memory)   │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGUSR2   │ 12     │ Terminate │ User-defined signal 2                 │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGPIPE   │ 13     │ Terminate │ Write to pipe with no reader          │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGALRM   │ 14     │ Terminate │ Timer signal from alarm()             │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGTERM   │ 15     │ Terminate │ Termination signal (polite kill)      │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGCHLD   │ 17     │ Ignore    │ Child stopped or terminated           │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGCONT   │ 18     │ Continue  │ Continue if stopped                    │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGSTOP   │ 19     │ Stop      │ Stop process (cannot be caught)       │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGTSTP   │ 20     │ Stop      │ Stop from terminal (Ctrl+Z)           │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGTTIN   │ 21     │ Stop      │ Background process reading tty        │
│   ──────────┼────────┼───────────┼──────────────────────────────────────  │
│   SIGTTOU   │ 22     │ Stop      │ Background process writing tty        │
│                                                                            │
│   Note: Signal numbers may vary across Unix variants                      │
│   SIGKILL (9) and SIGSTOP (19) CANNOT be caught or ignored               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Sending Signals: kill()

Despite its name, the `kill()` system call is the general mechanism for sending **any** signal to a process:

```c
#include <signal.h>

int kill(pid_t pid, int sig);
```

**The pid argument determines the target:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    kill() TARGET SELECTION                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   pid Value         │ Target                                              │
│   ──────────────────┼───────────────────────────────────────────────────  │
│   > 0               │ Process with that PID                               │
│   == 0              │ All processes in caller's process group            │
│   == -1             │ All processes caller has permission to signal      │
│   < -1              │ All processes in process group |pid|               │
│                                                                            │
│   EXAMPLES:                                                                │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   kill(1234, SIGTERM)    Send SIGTERM to process 1234                    │
│   kill(0, SIGINT)        Send SIGINT to all processes in my group        │
│   kill(-1, SIGKILL)      Kill all processes I can signal                 │
│   kill(-5678, SIGHUP)    Send SIGHUP to process group 5678               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Permission checking:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL PERMISSION RULES                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A process can send a signal to another process if:                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. Sender is SUPERUSER (root)                                     │ │
│   │      └──► Can signal ANY process                                    │ │
│   │                                                                      │ │
│   │   2. Sender's REAL or EFFECTIVE UID matches                         │ │
│   │      receiver's REAL or SAVED-SET UID                               │ │
│   │      └──► Normal inter-process signaling                            │ │
│   │                                                                      │ │
│   │   3. Special case: SIGCONT                                          │ │
│   │      └──► Can be sent to any process in same session               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL ALGORITHM (simplified):                                          │
│                                                                            │
│   algorithm kill                                                           │
│   input:  pid (target), sig (signal number)                               │
│   output: 0 on success, -1 on error                                       │
│   {                                                                        │
│       if (sig < 0 || sig >= NSIG)                                         │
│           return error(EINVAL);                                           │
│                                                                            │
│       if (pid > 0)                                                         │
│       {                                                                    │
│           p = find_process(pid);                                          │
│           if (p == NULL)                                                   │
│               return error(ESRCH);                                        │
│           if (!can_signal(current, p))                                    │
│               return error(EPERM);                                        │
│           send_signal(p, sig);                                            │
│       }                                                                    │
│       else if (pid == 0)                                                   │
│       {                                                                    │
│           for each process q in current->pgrp                              │
│               if (can_signal(current, q))                                  │
│                   send_signal(q, sig);                                    │
│       }                                                                    │
│       else if (pid == -1)                                                  │
│       {                                                                    │
│           for each process q (except init and self)                        │
│               if (can_signal(current, q))                                  │
│                   send_signal(q, sig);                                    │
│       }                                                                    │
│       else /* pid < -1 */                                                  │
│       {                                                                    │
│           pgrp = -pid;                                                     │
│           for each process q in pgrp                                       │
│               if (can_signal(current, q))                                  │
│                   send_signal(q, sig);                                    │
│       }                                                                    │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Related functions:**

```c
/* Send signal to own process */
int raise(int sig);          /* Equivalent to kill(getpid(), sig) */

/* Send signal to process group */
int killpg(pid_t pgrp, int sig);  /* Equivalent to kill(-pgrp, sig) */

/* Set alarm timer (sends SIGALRM) */
unsigned int alarm(unsigned int seconds);
```

### Signal Handling

A process can specify how each signal should be handled using `signal()` or `sigaction()`:

```c
#include <signal.h>

/* Traditional (unreliable) interface */
typedef void (*sighandler_t)(int);
sighandler_t signal(int signum, sighandler_t handler);

/* handler can be:
 *   SIG_DFL  - default action
 *   SIG_IGN  - ignore signal
 *   pointer  - user-defined function
 */
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL HANDLING EXAMPLE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <stdio.h>                                                       │
│   #include <signal.h>                                                      │
│   #include <unistd.h>                                                      │
│                                                                            │
│   void handler(int sig)                                                    │
│   {                                                                        │
│       printf("Caught signal %d\n", sig);                                  │
│   }                                                                        │
│                                                                            │
│   int main()                                                               │
│   {                                                                        │
│       /* Install handler for SIGINT */                                    │
│       signal(SIGINT, handler);                                            │
│                                                                            │
│       /* Ignore SIGQUIT */                                                │
│       signal(SIGQUIT, SIG_IGN);                                           │
│                                                                            │
│       /* Reset SIGTERM to default */                                      │
│       signal(SIGTERM, SIG_DFL);                                           │
│                                                                            │
│       printf("Press Ctrl+C...\n");                                        │
│       while (1)                                                            │
│           pause();  /* Wait for signal */                                 │
│                                                                            │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│   OUTPUT:                                                                  │
│   $ ./prog                                                                 │
│   Press Ctrl+C...                                                          │
│   ^CCaught signal 2                                                        │
│   ^CCaught signal 2                                                        │
│   ^\                           (SIGQUIT ignored)                          │
│   $ kill -TERM <pid>           (Process terminates - default action)     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Kernel Algorithm for Signal Delivery

Maurice Bach describes the signal delivery mechanism in detail. Signals are checked at specific points during process execution:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHEN ARE SIGNALS CHECKED?                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Signals are checked:                                              │ │
│   │                                                                      │ │
│   │   1. Just before returning to user mode from kernel mode            │ │
│   │      (after system call or interrupt)                               │ │
│   │                                                                      │ │
│   │   2. When entering or leaving a sleep state                         │ │
│   │      (interruptible sleeps can be interrupted by signals)          │ │
│   │                                                                      │ │
│   │   3. On context switch, before resuming a process                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   TIMELINE: Receiving a Signal                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────►   │
│                                                                            │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐       │
│   │ Process  │     │ Kernel   │     │ Signal   │     │ Return   │       │
│   │ in user  │────►│ handling │────►│ pending  │────►│ to user  │       │
│   │ mode     │     │ syscall  │     │ check    │     │ mode     │       │
│   └──────────┘     └──────────┘     └──────────┘     └────┬─────┘       │
│                                                           │              │
│                                                    Signal pending?       │
│                                            ┌─────────────┴─────────────┐ │
│                                            │                           │ │
│                                           YES                         NO │
│                                            │                           │ │
│                                            ▼                           ▼ │
│                                     ┌──────────────┐          ┌────────┐ │
│                                     │ Handle signal│          │Continue│ │
│                                     │ (issig/psig) │          │normally│ │
│                                     └──────────────┘          └────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**The key kernel functions:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL SIGNAL FUNCTIONS                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FUNCTION     │ PURPOSE                                                  │
│   ─────────────┼─────────────────────────────────────────────────────────│
│   psignal()    │ Posts (sends) a signal to a process                     │
│   issig()      │ Checks if current process has pending signal to handle  │
│   psig()       │ Performs the actual signal handling                     │
│   sendsig()    │ Sets up stack frame to call user handler                │
│                                                                            │
│                                                                            │
│   algorithm psignal  /* post signal to process */                         │
│   input:  process p, signal number sig                                    │
│   output: none                                                             │
│   {                                                                        │
│       set bit sig in p->p_sig;        /* mark signal pending */          │
│                                                                            │
│       if (p is sleeping at interruptible priority)                        │
│       {                                                                    │
│           setrun(p);                  /* wake it up */                    │
│       }                                                                    │
│                                                                            │
│       if (p is current process && signal not blocked)                     │
│       {                                                                    │
│           set need_signal flag for return to user mode;                   │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   algorithm issig  /* is there a signal to handle? */                     │
│   input:  none (operates on current process)                              │
│   output: signal number or 0                                               │
│   {                                                                        │
│       while (u.u_procp->p_sig != 0)                                       │
│       {                                                                    │
│           sig = find first bit set in p_sig;                              │
│                                                                            │
│           if (signal is blocked)                                          │
│               continue to next signal;                                    │
│                                                                            │
│           clear bit sig in p_sig;                                         │
│                                                                            │
│           if (action == SIG_IGN)                                          │
│               continue;               /* ignore it */                     │
│                                                                            │
│           return sig;                 /* found one to handle */           │
│       }                                                                    │
│       return 0;                       /* no signals */                    │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   algorithm psig  /* perform signal handling */                            │
│   input:  none (uses signal from issig)                                   │
│   output: none                                                             │
│   {                                                                        │
│       sig = u.u_cursig;                                                   │
│       action = u.u_signal[sig];                                           │
│                                                                            │
│       if (action == SIG_DFL)                                              │
│       {                                                                    │
│           /* Execute default action */                                    │
│           switch (sig)                                                    │
│           {                                                                │
│               case SIGKILL, SIGTERM, etc:                                 │
│                   exit();                                                 │
│               case SIGQUIT, SIGSEGV, etc:                                 │
│                   if (core dump enabled)                                  │
│                       core();                                             │
│                   exit();                                                 │
│               case SIGSTOP, SIGTSTP:                                      │
│                   stop process;                                           │
│               case SIGCONT:                                               │
│                   continue if stopped;                                    │
│           }                                                                │
│       }                                                                    │
│       else /* action is user function */                                  │
│       {                                                                    │
│           sendsig(action, sig);                                           │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Calling a user signal handler (sendsig):**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SENDSIG: CALLING USER HANDLER                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The kernel must arrange for the user's handler to be called,            │
│   then return to the interrupted code. This involves manipulating         │
│   the user's stack:                                                        │
│                                                                            │
│   BEFORE sendsig():                                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   User Stack                          Saved Registers (in kernel)         │
│   ┌─────────────────┐                 ┌─────────────────────────┐        │
│   │                 │                 │ PC = 0x4000 (where      │        │
│   │  (user's data)  │                 │      syscall was made)  │        │
│   │                 │                 │ SP = 0x7FFF0000         │        │
│   └─────────────────┘                 │ PSW = (user mode bits)  │        │
│         ▲                             └─────────────────────────┘        │
│         │                                                                  │
│        SP                                                                  │
│                                                                            │
│                                                                            │
│   AFTER sendsig():                                                         │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   User Stack                          Saved Registers (modified)          │
│   ┌─────────────────┐                 ┌─────────────────────────┐        │
│   │                 │                 │ PC = handler address    │        │
│   │  (user's data)  │                 │ SP = lower (stack grew) │        │
│   ├─────────────────┤                 │ PSW = (user mode bits)  │        │
│   │ return address  │ ◄── points to   └─────────────────────────┘        │
│   │ (sigreturn stub)│     trampoline                                      │
│   ├─────────────────┤                 When handler returns:               │
│   │ saved PC        │                 1. Trampoline calls sigreturn()    │
│   │ saved PSW       │                 2. Kernel restores original regs   │
│   │ saved signal #  │                 3. Process resumes at PC = 0x4000  │
│   ├─────────────────┤                                                      │
│   │ signal number   │ ◄── argument to handler                             │
│   └─────────────────┘                                                      │
│         ▲                                                                  │
│         │                                                                  │
│        SP (new)                                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Reliable Signals: sigaction()

The traditional `signal()` function has several problems that make it **unreliable**:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROBLEMS WITH signal()                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. HANDLER RESET                                                        │
│      ───────────────────────────────────────────────────────────────────  │
│      After a signal is caught, handler is reset to SIG_DFL               │
│      → Race condition: second signal may kill process                    │
│                                                                            │
│      void handler(int sig) {                                              │
│          signal(sig, handler);   /* Must reinstall! */                   │
│          /* ... but signal may arrive before reinstall */                │
│      }                                                                     │
│                                                                            │
│   2. NO BLOCKING DURING HANDLER                                           │
│      ───────────────────────────────────────────────────────────────────  │
│      Same signal can be delivered while handler is running               │
│      → Reentrant issues, stack overflow from nested handlers             │
│                                                                            │
│   3. INTERRUPTED SYSTEM CALLS                                             │
│      ───────────────────────────────────────────────────────────────────  │
│      Slow system calls (read, wait) are interrupted with EINTR           │
│      → Program must restart manually, complex error handling             │
│                                                                            │
│   4. NO ADDITIONAL INFORMATION                                            │
│      ───────────────────────────────────────────────────────────────────  │
│      Handler only receives signal number                                  │
│      → No info about who sent signal, fault address, etc.                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**sigaction() solves these problems:**

```c
#include <signal.h>

int sigaction(int signum, const struct sigaction *act,
              struct sigaction *oldact);

struct sigaction {
    void     (*sa_handler)(int);           /* Handler function */
    void     (*sa_sigaction)(int, siginfo_t *, void *);
                                            /* Extended handler */
    sigset_t   sa_mask;                    /* Signals to block */
    int        sa_flags;                   /* Options */
};
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sigaction() FLAGS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Flag           │ Effect                                                 │
│   ───────────────┼───────────────────────────────────────────────────────│
│   SA_RESTART     │ Automatically restart interrupted system calls        │
│   SA_SIGINFO     │ Use sa_sigaction handler with extra info              │
│   SA_NOCLDSTOP   │ Don't generate SIGCHLD when children stop            │
│   SA_NOCLDWAIT   │ Don't create zombie children                          │
│   SA_NODEFER     │ Don't block signal while handler runs                 │
│   SA_RESETHAND   │ Reset handler to SIG_DFL after catching               │
│   SA_ONSTACK     │ Use alternate signal stack                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Example using sigaction():**

```c
#include <stdio.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>

void handler(int sig, siginfo_t *info, void *ucontext)
{
    printf("Signal %d from PID %d\n", sig, info->si_pid);
}

int main()
{
    struct sigaction sa;

    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = handler;
    sa.sa_flags = SA_SIGINFO | SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sigaddset(&sa.sa_mask, SIGQUIT);  /* Block SIGQUIT during handler */

    sigaction(SIGINT, &sa, NULL);

    while (1) {
        pause();
    }
    return 0;
}
```

### Signal Sets and Blocking

POSIX introduced **signal sets** to manipulate groups of signals:

```c
#include <signal.h>

/* Initialize empty set */
int sigemptyset(sigset_t *set);

/* Initialize full set (all signals) */
int sigfillset(sigset_t *set);

/* Add signal to set */
int sigaddset(sigset_t *set, int signum);

/* Remove signal from set */
int sigdelset(sigset_t *set, int signum);

/* Test if signal is in set */
int sigismember(const sigset_t *set, int signum);
```

**Blocking signals with sigprocmask():**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL BLOCKING                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int sigprocmask(int how, const sigset_t *set, sigset_t *oldset);       │
│                                                                            │
│   HOW values:                                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│   SIG_BLOCK     │ Add set to current mask (mask = mask | set)            │
│   SIG_UNBLOCK   │ Remove set from mask (mask = mask & ~set)              │
│   SIG_SETMASK   │ Replace mask entirely (mask = set)                     │
│                                                                            │
│                                                                            │
│   BLOCKED vs PENDING:                                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Signal arrives         Is it blocked?                            │ │
│   │         │                      │                                    │ │
│   │         ▼                      ▼                                    │ │
│   │   ┌───────────────┐    ┌─────────────┐                            │ │
│   │   │ Mark as       │    │    YES      │────► Signal PENDING        │ │
│   │   │ PENDING       │    └──────┬──────┘      (stays in p_sig)      │ │
│   │   └───────────────┘           │                                    │ │
│   │                               │                                    │ │
│   │                         ┌─────▼─────┐                             │ │
│   │                         │    NO     │────► Deliver NOW            │ │
│   │                         └───────────┘                              │ │
│   │                                                                      │ │
│   │   When signal is UNBLOCKED:                                         │ │
│   │   If pending signal exists → deliver it immediately                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLE: Critical Section Protection                                    │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   sigset_t newmask, oldmask;                                              │
│                                                                            │
│   sigemptyset(&newmask);                                                  │
│   sigaddset(&newmask, SIGINT);                                            │
│   sigaddset(&newmask, SIGQUIT);                                           │
│                                                                            │
│   /* Block SIGINT and SIGQUIT */                                          │
│   sigprocmask(SIG_BLOCK, &newmask, &oldmask);                             │
│                                                                            │
│   /* Critical section - signals are deferred */                           │
│   update_shared_data();                                                   │
│                                                                            │
│   /* Restore previous mask */                                              │
│   sigprocmask(SIG_SETMASK, &oldmask, NULL);                               │
│   /* Any pending SIGINT/SIGQUIT delivered now */                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Related functions:**

```c
/* Check pending signals */
int sigpending(sigset_t *set);

/* Wait for a signal (atomically unblocking) */
int sigsuspend(const sigset_t *mask);

/* Wait for specific signals */
int sigwait(const sigset_t *set, int *sig);
int sigwaitinfo(const sigset_t *set, siginfo_t *info);
```

---

## 4. Program Execution: exec()

### The exec() Family

The `exec()` system calls **replace** the current process image with a new program:

```c
#include <unistd.h>

/* List arguments (l), path to executable */
int execl(const char *path, const char *arg0, ... /*, NULL */);

/* List arguments, search PATH */
int execlp(const char *file, const char *arg0, ... /*, NULL */);

/* List arguments, path, environment */
int execle(const char *path, const char *arg0, ... /*, NULL,
           char *const envp[] */);

/* Vector of arguments (v), path */
int execv(const char *path, char *const argv[]);

/* Vector, search PATH */
int execvp(const char *file, char *const argv[]);

/* Vector, path, environment */
int execve(const char *path, char *const argv[], char *const envp[]);
```



```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE exec() NAMING CONVENTION                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   exec + suffix:                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   l = list      Arguments passed as comma-separated list                  │
│   v = vector    Arguments passed as NULL-terminated array                 │
│   p = PATH      Search PATH environment variable for executable          │
│   e = environ   Pass explicit environment array                           │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   execve() is the ONLY actual system call                           │ │
│   │   All others are library wrappers that call execve()                │ │
│   │                                                                      │ │
│   │   execl()  ────┐                                                    │ │
│   │   execlp() ────┼──► convert to array ──► execve()                   │ │
│   │   execle() ────┘                                                    │ │
│   │                                                                      │ │
│   │   execv()  ────┐                                                    │ │
│   │   execvp() ────┴──► directly call ──► execve()                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**What happens during exec():**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    exec() TRANSFORMATION                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BEFORE exec():                     AFTER exec():                         │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   PID: 1234                          PID: 1234 (SAME!)                    │
│                                                                            │
│   ┌──────────────────────┐          ┌──────────────────────┐             │
│   │  bash (shell)        │          │  ls (new program)    │             │
│   ├──────────────────────┤          ├──────────────────────┤             │
│   │                      │          │                      │             │
│   │  TEXT: bash code     │          │  TEXT: ls code       │             │
│   │                      │          │                      │             │
│   │  DATA: bash globals  │  ═══►    │  DATA: ls globals    │             │
│   │                      │          │                      │             │
│   │  HEAP: malloc'd      │          │  HEAP: (empty)       │             │
│   │                      │          │                      │             │
│   │  STACK: bash stack   │          │  STACK: main args    │             │
│   │                      │          │                      │             │
│   └──────────────────────┘          └──────────────────────┘             │
│                                                                            │
│   The ENTIRE address space is replaced, but:                              │
│   - Same PID                                                               │
│   - Same parent                                                            │
│   - Same file descriptors (unless O_CLOEXEC)                              │
│   - Same process group and session                                        │
│   - Same working directory                                                 │
│   - Same umask                                                             │
│   - Same resource limits                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Algorithm for exec()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL ALGORITHM: exec()                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm exec                                                           │
│   input:  path to executable, argv[], envp[]                              │
│   output: no return on success, -1 on error                               │
│   {                                                                        │
│       /* 1. Get the executable file */                                    │
│       inode = namei(path);                                                │
│       if (inode == NULL)                                                   │
│           return error(ENOENT);                                           │
│                                                                            │
│       /* 2. Check permissions */                                          │
│       if (!executable(inode) || !can_read(inode))                         │
│           return error(EACCES);                                           │
│                                                                            │
│       /* 3. Read and verify executable header */                          │
│       read_header(inode, &header);                                        │
│       if (!valid_magic(header))                                           │
│           return error(ENOEXEC);                                          │
│                                                                            │
│       /* 4. Copy arguments to kernel space */                              │
│       /* (before destroying current address space) */                    │
│       copy_args_to_kernel(argv, envp);                                    │
│                                                                            │
│       /* 5. Point of no return - destroy old regions */                   │
│       detach_all_regions();                                               │
│                                                                            │
│       /* 6. Set up new address space */                                   │
│       attach_text_region(inode, header.text_offset);                      │
│       attach_data_region(inode, header.data_offset);                      │
│       allocate_stack_region();                                            │
│                                                                            │
│       /* 7. Set up stack with arguments */                                │
│       sp = setup_stack(argv, envp);                                       │
│                                                                            │
│       /* 8. Handle setuid/setgid */                                       │
│       if (inode->mode & S_ISUID)                                          │
│           u.u_uid = inode->uid;        /* Set effective UID */            │
│       if (inode->mode & S_ISGID)                                          │
│           u.u_gid = inode->gid;        /* Set effective GID */            │
│                                                                            │
│       /* 9. Reset signal handlers */                                       │
│       for (sig = 1; sig < NSIG; sig++)                                    │
│           if (u.u_signal[sig] != SIG_IGN)                                 │
│               u.u_signal[sig] = SIG_DFL;                                  │
│                                                                            │
│       /* 10. Close O_CLOEXEC file descriptors */                          │
│       for (fd = 0; fd < NOFILE; fd++)                                     │
│           if (u.u_pofile[fd] & UF_EXCLOSE)                                │
│               close(fd);                                                  │
│                                                                            │
│       /* 11. Set up entry point */                                         │
│       u.u_ar0[PC] = header.entry_point;                                   │
│       u.u_ar0[SP] = sp;                                                   │
│                                                                            │
│       /* Return to user mode starts executing new program */              │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Executable Formats

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EXECUTABLE FILE FORMATS                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   HISTORICAL:                                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│   a.out     Original Unix format (Assembler OUTput)                       │
│   COFF      Common Object File Format (System V)                          │
│                                                                            │
│   MODERN:                                                                  │
│   ─────────────────────────────────────────────────────────────────────── │
│   ELF       Executable and Linkable Format (Linux, most modern Unix)     │
│   Mach-O    Mach Object (macOS, iOS)                                      │
│                                                                            │
│                                                                            │
│   ELF FILE STRUCTURE:                                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌───────────────────────────────────┐                                   │
│   │         ELF Header                │ Magic: 0x7F 'E' 'L' 'F'          │
│   │    (identifies file type)         │ Class, Endianness, ABI           │
│   ├───────────────────────────────────┤                                   │
│   │      Program Header Table         │ Describes segments for loading   │
│   │     (for loading/execution)       │ - LOAD (text, data)              │
│   │                                   │ - INTERP (dynamic linker)        │
│   │                                   │ - DYNAMIC (shared libs)          │
│   ├───────────────────────────────────┤                                   │
│   │                                   │                                   │
│   │         .text section             │ Executable code                  │
│   │                                   │                                   │
│   ├───────────────────────────────────┤                                   │
│   │         .rodata section           │ Read-only data (strings)         │
│   ├───────────────────────────────────┤                                   │
│   │         .data section             │ Initialized data                 │
│   ├───────────────────────────────────┤                                   │
│   │         .bss section              │ Uninitialized data (zeroed)      │
│   ├───────────────────────────────────┤                                   │
│   │      Section Header Table         │ Describes all sections           │
│   │      (for linking/debugging)      │ (not needed at runtime)          │
│   └───────────────────────────────────┘                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 5. Process Termination: exit()

### How Processes End

A process can terminate in several ways:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WAYS A PROCESS CAN TERMINATE                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   VOLUNTARY (Normal):                                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. Return from main()                                                   │
│   2. Call exit()                                                          │
│   3. Call _exit() or _Exit()                                              │
│                                                                            │
│   INVOLUNTARY (Abnormal):                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│   4. Call abort()                            (sends SIGABRT)              │
│   5. Receive fatal signal (SIGKILL, SIGSEGV, etc.)                       │
│   6. Last thread exits or cancelled                                       │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   exit() vs _exit()                                                 │ │
│   │   ──────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   exit(status)                      _exit(status)                   │ │
│   │       │                                  │                          │ │
│   │       ▼                                  │                          │ │
│   │   Call atexit() handlers                │                          │ │
│   │       │                                  │                          │ │
│   │       ▼                                  │                          │ │
│   │   Flush stdio buffers                   │                          │ │
│   │       │                                  │                          │ │
│   │       ▼                                  │                          │ │
│   │   Close stdio streams                   │                          │ │
│   │       │                                  │                          │ │
│   │       ▼                                  ▼                          │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │       └──────────► _exit() system call ◄────────┘                  │ │
│   │                         │                                           │ │
│   │                         ▼                                           │ │
│   │                    KERNEL cleanup                                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Use _exit() in child after fork() if not calling exec()               │
│   (to avoid flushing parent's buffers twice)                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Algorithm for exit()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL ALGORITHM: exit()                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm exit                                                           │
│   input:  exit status                                                      │
│   output: never returns                                                    │
│   {                                                                        │
│       /* 1. Ignore all signals */                                         │
│       ignore_all_signals();                                               │
│                                                                            │
│       /* 2. Close all open files */                                       │
│       for (fd = 0; fd < NOFILE; fd++)                                     │
│           close(fd);                                                      │
│                                                                            │
│       /* 3. Release current directory and root directory */               │
│       iput(u.u_cdir);                                                     │
│       if (u.u_rdir)                                                        │
│           iput(u.u_rdir);                                                 │
│                                                                            │
│       /* 4. Detach all memory regions */                                  │
│       for each region r attached to process                                │
│       {                                                                    │
│           detach_region(r);                                               │
│           if (r->reference_count == 0)                                    │
│               free_region(r);                                             │
│       }                                                                    │
│                                                                            │
│       /* 5. Write accounting record */                                    │
│       if (accounting enabled)                                              │
│           write_accounting_record();                                      │
│                                                                            │
│       /* 6. Store exit status for parent */                               │
│       p->p_xstat = (status & 0xff) << 8;                                  │
│                                                                            │
│       /* 7. Send SIGCHLD to parent */                                     │
│       psignal(p->p_pptr, SIGCHLD);                                        │
│                                                                            │
│       /* 8. Reparent children to init (process 1) */                      │
│       for each child c of this process                                     │
│       {                                                                    │
│           c->p_pptr = &proc[1];        /* init */                         │
│                                                                            │
│           if (c->p_stat == SZOMB)                                         │
│               psignal(&proc[1], SIGCHLD);                                 │
│       }                                                                    │
│                                                                            │
│       /* 9. Change state to ZOMBIE */                                     │
│       p->p_stat = SZOMB;                                                  │
│                                                                            │
│       /* 10. Wake up parent if waiting */                                  │
│       wakeup(p->p_pptr);                                                  │
│                                                                            │
│       /* 11. Context switch - never returns */                            │
│       swtch();                                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Zombie State

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZOMBIE PROCESSES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When a process exits, it becomes a ZOMBIE until its parent              │
│   calls wait() to retrieve the exit status.                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   TIMELINE OF A ZOMBIE:                                             │ │
│   │                                                                      │ │
│   │   1. Process exits                                                  │ │
│   │      │                                                               │ │
│   │      ▼                                                               │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ ZOMBIE STATE                                                 │   │ │
│   │   │ - All resources released (memory, files, etc.)              │   │ │
│   │   │ - Only process table entry remains                          │   │ │
│   │   │ - Holds: PID, exit status, resource usage stats             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │      │                                                               │ │
│   │      │ Parent calls wait()                                          │ │
│   │      ▼                                                               │ │
│   │   2. Process table entry freed                                      │ │
│   │      PID can be reused                                              │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   WHAT IF PARENT NEVER CALLS wait()?                                │ │
│   │   ──────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   Zombie accumulates, wasting process table slots                   │ │
│   │   Too many zombies → cannot create new processes                    │ │
│   │                                                                      │ │
│   │   $ ps aux | grep Z                                                 │ │
│   │   user  1234  0.0  0.0  0  0  ?  Z  12:00  0:00 [defunct]          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTIONS TO ZOMBIE PROBLEM:                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. Parent calls wait() or waitpid()                                    │
│   2. Use SA_NOCLDWAIT flag in sigaction() for SIGCHLD                    │
│   3. Ignore SIGCHLD: signal(SIGCHLD, SIG_IGN)                            │
│   4. Double fork trick (grandchild orphaned to init)                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Awaiting Processes: wait()

### The wait() Family

```c
#include <sys/wait.h>

/* Wait for any child */
pid_t wait(int *status);

/* Wait for specific child with options */
pid_t waitpid(pid_t pid, int *status, int options);

/* Wait with rusage information */
pid_t wait3(int *status, int options, struct rusage *rusage);
pid_t wait4(pid_t pid, int *status, int options, struct rusage *rusage);

/* Modern: wait for specific state changes */
int waitid(idtype_t idtype, id_t id, siginfo_t *infop, int options);
```



### waitpid() Target Selection

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    waitpid() pid ARGUMENT                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   pid_t waitpid(pid_t pid, int *status, int options);                     │
│                                                                            │
│   ┌─────────────┬──────────────────────────────────────────────────────┐  │
│   │ pid value   │ Meaning                                              │  │
│   ├─────────────┼──────────────────────────────────────────────────────┤  │
│   │ pid > 0     │ Wait for specific child with this PID               │  │
│   │ pid == 0    │ Wait for any child in same process group            │  │
│   │ pid == -1   │ Wait for ANY child (same as wait())                 │  │
│   │ pid < -1    │ Wait for any child in process group |pid|           │  │
│   └─────────────┴──────────────────────────────────────────────────────┘  │
│                                                                            │
│   OPTIONS:                                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│   ┌─────────────┬──────────────────────────────────────────────────────┐  │
│   │ Option      │ Effect                                               │  │
│   ├─────────────┼──────────────────────────────────────────────────────┤  │
│   │ 0           │ Block until child terminates                        │  │
│   │ WNOHANG     │ Return immediately if no child has exited          │  │
│   │ WUNTRACED   │ Also return for stopped children (not just exited) │  │
│   │ WCONTINUED  │ Also return for continued children (Linux 2.6.10+)  │  │
│   └─────────────┴──────────────────────────────────────────────────────┘  │
│                                                                            │
│   Example: Non-blocking wait                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│   pid_t result = waitpid(-1, &status, WNOHANG);                          │
│   if (result > 0) {                                                       │
│       /* Child exited, result is the PID */                               │
│   } else if (result == 0) {                                               │
│       /* No child has exited yet */                                       │
│   } else {                                                                 │
│       /* Error: no children exist (ECHILD) */                             │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Status Examination Macros

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WAIT STATUS MACROS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The status returned by wait() is NOT just the exit code!                │
│   It's a bit field encoding HOW the process terminated.                   │
│                                                                            │
│   STATUS WORD FORMAT:                                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   For normal exit:                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │ 15      8 │ 7        0 │                                         │     │
│   │ exit code │    0x00    │                                         │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   For signal termination:                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │ 15      8 │ 7    │ 6    0 │                                      │     │
│   │   unused  │ core │ signal │                                      │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   For stopped process:                                                     │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │ 15      8 │ 7        0 │                                         │     │
│   │ stop sig  │    0x7F    │                                         │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│                                                                            │
│   USE THESE MACROS (don't decode manually):                               │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌───────────────────────┬────────────────────────────────────────────┐  │
│   │ Macro                 │ Description                                │  │
│   ├───────────────────────┼────────────────────────────────────────────┤  │
│   │ WIFEXITED(status)     │ True if exited normally (exit() or main)  │  │
│   │ WEXITSTATUS(status)   │ Exit code (0-255), use if WIFEXITED       │  │
│   │                       │                                            │  │
│   │ WIFSIGNALED(status)   │ True if terminated by a signal           │  │
│   │ WTERMSIG(status)      │ Signal number, use if WIFSIGNALED        │  │
│   │ WCOREDUMP(status)     │ True if core dump was produced           │  │
│   │                       │                                            │  │
│   │ WIFSTOPPED(status)    │ True if child is stopped                 │  │
│   │ WSTOPSIG(status)      │ Signal that stopped, use if WIFSTOPPED   │  │
│   │                       │                                            │  │
│   │ WIFCONTINUED(status)  │ True if child was continued (Linux)      │  │
│   └───────────────────────┴────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Typical wait() usage pattern:**

```c
#include <sys/wait.h>
#include <stdio.h>

pid_t pid;
int status;

pid = wait(&status);
if (pid == -1) {
    perror("wait");
    exit(1);
}

if (WIFEXITED(status)) {
    printf("Child %d exited normally with status %d\n",
           pid, WEXITSTATUS(status));
} else if (WIFSIGNALED(status)) {
    printf("Child %d killed by signal %d%s\n",
           pid, WTERMSIG(status),
           WCOREDUMP(status) ? " (core dumped)" : "");
} else if (WIFSTOPPED(status)) {
    printf("Child %d stopped by signal %d\n",
           pid, WSTOPSIG(status));
}
```

### Kernel Algorithm for wait()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL ALGORITHM: wait()                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm wait                                                           │
│   input:  pointer to status variable, options                              │
│   output: child PID, or -1 on error                                        │
│   {                                                                        │
│       loop:                                                                │
│           found = false;                                                   │
│                                                                            │
│           /* Search through all processes */                               │
│           for each process p in process table                              │
│           {                                                                │
│               if (p->p_pptr != current_process)                           │
│                   continue;       /* Not our child */                     │
│                                                                            │
│               found = true;       /* We have at least one child */        │
│                                                                            │
│               /* Check if this child matches our criteria */               │
│               if (!matches_pid_criteria(p, pid_arg))                      │
│                   continue;                                                │
│                                                                            │
│               /* Case 1: Child is a zombie - collect it */                │
│               if (p->p_stat == SZOMB)                                     │
│               {                                                            │
│                   *status = p->p_xstat;                                   │
│                   child_pid = p->p_pid;                                   │
│                                                                            │
│                   /* Add child's CPU time to parent */                    │
│                   u.u_cutime += p->p_utime;                               │
│                   u.u_cstime += p->p_stime;                               │
│                                                                            │
│                   /* Free process table slot */                           │
│                   p->p_stat = NULL;                                       │
│                   return child_pid;                                       │
│               }                                                            │
│                                                                            │
│               /* Case 2: Child is stopped (if WUNTRACED set) */          │
│               if ((options & WUNTRACED) && p->p_stat == SSTOP)           │
│               {                                                            │
│                   *status = (p->p_xstat << 8) | 0x7F;                     │
│                   return p->p_pid;                                        │
│               }                                                            │
│           }                                                                │
│                                                                            │
│           /* No matching children found */                                 │
│           if (!found)                                                      │
│               return error(ECHILD);   /* No children at all */            │
│                                                                            │
│           /* Non-blocking mode? */                                         │
│           if (options & WNOHANG)                                          │
│               return 0;               /* No child ready */                │
│                                                                            │
│           /* Sleep until a child changes state */                         │
│           sleep(current_process, PWAIT);                                  │
│           goto loop;                                                       │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Orphan Processes and init Adoption

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ORPHAN PROCESSES                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   What happens when a parent exits before its children?                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BEFORE PARENT EXIT:                                               │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │          ┌──────────┐                                               │ │
│   │          │  init    │ PID 1                                         │ │
│   │          │ (PID 1)  │                                               │ │
│   │          └────┬─────┘                                               │ │
│   │               │                                                      │ │
│   │          ┌────▼─────┐                                               │ │
│   │          │  Parent  │ PID 100                                       │ │
│   │          └────┬─────┘                                               │ │
│   │          ┌────┴────┐                                                │ │
│   │     ┌────▼───┐ ┌───▼────┐                                          │ │
│   │     │ Child1 │ │ Child2 │ PIDs 101, 102                            │ │
│   │     └────────┘ └────────┘                                          │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   AFTER PARENT EXIT:                                                │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │          ┌──────────┐                                               │ │
│   │          │  init    │ PID 1                                         │ │
│   │          │ (PID 1)  │                                               │ │
│   │          └────┬─────┘                                               │ │
│   │          ┌────┴────────────┐                                        │ │
│   │     ┌────▼───┐        ┌───▼────┐                                   │ │
│   │     │ Child1 │        │ Child2 │  Children adopted by init         │ │
│   │     └────────┘        └────────┘                                   │ │
│   │                                                                      │ │
│   │   The kernel sets p->p_pptr = &proc[1] for all orphaned children   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY init?                                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. init never exits (if it does, kernel panics)                        │
│   2. init always calls wait() to reap zombie children                    │
│   3. This prevents orphaned processes from becoming permanent zombies    │
│                                                                            │
│   LINUX: SUBREAPER PROCESSES (prctl PR_SET_CHILD_SUBREAPER)              │
│   ─────────────────────────────────────────────────────────────────────── │
│   Modern Linux allows a process to become a "subreaper" for its          │
│   descendants. Orphaned children are adopted by the nearest subreaper    │
│   ancestor instead of init. Useful for process supervisors.              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Process Memory Management: brk() and sbrk()

### The Heap and Dynamic Memory

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS MEMORY AND THE HEAP                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                    PROCESS ADDRESS SPACE                         │     │
│   ├─────────────────────────────────────────────────────────────────┤     │
│   │                                                                  │     │
│   │   High Address                                                   │     │
│   │   ┌─────────────────────────────────────────────────────────┐   │     │
│   │   │              STACK                                       │   │     │
│   │   │         (grows downward ↓)                               │   │     │
│   │   │                                                          │   │     │
│   │   │              │                                           │   │     │
│   │   │              ▼                                           │   │     │
│   │   ├─────────────────────────────────────────────────────────┤   │     │
│   │   │                                                          │   │     │
│   │   │         (unmapped space)                                 │   │     │
│   │   │                                                          │   │     │
│   │   ├─────────────────────────────────────────────────────────┤   │     │
│   │   │              ▲                                           │   │     │
│   │   │              │                                           │   │     │
│   │   │         (grows upward ↑)                                 │   │     │
│   │   │              HEAP                                        │   │     │
│   │   ├─────────────────────────────────────────────────────────┤   │     │
│   │   │   brk → ═══════════════════════════════════════════════ │   │     │
│   │   │              BSS (uninitialized data, zeroed)           │   │     │
│   │   ├─────────────────────────────────────────────────────────┤   │     │
│   │   │              DATA (initialized globals)                  │   │     │
│   │   ├─────────────────────────────────────────────────────────┤   │     │
│   │   │              TEXT (program code)                         │   │     │
│   │   └─────────────────────────────────────────────────────────┘   │     │
│   │   Low Address                                                    │     │
│   │                                                                  │     │
│   │   brk = "program break" = end of data segment                   │     │
│   │                                                                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### brk() and sbrk() System Calls

```c
#include <unistd.h>

/* Set the program break to a specific address */
int brk(void *addr);

/* Increment the program break by 'increment' bytes */
/* Returns the PREVIOUS break address (old end of heap) */
void *sbrk(intptr_t increment);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    brk() and sbrk() OPERATION                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   sbrk(0)     Returns current program break (useful for debugging)       │
│   sbrk(n)     Extends heap by n bytes, returns old break                 │
│   sbrk(-n)    Shrinks heap by n bytes (rarely used)                      │
│   brk(addr)   Sets break to specific address                              │
│                                                                            │
│   Example: How malloc() might use sbrk()                                  │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   BEFORE:                           AFTER sbrk(4096):                     │
│                                                                            │
│   │           │                     │           │                         │
│   │  (free)   │                     │  (free)   │                         │
│   ├───────────┤                     ├───────────┤                         │
│   │           │                     │           │                         │
│   │   heap    │                     │   heap    │                         │
│   │           │                     │           │                         │
│   ├───────────┤ ← brk               │ new alloc │                         │
│   │    bss    │                     ├───────────┤ ← old brk               │
│   │    data   │                     │    bss    │                         │
│   │    text   │                     │    data   │                         │
│                                     │    text   │                         │
│                                     ├───────────┤ ← new brk (+4096)       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Kernel Algorithm for brk()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL ALGORITHM: brk()                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm brk                                                            │
│   input:  new_break (desired end of data segment)                         │
│   output: 0 on success, -1 on error                                        │
│   {                                                                        │
│       /* 1. Validate the new break address */                             │
│       if (new_break < end_of_bss)                                         │
│           return error(ENOMEM);  /* Can't shrink below BSS */             │
│                                                                            │
│       if (new_break >= stack_limit)                                        │
│           return error(ENOMEM);  /* Would collide with stack */           │
│                                                                            │
│       /* 2. Check resource limits */                                       │
│       new_size = new_break - start_of_data;                               │
│       if (new_size > u.u_rlimit[RLIMIT_DATA])                             │
│           return error(ENOMEM);                                           │
│                                                                            │
│       /* 3. Calculate pages needed */                                      │
│       current_pages = (u.u_break - start) / PAGE_SIZE;                    │
│       new_pages = (new_break - start) / PAGE_SIZE;                        │
│                                                                            │
│       /* 4. Grow or shrink the data region */                             │
│       if (new_pages > current_pages)                                       │
│       {                                                                    │
│           /* Allocate new pages */                                         │
│           for (page = current_pages; page < new_pages; page++)            │
│           {                                                                │
│               pte = allocate_page();                                      │
│               if (pte == NULL)                                            │
│                   return error(ENOMEM);                                   │
│               /* Pages are zero-filled on first access */                 │
│           }                                                                │
│       }                                                                    │
│       else if (new_pages < current_pages)                                 │
│       {                                                                    │
│           /* Free excess pages */                                          │
│           for (page = new_pages; page < current_pages; page++)            │
│               free_page(page);                                            │
│       }                                                                    │
│                                                                            │
│       /* 5. Update break address */                                        │
│       u.u_break = new_break;                                              │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Modern Alternative: mmap()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    mmap() vs brk() FOR MEMORY ALLOCATION                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Modern malloc() implementations use BOTH:                               │
│                                                                            │
│   ┌────────────────────────┬────────────────────────────────────────────┐ │
│   │ Allocation Size        │ Method                                     │ │
│   ├────────────────────────┼────────────────────────────────────────────┤ │
│   │ Small (< 128KB)        │ brk()/sbrk() - extend heap                │ │
│   │ Large (≥ 128KB)        │ mmap() - separate memory region           │ │
│   └────────────────────────┴────────────────────────────────────────────┘ │
│                                                                            │
│   WHY mmap() FOR LARGE ALLOCATIONS?                                       │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. Can be unmapped independently (returned to OS)                      │
│   2. No fragmentation in the heap                                        │
│   3. Can be placed at any address                                        │
│   4. Can use huge pages (2MB, 1GB)                                       │
│                                                                            │
│   WHY brk() FOR SMALL ALLOCATIONS?                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. Less system call overhead                                            │
│   2. Better cache locality                                                │
│   3. No per-mapping kernel overhead                                       │
│                                                                            │
│                                                                            │
│   mmap() ANONYMOUS MEMORY:                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   void *ptr = mmap(NULL,                /* Let kernel choose address */  │
│                    size,                /* Allocation size */             │
│                    PROT_READ|PROT_WRITE, /* Read/write access */         │
│                    MAP_PRIVATE|MAP_ANONYMOUS, /* Private, no file */     │
│                    -1, 0);              /* No file descriptor */         │
│                                                                            │
│   munmap(ptr, size);                    /* Return memory to OS */        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. The Shell: Command Interpreter

### What is the Shell?

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE UNIX SHELL                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The shell is a USER-LEVEL PROGRAM that:                                 │
│   1. Reads commands from the user (or a script)                           │
│   2. Parses the command line                                              │
│   3. Creates child processes to execute programs                          │
│   4. Manages I/O redirection and pipelines                                │
│   5. Provides job control (foreground/background)                         │
│                                                                            │
│   The shell is NOT part of the kernel - it's just another program        │
│   that uses the process control system calls we've discussed.            │
│                                                                            │
│   COMMON SHELLS:                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│   sh      Bourne Shell (original, 1979)                                   │
│   csh     C Shell (BSD, 1978)                                             │
│   ksh     Korn Shell (1983)                                               │
│   bash    Bourne Again Shell (GNU, 1989)                                  │
│   zsh     Z Shell (1990)                                                  │
│   fish    Friendly Interactive Shell (2005)                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Shell Main Loop

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIMPLIFIED SHELL MAIN LOOP                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   while (1)                                                                │
│   {                                                                        │
│       /* 1. Print prompt */                                               │
│       print_prompt();                                                     │
│                                                                            │
│       /* 2. Read command line */                                          │
│       line = read_line();                                                 │
│       if (line == NULL)                 /* EOF (Ctrl-D) */               │
│           exit(0);                                                        │
│                                                                            │
│       /* 3. Parse command line */                                         │
│       cmd = parse(line);                                                  │
│                                                                            │
│       /* 4. Handle built-in commands */                                   │
│       if (is_builtin(cmd))                                                │
│       {                                                                    │
│           execute_builtin(cmd);         /* cd, export, exit, etc. */     │
│           continue;                                                       │
│       }                                                                    │
│                                                                            │
│       /* 5. Fork a child process */                                       │
│       pid = fork();                                                       │
│       if (pid == 0)                                                        │
│       {                                                                    │
│           /* Child: execute the command */                                │
│           setup_redirections(cmd);                                        │
│           execvp(cmd->argv[0], cmd->argv);                               │
│           perror(cmd->argv[0]);         /* exec failed */                │
│           exit(127);                                                      │
│       }                                                                    │
│                                                                            │
│       /* 6. Parent: wait for child (if foreground) */                     │
│       if (!cmd->background)                                               │
│           waitpid(pid, &status, 0);                                       │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### I/O Redirection

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHELL I/O REDIRECTION                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The shell sets up I/O redirection AFTER fork() but BEFORE exec()       │
│                                                                            │
│   $ command < input.txt > output.txt 2> error.txt                        │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   /* In child process, before exec() */                                   │
│                                                                            │
│   /* Redirect stdin from file */                                          │
│   fd = open("input.txt", O_RDONLY);                                       │
│   dup2(fd, STDIN_FILENO);    /* fd now becomes fd 0 */                   │
│   close(fd);                  /* Close original fd */                     │
│                                                                            │
│   /* Redirect stdout to file */                                           │
│   fd = open("output.txt", O_WRONLY|O_CREAT|O_TRUNC, 0644);               │
│   dup2(fd, STDOUT_FILENO);   /* fd now becomes fd 1 */                   │
│   close(fd);                                                              │
│                                                                            │
│   /* Redirect stderr to file */                                           │
│   fd = open("error.txt", O_WRONLY|O_CREAT|O_TRUNC, 0644);                │
│   dup2(fd, STDERR_FILENO);   /* fd now becomes fd 2 */                   │
│   close(fd);                                                              │
│                                                                            │
│   exec(command);  /* New program inherits these file descriptors */      │
│                                                                            │
│                                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │                  WHY THIS WORKS                                   │   │
│   │                                                                    │   │
│   │  1. fork() copies file descriptor table                          │   │
│   │  2. Child modifies ITS OWN descriptor table                      │   │
│   │  3. exec() preserves file descriptors (unless O_CLOEXEC)        │   │
│   │  4. New program uses fds 0,1,2 without knowing about redirection │   │
│   │                                                                    │   │
│   │  The program doesn't need to know about redirection!             │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Pipelines

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHELL PIPELINES                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   $ ls -la | grep "\.c$" | wc -l                                         │
│                                                                            │
│   This creates THREE processes connected by TWO pipes:                    │
│                                                                            │
│   ┌─────────┐    pipe[0]    ┌─────────┐    pipe[1]    ┌─────────┐        │
│   │   ls    │ ──────────► │  grep   │ ──────────► │   wc    │        │
│   │  -la   │  stdout→stdin │  "\.c$" │  stdout→stdin │   -l    │        │
│   └─────────┘              └─────────┘              └─────────┘        │
│                                                                            │
│   SHELL ALGORITHM FOR PIPELINE:                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   /* For pipeline: cmd1 | cmd2 | cmd3 */                                  │
│                                                                            │
│   for (i = 0; i < num_commands; i++)                                      │
│   {                                                                        │
│       if (i < num_commands - 1)                                           │
│           pipe(pipes[i]);       /* Create pipe for output */             │
│                                                                            │
│       pid[i] = fork();                                                    │
│       if (pid[i] == 0)                                                    │
│       {                                                                    │
│           /* Set up input from previous pipe */                           │
│           if (i > 0) {                                                    │
│               dup2(pipes[i-1][0], STDIN_FILENO);                         │
│               close(pipes[i-1][0]);                                       │
│               close(pipes[i-1][1]);                                       │
│           }                                                                │
│                                                                            │
│           /* Set up output to next pipe */                                │
│           if (i < num_commands - 1) {                                     │
│               dup2(pipes[i][1], STDOUT_FILENO);                          │
│               close(pipes[i][0]);                                         │
│               close(pipes[i][1]);                                         │
│           }                                                                │
│                                                                            │
│           exec(commands[i]);                                              │
│       }                                                                    │
│                                                                            │
│       /* Parent: close pipe ends we don't need */                         │
│       if (i > 0) {                                                        │
│           close(pipes[i-1][0]);                                           │
│           close(pipes[i-1][1]);                                           │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   /* Wait for all children */                                              │
│   for (i = 0; i < num_commands; i++)                                      │
│       waitpid(pid[i], &status[i], 0);                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Job Control

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    JOB CONTROL                                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   $ sleep 100 &                    # Run in background                    │
│   [1] 12345                        # Job 1, PID 12345                     │
│   $ fg %1                          # Bring to foreground                  │
│   $ ^Z                             # Ctrl-Z: suspend (SIGTSTP)           │
│   [1]+ Stopped    sleep 100                                               │
│   $ bg %1                          # Resume in background                 │
│   $ jobs                           # List jobs                            │
│   [1]+  Running   sleep 100 &                                             │
│                                                                            │
│   PROCESS GROUPS AND SESSIONS:                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                         SESSION                                    │  │
│   │                    (session leader: login shell)                   │  │
│   │                                                                     │  │
│   │   ┌────────────────────┐   ┌──────────────────┐                   │  │
│   │   │  Foreground PGRP   │   │ Background PGRP  │                   │  │
│   │   │  (receives ^C, ^Z) │   │ (job 1)          │                   │  │
│   │   │                    │   │                  │                   │  │
│   │   │  ┌──────┐ ┌──────┐ │   │  ┌──────────┐   │  ┌──────────────┐ │  │
│   │   │  │ vim  │ │(pipe)│ │   │  │ sleep 100│   │  │ Background   │ │  │
│   │   │  └──────┘ └──────┘ │   │  └──────────┘   │  │ PGRP (job 2) │ │  │
│   │   └────────────────────┘   └──────────────────┘  └──────────────┘ │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   KEY CONCEPTS:                                                            │
│   - Each pipeline is a process group                                     │
│   - Terminal has ONE foreground process group                            │
│   - ^C sends SIGINT to foreground process group                         │
│   - ^Z sends SIGTSTP to foreground process group                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 9. System Initialization

### The Boot Process

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX BOOT SEQUENCE                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │  1. HARDWARE POWER-ON                                               │ │
│   │     └──► BIOS/UEFI initializes hardware                            │ │
│   │                                                                      │ │
│   │  2. BOOTLOADER (GRUB, LILO, etc.)                                   │ │
│   │     └──► Loads kernel into memory                                   │ │
│   │     └──► Passes boot parameters                                     │ │
│   │                                                                      │ │
│   │  3. KERNEL INITIALIZATION                                           │ │
│   │     └──► start_kernel() runs                                        │ │
│   │     └──► Initialize memory management                               │ │
│   │     └──► Initialize process scheduler                               │ │
│   │     └──► Mount root filesystem                                      │ │
│   │     └──► Create process 0 (swapper/idle)                           │ │
│   │                                                                      │ │
│   │  4. PROCESS 0 (swapper/idle)                                        │ │
│   │     └──► The kernel "process" - handles idle CPU                   │ │
│   │     └──► fork()s to create process 1                               │ │
│   │                                                                      │ │
│   │  5. PROCESS 1 (init/systemd)                                        │ │
│   │     └──► First USER-MODE process                                    │ │
│   │     └──► Parent of all other processes                              │ │
│   │     └──► Reads configuration, starts services                       │ │
│   │                                                                      │ │
│   │  6. GETTY/LOGIN PROCESSES                                           │ │
│   │     └──► Wait for user login on terminals                          │ │
│   │                                                                      │ │
│   │  7. USER LOGIN SHELL                                                │ │
│   │     └──► User's interactive session begins                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Process 0: The Swapper

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS 0: THE SWAPPER                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Process 0 is UNIQUE - it's the only process not created by fork()      │
│                                                                            │
│   TRADITIONAL UNIX (Bach's book):                                         │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Called "swapper" because it manages process swapping                 │
│   - Created by hand-crafting its process table entry                     │
│   - Runs the "sched" routine in an infinite loop                         │
│   - Swaps processes in/out of memory as needed                           │
│                                                                            │
│   MODERN LINUX:                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Called "idle" process (PID 0)                                        │
│   - One per CPU (idle/0, idle/1, etc.)                                   │
│   - Runs when no other process is runnable                               │
│   - Executes HLT instruction (puts CPU in low-power state)               │
│                                                                            │
│   KERNEL BOOTSTRAP CODE (simplified):                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   void start_kernel(void)                                                 │
│   {                                                                        │
│       init_memory();                                                      │
│       init_scheduler();                                                   │
│       init_interrupts();                                                  │
│       ...                                                                  │
│                                                                            │
│       /* Create process 1 */                                               │
│       kernel_thread(init, NULL, CLONE_FS | CLONE_FILES);                 │
│                                                                            │
│       /* Process 0 becomes idle loop */                                   │
│       cpu_idle();     /* Never returns */                                 │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Process 1: init

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS 1: init                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Process 1 is the ANCESTOR OF ALL USER PROCESSES                        │
│                                                                            │
│   RESPONSIBILITIES:                                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. Read system configuration                                            │
│   2. Start system services (daemons)                                      │
│   3. Spawn getty processes for terminals                                  │
│   4. Adopt orphaned processes                                             │
│   5. Reap zombie processes                                                │
│   6. Handle system shutdown                                               │
│                                                                            │
│   TRADITIONAL init (/etc/inittab):                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   - SysV init: runlevels (0-6), /etc/rc.d scripts                        │
│   - BSD init: /etc/rc scripts                                             │
│                                                                            │
│   MODERN init SYSTEMS:                                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│   ┌──────────────┬─────────────────────────────────────────────────────┐  │
│   │ System       │ Description                                         │  │
│   ├──────────────┼─────────────────────────────────────────────────────┤  │
│   │ systemd      │ Most Linux distros (parallel startup, socket act.) │  │
│   │ launchd      │ macOS (plist files, on-demand services)            │  │
│   │ upstart      │ Ubuntu (until 15.04), event-based                  │  │
│   │ OpenRC       │ Gentoo, dependency-based                            │  │
│   │ runit        │ Minimal, supervision-based                          │  │
│   └──────────────┴─────────────────────────────────────────────────────┘  │
│                                                                            │
│   WHY init MUST NEVER EXIT:                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│   - If init exits, kernel panics (no one to adopt orphans)               │
│   - init is protected: can only be killed by SIGKILL if it wants        │
│   - Signals to init are special-cased in the kernel                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Login Process

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE LOGIN SEQUENCE                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   init (PID 1)                                                      │ │
│   │       │                                                              │ │
│   │       │ fork()+exec("/sbin/getty")                                  │ │
│   │       ▼                                                              │ │
│   │   getty (PID 100)              Opens terminal device               │ │
│   │       │                        Displays "login: " prompt           │ │
│   │       │                        Reads username                       │ │
│   │       │ exec("/bin/login")                                          │ │
│   │       ▼                                                              │ │
│   │   login (PID 100)              Prompts for password                │ │
│   │       │                        Validates credentials               │ │
│   │       │                        Sets UID/GID                         │ │
│   │       │                        Sets up environment                  │ │
│   │       │ exec("/bin/bash")                                           │ │
│   │       ▼                                                              │ │
│   │   bash (PID 100)               User's login shell                  │ │
│   │       │                        Reads .bashrc, .profile             │ │
│   │       │                        Accepts commands                     │ │
│   │       │                                                              │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │   Note: PID stays the same through exec() chain                    │ │
│   │   getty → login → shell all have PID 100                          │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHEN USER LOGS OUT:                                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│   1. Shell exits                                                          │
│   2. init receives SIGCHLD                                                │
│   3. init reaps the zombie                                                │
│   4. init fork()s a new getty for that terminal                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 10. Advanced Topics

### setuid and setgid Programs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SETUID AND SETGID PROGRAMS                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Programs can run with ELEVATED PRIVILEGES when needed                   │
│                                                                            │
│   THE PROBLEM:                                                             │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Regular users need to do privileged operations sometimes             │
│   - Example: change their password (requires writing /etc/shadow)        │
│   - Can't give everyone root access!                                     │
│                                                                            │
│   THE SOLUTION: setuid bit                                                │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   $ ls -l /usr/bin/passwd                                                 │
│   -rwsr-xr-x 1 root root 54256 Jan 1 2024 /usr/bin/passwd                │
│        ^                                                                   │
│        └── 's' instead of 'x' = setuid bit                               │
│                                                                            │
│   When executed:                                                           │
│   - Real UID = user who ran it (e.g., 1000)                              │
│   - Effective UID = owner of file (root = 0)                             │
│   - Process runs with ROOT privileges!                                    │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   ┌─────────────┐                    ┌─────────────┐                      │
│   │   alice     │    exec(passwd)    │   passwd    │                      │
│   │   UID=1000  │ ─────────────────► │  RUID=1000  │                      │
│   │             │                    │  EUID=0     │ ← runs as root       │
│   └─────────────┘                    └─────────────┘                      │
│                                                                            │
│   THE THREE UIDs:                                                          │
│   ┌──────────────┬──────────────────────────────────────────────────────┐ │
│   │ Real UID     │ Who actually started the process                     │ │
│   │ Effective UID│ Used for permission checks                           │ │
│   │ Saved UID    │ Copy of EUID at exec time (for dropping/regaining)  │ │
│   └──────────────┴──────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON SETUID PROGRAMS:                                                  │
│   ┌────────────────┬───────────────────────────────────────────────────┐  │
│   │ /usr/bin/passwd│ Change password (writes /etc/shadow)              │  │
│   │ /usr/bin/su    │ Switch user                                        │  │
│   │ /usr/bin/sudo  │ Execute as another user                           │  │
│   │ /bin/ping      │ Send ICMP packets (needs raw socket)              │  │
│   │ /usr/bin/crontab│ Edit crontab files                               │  │
│   └────────────────┴───────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Privilege Dropping

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PRIVILEGE DROPPING                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Setuid programs should DROP privileges as soon as possible             │
│                                                                            │
│   PRINCIPLE OF LEAST PRIVILEGE:                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Get elevated privileges                                               │
│   - Do the privileged operation                                           │
│   - Drop back to normal privileges immediately                           │
│   - Continue running with minimal permissions                            │
│                                                                            │
│   EXAMPLE: Web server binding to port 80                                  │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   int main()                                                               │
│   {                                                                        │
│       /* Running as root (started by init) */                             │
│       int sock = socket(AF_INET, SOCK_STREAM, 0);                        │
│       bind(sock, ..., 80);  /* Requires root for port < 1024 */          │
│       listen(sock, ...);                                                  │
│                                                                            │
│       /* IMMEDIATELY drop privileges */                                   │
│       setgid(NOBODY_GID);   /* Change GID first */                       │
│       setuid(NOBODY_UID);   /* Then UID (can't go back!) */              │
│                                                                            │
│       /* Now running as "nobody" user */                                  │
│       /* If exploited, attacker only has "nobody" privileges */          │
│       while (1) {                                                         │
│           accept_and_handle_request(sock);                                │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   FUNCTIONS FOR CHANGING CREDENTIALS:                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│   ┌────────────────┬──────────────────────────────────────────────────┐   │
│   │ setuid(uid)    │ Set real, effective, and saved UID (if root)   │   │
│   │ seteuid(uid)   │ Set only effective UID                          │   │
│   │ setreuid(r,e)  │ Set real and effective UIDs                     │   │
│   │ setresuid(r,e,s)│ Set real, effective, and saved UIDs (Linux)   │   │
│   │ setgid(gid)    │ Same as setuid but for groups                   │   │
│   └────────────────┴──────────────────────────────────────────────────┘   │
│                                                                            │
│   ⚠️  WARNING: Order matters!                                              │
│   - setgid() before setuid()                                              │
│   - After setuid(non-root), you CANNOT regain root privileges           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Resource Limits

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RESOURCE LIMITS                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Kernel limits how many resources a process can consume                  │
│                                                                            │
│   SYSTEM CALLS:                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│   #include <sys/resource.h>                                                │
│                                                                            │
│   int getrlimit(int resource, struct rlimit *rlim);                       │
│   int setrlimit(int resource, const struct rlimit *rlim);                │
│                                                                            │
│   struct rlimit {                                                          │
│       rlim_t rlim_cur;    /* Soft limit (current) */                      │
│       rlim_t rlim_max;    /* Hard limit (ceiling) */                      │
│   };                                                                       │
│                                                                            │
│   SOFT vs HARD LIMITS:                                                    │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Soft limit: enforced by kernel, can be raised by process             │
│   - Hard limit: maximum value for soft limit                              │
│   - Only root can raise hard limits                                       │
│                                                                            │
│   COMMON RESOURCES:                                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   ┌─────────────────┬─────────────────────────────────────────────────┐   │
│   │ Resource        │ Description                                     │   │
│   ├─────────────────┼─────────────────────────────────────────────────┤   │
│   │ RLIMIT_CPU      │ CPU time in seconds                             │   │
│   │ RLIMIT_FSIZE    │ Maximum file size                               │   │
│   │ RLIMIT_DATA     │ Maximum data segment size (heap)               │   │
│   │ RLIMIT_STACK    │ Maximum stack size                              │   │
│   │ RLIMIT_CORE     │ Maximum core dump size                          │   │
│   │ RLIMIT_NOFILE   │ Maximum number of open files                   │   │
│   │ RLIMIT_AS       │ Maximum address space (virtual memory)         │   │
│   │ RLIMIT_NPROC    │ Maximum number of processes                     │   │
│   │ RLIMIT_MEMLOCK  │ Maximum locked memory                           │   │
│   └─────────────────┴─────────────────────────────────────────────────┘   │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   /* Prevent fork bombs */                                                │
│   struct rlimit rl;                                                        │
│   rl.rlim_cur = 100;     /* Soft limit: 100 processes */                 │
│   rl.rlim_max = 100;     /* Hard limit: 100 processes */                 │
│   setrlimit(RLIMIT_NPROC, &rl);                                           │
│                                                                            │
│   SHELL INTERFACE:                                                         │
│   ─────────────────────────────────────────────────────────────────────── │
│   $ ulimit -a              # Show all limits                              │
│   $ ulimit -n 1024         # Set max open files to 1024                   │
│   $ ulimit -u 100          # Set max processes to 100                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Creating Daemon Processes

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CREATING DAEMON PROCESSES                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A daemon is a process that runs in the BACKGROUND, detached from       │
│   any controlling terminal                                                 │
│                                                                            │
│   CHARACTERISTICS OF A DAEMON:                                             │
│   ─────────────────────────────────────────────────────────────────────── │
│   - No controlling terminal                                               │
│   - Usually started at boot time                                          │
│   - Runs with superuser privileges (often)                                │
│   - Parent is init (PID 1)                                                │
│   - Working directory is typically /                                      │
│   - stdin, stdout, stderr closed or redirected                           │
│                                                                            │
│   TRADITIONAL DAEMON CREATION (the "double fork" technique):             │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   void daemonize(void)                                                    │
│   {                                                                        │
│       pid_t pid;                                                          │
│                                                                            │
│       /* STEP 1: Fork and exit parent */                                  │
│       pid = fork();                                                       │
│       if (pid > 0) exit(0);   /* Parent exits */                         │
│       if (pid < 0) exit(1);   /* Fork failed */                          │
│                                                                            │
│       /* Child continues... */                                            │
│                                                                            │
│       /* STEP 2: Create new session */                                    │
│       setsid();    /* Becomes session leader, no controlling tty */     │
│                                                                            │
│       /* STEP 3: Fork AGAIN (prevents reacquiring tty) */                │
│       pid = fork();                                                       │
│       if (pid > 0) exit(0);   /* First child exits */                    │
│       if (pid < 0) exit(1);                                               │
│                                                                            │
│       /* Grandchild continues as daemon... */                             │
│                                                                            │
│       /* STEP 4: Set file mode creation mask */                           │
│       umask(0);                                                           │
│                                                                            │
│       /* STEP 5: Change working directory to root */                      │
│       chdir("/");                                                         │
│                                                                            │
│       /* STEP 6: Close all open file descriptors */                       │
│       for (int fd = 0; fd < sysconf(_SC_OPEN_MAX); fd++)                 │
│           close(fd);                                                      │
│                                                                            │
│       /* STEP 7: Redirect stdin, stdout, stderr to /dev/null */          │
│       open("/dev/null", O_RDONLY);  /* stdin  = fd 0 */                  │
│       open("/dev/null", O_WRONLY);  /* stdout = fd 1 */                  │
│       open("/dev/null", O_WRONLY);  /* stderr = fd 2 */                  │
│   }                                                                        │
│                                                                            │
│   WHY DOUBLE FORK?                                                         │
│   ─────────────────────────────────────────────────────────────────────── │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │  Parent ──fork()──► Child ──setsid()──► Session leader            │  │
│   │   (exit)              │                    │                       │  │
│   │                       │                    │  Problem: session     │  │
│   │                       │                    │  leader CAN acquire   │  │
│   │                       │                    │  a controlling tty    │  │
│   │                       │                    │                       │  │
│   │                       └──fork()──► Grandchild (not session leader) │  │
│   │                          (exit)       │                            │  │
│   │                                       │  Safe: can NEVER get      │  │
│   │                                       │  a controlling terminal   │  │
│   │                                       ▼                            │  │
│   │                                    DAEMON                          │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   MODERN ALTERNATIVE: systemd                                             │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Don't daemonize! Let systemd handle it                               │
│   - Just write to stdout/stderr, systemd captures logs                   │
│   - Type=simple in unit file                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Process Accounting

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS ACCOUNTING                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The kernel can record information about every process that runs        │
│                                                                            │
│   WHAT IS RECORDED:                                                        │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Command name                                                          │
│   - User and group IDs                                                    │
│   - CPU time used (user + system)                                        │
│   - Elapsed time                                                          │
│   - Memory usage                                                          │
│   - I/O counts                                                            │
│   - Start time                                                            │
│   - Controlling terminal                                                  │
│   - Exit status                                                           │
│                                                                            │
│   THE ACCOUNTING RECORD (struct acct):                                    │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   struct acct {                                                           │
│       char     ac_flag;      /* Flags */                                 │
│       char     ac_comm[8];   /* Command name */                          │
│       comp_t   ac_utime;     /* User CPU time */                         │
│       comp_t   ac_stime;     /* System CPU time */                       │
│       comp_t   ac_etime;     /* Elapsed time */                          │
│       time_t   ac_btime;     /* Begin time */                            │
│       uid_t    ac_uid;       /* User ID */                               │
│       gid_t    ac_gid;       /* Group ID */                              │
│       dev_t    ac_tty;       /* Controlling terminal */                  │
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
│   ENABLING ACCOUNTING:                                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│   # Enable accounting to a file                                           │
│   $ accton /var/account/pacct                                             │
│                                                                            │
│   # Disable accounting                                                     │
│   $ accton                                                                 │
│                                                                            │
│   TOOLS:                                                                   │
│   ─────────────────────────────────────────────────────────────────────── │
│   ┌────────────┬───────────────────────────────────────────────────────┐  │
│   │ lastcomm   │ Show last commands executed                           │  │
│   │ sa         │ Summary of accounting data by user/command           │  │
│   │ accton     │ Turn accounting on/off                                │  │
│   │ dump-acct  │ Print accounting file                                 │  │
│   └────────────┴───────────────────────────────────────────────────────┘  │
│                                                                            │
│   EXAMPLE OUTPUT (lastcomm):                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│   $ lastcomm                                                              │
│   cat            alice    pts/0      0.00 secs Sun Feb 13 10:15          │
│   ls             alice    pts/0      0.01 secs Sun Feb 13 10:15          │
│   bash      F    alice    pts/0      0.10 secs Sun Feb 13 10:00          │
│          ^                                                                 │
│          └── F = forked but didn't exec                                  │
│                                                                            │
│   USE CASES:                                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│   - Billing (shared systems)                                              │
│   - Security auditing                                                     │
│   - Performance analysis                                                  │
│   - Capacity planning                                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 11. Summary and Appendix

### Process Control System Calls Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS CONTROL SYSTEM CALLS                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROCESS CREATION:                                                        │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ fork()      │ Create child process (copy of parent)              │   │
│   │ vfork()     │ Create child, share parent address space (legacy) │   │
│   │ clone()     │ Create child with fine-grained sharing (Linux)    │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   PROGRAM EXECUTION:                                                       │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ execve()    │ Replace process image (THE actual syscall)        │   │
│   │ execl()     │ execve() with arg list                             │   │
│   │ execv()     │ execve() with arg vector                           │   │
│   │ execle()    │ execve() with arg list + environment              │   │
│   │ execve()    │ execve() with arg vector + environment            │   │
│   │ execlp()    │ execve() with arg list + PATH search              │   │
│   │ execvp()    │ execve() with arg vector + PATH search            │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   PROCESS TERMINATION:                                                     │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ exit()      │ Terminate with cleanup (library function)         │   │
│   │ _exit()     │ Terminate immediately (no cleanup)                │   │
│   │ abort()     │ Terminate with SIGABRT                             │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   WAITING FOR CHILDREN:                                                   │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ wait()      │ Wait for any child                                 │   │
│   │ waitpid()   │ Wait for specific child (with options)            │   │
│   │ waitid()    │ More flexible wait (POSIX)                        │   │
│   │ wait3()     │ wait() + resource usage (BSD)                     │   │
│   │ wait4()     │ waitpid() + resource usage (BSD)                  │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   SIGNALS:                                                                 │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ kill()      │ Send signal to process(es)                        │   │
│   │ raise()     │ Send signal to self                                │   │
│   │ signal()    │ Set signal handler (simple)                       │   │
│   │ sigaction() │ Set signal handler (reliable)                     │   │
│   │ sigprocmask()│ Block/unblock signals                            │   │
│   │ sigpending()│ Get pending signals                                │   │
│   │ sigsuspend()│ Wait for signal                                    │   │
│   │ sigwait()   │ Synchronously wait for signal                     │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   PROCESS INFORMATION:                                                     │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ getpid()    │ Get process ID                                     │   │
│   │ getppid()   │ Get parent process ID                              │   │
│   │ getpgrp()   │ Get process group ID                               │   │
│   │ getsid()    │ Get session ID                                     │   │
│   │ getuid()    │ Get real user ID                                   │   │
│   │ geteuid()   │ Get effective user ID                              │   │
│   │ getgid()    │ Get real group ID                                  │   │
│   │ getegid()   │ Get effective group ID                             │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   PROCESS GROUPS AND SESSIONS:                                            │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ setpgid()   │ Set process group ID                               │   │
│   │ setsid()    │ Create new session                                 │   │
│   │ tcgetpgrp() │ Get foreground process group of terminal          │   │
│   │ tcsetpgrp() │ Set foreground process group of terminal          │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   CREDENTIALS:                                                             │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ setuid()    │ Set user ID                                        │   │
│   │ seteuid()   │ Set effective user ID                              │   │
│   │ setreuid()  │ Set real and effective user IDs                   │   │
│   │ setresuid() │ Set real, effective, and saved UIDs (Linux)       │   │
│   │ setgid()    │ Set group ID                                       │   │
│   │ setgroups() │ Set supplementary group IDs                       │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   RESOURCE LIMITS:                                                        │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ getrlimit() │ Get resource limits                                │   │
│   │ setrlimit() │ Set resource limits                                │   │
│   │ getrusage() │ Get resource usage                                 │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   MEMORY:                                                                  │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ brk()       │ Set data segment size                              │   │
│   │ sbrk()      │ Increment data segment (library function)         │   │
│   │ mmap()      │ Map memory                                         │   │
│   │ munmap()    │ Unmap memory                                       │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Signal Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMMON SIGNALS QUICK REFERENCE                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────┬──────┬─────────────────────────────────────────────────────┐ │
│   │ Signal │ Num  │ Description                              │ Default │ │
│   ├────────┼──────┼──────────────────────────────────────────┼─────────┤ │
│   │ SIGHUP │  1   │ Hangup (terminal closed)                │ Term    │ │
│   │ SIGINT │  2   │ Interrupt (Ctrl-C)                      │ Term    │ │
│   │ SIGQUIT│  3   │ Quit (Ctrl-\)                           │ Core    │ │
│   │ SIGILL │  4   │ Illegal instruction                     │ Core    │ │
│   │ SIGTRAP│  5   │ Trace/breakpoint trap                   │ Core    │ │
│   │ SIGABRT│  6   │ Abort (abort())                         │ Core    │ │
│   │ SIGFPE │  8   │ Floating point exception                │ Core    │ │
│   │ SIGKILL│  9   │ Kill (cannot catch!)                    │ Term    │ │
│   │ SIGSEGV│ 11   │ Segmentation fault                      │ Core    │ │
│   │ SIGPIPE│ 13   │ Broken pipe                             │ Term    │ │
│   │ SIGALRM│ 14   │ Alarm clock (alarm())                   │ Term    │ │
│   │ SIGTERM│ 15   │ Termination (graceful shutdown)        │ Term    │ │
│   │ SIGCHLD│ 17   │ Child status changed                    │ Ignore  │ │
│   │ SIGCONT│ 18   │ Continue if stopped                     │ Cont    │ │
│   │ SIGSTOP│ 19   │ Stop (cannot catch!)                    │ Stop    │ │
│   │ SIGTSTP│ 20   │ Stop from terminal (Ctrl-Z)            │ Stop    │ │
│   │ SIGUSR1│ 10   │ User-defined signal 1                   │ Term    │ │
│   │ SIGUSR2│ 12   │ User-defined signal 2                   │ Term    │ │
│   └────────┴──────┴──────────────────────────────────────────┴─────────┘ │
│                                                                            │
│   DEFAULT ACTIONS:                                                         │
│   - Term = Terminate process                                              │
│   - Core = Terminate process + core dump                                  │
│   - Stop = Stop (suspend) process                                        │
│   - Cont = Continue if stopped, else ignore                              │
│   - Ignore = Ignore signal                                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### The Big Picture: Process Life Cycle

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│           THE COMPLETE PROCESS CONTROL LIFE CYCLE                         │
│                                                                            │
│                           ┌─────────────────────────────────┐             │
│                           │                                  │             │
│                           │          KERNEL                 │             │
│                           │                                  │             │
│                           │  ┌─────────────────────────────┐│             │
│                           │  │ Process Table (task_struct) ││             │
│                           │  │                              ││             │
│                           │  │  PID  State    Parent  ...  ││             │
│                           │  │  ───  ─────    ──────  ───  ││             │
│                           │  │   1   RUNNING    0          ││             │
│                           │  │  100  RUNNING    1          ││             │
│                           │  │  101  SLEEPING  100         ││             │
│                           │  │  102  ZOMBIE   100         ││             │
│                           │  │                              ││             │
│                           │  └─────────────────────────────┘│             │
│                           │                                  │             │
│                           └─────────────────────────────────┘             │
│                                           │                                │
│                                           │                                │
│  ═══════════════════════════════════════════════════════════════════════  │
│                                USER SPACE                                  │
│  ═══════════════════════════════════════════════════════════════════════  │
│                                                                            │
│                                                                            │
│     ┌──────────────────────────────────────────────────────────────────┐  │
│     │                                                                   │  │
│     │                     PROCESS LIFE CYCLE                           │  │
│     │                                                                   │  │
│     │   ┌─────────┐     fork()      ┌─────────────────────────────┐   │  │
│     │   │ PARENT  │ ───────────────►│        CHILD                │   │  │
│     │   │ PROCESS │                 │   (copy of parent)          │   │  │
│     │   └─────────┘                 └─────────────────────────────┘   │  │
│     │       │                                    │                     │  │
│     │       │                                    │ exec()              │  │
│     │       │                                    ▼                     │  │
│     │       │                       ┌─────────────────────────────┐   │  │
│     │       │                       │    NEW PROGRAM IMAGE        │   │  │
│     │       │                       │  (same PID, new code/data)  │   │  │
│     │       │                       └─────────────────────────────┘   │  │
│     │       │                                    │                     │  │
│     │       │                                    │ exit() or killed   │  │
│     │       │                                    ▼                     │  │
│     │       │                       ┌─────────────────────────────┐   │  │
│     │       │                       │         ZOMBIE              │   │  │
│     │       │                       │  (waiting to be reaped)     │   │  │
│     │       │                       └─────────────────────────────┘   │  │
│     │       │                                    │                     │  │
│     │       │ wait()                            │                     │  │
│     │       ◄────────────────────────────────────┘                     │  │
│     │       │  (retrieves exit status, zombie removed)                │  │
│     │       ▼                                                          │  │
│     │   ┌─────────┐                                                    │  │
│     │   │ PARENT  │                                                    │  │
│     │   │CONTINUES│                                                    │  │
│     │   └─────────┘                                                    │  │
│     │                                                                   │  │
│     └──────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│     ┌──────────────────────────────────────────────────────────────────┐  │
│     │                                                                   │  │
│     │                      SIGNAL DELIVERY                              │  │
│     │                                                                   │  │
│     │   ┌─────────┐   kill(pid, sig)   ┌───────────────────────────┐  │  │
│     │   │ SENDER  │ ─────────────────► │   TARGET PROCESS          │  │  │
│     │   │         │                    │                            │  │  │
│     │   └─────────┘                    │  Signal pending bit set   │  │  │
│     │                                  │           │                │  │  │
│     │                                  │           ▼                │  │  │
│     │                                  │  ┌─────────────────────┐  │  │  │
│     │                                  │  │ On return to user:  │  │  │  │
│     │                                  │  │ • Default action    │  │  │  │
│     │                                  │  │ • Ignore             │  │  │  │
│     │                                  │  │ • Call handler      │  │  │  │
│     │                                  │  └─────────────────────┘  │  │  │
│     │                                  └───────────────────────────┘  │  │
│     │                                                                   │  │
│     └──────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│     ┌──────────────────────────────────────────────────────────────────┐  │
│     │                                                                   │  │
│     │                  THE SHELL: PUTTING IT ALL TOGETHER              │  │
│     │                                                                   │  │
│     │   $ ls -la | grep "\.c$" | wc -l                                 │  │
│     │                                                                   │  │
│     │   ┌──────────────────────────────────────────────────────────┐   │  │
│     │   │                                                           │   │  │
│     │   │   SHELL (PID 100)                                        │   │  │
│     │   │       │                                                   │   │  │
│     │   │       ├── pipe() ── pipe() ──────────────────────────────│   │  │
│     │   │       │                                                   │   │  │
│     │   │       ├── fork() ──► ls (PID 101)   stdout→pipe[0]      │   │  │
│     │   │       │                    │                              │   │  │
│     │   │       ├── fork() ──► grep (PID 102) stdin←pipe[0]       │   │  │
│     │   │       │                    │         stdout→pipe[1]      │   │  │
│     │   │       │                    │                              │   │  │
│     │   │       └── fork() ──► wc (PID 103)   stdin←pipe[1]       │   │  │
│     │   │                            │                              │   │  │
│     │   │       wait() ◄──── exit() ─┘                             │   │  │
│     │   │       wait() ◄──── exit() ─┘                             │   │  │
│     │   │       wait() ◄──── exit() ─┘                             │   │  │
│     │   │                                                           │   │  │
│     │   └──────────────────────────────────────────────────────────┘   │  │
│     │                                                                   │  │
│     └──────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 12. References

### Books

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ESSENTIAL READING                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PRIMARY SOURCE:                                                          │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   Maurice J. Bach                                                          │
│   "The Design of the UNIX Operating System"                               │
│   Prentice Hall, 1986                                                      │
│   ISBN: 0-13-201799-7                                                      │
│                                                                            │
│   Chapter 6: The Structure of Processes                                   │
│   Chapter 7: Process Control                                               │
│   Chapter 8: Process Scheduling and Time                                  │
│                                                                            │
│   COMPLEMENTARY TEXTS:                                                     │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   W. Richard Stevens, Stephen A. Rago                                     │
│   "Advanced Programming in the UNIX Environment" (3rd Ed.)               │
│   Addison-Wesley, 2013                                                     │
│   - Chapter 7: Process Environment                                        │
│   - Chapter 8: Process Control                                             │
│   - Chapter 9: Process Relationships                                       │
│   - Chapter 10: Signals                                                    │
│                                                                            │
│   Michael Kerrisk                                                          │
│   "The Linux Programming Interface"                                        │
│   No Starch Press, 2010                                                    │
│   - Part II: Processes (Chapters 24-29)                                   │
│   - Part III: Signals (Chapters 20-22)                                    │
│                                                                            │
│   Robert Love                                                              │
│   "Linux Kernel Development" (3rd Ed.)                                    │
│   Addison-Wesley, 2010                                                     │
│   - Chapter 3: Process Management                                          │
│   - Chapter 4: Process Scheduling                                          │
│                                                                            │
│   Daniel P. Bovet, Marco Cesati                                           │
│   "Understanding the Linux Kernel" (3rd Ed.)                              │
│   O'Reilly, 2005                                                           │
│   - Chapter 3: Processes                                                   │
│   - Chapter 11: Signals                                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Source Files

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX KERNEL SOURCE FILES                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROCESS MANAGEMENT:                                                      │
│   ─────────────────────────────────────────────────────────────────────── │
│   kernel/fork.c           - fork(), clone() implementation                │
│   kernel/exit.c           - exit(), wait() implementation                 │
│   kernel/exec.c           - exec*() common code                           │
│   fs/exec.c               - execve() implementation                       │
│   kernel/signal.c         - Signal delivery                               │
│                                                                            │
│   HEADERS:                                                                 │
│   ─────────────────────────────────────────────────────────────────────── │
│   include/linux/sched.h   - task_struct definition                        │
│   include/linux/signal.h  - Signal structures                             │
│   include/linux/resource.h- Resource limits                               │
│                                                                            │
│   ARCHITECTURE-SPECIFIC:                                                   │
│   ─────────────────────────────────────────────────────────────────────── │
│   arch/x86/entry/         - System call entry points                      │
│   arch/x86/kernel/process.c - x86 process handling                        │
│                                                                            │
│   HOW TO BROWSE:                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│   https://elixir.bootlin.com/linux/latest/source                          │
│   https://github.com/torvalds/linux                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Man Pages

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RELEVANT MAN PAGES                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SECTION 2 (System Calls):                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│   man 2 fork          - Create child process                              │
│   man 2 vfork         - Create child (obsolete)                           │
│   man 2 clone         - Create child (Linux)                              │
│   man 2 execve        - Execute program                                   │
│   man 2 _exit         - Terminate process                                 │
│   man 2 wait          - Wait for child                                    │
│   man 2 waitpid       - Wait for specific child                           │
│   man 2 waitid        - Wait for child (POSIX)                            │
│   man 2 kill          - Send signal                                       │
│   man 2 sigaction     - Set signal handler                                │
│   man 2 sigprocmask   - Block signals                                     │
│   man 2 brk           - Change data segment size                          │
│   man 2 getrlimit     - Get resource limits                               │
│   man 2 setrlimit     - Set resource limits                               │
│   man 2 getpid        - Get process ID                                    │
│   man 2 getppid       - Get parent process ID                             │
│   man 2 setuid        - Set user ID                                       │
│   man 2 setsid        - Create session                                    │
│                                                                            │
│   SECTION 3 (Library Functions):                                          │
│   ─────────────────────────────────────────────────────────────────────── │
│   man 3 exec          - exec() family overview                            │
│   man 3 exit          - Exit with cleanup                                 │
│   man 3 signal        - Signal handling (simple)                          │
│   man 3 daemon        - Daemonize process                                 │
│   man 3 system        - Execute shell command                             │
│   man 3 popen         - Pipe to/from process                              │
│                                                                            │
│   SECTION 7 (Miscellaneous):                                              │
│   ─────────────────────────────────────────────────────────────────────── │
│   man 7 signal        - Signal overview                                   │
│   man 7 credentials   - Process credentials                               │
│   man 7 pid_namespaces- PID namespaces                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Online Resources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ONLINE RESOURCES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DOCUMENTATION:                                                           │
│   ─────────────────────────────────────────────────────────────────────── │
│   https://www.kernel.org/doc/                 - Official Linux docs       │
│   https://lwn.net/                            - Linux Weekly News         │
│   https://man7.org/                           - Michael Kerrisk's site    │
│   https://www.gnu.org/software/libc/manual/   - glibc manual             │
│                                                                            │
│   KERNEL BROWSING:                                                         │
│   ─────────────────────────────────────────────────────────────────────── │
│   https://elixir.bootlin.com/                 - Cross-referenced source   │
│   https://lxr.sourceforge.io/                 - Linux Cross-Reference     │
│                                                                            │
│   TUTORIALS:                                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│   https://beej.us/guide/bgipc/                - Beej's IPC Guide         │
│   https://www.cs.cmu.edu/~410/                - CMU OS course materials  │
│                                                                            │
│   STANDARDS:                                                               │
│   ─────────────────────────────────────────────────────────────────────── │
│   https://pubs.opengroup.org/                 - POSIX specifications     │
│   https://www.unix.org/                       - The Open Group           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

*This document is inspired by Maurice J. Bach's seminal work*
*"The Design of the UNIX Operating System" (1986)*

*Process Control is the heart of Unix - it is what allows multiple programs*
*to run simultaneously, each believing it has the machine to itself.*

---
