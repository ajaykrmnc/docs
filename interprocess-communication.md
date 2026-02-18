# Interprocess Communication

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Pipes, FIFOs, System V IPC, POSIX IPC, Shared Memory, Message Queues, Semaphores, and Sockets

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [What is Interprocess Communication?](#what-is-interprocess-communication)
   - [The IPC Landscape](#the-ipc-landscape)
   - [Historical Context](#historical-context)

2. [Pipes](#2-pipes)
   - [What is a Pipe?](#what-is-a-pipe)
   - [The pipe() System Call](#the-pipe-system-call)
   - [Kernel Implementation of Pipes](#kernel-implementation-of-pipes)
   - [Pipe Capacity and Blocking](#pipe-capacity-and-blocking)
   - [Closing Pipe Ends](#closing-pipe-ends)
   - [Pipes in the Shell](#pipes-in-the-shell)

3. [FIFOs (Named Pipes)](#3-fifos-named-pipes)
   - [What is a FIFO?](#what-is-a-fifo)
   - [Creating FIFOs: mkfifo()](#creating-fifos-mkfifo)
   - [Opening and Using FIFOs](#opening-and-using-fifos)
   - [FIFO vs Pipe](#fifo-vs-pipe)
   - [Use Cases for FIFOs](#use-cases-for-fifos)

4. [System V IPC Overview](#4-system-v-ipc-overview)
   - [The System V IPC Model](#the-system-v-ipc-model)
   - [IPC Keys and Identifiers](#ipc-keys-and-identifiers)
   - [The ftok() Function](#the-ftok-function)
   - [IPC Permissions](#ipc-permissions)
   - [IPC Commands: ipcs and ipcrm](#ipc-commands-ipcs-and-ipcrm)

5. [System V Message Queues](#5-system-v-message-queues)
   - [What are Message Queues?](#what-are-message-queues)
   - [Creating Message Queues: msgget()](#creating-message-queues-msgget)
   - [Sending Messages: msgsnd()](#sending-messages-msgsnd)
   - [Receiving Messages: msgrcv()](#receiving-messages-msgrcv)
   - [Message Queue Control: msgctl()](#message-queue-control-msgctl)
   - [Kernel Data Structures](#kernel-data-structures)

6. [System V Semaphores](#6-system-v-semaphores)
   - [What are Semaphores?](#what-are-semaphores)
   - [Semaphore Concepts](#semaphore-concepts)
   - [Creating Semaphores: semget()](#creating-semaphores-semget)
   - [Semaphore Operations: semop()](#semaphore-operations-semop)
   - [Semaphore Control: semctl()](#semaphore-control-semctl)
   - [The Undo Feature](#the-undo-feature)

7. [System V Shared Memory](#7-system-v-shared-memory)
   - [What is Shared Memory?](#what-is-shared-memory)
   - [Creating Shared Memory: shmget()](#creating-shared-memory-shmget)
   - [Attaching Shared Memory: shmat()](#attaching-shared-memory-shmat)
   - [Detaching Shared Memory: shmdt()](#detaching-shared-memory-shmdt)
   - [Shared Memory Control: shmctl()](#shared-memory-control-shmctl)
   - [Synchronization Requirements](#synchronization-requirements)

8. [POSIX IPC](#8-posix-ipc)
   - [POSIX vs System V IPC](#posix-vs-system-v-ipc)
   - [POSIX Message Queues](#posix-message-queues)
   - [POSIX Semaphores](#posix-semaphores)
   - [POSIX Shared Memory](#posix-shared-memory)

9. [Memory-Mapped Files](#9-memory-mapped-files)
   - [mmap() for IPC](#mmap-for-ipc)
   - [Anonymous Mappings](#anonymous-mappings)
   - [File-Backed Mappings](#file-backed-mappings)
   - [Synchronization with msync()](#synchronization-with-msync)

10. [Signals as IPC](#10-signals-as-ipc)
    - [Signals for Notification](#signals-for-notification)
    - [Real-Time Signals](#real-time-signals)
    - [signalfd(): Synchronous Signal Handling](#signalfd-synchronous-signal-handling)

11. [Unix Domain Sockets](#11-unix-domain-sockets)
    - [What are Unix Domain Sockets?](#what-are-unix-domain-sockets)
    - [Socket Types: Stream vs Datagram](#socket-types-stream-vs-datagram)
    - [Creating Unix Domain Sockets](#creating-unix-domain-sockets)
    - [Abstract Socket Namespace](#abstract-socket-namespace)
    - [Passing File Descriptors](#passing-file-descriptors)
    - [Passing Credentials](#passing-credentials)

12. [Modern IPC Mechanisms](#12-modern-ipc-mechanisms)
    - [eventfd: Event Notification](#eventfd-event-notification)
    - [timerfd: Timer Notifications](#timerfd-timer-notifications)
    - [memfd: Anonymous Memory Files](#memfd-anonymous-memory-files)
    - [pidfd: Process File Descriptors](#pidfd-process-file-descriptors)

13. [IPC Performance and Selection](#13-ipc-performance-and-selection)
    - [Performance Comparison](#performance-comparison)
    - [Choosing the Right IPC Mechanism](#choosing-the-right-ipc-mechanism)
    - [IPC Design Patterns](#ipc-design-patterns)

14. [Summary and Appendix](#14-summary-and-appendix)
    - [IPC System Calls Quick Reference](#ipc-system-calls-quick-reference)
    - [The Big Picture](#the-big-picture)

15. [References](#15-references)

---

## 1. Introduction

### What is Interprocess Communication?

Interprocess Communication (IPC) encompasses the mechanisms by which separate processes exchange data and 
coordinate their activities. In the Unix philosophy, processes are isolated entities with their own address 
spaces—IPC provides the bridges that allow them to cooperate.

Maurice Bach describes IPC as:

> "The kernel provides several mechanisms that allow processes to communicate with each other. These 
> mechanisms range from simple signals to sophisticated shared memory and message passing facilities."

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    INTERPROCESS COMMUNICATION OVERVIEW                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────┐                                    ┌─────────────┐      │
│   │  Process A  │                                    │  Process B  │      │
│   │             │                                    │             │      │
│   │  ┌───────┐  │                                    │  ┌───────┐  │      │
│   │  │ Code  │  │                                    │  │ Code  │  │      │
│   │  ├───────┤  │                                    │  ├───────┤  │      │
│   │  │ Data  │  │         IPC MECHANISMS             │  │ Data  │  │      │
│   │  ├───────┤  │  ◄─────────────────────────────►   │  ├───────┤  │      │
│   │  │ Stack │  │                                    │  │ Stack │  │      │
│   │  └───────┘  │    • Pipes                         │  └───────┘  │      │
│   │             │    • FIFOs                         │             │      │
│   └─────────────┘    • Message Queues                └─────────────┘      │
│                      • Semaphores                                          │
│                      • Shared Memory                                       │
│                      • Sockets                                             │
│                      • Signals                                             │
│                                                                            │
│   Each process has its own isolated address space.                        │
│   IPC mechanisms provide controlled channels for communication.           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```




### The IPC Landscape

Unix provides a rich variety of IPC mechanisms, each with different characteristics suited to different use 
cases:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE IPC LANDSCAPE                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                    DATA TRANSFER MECHANISMS                          │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                      │ │
│   │   BYTE STREAM:              MESSAGE-BASED:                          │ │
│   │   ─────────────             ──────────────                          │ │
│   │   • Pipes                   • System V Message Queues               │ │
│   │   • FIFOs                   • POSIX Message Queues                  │ │
│   │   • Unix Stream Sockets    • Unix Datagram Sockets                 │ │
│   │                                                                      │ │
│   │   Data flows as            Messages have boundaries                 │ │
│   │   continuous stream        and can have types/priorities            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                    SHARED MEMORY MECHANISMS                          │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                      │ │
│   │   • System V Shared Memory (shmget/shmat)                           │ │
│   │   • POSIX Shared Memory (shm_open/mmap)                             │ │
│   │   • Memory-Mapped Files (mmap)                                      │ │
│   │   • Anonymous Mappings (mmap with MAP_SHARED|MAP_ANONYMOUS)         │ │
│   │                                                                      │ │
│   │   Fastest IPC - no kernel involvement after setup                   │ │
│   │   Requires explicit synchronization (semaphores, mutexes)           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                    SYNCHRONIZATION MECHANISMS                        │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                      │ │
│   │   • System V Semaphores (semget/semop)                              │ │
│   │   • POSIX Semaphores (sem_open/sem_wait)                            │ │
│   │   • File Locks (flock, fcntl)                                       │ │
│   │   • Futexes (Fast Userspace Mutexes)                                │ │
│   │                                                                      │ │
│   │   Coordinate access to shared resources                             │ │
│   │   Prevent race conditions                                            │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                    NOTIFICATION MECHANISMS                           │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                      │ │
│   │   • Signals (kill, sigqueue)                                        │ │
│   │   • eventfd (event notification)                                    │ │
│   │   • signalfd (synchronous signal handling)                          │ │
│   │                                                                      │ │
│   │   Lightweight notification without data transfer                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

The evolution of IPC in Unix reflects the system's growth from a simple time-sharing system to a sophisticated 
platform for distributed computing:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HISTORICAL EVOLUTION OF IPC                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1971 - FIRST EDITION UNIX                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Pipes introduced by Ken Thompson                                      │
│   • Simple, elegant mechanism for process pipelines                       │
│   • "Do one thing well" philosophy enabled by pipes                       │
│                                                                            │
│                                                                            │
│   1974 - FIFTH EDITION UNIX                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Signals formalized                                                    │
│   • Basic process notification                                            │
│                                                                            │
│                                                                            │
│   1983 - SYSTEM V RELEASE 2                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   • System V IPC introduced:                                              │
│     - Message Queues                                                      │
│     - Semaphores                                                          │
│     - Shared Memory                                                       │
│   • Designed for database and transaction processing                      │
│   • Key-based identification                                              │
│                                                                            │
│                                                                            │
│   1983 - 4.2BSD                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Berkeley Sockets introduced                                           │
│   • Unix Domain Sockets for local IPC                                    │
│   • Network transparency                                                  │
│                                                                            │
│                                                                            │
│   1993 - POSIX.1b (POSIX Real-Time Extensions)                           │
│   ─────────────────────────────────────────────────────────────────────   │
│   • POSIX IPC standardized:                                               │
│     - POSIX Message Queues                                                │
│     - POSIX Semaphores                                                    │
│     - POSIX Shared Memory                                                 │
│   • File descriptor based (unlike System V)                               │
│   • Better integration with select/poll                                   │
│                                                                            │
│                                                                            │
│   2002+ - MODERN LINUX                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│   • eventfd, timerfd, signalfd                                           │
│   • memfd_create for anonymous memory                                     │
│   • pidfd for process management                                          │
│   • io_uring for async I/O                                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 2. Pipes

### What is a Pipe?

A pipe is the oldest and simplest form of Unix IPC. It provides a unidirectional channel for data flow between 
processes, typically between a parent and child or between siblings.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE UNIX PIPE                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A pipe is a unidirectional data channel:                                │
│                                                                            │
│                                                                            │
│   ┌─────────────┐                              ┌─────────────┐            │
│   │  Process A  │                              │  Process B  │            │
│   │   (Writer)  │                              │   (Reader)  │            │
│   │             │                              │             │            │
│   │   write()   │                              │   read()    │            │
│   │      │      │                              │      ▲      │            │
│   │      ▼      │                              │      │      │            │
│   │  ┌───────┐  │      ┌──────────────┐       │  ┌───────┐  │            │
│   │  │ fd[1] │──┼─────►│  PIPE BUFFER │───────┼─►│ fd[0] │  │            │
│   │  │(write)│  │      │              │       │  │(read) │  │            │
│   │  └───────┘  │      │  ──────────► │       │  └───────┘  │            │
│   │             │      │  Data flows  │       │             │            │
│   └─────────────┘      │  this way    │       └─────────────┘            │
│                        └──────────────┘                                   │
│                                                                            │
│                                                                            │
│   KEY CHARACTERISTICS:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Unidirectional (one-way data flow)                                   │
│   • Byte stream (no message boundaries)                                   │
│   • FIFO ordering (first in, first out)                                  │
│   • Limited capacity (kernel buffer)                                      │
│   • Only between related processes (parent/child, siblings)              │
│   • No persistence (exists only while processes exist)                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### The pipe() System Call

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE pipe() SYSTEM CALL                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <unistd.h>                                                      │
│                                                                            │
│   int pipe(int pipefd[2]);                                                │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│                                                                            │
│   PARAMETERS:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│   pipefd[0]    Read end of the pipe                                       │
│   pipefd[1]    Write end of the pipe                                      │
│                                                                            │
│                                                                            │
│   TYPICAL USAGE PATTERN:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int pipefd[2];                                                           │
│   pipe(pipefd);                                                            │
│                                                                            │
│   if (fork() == 0) {                                                       │
│       /* Child: will read from pipe */                                    │
│       close(pipefd[1]);           /* Close unused write end */            │
│       read(pipefd[0], buf, size);                                         │
│       close(pipefd[0]);                                                   │
│   } else {                                                                 │
│       /* Parent: will write to pipe */                                    │
│       close(pipefd[0]);           /* Close unused read end */             │
│       write(pipefd[1], data, len);                                        │
│       close(pipefd[1]);                                                   │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   LINUX EXTENSION - pipe2():                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int pipe2(int pipefd[2], int flags);                                    │
│                                                                            │
│   Flags:                                                                   │
│   • O_CLOEXEC   - Close on exec                                           │
│   • O_NONBLOCK  - Non-blocking I/O                                        │
│   • O_DIRECT    - Packet mode (Linux 3.4+)                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Implementation of Pipes

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KERNEL IMPLEMENTATION OF PIPES                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   In the kernel, a pipe is implemented as a circular buffer with          │
│   associated synchronization:                                              │
│                                                                            │
│                                                                            │
│   struct pipe_inode_info {                                                │
│       struct mutex mutex;           /* Protects pipe state */             │
│       wait_queue_head_t rd_wait;    /* Readers waiting */                 │
│       wait_queue_head_t wr_wait;    /* Writers waiting */                 │
│       unsigned int head;            /* Write position */                  │
│       unsigned int tail;            /* Read position */                   │
│       unsigned int max_usage;       /* Max slots used */                  │
│       unsigned int ring_size;       /* Number of slots */                 │
│       unsigned int nr_accounted;    /* Accounted pages */                 │
│       unsigned int readers;         /* Number of readers */               │
│       unsigned int writers;         /* Number of writers */               │
│       unsigned int files;           /* Number of file refs */             │
│       unsigned int r_counter;       /* Reader open counter */             │
│       unsigned int w_counter;       /* Writer open counter */             │
│       struct page *tmp_page;        /* Cached page */                     │
│       struct pipe_buffer *bufs;     /* Circular buffer array */           │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   PIPE BUFFER STRUCTURE:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     CIRCULAR BUFFER                                  │ │
│   │                                                                      │ │
│   │   ┌───────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐ │ │
│   │   │ buf 0 │ buf 1 │ buf 2 │ buf 3 │ buf 4 │ buf 5 │ buf 6 │ buf 7 │ │ │
│   │   └───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘ │ │
│   │       ▲                               ▲                              │ │
│   │       │                               │                              │ │
│   │      tail                           head                             │ │
│   │     (read)                         (write)                           │ │
│   │                                                                      │ │
│   │   Each buffer slot:                                                  │ │
│   │   struct pipe_buffer {                                               │ │
│   │       struct page *page;     /* Page containing data */              │ │
│   │       unsigned int offset;   /* Offset within page */                │ │
│   │       unsigned int len;      /* Length of data */                    │ │
│   │       const struct pipe_buf_operations *ops;                         │ │
│   │       unsigned int flags;                                            │ │
│   │   };                                                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   DEFAULT CAPACITY:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Linux: 16 pages = 65,536 bytes (since Linux 2.6.11)                  │
│   • Can be changed via fcntl(F_SETPIPE_SZ)                               │
│   • Maximum: /proc/sys/fs/pipe-max-size (default 1MB)                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Pipe Capacity and Blocking

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIPE CAPACITY AND BLOCKING BEHAVIOR                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BLOCKING SCENARIOS:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│                                                                            │
│   1. READ FROM EMPTY PIPE (with writers):                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Reader                    Pipe Buffer                              │ │
│   │     │                      ┌─────────┐                               │ │
│   │     │  read()              │ (empty) │                               │ │
│   │     │────────────────────► │         │                               │ │
│   │     │                      └─────────┘                               │ │
│   │     │                                                                │ │
│   │     ▼                                                                │ │
│   │   BLOCKS until data available or all writers close                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   2. WRITE TO FULL PIPE (with readers):                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Writer                    Pipe Buffer                              │ │
│   │     │                      ┌─────────┐                               │ │
│   │     │  write()             │ (full)  │                               │ │
│   │     │────────────────────► │█████████│                               │ │
│   │     │                      └─────────┘                               │ │
│   │     │                                                                │ │
│   │     ▼                                                                │ │
│   │   BLOCKS until space available or all readers close                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   3. READ FROM PIPE WITH NO WRITERS:                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   read() returns 0 (EOF) immediately                                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   4. WRITE TO PIPE WITH NO READERS:                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   SIGPIPE signal sent to writer                                     │ │
│   │   write() returns -1 with errno = EPIPE                             │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   PIPE_BUF AND ATOMICITY:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   POSIX guarantees atomic writes up to PIPE_BUF bytes:                    │
│   • PIPE_BUF = 4096 bytes on Linux                                       │
│   • Writes ≤ PIPE_BUF: atomic (not interleaved)                          │
│   • Writes > PIPE_BUF: may be interleaved with other writes              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Closing Pipe Ends

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IMPORTANCE OF CLOSING PIPE ENDS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Proper closing of unused pipe ends is CRITICAL:                         │
│                                                                            │
│                                                                            │
│   BEFORE FORK:                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Parent Process                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │  fd[0] ─────────────────┐                                    │   │ │
│   │   │                         │                                    │   │ │
│   │   │                    ┌────┴────┐                               │   │ │
│   │   │                    │  PIPE   │                               │   │ │
│   │   │                    └────┬────┘                               │   │ │
│   │   │                         │                                    │   │ │
│   │   │  fd[1] ─────────────────┘                                    │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   AFTER FORK (before closing):                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Parent                              Child                          │ │
│   │   ┌───────────────┐                  ┌───────────────┐              │ │
│   │   │  fd[0] ───────┼──────────────────┼─────── fd[0]  │              │ │
│   │   │               │    ┌────────┐    │               │              │ │
│   │   │               └────┤  PIPE  ├────┘               │              │ │
│   │   │               ┌────┤        ├────┐               │              │ │
│   │   │               │    └────────┘    │               │              │ │
│   │   │  fd[1] ───────┼──────────────────┼─────── fd[1]  │              │ │
│   │   └───────────────┘                  └───────────────┘              │ │
│   │                                                                      │ │
│   │   Problem: 4 file descriptors reference the pipe!                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   AFTER PROPER CLOSING:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Parent (writer)                    Child (reader)                  │ │
│   │   ┌───────────────┐                  ┌───────────────┐              │ │
│   │   │  fd[0] CLOSED │                  │  fd[0] ───────┼──┐           │ │
│   │   │               │    ┌────────┐    │               │  │           │ │
│   │   │               │    │  PIPE  ├────┘               │  │ read()    │ │
│   │   │               └────┤        │                    │  │           │ │
│   │   │               │    └────────┘                    │  ▼           │ │
│   │   │  fd[1] ───────┼──┐               │  fd[1] CLOSED │              │ │
│   │   └───────────────┘  │ write()       └───────────────┘              │ │
│   │                      ▼                                               │ │
│   │                                                                      │ │
│   │   Now: EOF detected when parent closes fd[1]                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   WHY CLOSING MATTERS:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Reader won't see EOF until ALL write ends are closed                 │
│   • Writer won't get SIGPIPE until ALL read ends are closed              │
│   • Unclosed descriptors waste kernel resources                          │
│   • Can cause deadlocks (reader waiting for EOF that never comes)        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Pipes in the Shell

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIPES IN THE SHELL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The shell uses pipes to connect commands in a pipeline:                 │
│                                                                            │
│   $ cat file.txt | grep "pattern" | sort | uniq -c                        │
│                                                                            │
│                                                                            │
│   SHELL IMPLEMENTATION:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      │ │
│   │   │ cat │─────►│pipe1│─────►│grep │─────►│pipe2│─────►│sort │      │ │
│   │   └─────┘      └─────┘      └─────┘      └─────┘      └─────┘      │ │
│   │                                              │                       │ │
│   │                                              ▼                       │ │
│   │                                          ┌─────┐      ┌─────┐      │ │
│   │                                          │pipe3│─────►│uniq │      │ │
│   │                                          └─────┘      └─────┘      │ │
│   │                                                           │         │ │
│   │                                                           ▼         │ │
│   │                                                        stdout       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SHELL ALGORITHM FOR PIPELINE:                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   for each command in pipeline:                                            │
│       if not last command:                                                 │
│           create pipe                                                      │
│       fork()                                                               │
│       if child:                                                            │
│           if not first command:                                            │
│               dup2(prev_pipe[0], STDIN_FILENO)                            │
│               close prev_pipe ends                                         │
│           if not last command:                                             │
│               dup2(curr_pipe[1], STDOUT_FILENO)                           │
│               close curr_pipe ends                                         │
│           exec(command)                                                    │
│       else (parent):                                                       │
│           close unused pipe ends                                           │
│           prev_pipe = curr_pipe                                            │
│   wait for all children                                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 3. FIFOs (Named Pipes)

### What is a FIFO?

A FIFO (First In, First Out), also called a named pipe, is a pipe with a name in the filesystem. Unlike 
anonymous pipes, FIFOs can be used between unrelated processes.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FIFO (NAMED PIPE)                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A FIFO appears as a special file in the filesystem:                     │
│                                                                            │
│   $ ls -l /tmp/myfifo                                                     │
│   prw-r--r-- 1 user user 0 Feb 13 10:00 /tmp/myfifo                      │
│   │                                                                        │
│   └── 'p' indicates a pipe (FIFO)                                         │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process A                                    Process B             │ │
│   │   (unrelated)                                  (unrelated)           │ │
│   │                                                                      │ │
│   │   fd = open("/tmp/myfifo", O_WRONLY)          fd = open(...O_RDONLY)│ │
│   │        │                                            ▲               │ │
│   │        │                                            │               │ │
│   │        ▼                                            │               │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                              │   │ │
│   │   │                    /tmp/myfifo                               │   │ │
│   │   │                    ┌──────────────────────────────────┐     │   │ │
│   │   │   write() ────────►│          KERNEL BUFFER           │─────┼───┘ │
│   │   │                    └──────────────────────────────────┘     │     │
│   │   │                                                              │     │
│   │   └─────────────────────────────────────────────────────────────┘     │
│   │                                                                        │
│   └───────────────────────────────────────────────────────────────────────┘│
│                                                                            │
│                                                                            │
│   KEY DIFFERENCES FROM ANONYMOUS PIPES:                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Has a name in the filesystem                                          │
│   • Can be used between unrelated processes                               │
│   • Persists until explicitly deleted (but data doesn't persist)         │
│   • Must be opened by both reader and writer                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Creating FIFOs: mkfifo()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CREATING FIFOs                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/types.h>                                                   │
│   #include <sys/stat.h>                                                    │
│                                                                            │
│   int mkfifo(const char *pathname, mode_t mode);                          │
│   int mkfifoat(int dirfd, const char *pathname, mode_t mode);             │
│                                                                            │
│   Returns: 0 on success, -1 on error                                      │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   // Create a FIFO with read/write permissions for owner                  │
│   if (mkfifo("/tmp/myfifo", 0644) == -1) {                                │
│       if (errno == EEXIST) {                                              │
│           // FIFO already exists - that's OK                              │
│       } else {                                                             │
│           perror("mkfifo");                                                │
│           exit(1);                                                         │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   SHELL COMMAND:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   $ mkfifo /tmp/myfifo                                                    │
│   $ mkfifo -m 0644 /tmp/myfifo                                            │
│                                                                            │
│                                                                            │
│   COMMON ERRORS:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│   EEXIST     Path already exists                                          │
│   ENOENT     Directory component doesn't exist                            │
│   EACCES     Permission denied                                            │
│   ENOSPC     No space on filesystem                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Opening and Using FIFOs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    OPENING FIFOs                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FIFOs are opened using open() with specific blocking behavior:          │
│                                                                            │
│                                                                            │
│   BLOCKING BEHAVIOR (default):                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   open("/tmp/myfifo", O_RDONLY)                                     │ │
│   │   │                                                                  │ │
│   │   └───► BLOCKS until a writer opens the FIFO                       │ │
│   │                                                                      │ │
│   │   open("/tmp/myfifo", O_WRONLY)                                     │ │
│   │   │                                                                  │ │
│   │   └───► BLOCKS until a reader opens the FIFO                       │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   This ensures both ends are connected before I/O proceeds         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   NON-BLOCKING BEHAVIOR (O_NONBLOCK):                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   open("/tmp/myfifo", O_RDONLY | O_NONBLOCK)                        │ │
│   │   │                                                                  │ │
│   │   └───► Returns immediately (even without writer)                  │ │
│   │                                                                      │ │
│   │   open("/tmp/myfifo", O_WRONLY | O_NONBLOCK)                        │ │
│   │   │                                                                  │ │
│   │   └───► Returns -1 with ENXIO if no reader                         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   OPENING FOR BOTH READ AND WRITE:                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   fd = open("/tmp/myfifo", O_RDWR);                                       │
│                                                                            │
│   • Never blocks (process is both reader and writer)                      │
│   • Useful for keeping FIFO open between client connections              │
│   • Not standard POSIX behavior - avoid for portability                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### FIFO vs Pipe Comparison

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FIFO vs ANONYMOUS PIPE COMPARISON                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────────────────────┬─────────────────────┬─────────────────────┐  │
│   │      Feature           │    Anonymous Pipe    │       FIFO         │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Creation               │ pipe()/pipe2()      │ mkfifo()           │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Filesystem presence    │ No                  │ Yes                │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Related processes      │ Required            │ Not required       │  │
│   │ (fork)                 │                     │                    │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Persistence            │ Until all fds       │ Until unlink()     │  │
│   │                        │ closed              │ called             │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Data persistence       │ No                  │ No                 │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Naming                 │ File descriptors    │ Pathname           │  │
│   │                        │ only                │                    │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Direction              │ Unidirectional      │ Unidirectional     │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Buffer size            │ Same (PIPE_BUF)     │ Same (PIPE_BUF)    │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ select()/poll()        │ Yes                 │ Yes                │  │
│   ├────────────────────────┼─────────────────────┼─────────────────────┤  │
│   │ Use case               │ Parent-child        │ Client-server      │  │
│   │                        │ communication       │ IPC                │  │
│   └────────────────────────┴─────────────────────┴─────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### FIFO Use Cases

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FIFO USE CASES                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. CLIENT-SERVER WITH SINGLE FIFO (one direction):                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Multiple Clients            Server                                │ │
│   │   ┌────────┐                  ┌────────┐                            │ │
│   │   │Client 1│─────┐            │        │                            │ │
│   │   └────────┘     │            │        │                            │ │
│   │   ┌────────┐     │ /tmp/      │ Server │                            │ │
│   │   │Client 2│─────┼─server.fifo│        │                            │ │
│   │   └────────┘     │ ────────►  │        │                            │ │
│   │   ┌────────┐     │            │        │                            │ │
│   │   │Client 3│─────┘            └────────┘                            │ │
│   │   └────────┘                                                        │ │
│   │                                                                      │ │
│   │   Problem: Server can't respond to specific clients!                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   2. CLIENT-SERVER WITH REPLY FIFOS (bidirectional):                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Client                               Server                       │ │
│   │   ┌────────────┐                       ┌────────────┐               │ │
│   │   │            │                       │            │               │ │
│   │   │  1. Create │ /tmp/client.PID.fifo  │            │               │ │
│   │   │     own    │◄──────────────────────│            │               │ │
│   │   │     FIFO   │                       │            │               │ │
│   │   │            │                       │            │               │ │
│   │   │  2. Send   │ /tmp/server.fifo      │  Server    │               │ │
│   │   │   request  │──────────────────────►│  reads     │               │ │
│   │   │   + PID    │                       │  request   │               │ │
│   │   │            │                       │            │               │ │
│   │   │  3. Read   │ /tmp/client.PID.fifo  │  3. Send   │               │ │
│   │   │   reply    │◄──────────────────────│   reply    │               │ │
│   │   │            │                       │            │               │ │
│   │   └────────────┘                       └────────────┘               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   3. SHELL USAGE EXAMPLES:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   # Terminal 1: Create FIFO and read from it                              │
│   $ mkfifo /tmp/myfifo                                                    │
│   $ cat /tmp/myfifo                     # Blocks until writer            │
│                                                                            │
│   # Terminal 2: Write to the FIFO                                         │
│   $ echo "Hello" > /tmp/myfifo          # Unblocks the reader            │
│                                                                            │
│                                                                            │
│   # Backup to remote using FIFO and nc                                    │
│   $ mkfifo /tmp/backup.fifo                                               │
│   $ tar czf - /data > /tmp/backup.fifo &                                  │
│   $ nc remote.host 9999 < /tmp/backup.fifo                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 4. System V IPC Overview

System V IPC refers to three IPC mechanisms introduced in UNIX System V: message queues, semaphores, and 
shared memory. These mechanisms share common design principles.


### The System V IPC Model

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM V IPC MODEL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   System V IPC provides three facilities:                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │ │
│   │   │    MESSAGE     │  │   SEMAPHORES   │  │    SHARED      │       │ │
│   │   │    QUEUES      │  │                │  │    MEMORY      │       │ │
│   │   ├────────────────┤  ├────────────────┤  ├────────────────┤       │ │
│   │   │                │  │                │  │                │       │ │
│   │   │ • Discrete     │  │ • Process      │  │ • Fastest IPC  │       │ │
│   │   │   messages     │  │   synchroniz.  │  │                │       │ │
│   │   │ • Message      │  │ • Counting     │  │ • Direct mem   │       │ │
│   │   │   types        │  │   semaphores   │  │   access       │       │ │
│   │   │ • Priority     │  │ • Atomic ops   │  │ • Needs sync   │       │ │
│   │   │   queuing      │  │                │  │                │       │ │
│   │   │                │  │                │  │                │       │ │
│   │   └────────────────┘  └────────────────┘  └────────────────┘       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   COMMON CHARACTERISTICS:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   1. KEY-BASED IDENTIFICATION                                              │
│      • IPC objects identified by integer keys                             │
│      • Keys converted to IPC identifiers by kernel                        │
│                                                                            │
│   2. SYSTEM-WIDE NAMESPACE                                                 │
│      • IPC objects exist independently of processes                       │
│      • Persist until explicitly deleted or system reboot                  │
│                                                                            │
│   3. PERMISSION STRUCTURE                                                  │
│      • Similar to file permissions (owner, group, other)                  │
│      • Read and write (alter) permissions                                 │
│                                                                            │
│   4. COMMON HEADER                                                         │
│      • All System V IPC structures include ipc_perm                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### IPC Keys and Identifiers

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC KEYS AND IDENTIFIERS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Application                          Kernel                       │ │
│   │                                                                      │ │
│   │   ┌─────────┐                         ┌─────────────────────┐       │ │
│   │   │   KEY   │ ──── xxxget() ────────► │   IPC OBJECT TABLE  │       │ │
│   │   │ (key_t) │         │               │   ┌───┬───────────┐ │       │ │
│   │   └─────────┘         │               │   │ 0 │ object 0  │ │       │ │
│   │                       │               │   ├───┼───────────┤ │       │ │
│   │                       ▼               │   │ 1 │ object 1  │ │       │ │
│   │   ┌─────────┐   ┌──────────┐          │   ├───┼───────────┤ │       │ │
│   │   │   ID    │◄──│ Returns  │          │   │ 2 │ object 2  │◄┼───┐   │ │
│   │   │  (int)  │   │    ID    │          │   ├───┼───────────┤ │   │   │ │
│   │   └─────────┘   └──────────┘          │   │...│    ...    │ │   │   │ │
│   │       │                               │   └───┴───────────┘ │   │   │ │
│   │       │                               └─────────────────────┘   │   │ │
│   │       │                                                         │   │ │
│   │       └─── Used for subsequent operations ──────────────────────┘   │ │
│   │            (xxxctl, xxxop, etc.)                                    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KEY TYPES:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   IPC_PRIVATE (0)                                                          │
│   • Creates a new, unique IPC object                                      │
│   • Typically used between parent and child processes                     │
│   • Child inherits the identifier after fork()                            │
│                                                                            │
│   User-Defined Key                                                         │
│   • Any non-zero key_t value                                              │
│   • Used for unrelated processes to access same IPC object               │
│   • Often generated using ftok()                                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The ftok() Function

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE ftok() FUNCTION                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/types.h>                                                   │
│   #include <sys/ipc.h>                                                     │
│                                                                            │
│   key_t ftok(const char *pathname, int proj_id);                          │
│                                                                            │
│   Returns: key on success, -1 on error                                    │
│                                                                            │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   pathname ─────► stat() ─────► st_dev (device number)             │ │
│   │       │                         st_ino (inode number)              │ │
│   │       │                              │                              │ │
│   │       │                              │                              │ │
│   │       │                              ▼                              │ │
│   │       │           ┌──────────────────────────────────────┐          │ │
│   │       │           │                                      │          │ │
│   │       └──────────►│   KEY = f(st_dev, st_ino, proj_id)  │          │ │
│   │                   │                                      │          │ │
│   │   proj_id ───────►│   Combines into unique 32-bit key   │          │ │
│   │   (lower 8 bits)  │                                      │          │ │
│   │                   └──────────────────────────────────────┘          │ │
│   │                                      │                              │ │
│   │                                      ▼                              │ │
│   │                               ┌────────────┐                        │ │
│   │                               │   key_t    │                        │ │
│   │                               └────────────┘                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   key_t key;                                                               │
│                                                                            │
│   // Use existing file as basis for key                                   │
│   key = ftok("/tmp/myapp", 'A');  // proj_id = 65 ('A')                  │
│                                                                            │
│   if (key == -1) {                                                        │
│       perror("ftok");                                                     │
│       exit(1);                                                            │
│   }                                                                        │
│                                                                            │
│   // Now use key with msgget(), semget(), or shmget()                     │
│                                                                            │
│                                                                            │
│   LIMITATIONS:                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│   • pathname must exist and be accessible                                 │
│   • If file is deleted and recreated, key may change                     │
│   • Only lower 8 bits of proj_id are used                                │
│   • Collisions possible (different paths → same key)                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### IPC Permissions Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC PERMISSIONS STRUCTURE                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct ipc_perm {                                                        │
│       key_t          __key;    /* Key supplied to xxxget() */             │
│       uid_t          uid;      /* Effective UID of owner */               │
│       gid_t          gid;      /* Effective GID of owner */               │
│       uid_t          cuid;     /* Effective UID of creator */             │
│       gid_t          cgid;     /* Effective GID of creator */             │
│       unsigned short mode;     /* Permissions */                          │
│       unsigned short __seq;    /* Sequence number */                      │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   PERMISSION BITS:                                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────┬───────────────────────────────────────────────────────────┐  │
│   │  Bit   │  Description                                              │  │
│   ├────────┼───────────────────────────────────────────────────────────┤  │
│   │ 0400   │  Read by owner                                           │  │
│   │ 0200   │  Write by owner                                          │  │
│   │ 0040   │  Read by group                                           │  │
│   │ 0020   │  Write by group                                          │  │
│   │ 0004   │  Read by other                                           │  │
│   │ 0002   │  Write by other                                          │  │
│   └────────┴───────────────────────────────────────────────────────────┘  │
│                                                                            │
│   Note: "Write" means:                                                     │
│   • Message queues: send messages                                         │
│   • Semaphores: alter semaphore values                                    │
│   • Shared memory: attach for writing                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### IPC Commands: ipcs and ipcrm

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC COMMANDS                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   IPCS - DISPLAY IPC FACILITIES:                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   $ ipcs                    # Show all IPC objects                        │
│   $ ipcs -q                 # Show only message queues                    │
│   $ ipcs -s                 # Show only semaphores                        │
│   $ ipcs -m                 # Show only shared memory                     │
│   $ ipcs -a                 # Show all details                            │
│                                                                            │
│                                                                            │
│   EXAMPLE OUTPUT:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ------ Message Queues --------                                           │
│   key        msqid      owner      perms      used-bytes   messages       │
│   0x0000162e 0          user       644        0            0              │
│                                                                            │
│   ------ Shared Memory Segments --------                                   │
│   key        shmid      owner      perms      bytes      nattch           │
│   0x00001234 32768      user       644        4096       2                │
│                                                                            │
│   ------ Semaphore Arrays --------                                         │
│   key        semid      owner      perms      nsems                       │
│   0x00005678 65536      user       644        1                           │
│                                                                            │
│                                                                            │
│   IPCRM - REMOVE IPC FACILITIES:                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   $ ipcrm -q <msqid>        # Remove message queue by ID                  │
│   $ ipcrm -Q <key>          # Remove message queue by key                 │
│   $ ipcrm -s <semid>        # Remove semaphore by ID                      │
│   $ ipcrm -S <key>          # Remove semaphore by key                     │
│   $ ipcrm -m <shmid>        # Remove shared memory by ID                  │
│   $ ipcrm -M <key>          # Remove shared memory by key                 │
│   $ ipcrm -a                # Remove all (Linux extension)                │
│                                                                            │
│                                                                            │
│   SYSTEM LIMITS:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   $ ipcs -l                 # Show system limits                          │
│                                                                            │
│   ------ Messages Limits --------                                          │
│   max queues system wide = 32000                                           │
│   max size of message (bytes) = 8192                                       │
│   default max size of queue (bytes) = 16384                                │
│                                                                            │
│   ------ Shared Memory Limits --------                                     │
│   max number of segments = 4096                                            │
│   max seg size (kbytes) = 18014398509465599                               │
│   max total shared memory (kbytes) = 18014398509481980                    │
│                                                                            │
│   ------ Semaphore Limits --------                                         │
│   max number of arrays = 32000                                             │
│   max semaphores per array = 32000                                         │
│   max semaphores system wide = 1024000000                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 5. System V Message Queues

Message queues provide a way to exchange discrete messages between processes. Each message has a type and a 
body.

### Message Queue Operations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE QUEUE OPERATIONS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/types.h>                                                   │
│   #include <sys/ipc.h>                                                     │
│   #include <sys/msg.h>                                                     │
│                                                                            │
│                                                                            │
│   CREATE/ACCESS QUEUE:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int msgget(key_t key, int msgflg);                                      │
│                                                                            │
│   Returns: message queue identifier on success, -1 on error              │
│                                                                            │
│   Flags:                                                                   │
│   • IPC_CREAT     Create queue if it doesn't exist                        │
│   • IPC_EXCL      Fail if queue exists (with IPC_CREAT)                  │
│   • Permission bits (e.g., 0644)                                          │
│                                                                            │
│                                                                            │
│   SEND MESSAGE:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int msgsnd(int msqid, const void *msgp, size_t msgsz, int msgflg);     │
│                                                                            │
│   Returns: 0 on success, -1 on error                                     │
│                                                                            │
│   • msgp points to message buffer (must start with long mtype)            │
│   • msgsz is size of message body (not including mtype)                   │
│   • IPC_NOWAIT: return immediately if queue full                          │
│                                                                            │
│                                                                            │
│   RECEIVE MESSAGE:                                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ssize_t msgrcv(int msqid, void *msgp, size_t msgsz,                    │
│                  long msgtyp, int msgflg);                                │
│                                                                            │
│   Returns: number of bytes in message body, -1 on error                  │
│                                                                            │
│   msgtyp behavior:                                                         │
│   • = 0:  Receive first message (any type)                                │
│   • > 0:  Receive first message of type msgtyp                            │
│   • < 0:  Receive first message with type ≤ |msgtyp|                      │
│                                                                            │
│   Flags:                                                                   │
│   • IPC_NOWAIT:   Return immediately if no message                        │
│   • MSG_NOERROR: Truncate message if too large                            │
│   • MSG_EXCEPT:  Receive first message NOT of type msgtyp (Linux)        │
│                                                                            │
│                                                                            │
│   CONTROL OPERATIONS:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int msgctl(int msqid, int cmd, struct msqid_ds *buf);                  │
│                                                                            │
│   Commands:                                                                │
│   • IPC_STAT:  Get queue status into buf                                  │
│   • IPC_SET:   Set permissions from buf                                   │
│   • IPC_RMID:  Remove queue immediately                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Message Queue Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE QUEUE STRUCTURE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MESSAGE BUFFER FORMAT:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct msgbuf {                                                          │
│       long mtype;       /* Message type (must be > 0) */                  │
│       char mtext[1];    /* Message body (variable length) */              │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   EXAMPLE CUSTOM MESSAGE:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct my_message {                                                      │
│       long mtype;                                                          │
│       int  command;                                                        │
│       char data[256];                                                      │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   KERNEL QUEUE STRUCTURE:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct msqid_ds (in kernel)                                       │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │ struct ipc_perm msg_perm     /* Permissions */               │  │ │
│   │   │ time_t          msg_stime    /* Last msgsnd time */          │  │ │
│   │   │ time_t          msg_rtime    /* Last msgrcv time */          │  │ │
│   │   │ time_t          msg_ctime    /* Last change time */          │  │ │
│   │   │ unsigned long   msg_cbytes   /* Bytes in queue */            │  │ │
│   │   │ msgqnum_t       msg_qnum     /* Messages in queue */         │  │ │
│   │   │ msglen_t        msg_qbytes   /* Max bytes allowed */         │  │ │
│   │   │ pid_t           msg_lspid    /* Last msgsnd PID */           │  │ │
│   │   │ pid_t           msg_lrpid    /* Last msgrcv PID */           │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                          │                                          │ │
│   │                          │                                          │ │
│   │                          ▼                                          │ │
│   │   ┌───────────────────────────────────────────────────────────┐    │ │
│   │   │              MESSAGE QUEUE (Linked List)                   │    │ │
│   │   │                                                            │    │ │
│   │   │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │    │ │
│   │   │   │ type: 1 │──►│ type: 2 │──►│ type: 1 │──►│ type: 3 │  │    │ │
│   │   │   │ data... │   │ data... │   │ data... │   │ data... │  │    │ │
│   │   │   └─────────┘   └─────────┘   └─────────┘   └─────────┘  │    │ │
│   │   │                                                            │    │ │
│   │   │   Messages are stored in FIFO order within the queue      │    │ │
│   │   │   but can be retrieved by type                             │    │ │
│   │   │                                                            │    │ │
│   │   └───────────────────────────────────────────────────────────┘    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Message Queue Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE QUEUE EXAMPLE                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SENDER:                                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/msg.h>                                                    │
│   #include <string.h>                                                     │
│                                                                            │
│   struct msgbuf {                                                          │
│       long mtype;                                                          │
│       char mtext[256];                                                     │
│   };                                                                       │
│                                                                            │
│   int main() {                                                             │
│       key_t key = ftok("/tmp/msgq", 'A');                                 │
│       int msqid = msgget(key, IPC_CREAT | 0644);                          │
│                                                                            │
│       struct msgbuf msg;                                                   │
│       msg.mtype = 1;                        /* Message type */            │
│       strcpy(msg.mtext, "Hello, World!");                                 │
│                                                                            │
│       msgsnd(msqid, &msg, strlen(msg.mtext) + 1, 0);                     │
│                                                                            │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   RECEIVER:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int main() {                                                             │
│       key_t key = ftok("/tmp/msgq", 'A');                                 │
│       int msqid = msgget(key, 0);           /* Access existing */        │
│                                                                            │
│       struct msgbuf msg;                                                   │
│       msgrcv(msqid, &msg, sizeof(msg.mtext), 1, 0);  /* Type 1 */        │
│                                                                            │
│       printf("Received: %s\n", msg.mtext);                                │
│                                                                            │
│       msgctl(msqid, IPC_RMID, NULL);        /* Remove queue */            │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 6. System V Semaphores

System V semaphores are counting semaphores used for synchronization between processes. Unlike binary 
semaphores, they can hold any non-negative integer value.

### Semaphore Operations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE OPERATIONS                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/types.h>                                                   │
│   #include <sys/ipc.h>                                                     │
│   #include <sys/sem.h>                                                     │
│                                                                            │
│                                                                            │
│   CREATE/ACCESS SEMAPHORE SET:                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int semget(key_t key, int nsems, int semflg);                           │
│                                                                            │
│   Returns: semaphore set identifier on success, -1 on error              │
│                                                                            │
│   • nsems: Number of semaphores in the set (1 or more)                   │
│   • Flags: IPC_CREAT, IPC_EXCL, permission bits                          │
│                                                                            │
│                                                                            │
│   SEMAPHORE OPERATIONS:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int semop(int semid, struct sembuf *sops, size_t nsops);               │
│                                                                            │
│   struct sembuf {                                                          │
│       unsigned short sem_num;   /* Semaphore number (0, 1, ...) */       │
│       short          sem_op;    /* Operation */                          │
│       short          sem_flg;   /* IPC_NOWAIT, SEM_UNDO */               │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   SEM_OP VALUES:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   sem_op > 0:  ADD to semaphore value (V operation)                 │ │
│   │                semval += sem_op                                      │ │
│   │                Wake up waiting processes if any                      │ │
│   │                                                                      │ │
│   │   sem_op < 0:  SUBTRACT from semaphore (P operation)                │ │
│   │                If semval >= |sem_op|:                                │ │
│   │                    semval -= |sem_op|                                │ │
│   │                Else:                                                 │ │
│   │                    Block until semval >= |sem_op|                   │ │
│   │                                                                      │ │
│   │   sem_op = 0:  WAIT FOR ZERO                                        │ │
│   │                Block until semval == 0                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   CONTROL OPERATIONS:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int semctl(int semid, int semnum, int cmd, ...);                       │
│                                                                            │
│   Commands:                                                                │
│   • SETVAL:   Set semaphore value                                         │
│   • GETVAL:   Get semaphore value                                         │
│   • SETALL:   Set all semaphores in set                                   │
│   • GETALL:   Get all semaphore values                                    │
│   • IPC_STAT: Get status                                                  │
│   • IPC_SET:  Set permissions                                             │
│   • IPC_RMID: Remove semaphore set                                        │
│   • GETNCNT:  Get number of processes waiting for increase               │
│   • GETZCNT:  Get number of processes waiting for zero                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Semaphore Structure and SEM_UNDO

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE STRUCTURE                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KERNEL SEMAPHORE SET STRUCTURE:                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct semid_ds                                                   │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │ struct ipc_perm sem_perm     /* Permissions */               │  │ │
│   │   │ time_t          sem_otime    /* Last semop time */           │  │ │
│   │   │ time_t          sem_ctime    /* Last change time */          │  │ │
│   │   │ unsigned long   sem_nsems    /* Number of semaphores */      │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                          │                                          │ │
│   │                          ▼                                          │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │              SEMAPHORE ARRAY                                  │  │ │
│   │   │   ┌────────┬────────┬────────┬────────┬────────┐             │  │ │
│   │   │   │ sem[0] │ sem[1] │ sem[2] │  ...   │sem[n-1]│             │  │ │
│   │   │   │  val   │  val   │  val   │        │  val   │             │  │ │
│   │   │   └────────┴────────┴────────┴────────┴────────┘             │  │ │
│   │   │                                                               │  │ │
│   │   │   Each semaphore:                                            │  │ │
│   │   │   • semval:  Current value                                   │  │ │
│   │   │   • sempid:  PID of last operation                          │  │ │
│   │   │   • semncnt: Count of processes waiting for increase        │  │ │
│   │   │   • semzcnt: Count of processes waiting for zero            │  │ │
│   │   │                                                               │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   THE SEM_UNDO FLAG:                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   When SEM_UNDO is set, the kernel tracks all semaphore adjustments      │
│   and automatically reverses them when the process terminates:            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Process acquires lock:                                            │ │
│   │                                                                      │ │
│   │   struct sembuf op = {0, -1, SEM_UNDO};                            │ │
│   │   semop(semid, &op, 1);                                            │ │
│   │                                                                      │ │
│   │   Kernel records: "This process owes +1 to sem[0]"                  │ │
│   │                                                                      │ │
│   │   If process exits without releasing:                               │ │
│   │   • Kernel automatically adds +1 to sem[0]                          │ │
│   │   • Prevents deadlock from abnormal termination                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Semaphore Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SEMAPHORE EXAMPLE: BINARY SEMAPHORE                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Using a semaphore as a mutex (binary semaphore):                        │
│                                                                            │
│   union semun {                                                            │
│       int              val;                                                │
│       struct semid_ds *buf;                                               │
│       unsigned short  *array;                                             │
│   };                                                                       │
│                                                                            │
│   /* Initialize semaphore to 1 (unlocked) */                              │
│   int init_semaphore() {                                                  │
│       key_t key = ftok("/tmp/sem", 'S');                                  │
│       int semid = semget(key, 1, IPC_CREAT | 0644);                      │
│                                                                            │
│       union semun arg;                                                     │
│       arg.val = 1;                           /* Initial value = 1 */     │
│       semctl(semid, 0, SETVAL, arg);                                     │
│                                                                            │
│       return semid;                                                        │
│   }                                                                        │
│                                                                            │
│   /* P operation (wait/lock) */                                           │
│   void sem_lock(int semid) {                                              │
│       struct sembuf op = {0, -1, SEM_UNDO};                              │
│       semop(semid, &op, 1);                                              │
│   }                                                                        │
│                                                                            │
│   /* V operation (signal/unlock) */                                       │
│   void sem_unlock(int semid) {                                            │
│       struct sembuf op = {0, 1, SEM_UNDO};                               │
│       semop(semid, &op, 1);                                              │
│   }                                                                        │
│                                                                            │
│   int main() {                                                             │
│       int semid = init_semaphore();                                       │
│                                                                            │
│       sem_lock(semid);                                                    │
│       /* Critical section - exclusive access */                           │
│       printf("In critical section\n");                                    │
│       sem_unlock(semid);                                                  │
│                                                                            │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 7. System V Shared Memory

System V shared memory is the fastest form of IPC because data doesn't need to be copied between 
processes—they access the same physical memory.

### Shared Memory Operations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHARED MEMORY OPERATIONS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/types.h>                                                   │
│   #include <sys/ipc.h>                                                     │
│   #include <sys/shm.h>                                                     │
│                                                                            │
│                                                                            │
│   CREATE/ACCESS SHARED MEMORY:                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int shmget(key_t key, size_t size, int shmflg);                        │
│                                                                            │
│   Returns: shared memory identifier on success, -1 on error              │
│                                                                            │
│   • size: Size in bytes (rounded up to page boundary)                     │
│   • Flags: IPC_CREAT, IPC_EXCL, permission bits                          │
│                                                                            │
│                                                                            │
│   ATTACH TO ADDRESS SPACE:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void *shmat(int shmid, const void *shmaddr, int shmflg);               │
│                                                                            │
│   Returns: pointer to shared memory, (void *)-1 on error                 │
│                                                                            │
│   • shmaddr: Suggested address (usually NULL for kernel choice)          │
│   • Flags:                                                                 │
│     - SHM_RDONLY: Attach read-only                                        │
│     - SHM_RND:    Round shmaddr down to page boundary                    │
│                                                                            │
│                                                                            │
│   DETACH FROM ADDRESS SPACE:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int shmdt(const void *shmaddr);                                         │
│                                                                            │
│   Returns: 0 on success, -1 on error                                     │
│                                                                            │
│   • Does NOT delete the shared memory segment                             │
│   • Only removes mapping from process address space                       │
│                                                                            │
│                                                                            │
│   CONTROL OPERATIONS:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int shmctl(int shmid, int cmd, struct shmid_ds *buf);                  │
│                                                                            │
│   Commands:                                                                │
│   • IPC_STAT:  Get status                                                 │
│   • IPC_SET:   Set permissions                                            │
│   • IPC_RMID:  Mark for deletion (deleted when nattch reaches 0)         │
│   • SHM_LOCK:  Lock segment in memory (privileged)                       │
│   • SHM_UNLOCK: Unlock segment                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Shared Memory Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHARED MEMORY STRUCTURE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KERNEL SHARED MEMORY STRUCTURE:                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   struct shmid_ds                                                   │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │ struct ipc_perm shm_perm      /* Permissions */              │  │ │
│   │   │ size_t          shm_segsz     /* Size of segment (bytes) */  │  │ │
│   │   │ time_t          shm_atime     /* Last attach time */         │  │ │
│   │   │ time_t          shm_dtime     /* Last detach time */         │  │ │
│   │   │ time_t          shm_ctime     /* Last change time */         │  │ │
│   │   │ pid_t           shm_cpid      /* PID of creator */           │  │ │
│   │   │ pid_t           shm_lpid      /* PID of last shmat/shmdt */  │  │ │
│   │   │ shmatt_t        shm_nattch    /* Current attach count */     │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SHARED MEMORY IN PROCESS ADDRESS SPACE:                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Process A                          Process B                             │
│   ┌──────────────────┐              ┌──────────────────┐                  │
│   │      Stack       │              │      Stack       │                  │
│   ├──────────────────┤              ├──────────────────┤                  │
│   │       ...        │              │       ...        │                  │
│   ├──────────────────┤              ├──────────────────┤                  │
│   │  Shared Memory ──┼──────┬───────┼── Shared Memory  │                  │
│   │    (mapped)      │      │       │    (mapped)      │                  │
│   ├──────────────────┤      │       ├──────────────────┤                  │
│   │       ...        │      │       │       ...        │                  │
│   ├──────────────────┤      │       ├──────────────────┤                  │
│   │      Heap        │      │       │      Heap        │                  │
│   ├──────────────────┤      │       ├──────────────────┤                  │
│   │      Data        │      │       │      Data        │                  │
│   ├──────────────────┤      │       ├──────────────────┤                  │
│   │      Text        │      │       │      Text        │                  │
│   └──────────────────┘      │       └──────────────────┘                  │
│                             │                                              │
│                             ▼                                              │
│                    ┌──────────────────┐                                   │
│                    │  Physical Memory │                                   │
│                    │   (Shared Page)  │                                   │
│                    │                  │                                   │
│                    │  ┌────────────┐  │                                   │
│                    │  │   Data     │  │                                   │
│                    │  └────────────┘  │                                   │
│                    │                  │                                   │
│                    └──────────────────┘                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Synchronization with Shared Memory

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SYNCHRONIZATION WITH SHARED MEMORY                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CRITICAL ISSUE: RACE CONDITIONS                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Shared memory provides NO synchronization. Without proper locking:      │
│                                                                            │
│   Process A                         Process B                              │
│      │                                  │                                  │
│      │ reads value = 10                 │                                  │
│      │                                  │ reads value = 10                 │
│      │ value = value + 5                │                                  │
│      │                                  │ value = value + 3                │
│      │ writes value = 15                │                                  │
│      │                                  │ writes value = 13  ← WRONG!      │
│      ▼                                  ▼                                  │
│                                                                            │
│   Expected: 10 + 5 + 3 = 18                                               │
│   Actual: 13 (Process A's update lost!)                                   │
│                                                                            │
│                                                                            │
│   SYNCHRONIZATION OPTIONS:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   1. System V Semaphores                                                   │
│      - Traditional approach                                                │
│      - Works across unrelated processes                                   │
│      - Persistent until explicitly removed                                │
│                                                                            │
│   2. POSIX Semaphores                                                      │
│      - Named: sem_open() for unrelated processes                          │
│      - Unnamed: sem_init() in shared memory                               │
│                                                                            │
│   3. pthread Mutexes in Shared Memory                                      │
│      - Must use PTHREAD_PROCESS_SHARED attribute                          │
│      - Higher performance than semaphores                                 │
│                                                                            │
│   4. File Locking (fcntl/flock)                                           │
│      - Simple but slower                                                   │
│      - Works with any shared resource                                     │
│                                                                            │
│                                                                            │
│   PTHREAD MUTEX IN SHARED MEMORY:                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct shared_data {                                                     │
│       pthread_mutex_t mutex;                                               │
│       int counter;                                                         │
│   };                                                                       │
│                                                                            │
│   /* Creator process */                                                    │
│   struct shared_data *data = shmat(shmid, NULL, 0);                       │
│                                                                            │
│   pthread_mutexattr_t attr;                                                │
│   pthread_mutexattr_init(&attr);                                           │
│   pthread_mutexattr_setpshared(&attr, PTHREAD_PROCESS_SHARED);            │
│   pthread_mutex_init(&data->mutex, &attr);                                │
│                                                                            │
│   /* Any process using the shared memory */                                │
│   pthread_mutex_lock(&data->mutex);                                       │
│   data->counter++;                                                         │
│   pthread_mutex_unlock(&data->mutex);                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Shared Memory Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHARED MEMORY EXAMPLE                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WRITER PROCESS:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/shm.h>                                                    │
│   #include <string.h>                                                     │
│                                                                            │
│   struct shared_data {                                                     │
│       int ready;                                                           │
│       char message[256];                                                   │
│   };                                                                       │
│                                                                            │
│   int main() {                                                             │
│       key_t key = ftok("/tmp/shm", 'M');                                  │
│       int shmid = shmget(key, sizeof(struct shared_data),                │
│                          IPC_CREAT | 0644);                               │
│                                                                            │
│       struct shared_data *data = shmat(shmid, NULL, 0);                  │
│                                                                            │
│       strcpy(data->message, "Hello from shared memory!");                │
│       data->ready = 1;                 /* Signal reader */               │
│                                                                            │
│       /* Keep running while reader processes */                           │
│       sleep(10);                                                           │
│                                                                            │
│       shmdt(data);                                                        │
│       shmctl(shmid, IPC_RMID, NULL);   /* Remove when done */            │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   READER PROCESS:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int main() {                                                             │
│       key_t key = ftok("/tmp/shm", 'M');                                  │
│       int shmid = shmget(key, 0, 0);   /* Access existing */             │
│                                                                            │
│       struct shared_data *data = shmat(shmid, NULL, SHM_RDONLY);        │
│                                                                            │
│       while (!data->ready)             /* Wait for data */               │
│           usleep(1000);                                                    │
│                                                                            │
│       printf("Read: %s\n", data->message);                                │
│                                                                            │
│       shmdt(data);                                                        │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   NOTE: This example uses busy-waiting (polling). In production,          │
│   use proper synchronization (semaphores, condition variables).           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 8. POSIX IPC

POSIX IPC provides a more modern alternative to System V IPC with file-descriptor-based APIs.


### POSIX vs System V IPC

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX VS SYSTEM V IPC                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────┬────────────────────┬────────────────────────────┐   │
│   │ Feature         │ System V           │ POSIX                      │   │
│   ├─────────────────┼────────────────────┼────────────────────────────┤   │
│   │ Identification  │ Key (key_t)        │ Name (string "/name")      │   │
│   │ API Style       │ xxxget/xxxctl      │ xxx_open/xxx_close         │   │
│   │ File Descriptor │ No (uses IDs)      │ Yes (uses fds)             │   │
│   │ select/poll     │ Not supported      │ Supported (mq only)        │   │
│   │ Namespace       │ System-wide        │ Filesystem-like            │   │
│   │ Reference Count │ Manual cleanup     │ Automatic (unlink+close)   │   │
│   │ Atomicity       │ Set operations     │ Individual operations      │   │
│   │ Portability     │ Wider support      │ Better designed            │   │
│   └─────────────────┴────────────────────┴────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   POSIX IPC NAMING:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   POSIX IPC objects use names that start with '/':                        │
│                                                                            │
│   /myqueue          Message queue                                          │
│   /mysemaphore      Semaphore                                              │
│   /myshm            Shared memory                                          │
│                                                                            │
│   On Linux, these appear in:                                               │
│   • /dev/mqueue/     for message queues                                   │
│   • /dev/shm/        for shared memory                                    │
│   • Semaphores may not have visible filesystem representation             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### POSIX Message Queues

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX MESSAGE QUEUES                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <mqueue.h>                                                      │
│   /* Link with -lrt */                                                    │
│                                                                            │
│                                                                            │
│   CREATE/OPEN QUEUE:                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   mqd_t mq_open(const char *name, int oflag, ...);                       │
│                                                                            │
│   /* mode_t mode, struct mq_attr *attr - when creating */                │
│                                                                            │
│   Flags: O_RDONLY, O_WRONLY, O_RDWR, O_CREAT, O_EXCL, O_NONBLOCK         │
│                                                                            │
│   struct mq_attr {                                                         │
│       long mq_flags;       /* 0 or O_NONBLOCK */                          │
│       long mq_maxmsg;      /* Max messages in queue */                    │
│       long mq_msgsize;     /* Max message size (bytes) */                 │
│       long mq_curmsgs;     /* Current messages in queue */                │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   SEND/RECEIVE:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int mq_send(mqd_t mqdes, const char *msg_ptr,                          │
│               size_t msg_len, unsigned int msg_prio);                     │
│                                                                            │
│   ssize_t mq_receive(mqd_t mqdes, char *msg_ptr,                         │
│                      size_t msg_len, unsigned int *msg_prio);            │
│                                                                            │
│   • Messages have priority (0-31, higher = more urgent)                   │
│   • mq_receive always returns highest priority message first             │
│   • msg_len must be >= mq_msgsize                                         │
│                                                                            │
│                                                                            │
│   TIMED OPERATIONS:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int mq_timedsend(..., const struct timespec *abs_timeout);             │
│   ssize_t mq_timedreceive(..., const struct timespec *abs_timeout);      │
│                                                                            │
│                                                                            │
│   NOTIFICATION:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int mq_notify(mqd_t mqdes, const struct sigevent *notification);       │
│                                                                            │
│   • Get notified when empty queue receives a message                      │
│   • Can use signal or spawn a thread                                      │
│                                                                            │
│                                                                            │
│   CLOSE/REMOVE:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int mq_close(mqd_t mqdes);           /* Close descriptor */            │
│   int mq_unlink(const char *name);     /* Remove queue */                │
│                                                                            │
│   • unlink marks for deletion (deleted when all close)                    │
│   • Similar to file unlink semantics                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### POSIX Semaphores

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX SEMAPHORES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <semaphore.h>                                                   │
│   /* Link with -pthread */                                                │
│                                                                            │
│                                                                            │
│   TWO TYPES OF POSIX SEMAPHORES:                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   NAMED SEMAPHORES (for unrelated processes):                       │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   sem_t *sem_open(const char *name, int oflag,                     │ │
│   │                   mode_t mode, unsigned int value);                │ │
│   │   int sem_close(sem_t *sem);                                       │ │
│   │   int sem_unlink(const char *name);                                │ │
│   │                                                                      │ │
│   │   Example:                                                          │ │
│   │   sem_t *sem = sem_open("/mysem", O_CREAT, 0644, 1);              │ │
│   │   sem_wait(sem);     /* P operation */                             │ │
│   │   /* critical section */                                           │ │
│   │   sem_post(sem);     /* V operation */                             │ │
│   │   sem_close(sem);                                                  │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   UNNAMED SEMAPHORES (for related processes or threads):           │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   int sem_init(sem_t *sem, int pshared, unsigned int value);       │ │
│   │   int sem_destroy(sem_t *sem);                                     │ │
│   │                                                                      │ │
│   │   pshared = 0:  For threads in same process                        │ │
│   │   pshared = 1:  For processes (sem must be in shared memory)       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SEMAPHORE OPERATIONS:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int sem_wait(sem_t *sem);         /* Block until > 0, then decrement */│
│   int sem_trywait(sem_t *sem);      /* Non-blocking wait */              │
│   int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout);    │
│   int sem_post(sem_t *sem);         /* Increment (wake waiters) */       │
│   int sem_getvalue(sem_t *sem, int *sval);  /* Get current value */     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### POSIX Shared Memory

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX SHARED MEMORY                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/mman.h>                                                    │
│   #include <fcntl.h>                                                       │
│   /* Link with -lrt */                                                    │
│                                                                            │
│                                                                            │
│   CREATE/OPEN SHARED MEMORY:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int shm_open(const char *name, int oflag, mode_t mode);                │
│                                                                            │
│   Returns: file descriptor on success, -1 on error                       │
│                                                                            │
│   Flags: O_RDONLY, O_RDWR, O_CREAT, O_EXCL, O_TRUNC                       │
│                                                                            │
│   • Returns fd referencing shared memory object                           │
│   • Initially has size 0 - must use ftruncate()                          │
│                                                                            │
│                                                                            │
│   SET SIZE:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int ftruncate(int fd, off_t length);                                   │
│                                                                            │
│   • Required after creation to set size                                   │
│   • Size rounded up to page boundary                                      │
│                                                                            │
│                                                                            │
│   MAP INTO ADDRESS SPACE:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void *mmap(void *addr, size_t length, int prot, int flags,             │
│              int fd, off_t offset);                                       │
│                                                                            │
│   prot: PROT_READ, PROT_WRITE, PROT_EXEC                                 │
│   flags: MAP_SHARED (required for IPC)                                    │
│                                                                            │
│                                                                            │
│   UNMAP AND REMOVE:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int munmap(void *addr, size_t length);  /* Unmap from address space */ │
│   int close(int fd);                       /* Close file descriptor */   │
│   int shm_unlink(const char *name);        /* Remove shm object */       │
│                                                                            │
│                                                                            │
│   COMPLETE EXAMPLE:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   /* Creator */                                                            │
│   int fd = shm_open("/myshm", O_CREAT | O_RDWR, 0644);                   │
│   ftruncate(fd, 4096);                                                    │
│   void *ptr = mmap(NULL, 4096, PROT_READ | PROT_WRITE,                   │
│                    MAP_SHARED, fd, 0);                                    │
│   close(fd);                        /* fd not needed after mmap */       │
│                                                                            │
│   /* Use shared memory */                                                  │
│   strcpy(ptr, "Hello!");                                                  │
│                                                                            │
│   /* Cleanup */                                                            │
│   munmap(ptr, 4096);                                                      │
│   shm_unlink("/myshm");                                                   │
│                                                                            │
│                                                                            │
│   /* Accessor (another process) */                                        │
│   int fd = shm_open("/myshm", O_RDONLY, 0);                              │
│   void *ptr = mmap(NULL, 4096, PROT_READ, MAP_SHARED, fd, 0);           │
│   printf("%s\n", (char *)ptr);                                           │
│   munmap(ptr, 4096);                                                      │
│   close(fd);                                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 9. Memory-Mapped Files

Memory-mapped files provide a powerful IPC mechanism by allowing multiple processes to share access to the 
same file through their address space.

### mmap() for IPC

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MMAP() FOR IPC                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   void *mmap(void *addr, size_t length, int prot, int flags,             │
│              int fd, off_t offset);                                       │
│                                                                            │
│                                                                            │
│   MAPPING TYPES FOR IPC:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. FILE-BACKED SHARED MAPPING (MAP_SHARED + regular file):       │ │
│   │      • Changes visible to all processes                             │ │
│   │      • Changes written back to file                                 │ │
│   │      • Provides persistence                                         │ │
│   │                                                                      │ │
│   │   2. ANONYMOUS SHARED MAPPING (MAP_SHARED | MAP_ANONYMOUS):        │ │
│   │      • Shared between parent and child after fork()                │ │
│   │      • No backing file (pure memory)                               │ │
│   │      • More efficient than file-backed for IPC                     │ │
│   │                                                                      │ │
│   │   3. POSIX SHARED MEMORY (shm_open + mmap):                        │ │
│   │      • Named for unrelated processes                               │ │
│   │      • Uses tmpfs (RAM-backed filesystem)                          │ │
│   │      • Faster than disk-backed files                               │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   MAP_SHARED VS MAP_PRIVATE:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   MAP_SHARED:                                                              │
│   • Changes visible to all mappers                                        │
│   • Changes written to underlying file                                    │
│   • Required for IPC                                                       │
│                                                                            │
│   MAP_PRIVATE:                                                             │
│   • Copy-on-write semantics                                               │
│   • Changes private to this process                                       │
│   • NOT suitable for IPC                                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Anonymous Shared Mapping Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ANONYMOUS SHARED MAPPING                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   For parent-child communication without a file:                          │
│                                                                            │
│   #include <sys/mman.h>                                                    │
│   #include <sys/wait.h>                                                    │
│                                                                            │
│   int main() {                                                             │
│       /* Create anonymous shared mapping */                                │
│       int *shared = mmap(NULL, sizeof(int),                               │
│                          PROT_READ | PROT_WRITE,                          │
│                          MAP_SHARED | MAP_ANONYMOUS,                       │
│                          -1, 0);                    /* fd=-1, offset=0 */ │
│                                                                            │
│       *shared = 0;                                                         │
│                                                                            │
│       if (fork() == 0) {                                                  │
│           /* Child */                                                      │
│           (*shared)++;                                                     │
│           printf("Child set shared to %d\n", *shared);                    │
│           exit(0);                                                        │
│       }                                                                    │
│                                                                            │
│       /* Parent */                                                         │
│       wait(NULL);                                                          │
│       printf("Parent sees shared = %d\n", *shared);                       │
│                                                                            │
│       munmap(shared, sizeof(int));                                        │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│   Output:                                                                  │
│   Child set shared to 1                                                    │
│   Parent sees shared = 1                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### File-Backed Shared Mapping Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILE-BACKED SHARED MAPPING                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   For unrelated processes using a regular file:                           │
│                                                                            │
│   /* Writer process */                                                     │
│   int fd = open("/tmp/shared_data", O_CREAT | O_RDWR, 0644);             │
│   ftruncate(fd, 4096);                                                    │
│                                                                            │
│   char *ptr = mmap(NULL, 4096, PROT_READ | PROT_WRITE,                   │
│                    MAP_SHARED, fd, 0);                                    │
│   close(fd);                                                              │
│                                                                            │
│   strcpy(ptr, "Data from writer process");                                │
│   msync(ptr, 4096, MS_SYNC);           /* Force write to disk */         │
│                                                                            │
│   munmap(ptr, 4096);                                                      │
│                                                                            │
│                                                                            │
│   /* Reader process (can run independently) */                            │
│   int fd = open("/tmp/shared_data", O_RDONLY);                           │
│   char *ptr = mmap(NULL, 4096, PROT_READ, MAP_SHARED, fd, 0);           │
│   close(fd);                                                              │
│                                                                            │
│   printf("Read: %s\n", ptr);                                              │
│                                                                            │
│   munmap(ptr, 4096);                                                      │
│                                                                            │
│                                                                            │
│   MSYNC FLAGS:                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • MS_SYNC:   Synchronous write (blocks until complete)                 │
│   • MS_ASYNC:  Asynchronous write (returns immediately)                  │
│   • MS_INVALIDATE: Invalidate cached data                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 10. Signals as IPC

Signals are the oldest form of IPC in Unix, originally designed for exception handling but also usable for 
simple interprocess notification.

### Signal Fundamentals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL FUNDAMENTALS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHAT IS A SIGNAL:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   A signal is an asynchronous notification sent to a process.            │
│   It can come from:                                                        │
│   • The kernel (hardware faults, timer expiration)                        │
│   • Another process (kill, sigqueue)                                      │
│   • The process itself (raise, abort)                                     │
│                                                                            │
│                                                                            │
│   SIGNAL DELIVERY:                                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────┐    signal     ┌────────────┐                             │
│   │ Process A  │ ─────────────►│ Process B  │                             │
│   └────────────┘    (async)    └────────────┘                             │
│                                      │                                     │
│                                      ▼                                     │
│                              ┌───────────────┐                            │
│                              │ Signal Handler│                            │
│                              │  or Default   │                            │
│                              │   Action      │                            │
│                              └───────────────┘                            │
│                                                                            │
│                                                                            │
│   LIMITATIONS FOR IPC:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Standard signals: no data payload                                     │
│   • Signals can be lost (not queued by default)                          │
│   • Asynchronous nature makes programming complex                         │
│   • Limited number of signal types                                        │
│   • Signal handlers have restrictions (async-signal-safe functions)      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Sending Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SENDING SIGNALS                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BASIC SIGNAL SENDING:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int kill(pid_t pid, int sig);                                           │
│                                                                            │
│   pid interpretation:                                                      │
│   • pid > 0:   Send to specific process                                   │
│   • pid == 0:  Send to all processes in sender's process group           │
│   • pid == -1: Send to all processes (sender has permission)             │
│   • pid < -1:  Send to all processes in group |pid|                      │
│                                                                            │
│   int raise(int sig);           /* Send signal to self */                │
│                                                                            │
│                                                                            │
│   COMMON SIGNALS FOR IPC:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   SIGUSR1, SIGUSR2:  User-defined signals (no default meaning)           │
│   SIGCHLD:           Child status change notification                     │
│   SIGPIPE:           Write to pipe with no reader                        │
│   SIGALRM:           Timer expiration                                     │
│   SIGHUP:            Often used for configuration reload                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Real-time Signals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME SIGNALS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Real-time signals (SIGRTMIN to SIGRTMAX) overcome standard signal       │
│   limitations:                                                             │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   ADVANTAGES OVER STANDARD SIGNALS:                                 │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   1. QUEUED:    Multiple instances are queued, not lost            │ │
│   │   2. ORDERED:   Delivered in FIFO order                            │ │
│   │   3. PAYLOAD:   Can carry an integer or pointer (sigqueue)         │ │
│   │   4. RANGE:     At least 32 signals (SIGRTMIN to SIGRTMAX)         │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SENDING WITH DATA (sigqueue):                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <signal.h>                                                      │
│                                                                            │
│   int sigqueue(pid_t pid, int sig, const union sigval value);            │
│                                                                            │
│   union sigval {                                                           │
│       int   sival_int;      /* Integer value */                           │
│       void *sival_ptr;      /* Pointer value (same address space) */     │
│   };                                                                       │
│                                                                            │
│   Example:                                                                 │
│   union sigval sv;                                                         │
│   sv.sival_int = 42;                                                       │
│   sigqueue(target_pid, SIGRTMIN, sv);                                     │
│                                                                            │
│                                                                            │
│   RECEIVING WITH SA_SIGINFO:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct sigaction sa;                                                     │
│   sa.sa_sigaction = handler;     /* 3-arg handler */                      │
│   sa.sa_flags = SA_SIGINFO;                                                │
│   sigaction(SIGRTMIN, &sa, NULL);                                         │
│                                                                            │
│   void handler(int sig, siginfo_t *info, void *ucontext) {               │
│       printf("Signal %d from PID %d\n", sig, info->si_pid);              │
│       printf("Value: %d\n", info->si_value.sival_int);                   │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   SIGINFO_T STRUCTURE:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   siginfo_t {                                                              │
│       int      si_signo;     /* Signal number */                          │
│       int      si_errno;     /* errno value */                            │
│       int      si_code;      /* Signal code */                            │
│       pid_t    si_pid;       /* Sending process ID */                     │
│       uid_t    si_uid;       /* Real UID of sender */                     │
│       union sigval si_value; /* Value from sigqueue */                    │
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Signal Handling Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNAL-BASED IPC EXAMPLE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   /* Server: waits for signals from clients */                            │
│                                                                            │
│   #include <signal.h>                                                      │
│   #include <stdio.h>                                                       │
│                                                                            │
│   volatile sig_atomic_t request_count = 0;                                │
│                                                                            │
│   void handler(int sig, siginfo_t *info, void *ctx) {                    │
│       request_count++;                                                     │
│       printf("Request from PID %d: %d\n",                                 │
│              info->si_pid, info->si_value.sival_int);                     │
│   }                                                                        │
│                                                                            │
│   int main() {                                                             │
│       struct sigaction sa = {0};                                          │
│       sa.sa_sigaction = handler;                                          │
│       sa.sa_flags = SA_SIGINFO;                                            │
│       sigaction(SIGRTMIN, &sa, NULL);                                     │
│                                                                            │
│       printf("Server PID: %d\n", getpid());                               │
│                                                                            │
│       while (1) {                                                          │
│           pause();  /* Wait for signal */                                 │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   /* Client: sends request to server */                                   │
│                                                                            │
│   int main(int argc, char *argv[]) {                                      │
│       pid_t server_pid = atoi(argv[1]);                                   │
│       union sigval sv;                                                     │
│       sv.sival_int = 100;  /* Request code */                             │
│                                                                            │
│       sigqueue(server_pid, SIGRTMIN, sv);                                 │
│       printf("Sent request to %d\n", server_pid);                         │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 11. Unix Domain Sockets

Unix domain sockets provide the most versatile IPC mechanism, combining the socket API with local-only 
communication.

### Unix Domain Socket Fundamentals

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX DOMAIN SOCKET FUNDAMENTALS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Unix domain sockets (also called local sockets or IPC sockets)          │
│   provide bidirectional communication between processes on the same       │
│   host.                                                                    │
│                                                                            │
│                                                                            │
│   WHY UNIX DOMAIN SOCKETS:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   • Use familiar socket API (socket, bind, listen, accept, etc.)   │ │
│   │   • Bidirectional communication                                     │ │
│   │   • Support both stream and datagram modes                         │ │
│   │   • Pass file descriptors between processes                        │ │
│   │   • Pass credentials (PID, UID, GID)                               │ │
│   │   • Much faster than TCP/IP loopback                               │ │
│   │   • No network stack overhead                                       │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SOCKET TYPES:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┬───────────────────────────────────────────────────┐ │
│   │ Type            │ Description                                       │ │
│   ├─────────────────┼───────────────────────────────────────────────────┤ │
│   │ SOCK_STREAM     │ Connection-oriented, reliable, ordered            │ │
│   │                 │ Like TCP, but local only                          │ │
│   │                 │ Requires connect/accept                           │ │
│   ├─────────────────┼───────────────────────────────────────────────────┤ │
│   │ SOCK_DGRAM      │ Connectionless, message-based                     │ │
│   │                 │ Like UDP, but reliable on local system           │ │
│   │                 │ Message boundaries preserved                      │ │
│   ├─────────────────┼───────────────────────────────────────────────────┤ │
│   │ SOCK_SEQPACKET  │ Connection-oriented + message boundaries         │ │
│   │                 │ Best of both worlds                               │ │
│   │                 │ Like SCTP, but local only                        │ │
│   └─────────────────┴───────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Socket Addressing

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX DOMAIN SOCKET ADDRESSING                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/socket.h>                                                  │
│   #include <sys/un.h>                                                      │
│                                                                            │
│   struct sockaddr_un {                                                     │
│       sa_family_t sun_family;    /* AF_UNIX */                            │
│       char        sun_path[108]; /* Pathname */                           │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   TWO ADDRESSING MODES:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   1. PATHNAME SOCKETS (Traditional):                               │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   struct sockaddr_un addr;                                          │ │
│   │   addr.sun_family = AF_UNIX;                                        │ │
│   │   strcpy(addr.sun_path, "/tmp/my.socket");                         │ │
│   │                                                                      │ │
│   │   • Creates a socket file in the filesystem                        │ │
│   │   • Must unlink() before bind if file exists                       │ │
│   │   • Subject to filesystem permissions                               │ │
│   │   • Visible with ls: srwxr-xr-x (type 's')                        │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   2. ABSTRACT NAMESPACE (Linux-specific):                          │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │                                                                      │ │
│   │   addr.sun_path[0] = '\0';                                          │ │
│   │   strcpy(addr.sun_path + 1, "my_abstract_socket");                 │ │
│   │                                                                      │ │
│   │   • First byte is null (indicates abstract)                        │ │
│   │   • No filesystem entry created                                     │ │
│   │   • Auto-removed when all sockets close                            │ │
│   │   • No filesystem permission checks                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Stream Socket Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX DOMAIN STREAM SOCKET                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   /* SERVER */                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   #include <sys/socket.h>                                                  │
│   #include <sys/un.h>                                                      │
│                                                                            │
│   int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);                        │
│                                                                            │
│   struct sockaddr_un addr = {0};                                          │
│   addr.sun_family = AF_UNIX;                                               │
│   strcpy(addr.sun_path, "/tmp/my.socket");                                │
│                                                                            │
│   unlink("/tmp/my.socket");  /* Remove if exists */                       │
│   bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));                │
│   listen(server_fd, 5);                                                    │
│                                                                            │
│   int client_fd = accept(server_fd, NULL, NULL);                          │
│   char buf[256];                                                           │
│   read(client_fd, buf, sizeof(buf));                                      │
│   write(client_fd, "Response", 8);                                        │
│   close(client_fd);                                                        │
│                                                                            │
│                                                                            │
│   /* CLIENT */                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int client_fd = socket(AF_UNIX, SOCK_STREAM, 0);                        │
│                                                                            │
│   struct sockaddr_un addr = {0};                                          │
│   addr.sun_family = AF_UNIX;                                               │
│   strcpy(addr.sun_path, "/tmp/my.socket");                                │
│                                                                            │
│   connect(client_fd, (struct sockaddr *)&addr, sizeof(addr));             │
│   write(client_fd, "Request", 7);                                          │
│   read(client_fd, buf, sizeof(buf));                                      │
│   close(client_fd);                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### socketpair() for Related Processes

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SOCKETPAIR()                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Creates a pair of connected sockets (like a bidirectional pipe):        │
│                                                                            │
│   int socketpair(int domain, int type, int protocol, int sv[2]);         │
│                                                                            │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │     sv[0] ◄─────────────────────────────────────────────► sv[1]  │    │
│   │           write()                                    read()      │    │
│   │           read()                                     write()     │    │
│   │                                                                   │    │
│   │     Both ends can read AND write (bidirectional)                │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int sv[2];                                                               │
│   socketpair(AF_UNIX, SOCK_STREAM, 0, sv);                                │
│                                                                            │
│   if (fork() == 0) {                                                      │
│       /* Child uses sv[1] */                                              │
│       close(sv[0]);                                                        │
│       write(sv[1], "From child", 10);                                     │
│       read(sv[1], buf, sizeof(buf));                                      │
│       close(sv[1]);                                                        │
│       exit(0);                                                             │
│   }                                                                        │
│                                                                            │
│   /* Parent uses sv[0] */                                                  │
│   close(sv[1]);                                                            │
│   read(sv[0], buf, sizeof(buf));                                          │
│   write(sv[0], "From parent", 11);                                        │
│   close(sv[0]);                                                            │
│   wait(NULL);                                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### Passing File Descriptors (SCM_RIGHTS)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PASSING FILE DESCRIPTORS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Unix domain sockets can send file descriptors between processes!        │
│   This is one of the most powerful IPC features.                          │
│                                                                            │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Process A                              Process B                 │  │
│   │   ┌────────┐                             ┌────────┐                │  │
│   │   │ fd = 5 │ ───(SCM_RIGHTS)───────────► │ fd = 8 │                │  │
│   │   └───┬────┘     via socket              └───┬────┘                │  │
│   │       │                                      │                      │  │
│   │       ▼                                      ▼                      │  │
│   │   ┌────────┐                             ┌────────┐                │  │
│   │   │ File   │                             │ File   │ (same file!)  │  │
│   │   │ Object │ ◄───────────────────────────│ Object │                │  │
│   │   └────────┘                             └────────┘                │  │
│   │                                                                     │  │
│   │   Both processes now have access to the same kernel file object   │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   SENDING A FILE DESCRIPTOR:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   void send_fd(int socket, int fd_to_send) {                             │
│       struct msghdr msg = {0};                                            │
│       struct iovec iov[1];                                                │
│       char buf[1] = {'x'};  /* At least 1 byte of data required */       │
│                                                                            │
│       /* Ancillary data buffer */                                         │
│       char cmsgbuf[CMSG_SPACE(sizeof(int))];                             │
│                                                                            │
│       iov[0].iov_base = buf;                                              │
│       iov[0].iov_len = 1;                                                  │
│       msg.msg_iov = iov;                                                   │
│       msg.msg_iovlen = 1;                                                  │
│                                                                            │
│       msg.msg_control = cmsgbuf;                                          │
│       msg.msg_controllen = sizeof(cmsgbuf);                               │
│                                                                            │
│       struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);                        │
│       cmsg->cmsg_level = SOL_SOCKET;                                      │
│       cmsg->cmsg_type = SCM_RIGHTS;                                       │
│       cmsg->cmsg_len = CMSG_LEN(sizeof(int));                            │
│       *((int *)CMSG_DATA(cmsg)) = fd_to_send;                            │
│                                                                            │
│       sendmsg(socket, &msg, 0);                                           │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   RECEIVING A FILE DESCRIPTOR:                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int recv_fd(int socket) {                                               │
│       struct msghdr msg = {0};                                            │
│       struct iovec iov[1];                                                │
│       char buf[1];                                                         │
│       char cmsgbuf[CMSG_SPACE(sizeof(int))];                             │
│                                                                            │
│       iov[0].iov_base = buf;                                              │
│       iov[0].iov_len = 1;                                                  │
│       msg.msg_iov = iov;                                                   │
│       msg.msg_iovlen = 1;                                                  │
│       msg.msg_control = cmsgbuf;                                          │
│       msg.msg_controllen = sizeof(cmsgbuf);                               │
│                                                                            │
│       recvmsg(socket, &msg, 0);                                           │
│                                                                            │
│       struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);                        │
│       return *((int *)CMSG_DATA(cmsg));                                  │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Passing Credentials (SCM_CREDENTIALS)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PASSING CREDENTIALS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Unix domain sockets can pass and verify peer credentials:               │
│                                                                            │
│   struct ucred {                                                           │
│       pid_t pid;    /* Process ID of sender */                            │
│       uid_t uid;    /* User ID of sender */                               │
│       gid_t gid;    /* Group ID of sender */                              │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   ENABLING CREDENTIAL PASSING:                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int enable = 1;                                                          │
│   setsockopt(sock, SOL_SOCKET, SO_PASSCRED, &enable, sizeof(enable));    │
│                                                                            │
│                                                                            │
│   GETTING PEER CREDENTIALS (simpler method):                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   /* For connected sockets, use getsockopt */                             │
│   struct ucred cred;                                                       │
│   socklen_t len = sizeof(cred);                                            │
│   getsockopt(client_fd, SOL_SOCKET, SO_PEERCRED, &cred, &len);           │
│                                                                            │
│   printf("Peer PID: %d, UID: %d, GID: %d\n",                             │
│          cred.pid, cred.uid, cred.gid);                                   │
│                                                                            │
│                                                                            │
│   USE CASES:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Authentication without passwords (verify UID)                         │
│   • Access control based on process identity                              │
│   • Audit logging (who connected?)                                        │
│   • D-Bus uses this extensively for security                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


---

## 12. Modern IPC Mechanisms

Linux provides several modern IPC mechanisms that address specific use cases with better integration with the 
event-driven programming model.

### eventfd

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVENTFD                                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   eventfd creates a file descriptor for event notification.               │
│   Simpler and more efficient than pipes for signaling.                    │
│                                                                            │
│   #include <sys/eventfd.h>                                                │
│                                                                            │
│   int eventfd(unsigned int initval, int flags);                          │
│                                                                            │
│   Flags:                                                                   │
│   • EFD_CLOEXEC:    Close on exec                                        │
│   • EFD_NONBLOCK:   Non-blocking                                          │
│   • EFD_SEMAPHORE:  Semaphore-like semantics                             │
│                                                                            │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   eventfd maintains a 64-bit counter:                              │ │
│   │                                                                      │ │
│   │   write(efd, &val, 8):  Adds val to counter                        │ │
│   │   read(efd, &val, 8):   Returns counter, resets to 0               │ │
│   │                          (with EFD_SEMAPHORE: decrements by 1)     │ │
│   │                                                                      │ │
│   │   Can use with epoll/select/poll                                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int efd = eventfd(0, EFD_NONBLOCK);                                     │
│                                                                            │
│   /* Signal event (writer) */                                             │
│   uint64_t val = 1;                                                        │
│   write(efd, &val, sizeof(val));                                          │
│                                                                            │
│   /* Wait for event (reader) */                                           │
│   uint64_t count;                                                          │
│   read(efd, &count, sizeof(count));                                       │
│   printf("Got %lu events\n", count);                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### timerfd

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TIMERFD                                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   timerfd creates a file descriptor that delivers timer notifications.   │
│                                                                            │
│   #include <sys/timerfd.h>                                                │
│                                                                            │
│   int timerfd_create(int clockid, int flags);                            │
│   int timerfd_settime(int fd, int flags,                                 │
│                       const struct itimerspec *new_value,                │
│                       struct itimerspec *old_value);                     │
│   int timerfd_gettime(int fd, struct itimerspec *curr_value);           │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK);               │
│                                                                            │
│   struct itimerspec ts = {                                                │
│       .it_interval = {1, 0},    /* Repeat every 1 second */              │
│       .it_value = {1, 0}        /* First expiration in 1 second */       │
│   };                                                                       │
│   timerfd_settime(tfd, 0, &ts, NULL);                                    │
│                                                                            │
│   /* Use in epoll loop */                                                 │
│   uint64_t expirations;                                                    │
│   read(tfd, &expirations, sizeof(expirations));                          │
│   /* expirations = number of times timer fired since last read */        │
│                                                                            │
│                                                                            │
│   ADVANTAGES:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Integrates with epoll/select/poll                                     │
│   • No signal handling complexity                                         │
│   • Multiple independent timers possible                                  │
│   • Can be passed between processes via SCM_RIGHTS                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### signalfd

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALFD                                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   signalfd creates a file descriptor for receiving signals synchronously. │
│                                                                            │
│   #include <sys/signalfd.h>                                               │
│                                                                            │
│   int signalfd(int fd, const sigset_t *mask, int flags);                 │
│                                                                            │
│                                                                            │
│   HOW TO USE:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   1. Block the signals with sigprocmask()                                 │
│   2. Create signalfd with same signal mask                                │
│   3. Read signal info from fd (struct signalfd_siginfo)                  │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   sigset_t mask;                                                           │
│   sigemptyset(&mask);                                                      │
│   sigaddset(&mask, SIGINT);                                                │
│   sigaddset(&mask, SIGTERM);                                               │
│                                                                            │
│   /* Block so they don't trigger default handler */                       │
│   sigprocmask(SIG_BLOCK, &mask, NULL);                                    │
│                                                                            │
│   int sfd = signalfd(-1, &mask, SFD_NONBLOCK);                           │
│                                                                            │
│   /* In event loop */                                                      │
│   struct signalfd_siginfo info;                                            │
│   read(sfd, &info, sizeof(info));                                         │
│                                                                            │
│   if (info.ssi_signo == SIGINT) {                                         │
│       printf("Got SIGINT from PID %d\n", info.ssi_pid);                  │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   ADVANTAGES:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • No async signal handling complexity                                    │
│   • Integrates with event loops (epoll/select/poll)                       │
│   • Can handle multiple signals in main loop                              │
│   • Full signal information available                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### memfd_create

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMFD_CREATE                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   memfd_create creates an anonymous file backed by memory.                │
│   Perfect for sharing memory without filesystem visibility.              │
│                                                                            │
│   #include <sys/mman.h>                                                    │
│                                                                            │
│   int memfd_create(const char *name, unsigned int flags);                │
│                                                                            │
│   Flags:                                                                   │
│   • MFD_CLOEXEC:       Close on exec                                      │
│   • MFD_ALLOW_SEALING: Allow adding seals                                 │
│   • MFD_HUGETLB:       Use huge pages                                     │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   /* Create memory file */                                                 │
│   int mfd = memfd_create("shared_buffer", MFD_CLOEXEC);                  │
│   ftruncate(mfd, 4096);                                                    │
│                                                                            │
│   /* Map it */                                                             │
│   void *ptr = mmap(NULL, 4096, PROT_READ | PROT_WRITE,                   │
│                    MAP_SHARED, mfd, 0);                                   │
│                                                                            │
│   /* Pass fd to another process via SCM_RIGHTS */                        │
│   send_fd(socket, mfd);                                                    │
│                                                                            │
│                                                                            │
│   USE CASES:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Share memory without filesystem namespace pollution                   │
│   • Zero-copy buffer passing between processes                            │
│   • In-memory file content for execve (with MFD_CLOEXEC)                 │
│   • Wayland compositor buffer sharing                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### pidfd

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIDFD                                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   pidfd provides a file descriptor reference to a process.               │
│   Solves the PID reuse race condition problem.                           │
│                                                                            │
│   #include <sys/syscall.h>                                                │
│                                                                            │
│   int pidfd_open(pid_t pid, unsigned int flags);                         │
│   int pidfd_send_signal(int pidfd, int sig, siginfo_t *info, int flags);│
│                                                                            │
│                                                                            │
│   THE PID REUSE PROBLEM:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Traditional:                                                     │  │
│   │   1. Get target PID (e.g., 1234)                                   │  │
│   │   2. Target exits                                                   │  │
│   │   3. New process gets PID 1234                                     │  │
│   │   4. kill(1234, SIGTERM) kills wrong process!                     │  │
│   │                                                                     │  │
│   │   With pidfd:                                                       │  │
│   │   1. pidfd_open(1234) returns fd referring to target              │  │
│   │   2. Target exits                                                   │  │
│   │   3. pidfd_send_signal(fd, SIGTERM) returns ESRCH (safe!)        │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   WAITING ON PROCESSES:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   /* Can poll/epoll on pidfd for process exit */                         │
│   int pidfd = pidfd_open(child_pid, 0);                                  │
│                                                                            │
│   struct pollfd pfd = { .fd = pidfd, .events = POLLIN };                │
│   poll(&pfd, 1, -1);  /* Blocks until process exits */                  │
│                                                                            │
│   /* Now safe to waitid */                                                │
│   siginfo_t info;                                                          │
│   waitid(P_PIDFD, pidfd, &info, WEXITED);                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 13. IPC Performance and Selection

### Performance Comparison

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC PERFORMANCE COMPARISON                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────┬──────────┬───────────┬──────────┬─────────────────┐ │
│   │ Mechanism       │ Latency  │ Throughput│ Overhead │ Best For        │ │
│   ├─────────────────┼──────────┼───────────┼──────────┼─────────────────┤ │
│   │ Shared Memory   │ Lowest   │ Highest   │ Lowest   │ Large data      │ │
│   │ Unix Socket     │ Low      │ High      │ Low      │ General IPC     │ │
│   │ Pipe            │ Low      │ High      │ Low      │ Parent-child    │ │
│   │ Message Queue   │ Medium   │ Medium    │ Medium   │ Structured msgs │ │
│   │ Signal          │ Low      │ N/A       │ Low      │ Notification    │ │
│   │ eventfd         │ Lowest   │ N/A       │ Lowest   │ Event signaling │ │
│   │ FIFO            │ Low      │ High      │ Low      │ Unrelated procs │ │
│   │ Semaphore       │ Low      │ N/A       │ Low      │ Synchronization │ │
│   └─────────────────┴──────────┴───────────┴──────────┴─────────────────┘ │
│                                                                            │
│                                                                            │
│   LATENCY COMPARISON (approximate, single message):                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Shared Memory:     ~100 ns   (just memory access + sync)                │
│   eventfd:           ~500 ns   (minimal kernel path)                      │
│   Unix Socket:       ~1-2 μs   (socket buffer copy)                       │
│   Pipe:              ~1-2 μs   (pipe buffer copy)                         │
│   Signal:            ~2-3 μs   (signal delivery overhead)                 │
│   SysV Message Queue:~3-5 μs   (more kernel overhead)                     │
│                                                                            │
│                                                                            │
│   THROUGHPUT (data transfer):                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Shared Memory:     Memory bandwidth (10+ GB/s)                          │
│   Unix Socket:       ~4-8 GB/s (optimized path)                           │
│   Pipe:              ~3-6 GB/s (similar to socket)                        │
│   Message Queue:     ~1-2 GB/s (message overhead)                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### When to Use Which IPC

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC SELECTION GUIDE                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                       DECISION FLOWCHART                            │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                    Need IPC?                                               │
│                        │                                                   │
│           ┌───────────┼───────────┐                                       │
│           ▼           │           ▼                                       │
│    Related procs?     │     Unrelated procs?                              │
│           │           │           │                                        │
│     ┌─────┴─────┐     │     ┌─────┴─────┐                                 │
│     ▼           ▼     │     ▼           ▼                                 │
│   Stream?    Event?   │  Named?    Anonymous?                             │
│     │         │       │     │           │                                 │
│     ▼         ▼       │     ▼           ▼                                 │
│   pipe()   eventfd    │   FIFO     Unix Socket                            │
│            socketpair │   Unix Socket (path)                              │
│                       │   Message Queue                                    │
│                       │   Shared Memory                                    │
│                                                                            │
│                                                                            │
│   USE CASE RECOMMENDATIONS:                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ Use Case                        │ Recommended IPC                   │ │
│   ├─────────────────────────────────┼───────────────────────────────────┤ │
│   │ Shell pipeline (ls | grep)      │ Pipe                              │ │
│   │ Client-server daemon            │ Unix Domain Socket                │ │
│   │ High-throughput data sharing    │ Shared Memory + eventfd/futex     │ │
│   │ Multiple readers, one writer    │ Message Queue or Shared Memory    │ │
│   │ Simple process notification     │ Signal or eventfd                 │ │
│   │ Timer-based events              │ timerfd                           │ │
│   │ Mutual exclusion                │ Semaphore or futex                │ │
│   │ Passing file descriptors        │ Unix Domain Socket (SCM_RIGHTS)   │ │
│   │ Database buffer pool            │ Shared Memory + Semaphores        │ │
│   │ Microservices (same host)       │ Unix Domain Socket                │ │
│   │ Event loop integration          │ eventfd/timerfd/signalfd          │ │
│   └─────────────────────────────────┴───────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### IPC Design Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC DESIGN PATTERNS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PATTERN 1: PRODUCER-CONSUMER (SHARED MEMORY)                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────┐     ┌─────────────────────────┐     ┌─────────────┐    │
│   │  Producer   │     │     Shared Memory       │     │  Consumer   │    │
│   │             │     │  ┌─────────────────┐    │     │             │    │
│   │  write()    │────►│  │ Ring Buffer     │    │────►│  read()     │    │
│   │             │     │  │ [][][][][]...   │    │     │             │    │
│   └─────────────┘     │  └─────────────────┘    │     └─────────────┘    │
│         │             │  ┌─────────────────┐    │           │            │
│         └────────────►│  │ Semaphore/Futex │◄───┼───────────┘            │
│                       │  │ (sync)          │    │                        │
│                       │  └─────────────────┘    │                        │
│                       └─────────────────────────┘                        │
│                                                                            │
│                                                                            │
│   PATTERN 2: REQUEST-RESPONSE (UNIX SOCKET)                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────┐                              ┌─────────────┐            │
│   │   Client    │                              │   Server    │            │
│   │             │       Unix Socket            │             │            │
│   │  connect()  │─────────────────────────────►│  accept()   │            │
│   │  send()     │─────── Request ─────────────►│  recv()     │            │
│   │  recv()     │◄────── Response ─────────────│  send()     │            │
│   │  close()    │                              │  close()    │            │
│   └─────────────┘                              └─────────────┘            │
│                                                                            │
│                                                                            │
│   PATTERN 3: WORK QUEUE (MESSAGE QUEUE)                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌──────────┐                                                            │
│   │ Producer │──┐       ┌─────────────────────┐      ┌──────────┐        │
│   └──────────┘  │       │    Message Queue    │      │ Worker 1 │        │
│                 ├──────►│ ┌───┬───┬───┬───┐   │─────►└──────────┘        │
│   ┌──────────┐  │       │ │msg│msg│msg│msg│   │                          │
│   │ Producer │──┤       │ └───┴───┴───┴───┘   │      ┌──────────┐        │
│   └──────────┘  │       └─────────────────────┘─────►│ Worker 2 │        │
│                 │                                     └──────────┘        │
│   ┌──────────┐  │                                                         │
│   │ Producer │──┘                                    ┌──────────┐        │
│   └──────────┘                                  ────►│ Worker 3 │        │
│                                                       └──────────┘        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Common Pitfalls

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMMON IPC PITFALLS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. RESOURCE LEAKS                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ✗ System V IPC objects persist after process death                     │
│   ✓ Always clean up with msgctl(IPC_RMID), shmctl(IPC_RMID)             │
│   ✓ Use signal handlers for cleanup on abnormal exit                     │
│   ✓ Or use POSIX IPC with unlink-on-create pattern                       │
│                                                                            │
│                                                                            │
│   2. DEADLOCKS                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ✗ Two processes waiting for each other                                 │
│   ✗ Lock ordering violations                                              │
│                                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │   Process A          Process B                                    │  │
│   │                                                                    │  │
│   │   lock(mutex1)       lock(mutex2)                                 │  │
│   │   lock(mutex2) ─X─   lock(mutex1) ─X─    DEADLOCK!               │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   ✓ Always acquire locks in consistent order                             │
│   ✓ Use timeouts on blocking operations                                  │
│   ✓ Consider lock-free algorithms for high-performance code             │
│                                                                            │
│                                                                            │
│   3. RACE CONDITIONS                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ✗ Check-then-act without synchronization                               │
│   ✗ Multiple writers to shared memory without locks                      │
│                                                                            │
│   ✓ Use atomic operations when possible                                  │
│   ✓ Protect critical sections with semaphores/mutexes                   │
│                                                                            │
│                                                                            │
│   4. BLOCKING ISSUES                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ✗ Blocking read on pipe when writer is gone                            │
│   ✗ Blocking on full message queue                                       │
│                                                                            │
│   ✓ Use O_NONBLOCK and check for EAGAIN                                  │
│   ✓ Use select/poll/epoll for multiplexing                               │
│   ✓ Always handle EINTR (interrupted by signal)                         │
│                                                                            │
│                                                                            │
│   5. SECURITY ISSUES                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ✗ World-writable FIFOs or sockets                                      │
│   ✗ Trusting data from IPC without validation                            │
│                                                                            │
│   ✓ Set appropriate permissions (0600 or 0660)                           │
│   ✓ Verify credentials with SO_PEERCRED                                  │
│   ✓ Validate all received data                                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 14. Summary and Appendix

### Quick Reference: IPC System Calls

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIPES AND FIFOS                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int pipe(int pipefd[2]);                                                │
│   int pipe2(int pipefd[2], int flags);                                   │
│   int mkfifo(const char *pathname, mode_t mode);                         │
│   int mkfifoat(int dirfd, const char *pathname, mode_t mode);           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM V MESSAGE QUEUES                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int msgget(key_t key, int msgflg);                                     │
│   int msgsnd(int msqid, const void *msgp, size_t msgsz, int msgflg);    │
│   ssize_t msgrcv(int msqid, void *msgp, size_t msgsz,                   │
│                  long msgtyp, int msgflg);                               │
│   int msgctl(int msqid, int cmd, struct msqid_ds *buf);                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM V SEMAPHORES                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int semget(key_t key, int nsems, int semflg);                          │
│   int semop(int semid, struct sembuf *sops, size_t nsops);              │
│   int semtimedop(int semid, struct sembuf *sops, size_t nsops,          │
│                  const struct timespec *timeout);                        │
│   int semctl(int semid, int semnum, int cmd, ...);                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM V SHARED MEMORY                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int shmget(key_t key, size_t size, int shmflg);                        │
│   void *shmat(int shmid, const void *shmaddr, int shmflg);              │
│   int shmdt(const void *shmaddr);                                         │
│   int shmctl(int shmid, int cmd, struct shmid_ds *buf);                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX MESSAGE QUEUES                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   mqd_t mq_open(const char *name, int oflag, mode_t mode,               │
│                 struct mq_attr *attr);                                    │
│   int mq_send(mqd_t mqdes, const char *msg_ptr, size_t msg_len,         │
│               unsigned int msg_prio);                                     │
│   ssize_t mq_receive(mqd_t mqdes, char *msg_ptr, size_t msg_len,        │
│                      unsigned int *msg_prio);                            │
│   int mq_close(mqd_t mqdes);                                              │
│   int mq_unlink(const char *name);                                        │
│   int mq_notify(mqd_t mqdes, const struct sigevent *notification);      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX SEMAPHORES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   sem_t *sem_open(const char *name, int oflag, mode_t mode,             │
│                   unsigned int value);                                    │
│   int sem_wait(sem_t *sem);                                               │
│   int sem_trywait(sem_t *sem);                                            │
│   int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout);    │
│   int sem_post(sem_t *sem);                                               │
│   int sem_close(sem_t *sem);                                              │
│   int sem_unlink(const char *name);                                       │
│   int sem_init(sem_t *sem, int pshared, unsigned int value);            │
│   int sem_destroy(sem_t *sem);                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX SHARED MEMORY                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int shm_open(const char *name, int oflag, mode_t mode);               │
│   int shm_unlink(const char *name);                                       │
│   void *mmap(void *addr, size_t length, int prot, int flags,            │
│              int fd, off_t offset);                                       │
│   int munmap(void *addr, size_t length);                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX DOMAIN SOCKETS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int socket(AF_UNIX, int type, 0);                                      │
│   int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen); │
│   int listen(int sockfd, int backlog);                                    │
│   int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);    │
│   int connect(int sockfd, const struct sockaddr *addr, socklen_t len);  │
│   int socketpair(AF_UNIX, int type, 0, int sv[2]);                      │
│   ssize_t sendmsg(int sockfd, const struct msghdr *msg, int flags);     │
│   ssize_t recvmsg(int sockfd, struct msghdr *msg, int flags);           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    MODERN LINUX IPC                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int eventfd(unsigned int initval, int flags);                          │
│   int timerfd_create(int clockid, int flags);                            │
│   int timerfd_settime(int fd, int flags,                                 │
│                       const struct itimerspec *new, struct itimerspec *old);│
│   int signalfd(int fd, const sigset_t *mask, int flags);                │
│   int memfd_create(const char *name, unsigned int flags);               │
│   int pidfd_open(pid_t pid, unsigned int flags);                         │
│   int pidfd_send_signal(int pidfd, int sig, siginfo_t *info, int flags);│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    SIGNALS                                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   int kill(pid_t pid, int sig);                                           │
│   int raise(int sig);                                                      │
│   int sigqueue(pid_t pid, int sig, const union sigval value);           │
│   int sigaction(int signum, const struct sigaction *act,                 │
│                 struct sigaction *oldact);                                │
│   int sigprocmask(int how, const sigset_t *set, sigset_t *oldset);      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                    INTERPROCESS COMMUNICATION                              │
│                        THE BIG PICTURE                                     │
│                                                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         PROCESS A                                   │ │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │ │
│   │  │ User    │  │ File    │  │ Signal  │  │ Memory  │  │ Socket  │  │ │
│   │  │ Code    │  │ Desc    │  │ Handlers│  │ Regions │  │ Buffers │  │ │
│   │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │ │
│   └───────┼────────────┼───────────┼────────────┼────────────┼────────┘ │
│           │            │           │            │            │           │
│   ════════╪════════════╪═══════════╪════════════╪════════════╪═══════════│
│           │            │           │            │            │           │
│   ┌───────▼────────────▼───────────▼────────────▼────────────▼─────────┐ │
│   │                                                                     │ │
│   │                         KERNEL SPACE                               │ │
│   │                                                                     │ │
│   │  ┌──────────────────────────────────────────────────────────────┐  │ │
│   │  │                    IPC MECHANISMS                            │  │ │
│   │  │                                                              │  │ │
│   │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │  │ │
│   │  │  │   PIPES    │  │   FIFOS    │  │   MESSAGE QUEUES       │ │  │ │
│   │  │  │            │  │            │  │   (SysV & POSIX)       │ │  │ │
│   │  │  │ pipe_buf   │  │ pipe_buf   │  │   msg_queue            │ │  │ │
│   │  │  │ [______]   │  │ [______]   │  │   [msg][msg][msg]     │ │  │ │
│   │  │  └────────────┘  └────────────┘  └────────────────────────┘ │  │ │
│   │  │                                                              │  │ │
│   │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │  │ │
│   │  │  │ SEMAPHORES │  │  SHARED    │  │   UNIX DOMAIN          │ │  │ │
│   │  │  │            │  │  MEMORY    │  │   SOCKETS              │ │  │ │
│   │  │  │ sem_array  │  │            │  │                        │ │  │ │
│   │  │  │ [3][1][0]  │  │ ┌────────┐ │  │  sock_buf ──────────── │ │  │ │
│   │  │  └────────────┘  │ │ Pages  │ │  │  ┌──────┐    ┌──────┐ │ │  │ │
│   │  │                  │ │ ██████ │ │  │  │Server│◄──►│Client│ │ │  │ │
│   │  │                  │ └────────┘ │  │  └──────┘    └──────┘ │ │  │ │
│   │  │                  └────────────┘  └────────────────────────┘ │  │ │
│   │  │                                                              │  │ │
│   │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │  │ │
│   │  │  │  SIGNALS   │  │  EVENTFD   │  │   TIMERFD/SIGNALFD     │ │  │ │
│   │  │  │            │  │            │  │                        │ │  │ │
│   │  │  │ sig_pending│  │ counter=3  │  │  timer_spec            │ │  │ │
│   │  │  │ [SIGUSR1]  │  │ [   3   ]  │  │  [1sec|repeat]        │ │  │ │
│   │  │  └────────────┘  └────────────┘  └────────────────────────┘ │  │ │
│   │  │                                                              │  │ │
│   │  └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│           │            │           │            │            │           │
│   ════════╪════════════╪═══════════╪════════════╪════════════╪═══════════│
│           │            │           │            │            │           │
│   ┌───────▼────────────▼───────────▼────────────▼────────────▼─────────┐ │
│   │                         PROCESS B                                   │ │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │ │
│   │  │ User    │  │ File    │  │ Signal  │  │ Memory  │  │ Socket  │  │ │
│   │  │ Code    │  │ Desc    │  │ Handlers│  │ Regions │  │ Buffers │  │ │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   KEY INSIGHT:                                                             │
│   ──────────────────────────────────────────────────────────────────────  │
│                                                                            │
│   All IPC mechanisms involve the kernel as an intermediary, except       │
│   shared memory (after initial setup). The kernel provides:              │
│                                                                            │
│   • Protection - processes cannot access each other's memory directly    │
│   • Synchronization - blocking operations, atomicity guarantees          │
│   • Naming - ftok keys, filesystem paths, abstract socket names         │
│   • Buffering - kernel buffers decouple sender and receiver timing      │
│                                                                            │
│   Shared memory is unique: after mmap(), processes share pages directly, │
│   bypassing the kernel for data transfer. But synchronization still      │
│   requires kernel help (semaphores, futex) or careful lock-free coding. │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```


### IPC Evolution Timeline

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IPC EVOLUTION TIMELINE                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1971  ──┬── First Edition Unix                                          │
│           │   • Pipes introduced                                          │
│           │                                                                │
│   1974  ──┼── Fifth Edition Unix                                          │
│           │   • Signals added (basic form)                                │
│           │                                                                │
│   1979  ──┼── Seventh Edition Unix                                        │
│           │   • FIFOs (named pipes)                                       │
│           │                                                                │
│   1983  ──┼── System V                                                     │
│           │   • Message Queues                                            │
│           │   • Semaphores                                                │
│           │   • Shared Memory                                             │
│           │                                                                │
│   1983  ──┼── 4.2BSD                                                       │
│           │   • Unix Domain Sockets                                       │
│           │                                                                │
│   1988  ──┼── POSIX.1                                                      │
│           │   • Standardized signals                                      │
│           │                                                                │
│   1993  ──┼── POSIX.1b (Real-time extensions)                             │
│           │   • POSIX Message Queues                                      │
│           │   • POSIX Semaphores                                          │
│           │   • POSIX Shared Memory                                       │
│           │   • Real-time Signals                                         │
│           │                                                                │
│   2002  ──┼── Linux 2.6                                                    │
│           │   • eventfd                                                   │
│           │   • timerfd                                                   │
│           │   • signalfd                                                  │
│           │                                                                │
│   2014  ──┼── Linux 3.17                                                   │
│           │   • memfd_create                                              │
│           │                                                                │
│   2019  ──┼── Linux 5.3                                                    │
│           │   • pidfd                                                     │
│           │                                                                │
│   Future ─┴── io_uring for async IPC?                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



---

## 15. References

### Books

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ESSENTIAL READING                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Maurice J. Bach                                                          │
│   "The Design of the UNIX Operating System"                               │
│   Prentice Hall, 1986                                                      │
│   - Chapter 11: Interprocess Communication                                │
│   - Classic description of System V IPC                                   │
│                                                                            │
│   W. Richard Stevens, Stephen A. Rago                                     │
│   "Advanced Programming in the UNIX Environment" (3rd Ed)                │
│   Addison-Wesley, 2013                                                     │
│   - Chapter 14: Advanced I/O                                              │
│   - Chapter 15: Interprocess Communication                                │
│   - Chapter 17: Advanced IPC                                              │
│                                                                            │
│   Michael Kerrisk                                                          │
│   "The Linux Programming Interface"                                       │
│   No Starch Press, 2010                                                    │
│   - Part VI: Interprocess Communication (Chapters 43-57)                 │
│   - The definitive Linux IPC reference                                    │
│                                                                            │
│   Robert Love                                                              │
│   "Linux Kernel Development" (3rd Ed)                                     │
│   Addison-Wesley, 2010                                                     │
│   - Chapter 19: Portability                                               │
│   - Kernel-level IPC implementation details                               │
│                                                                            │
│   Daniel P. Bovet, Marco Cesati                                           │
│   "Understanding the Linux Kernel" (3rd Ed)                               │
│   O'Reilly, 2005                                                           │
│   - Chapter 19: Process Communication                                     │
│   - Deep dive into kernel data structures                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Source Files

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX KERNEL SOURCE                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Pipes:                                                                   │
│   • fs/pipe.c                    - Pipe implementation                    │
│   • include/linux/pipe_fs_i.h    - struct pipe_inode_info                │
│                                                                            │
│   System V IPC:                                                            │
│   • ipc/msg.c                    - Message queues                         │
│   • ipc/sem.c                    - Semaphores                             │
│   • ipc/shm.c                    - Shared memory                          │
│   • ipc/util.c                   - Common IPC utilities                   │
│   • include/linux/ipc.h          - IPC structures                         │
│                                                                            │
│   POSIX IPC:                                                               │
│   • ipc/mqueue.c                 - POSIX message queues                   │
│   • kernel/futex.c               - Futex (POSIX sem basis)               │
│                                                                            │
│   Unix Domain Sockets:                                                     │
│   • net/unix/af_unix.c           - Unix socket implementation            │
│   • net/unix/garbage.c           - Socket garbage collection             │
│   • include/net/af_unix.h        - Unix socket structures                │
│                                                                            │
│   Signals:                                                                 │
│   • kernel/signal.c              - Signal implementation                  │
│   • include/linux/signal.h       - Signal definitions                    │
│                                                                            │
│   Modern IPC:                                                              │
│   • fs/eventfd.c                 - eventfd                                │
│   • fs/timerfd.c                 - timerfd                                │
│   • fs/signalfd.c                - signalfd                               │
│   • mm/memfd.c                   - memfd_create                           │
│   • kernel/pid.c                 - pidfd                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Man Pages

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MANUAL PAGES                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Section 2 (System Calls):                                                │
│   • pipe(2), pipe2(2)            • msgget(2), msgsnd(2), msgrcv(2)       │
│   • mkfifo(2)                    • semget(2), semop(2), semctl(2)        │
│   • shmget(2), shmat(2)          • kill(2), sigaction(2)                 │
│   • socket(2), socketpair(2)     • eventfd(2), timerfd_create(2)         │
│   • signalfd(2)                  • memfd_create(2), pidfd_open(2)        │
│   • mmap(2), munmap(2)           • mq_open(2), mq_send(2)                │
│                                                                            │
│   Section 3 (Library Functions):                                           │
│   • sem_open(3), sem_wait(3)     • shm_open(3), shm_unlink(3)            │
│   • mq_receive(3), mq_notify(3)  • ftok(3)                               │
│                                                                            │
│   Section 7 (Miscellaneous):                                               │
│   • pipe(7)                      - Overview of pipes and FIFOs            │
│   • unix(7)                      - Unix domain sockets                    │
│   • signal(7)                    - Signal overview                        │
│   • mq_overview(7)               - POSIX message queue overview          │
│   • sem_overview(7)              - POSIX semaphore overview              │
│   • shm_overview(7)              - POSIX shared memory overview          │
│   • svipc(7)                     - System V IPC overview                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Online Resources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ONLINE RESOURCES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Linux Kernel Documentation:                                              │
│   • https://www.kernel.org/doc/html/latest/                              │
│                                                                            │
│   LWN.net Articles:                                                        │
│   • "eventfd" - https://lwn.net/Articles/267331/                         │
│   • "timerfd" - https://lwn.net/Articles/245533/                         │
│   • "signalfd" - https://lwn.net/Articles/225714/                        │
│   • "memfd_create" - https://lwn.net/Articles/607627/                    │
│   • "pidfd" - https://lwn.net/Articles/794707/                           │
│                                                                            │
│   Beej's Guide to Unix IPC:                                                │
│   • https://beej.us/guide/bgipc/                                          │
│   • Excellent practical introduction to IPC                               │
│                                                                            │
│   The Linux Kernel Module Programming Guide:                               │
│   • https://sysprog21.github.io/lkmpg/                                   │
│                                                                            │
│   man7.org (Michael Kerrisk):                                              │
│   • https://man7.org/linux/man-pages/                                     │
│   • Comprehensive Linux man pages                                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

*This document is part of the Unix Kernel Internals series, written in the style of Maurice J. Bach's "The 
Design of the UNIX Operating System".*

