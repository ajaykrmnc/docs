# Blocking and Non-Blocking I/O in Unix Systems

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Kernel Internals, Process States, I/O Multiplexing, and Event-Driven Architecture

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The Fundamental I/O Problem](#the-fundamental-io-problem)
   - [Historical Context](#historical-context)
   - [Document Organization](#document-organization)

2. [Fundamental Concepts](#2-fundamental-concepts)
   - [Process States and the Scheduler](#process-states-and-the-scheduler)
   - [Wait Queues in the Kernel](#wait-queues-in-the-kernel)
   - [File Descriptor Flags](#file-descriptor-flags)
   - [The Speed Mismatch Problem](#the-speed-mismatch-problem)

3. [Blocking I/O](#3-blocking-io)
   - [What Does "Blocking" Mean?](#what-does-blocking-mean)
   - [The Blocking Read Algorithm](#the-blocking-read-algorithm)
   - [The Blocking Write Algorithm](#the-blocking-write-algorithm)
   - [Blocking on Different Resource Types](#blocking-on-different-resource-types)
   - [Interruptible vs Uninterruptible Sleep](#interruptible-vs-uninterruptible-sleep)

4. [Non-Blocking I/O](#4-non-blocking-io)
   - [The O_NONBLOCK Flag](#the-o_nonblock-flag)
   - [EAGAIN and EWOULDBLOCK](#eagain-and-ewouldblock)
   - [The Non-Blocking Read Algorithm](#the-non-blocking-read-algorithm)
   - [The Non-Blocking Write Algorithm](#the-non-blocking-write-algorithm)
   - [Partial Reads and Writes](#partial-reads-and-writes)
   - [The Busy-Wait Anti-Pattern](#the-busy-wait-anti-pattern)

5. [I/O Multiplexing](#5-io-multiplexing)
   - [The Problem: Monitoring Multiple File Descriptors](#the-problem-monitoring-multiple-file-descriptors)
   - [select() - The Original Solution](#select---the-original-solution)
   - [poll() - Removing the fd Limit](#poll---removing-the-fd-limit)
   - [epoll() - The Linux Scalable Solution](#epoll---the-linux-scalable-solution)
   - [kqueue() - The BSD Approach](#kqueue---the-bsd-approach)
   - [Comparison and Trade-offs](#comparison-and-trade-offs)

6. [Advanced Topics](#6-advanced-topics)
   - [Level-Triggered vs Edge-Triggered](#level-triggered-vs-edge-triggered)
   - [The Thundering Herd Problem](#the-thundering-herd-problem)
   - [Asynchronous I/O (AIO)](#asynchronous-io-aio)
   - [io_uring - Modern Linux Async I/O](#io_uring---modern-linux-async-io)

7. [Event-Driven Architecture](#7-event-driven-architecture)
   - [The Event Loop Pattern](#the-event-loop-pattern)
   - [Reactor Pattern](#reactor-pattern)
   - [Proactor Pattern](#proactor-pattern)
   - [Real-World Implementations](#real-world-implementations)

8. [Practical Implementation](#8-practical-implementation)
   - [Building a Non-Blocking Server](#building-a-non-blocking-server)
   - [The Main Event Loop](#the-main-event-loop)
   - [Error Handling Patterns](#error-handling-patterns)
   - [Common Pitfalls](#common-pitfalls)
   - [Performance Considerations](#performance-considerations)

9. [Summary and Appendix](#9-summary-and-appendix)
   - [Quick Reference: When to Use What](#quick-reference-when-to-use-what)
   - [System Call Quick Reference](#system-call-quick-reference)
   - [Error Codes Reference](#error-codes-reference)
   - [Historical Context](#historical-context-1)
   - [The Big Picture](#the-big-picture)

10. [References](#references)

---

## 1. Introduction

### The Fundamental I/O Problem

At the heart of every operating system lies a fundamental tension: **CPUs are fast, but I/O is slow.**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SPEED MISMATCH PROBLEM                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Operation                          Time            CPU Cycles Wasted     │
│   ─────────────────────────────────────────────────────────────────────   │
│   CPU instruction                    ~1 ns           0                     │
│   L1 cache access                    ~1 ns           0                     │
│   L2 cache access                    ~4 ns           0                     │
│   RAM access                         ~100 ns         ~100                  │
│   SSD read                           ~100 μs         ~100,000              │
│   HDD read                           ~10 ms          ~10,000,000           │
│   Network round-trip (same DC)       ~500 μs         ~500,000              │
│   Network round-trip (cross-country) ~50 ms          ~50,000,000           │
│                                                                            │
│   If a CPU cycle were 1 second:                                            │
│   • RAM access = 1.5 minutes                                               │
│   • SSD read = 1-2 days                                                    │
│   • HDD read = 3-6 months                                                  │
│   • Network (cross-country) = 1.5 years                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

When a process performs I/O, what should happen while waiting for the slow device?

**Option 1: Busy Wait (Polling)**
```c
while (device_not_ready()) {
    /* Do nothing, waste CPU cycles */
}
read_from_device();
```
This wastes enormous CPU resources. A process waiting for network data would burn millions of cycles doing nothing useful.

**Option 2: Block (Sleep)**
```c
/* Kernel puts process to sleep */
/* Kernel wakes process when data arrives */
read_from_device();
```
The CPU can run other processes while this one waits. This is **blocking I/O**.

**Option 3: Return Immediately**
```c
result = try_read_from_device();
if (result == WOULD_BLOCK) {
    /* No data available, do something else */
}
```
The process can do other work instead of waiting. This is **non-blocking I/O**.

Each approach has trade-offs that we will explore in depth.

### Historical Context

The evolution of I/O handling in Unix reflects decades of learning:

| Era   | Mechanism              | Characteristics                                    |
| ----- | ---------------------- | -------------------------------------------------- |
| 1970s | Blocking I/O only      | Simple, one process per connection                 |
| 1983  | select() (4.2BSD)      | Monitor multiple fds, but O(n) scanning            |
| 1986  | poll() (System V)      | No fd limit, but still O(n)                        |
| 1999  | /dev/poll (Solaris)    | Stateful, better scalability                       |
| 2000  | kqueue (FreeBSD)       | Edge-triggered, O(1) operations                    |
| 2002  | epoll (Linux 2.5.44)   | Scalable, edge/level triggered                     |
| 2007  | signalfd, timerfd      | Unify signals/timers with fd interface             |
| 2019  | io_uring (Linux 5.1)   | True async I/O, shared ring buffers                |

As W. Richard Stevens wrote in "Unix Network Programming":

> "The key to writing high-performance servers is understanding the various I/O models available and choosing the right one for your application."

### Document Organization

This document follows the structure established by Maurice Bach, proceeding from fundamental concepts through kernel implementation to practical application:

1. **Fundamentals**: Process states, wait queues, and the kernel's view of I/O
2. **Blocking I/O**: How the kernel puts processes to sleep and wakes them
3. **Non-Blocking I/O**: Immediate return semantics and error handling
4. **Multiplexing**: Monitoring multiple file descriptors efficiently
5. **Advanced Topics**: Edge-triggering, async I/O, and modern interfaces
6. **Practical Patterns**: Building real-world event-driven systems

---

## 2. Fundamental Concepts

Before examining blocking and non-blocking I/O, we must understand the kernel mechanisms that make them possible.

### Process States and the Scheduler

A Unix process exists in one of several states. Understanding these states is crucial to understanding I/O behavior.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         PROCESS STATE DIAGRAM                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                              ┌─────────────┐                               │
│                              │   CREATED   │                               │
│                              │  (fork())   │                               │
│                              └──────┬──────┘                               │
│                                     │                                      │
│                                     ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                                                                  │     │
│   │  ┌─────────────┐    schedule()    ┌─────────────┐               │     │
│   │  │             │ ───────────────> │             │               │     │
│   │  │    READY    │                  │   RUNNING   │               │     │
│   │  │  (runnable) │ <─────────────── │  (on CPU)   │               │     │
│   │  │             │    preempt /     │             │               │     │
│   │  └─────────────┘    time slice    └──────┬──────┘               │     │
│   │        ▲                                 │                       │     │
│   │        │                                 │                       │     │
│   │        │ wake_up()              I/O request (read/write)        │     │
│   │        │ (data ready)           or wait for event               │     │
│   │        │                                 │                       │     │
│   │        │                                 ▼                       │     │
│   │        │                         ┌─────────────┐                │     │
│   │        │                         │  SLEEPING   │                │     │
│   │        └──────────────────────── │  (blocked)  │                │     │
│   │                                  │  WAITING    │                │     │
│   │                                  └─────────────┘                │     │
│   │                                                                  │     │
│   │   THE SCHEDULER ONLY RUNS PROCESSES IN THE "READY" STATE!       │     │
│   │   A sleeping process uses ZERO CPU time.                         │     │
│   │                                                                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                     │                                      │
│                                     │ exit()                               │
│                                     ▼                                      │
│                              ┌─────────────┐                               │
│                              │   ZOMBIE    │                               │
│                              │ (terminated)│                               │
│                              └─────────────┘                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key insight**: When a process performs blocking I/O, it moves from RUNNING to SLEEPING. The kernel removes it from the run queue, so it consumes **zero CPU time** while waiting. This is the fundamental efficiency of blocking I/O.

#### Linux Process States (task_struct->state)

```c
/* From linux/sched.h */
#define TASK_RUNNING            0x0000   /* On run queue or currently executing */
#define TASK_INTERRUPTIBLE      0x0001   /* Sleeping, can be woken by signal */
#define TASK_UNINTERRUPTIBLE    0x0002   /* Sleeping, cannot be interrupted */
#define TASK_STOPPED            0x0004   /* Stopped (e.g., by SIGSTOP) */
#define TASK_TRACED             0x0008   /* Being traced (debugger) */
#define EXIT_ZOMBIE             0x0010   /* Terminated, waiting for parent */
#define EXIT_DEAD               0x0020   /* Final state */
```

### Wait Queues in the Kernel

When a process blocks on I/O, where does it go? The kernel maintains **wait queues** — linked lists of processes waiting for specific events.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         WAIT QUEUE STRUCTURE                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Every I/O resource has an associated wait queue:                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                        PIPE STRUCTURE                            │     │
│   │  ┌─────────────────────────────────────────────────────────┐    │     │
│   │  │  struct pipe_inode_info {                                │    │     │
│   │  │      ...                                                 │    │     │
│   │  │      wait_queue_head_t rd_wait;  /* Readers waiting */   │    │     │
│   │  │      wait_queue_head_t wr_wait;  /* Writers waiting */   │    │     │
│   │  │      ...                                                 │    │     │
│   │  │  }                                                       │    │     │
│   │  └─────────────────────────────────────────────────────────┘    │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                        SOCKET STRUCTURE                          │     │
│   │  ┌─────────────────────────────────────────────────────────┐    │     │
│   │  │  struct socket {                                         │    │     │
│   │  │      ...                                                 │    │     │
│   │  │      struct socket_wq *wq;  /* Wait queue for events */  │    │     │
│   │  │      ...                                                 │    │     │
│   │  │  }                                                       │    │     │
│   │  └─────────────────────────────────────────────────────────┘    │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   When process blocks:                                                     │
│                                                                            │
│   rd_wait (readers waiting for data)                                       │
│   ┌──────────────────────────────────────────────────────────────┐        │
│   │ HEAD ──> [Process A] ──> [Process B] ──> [Process C] ──> NULL │        │
│   │          (PID 100)       (PID 205)       (PID 308)            │        │
│   └──────────────────────────────────────────────────────────────┘        │
│                                                                            │
│   When data arrives, kernel calls wake_up(&rd_wait):                       │
│   • All processes on the queue are moved to READY state                    │
│   • Scheduler will eventually run them                                     │
│   • They will retry their read() operation                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

#### The wait_event() Macro

The kernel provides macros for sleeping on wait queues:

```c
/* Sleep until condition becomes true */
wait_event(wq, condition);

/* Sleep until condition becomes true, but wake on signals too */
wait_event_interruptible(wq, condition);

/* Wake up all processes on the wait queue */
wake_up(&wq);

/* Wake up only one process (more efficient) */
wake_up_one(&wq);
```

### File Descriptor Flags

Each open file descriptor has associated flags that control its behavior. The most important for our discussion is `O_NONBLOCK`.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILE DESCRIPTOR FLAGS                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct file {                                                            │
│       ...                                                                  │
│       unsigned int f_flags;    /* O_RDONLY, O_NONBLOCK, etc. */           │
│       ...                                                                  │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                     f_flags BITMASK                              │     │
│   ├─────────────────────────────────────────────────────────────────┤     │
│   │  Bit 0-1:  Access mode (O_RDONLY=0, O_WRONLY=1, O_RDWR=2)       │     │
│   │  Bit 6:    O_NONBLOCK  - Don't block on I/O                     │     │
│   │  Bit 10:   O_APPEND    - Append mode                            │     │
│   │  Bit 11:   O_DSYNC     - Synchronized data writes               │     │
│   │  Bit 14:   O_DIRECT    - Direct I/O (bypass page cache)         │     │
│   │  Bit 19:   O_CLOEXEC   - Close on exec                          │     │
│   │  ...                                                             │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   Setting O_NONBLOCK:                                                      │
│                                                                            │
│   /* Method 1: At open() time */                                           │
│   int fd = open("/dev/tty", O_RDWR | O_NONBLOCK);                          │
│                                                                            │
│   /* Method 2: Using fcntl() on existing fd */                             │
│   int flags = fcntl(fd, F_GETFL);                                          │
│   fcntl(fd, F_SETFL, flags | O_NONBLOCK);                                  │
│                                                                            │
│   /* Method 3: For pipes, use pipe2() */                                   │
│   pipe2(pipefd, O_NONBLOCK);                                               │
│                                                                            │
│   /* Method 4: For sockets, use SOCK_NONBLOCK */                           │
│   socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Speed Mismatch Problem Visualized

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHY BLOCKING EXISTS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Imagine a process reading from a network socket:                         │
│                                                                            │
│   TIME ─────────────────────────────────────────────────────────────────>  │
│                                                                            │
│   Process calls read()                                                     │
│        │                                                                   │
│        ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │                                                                  │     │
│   │   CPU: "I need data from the network!"                           │     │
│   │                                                                  │     │
│   │   Network: "Sure, let me send a packet across the internet..."   │     │
│   │            "...through 15 routers..."                            │     │
│   │            "...wait for the server to respond..."                │     │
│   │            "...send the response back..."                        │     │
│   │            "...50 milliseconds later..."                         │     │
│   │            "Here's your data!"                                   │     │
│   │                                                                  │     │
│   │   50 ms = 50,000,000 nanoseconds = ~150,000,000 CPU cycles!      │     │
│   │                                                                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   WITHOUT BLOCKING (busy wait):                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │   while (!data_ready) {                                          │     │
│   │       /* Burn 150 million CPU cycles doing NOTHING */            │     │
│   │       /* Other processes can't run */                            │     │
│   │       /* Laptop battery drains */                                │     │
│   │       /* CPU heats up */                                         │     │
│   │   }                                                              │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│   WITH BLOCKING:                                                           │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │   /* Kernel: "This process needs to wait. I'll put it to sleep" │     │
│   │              "and run other processes instead."                  │     │
│   │                                                                  │     │
│   │   Process A: SLEEPING (waiting for network)                      │     │
│   │   Process B: RUNNING  (doing useful work)                        │     │
│   │   Process C: RUNNING  (doing useful work)                        │     │
│   │   ...                                                            │     │
│   │                                                                  │     │
│   │   /* 50ms later, data arrives */                                 │     │
│   │   /* Kernel: "Wake up Process A, its data is here!" */           │     │
│   │   Process A: RUNNING (continues with data)                       │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Blocking I/O

### What Does "Blocking" Mean?

When we say a system call "blocks," we mean:

1. The process **voluntarily gives up the CPU**
2. The kernel moves the process to a **wait queue**
3. The process state changes from RUNNING to **SLEEPING**
4. The scheduler runs **other processes** instead
5. When the awaited event occurs, the kernel **wakes up** the process
6. The process resumes execution **as if no time passed**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BLOCKING FROM THE PROCESS'S PERSPECTIVE                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   From the process's point of view, blocking is INVISIBLE:                 │
│                                                                            │
│   printf("About to read...\n");                                            │
│   n = read(fd, buf, sizeof(buf));    /* <-- Process sleeps here */         │
│   printf("Read %d bytes\n", n);      /* <-- Continues when data ready */   │
│                                                                            │
│   The process doesn't "know" it slept. It just sees:                       │
│   1. Called read()                                                         │
│   2. Got data back                                                         │
│                                                                            │
│   But in reality:                                                          │
│   1. Called read()                                                         │
│   2. No data available                                                     │
│   3. Kernel put process to sleep                                           │
│   4. 50ms passed, other processes ran                                      │
│   5. Data arrived, kernel woke process                                     │
│   6. read() returned with data                                             │
│                                                                            │
│   TIME ─────────────────────────────────────────────────────────────────>  │
│                                                                            │
│   Process view:  [read()]─────────────────────────────────────[return]     │
│                     │                                             │        │
│   Reality:       [read]──[SLEEP]─────────────────────[WAKE]──[return]      │
│                           │                            │                   │
│                           └── Other processes run ─────┘                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Blocking Read Algorithm

Here is the kernel's algorithm for a blocking read, presented in the style of Maurice Bach:

```
algorithm: sys_read (blocking mode)
input:     fd        - file descriptor
           buf       - user buffer to receive data
           count     - maximum bytes to read
output:    number of bytes read, or error

{
    /* Step 1: Validate file descriptor */
    file = fget(fd);
    if (file == NULL)
        return -EBADF;

    /* Step 2: Check if file is readable */
    if (!(file->f_mode & FMODE_READ))
        return -EBADF;

    /* Step 3: Get the file operations */
    fops = file->f_op;

    /* Step 4: Call the file-type-specific read function */
    /* This is where blocking happens! */
    return fops->read(file, buf, count, &file->f_pos);
}
```

For a pipe, the `fops->read` function is `pipe_read()`:

```
algorithm: pipe_read (blocking mode)
input:     file      - file structure for read end of pipe
           buf       - user buffer
           count     - bytes requested
output:    bytes read, 0 for EOF, or negative error

{
    pipe = file->f_inode->i_pipe;

    for (;;) {    /* Loop until we get data or error */

        /* Step 1: Check if there's data in the pipe buffer */
        if (pipe->nrbufs > 0) {
            /* Data available! Copy to user buffer */
            bytes_copied = copy_to_user(buf, pipe->bufs, count);
            pipe->nrbufs -= bytes_copied;

            /* Wake up any writers waiting for space */
            wake_up(&pipe->wr_wait);

            return bytes_copied;
        }

        /* Step 2: No data. Check if any writers exist */
        if (pipe->writers == 0) {
            /* No writers, no data = EOF */
            return 0;
        }

        /* Step 3: Check if non-blocking mode */
        if (file->f_flags & O_NONBLOCK) {
            return -EAGAIN;    /* Would block, but can't */
        }

        /* Step 4: BLOCKING HAPPENS HERE! */
        /* Add ourselves to the wait queue and sleep */
        prepare_to_wait(&pipe->rd_wait, &wait, TASK_INTERRUPTIBLE);

        /* Double-check condition before sleeping */
        if (pipe->nrbufs == 0 && pipe->writers > 0) {
            schedule();    /* <-- Process sleeps here! */
        }

        finish_wait(&pipe->rd_wait, &wait);

        /* Step 5: We were woken up. Check why */
        if (signal_pending(current)) {
            return -ERESTARTSYS;    /* Interrupted by signal */
        }

        /* Loop back and try to read again */
    }
}
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BLOCKING READ VISUALIZED                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Process A calls: read(pipe_fd, buf, 100)                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │ KERNEL                                                           │     │
│   │                                                                  │     │
│   │  1. Look up fd in process's file table                          │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  2. Call pipe_read()                                             │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  3. Check pipe buffer ──── Data available? ──── YES ──> Return  │     │
│   │                    │                                             │     │
│   │                   NO                                             │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  4. Check writers ──── Any writers? ──── NO ──> Return 0 (EOF)  │     │
│   │                    │                                             │     │
│   │                   YES                                            │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  5. Check O_NONBLOCK ──── Set? ──── YES ──> Return -EAGAIN      │     │
│   │                    │                                             │     │
│   │                   NO                                             │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  6. Add process to pipe->rd_wait queue                          │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  7. Set process state to TASK_INTERRUPTIBLE                     │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  8. Call schedule() ──────────────────────────────────────┐     │     │
│   │                                                            │     │     │
│   │     ┌──────────────────────────────────────────────────────┤     │     │
│   │     │  PROCESS A IS NOW SLEEPING                           │     │     │
│   │     │  • Removed from run queue                            │     │     │
│   │     │  • Using ZERO CPU                                    │     │     │
│   │     │  • Waiting on pipe->rd_wait                          │     │     │
│   │     └──────────────────────────────────────────────────────┤     │     │
│   │                                                            │     │     │
│   │  ... time passes, other processes run ...                  │     │     │
│   │                                                            │     │     │
│   │  Process B calls: write(pipe_fd, "Hello", 5)               │     │     │
│   │                    │                                       │     │     │
│   │                    ▼                                       │     │     │
│   │  9. pipe_write() puts data in buffer                       │     │     │
│   │                    │                                       │     │     │
│   │                    ▼                                       │     │     │
│   │  10. wake_up(&pipe->rd_wait) ──────────────────────────────┘     │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  11. Process A moves to READY state                              │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  12. Scheduler eventually runs Process A                         │     │
│   │                    │                                             │     │
│   │                    ▼                                             │     │
│   │  13. Process A loops back, finds data, returns 5                 │     │
│   │                                                                  │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Blocking Write Algorithm

Writing can also block — when the buffer is full!

```
algorithm: pipe_write (blocking mode)
input:     file      - file structure for write end of pipe
           buf       - user buffer with data to write
           count     - bytes to write
output:    bytes written, or negative error

{
    pipe = file->f_inode->i_pipe;

    for (;;) {

        /* Step 1: Check if any readers exist */
        if (pipe->readers == 0) {
            /* No readers! Send SIGPIPE to writer */
            send_sig(SIGPIPE, current, 0);
            return -EPIPE;
        }

        /* Step 2: Check if there's space in the buffer */
        if (pipe_has_space(pipe)) {
            /* Space available! Copy from user buffer */
            bytes_copied = copy_from_user(pipe->bufs, buf, count);
            pipe->nrbufs += bytes_copied;

            /* Wake up any readers waiting for data */
            wake_up(&pipe->rd_wait);

            return bytes_copied;
        }

        /* Step 3: Buffer is full. Check non-blocking mode */
        if (file->f_flags & O_NONBLOCK) {
            return -EAGAIN;    /* Would block, but can't */
        }

        /* Step 4: BLOCKING HAPPENS HERE! */
        prepare_to_wait(&pipe->wr_wait, &wait, TASK_INTERRUPTIBLE);

        if (!pipe_has_space(pipe) && pipe->readers > 0) {
            schedule();    /* <-- Process sleeps here! */
        }

        finish_wait(&pipe->wr_wait, &wait);

        if (signal_pending(current)) {
            return -ERESTARTSYS;
        }

        /* Loop back and try to write again */
    }
}
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHEN DOES WRITE BLOCK?                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PIPE BUFFER (typically 64KB on Linux):                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │████████████████████████████████████████████████████████████████│     │
│   │████████████████████████████████████████████████████████████████│     │
│   │████████████████████████████████████████████████████████████████│     │
│   │████████████████████████████████████████████████████████████████│     │
│   └─────────────────────────────────────────────────────────────────┘     │
│   ▲                                                                 ▲      │
│   │                         BUFFER FULL!                            │      │
│   │                                                                 │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│   If writer tries to write more data:                                      │
│   • Blocking mode: Writer sleeps until reader consumes some data           │
│   • Non-blocking mode: write() returns -1, errno = EAGAIN                  │
│                                                                            │
│   SCENARIO: Producer-Consumer with slow consumer                           │
│                                                                            │
│   Producer (fast)                    Consumer (slow)                       │
│   ┌─────────────────┐                ┌─────────────────┐                  │
│   │ while(1) {      │                │ while(1) {      │                  │
│   │   data = gen(); │                │   read(fd,...)  │                  │
│   │   write(fd,...);│ ──── PIPE ──── │   slow_process()│                  │
│   │ }               │                │ }               │                  │
│   └─────────────────┘                └─────────────────┘                  │
│                                                                            │
│   Producer generates data faster than consumer processes it.               │
│   Pipe buffer fills up. Producer BLOCKS until consumer catches up.         │
│   This is BACKPRESSURE - the system naturally throttles the producer!      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Interruptible vs Uninterruptible Sleep

When a process blocks, the kernel must decide: **can signals wake it up?**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TWO KINDS OF SLEEP                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TASK_INTERRUPTIBLE (S state in ps)                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Process can be woken by SIGNALS (Ctrl+C, SIGTERM, etc.)          │ │
│   │  • Used for: pipes, sockets, terminals, user-initiated I/O          │ │
│   │  • If signal arrives: wake up, return -EINTR or -ERESTARTSYS        │ │
│   │  • User can "cancel" the operation                                  │ │
│   │                                                                     │ │
│   │  Example: read(socket_fd, ...) - user can Ctrl+C to abort           │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TASK_UNINTERRUPTIBLE (D state in ps)                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Process CANNOT be woken by signals                               │ │
│   │  • Used for: disk I/O, NFS, critical kernel operations              │ │
│   │  • If signal arrives: ignored until I/O completes                   │ │
│   │  • The "unkillable" process state                                   │ │
│   │                                                                     │ │
│   │  Example: read() from hung NFS mount - even kill -9 won't work!     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Why UNINTERRUPTIBLE exists:                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Some operations CANNOT be safely interrupted mid-way:              │ │
│   │                                                                     │ │
│   │  • Writing to disk: interruption could corrupt filesystem          │ │
│   │  • NFS operation: server might have partial data                    │ │
│   │  • Device driver handshake: hardware might be in bad state          │ │
│   │                                                                     │ │
│   │  The kernel says: "This WILL complete. You WILL wait."              │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ps output example:                                                       │
│   $ ps aux | grep myprocess                                                │
│   user  1234  0.0  0.1  S  pts/0  sleep_on_pipe    # Interruptible         │
│   user  5678  0.0  0.1  D  pts/0  nfs_read         # Uninterruptible       │
│                   │        │                                               │
│                   │        └── Can't be killed!                            │
│                   └── Can be killed with Ctrl+C                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```c
/* In kernel code, the difference is one constant: */

/* Interruptible - can be woken by signals */
prepare_to_wait(&wq, &wait, TASK_INTERRUPTIBLE);
schedule();
if (signal_pending(current))
    return -ERESTARTSYS;  /* Signal arrived, abort operation */

/* Uninterruptible - ignores signals */
prepare_to_wait(&wq, &wait, TASK_UNINTERRUPTIBLE);
schedule();
/* No signal check - we only wake when the I/O is done */
```

### Blocking on Different Resource Types

Different types of file descriptors have different blocking behaviors:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BLOCKING BEHAVIORS BY RESOURCE TYPE                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PIPES                                                                    │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │  read():  blocks if empty AND writers exist                       │   │
│   │  write(): blocks if full AND readers exist                        │   │
│   │  EOF:     read() returns 0 when no writers left                   │   │
│   │  EPIPE:   write() fails when no readers left                      │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   SOCKETS                                                                  │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │  accept(): blocks waiting for incoming connections                │   │
│   │  connect(): blocks during TCP three-way handshake                 │   │
│   │  read():  blocks if receive buffer empty                          │   │
│   │  write(): blocks if send buffer full (TCP backpressure)           │   │
│   │  EOF:     read() returns 0 when peer closes connection            │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   TERMINALS (TTY)                                                          │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │  read():  blocks waiting for user to type + press Enter           │   │
│   │  write(): usually doesn't block (terminal buffers output)         │   │
│   │  Special: canonical mode vs raw mode affects behavior             │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   REGULAR FILES                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │  read():  blocks during disk I/O (UNINTERRUPTIBLE!)               │   │
│   │  write(): blocks during disk I/O (UNINTERRUPTIBLE!)               │   │
│   │  Note: O_NONBLOCK has NO EFFECT on regular files!                 │   │
│   │        (POSIX says regular files are "always ready")               │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   FIFOS (Named Pipes)                                                      │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │  open() for read:  blocks until a writer opens the FIFO           │   │
│   │  open() for write: blocks until a reader opens the FIFO           │   │
│   │  (unless O_NONBLOCK is set)                                       │   │
│   │  Data transfer: same as regular pipes                             │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Non-Blocking I/O

### The O_NONBLOCK Flag

Non-blocking I/O changes the fundamental contract between process and kernel:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BLOCKING vs NON-BLOCKING CONTRACT                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BLOCKING I/O CONTRACT:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  "Dear Kernel,                                                      │ │
│   │   I need data. I'll wait as long as it takes.                       │ │
│   │   Put me to sleep if necessary. Wake me when you have something."   │ │
│   │                                                                     │ │
│   │   - Signed, Process                                                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NON-BLOCKING I/O CONTRACT:                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  "Dear Kernel,                                                      │ │
│   │   I want data, but I'm busy. Do you have any RIGHT NOW?             │ │
│   │   If yes, give it to me. If no, tell me immediately.                │ │
│   │   DO NOT put me to sleep. I have other things to do."               │ │
│   │                                                                     │ │
│   │   - Signed, Process                                                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### EAGAIN and EWOULDBLOCK

When a non-blocking operation cannot proceed, the kernel returns an error:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE EAGAIN / EWOULDBLOCK ERRORS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When read() or write() on a non-blocking fd cannot proceed:              │
│                                                                            │
│   Return value:  -1                                                        │
│   errno:         EAGAIN  or  EWOULDBLOCK                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  EAGAIN = "Try again" - Resource temporarily unavailable            │ │
│   │  EWOULDBLOCK = "Would block" - Operation would block                │ │
│   │                                                                     │ │
│   │  On Linux: EAGAIN == EWOULDBLOCK (same numeric value: 11)           │ │
│   │  On some other systems: they may be different                       │ │
│   │                                                                     │ │
│   │  Best practice: Check for both                                      │ │
│   │  if (errno == EAGAIN || errno == EWOULDBLOCK) { ... }               │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   This is NOT a failure! It means:                                         │
│   "Nothing wrong happened. There's just no data right now. Try later."    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  CRITICAL DISTINCTION:                                              │ │
│   │                                                                     │ │
│   │  Blocking read:                                                     │ │
│   │    n = read(fd, buf, 100);                                          │ │
│   │    if (n == 0) → EOF (other end closed)                             │ │
│   │    if (n == -1) → Error (check errno)                               │ │
│   │    if (n > 0) → Got data                                            │ │
│   │                                                                     │ │
│   │  Non-blocking read:                                                 │ │
│   │    n = read(fd, buf, 100);                                          │ │
│   │    if (n == 0) → EOF (other end closed)                             │ │
│   │    if (n == -1 && errno == EAGAIN) → No data YET (try later)        │ │
│   │    if (n == -1 && errno != EAGAIN) → Real error                     │ │
│   │    if (n > 0) → Got data                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Non-Blocking Read Algorithm

```
algorithm: pipe_read (non-blocking mode, O_NONBLOCK set)
input:     file      - file structure with O_NONBLOCK flag set
           buf       - user buffer
           count     - bytes requested
output:    bytes read, 0 for EOF, -EAGAIN if would block, or error

{
    pipe = file->f_inode->i_pipe;

    /* Step 1: Check if there's data in the pipe buffer */
    if (pipe->nrbufs > 0) {
        /* Data available! Same as blocking case */
        bytes_copied = copy_to_user(buf, pipe->bufs, count);
        pipe->nrbufs -= bytes_copied;
        wake_up(&pipe->wr_wait);
        return bytes_copied;
    }

    /* Step 2: No data. Check if any writers exist */
    if (pipe->writers == 0) {
        /* No writers, no data = EOF */
        return 0;
    }

    /* Step 3: HERE'S THE DIFFERENCE! */
    /* Instead of sleeping, return immediately with EAGAIN */
    return -EAGAIN;

    /* We NEVER call schedule() - we NEVER sleep */
}
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NON-BLOCKING READ VISUALIZED                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Process A calls: read(nonblock_fd, buf, 100)                             │
│                                                                            │
│   TIME ────────────────────────────────────────────────────────────────>   │
│                                                                            │
│   Blocking:    [read]──────────[SLEEP]────────────────[WAKE]──[return 5]   │
│                                                                            │
│   Non-block:   [read]──[return -1, EAGAIN]                                 │
│                              │                                             │
│                              └── Returns IMMEDIATELY!                      │
│                                  Process keeps running.                    │
│                                  Can do other work.                        │
│                                  Will try again later.                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Partial Reads and Writes

Non-blocking I/O introduces the concept of **partial operations**:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PARTIAL READS AND WRITES                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   You ask for 1000 bytes, but only 100 are available:                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  n = read(fd, buf, 1000);                                           │ │
│   │                                                                     │ │
│   │  Blocking mode:                                                     │ │
│   │    • Might return 1000 (if all data arrives)                        │ │
│   │    • Might return 100 (partial read is ALLOWED)                     │ │
│   │    • Might return 500 (whatever is available)                       │ │
│   │    • Only blocks if ZERO bytes available                            │ │
│   │                                                                     │ │
│   │  Non-blocking mode:                                                 │ │
│   │    • Returns 100 (whatever is available RIGHT NOW)                  │ │
│   │    • Returns -1/EAGAIN only if ZERO bytes available                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY INSIGHT: read() and write() are allowed to do LESS than requested!   │
│                                                                            │
│   YOU MUST ALWAYS CHECK THE RETURN VALUE!                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  /* WRONG: Assumes read() gets everything */                        │ │
│   │  read(fd, buf, 1000);                                               │ │
│   │  process(buf, 1000);  /* Bug! Might have only read 100 bytes! */    │ │
│   │                                                                     │ │
│   │  /* RIGHT: Check how much was actually read */                      │ │
│   │  n = read(fd, buf, 1000);                                           │ │
│   │  if (n > 0)                                                         │ │
│   │      process(buf, n);  /* Use actual byte count */                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Busy-Wait Anti-Pattern

A naive approach to non-blocking I/O leads to **busy waiting**:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE BUSY-WAIT PROBLEM                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WRONG: Busy-wait loop (wastes CPU!)                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  /* Set non-blocking mode */                                        │ │
│   │  fcntl(fd, F_SETFL, O_NONBLOCK);                                    │ │
│   │                                                                     │ │
│   │  /* Busy wait - TERRIBLE! */                                        │ │
│   │  for (;;) {                                                         │ │
│   │      n = read(fd, buf, sizeof(buf));                                │ │
│   │      if (n > 0) {                                                   │ │
│   │          process(buf, n);                                           │ │
│   │          break;                                                     │ │
│   │      }                                                              │ │
│   │      /* n == -1 && errno == EAGAIN */                               │ │
│   │      /* Loop again immediately - burns CPU! */                      │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CPU USAGE VISUALIZATION:                                                 │
│                                                                            │
│   Blocking I/O:                                                            │
│   CPU |____████____|  (Low usage - process sleeps while waiting)           │
│                                                                            │
│   Non-blocking + Busy wait:                                                │
│   CPU |████████████|  (100% usage! Checking constantly!)                   │
│                                                                            │
│   This is WORSE than blocking! We've traded sleeping for spinning.         │
│                                                                            │
│   The solution? I/O MULTIPLEXING (select, poll, epoll)                     │
│   "Tell me WHEN data is ready, so I don't have to keep asking."            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. I/O Multiplexing

### The Problem: Monitoring Multiple File Descriptors

Consider a server handling 1000 client connections. How does it know which sockets have data?

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE MULTIPLE FD PROBLEM                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Server with 1000 client connections:                                     │
│                                                                            │
│   fd 3  ──── Client A (no data)                                            │
│   fd 4  ──── Client B (no data)                                            │
│   fd 5  ──── Client C (HAS DATA!) ◄─── How do we know?                     │
│   fd 6  ──── Client D (no data)                                            │
│   fd 7  ──── Client E (no data)                                            │
│   ...                                                                      │
│   fd 1002 ─── Client Z (no data)                                           │
│                                                                            │
│   NAIVE APPROACHES:                                                        │
│                                                                            │
│   1. One thread per connection:                                            │
│      ┌─────────────────────────────────────────────────────────────────┐  │
│      │  for each client:                                               │  │
│      │      create_thread(handle_client, client_fd);                   │  │
│      │                                                                 │  │
│      │  Problem: 1000 threads = huge memory overhead!                  │  │
│      │           Context switching kills performance                   │  │
│      │           C10K problem: doesn't scale beyond ~10,000            │  │
│      └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   2. Non-blocking + polling each fd:                                       │
│      ┌─────────────────────────────────────────────────────────────────┐  │
│      │  for (;;) {                                                     │  │
│      │      for (i = 0; i < 1000; i++) {                               │  │
│      │          n = read(fds[i], buf, ...);  /* Non-blocking */        │  │
│      │          if (n > 0) handle(buf);                                │  │
│      │      }                                                          │  │
│      │  }                                                              │  │
│      │                                                                 │  │
│      │  Problem: 1000 system calls per iteration!                      │  │
│      │           Burns CPU checking fds with no data                   │  │
│      └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   THE SOLUTION: Ask kernel "which fds are ready?" in ONE system call       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### select() - The Original Multiplexer

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SELECT() SYSTEM CALL                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int select(int nfds,                                                     │
│              fd_set *readfds,     /* Watch for read readiness */           │
│              fd_set *writefds,    /* Watch for write readiness */          │
│              fd_set *exceptfds,   /* Watch for exceptions */               │
│              struct timeval *timeout);                                     │
│                                                                            │
│   USAGE PATTERN:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  fd_set readfds;                                                    │ │
│   │                                                                     │ │
│   │  while (1) {                                                        │ │
│   │      FD_ZERO(&readfds);              /* Clear the set */            │ │
│   │      FD_SET(fd1, &readfds);          /* Add fd1 to watch */         │ │
│   │      FD_SET(fd2, &readfds);          /* Add fd2 to watch */         │ │
│   │      FD_SET(fd3, &readfds);          /* Add fd3 to watch */         │ │
│   │                                                                     │ │
│   │      /* Block until at least one fd is ready */                     │ │
│   │      n = select(maxfd + 1, &readfds, NULL, NULL, NULL);             │ │
│   │                                                                     │ │
│   │      /* Check which fds are ready */                                │ │
│   │      if (FD_ISSET(fd1, &readfds)) handle(fd1);                      │ │
│   │      if (FD_ISSET(fd2, &readfds)) handle(fd2);                      │ │
│   │      if (FD_ISSET(fd3, &readfds)) handle(fd3);                      │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL INTERNALS:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  algorithm: sys_select                                              │ │
│   │  {                                                                  │ │
│   │      /* Copy fd_set from user space */                              │ │
│   │      copy_from_user(&kreadfds, readfds, sizeof(fd_set));            │ │
│   │                                                                     │ │
│   │      for (;;) {                                                     │ │
│   │          /* Check each fd in the set */                             │ │
│   │          for (fd = 0; fd < nfds; fd++) {                            │ │
│   │              if (FD_ISSET(fd, &kreadfds)) {                         │ │
│   │                  file = fget(fd);                                   │ │
│   │                  /* Ask the file if it's readable */                │ │
│   │                  if (file->f_op->poll(file) & POLLIN)               │ │
│   │                      FD_SET(fd, &result);                           │ │
│   │              }                                                      │ │
│   │          }                                                          │ │
│   │                                                                     │ │
│   │          if (any_fd_ready || timeout_expired)                       │ │
│   │              break;                                                 │ │
│   │                                                                     │ │
│   │          /* No fd ready - sleep */                                  │ │
│   │          schedule_timeout(remaining_time);                          │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      /* Copy results back to user space */                          │ │
│   │      copy_to_user(readfds, &result, sizeof(fd_set));                │ │
│   │      return num_ready_fds;                                          │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LIMITATIONS OF SELECT:                                                   │
│   • FD_SETSIZE limit (typically 1024 fds)                                  │
│   • Must rebuild fd_set each iteration (kernel modifies it)               │
│   • O(n) kernel scan on each call                                         │
│   • Copies entire fd_set to/from kernel on each call                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Deep Dive: How select() Actually Monitors File Descriptors

The key question is: **How does select() efficiently wait for data without burning CPU?**

The answer lies in **wait queues** - the same mechanism the kernel uses for blocking I/O, but applied cleverly to monitor MULTIPLE file descriptors with a SINGLE sleeping process.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE TWO APPROACHES: WHY SELECT WINS                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   APPROACH 1: Non-blocking + Poll Every FD (THE BAD WAY)                   │
│   ════════════════════════════════════════════════════════                 │
│                                                                            │
│   while (1) {                                                              │
│       for (i = 0; i < 1000; i++) {                                         │
│           n = read(fds[i], buf, size);   /* Non-blocking read */           │
│           if (n > 0) {                                                     │
│               handle_data(buf);                                            │
│           } else if (errno == EAGAIN) {                                    │
│               /* No data - fd not ready */                                 │
│               continue;                                                    │
│           }                                                                │
│       }                                                                    │
│       /* Maybe sleep a bit? usleep(1000)? */                               │
│   }                                                                        │
│                                                                            │
│   TIMELINE (1000 fds, only fd[500] has data):                              │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────>     │
│                                                                            │
│   ┌──────┬──────┬──────┬──────┬─────┬──────┬──────┬──────┬──────┬─────┐   │
│   │read  │read  │read  │ ...  │read │read  │ ...  │read  │sleep │loop │   │
│   │fd[0] │fd[1] │fd[2] │      │fd500│fd501 │      │fd999 │ 1ms  │again│   │
│   │EAGAIN│EAGAIN│EAGAIN│      │DATA!│EAGAIN│      │EAGAIN│      │     │   │
│   └──────┴──────┴──────┴──────┴─────┴──────┴──────┴──────┴──────┴─────┘   │
│    ↑                                                               ↑       │
│    └─────────── 1000 system calls + 1 usleep ─────────────────────┘       │
│                                                                            │
│   PROBLEMS:                                                                │
│   • 1000 system calls per iteration (each costs ~1000 CPU cycles)         │
│   • Each read() requires user→kernel→user transition                       │
│   • If you sleep: adds latency (data arrived, but we're sleeping!)        │
│   • If you don't sleep: 100% CPU spinning                                 │
│   • You process data at fd[500] but still check fd[501] to fd[999]!       │
│                                                                            │
│   COST PER ITERATION:                                                      │
│   • ~1000 system calls × 1000 cycles = ~1,000,000 CPU cycles              │
│   • Plus context switch overhead for each call                            │
│   • WASTED WORK: 999 calls return EAGAIN (nothing to do!)                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   APPROACH 2: select() (THE EFFICIENT WAY)                                 │
│   ════════════════════════════════════════                                 │
│                                                                            │
│   while (1) {                                                              │
│       FD_ZERO(&readfds);                                                   │
│       for (i = 0; i < 1000; i++)                                           │
│           FD_SET(fds[i], &readfds);                                        │
│                                                                            │
│       n = select(maxfd+1, &readfds, NULL, NULL, NULL);  /* ONE syscall! */ │
│                                                                            │
│       for (i = 0; i < 1000; i++) {                                         │
│           if (FD_ISSET(fds[i], &readfds)) {                                │
│               read(fds[i], buf, size);  /* Guaranteed to have data! */     │
│               handle_data(buf);                                            │
│           }                                                                │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   TIMELINE (1000 fds, only fd[500] has data):                              │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────>     │
│                                                                            │
│   ┌───────────────────────────────────┬──────┬──────────────────────────┐  │
│   │          select()                 │read  │       next select()      │  │
│   │   (process SLEEPS until event)    │fd500 │                          │  │
│   │         zzzzZZZZzzz               │DATA! │                          │  │
│   └───────────────────────────────────┴──────┴──────────────────────────┘  │
│    ↑                                   ↑                                   │
│    │ ZERO CPU used while sleeping!     │ ONE read() that succeeds          │
│    └───────────────────────────────────┴──────────────────────────────────│
│                                                                            │
│   COST PER "ROUND":                                                        │
│   • 1 select() system call                                                 │
│   • 0 CPU while sleeping (process is OFF the run queue)                   │
│   • Only read() fds that are ACTUALLY ready                               │
│   • ~1 system call × 1000 cycles = ~1000 CPU cycles (1000x better!)       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HOW SELECT() ACTUALLY WORKS: THE WAIT QUEUE MAGIC       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   When you call select(), here's what happens in the kernel:               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. SETUP: Kernel creates a "poll_table" (callback registration)   │ │
│   │                                                                     │ │
│   │      poll_table                                                     │ │
│   │      ┌──────────────────────────────────┐                           │ │
│   │      │  callback: select_poll_callback  │──── Called when ANY fd   │ │
│   │      │  private:  current process       │     becomes ready         │ │
│   │      └──────────────────────────────────┘                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   2. REGISTRATION: For each fd, kernel calls file->f_op->poll()     │ │
│   │                                                                     │ │
│   │      Each fd type (socket, pipe, etc.) has a poll() function:       │ │
│   │                                                                     │ │
│   │      socket_poll(file, poll_table) {                                │ │
│   │          /* Add caller to socket's wait queue */                    │ │
│   │          poll_wait(file, &socket->wait_queue, poll_table);          │ │
│   │                                                                     │ │
│   │          /* Check if socket currently has data */                   │ │
│   │          if (socket->receive_buffer.len > 0)                        │ │
│   │              return POLLIN;  /* Yes! Data available */              │ │
│   │          return 0;           /* No data yet */                      │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      The poll_wait() function registers our process with this fd!   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   3. STATE: After iterating all fds, we're registered everywhere    │ │
│   │                                                                     │ │
│   │                 fd[0]              fd[1]              fd[2]         │ │
│   │               (socket)            (pipe)            (socket)        │ │
│   │                  │                  │                  │            │ │
│   │                  ▼                  ▼                  ▼            │ │
│   │   ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ │ │
│   │   │    wait_queue     │ │    wait_queue     │ │    wait_queue     │ │ │
│   │   │                   │ │                   │ │                   │ │ │
│   │   │ → [our process]   │ │ → [our process]   │ │ → [our process]   │ │ │
│   │   │ → [other waiter]  │ │                   │ │ → [other waiter]  │ │ │
│   │   └───────────────────┘ └───────────────────┘ └───────────────────┘ │ │
│   │          │                      │                      │            │ │
│   │          └──────────────────────┼──────────────────────┘            │ │
│   │                                 │                                   │ │
│   │                Our process is now on ALL THREE wait queues!         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SLEEP AND WAKEUP MECHANISM                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   4. SLEEP: If no fd is ready, process goes to sleep                │ │
│   │                                                                     │ │
│   │      if (no_fd_ready && !timeout_expired) {                         │ │
│   │          set_current_state(TASK_INTERRUPTIBLE);                     │ │
│   │          schedule();   /* CPU given to other processes */           │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      Process State:   RUNNING  ──────>  SLEEPING                    │ │
│   │      CPU Usage:       Active           ZERO! (not scheduled)        │ │
│   │                                                                     │ │
│   │      ┌─────────────────────────────────────────────────────────┐   │ │
│   │      │                                                         │   │ │
│   │      │   CPU                                                   │   │ │
│   │      │   ┌──────────────────────────────────────────────────┐  │   │ │
│   │      │   │ Process A │ Process B │ Process C │ Process A │ ← │  │   │ │
│   │      │   └──────────────────────────────────────────────────┘  │   │ │
│   │      │                                                         │   │ │
│   │      │   Our process (in select) is NOT using any CPU time!    │   │ │
│   │      │                                                         │   │ │
│   │      └─────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   5. WAKEUP: When data arrives on ANY fd, we get woken up!          │ │
│   │                                                                     │ │
│   │      Network card receives packet for fd[500]:                      │ │
│   │                                                                     │ │
│   │      Network Driver                                                 │ │
│   │           │                                                         │ │
│   │           ▼                                                         │ │
│   │      TCP Layer: "Packet belongs to socket fd[500]"                  │ │
│   │           │                                                         │ │
│   │           ▼                                                         │ │
│   │      Socket: sock->sk_data_ready()                                  │ │
│   │           │                                                         │ │
│   │           ▼                                                         │ │
│   │      wake_up_interruptible(&socket->wait_queue)                     │ │
│   │           │                                                         │ │
│   │           ▼                                                         │ │
│   │      ┌─────────────────────────────────────────────────────────┐   │ │
│   │      │                                                         │   │ │
│   │      │  Wait Queue for fd[500]:                                │   │ │
│   │      │                                                         │   │ │
│   │      │    → [our process] ◄──── WAKE UP!                       │   │ │
│   │      │    → [other process]                                    │   │ │
│   │      │                                                         │   │ │
│   │      └─────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │      Our process moves from SLEEPING → RUNNING                      │ │
│   │      Scheduler will give us CPU time                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   6. CLEANUP: Before returning, kernel removes us from wait queues  │ │
│   │                                                                     │ │
│   │      for each fd we registered with:                                │ │
│   │          remove_from_wait_queue(fd, current_process);               │ │
│   │                                                                     │ │
│   │      This is important! Otherwise we'd get spurious wakeups later.  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SELECT VS BUSY-POLLING: THE EFFICIENCY COMPARISON       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO: 1000 fds, data arrives every 100ms on random fd                │
│                                                                            │
│   ═══════════════════════════════════════════════════════════════════════ │
│   NON-BLOCKING + POLL EVERY FD:                                            │
│   ═══════════════════════════════════════════════════════════════════════ │
│                                                                            │
│   If polling with 1ms sleep:                                               │
│   • 100 iterations per data arrival (100ms / 1ms)                          │
│   • 100 × 1000 = 100,000 system calls per data event!                      │
│   • Latency: up to 1ms (sleeping when data arrives)                        │
│                                                                            │
│   If polling with no sleep (busy-wait):                                    │
│   • Millions of iterations per data arrival                                │
│   • Millions of system calls!                                              │
│   • 100% CPU usage                                                         │
│   • Latency: ~0 (but at what cost?)                                        │
│                                                                            │
│   CPU USAGE GRAPH:                                                         │
│                                                                            │
│   100% │████████████████████████████████████████████████████████████      │
│        │█████████████████ WASTED CPU ████████████████████████████████      │
│        │████████████████████████████████████████████████████████████      │
│     0% └───────────────────────────────────────────────────────────>      │
│         time →                                                             │
│                                                                            │
│   ═══════════════════════════════════════════════════════════════════════ │
│   SELECT():                                                                │
│   ═══════════════════════════════════════════════════════════════════════ │
│                                                                            │
│   • 1 select() call → process sleeps (0 CPU)                               │
│   • Data arrives → kernel wakes us instantly                               │
│   • 1 read() call → get data                                               │
│   • Total: 2 system calls per data event                                   │
│   • Latency: ~0 (woken immediately)                                        │
│   • CPU: 0% while waiting!                                                 │
│                                                                            │
│   CPU USAGE GRAPH:                                                         │
│                                                                            │
│   100% │                                                                   │
│        │                                                                   │
│        │                                 ▃                                 │
│     0% │▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▃▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁>  │
│         time →                          ↑                                  │
│                                   Data arrived,                            │
│                                   brief processing                         │
│                                                                            │
│   ═══════════════════════════════════════════════════════════════════════ │
│   SUMMARY:                                                                 │
│                                                                            │
│   │ Metric              │ Poll Every FD     │ select()            │        │
│   │─────────────────────│───────────────────│─────────────────────│        │
│   │ System calls/event  │ 100,000+          │ 2                   │        │
│   │ CPU while waiting   │ ~100% or latency  │ 0%                  │        │
│   │ Wake latency        │ 0-1ms (tradeoff)  │ ~microseconds       │        │
│   │ Power consumption   │ High              │ Low                 │        │
│   │ Scalability         │ Terrible          │ Good (to ~1000 fds) │        │
│   │                                                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE KEY INSIGHT: EVENT-DRIVEN VS POLLING                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   POLLING (checking constantly):                                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "Is there mail?"  "Is there mail?"  "Is there mail?"             │ │
│   │         │                 │                 │                       │ │
│   │         ▼                 ▼                 ▼                       │ │
│   │   ┌──────────┐      ┌──────────┐      ┌──────────┐                 │ │
│   │   │  Check   │      │  Check   │      │  Check   │                 │ │
│   │   │  mailbox │      │  mailbox │      │  mailbox │                 │ │
│   │   │  (empty) │      │  (empty) │      │  (MAIL!) │                 │ │
│   │   └──────────┘      └──────────┘      └──────────┘                 │ │
│   │                                                                     │ │
│   │   Wasted trips: 2    (You walked to mailbox for nothing!)          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EVENT-DRIVEN (select/poll/epoll - kernel notifies you):                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "Notify me when mail arrives" ─────────────┐                     │ │
│   │                                              │                     │ │
│   │   ┌──────────┐                               ▼                     │ │
│   │   │   You    │                         ┌───────────┐               │ │
│   │   │  (doing  │  ◄───── "DING DONG!" ───│  Mailman  │               │ │
│   │   │  other   │       (kernel wakes     │  arrives  │               │ │
│   │   │  things) │        you up)          └───────────┘               │ │
│   │   └──────────┘                                                     │ │
│   │                                                                     │ │
│   │   Wasted trips: 0    (You only check when notified!)               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   This is why select() is efficient:                                       │
│   • You tell kernel: "Watch these 1000 fds for me"                        │
│   • Kernel: "OK, go to sleep. I'll wake you when something happens."      │
│   • Data arrives on fd[500]                                               │
│   • Kernel: "Wake up! fd[500] has data!"                                  │
│   • You: (read from fd[500], do work, go back to select)                  │
│                                                                            │
│   NO WASTED WORK. NO BURNING CPU. INSTANT NOTIFICATION.                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SELECT'S OVERHEAD: WHY EPOLL IS EVEN BETTER             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   select() is efficient compared to polling, but has its own overhead:     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   EVERY call to select():                                           │ │
│   │                                                                     │ │
│   │   User Space                          Kernel Space                  │ │
│   │   ──────────                          ────────────                  │ │
│   │                                                                     │ │
│   │   fd_set (1024 bits)  ──COPY──>    kernel fd_set                   │ │
│   │                                                                     │ │
│   │                                    for fd = 0 to maxfd:             │ │
│   │                                        if (FD_ISSET(fd)):           │ │
│   │                                            poll_wait(fd)  ◄── O(n) │ │
│   │                                            register callback        │ │
│   │                                                                     │ │
│   │                                    sleep if nothing ready           │ │
│   │                                    ...wake up...                    │ │
│   │                                                                     │ │
│   │                                    for fd = 0 to maxfd:  ◄── O(n)  │ │
│   │                                        check if ready               │ │
│   │                                        remove from wait queues      │ │
│   │                                                                     │ │
│   │   result fd_set      <──COPY──     kernel result                   │ │
│   │                                                                     │ │
│   │   for fd = 0 to maxfd:  ◄── O(n)                                   │ │
│   │       if FD_ISSET(fd, &result)                                     │ │
│   │           handle(fd)                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COST BREAKDOWN:                                                          │
│   • 2 copies (fd_set to kernel, results back) = O(FD_SETSIZE/8) bytes     │
│   • Kernel scans all fds: O(n)                                            │
│   • User scans all fds: O(n)                                              │
│                                                                            │
│   For 1000 fds, this is still MUCH better than 1000 read() calls!         │
│   But for 100,000 fds... this O(n) overhead becomes painful.              │
│                                                                            │
│   That's why epoll exists:                                                │
│   • Registration is ONE TIME (epoll_ctl), not every call                 │
│   • Kernel maintains state, no copying fd_set                             │
│   • Returns ONLY ready fds, not full scan                                 │
│   • O(ready) instead of O(total)                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### poll() - Removing the FD Limit

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POLL() SYSTEM CALL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int poll(struct pollfd *fds, nfds_t nfds, int timeout);                  │
│                                                                            │
│   struct pollfd {                                                          │
│       int   fd;         /* File descriptor to watch */                     │
│       short events;     /* Events to watch FOR (input) */                  │
│       short revents;    /* Events that occurred (output) */                │
│   };                                                                       │
│                                                                            │
│   EVENT FLAGS:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  POLLIN   - Data available to read                                  │ │
│   │  POLLOUT  - Can write without blocking                              │ │
│   │  POLLERR  - Error condition (output only)                           │ │
│   │  POLLHUP  - Hang up (output only)                                   │ │
│   │  POLLNVAL - Invalid fd (output only)                                │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   USAGE PATTERN:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  struct pollfd fds[3];                                              │ │
│   │                                                                     │ │
│   │  fds[0].fd = socket_fd;                                             │ │
│   │  fds[0].events = POLLIN;                                            │ │
│   │                                                                     │ │
│   │  fds[1].fd = pipe_fd;                                               │ │
│   │  fds[1].events = POLLIN;                                            │ │
│   │                                                                     │ │
│   │  fds[2].fd = client_fd;                                             │ │
│   │  fds[2].events = POLLIN | POLLOUT;  /* Watch both */                │ │
│   │                                                                     │ │
│   │  while (1) {                                                        │ │
│   │      n = poll(fds, 3, -1);  /* -1 = wait forever */                 │ │
│   │                                                                     │ │
│   │      for (i = 0; i < 3; i++) {                                      │ │
│   │          if (fds[i].revents & POLLIN) {                             │ │
│   │              handle_read(fds[i].fd);                                │ │
│   │          }                                                          │ │
│   │          if (fds[i].revents & POLLOUT) {                            │ │
│   │              handle_write(fds[i].fd);                               │ │
│   │          }                                                          │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ADVANTAGES OVER SELECT:                                                  │
│   • No artificial fd limit (limited only by memory)                        │
│   • events/revents separation (no need to rebuild on each call)            │
│   • Cleaner API                                                            │
│                                                                            │
│   STILL HAS PROBLEMS:                                                      │
│   • O(n) kernel scan on each call                                          │
│   • Copies entire array to/from kernel on each call                       │
│   • Kernel must iterate through ALL fds even if only 1 is ready           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### epoll() - The Linux Solution

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EPOLL() - LINUX-SPECIFIC HIGH PERFORMANCE               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Three system calls:                                                      │
│                                                                            │
│   int epoll_create(int size);           /* Create epoll instance */        │
│   int epoll_ctl(int epfd, int op,       /* Add/modify/remove fds */        │
│                 int fd, struct epoll_event *event);                        │
│   int epoll_wait(int epfd,              /* Wait for events */              │
│                  struct epoll_event *events,                               │
│                  int maxevents, int timeout);                              │
│                                                                            │
│   THE KEY INSIGHT:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  select/poll: "Here are 1000 fds. Which are ready?"                 │ │
│   │               Kernel scans all 1000. Every. Single. Time.           │ │
│   │                                                                     │ │
│   │  epoll: "Kernel, keep track of these 1000 fds for me.               │ │
│   │         When something happens, just tell me WHICH ONES changed."   │ │
│   │                                                                     │ │
│   │  With select/poll: O(n) per call                                    │ │
│   │  With epoll: O(1) for epoll_wait, O(number of READY fds) for result │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL DATA STRUCTURES:                                                  │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                  │    │
│   │  epoll_create() creates:                                         │    │
│   │                                                                  │    │
│   │  struct eventpoll {                                              │    │
│   │      spinlock_t lock;                                            │    │
│   │      struct rb_root rbr;         /* Red-black tree of watched   │    │
│   │                                      fds - O(log n) lookup */    │    │
│   │      struct list_head rdllist;   /* READY list - fds with       │    │
│   │                                      pending events */           │    │
│   │      wait_queue_head_t wq;       /* Processes waiting in        │    │
│   │                                      epoll_wait() */             │    │
│   │  };                                                              │    │
│   │                                                                  │    │
│   │  epoll_ctl(ADD) creates:                                         │    │
│   │                                                                  │    │
│   │  struct epitem {                                                 │    │
│   │      struct rb_node rbn;         /* Node in red-black tree */   │    │
│   │      struct list_head rdllink;   /* Link in ready list */       │    │
│   │      struct epoll_filefd ffd;    /* fd + file pointer */        │    │
│   │      struct eventpoll *ep;       /* Back pointer to eventpoll */│    │
│   │      struct epoll_event event;   /* User-specified events */    │    │
│   │  };                                                              │    │
│   │                                                                  │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HOW EPOLL WORKS INTERNALLY                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SETUP PHASE (done once per fd):                                          │
│                                                                            │
│   epoll_ctl(epfd, EPOLL_CTL_ADD, socket_fd, &event);                       │
│        │                                                                   │
│        ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  1. Create epitem for this fd                                       │ │
│   │  2. Insert into red-black tree (O(log n))                           │ │
│   │  3. Register CALLBACK with the fd's wait queue                      │ │
│   │                                                                     │ │
│   │     socket_fd's wait queue:                                         │ │
│   │     ┌──────────────────────────────────────────────────┐            │ │
│   │     │  wait_queue_entry {                              │            │ │
│   │     │      .func = ep_poll_callback,  ◄── THE MAGIC!   │            │ │
│   │     │      .private = epitem,                          │            │ │
│   │     │  }                                               │            │ │
│   │     └──────────────────────────────────────────────────┘            │ │
│   │                                                                     │ │
│   │  When socket_fd becomes ready, kernel calls ep_poll_callback!       │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHEN DATA ARRIVES ON socket_fd:                                          │
│                                                                            │
│   Network interrupt → Kernel receives packet → Puts data in socket buffer  │
│        │                                                                   │
│        ▼                                                                   │
│   wake_up(&socket->wait_queue);                                            │
│        │                                                                   │
│        ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  ep_poll_callback() runs:                                           │ │
│   │  {                                                                  │ │
│   │      /* Add this epitem to the READY list */                        │ │
│   │      list_add_tail(&epitem->rdllink, &ep->rdllist);                 │ │
│   │                                                                     │ │
│   │      /* Wake up anyone waiting in epoll_wait() */                   │ │
│   │      wake_up(&ep->wq);                                              │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EPOLL_WAIT:                                                              │
│                                                                            │
│   n = epoll_wait(epfd, events, maxevents, timeout);                        │
│        │                                                                   │
│        ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  if (ready_list is empty) {                                         │ │
│   │      /* Sleep on ep->wq until callback wakes us */                  │ │
│   │      schedule();                                                    │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   │  /* Copy ONLY the ready items to user space */                      │ │
│   │  /* No scanning all fds - just traverse ready list! */              │ │
│   │  for_each_item_in(ready_list) {                                     │ │
│   │      events[n++] = item->event;                                     │ │
│   │  }                                                                  │ │
│   │  return n;                                                          │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### epoll Usage Example

```c
#include <sys/epoll.h>

#define MAX_EVENTS 100

int main() {
    int epfd, nfds, i;
    struct epoll_event ev, events[MAX_EVENTS];

    /* Step 1: Create epoll instance */
    epfd = epoll_create1(0);

    /* Step 2: Add fds to watch */
    ev.events = EPOLLIN;           /* Watch for read readiness */
    ev.data.fd = listen_socket;
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_socket, &ev);

    /* Step 3: Event loop */
    while (1) {
        /* Wait for events - blocks efficiently! */
        nfds = epoll_wait(epfd, events, MAX_EVENTS, -1);

        for (i = 0; i < nfds; i++) {
            if (events[i].data.fd == listen_socket) {
                /* New connection */
                client_fd = accept(listen_socket, ...);

                /* Add new client to epoll */
                ev.events = EPOLLIN | EPOLLET;  /* Edge-triggered */
                ev.data.fd = client_fd;
                epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &ev);
            } else {
                /* Data from existing client */
                handle_client(events[i].data.fd);
            }
        }
    }
}
```

### kqueue() - BSD's Answer

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KQUEUE() - BSD/macOS                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BSD (FreeBSD, OpenBSD, NetBSD) and macOS use kqueue:                     │
│                                                                            │
│   int kqueue(void);                                                        │
│   int kevent(int kq,                                                       │
│              const struct kevent *changelist, int nchanges,                │
│              struct kevent *eventlist, int nevents,                        │
│              const struct timespec *timeout);                              │
│                                                                            │
│   ADVANTAGES:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Similar O(1) performance to epoll                                │ │
│   │  • Can monitor MORE than just file descriptors:                     │ │
│   │    - File descriptors (EVFILT_READ, EVFILT_WRITE)                   │ │
│   │    - Signals (EVFILT_SIGNAL)                                        │ │
│   │    - Process events (EVFILT_PROC)                                   │ │
│   │    - Timers (EVFILT_TIMER)                                          │ │
│   │    - File system changes (EVFILT_VNODE)                             │ │
│   │  • More unified API than Linux's separate mechanisms                │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   USAGE:                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  int kq = kqueue();                                                 │ │
│   │                                                                     │ │
│   │  struct kevent change;                                              │ │
│   │  EV_SET(&change, socket_fd, EVFILT_READ, EV_ADD, 0, 0, NULL);       │ │
│   │  kevent(kq, &change, 1, NULL, 0, NULL);  /* Register */             │ │
│   │                                                                     │ │
│   │  struct kevent events[10];                                          │ │
│   │  n = kevent(kq, NULL, 0, events, 10, NULL);  /* Wait */             │ │
│   │  for (i = 0; i < n; i++) {                                          │ │
│   │      handle(events[i].ident);  /* events[i].ident = fd */           │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Comparison Table

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    I/O MULTIPLEXING COMPARISON                             │
├─────────────┬───────────────┬───────────────┬───────────────┬─────────────┤
│             │    select()   │    poll()     │    epoll()    │   kqueue()  │
├─────────────┼───────────────┼───────────────┼───────────────┼─────────────┤
│ Max fds     │ 1024 (typical)│ No limit      │ No limit      │ No limit    │
├─────────────┼───────────────┼───────────────┼───────────────┼─────────────┤
│ Complexity  │ O(n)          │ O(n)          │ O(1) wait     │ O(1) wait   │
│ (per call)  │               │               │ O(ready) copy │ O(ready)    │
├─────────────┼───────────────┼───────────────┼───────────────┼─────────────┤
│ fd passing  │ Copy entire   │ Copy entire   │ Once at       │ Once at     │
│             │ set each call │ array each    │ registration  │ registration│
├─────────────┼───────────────┼───────────────┼───────────────┼─────────────┤
│ Portability │ POSIX         │ POSIX         │ Linux only    │ BSD/macOS   │
├─────────────┼───────────────┼───────────────┼───────────────┼─────────────┤
│ Edge vs     │ Level only    │ Level only    │ Both          │ Both        │
│ Level       │               │               │               │             │
├─────────────┼───────────────┼───────────────┼───────────────┼─────────────┤
│ Use case    │ Portability   │ Portability,  │ Linux high-   │ BSD high-   │
│             │ small fd sets │ >1024 fds     │ performance   │ performance │
├─────────────┴───────────────┴───────────────┴───────────────┴─────────────┤
│                                                                            │
│   SCALING VISUALIZATION (1000 fds, 10 are ready):                          │
│                                                                            │
│   select/poll:                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐│
│   │  Copy 1000 fds to kernel                                             ││
│   │  Scan all 1000 fds                                                   ││
│   │  Copy 1000 fds back                                                  ││
│   │  User scans 1000 fds to find 10 ready                                ││
│   └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
│   epoll/kqueue:                                                            │
│   ┌──────────────────────────────────────────────────────────────────────┐│
│   │  (fds already registered)                                            ││
│   │  Kernel copies 10 ready fds                                          ││
│   │  User processes 10 fds                                               ││
│   └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Advanced Topics

### Level-Triggered vs Edge-Triggered

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LEVEL-TRIGGERED vs EDGE-TRIGGERED                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   LEVEL-TRIGGERED (default):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  "Tell me whenever the fd IS ready"                                 │ │
│   │                                                                     │ │
│   │  fd state:    ─────┐          ┌─────────────────                    │ │
│   │                    │          │                                     │ │
│   │                    └──────────┘                                     │ │
│   │                     (data in buffer)                                │ │
│   │                                                                     │ │
│   │  notifications: ▲  ▲  ▲  ▲  ▲  (reported EVERY time you check)      │ │
│   │                                                                     │ │
│   │  • If you don't read all data, you'll be notified again            │ │
│   │  • Simple to program - hard to miss events                         │ │
│   │  • Can cause unnecessary wakeups if you're not ready to read       │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EDGE-TRIGGERED (EPOLLET flag):                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  "Tell me when the fd BECOMES ready (state change)"                 │ │
│   │                                                                     │ │
│   │  fd state:    ─────┐          ┌─────────────────                    │ │
│   │                    │          │                                     │ │
│   │                    └──────────┘                                     │ │
│   │                     (data in buffer)                                │ │
│   │                                                                     │ │
│   │  notifications: ▲             ▲  (only on TRANSITIONS)              │ │
│   │                 │             │                                     │ │
│   │                 └─ became     └─ became ready again                 │ │
│   │                    ready         (after being empty)                │ │
│   │                                                                     │ │
│   │  • MUST read until EAGAIN, or you'll never be notified again!      │ │
│   │  • More efficient - fewer wakeups                                  │ │
│   │  • Harder to program correctly                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   EDGE-TRIGGERED PITFALL:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  /* WRONG - may miss data! */                                       │ │
│   │  n = read(fd, buf, 100);  /* Only reads 100 bytes */                │ │
│   │  /* If 200 bytes arrived, you'll never know about the other 100! */ │ │
│   │                                                                     │ │
│   │  /* RIGHT - read until empty */                                     │ │
│   │  while ((n = read(fd, buf, sizeof(buf))) > 0) {                     │ │
│   │      process(buf, n);                                               │ │
│   │  }                                                                  │ │
│   │  if (n == -1 && errno != EAGAIN) { error(); }                       │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Thundering Herd Problem

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE THUNDERING HERD                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO: Multiple processes waiting on the same fd (e.g., accept())    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Worker 1 ──┐                                                      │ │
│   │   Worker 2 ──┤                                                      │ │
│   │   Worker 3 ──┼──── All blocked on accept(listen_fd)                 │ │
│   │   Worker 4 ──┤                                                      │ │
│   │   Worker 5 ──┘                                                      │ │
│   │                                                                     │ │
│   │   Connection arrives!                                               │ │
│   │          │                                                          │ │
│   │          ▼                                                          │ │
│   │                                                                     │ │
│   │   OLD BEHAVIOR (thundering herd):                                   │ │
│   │   ┌────────────────────────────────────────────────────────┐       │ │
│   │   │  wake_up(&listen_fd->wait_queue);                      │       │ │
│   │   │  /* ALL 5 workers wake up! */                          │       │ │
│   │   │  /* 4 workers find connection already accepted */      │       │ │
│   │   │  /* 4 workers go back to sleep - WASTED WORK! */       │       │ │
│   │   └────────────────────────────────────────────────────────┘       │ │
│   │                                                                     │ │
│   │   SOLUTION: EPOLLEXCLUSIVE (Linux 4.5+)                             │ │
│   │   ┌────────────────────────────────────────────────────────┐       │ │
│   │   │  ev.events = EPOLLIN | EPOLLEXCLUSIVE;                 │       │ │
│   │   │  /* Only ONE worker wakes up per event! */             │       │ │
│   │   └────────────────────────────────────────────────────────┘       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   OTHER SOLUTIONS:                                                         │
│   • SO_REUSEPORT - each worker gets own queue, kernel load-balances        │
│   • Accept mutex - serialize accept() calls (nginx approach pre-kernel)   │
│   • Single accept thread - one thread accepts, distributes to workers     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Asynchronous I/O (AIO)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ASYNCHRONOUS I/O                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BLOCKING:                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Process: "read()"                                                  │ │
│   │  Kernel:  "OK, sleep while I get data"                              │ │
│   │  ...time passes...                                                  │ │
│   │  Kernel:  "Here's your data"                                        │ │
│   │  Process: "Great, I'll process it now"                              │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NON-BLOCKING + MULTIPLEXING:                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Process: "epoll_wait() - tell me when ready"                       │ │
│   │  Kernel:  "OK, sleep until something is ready"                      │ │
│   │  ...time passes...                                                  │ │
│   │  Kernel:  "fd 5 is ready!"                                          │ │
│   │  Process: "read(fd5)" - now this doesn't block                      │ │
│   │  Process: "process(data)"                                           │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TRUE ASYNCHRONOUS:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Process: "aio_read() - start reading, don't wait"                  │ │
│   │  Kernel:  "OK, I'll do it in the background"                        │ │
│   │  Process: /* immediately continues - does other work! */            │ │
│   │  ...kernel reads data in background...                              │ │
│   │  Kernel:  "Done! Here's a signal/callback/event"                    │ │
│   │  Process: "process(data)"                                           │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  CRITICAL QUESTION: "What other work? If no fd has data, won't      │ │
│   │  the process just sleep anyway - same as epoll_wait()?"             │ │
│   │                                                                     │ │
│   │  ANSWER: The key difference is what the process does WHILE WAITING: │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NON-BLOCKING + MULTIPLEXING (epoll):                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  TIME ──────────────────────────────────────────────────────────>   │ │
│   │                                                                     │ │
│   │  Process: [epoll_wait()]----SLEEPING----[wake][read][process]       │ │
│   │                │                           │                        │ │
│   │                └── Process is BLOCKED ─────┘                        │ │
│   │                    Cannot do ANY work                               │ │
│   │                    CPU runs other processes                         │ │
│   │                                                                     │ │
│   │  The process MUST sleep in epoll_wait() until some fd is ready.     │ │
│   │  If no fd has data, the process does NOTHING - it's sleeping!       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TRUE ASYNCHRONOUS (io_uring/AIO):                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  TIME ──────────────────────────────────────────────────────────>   │ │
│   │                                                                     │ │
│   │  Process: [submit I/O][compute][compute][compute][check CQ][process]│ │
│   │                │          │        │        │         │             │ │
│   │                │          └────────┴────────┘         │             │ │
│   │                │          Process keeps RUNNING!      │             │ │
│   │                │          Doing CPU-bound work        │             │ │
│   │                │                                      │             │ │
│   │  Kernel:       └──[doing I/O in background]───────────┘             │ │
│   │                                                                     │ │
│   │  The process NEVER sleeps! It keeps running, doing other work.      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHAT "OTHER WORK" CAN THE PROCESS DO?                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  1. CPU-BOUND COMPUTATIONS:                                         │ │
│   │     • Encryption/decryption of previously received data             │ │
│   │     • Compression/decompression                                     │ │
│   │     • Mathematical calculations, simulations                        │ │
│   │     • Parsing/serialization (JSON, protobuf, etc.)                  │ │
│   │                                                                     │ │
│   │  2. PROCESSING COMPLETED I/O:                                       │ │
│   │     • While waiting for request #5, process results of request #3   │ │
│   │     • Pipeline: submit → compute on old data → check completion     │ │
│   │                                                                     │ │
│   │  3. PREPARING NEXT BATCH:                                           │ │
│   │     • Build next set of I/O requests                                │ │
│   │     • Allocate buffers, prepare data structures                     │ │
│   │                                                                     │ │
│   │  4. APPLICATION LOGIC:                                              │ │
│   │     • Game: render frames while loading assets                      │ │
│   │     • Server: handle in-memory requests while disk I/O pending      │ │
│   │     • Database: process queries while fetching pages from disk      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONCRETE EXAMPLE - Image Processing Server:                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  WITH EPOLL (non-blocking + multiplexing):                          │ │
│   │  ┌───────────────────────────────────────────────────────────────┐  │ │
│   │  │  while (1) {                                                  │  │ │
│   │  │      n = epoll_wait(epfd, events, ...);  // BLOCKS HERE!      │  │ │
│   │  │      for (i = 0; i < n; i++) {                                │  │ │
│   │  │          read(events[i].fd, buf, ...);   // get image         │  │ │
│   │  │          process_image(buf);              // CPU-heavy!       │  │ │
│   │  │          write(out_fd, result, ...);     // send result       │  │ │
│   │  │      }                                                        │  │ │
│   │  │  }                                                            │  │ │
│   │  │                                                               │  │ │
│   │  │  Problem: While blocked in epoll_wait(), CPU is IDLE.         │  │ │
│   │  │  We could be processing images, but we're sleeping!           │  │ │
│   │  └───────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │  WITH TRUE ASYNC (io_uring):                                        │ │
│   │  ┌───────────────────────────────────────────────────────────────┐  │ │
│   │  │  // Submit read requests for images 1, 2, 3                   │  │ │
│   │  │  io_uring_submit_read(ring, fd1, buf1);                       │  │ │
│   │  │  io_uring_submit_read(ring, fd2, buf2);                       │  │ │
│   │  │  io_uring_submit_read(ring, fd3, buf3);                       │  │ │
│   │  │                                                               │  │ │
│   │  │  while (1) {                                                  │  │ │
│   │  │      // Check if any I/O completed (NON-BLOCKING peek!)       │  │ │
│   │  │      cqe = io_uring_peek_cqe(ring);  // Does NOT block!       │  │ │
│   │  │                                                               │  │ │
│   │  │      if (cqe) {                                               │  │ │
│   │  │          // I/O completed - add to processing queue           │  │ │
│   │  │          enqueue_for_processing(cqe->user_data);              │  │ │
│   │  │          io_uring_cqe_seen(ring, cqe);                        │  │ │
│   │  │          // Submit another read to keep pipeline full         │  │ │
│   │  │          io_uring_submit_read(ring, next_fd, next_buf);       │  │ │
│   │  │      }                                                        │  │ │
│   │  │                                                               │  │ │
│   │  │      // Process images from queue (CPU work!)                 │  │ │
│   │  │      if (has_work_in_queue()) {                               │  │ │
│   │  │          img = dequeue();                                     │  │ │
│   │  │          process_image(img);  // CPU stays busy!              │  │ │
│   │  │      }                                                        │  │ │
│   │  │  }                                                            │  │ │
│   │  │                                                               │  │ │
│   │  │  Benefit: CPU processes images WHILE kernel fetches more!     │  │ │
│   │  │  I/O and computation happen IN PARALLEL.                      │  │ │
│   │  └───────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BUT WHAT IF THERE'S NO CPU WORK TO DO?                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  If your application is PURELY I/O-bound (no CPU work between I/O   │ │
│   │  operations), then TRUE ASYNC provides NO BENEFIT over epoll!       │ │
│   │                                                                     │ │
│   │  Example - Simple proxy server:                                     │ │
│   │  ┌───────────────────────────────────────────────────────────────┐  │ │
│   │  │  // Just forwards data, no processing                         │  │ │
│   │  │  while (1) {                                                  │  │ │
│   │  │      read(client_fd, buf, ...);                               │  │ │
│   │  │      write(server_fd, buf, ...);  // No CPU work here!        │  │ │
│   │  │  }                                                            │  │ │
│   │  └───────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │  For this workload, epoll is just as good as io_uring.              │ │
│   │  The process has nothing to do while waiting anyway!                │ │
│   │                                                                     │ │
│   │  TRUE ASYNC SHINES WHEN:                                            │ │
│   │  • You have CPU work to do between I/O operations                   │ │
│   │  • You want to overlap I/O with computation                         │ │
│   │  • You're doing disk I/O (where epoll doesn't help at all!)         │ │
│   │  • You want to batch many I/O operations efficiently                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY DIFFERENCE SUMMARY:                                                  │
│   • Non-blocking + epoll: "Wake me when SOMETHING is ready" (still sleeps)│
│   • True async: "Start I/O, I'll keep working, tell me when DONE"         │
│                                                                            │
│   POSIX AIO (aio_read, aio_write):                                         │
│   • Works on regular files (unlike epoll)                                  │
│   • Poorly implemented on most systems (uses thread pool internally)      │
│   • Limited practical use                                                  │
│                                                                            │
│   LINUX io_uring (5.1+):                                                   │
│   • True kernel async I/O                                                  │
│   • Single interface for all I/O types                                     │
│   • Zero-copy where possible                                               │
│   • The future of Linux I/O                                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### io_uring - The Future of Linux I/O

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IO_URING ARCHITECTURE                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   io_uring uses two ring buffers shared between user space and kernel:    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   USER SPACE                           KERNEL SPACE                 │ │
│   │   ┌─────────────────┐                                               │ │
│   │   │                 │                                               │ │
│   │   │  Application    │                                               │ │
│   │   │                 │                                               │ │
│   │   └───────┬─────────┘                                               │ │
│   │           │                                                         │ │
│   │           ▼                                                         │ │
│   │   ┌─────────────────┐    SHARED     ┌─────────────────┐             │ │
│   │   │  Submission     │◄─────────────►│  Kernel reads   │             │ │
│   │   │  Queue (SQ)     │    MEMORY     │  submissions    │             │ │
│   │   │                 │               │                 │             │ │
│   │   │  [read fd=5]    │               │  Does the I/O   │             │ │
│   │   │  [write fd=7]   │               │  async!         │             │ │
│   │   │  [send fd=10]   │               │                 │             │ │
│   │   └─────────────────┘               └────────┬────────┘             │ │
│   │                                              │                      │ │
│   │   ┌─────────────────┐               ┌────────▼────────┐             │ │
│   │   │  Completion     │◄──────────────│  Kernel writes  │             │ │
│   │   │  Queue (CQ)     │    SHARED     │  completions    │             │ │
│   │   │                 │    MEMORY     │                 │             │ │
│   │   │  [read done: 5] │               │                 │             │ │
│   │   │  [write done: 7]│               │                 │             │ │
│   │   └─────────────────┘               └─────────────────┘             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ADVANTAGES:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • ZERO system calls in fast path (polling mode)                    │ │
│   │  • ZERO copies between user/kernel for ring management              │ │
│   │  • Batch submissions - one syscall can start many operations        │ │
│   │  • Works on ALL I/O: files, sockets, pipes, even fsync!             │ │
│   │  • Fixed buffers for zero-copy I/O                                  │ │
│   │  • Linked operations (operation B starts when A completes)          │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BASIC USAGE:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  struct io_uring ring;                                              │ │
│   │  io_uring_queue_init(32, &ring, 0);                                 │ │
│   │                                                                     │ │
│   │  /* Get a submission queue entry */                                 │ │
│   │  struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);                │ │
│   │                                                                     │ │
│   │  /* Prepare a read operation */                                     │ │
│   │  io_uring_prep_read(sqe, fd, buf, len, offset);                     │ │
│   │                                                                     │ │
│   │  /* Submit to kernel */                                             │ │
│   │  io_uring_submit(&ring);                                            │ │
│   │                                                                     │ │
│   │  /* Wait for completion */                                          │ │
│   │  struct io_uring_cqe *cqe;                                          │ │
│   │  io_uring_wait_cqe(&ring, &cqe);                                    │ │
│   │                                                                     │ │
│   │  /* Process result */                                               │ │
│   │  int result = cqe->res;  /* bytes read, or negative error */        │ │
│   │  io_uring_cqe_seen(&ring, cqe);                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### io_uring Deep Dive - Ring Buffer Mechanics

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SUBMISSION QUEUE (SQ) INTERNALS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The SQ is a circular buffer with head and tail pointers:                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SUBMISSION QUEUE ENTRY (SQE) - 64 bytes each                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  struct io_uring_sqe {                                      │   │ │
│   │   │      __u8    opcode;      /* IORING_OP_READ, _WRITE, etc */ │   │ │
│   │   │      __u8    flags;       /* IOSQE_FIXED_FILE, etc */       │   │ │
│   │   │      __u16   ioprio;      /* I/O priority */                │   │ │
│   │   │      __s32   fd;          /* file descriptor */             │   │ │
│   │   │      __u64   off;         /* offset in file */              │   │ │
│   │   │      __u64   addr;        /* pointer to buffer */           │   │ │
│   │   │      __u32   len;         /* buffer length */               │   │ │
│   │   │      __u64   user_data;   /* returned in CQE - YOUR TAG! */ │   │ │
│   │   │      ...                                                    │   │ │
│   │   │  }                                                          │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   RING BUFFER LAYOUT (example with 8 entries):                      │ │
│   │                                                                     │ │
│   │        tail (user writes here)                                      │ │
│   │          │                                                          │ │
│   │          ▼                                                          │ │
│   │   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                │ │
│   │   │ SQE │ SQE │ SQE │     │     │     │     │     │                │ │
│   │   │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │                │ │
│   │   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                │ │
│   │     ▲                                                               │ │
│   │     │                                                               │ │
│   │   head (kernel reads from here)                                     │ │
│   │                                                                     │ │
│   │   User increments tail after adding SQE                             │ │
│   │   Kernel increments head after consuming SQE                        │ │
│   │   When tail == head: queue is empty                                 │ │
│   │   When (tail + 1) % size == head: queue is full                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HOW SUBMISSION WORKS (no syscall in polling mode!):                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. User gets free SQE:     sqe = &sq_ring[tail % size]            │ │
│   │   2. User fills in SQE:      sqe->opcode = IORING_OP_READ; ...      │ │
│   │   3. User increments tail:   tail++  (memory barrier!)              │ │
│   │   4. Kernel sees new tail:   "Oh, new work to do!"                  │ │
│   │   5. Kernel processes SQE:   starts the I/O operation               │ │
│   │   6. Kernel increments head: "Done consuming this SQE"              │ │
│   │                                                                     │ │
│   │   In POLLING MODE: No syscall needed! Kernel thread polls the ring. │ │
│   │   In NORMAL MODE:  io_uring_submit() syscall notifies kernel.       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETION QUEUE (CQ) INTERNALS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The CQ is where kernel reports completed operations:                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   COMPLETION QUEUE ENTRY (CQE) - 16 bytes each                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  struct io_uring_cqe {                                      │   │ │
│   │   │      __u64   user_data;   /* copied from SQE - YOUR TAG! */ │   │ │
│   │   │      __s32   res;         /* result: bytes transferred or  ││   │ │
│   │   │                              negative errno on error */     │   │ │
│   │   │      __u32   flags;       /* IORING_CQE_F_BUFFER, etc */    │   │ │
│   │   │  }                                                          │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   THE user_data FIELD IS CRUCIAL:                                   │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  When you submit:  sqe->user_data = (uint64_t)my_context;   │   │ │
│   │   │  When complete:    my_context = (void*)cqe->user_data;      │   │ │
│   │   │                                                             │   │ │
│   │   │  This is how you match completions to requests!             │   │ │
│   │   │  Store a pointer to your request context, connection        │   │ │
│   │   │  object, or any identifier you need.                        │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   RING BUFFER LAYOUT:                                               │ │
│   │                                                                     │ │
│   │        head (user reads from here)                                  │ │
│   │          │                                                          │ │
│   │          ▼                                                          │ │
│   │   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐                │ │
│   │   │ CQE │ CQE │ CQE │ CQE │     │     │     │     │                │ │
│   │   │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │                │ │
│   │   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘                │ │
│   │                       ▲                                             │ │
│   │                       │                                             │ │
│   │                     tail (kernel writes here)                       │ │
│   │                                                                     │ │
│   │   Kernel increments tail after adding CQE                           │ │
│   │   User increments head after consuming CQE                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### io_uring Usage Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PATTERN 1: BLOCKING WAIT (Simple)                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Use when: You have nothing else to do until I/O completes                │
│   Similar to: Blocking read(), but can batch multiple operations           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  // Submit multiple reads at once                                   │ │
│   │  for (int i = 0; i < 10; i++) {                                     │ │
│   │      struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);            │ │
│   │      io_uring_prep_read(sqe, fds[i], bufs[i], len, 0);              │ │
│   │      sqe->user_data = i;  // Tag with index                         │ │
│   │  }                                                                  │ │
│   │  io_uring_submit(&ring);  // One syscall for 10 operations!         │ │
│   │                                                                     │ │
│   │  // Wait for ALL to complete (blocking)                             │ │
│   │  for (int i = 0; i < 10; i++) {                                     │ │
│   │      struct io_uring_cqe *cqe;                                      │ │
│   │      io_uring_wait_cqe(&ring, &cqe);  // BLOCKS until one ready     │ │
│   │                                                                     │ │
│   │      int idx = cqe->user_data;                                      │ │
│   │      int bytes = cqe->res;                                          │ │
│   │      printf("Read %d completed: %d bytes\n", idx, bytes);           │ │
│   │                                                                     │ │
│   │      io_uring_cqe_seen(&ring, cqe);  // Mark as consumed            │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TIMELINE:                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Process: [submit 10]──[wait]─────────────[process]──[wait]──...    │ │
│   │                           │                   │         │           │ │
│   │                        BLOCKED             got one   BLOCKED        │ │
│   │                                                                     │ │
│   │  Kernel:           [I/O 1]────────────────────┐                     │ │
│   │                    [I/O 2]──────────┐         │                     │ │
│   │                    [I/O 3]────┐     │         │                     │ │
│   │                    ...        │     │         │                     │ │
│   │                               ▼     ▼         ▼                     │ │
│   │                            (completions arrive out of order)        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BENEFIT: Batching! 10 operations with 2 syscalls (submit + wait)         │
│   vs traditional: 20 syscalls (10 reads + 10 waits)                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PATTERN 2: NON-BLOCKING PEEK (True Async)               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Use when: You have CPU work to do while waiting for I/O                  │
│   This is TRUE ASYNCHRONOUS - process never sleeps!                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  // Submit I/O requests                                             │ │
│   │  submit_read_requests(&ring, files, buffers, count);                │ │
│   │                                                                     │ │
│   │  int pending = count;                                               │ │
│   │  while (pending > 0 || has_cpu_work()) {                            │ │
│   │                                                                     │ │
│   │      // NON-BLOCKING check for completions                          │ │
│   │      struct io_uring_cqe *cqe;                                      │ │
│   │      while (io_uring_peek_cqe(&ring, &cqe) == 0) {  // NO BLOCK!    │ │
│   │          // Process completed I/O                                   │ │
│   │          handle_completion(cqe);                                    │ │
│   │          io_uring_cqe_seen(&ring, cqe);                             │ │
│   │          pending--;                                                 │ │
│   │                                                                     │ │
│   │          // Maybe submit more I/O to keep pipeline full             │ │
│   │          if (has_more_files()) {                                    │ │
│   │              submit_next_read(&ring);                               │ │
│   │              pending++;                                             │ │
│   │          }                                                          │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      // Do CPU-bound work (THIS IS THE KEY DIFFERENCE!)             │ │
│   │      if (has_cpu_work()) {                                          │ │
│   │          do_some_computation();  // Encrypt, compress, calculate    │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TIMELINE - CPU AND I/O OVERLAP:                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Process: [submit][cpu][cpu][peek+process][cpu][peek+process][cpu]  │ │
│   │              │      │    │        │         │        │         │    │ │
│   │              │      └────┴────────┴─────────┴────────┴─────────┘    │ │
│   │              │           NEVER SLEEPS! Always doing useful work     │ │
│   │              │                                                      │ │
│   │  Kernel:    [I/O 1]───────────────┐                                 │ │
│   │             [I/O 2]─────┐         │                                 │ │
│   │             [I/O 3]───────────┐   │                                 │ │
│   │                         │     │   │                                 │ │
│   │                         ▼     ▼   ▼                                 │ │
│   │                      (completions added to CQ)                      │ │
│   │                                                                     │ │
│   │  OVERLAP: CPU work happens IN PARALLEL with kernel I/O!             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMPARISON WITH EPOLL:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  EPOLL:     [epoll_wait]──SLEEPING──[wake][read][cpu][epoll_wait]   │ │
│   │                  │                     │                  │         │ │
│   │                  └─────────────────────┴──────────────────┘         │ │
│   │                        Process sleeps between events!               │ │
│   │                                                                     │ │
│   │  IO_URING:  [submit][cpu][cpu][peek][cpu][peek][cpu][cpu][peek]     │ │
│   │                       │    │    │     │    │     │    │    │        │ │
│   │                       └────┴────┴─────┴────┴─────┴────┴────┘        │ │
│   │                        Process NEVER sleeps! Always working!        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PATTERN 3: HYBRID (Adaptive)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Use when: Sometimes you have CPU work, sometimes you don't               │
│   Best of both worlds - work when you can, sleep when you can't            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  while (running) {                                                  │ │
│   │      // First, drain all ready completions (non-blocking)           │ │
│   │      struct io_uring_cqe *cqe;                                      │ │
│   │      while (io_uring_peek_cqe(&ring, &cqe) == 0) {                  │ │
│   │          handle_completion(cqe);                                    │ │
│   │          io_uring_cqe_seen(&ring, cqe);                             │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      // Do available CPU work                                       │ │
│   │      while (has_cpu_work()) {                                       │ │
│   │          do_one_unit_of_cpu_work();                                 │ │
│   │                                                                     │ │
│   │          // Periodically check for completions                      │ │
│   │          if (work_units++ % 100 == 0) {                             │ │
│   │              while (io_uring_peek_cqe(&ring, &cqe) == 0) {          │ │
│   │                  handle_completion(cqe);                            │ │
│   │                  io_uring_cqe_seen(&ring, cqe);                     │ │
│   │              }                                                      │ │
│   │          }                                                          │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      // No CPU work left - NOW we can sleep efficiently             │ │
│   │      if (has_pending_io()) {                                        │ │
│   │          // Wait with timeout - don't sleep forever                 │ │
│   │          struct __kernel_timespec ts = {.tv_sec = 0, .tv_nsec = 1000000};│
│   │          io_uring_wait_cqe_timeout(&ring, &cqe, &ts);  // 1ms max   │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TIMELINE - ADAPTIVE BEHAVIOR:                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Lots of CPU work:                                                  │ │
│   │  [submit][cpu][cpu][peek][cpu][cpu][peek][cpu][cpu][peek]...        │ │
│   │           └────────────────────────────────────────────┘            │ │
│   │                    Never sleeps - always busy                       │ │
│   │                                                                     │ │
│   │  No CPU work:                                                       │ │
│   │  [submit][peek][wait 1ms][peek][wait 1ms][peek][completion!][...]   │ │
│   │                  │              │                                   │ │
│   │               sleeping       sleeping                               │ │
│   │           (saves power, lets other processes run)                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PATTERN 4: KERNEL-SIDE POLLING (SQPOLL)                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Use when: Ultra-low latency required, willing to dedicate CPU core       │
│   The kernel polls the submission queue - ZERO syscalls!                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  // Setup with SQPOLL flag                                          │ │
│   │  struct io_uring_params params = {0};                               │ │
│   │  params.flags = IORING_SETUP_SQPOLL;                                │ │
│   │  params.sq_thread_idle = 2000;  // Keep polling for 2 seconds       │ │
│   │                                                                     │ │
│   │  io_uring_queue_init_params(32, &ring, &params);                    │ │
│   │                                                                     │ │
│   │  // Now submissions don't need syscalls!                            │ │
│   │  while (running) {                                                  │ │
│   │      struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);            │ │
│   │      io_uring_prep_read(sqe, fd, buf, len, offset);                 │ │
│   │                                                                     │ │
│   │      // Just update the tail pointer - kernel thread sees it!       │ │
│   │      io_uring_submit(&ring);  // NO SYSCALL in SQPOLL mode!         │ │
│   │                                                                     │ │
│   │      // ... do other work ...                                       │ │
│   │                                                                     │ │
│   │      // Check completions (also no syscall)                         │ │
│   │      struct io_uring_cqe *cqe;                                      │ │
│   │      if (io_uring_peek_cqe(&ring, &cqe) == 0) {                     │ │
│   │          handle_completion(cqe);                                    │ │
│   │          io_uring_cqe_seen(&ring, cqe);                             │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │ │
│   HOW SQPOLL WORKS:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   USER SPACE                         KERNEL SPACE                   │ │
│   │   ┌─────────────┐                   ┌─────────────────────┐         │ │
│   │   │ Application │                   │  SQPOLL Thread      │         │ │
│   │   │             │                   │  (dedicated CPU)    │         │ │
│   │   │ 1. Write SQE│                   │                     │         │ │
│   │   │ 2. Update   │    SHARED         │  while(1) {         │         │ │
│   │   │    tail     │◄──MEMORY─────────►│    if (new_sqe) {   │         │ │
│   │   │             │                   │      process_it();  │         │ │
│   │   │ (no syscall)│                   │    }                │         │ │
│   │   │             │                   │    // busy loop!    │         │ │
│   │   └─────────────┘                   │  }                  │         │ │
│   │                                     └─────────────────────┘         │ │
│   │                                                                     │ │
│   │   LATENCY: Sub-microsecond! No syscall overhead at all.             │ │
│   │   COST: Kernel thread burns 100% CPU while polling.                 │ │
│   │   USE CASE: High-frequency trading, real-time systems.              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### io_uring Complete Example - High-Performance File Copy

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE EXAMPLE: ASYNC FILE COPY                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Copy a file using io_uring with overlapped I/O:                          │
│   Read and write happen IN PARALLEL!                                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  #include <liburing.h>                                              │ │
│   │                                                                     │ │
│   │  #define BLOCK_SIZE  (128 * 1024)  // 128KB blocks                  │ │
│   │  #define QUEUE_DEPTH 32                                             │ │
│   │                                                                     │ │
│   │  struct io_request {                                                │ │
│   │      int type;           // READ or WRITE                           │ │
│   │      off_t offset;       // File offset                             │ │
│   │      char *buf;          // Data buffer                             │ │
│   │  };                                                                 │ │
│   │                                                                     │ │
│   │  void async_copy(int src_fd, int dst_fd, size_t file_size) {        │ │
│   │      struct io_uring ring;                                          │ │
│   │      io_uring_queue_init(QUEUE_DEPTH, &ring, 0);                    │ │
│   │                                                                     │ │
│   │      off_t read_offset = 0;                                         │ │
│   │      off_t write_offset = 0;                                        │ │
│   │      int reads_pending = 0;                                         │ │
│   │      int writes_pending = 0;                                        │ │
│   │                                                                     │ │
│   │      // Pre-allocate buffers                                        │ │
│   │      char *buffers[QUEUE_DEPTH];                                    │ │
│   │      struct io_request requests[QUEUE_DEPTH];                       │ │
│   │      for (int i = 0; i < QUEUE_DEPTH; i++) {                        │ │
│   │          buffers[i] = aligned_alloc(4096, BLOCK_SIZE);              │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      // Submit initial batch of reads                               │ │
│   │      int buf_idx = 0;                                               │ │
│   │      while (read_offset < file_size && buf_idx < QUEUE_DEPTH/2) {   │ │
│   │          struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);        │ │
│   │          requests[buf_idx].type = READ;                             │ │
│   │          requests[buf_idx].offset = read_offset;                    │ │
│   │          requests[buf_idx].buf = buffers[buf_idx];                  │ │
│   │                                                                     │ │
│   │          io_uring_prep_read(sqe, src_fd, buffers[buf_idx],          │ │
│   │                             BLOCK_SIZE, read_offset);               │ │
│   │          sqe->user_data = (uint64_t)&requests[buf_idx];             │ │
│   │                                                                     │ │
│   │          read_offset += BLOCK_SIZE;                                 │ │
│   │          reads_pending++;                                           │ │
│   │          buf_idx++;                                                 │ │
│   │      }                                                              │ │
│   │      io_uring_submit(&ring);                                        │ │
│   │                                                                     │ │
│   │      // Main loop: process completions, submit new operations       │ │
│   │      while (reads_pending > 0 || writes_pending > 0) {              │ │
│   │          struct io_uring_cqe *cqe;                                  │ │
│   │          io_uring_wait_cqe(&ring, &cqe);                            │ │
│   │                                                                     │ │
│   │          struct io_request *req = (void*)cqe->user_data;            │ │
│   │          int bytes = cqe->res;                                      │ │
│   │                                                                     │ │
│   │          if (req->type == READ) {                                   │ │
│   │              reads_pending--;                                       │ │
│   │              // Read completed - submit write for this block        │ │
│   │              struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);    │ │
│   │              req->type = WRITE;                                     │ │
│   │              io_uring_prep_write(sqe, dst_fd, req->buf,             │ │
│   │                                  bytes, req->offset);               │ │
│   │              sqe->user_data = (uint64_t)req;                        │ │
│   │              writes_pending++;                                      │ │
│   │                                                                     │ │
│   │              // Submit another read if more data                    │ │
│   │              if (read_offset < file_size) {                         │ │
│   │                  // ... (reuse a free buffer, submit read)          │ │
│   │              }                                                      │ │
│   │              io_uring_submit(&ring);                                │ │
│   │          } else {  // WRITE completed                               │ │
│   │              writes_pending--;                                      │ │
│   │              // Buffer is now free for reuse                        │ │
│   │          }                                                          │ │
│   │                                                                     │ │
│   │          io_uring_cqe_seen(&ring, cqe);                             │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      io_uring_queue_exit(&ring);                                    │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PIPELINE VISUALIZATION:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  TIME ──────────────────────────────────────────────────────────>   │ │
│   │                                                                     │ │
│   │  Block 0: [READ]────────────────[WRITE]────────────────             │ │
│   │  Block 1:      [READ]────────────────[WRITE]────────────────        │ │
│   │  Block 2:           [READ]────────────────[WRITE]────────────────   │ │
│   │  Block 3:                [READ]────────────────[WRITE]──────────    │ │
│   │                                                                     │ │
│   │           └──────────────────────────────────────────────────┘      │ │
│   │                    OVERLAPPED! Multiple I/Os in flight              │ │
│   │                                                                     │ │
│   │  TRADITIONAL (blocking):                                            │ │
│   │  [READ 0][WRITE 0][READ 1][WRITE 1][READ 2][WRITE 2]...             │ │
│   │  └──────────────────────────────────────────────────────┘           │ │
│   │                    SEQUENTIAL - much slower!                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### io_uring vs epoll - When to Use Which

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IO_URING vs EPOLL DECISION GUIDE                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  USE EPOLL WHEN:                                                    │ │
│   │  ┌───────────────────────────────────────────────────────────────┐  │ │
│   │  │  • Network I/O only (sockets)                                 │  │ │
│   │  │  • Simple request-response pattern                            │  │ │
│   │  │  • No CPU-intensive work between I/O                          │  │ │
│   │  │  • Portability matters (epoll is well-understood)             │  │ │
│   │  │  • Kernel < 5.1 (io_uring not available)                      │  │ │
│   │  │  • Simpler mental model is preferred                          │  │ │
│   │  │                                                               │  │ │
│   │  │  Examples: Simple web servers, proxies, chat servers          │  │ │
│   │  └───────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │  USE IO_URING WHEN:                                                 │ │
│   │  ┌───────────────────────────────────────────────────────────────┐  │ │
│   │  │  • Disk I/O involved (epoll doesn't help with files!)         │  │ │
│   │  │  • Need to overlap I/O with CPU computation                   │  │ │
│   │  │  • High-throughput batching of many operations                │  │ │
│   │  │  • Ultra-low latency required (SQPOLL mode)                   │  │ │
│   │  │  • Mixed I/O types (files + sockets + pipes)                  │  │ │
│   │  │  • Want to minimize syscall overhead                          │  │ │
│   │  │                                                               │  │ │
│   │  │  Examples: Databases, file servers, video processing,         │  │ │
│   │  │           high-frequency trading, game engines                │  │ │
│   │  └───────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PERFORMANCE COMPARISON:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Scenario: 10,000 concurrent connections, echo server               │ │
│   │                                                                     │ │
│   │                        epoll          io_uring                      │ │
│   │  ─────────────────────────────────────────────────                  │ │
│   │  Syscalls/request:     2-3            0-1 (with SQPOLL: 0)          │ │
│   │  Latency (p99):        ~50μs          ~10μs                         │ │
│   │  Throughput:           ~500K/s        ~800K/s                       │ │
│   │                                                                     │ │
│   │  Scenario: Copy 1GB file                                            │ │
│   │                                                                     │ │
│   │                        read/write     io_uring (pipelined)          │ │
│   │  ─────────────────────────────────────────────────────              │ │
│   │  Time:                 2.5s           0.8s                          │ │
│   │  Syscalls:             16,000         ~100                          │ │
│   │                                                                     │ │
│   │  (Numbers are illustrative - actual results depend on hardware)     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE KEY INSIGHT:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  EPOLL answers:  "WHICH file descriptors are ready?"                │ │
│   │                  (then you still need to do the I/O)                │ │
│   │                                                                     │ │
│   │  IO_URING answers: "DO this I/O and tell me when DONE"              │ │
│   │                    (kernel does the I/O for you)                    │ │
│   │                                                                     │ │
│   │  EPOLL = readiness notification                                     │ │
│   │  IO_URING = completion notification                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Event-Driven Architecture

### The Event Loop Pattern

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE EVENT LOOP                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The central pattern of modern high-performance servers:                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   for (;;) {                                                        │ │
│   │       /* 1. Wait for events (blocking, but efficient) */            │ │
│   │       events = epoll_wait(...);                                     │ │
│   │                                                                     │ │
│   │       /* 2. Process each ready event */                             │ │
│   │       for (event in events) {                                       │ │
│   │           handler = get_handler(event.fd);                          │ │
│   │           handler(event);    /* MUST BE NON-BLOCKING! */            │ │
│   │       }                                                             │ │
│   │                                                                     │ │
│   │       /* 3. Process timers, deferred work, etc. */                  │ │
│   │       run_timers();                                                 │ │
│   │       run_deferred_callbacks();                                     │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   GOLDEN RULE: NEVER BLOCK IN AN EVENT HANDLER!                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  If a handler blocks, the ENTIRE event loop stops.                  │ │
│   │  All other connections wait. Latency spikes. Users complain.        │ │
│   │                                                                     │ │
│   │  BAD:                                                               │ │
│   │  void handle_request(int fd) {                                      │ │
│   │      data = read(fd, ...);         /* What if slow client? */       │ │
│   │      result = query_database(...); /* What if DB is slow? */        │ │
│   │      write(fd, result);            /* What if client slow? */       │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   │  GOOD:                                                              │ │
│   │  void handle_readable(int fd) {                                     │ │
│   │      n = read(fd, buf, ...);       /* Non-blocking, partial OK */   │ │
│   │      if (n == -1 && errno == EAGAIN) return;  /* Not ready yet */   │ │
│   │      if (request_complete(buf)) {                                   │ │
│   │          start_async_db_query(buf, on_db_result);  /* Async! */     │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Reactor vs Proactor Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TWO PATTERNS FOR EVENT-DRIVEN I/O                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   REACTOR PATTERN (Linux epoll, BSD kqueue):                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "I'll tell you when I/O is READY, YOU do the I/O"                 │ │
│   │                                                                     │ │
│   │   1. Application registers interest: epoll_ctl(fd, EPOLLIN)         │ │
│   │   2. Application waits: epoll_wait()                                │ │
│   │   3. Kernel: "fd 5 is READY to read"                                │ │
│   │   4. Application: read(fd5, buf, ...)  ◄── YOU do the read          │ │
│   │   5. Application: process(buf)                                       │ │
│   │                                                                     │ │
│   │   Timeline:                                                          │ │
│   │   App:    [wait]──────────[read()]──[process]                       │ │
│   │   Kernel: ────[data arrives]────────────────                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PROACTOR PATTERN (Windows IOCP, Linux io_uring):                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "I'll DO the I/O for you, tell you when COMPLETE"                 │ │
│   │                                                                     │ │
│   │   1. Application submits: io_uring_prep_read(sqe, fd, buf, ...)     │ │
│   │   2. Application does other work (or waits)                          │ │
│   │   3. Kernel does the read IN THE BACKGROUND                          │ │
│   │   4. Kernel: "Read COMPLETE, data is in your buffer"                │ │
│   │   5. Application: process(buf)  ◄── I/O already done!              │ │
│   │                                                                     │ │
│   │   Timeline:                                                          │ │
│   │   App:    [submit]──[other work]────────────[process]               │ │
│   │   Kernel: ────────[data arrives][copy to buf]────────                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMPARISON:                                                              │
│   ┌──────────────────┬────────────────────┬────────────────────┐          │
│   │                  │ REACTOR            │ PROACTOR           │          │
│   ├──────────────────┼────────────────────┼────────────────────┤          │
│   │ Notification     │ "Ready to read"    │ "Read complete"    │          │
│   │ Who does I/O     │ Application        │ Kernel             │          │
│   │ Buffer owned by  │ App (on demand)    │ Pre-registered     │          │
│   │ Complexity       │ Simpler            │ More complex       │          │
│   │ Performance      │ Good               │ Best (zero-copy)   │          │
│   │ Examples         │ epoll, kqueue      │ IOCP, io_uring     │          │
│   └──────────────────┴────────────────────┴────────────────────┘          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Real-World Implementations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-WORLD EVENT LOOP IMPLEMENTATIONS                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NGINX Architecture:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Master Process                                                     │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │ • Reads config, binds ports                                   │  │ │
│   │   │ • Spawns worker processes                                     │  │ │
│   │   │ • Handles signals, graceful reload                            │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │           │                                                          │ │
│   │           ├──────────────────┬──────────────────┐                   │ │
│   │           ▼                  ▼                  ▼                   │ │
│   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │ │
│   │   │   Worker 1   │   │   Worker 2   │   │   Worker N   │           │ │
│   │   ├──────────────┤   ├──────────────┤   ├──────────────┤           │ │
│   │   │ Event Loop:  │   │ Event Loop:  │   │ Event Loop:  │           │ │
│   │   │ • epoll_wait │   │ • epoll_wait │   │ • epoll_wait │           │ │
│   │   │ • accept()   │   │ • accept()   │   │ • accept()   │           │ │
│   │   │ • read/write │   │ • read/write │   │ • read/write │           │ │
│   │   │ • Handles    │   │ • Handles    │   │ • Handles    │           │ │
│   │   │   10K+ conns │   │   10K+ conns │   │   10K+ conns │           │ │
│   │   └──────────────┘   └──────────────┘   └──────────────┘           │ │
│   │                                                                     │ │
│   │   Key: Each worker handles THOUSANDS of connections via            │ │
│   │        single-threaded event loop. No thread-per-connection!       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NODE.JS / LIBUV:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                     JavaScript Thread                        │   │ │
│   │   │                                                              │   │ │
│   │   │   while (true) {                                             │   │ │
│   │   │       runTimers();                                           │   │ │
│   │   │       runPendingCallbacks();                                 │   │ │
│   │   │       poll();           // epoll_wait / kqueue               │   │ │
│   │   │       runSetImmediate();                                     │   │ │
│   │   │       runCloseCallbacks();                                   │   │ │
│   │   │   }                                                          │   │ │
│   │   │                                                              │   │ │
│   │   └────────────────────────────┬────────────────────────────────┘   │ │
│   │                                │                                    │ │
│   │                                ▼                                    │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                     Thread Pool (libuv)                      │   │ │
│   │   │                                                              │   │ │
│   │   │   For operations that CAN'T be non-blocking:                 │   │ │
│   │   │   • File system I/O (most OSes don't have async file I/O)   │   │ │
│   │   │   • DNS lookups                                              │   │ │
│   │   │   • CPU-intensive crypto                                     │   │ │
│   │   │                                                              │   │ │
│   │   │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐               │   │ │
│   │   │   │Thread 1│ │Thread 2│ │Thread 3│ │Thread 4│               │   │ │
│   │   │   └────────┘ └────────┘ └────────┘ └────────┘               │   │ │
│   │   │                                                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   REDIS Single-Threaded Model:                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌───────────────────────────────────────────────────────────┐     │ │
│   │   │                    Redis Main Thread                       │     │ │
│   │   │                                                            │     │ │
│   │   │   while (true) {                                           │     │ │
│   │   │       /* All of this is single-threaded */                 │     │ │
│   │   │       events = aeApiPoll();    // epoll/kqueue             │     │ │
│   │   │       for (event in events) {                              │     │ │
│   │   │           if (event.readable) readQueryFromClient();       │     │ │
│   │   │           if (event.writable) sendReplyToClient();         │     │ │
│   │   │       }                                                    │     │ │
│   │   │       processTimeEvents();     // Expiry, etc.             │     │ │
│   │   │   }                                                        │     │ │
│   │   │                                                            │     │ │
│   │   │   Why single-threaded works for Redis:                     │     │ │
│   │   │   • Memory operations are FAST (microseconds)              │     │ │
│   │   │   • No locks needed - no race conditions!                  │     │ │
│   │   │   • Bottleneck is usually network, not CPU                 │     │ │
│   │   │                                                            │     │ │
│   │   └───────────────────────────────────────────────────────────┘     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Practical Implementation

### Building a Non-Blocking Server

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ANATOMY OF A NON-BLOCKING SERVER                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STEP 1: Set Up Non-Blocking Listening Socket                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  int server_fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);   │ │
│   │                                                                     │ │
│   │  /* Allow address reuse */                                          │ │
│   │  int opt = 1;                                                       │ │
│   │  setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));│ │
│   │                                                                     │ │
│   │  /* Bind and listen */                                              │ │
│   │  bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));            │ │
│   │  listen(server_fd, SOMAXCONN);                                      │ │
│   │                                                                     │ │
│   │  /* Make non-blocking (alternative to SOCK_NONBLOCK) */             │ │
│   │  int flags = fcntl(server_fd, F_GETFL, 0);                          │ │
│   │  fcntl(server_fd, F_SETFL, flags | O_NONBLOCK);                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STEP 2: Set Up epoll                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  int epfd = epoll_create1(0);                                       │ │
│   │                                                                     │ │
│   │  struct epoll_event ev;                                             │ │
│   │  ev.events = EPOLLIN;                                               │ │
│   │  ev.data.fd = server_fd;                                            │ │
│   │  epoll_ctl(epfd, EPOLL_CTL_ADD, server_fd, &ev);                    │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   STEP 3: Connection State Machine                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  struct connection {                                                │ │
│   │      int fd;                                                        │ │
│   │      enum { READING, WRITING, CLOSED } state;                       │ │
│   │      char read_buf[4096];                                           │ │
│   │      size_t read_pos;                                               │ │
│   │      char write_buf[4096];                                          │ │
│   │      size_t write_pos;                                              │ │
│   │      size_t write_len;                                              │ │
│   │  };                                                                 │ │
│   │                                                                     │ │
│   │  /* State machine visualization:                                    │ │
│   │                                                                     │ │
│   │       ┌──────────┐      request        ┌──────────┐                │ │
│   │   ───▶│ READING  │ ──────complete────▶ │ WRITING  │───▶ back to    │ │
│   │       └──────────┘                      └──────────┘     READING    │ │
│   │            │                                 │           or CLOSED │ │
│   │            │ error/EOF                       │ error                │ │
│   │            ▼                                 ▼                      │ │
│   │       ┌──────────┐                      ┌──────────┐                │ │
│   │       │  CLOSED  │                      │  CLOSED  │                │ │
│   │       └──────────┘                      └──────────┘                │ │
│   │  */                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Main Event Loop

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE EVENT LOOP EXAMPLE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  #define MAX_EVENTS 64                                              │ │
│   │  struct epoll_event events[MAX_EVENTS];                             │ │
│   │                                                                     │ │
│   │  for (;;) {                                                         │ │
│   │      int nfds = epoll_wait(epfd, events, MAX_EVENTS, -1);           │ │
│   │      if (nfds == -1) {                                              │ │
│   │          if (errno == EINTR) continue;  /* Signal interrupted */    │ │
│   │          perror("epoll_wait");                                      │ │
│   │          break;                                                     │ │
│   │      }                                                              │ │
│   │                                                                     │ │
│   │      for (int i = 0; i < nfds; i++) {                               │ │
│   │          int fd = events[i].data.fd;                                │ │
│   │          uint32_t ev = events[i].events;                            │ │
│   │                                                                     │ │
│   │          if (fd == server_fd) {                                     │ │
│   │              /* New connection */                                   │ │
│   │              handle_accept(epfd, server_fd);                        │ │
│   │          }                                                          │ │
│   │          else if (ev & (EPOLLERR | EPOLLHUP)) {                     │ │
│   │              /* Error or hangup */                                  │ │
│   │              close_connection(epfd, fd);                            │ │
│   │          }                                                          │ │
│   │          else if (ev & EPOLLIN) {                                   │ │
│   │              /* Readable */                                         │ │
│   │              handle_read(epfd, fd);                                 │ │
│   │          }                                                          │ │
│   │          else if (ev & EPOLLOUT) {                                  │ │
│   │              /* Writable */                                         │ │
│   │              handle_write(epfd, fd);                                │ │
│   │          }                                                          │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ACCEPT HANDLER:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  void handle_accept(int epfd, int server_fd) {                      │ │
│   │      for (;;) {  /* Accept all pending connections */               │ │
│   │          int client_fd = accept4(server_fd, NULL, NULL,             │ │
│   │                                   SOCK_NONBLOCK | SOCK_CLOEXEC);    │ │
│   │          if (client_fd == -1) {                                     │ │
│   │              if (errno == EAGAIN || errno == EWOULDBLOCK) {         │ │
│   │                  return;  /* No more pending connections */         │ │
│   │              }                                                      │ │
│   │              perror("accept4");                                     │ │
│   │              return;                                                │ │
│   │          }                                                          │ │
│   │                                                                     │ │
│   │          /* Create connection state */                              │ │
│   │          struct connection *conn = new_connection(client_fd);       │ │
│   │                                                                     │ │
│   │          /* Add to epoll */                                         │ │
│   │          struct epoll_event ev;                                     │ │
│   │          ev.events = EPOLLIN | EPOLLET;  /* Edge-triggered */       │ │
│   │          ev.data.ptr = conn;             /* Store connection ptr */ │ │
│   │          epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &ev);            │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   READ HANDLER (Edge-Triggered):                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  void handle_read(int epfd, struct connection *conn) {              │ │
│   │      for (;;) {  /* MUST loop until EAGAIN for edge-triggered */    │ │
│   │          ssize_t n = read(conn->fd,                                 │ │
│   │                           conn->read_buf + conn->read_pos,          │ │
│   │                           sizeof(conn->read_buf) - conn->read_pos); │ │
│   │                                                                     │ │
│   │          if (n == -1) {                                             │ │
│   │              if (errno == EAGAIN) {                                 │ │
│   │                  /* No more data right now */                       │ │
│   │                  break;                                             │ │
│   │              }                                                      │ │
│   │              /* Real error */                                       │ │
│   │              close_connection(epfd, conn);                          │ │
│   │              return;                                                │ │
│   │          }                                                          │ │
│   │                                                                     │ │
│   │          if (n == 0) {                                              │ │
│   │              /* EOF - client closed connection */                   │ │
│   │              close_connection(epfd, conn);                          │ │
│   │              return;                                                │ │
│   │          }                                                          │ │
│   │                                                                     │ │
│   │          conn->read_pos += n;                                       │ │
│   │                                                                     │ │
│   │          /* Check if request is complete */                         │ │
│   │          if (request_complete(conn)) {                              │ │
│   │              process_request(conn);                                 │ │
│   │              /* Switch to writing response */                       │ │
│   │              struct epoll_event ev;                                 │ │
│   │              ev.events = EPOLLOUT | EPOLLET;                        │ │
│   │              ev.data.ptr = conn;                                    │ │
│   │              epoll_ctl(epfd, EPOLL_CTL_MOD, conn->fd, &ev);         │ │
│   │              return;                                                │ │
│   │          }                                                          │ │
│   │      }                                                              │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Error Handling Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ROBUST ERROR HANDLING                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ERRNO VALUES AND THEIR MEANINGS:                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   EAGAIN / EWOULDBLOCK:                                             │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │ • "Try again later" - NOT an error!                           │ │ │
│   │   │ • Resource temporarily unavailable                            │ │ │
│   │   │ • CORRECT response: return to event loop, wait for readiness  │ │ │
│   │   │ • Common mistake: treating as fatal error                     │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   EINTR:                                                            │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │ • System call interrupted by signal                           │ │ │
│   │   │ • CORRECT response: retry the system call                     │ │ │
│   │   │ • Often wrapped in a retry loop:                              │ │ │
│   │   │   do { n = read(...); } while (n == -1 && errno == EINTR);    │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   EPIPE / SIGPIPE:                                                  │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │ • Write to pipe/socket with no readers                        │ │ │
│   │   │ • SIGPIPE kills process by default!                           │ │ │
│   │   │ • SOLUTION: signal(SIGPIPE, SIG_IGN);                         │ │ │
│   │   │             Then check for EPIPE error                        │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   ECONNRESET:                                                       │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │ • Peer reset connection (sent RST)                            │ │ │
│   │   │ • Connection is dead - close it                               │ │ │
│   │   │ • Common with misbehaving clients                             │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   ETIMEDOUT:                                                        │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │ • TCP connection timed out                                    │ │ │
│   │   │ • No response from peer for too long                          │ │ │
│   │   │ • Close connection, maybe retry                               │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DEFENSIVE READ PATTERN:                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  ssize_t safe_read(int fd, void *buf, size_t count) {               │ │
│   │      ssize_t n;                                                     │ │
│   │      do {                                                           │ │
│   │          n = read(fd, buf, count);                                  │ │
│   │      } while (n == -1 && errno == EINTR);  /* Retry on signal */    │ │
│   │                                                                     │ │
│   │      if (n == -1) {                                                 │ │
│   │          if (errno == EAGAIN || errno == EWOULDBLOCK) {             │ │
│   │              return 0;  /* Would block - not an error */            │ │
│   │          }                                                          │ │
│   │          return -1;  /* Real error */                               │ │
│   │      }                                                              │ │
│   │      return n;  /* Bytes read (0 = EOF) */                          │ │
│   │  }                                                                  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Common Pitfalls

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMMON NON-BLOCKING I/O PITFALLS                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PITFALL #1: Forgetting to Set Non-Blocking Mode                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG:                                                            │ │
│   │   int client_fd = accept(server_fd, ...);                           │ │
│   │   /* client_fd is BLOCKING! Event loop will stall on slow clients */│ │
│   │                                                                     │ │
│   │   RIGHT:                                                            │ │
│   │   int client_fd = accept4(server_fd, ..., SOCK_NONBLOCK);           │ │
│   │   /* OR */                                                          │ │
│   │   int client_fd = accept(server_fd, ...);                           │ │
│   │   fcntl(client_fd, F_SETFL, fcntl(client_fd, F_GETFL) | O_NONBLOCK);│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL #2: Not Reading Until EAGAIN (Edge-Triggered)                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG (with EPOLLET):                                             │ │
│   │   void handle_read(int fd) {                                        │ │
│   │       n = read(fd, buf, sizeof(buf));  /* Read once */              │ │
│   │       process(buf, n);                                              │ │
│   │   }                                                                 │ │
│   │   /* If more data arrived, no more events! Data stuck forever! */   │ │
│   │                                                                     │ │
│   │   RIGHT (with EPOLLET):                                             │ │
│   │   void handle_read(int fd) {                                        │ │
│   │       for (;;) {                                                    │ │
│   │           n = read(fd, buf, sizeof(buf));                           │ │
│   │           if (n == -1 && errno == EAGAIN) break;  /* Done */        │ │
│   │           if (n <= 0) { close(fd); return; }                        │ │
│   │           process(buf, n);                                          │ │
│   │       }                                                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL #3: Blocking Operations Inside Event Handler                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG:                                                            │ │
│   │   void handle_request(int fd) {                                     │ │
│   │       result = mysql_query(...);  /* BLOCKS! */                     │ │
│   │       data = memcached_get(...);  /* BLOCKS! */                     │ │
│   │       file = fopen(...); fread(...);  /* BLOCKS! */                 │ │
│   │       sleep(1);  /* Obviously blocks */                             │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   │   RIGHT:                                                            │ │
│   │   • Use async database clients                                      │ │
│   │   • Use connection pools with non-blocking I/O                      │ │
│   │   • Offload to thread pool for file I/O                             │ │
│   │   • Use timers instead of sleep()                                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL #4: Small Buffer Sizes                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG:                                                            │ │
│   │   char buf[64];  /* Tiny buffer */                                  │ │
│   │   /* Many syscalls to read large request */                         │ │
│   │                                                                     │ │
│   │   RIGHT:                                                            │ │
│   │   char buf[16384];  /* Larger buffer, fewer syscalls */             │ │
│   │   /* Or use readv/writev for scatter-gather I/O */                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL #5: Not Handling Partial Writes                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG:                                                            │ │
│   │   write(fd, buf, len);  /* Assume all written */                    │ │
│   │                                                                     │ │
│   │   RIGHT:                                                            │ │
│   │   size_t written = 0;                                               │ │
│   │   while (written < len) {                                           │ │
│   │       ssize_t n = write(fd, buf + written, len - written);          │ │
│   │       if (n == -1) {                                                │ │
│   │           if (errno == EAGAIN) {                                    │ │
│   │               /* Save write position, wait for EPOLLOUT */          │ │
│   │               conn->write_pos = written;                            │ │
│   │               return;                                               │ │
│   │           }                                                         │ │
│   │           /* Handle error */                                        │ │
│   │       }                                                             │ │
│   │       written += n;                                                 │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PITFALL #6: fd Leak on Error Paths                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WRONG:                                                            │ │
│   │   int fd = accept(...);                                             │ │
│   │   struct conn *c = malloc(sizeof(*c));                              │ │
│   │   if (!c) return;  /* fd leaked! */                                 │ │
│   │                                                                     │ │
│   │   RIGHT:                                                            │ │
│   │   int fd = accept(...);                                             │ │
│   │   struct conn *c = malloc(sizeof(*c));                              │ │
│   │   if (!c) { close(fd); return; }                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Performance Considerations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE OPTIMIZATION                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SYSCALL OVERHEAD:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Each system call costs ~100-1000 nanoseconds:                     │ │
│   │   • Mode switch user → kernel                                       │ │
│   │   • Kernel validates arguments                                       │ │
│   │   • Mode switch kernel → user                                       │ │
│   │                                                                     │ │
│   │   REDUCE SYSCALLS:                                                  │ │
│   │   • Use epoll_wait with larger maxevents                            │ │
│   │   • Use readv/writev for scatter-gather I/O                         │ │
│   │   • Use sendfile() for file→socket transfers                        │ │
│   │   • Use io_uring for batching                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MEMORY ALLOCATION:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   malloc() in hot path = SLOW                                       │ │
│   │                                                                     │ │
│   │   SOLUTIONS:                                                        │ │
│   │   • Pre-allocate connection pool                                    │ │
│   │   • Use slab allocator for fixed-size objects                       │ │
│   │   • Use arena/bump allocator for request lifetime                   │ │
│   │   • Avoid allocations in event handlers                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CACHE EFFICIENCY:                                                        │ │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Keep hot data together in memory (struct packing)              │ │
│   │   • Process events in batch (cache-friendly)                        │ │
│   │   • Avoid pointer chasing in hot paths                              │ │
│   │   • Consider CPU affinity for workers                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BENCHMARK: Connections per Second (approximate)                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Model                         │ Connections/sec                   │ │
│   │   ──────────────────────────────┼─────────────────────             │ │
│   │   Thread-per-connection         │ ~1,000-10,000                     │ │
│   │   select() based                │ ~10,000-50,000                    │ │
│   │   poll() based                  │ ~10,000-50,000                    │ │
│   │   epoll (level-triggered)       │ ~100,000-500,000                  │ │
│   │   epoll (edge-triggered)        │ ~500,000-1,000,000                │ │
│   │   io_uring                      │ ~1,000,000+                       │ │
│   │                                                                     │ │
│   │   Note: Actual numbers depend on hardware, workload, etc.           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Summary and Appendix

### Quick Reference: When to Use What

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DECISION TREE: WHICH I/O MODEL?                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                         ┌─────────────────────┐                            │
│                         │ How many concurrent │                            │
│                         │ connections?        │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                       │
│               ┌────────────────────┼────────────────────┐                  │
│               │                    │                    │                  │
│               ▼                    ▼                    ▼                  │
│        ┌──────────┐         ┌──────────┐         ┌──────────┐             │
│        │  < 100   │         │ 100-10K  │         │  > 10K   │             │
│        └────┬─────┘         └────┬─────┘         └────┬─────┘             │
│             │                    │                    │                   │
│             ▼                    ▼                    ▼                   │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐         │
│   │ Thread-per-conn │   │  poll() or      │   │ epoll/kqueue +  │         │
│   │ is fine         │   │  epoll LT       │   │ edge-triggered  │         │
│   │                 │   │                 │   │ or io_uring     │         │
│   │ Simple code,    │   │ Good balance    │   │                 │         │
│   │ good enough     │   │ of complexity   │   │ Maximum         │         │
│   │ performance     │   │ and performance │   │ performance     │         │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘         │
│                                                                            │
│   OTHER CONSIDERATIONS:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Need portable code? → poll() (works everywhere)                 │ │
│   │   • Linux only? → epoll                                             │ │
│   │   • BSD/macOS? → kqueue                                             │ │
│   │   • Maximum Linux perf? → io_uring                                  │ │
│   │   • Windows? → IOCP                                                 │ │
│   │   • Cross-platform library? → libuv, libevent, libev                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### System Call Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM CALL QUICK REFERENCE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FILE DESCRIPTOR OPERATIONS:                                              │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ open()             │ Open file, returns fd                          │ │
│   │ close()            │ Close fd                                       │ │
│   │ read()             │ Read from fd into buffer                       │ │
│   │ write()            │ Write buffer to fd                             │ │
│   │ fcntl()            │ Control fd flags (including O_NONBLOCK)        │ │
│   │ dup(), dup2()      │ Duplicate fd                                   │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│   SOCKET OPERATIONS:                                                       │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ socket()           │ Create socket, returns fd                      │ │
│   │ bind()             │ Bind socket to address                         │ │
│   │ listen()           │ Mark socket as listening                       │ │
│   │ accept()           │ Accept connection, returns new fd              │ │
│   │ accept4()          │ Accept with flags (SOCK_NONBLOCK)              │ │
│   │ connect()          │ Connect to remote address                      │ │
│   │ send(), recv()     │ Send/receive on socket                         │ │
│   │ sendto(), recvfrom()│ UDP send/receive with address                 │ │
│   │ setsockopt()       │ Set socket options                             │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│   MULTIPLEXING:                                                            │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ select()           │ Wait on multiple fds (limited to FD_SETSIZE)   │ │
│   │ pselect()          │ select() with signal mask                      │ │
│   │ poll()             │ Wait on multiple fds (no limit)                │ │
│   │ ppoll()            │ poll() with signal mask                        │ │
│   │ epoll_create1()    │ Create epoll instance                          │ │
│   │ epoll_ctl()        │ Add/modify/delete fd from epoll                │ │
│   │ epoll_wait()       │ Wait for events                                │ │
│   │ kqueue()           │ Create kqueue instance (BSD)                   │ │
│   │ kevent()           │ Register/wait for events (BSD)                 │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│   ADVANCED I/O:                                                            │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ readv(), writev()  │ Scatter-gather I/O                             │ │
│   │ sendfile()         │ Zero-copy file to socket                       │ │
│   │ splice()           │ Move data between fds without user-space copy  │ │
│   │ io_uring_setup()   │ Create io_uring instance                       │ │
│   │ io_uring_enter()   │ Submit/wait for io_uring operations            │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Error Codes Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ERRNO VALUES REFERENCE                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NON-BLOCKING SPECIFIC:                                                   │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ EAGAIN             │ Resource temporarily unavailable (try again)  │ │
│   │ EWOULDBLOCK        │ Same as EAGAIN on most systems                │ │
│   │ EINPROGRESS        │ connect() in progress (non-blocking)          │ │
│   │ EALREADY           │ Connection already in progress                │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│   CONNECTION ERRORS:                                                       │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ ECONNREFUSED       │ Connection refused by peer                    │ │
│   │ ECONNRESET         │ Connection reset by peer                      │ │
│   │ ECONNABORTED       │ Connection aborted                            │ │
│   │ ETIMEDOUT          │ Connection timed out                          │ │
│   │ ENETUNREACH        │ Network unreachable                           │ │
│   │ EHOSTUNREACH       │ Host unreachable                              │ │
│   │ ENOTCONN           │ Socket not connected                          │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│   PIPE/FIFO SPECIFIC:                                                      │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ EPIPE              │ Broken pipe (no readers)                      │ │
│   │ SIGPIPE            │ Signal sent when EPIPE (kills process!)       │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
│   GENERAL:                                                                 │
│   ┌────────────────────┬────────────────────────────────────────────────┐ │
│   │ EINTR              │ Interrupted by signal (retry)                 │ │
│   │ EINVAL             │ Invalid argument                              │ │
│   │ EBADF              │ Bad file descriptor                           │ │
│   │ ENOMEM             │ Out of memory                                 │ │
│   │ EMFILE             │ Too many open files (per-process limit)       │ │
│   │ ENFILE             │ Too many open files (system-wide limit)       │ │
│   │ EIO                │ I/O error                                     │ │
│   └────────────────────┴────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF UNIX I/O                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1969: Unix Created                                                       │
│         • Everything is a file                                             │
│         • Simple blocking read()/write()                                   │
│                                                                            │
│   1983: BSD 4.2 - Sockets Introduced                                       │
│         • select() for multiplexing                                        │
│         • First non-blocking support                                       │
│                                                                            │
│   1986: SVR3 - poll() Introduced                                           │
│         • No FD_SETSIZE limit                                              │
│         • Cleaner interface than select()                                  │
│                                                                            │
│   1999: FreeBSD 4.1 - kqueue Introduced                                    │
│         • O(1) operations                                                  │
│         • Edge-triggered support                                           │
│         • Generic event notification                                       │
│                                                                            │
│   2002: Linux 2.5.44 - epoll Introduced                                    │
│         • O(1) event notification                                          │
│         • Edge-triggered mode                                              │
│         • The C10K problem solved                                          │
│                                                                            │
│   2019: Linux 5.1 - io_uring Introduced                                    │
│         • True async I/O for everything                                    │
│         • Zero-copy ring buffers                                           │
│         • The future of Linux I/O                                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Timeline:                                                         │ │
│   │                                                                     │ │
│   │   1969      1983      1986      1999      2002      2019            │ │
│   │   ─┼─────────┼─────────┼─────────┼─────────┼─────────┼────────>     │ │
│   │    │         │         │         │         │         │              │ │
│   │   Unix    select()  poll()   kqueue    epoll   io_uring            │ │
│   │   read()                      (BSD)    (Linux)  (Linux)            │ │
│   │   write()                                                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BLOCKING VS NON-BLOCKING: THE BIG PICTURE               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BLOCKING I/O:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✓ Simple to understand and code                                   │ │
│   │   ✓ Each connection = one thread = isolated state                   │ │
│   │   ✓ Errors are local (one thread crashes, others continue)          │ │
│   │   ✗ Thread overhead: ~1MB stack per thread                          │ │
│   │   ✗ Context switch overhead: ~1-10 microseconds                     │ │
│   │   ✗ Doesn't scale beyond thousands of connections                   │ │
│   │                                                                     │ │
│   │   BEST FOR: Simple services, low concurrency, quick development     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NON-BLOCKING I/O:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✓ Handles 10K+ connections with single thread                     │ │
│   │   ✓ Minimal memory overhead per connection                          │ │
│   │   ✓ No thread sync issues (single-threaded event loop)              │ │
│   │   ✗ More complex state management                                   │ │
│   │   ✗ Must never block in handlers                                    │ │
│   │   ✗ Error in one handler affects all connections                    │ │
│   │   ✗ Debugging can be harder                                         │ │
│   │                                                                     │ │
│   │   BEST FOR: High concurrency servers, proxies, load balancers       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE HYBRID APPROACH (Modern Best Practice):                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                    Main Event Loop                            │  │ │
│   │   │   • Non-blocking network I/O (epoll/kqueue)                  │  │ │
│   │   │   • Handles 100K+ connections                                 │  │ │
│   │   │   • Never blocks!                                             │  │ │
│   │   └────────────────────────┬─────────────────────────────────────┘  │ │
│   │                            │                                        │ │
│   │                            │ Offload blocking work                  │ │
│   │                            ▼                                        │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                    Thread Pool                                │  │ │
│   │   │   • File system I/O                                          │  │ │
│   │   │   • DNS lookups                                               │  │ │
│   │   │   • CPU-intensive work                                        │  │ │
│   │   │   • Database queries (if not using async client)             │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   Examples: Node.js (libuv), Nginx, Go runtime                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FINAL WISDOM:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   "Blocking I/O is not evil. Non-blocking I/O is not magic.        │ │
│   │    Choose the right tool for the job."                              │ │
│   │                                                                     │ │
│   │   • < 1000 connections? Thread-per-connection is often simpler.    │ │
│   │   • > 10000 connections? Event loop is likely necessary.           │ │
│   │   • Mixed workload? Hybrid approach wins.                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## References

- Bach, Maurice J. *The Design of the UNIX Operating System*. Prentice Hall, 1986.
- Stevens, W. Richard. *UNIX Network Programming, Volume 1*. Prentice Hall, 2003.
- Love, Robert. *Linux System Programming*. O'Reilly Media, 2013.
- Kerrisk, Michael. *The Linux Programming Interface*. No Starch Press, 2010.
- Linux kernel source: `fs/select.c`, `fs/eventpoll.c`, `fs/io_uring.c`
- FreeBSD manual pages: `kqueue(2)`, `kevent(2)`
- Linux manual pages: `epoll(7)`, `poll(2)`, `select(2)`, `io_uring(7)`
