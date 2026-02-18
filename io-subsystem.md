# The I/O Subsystem

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Buffer Cache, Block and Character Devices, Device Drivers, Disk I/O, and Modern I/O

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [What is the I/O Subsystem?](#what-is-the-io-subsystem)
   - [The Kernel I/O Architecture](#the-kernel-io-architecture)
   - [Historical Context](#historical-context)

2. [The Buffer Cache](#2-the-buffer-cache)
   - [Why a Buffer Cache?](#why-a-buffer-cache)
   - [Buffer Headers](#buffer-headers)
   - [Structure of the Buffer Pool](#structure-of-the-buffer-pool)
   - [Buffer Lookup Algorithm](#buffer-lookup-algorithm)
   - [Reading and Writing Disk Blocks](#reading-and-writing-disk-blocks)
   - [Buffer Cache Scenarios](#buffer-cache-scenarios)

3. [Block Devices](#3-block-devices)
   - [What are Block Devices?](#what-are-block-devices)
   - [The Block Device Interface](#the-block-device-interface)
   - [Device Numbers: Major and Minor](#device-numbers-major-and-minor)
   - [The bdevsw Table](#the-bdevsw-table)

4. [Character Devices](#4-character-devices)
   - [What are Character Devices?](#what-are-character-devices)
   - [The Character Device Interface](#the-character-device-interface)
   - [The cdevsw Table](#the-cdevsw-table)
   - [Raw Device Access](#raw-device-access)

5. [Device Drivers](#5-device-drivers)
   - [Driver Architecture](#driver-architecture)
   - [Top Half vs Bottom Half](#top-half-vs-bottom-half)
   - [Interrupt Handling](#interrupt-handling)
   - [Driver Entry Points](#driver-entry-points)
   - [Modern Linux Driver Model](#modern-linux-driver-model)

6. [Terminal I/O](#6-terminal-io)
   - [Terminal Drivers and Line Disciplines](#terminal-drivers-and-line-disciplines)
   - [Canonical vs Non-Canonical Mode](#canonical-vs-non-canonical-mode)
   - [The termios Structure](#the-termios-structure)
   - [Pseudo-Terminals (PTY)](#pseudo-terminals-pty)

7. [Disk I/O](#7-disk-io)
   - [Disk Structure and Geometry](#disk-structure-and-geometry)
   - [I/O Request Flow](#io-request-flow)
   - [I/O Scheduling Algorithms](#io-scheduling-algorithms)
   - [The Linux Block Layer](#the-linux-block-layer)

8. [Direct Memory Access (DMA)](#8-direct-memory-access-dma)
   - [What is DMA?](#what-is-dma)
   - [DMA Operations](#dma-operations)
   - [Scatter-Gather DMA](#scatter-gather-dma)
   - [DMA Mapping](#dma-mapping)

9. [The VFS and I/O](#9-the-vfs-and-io)
   - [Virtual File System Layer](#virtual-file-system-layer)
   - [File Operations Structure](#file-operations-structure)
   - [Address Space Operations](#address-space-operations)
   - [Page Cache Integration](#page-cache-integration)

10. [I/O System Calls](#10-io-system-calls)
    - [read() and write()](#read-and-write)
    - [Vectored I/O: readv() and writev()](#vectored-io-readv-and-writev)
    - [Positioned I/O: pread() and pwrite()](#positioned-io-pread-and-pwrite)
    - [Asynchronous I/O: aio\_\*](#asynchronous-io-aio)

11. [Modern Linux I/O](#11-modern-linux-io)
    - [The io_uring Interface](#the-io_uring-interface)
    - [Direct I/O (O_DIRECT)](#direct-io-o_direct)
    - [Memory-Mapped I/O](#memory-mapped-io)
    - [Splice and Tee](#splice-and-tee)
    - [Copy File Range](#copy-file-range)

12. [Summary and Appendix](#12-summary-and-appendix)
    - [I/O System Calls Quick Reference](#io-system-calls-quick-reference)
    - [The Big Picture](#the-big-picture)

13. [References](#13-references)

---

## 1. Introduction

### What is the I/O Subsystem?

The I/O subsystem is the kernel's interface between processes and hardware devices. It provides a uniform
abstraction that allows programs to interact with diverse hardware—disks, terminals, networks, and
more—through a consistent set of system calls.

Maurice Bach describes the I/O subsystem:

> "The kernel provides a uniform interface for all I/O operations, hiding the peculiarities of individual
> devices from user processes."

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE I/O SUBSYSTEM OVERVIEW                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     USER PROCESSES                                   │ │
│   │                                                                      │ │
│   │    read()   write()   open()   close()   ioctl()   mmap()          │ │
│   │      │        │         │        │         │         │              │ │
│   └──────┼────────┼─────────┼────────┼─────────┼─────────┼──────────────┘ │
│          │        │         │        │         │         │                │
│          └────────┴─────────┴────────┴─────────┴─────────┘                │
│                              │                                             │
│                              ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                SYSTEM CALL INTERFACE                                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                              │                                             │
│                              ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │                VIRTUAL FILE SYSTEM (VFS)                            │ │
│   │                                                                      │ │
│   │    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │ │
│   │    │   Regular    │  │  Directory   │  │   Device     │            │ │
│   │    │    Files     │  │   Files      │  │   Files      │            │ │
│   │    └──────┬───────┘  └──────────────┘  └──────┬───────┘            │ │
│   │           │                                    │                    │ │
│   └───────────┼────────────────────────────────────┼────────────────────┘ │
│               │                                    │                      │
│               ▼                                    ▼                      │
│   ┌───────────────────────┐            ┌────────────────────────────────┐│
│   │                       │            │                                 ││
│   │  FILE SYSTEMS         │            │    DEVICE SWITCH TABLES        ││
│   │  (ext4, xfs, etc.)    │            │    (bdevsw / cdevsw)           ││
│   │                       │            │                                 ││
│   └───────────┬───────────┘            └─────────────┬──────────────────┘│
│               │                                      │                    │
│               ▼                                      ▼                    │
│   ┌───────────────────────┐            ┌────────────────────────────────┐│
│   │                       │            │                                 ││
│   │    BUFFER CACHE /     │            │     DEVICE DRIVERS             ││
│   │    PAGE CACHE         │            │     (Block & Character)        ││
│   │                       │            │                                 ││
│   └───────────┬───────────┘            └─────────────┬──────────────────┘│
│               │                                      │                    │

```

### The Kernel I/O Architecture

The Unix I/O architecture is built on several fundamental principles:

```

┌───────────────────────────────────────────────────────────────────────────┐
│                    FUNDAMENTAL I/O PRINCIPLES                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. EVERYTHING IS A FILE                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│      Unix treats devices as files:                                         │
│                                                                            │
│      /dev/sda        ─► Block device (disk)                               │
│      /dev/tty0       ─► Character device (terminal)                       │
│      /dev/null       ─► Special device (data sink)                        │
│      /dev/zero       ─► Special device (zero source)                      │
│      /dev/random     ─► Special device (random data)                      │
│                                                                            │
│      This allows: cat file > /dev/lp0    (print file)                     │
│                   dd if=/dev/sda of=disk.img  (copy disk)                 │
│                                                                            │
│                                                                            │
│   2. UNIFORM SYSTEM CALL INTERFACE                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│      ┌───────────┬──────────────────────────────────────────────────┐     │
│      │ System    │                                                   │     │
│      │ Call      │  Works on...                                      │     │
│      ├───────────┼──────────────────────────────────────────────────┤     │
│      │ open()    │  Files, devices, pipes, sockets                  │     │
│      │ read()    │  Files, devices, pipes, sockets                  │     │
│      │ write()   │  Files, devices, pipes, sockets                  │     │
│      │ close()   │  Files, devices, pipes, sockets                  │     │
│      │ ioctl()   │  Devices (device-specific operations)            │     │
│      └───────────┴──────────────────────────────────────────────────┘     │
│                                                                            │
│                                                                            │
│   3. BLOCK VS CHARACTER DEVICES                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│      ┌─────────────────────────┬───────────────────────────────────┐      │
│      │    BLOCK DEVICES        │    CHARACTER DEVICES               │      │
│      ├─────────────────────────┼───────────────────────────────────┤      │
│      │ Fixed-size blocks       │ Byte stream                        │      │
│      │ Random access           │ Sequential access (usually)        │      │
│      │ Uses buffer cache       │ No buffer cache                    │      │
│      │ Examples:               │ Examples:                          │      │
│      │   - Hard disks          │   - Terminals                      │      │
│      │   - SSDs                │   - Serial ports                   │      │
│      │   - CD-ROMs             │   - Mice                           │      │
│      │   - USB drives          │   - Printers                       │      │
│      └─────────────────────────┴───────────────────────────────────┘      │
│                                                                            │
│                                                                            │
│   4. THE FILE DESCRIPTOR ABSTRACTION                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│      ┌─────────────────────────────────────────────────────────────┐      │
│      │ Process                                                      │      │
│      │ ┌─────────────────┐                                         │      │
│      │ │ File Descriptor │     ┌──────────────────┐                │      │
│      │ │ Table           │     │ System File Table│                │      │
│      │ ├────┬────────────┤     ├──────────────────┤                │      │
│      │ │ 0  │ ──────────────►  │ stdin (tty)      │                │      │
│      │ │ 1  │ ──────────────►  │ stdout (tty)     │                │      │
│      │ │ 2  │ ──────────────►  │ stderr (tty)     │                │      │
│      │ │ 3  │ ──────────────►  │ /home/user/file  │                │      │
│      │ │ 4  │ ──────────────►  │ /dev/sda1        │                │      │
│      │ │ 5  │ ──────────────►  │ socket           │                │      │
│      │ └────┴────────────┘     └──────────────────┘                │      │
│      └─────────────────────────────────────────────────────────────┘      │
│                                                                            │
│      File descriptors are small integers that index into the              │
│      process's file descriptor table.                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    I/O SUBSYSTEM EVOLUTION                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1970s: EARLY UNIX                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Simple buffer cache (hash + free list)                           │ │
│   │  • Block devices: disk drives                                        │ │
│   │  • Character devices: teletypes (TTY)                               │ │
│   │  • Device switch tables (bdevsw, cdevsw)                            │ │
│   │  • Synchronous I/O only                                              │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   1980s: SYSTEM V AND BSD                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Larger buffer cache                                               │ │
│   │  • STREAMS framework (System V)                                      │ │
│   │  • BSD socket interface                                              │ │
│   │  • Raw device access                                                 │ │
│   │  • Scatter-gather I/O (readv/writev)                                │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   1990s: LINUX AND MODERN UNIX                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Unified page cache (replacing buffer cache for files)            │ │
│   │  • VFS (Virtual File System) layer                                  │ │
│   │  • PCI bus and advanced device models                               │ │
│   │  • POSIX AIO (asynchronous I/O)                                     │ │
│   │  • Direct I/O (O_DIRECT)                                            │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   2000s: HIGH-PERFORMANCE I/O                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • Block layer rewrite (bio structure)                              │ │
│   │  • Multiple I/O schedulers (CFQ, deadline, noop)                    │ │
│   │  • Splice and sendfile for zero-copy I/O                            │ │
│   │  • epoll for scalable I/O multiplexing                              │ │
│   │  • Native Command Queuing (NCQ) for SATA                            │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   2010s-Present: MODERN I/O                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  • io_uring (2019): High-performance async I/O                      │ │
│   │  • NVMe and multi-queue block layer                                 │ │
│   │  • BPF for programmable I/O filtering                               │ │
│   │  • Memory-mapped I/O (DAX) for persistent memory                    │ │
│   │  • Kernel bypass for high-frequency trading                         │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

The original Unix I/O subsystem, as described by Maurice Bach, was elegant in its simplicity. Modern systems
have added layers of complexity to handle the performance demands of SSDs, NVMe devices, and high-speed
networks, but the fundamental abstractions remain remarkably similar.

---

## 2. The Buffer Cache

### Why a Buffer Cache?

The buffer cache is one of the most important concepts in traditional Unix I/O. It serves as an intermediary
between the file system and disk devices, caching disk blocks in memory to improve performance.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE NEED FOR A BUFFER CACHE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM: DISK IS SLOW                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │                                                                    │   │
│   │   Access Times:                                                    │   │
│   │                                                                    │   │
│   │   CPU Register     :  < 1 nanosecond                              │   │
│   │   L1 Cache         :  ~ 1 nanosecond                              │   │
│   │   L2 Cache         :  ~ 4 nanoseconds                             │   │
│   │   L3 Cache         :  ~ 10 nanoseconds                            │   │
│   │   Main Memory      :  ~ 100 nanoseconds                           │   │
│   │   SSD              :  ~ 100 microseconds (100,000 ns)             │   │
│   │   Hard Disk        :  ~ 10 milliseconds (10,000,000 ns)           │   │
│   │                                                                    │   │
│   │   Disk is 100,000x slower than memory!                            │   │
│   │                                                                    │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   THE SOLUTION: BUFFER CACHE                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────┐                        ┌────────────────┐            │
│   │                │                        │                │            │
│   │   Process      │   read block 100      │   Process      │            │
│   │   (First       │ ──────────────────►   │   (Second      │            │
│   │   Access)      │   FROM DISK: 10ms     │   Access)      │            │
│   │                │                        │                │            │
│   └────────────────┘                        └────────────────┘            │
│          │                                         │                      │
│          │                                         │ read block 100       │
│          ▼                                         ▼ FROM CACHE: 100ns    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         BUFFER CACHE                                 │ │
│   │                                                                      │ │
│   │    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │ │
│   │    │ Block   │ │ Block   │ │ Block   │ │ Block   │ │ Block   │     │ │
│   │    │   42    │ │   100   │ │   256   │ │   99    │ │   500   │     │ │
│   │    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                           │                                               │
│                           ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         DISK DRIVE                                   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   BENEFITS OF THE BUFFER CACHE:                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   1. Read Caching     - Recently read blocks stay in memory               │
│   2. Write Buffering  - Writes go to cache, disk I/O batched later       │
│   3. Request Coalescing - Multiple small writes become one large write   │
│   4. Uniform Interface - File system doesn't deal with device details    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffer Headers

In traditional Unix, each buffer in the cache has a header (struct buf) that describes the buffer:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE BUFFER HEADER (struct buf)                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct buf {                                                             │
│       int         b_flags;      /* Status flags                         */│
│       struct buf *b_forw;       /* Hash chain forward pointer           */│
│       struct buf *b_back;       /* Hash chain backward pointer          */│
│       struct buf *av_forw;      /* Free list forward pointer            */│
│       struct buf *av_back;      /* Free list backward pointer           */│
│       dev_t       b_dev;        /* Device number                        */│
│       daddr_t     b_blkno;      /* Block number on device               */│
│       char       *b_addr;       /* Address of data buffer               */│
│       unsigned    b_bcount;     /* Size of I/O request                  */│
│       int         b_error;      /* Error code (if B_ERROR)              */│
│       void      (*b_iodone)();  /* Callback when I/O completes          */│
│   };                                                                       │
│                                                                            │
│                                                                            │
│   BUFFER FLAGS (b_flags):                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────┬────────────────────────────────────────────────────┐     │
│   │ Flag       │ Meaning                                             │     │
│   ├────────────┼────────────────────────────────────────────────────┤     │
│   │ B_WRITE    │ Write operation (0 = read)                         │     │
│   │ B_READ     │ Read operation                                      │     │
│   │ B_DONE     │ I/O completed                                       │     │
│   │ B_ERROR    │ Error occurred during I/O                          │     │
│   │ B_BUSY     │ Buffer is locked, not on free list                 │     │
│   │ B_PHYS     │ Physical (raw) I/O                                  │     │
│   │ B_WANTED   │ Process waiting for buffer to become free          │     │
│   │ B_ASYNC    │ Don't wait for I/O completion                      │     │
│   │ B_DELWRI   │ Delayed write - write on reassignment              │     │
│   │ B_STALE    │ Contents no longer valid                           │     │
│   └────────────┴────────────────────────────────────────────────────┘     │
│                                                                            │
│                                                                            │
│   BUFFER STRUCTURE IN MEMORY:                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Buffer Header (struct buf)         Data Area                      │ │
│   │   ┌──────────────────────────┐      ┌──────────────────────────┐   │ │
│   │   │ b_flags: B_DONE          │      │                          │   │ │
│   │   │ b_dev: 8,1               │      │   Block of data from     │   │ │
│   │   │ b_blkno: 12345           │─────►│   disk (512-8192 bytes)  │   │ │
│   │   │ b_addr: 0xffff8000       │      │                          │   │ │
│   │   │ b_bcount: 4096           │      │                          │   │ │
│   │   │ b_forw: ...              │      └──────────────────────────┘   │ │
│   │   │ b_back: ...              │                                      │ │
│   │   └──────────────────────────┘                                      │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Structure of the Buffer Pool

The buffer cache is organized using two data structures:

1. **Hash Queues** - For fast lookup of buffers by (device, block number)
2. **Free List** - LRU list of buffers available for reuse

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BUFFER CACHE ORGANIZATION                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   HASH QUEUES (for fast lookup by device + block number):                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Hash function: hash = (device_number + block_number) % NHASH            │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   bufhash[0] ◄──► [buf] ◄──► [buf] ◄──► [buf]                     │  │
│   │                                                                     │  │
│   │   bufhash[1] ◄──► [buf] ◄──► [buf]                                 │  │
│   │                                                                     │  │
│   │   bufhash[2] ◄──► [buf] ◄──► [buf] ◄──► [buf] ◄──► [buf]         │  │
│   │                                                                     │  │
│   │   bufhash[3] ◄──► [buf]                                            │  │
│   │                                                                     │  │
│   │      ...                                                            │  │
│   │                                                                     │  │
│   │   bufhash[NHASH-1] ◄──► [buf] ◄──► [buf]                          │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   Each hash chain is a doubly-linked list (b_forw, b_back pointers)       │
│                                                                            │
│                                                                            │
│   FREE LIST (LRU order for buffer reuse):                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   bfreelist                                                         │  │
│   │       │                                                             │  │
│   │       ▼                                                             │  │
│   │   ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐  │  │
│   │   │ buf A │◄──►│ buf B │◄──►│ buf C │◄──►│ buf D │◄──►│ buf E │  │  │
│   │   └───────┘    └───────┘    └───────┘    └───────┘    └───────┘  │  │
│   │       ▲                                                     │      │  │
│   │       │                                                     │      │  │
│   │       └─────────────────────────────────────────────────────┘      │  │
│   │                                                                     │  │
│   │   HEAD (LRU)                                           TAIL (MRU)   │  │
│   │   Least recently                                       Most recently│  │
│   │   used - reuse                                         used - keep  │  │
│   │   first                                                             │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   Each buffer is on BOTH a hash chain AND the free list (unless busy)    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffer Lookup Algorithm

The getblk() algorithm is the heart of the buffer cache. It retrieves a buffer for a given device and block
number:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ALGORITHM: getblk()                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm getblk                                                         │
│   input:  device number                                                    │
│           block number                                                     │
│   output: locked buffer                                                    │
│   {                                                                        │
│       while (buffer not found)                                             │
│       {                                                                    │
│           if (block in hash queue)                          /* SCENARIO 1 */
│           {                                                                │
│               if (buffer busy)                              /* SCENARIO 5 */
│               {                                                            │
│                   set B_WANTED flag;                                       │
│                   sleep(event buffer becomes free);                        │
│                   continue;  /* start again */                             │
│               }                                                            │
│               mark buffer busy;                                            │
│               remove from free list;                                       │
│               return buffer;                                               │
│           }                                                                │
│           else  /* block not in cache */                                  │
│           {                                                                │
│               if (free list empty)                          /* SCENARIO 4 */
│               {                                                            │
│                   sleep(event any buffer becomes free);                    │
│                   continue;                                                │
│               }                                                            │
│               remove buffer from head of free list;                        │
│               if (buffer marked delayed write)              /* SCENARIO 3 */
│               {                                                            │
│                   asynchronous write buffer to disk;                       │
│                   continue;                                                │
│               }                                                            │
│               /* SCENARIO 2 */                                             │
│               remove buffer from old hash queue;                           │
│               put buffer on new hash queue;                                │
│               mark buffer busy;                                            │
│               return buffer;                                               │
│           }                                                                │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffer Cache Scenarios

Maurice Bach describes five scenarios that can occur when searching for a buffer:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE FIVE SCENARIOS OF getblk()                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO 1: Block is in cache and buffer is free                        │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┐                                                     │
│   │ getblk(dev, 100)│                                                     │
│   └────────┬────────┘                                                     │
│            │                                                               │
│            ▼ Search hash queue                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Hash queue: ... ◄──► [buf 100] ◄──► ...                           │  │
│   │                        NOT BUSY                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│            │                                                               │
│            ▼ Found! Mark busy, remove from free list                      │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Return buffer immediately - BEST CASE (no disk I/O)               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   SCENARIO 2: Block not in cache, free buffer available                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┐                                                     │
│   │ getblk(dev, 200)│                                                     │
│   └────────┬────────┘                                                     │
│            │                                                               │
│            ▼ Not in hash queue                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Free list: [buf A] ◄──► [buf B] ◄──► [buf C] ◄──► ...             │  │
│   │              ▲                                                      │  │
│   │              └── Take this one (LRU)                                │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│            │                                                               │
│            ▼ Reassign buffer to new block                                 │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Move buf A from old hash queue to new hash queue                  │  │
│   │ Return buffer (will need to read data from disk)                  │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   SCENARIO 3: Block not in cache, buffer has delayed write               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┐                                                     │
│   │ getblk(dev, 300)│                                                     │
│   └────────┬────────┘                                                     │
│            │                                                               │
│            ▼ Not in hash queue                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Free list: [buf X] ◄──► ...                                        │  │
│   │             B_DELWRI                                                │  │
│   │              ▲                                                      │  │
│   │              └── This buffer has modified data!                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│            │                                                               │
│            ▼ Must write to disk first                                     │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Start async write of buf X                                         │  │
│   │ Continue searching free list (loop back)                          │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   SCENARIO 4: Block not in cache, no free buffers                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┐                                                     │
│   │ getblk(dev, 400)│                                                     │
│   └────────┬────────┘                                                     │
│            │                                                               │
│            ▼ Not in hash queue                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Free list: (empty)                                                  │  │
│   │                                                                     │  │
│   │ All buffers are busy!                                               │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│            │                                                               │
│            ▼ Must wait                                                    │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ sleep(event: any buffer becomes free)                              │  │
│   │ When woken, start over from beginning                              │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   SCENARIO 5: Block in cache but buffer is busy                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┐                                                     │
│   │ getblk(dev, 500)│                                                     │
│   └────────┬────────┘                                                     │
│            │                                                               │
│            ▼ Found in hash queue                                          │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Hash queue: ... ◄──► [buf 500] ◄──► ...                           │  │
│   │                        B_BUSY (another process using it)           │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│            │                                                               │
│            ▼ Must wait for specific buffer                                │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Set B_WANTED on buffer                                             │  │
│   │ sleep(event: this buffer becomes free)                             │  │
│   │ When woken, start over (buffer may have moved!)                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Reading and Writing Disk Blocks

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ALGORITHM: bread() - Block Read                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm bread                                                          │
│   input:  device number                                                    │
│           block number                                                     │
│   output: buffer containing data                                           │
│   {                                                                        │
│       buffer = getblk(device, block);                                      │
│       if (buffer data valid)      /* B_DONE set */                        │
│           return buffer;          /* data already in cache */             │
│                                                                            │
│       /* Data not in cache - must read from disk */                       │
│       initiate disk read;                                                  │
│       sleep(event: I/O complete);                                          │
│       return buffer;                                                       │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   BREAD FLOW:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│   │ bread()  │───►│ getblk() │───►│ Data in  │───►│ Return   │           │
│   │          │    │          │    │ cache?   │ Y  │ buffer   │           │
│   └──────────┘    └──────────┘    └─────┬────┘    └──────────┘           │
│                                         │ N                               │
│                                         ▼                                 │
│                                   ┌──────────┐                            │
│                                   │ Start    │                            │
│                                   │ disk I/O │                            │
│                                   └─────┬────┘                            │
│                                         │                                 │
│                                         ▼                                 │
│                                   ┌──────────┐                            │
│                                   │ sleep()  │                            │
│                                   │ (wait)   │                            │
│                                   └─────┬────┘                            │
│                                         │ interrupt                       │
│                                         ▼                                 │
│                                   ┌──────────┐                            │
│                                   │ Return   │                            │
│                                   │ buffer   │                            │
│                                   └──────────┘                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ALGORITHM: bwrite() - Block Write                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   algorithm bwrite                                                         │
│   input:  buffer                                                           │
│   output: none                                                             │
│   {                                                                        │
│       initiate disk write;                                                 │
│       if (I/O synchronous)                                                 │
│       {                                                                    │
│           sleep(event: I/O complete);                                      │
│           release buffer;                                                  │
│       }                                                                    │
│       else if (buffer marked delayed write)                                │
│       {                                                                    │
│           mark buffer B_ASYNC;                                             │
│           /* interrupt handler will release buffer */                     │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│                                                                            │
│   TYPES OF WRITE:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   SYNCHRONOUS WRITE:                                                 │ │
│   │   ───────────────────────────────────────────────────────────────   │ │
│   │   Process waits for write to complete                               │ │
│   │   Used for: metadata, critical data                                 │ │
│   │                                                                      │ │
│   │   Process ──► write ──► sleep ──► [disk I/O] ──► wake ──► continue  │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   ASYNCHRONOUS WRITE:                                                │ │
│   │   ───────────────────────────────────────────────────────────────   │ │
│   │   Process continues immediately                                      │ │
│   │   Interrupt handler releases buffer                                  │ │
│   │                                                                      │ │
│   │   Process ──► write ──► continue immediately                        │ │
│   │                   └───────► [disk I/O] ──► interrupt ──► release    │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   DELAYED WRITE:                                                     │ │
│   │   ───────────────────────────────────────────────────────────────   │ │
│   │   Data marked dirty, written later                                   │ │
│   │   Most efficient for frequently modified data                       │ │
│   │                                                                      │ │
│   │   Process ──► mark B_DELWRI ──► continue                            │ │
│   │                     └───────► [written when buffer reused or sync]  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Modern Linux: Page Cache vs Buffer Cache

In modern Linux, the traditional buffer cache has been largely replaced by the page cache for file data.
However, the buffer cache concept still exists for block device metadata:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION: BUFFER CACHE TO PAGE CACHE                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TRADITIONAL UNIX (Bach Era):                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌──────────┐                                                            │
│   │ Process  │                                                            │
│   └────┬─────┘                                                            │
│        │ read()                                                           │
│        ▼                                                                  │
│   ┌──────────┐    ┌──────────────────────────────────────────────┐       │
│   │   VFS    │───►│              BUFFER CACHE                     │       │
│   └──────────┘    │  (device, block) → buffer                     │       │
│                   │  Fixed-size blocks (512-8192 bytes)           │       │
│                   └──────────────────────┬───────────────────────┘       │
│                                          │                                │
│                                          ▼                                │
│                                   ┌──────────┐                            │
│                                   │   Disk   │                            │
│                                   └──────────┘                            │
│                                                                            │
│                                                                            │
│   MODERN LINUX:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌──────────┐                                                            │
│   │ Process  │                                                            │
│   └────┬─────┘                                                            │
│        │ read()                                                           │
│        ▼                                                                  │
│   ┌──────────┐    ┌──────────────────────────────────────────────┐       │
│   │   VFS    │───►│              PAGE CACHE                       │       │
│   └──────────┘    │  (inode, offset) → page                       │       │
│                   │  Page-sized (4KB) aligned with VM system      │       │
│                   └──────────────────────┬───────────────────────┘       │
│                                          │                                │
│                                          │                                │
│                   ┌──────────────────────┴───────────────────────┐       │
│                   │           BUFFER HEADS                        │       │
│                   │  (for block device metadata only)             │       │
│                   │  Maps page cache pages to disk blocks         │       │
│                   └──────────────────────┬───────────────────────┘       │
│                                          │                                │
│                                          ▼                                │
│                                   ┌──────────┐                            │
│                                   │   Disk   │                            │
│                                   └──────────┘                            │
│                                                                            │
│                                                                            │
│   WHY THE CHANGE?                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   1. Unified memory management - pages can be cached OR mapped            │
│   2. Memory-mapped files work seamlessly with cache                       │
│   3. No double buffering (buffer cache + page cache)                      │
│   4. Better integration with virtual memory system                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Block Devices

### What are Block Devices?

Block devices transfer data in fixed-size blocks and support random access. They typically use the buffer
cache (or page cache in modern systems) for caching.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BLOCK DEVICE CHARACTERISTICS                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BLOCK DEVICE PROPERTIES:                                           │ │
│   │                                                                      │ │
│   │   • Fixed block size (512 bytes, 4KB, etc.)                         │ │
│   │   • Random access supported                                          │ │
│   │   • Data cached in buffer/page cache                                │ │
│   │   • Addressable by block number                                      │ │
│   │   • Typically hardware with physical storage                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLES OF BLOCK DEVICES:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────┬────────────────────────────────────────────┐    │
│   │ Device             │ Description                                 │    │
│   ├────────────────────┼────────────────────────────────────────────┤    │
│   │ /dev/sda           │ First SCSI/SATA disk                       │    │
│   │ /dev/sda1          │ First partition on first disk              │    │
│   │ /dev/nvme0n1       │ First NVMe drive                           │    │
│   │ /dev/nvme0n1p1     │ First partition on NVMe drive              │    │
│   │ /dev/loop0         │ Loop device (file as block device)         │    │
│   │ /dev/md0           │ RAID array                                  │    │
│   │ /dev/dm-0          │ Device mapper (LVM, encryption)            │    │
│   │ /dev/sr0           │ CD/DVD drive                                │    │
│   └────────────────────┴────────────────────────────────────────────┘    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Device Numbers: Major and Minor

In Unix, devices are identified by two numbers: a major number (identifying the driver) and a minor number
(identifying the specific device):

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEVICE NUMBERS                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DEVICE NUMBER STRUCTURE:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Traditional Unix (16-bit dev_t):                                 │  │
│   │   ┌─────────────────┬─────────────────┐                            │  │
│   │   │   Major (8 bit) │   Minor (8 bit) │                            │  │
│   │   │     (driver)    │    (device)     │                            │  │
│   │   └─────────────────┴─────────────────┘                            │  │
│   │                                                                     │  │
│   │   Modern Linux (32-bit or 64-bit dev_t):                           │  │
│   │   ┌─────────────────┬─────────────────────────────────────────────┐│  │
│   │   │   Major (12 bit)│           Minor (20 bit)                    ││  │
│   │   │     (driver)    │            (device)                         ││  │
│   │   └─────────────────┴─────────────────────────────────────────────┘│  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   EXAMPLE: /dev/sda1                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│      $ ls -l /dev/sda1                                                    │
│      brw-rw---- 1 root disk 8, 1 Jan 1 00:00 /dev/sda1                   │
│                              │  │                                         │
│                              │  └── Minor number: 1 (first partition)    │
│                              └───── Major number: 8 (sd driver)          │
│                                                                            │
│                                                                            │
│   MAJOR NUMBER EXAMPLES:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────┬──────────────────────────────────────────────────────┐   │
│   │ Major      │ Device Type                                          │   │
│   ├────────────┼──────────────────────────────────────────────────────┤   │
│   │ 1          │ RAM disk                                              │   │
│   │ 3          │ IDE hard disk (hda, hdb - legacy)                    │   │
│   │ 7          │ Loop devices                                          │   │
│   │ 8          │ SCSI disk (sda, sdb, ...)                            │   │
│   │ 9          │ MD (software RAID)                                    │   │
│   │ 11         │ SCSI CD-ROM                                           │   │
│   │ 253        │ Device mapper                                         │   │
│   │ 259        │ Block Extended Major (NVMe, etc.)                    │   │
│   └────────────┴──────────────────────────────────────────────────────┘   │
│                                                                            │
│                                                                            │
│   KERNEL MACROS:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   MAJOR(dev)  - Extract major number from dev_t                           │
│   MINOR(dev)  - Extract minor number from dev_t                           │
│   MKDEV(ma,mi)- Create dev_t from major and minor                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Block Device Switch Table (bdevsw)

In traditional Unix, the kernel uses a switch table to dispatch operations to the appropriate device driver:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE bdevsw TABLE                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BLOCK DEVICE SWITCH TABLE:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct bdevsw {                                                          │
│       int (*d_open)();      /* Open device */                             │
│       int (*d_close)();     /* Close device */                            │
│       int (*d_strategy)();  /* Start I/O operation */                     │
│       int (*d_dump)();      /* Dump memory to device */                   │
│       int (*d_psize)();     /* Get partition size */                      │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   bdevsw[]  (indexed by major number)                               │ │
│   │                                                                      │ │
│   │   Index   d_open      d_close     d_strategy   d_dump    d_psize   │ │
│   │   ┌─────┬───────────┬───────────┬────────────┬─────────┬─────────┐ │ │
│   │   │  0  │ nulldev   │ nulldev   │ swstrategy │ nodev   │ 0       │ │ │
│   │   │     │ (swap)    │           │            │         │         │ │ │
│   │   ├─────┼───────────┼───────────┼────────────┼─────────┼─────────┤ │ │
│   │   │  1  │ ram_open  │ ram_close │ ram_strat  │ nodev   │ ram_sz  │ │ │
│   │   │     │ (ramdisk) │           │            │         │         │ │ │
│   │   ├─────┼───────────┼───────────┼────────────┼─────────┼─────────┤ │ │
│   │   │  8  │ sd_open   │ sd_close  │ sd_strategy│ nodev   │ sd_size │ │ │
│   │   │     │ (SCSI)    │           │            │         │         │ │ │
│   │   ├─────┼───────────┼───────────┼────────────┼─────────┼─────────┤ │ │
│   │   │ ... │    ...    │    ...    │     ...    │   ...   │   ...   │ │ │
│   │   └─────┴───────────┴───────────┴────────────┴─────────┴─────────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   HOW THE KERNEL USES bdevsw:                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌──────────────┐                                                        │
│   │ read(fd,...) │                                                        │
│   └──────┬───────┘                                                        │
│          │                                                                 │
│          ▼                                                                 │
│   ┌──────────────────┐                                                    │
│   │ Get device number│  dev = file->f_inode->i_rdev                       │
│   │ from file        │                                                    │
│   └────────┬─────────┘                                                    │
│            │                                                               │
│            ▼                                                               │
│   ┌──────────────────┐                                                    │
│   │ Extract major    │  major = MAJOR(dev)                                │
│   └────────┬─────────┘                                                    │
│            │                                                               │
│            ▼                                                               │
│   ┌──────────────────────────────────────┐                                │
│   │ Call driver function                  │                                │
│   │ (*bdevsw[major].d_strategy)(buffer)  │                                │
│   └──────────────────────────────────────┘                                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Character Devices

### What are Character Devices?

Character devices transfer data as a stream of bytes without buffering through the buffer cache. They
typically do not support random access.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CHARACTER DEVICE CHARACTERISTICS                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CHARACTER DEVICE PROPERTIES:                                       │ │
│   │                                                                      │ │
│   │   • Byte stream (no fixed block size)                               │ │
│   │   • Sequential access (usually)                                      │ │
│   │   • No buffer cache (data goes directly to/from device)             │ │
│   │   • Often represent hardware with stream-based I/O                  │ │
│   │   • May support ioctl() for device-specific operations              │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLES OF CHARACTER DEVICES:                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────┬────────────────────────────────────────────┐    │
│   │ Device             │ Description                                 │    │
│   ├────────────────────┼────────────────────────────────────────────┤    │
│   │ /dev/tty           │ Current terminal                            │    │
│   │ /dev/tty0          │ First virtual console                       │    │
│   │ /dev/pts/0         │ First pseudo-terminal slave                 │    │
│   │ /dev/null          │ Null device (discards all writes)          │    │
│   │ /dev/zero          │ Infinite stream of zero bytes               │    │
│   │ /dev/random        │ Random number generator (blocking)          │    │
│   │ /dev/urandom       │ Random number generator (non-blocking)      │    │
│   │ /dev/console       │ System console                              │    │
│   │ /dev/ttyS0         │ First serial port                           │    │
│   │ /dev/lp0           │ First parallel printer                      │    │
│   │ /dev/input/mice    │ Mouse input                                  │    │
│   └────────────────────┴────────────────────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   BLOCK vs CHARACTER DEVICES:                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────┬─────────────────────────────────────────┐   │
│   │ Block Devices            │ Character Devices                      │   │
│   ├─────────────────────────┼─────────────────────────────────────────┤   │
│   │ Fixed-size blocks        │ Byte stream                            │   │
│   │ Random access            │ Sequential (usually)                   │   │
│   │ Buffer/page cache used  │ No buffer cache                        │   │
│   │ File systems mounted    │ Cannot mount file systems              │   │
│   │ /dev/sda, /dev/nvme0n1  │ /dev/tty, /dev/null                    │   │
│   │ 'b' in ls -l            │ 'c' in ls -l                           │   │
│   └─────────────────────────┴─────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Character Device Switch Table (cdevsw)

Similar to block devices, character devices have their own switch table:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE cdevsw TABLE                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CHARACTER DEVICE SWITCH TABLE:                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct cdevsw {                                                          │
│       int (*d_open)();      /* Open device */                             │
│       int (*d_close)();     /* Close device */                            │
│       int (*d_read)();      /* Read from device */                        │
│       int (*d_write)();     /* Write to device */                         │
│       int (*d_ioctl)();     /* Device-specific control */                 │
│       int (*d_stop)();      /* Stop output (terminals) */                 │
│       int (*d_reset)();     /* Reset device */                            │
│       struct tty *d_ttys;   /* TTY structures (for terminals) */          │
│       int (*d_select)();    /* Select for I/O readiness */                │
│       int (*d_mmap)();      /* Memory map device */                       │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   cdevsw[]  (indexed by major number)                               │ │
│   │                                                                      │ │
│   │   Index  d_open     d_close   d_read    d_write   d_ioctl   ...    │ │
│   │   ┌─────┬──────────┬─────────┬─────────┬─────────┬─────────┬─────┐ │ │
│   │   │  1  │ mem_open │mem_close│ mem_read│mem_write│ nodev   │ ... │ │ │
│   │   │     │ (memory) │         │         │         │         │     │ │ │
│   │   ├─────┼──────────┼─────────┼─────────┼─────────┼─────────┼─────┤ │ │
│   │   │  4  │ tty_open │tty_close│ tty_read│tty_write│tty_ioctl│ ... │ │ │
│   │   │     │ (tty)    │         │         │         │         │     │ │ │
│   │   ├─────┼──────────┼─────────┼─────────┼─────────┼─────────┼─────┤ │ │
│   │   │  5  │ ptc_open │ptc_close│ ptc_read│ptc_write│ptc_ioctl│ ... │ │ │
│   │   │     │ (pty)    │         │         │         │         │     │ │ │
│   │   ├─────┼──────────┼─────────┼─────────┼─────────┼─────────┼─────┤ │ │
│   │   │ ... │   ...    │   ...   │   ...   │   ...   │   ...   │ ... │ │ │
│   │   └─────┴──────────┴─────────┴─────────┴─────────┴─────────┴─────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Raw Device Access

Unix provides "raw" access to block devices through character device interfaces, bypassing the buffer cache:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RAW DEVICE ACCESS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Every block device typically has a corresponding raw (character) device:│
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Block Device         Raw Device                                  │  │
│   │   ────────────         ──────────                                  │  │
│   │   /dev/sda    ◄────►   /dev/rsda  (traditional Unix)              │  │
│   │   /dev/hda    ◄────►   /dev/rhda                                   │  │
│   │                                                                     │  │
│   │   In Linux: same device with O_DIRECT flag                         │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   BUFFERED vs RAW ACCESS:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BUFFERED ACCESS (through block device):                           │ │
│   │                                                                      │ │
│   │   Process ──► Buffer Cache ──► Disk                                 │ │
│   │                    │                                                 │ │
│   │                    └── Kernel manages caching                       │ │
│   │                        Good for: file systems, general I/O          │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   RAW ACCESS (through character device or O_DIRECT):                │ │
│   │                                                                      │ │
│   │   Process ──────────────────► Disk                                  │ │
│   │        │                                                             │ │
│   │        └── Direct transfer, no caching                              │ │
│   │            Good for: databases, backup utilities                    │ │
│   │            Requires: aligned buffers, sector-sized transfers        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Device Drivers

### Driver Architecture

Device drivers are the kernel components that manage hardware devices. They provide a standard interface to
the rest of the kernel.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEVICE DRIVER ARCHITECTURE                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                       USER SPACE                                     │ │
│   │                                                                      │ │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │ │
│   │   │  App 1   │  │  App 2   │  │  App 3   │  │  App 4   │           │ │
│   │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │ │
│   │        │              │              │              │                │ │
│   └────────┼──────────────┼──────────────┼──────────────┼────────────────┘ │
│            │ System Calls │              │              │                  │
│   ─────────▼──────────────▼──────────────▼──────────────▼──────────────── │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                       KERNEL SPACE                                   │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │              VIRTUAL FILE SYSTEM (VFS)                       │   │ │
│   │   │         open, close, read, write, ioctl, ...                │   │ │
│   │   └───────────────────────────┬─────────────────────────────────┘   │ │
│   │                               │                                      │ │
│   │         ┌─────────────────────┼─────────────────────┐               │ │
│   │         │                     │                     │               │ │
│   │         ▼                     ▼                     ▼               │ │
│   │   ┌──────────┐         ┌──────────┐          ┌──────────┐          │ │
│   │   │  Block   │         │Character │          │ Network  │          │ │
│   │   │  Layer   │         │  Layer   │          │  Stack   │          │ │
│   │   └────┬─────┘         └────┬─────┘          └────┬─────┘          │ │
│   │        │                    │                     │                 │ │
│   │        ▼                    ▼                     ▼                 │ │
│   │   ┌──────────┐         ┌──────────┐          ┌──────────┐          │ │
│   │   │  Block   │         │   Char   │          │  Network │          │ │
│   │   │ Drivers  │         │ Drivers  │          │ Drivers  │          │ │
│   │   │ (sd,nvme)│         │(tty,null)│          │(eth,wifi)│          │ │
│   │   └────┬─────┘         └────┬─────┘          └────┬─────┘          │ │
│   │        │                    │                     │                 │ │
│   └────────┼────────────────────┼─────────────────────┼─────────────────┘ │
│            │                    │                     │                   │
│   ─────────▼────────────────────▼─────────────────────▼────────────────── │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         HARDWARE                                     │ │
│   │   ┌──────────┐         ┌──────────┐          ┌──────────┐           │ │
│   │   │  Disks   │         │ Terminals│          │   NIC    │           │ │
│   │   └──────────┘         └──────────┘          └──────────┘           │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Top Half vs Bottom Half

Device drivers are split into two parts to handle the asynchronous nature of hardware:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TOP HALF vs BOTTOM HALF                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   TOP HALF (Interrupt Handler / Hard IRQ):                          │ │
│   │   ─────────────────────────────────────────                         │ │
│   │                                                                      │ │
│   │   • Runs in interrupt context                                       │ │
│   │   • Cannot sleep or block                                           │ │
│   │   • Must complete quickly                                           │ │
│   │   • Does minimal work:                                              │ │
│   │     - Acknowledge interrupt                                         │ │
│   │     - Save data to buffer                                           │ │
│   │     - Schedule bottom half                                          │ │
│   │                                                                      │ │
│   │                                                                      │ │
│   │   BOTTOM HALF (Deferred Work):                                      │ │
│   │   ─────────────────────────────                                     │ │
│   │                                                                      │ │
│   │   • Runs later, not in interrupt context                            │ │
│   │   • Can take more time                                              │ │
│   │   • Different mechanisms:                                           │ │
│   │     - Softirqs (highest priority)                                   │ │
│   │     - Tasklets (built on softirqs)                                  │ │
│   │     - Work queues (can sleep)                                       │ │
│   │     - Threaded IRQs (modern)                                        │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   INTERRUPT FLOW:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────┐                                                          │
│   │  Hardware  │                                                          │
│   │  Interrupt │                                                          │
│   └─────┬──────┘                                                          │
│         │                                                                  │
│         ▼                                                                  │
│   ┌────────────────────────────────────────────┐                          │
│   │           TOP HALF (Hard IRQ)              │  Interrupts disabled    │
│   │  • Acknowledge interrupt                   │  Must be FAST           │
│   │  • Read data from device                   │                          │
│   │  • Schedule bottom half                    │                          │
│   └────────────────────┬───────────────────────┘                          │
│                        │                                                   │
│         ┌──────────────┴──────────────┐                                   │
│         ▼                             ▼                                   │
│   ┌───────────────┐           ┌───────────────┐                           │
│   │   Softirq /   │           │  Work Queue   │                           │
│   │   Tasklet     │           │    Thread     │                           │
│   │ (atomic ctx)  │           │ (process ctx) │                           │
│   └───────┬───────┘           └───────┬───────┘                           │
│           │                           │                                    │
│           └───────────┬───────────────┘                                   │
│                       │                                                    │
│                       ▼                                                    │
│               ┌───────────────┐                                           │
│               │ Complete I/O  │                                           │
│               │ Wake process  │                                           │
│               └───────────────┘                                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Driver Entry Points

Every device driver provides a set of functions that the kernel calls:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DRIVER ENTRY POINTS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   COMMON DRIVER FUNCTIONS:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┬──────────────────────────────────────────────────┐  │
│   │ Function        │ Description                                       │  │
│   ├─────────────────┼──────────────────────────────────────────────────┤  │
│   │ open()          │ Called when device file is opened                │  │
│   │ close/release() │ Called when last reference to device is closed  │  │
│   │ read()          │ Transfer data from device to user                │  │
│   │ write()         │ Transfer data from user to device                │  │
│   │ ioctl()         │ Device-specific control operations               │  │
│   │ poll/select()   │ Check if I/O is possible without blocking        │  │
│   │ mmap()          │ Map device memory into user space                │  │
│   │ llseek()        │ Change current read/write position               │  │
│   └─────────────────┴──────────────────────────────────────────────────┘  │
│                                                                            │
│                                                                            │
│   MODERN LINUX: struct file_operations                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   struct file_operations {                                                 │
│       struct module *owner;                                                │
│       loff_t (*llseek)(struct file *, loff_t, int);                       │
│       ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);   │
│       ssize_t (*write)(struct file *, const char __user *, size_t, ...); │
│       __poll_t (*poll)(struct file *, struct poll_table_struct *);       │
│       long (*unlocked_ioctl)(struct file *, unsigned int, unsigned long);│
│       int (*mmap)(struct file *, struct vm_area_struct *);               │
│       int (*open)(struct inode *, struct file *);                         │
│       int (*release)(struct inode *, struct file *);                      │
│       int (*fsync)(struct file *, loff_t, loff_t, int);                  │
│       /* ... more operations ... */                                       │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   EXAMPLE DRIVER REGISTRATION:                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   static struct file_operations my_fops = {                                │
│       .owner   = THIS_MODULE,                                              │
│       .open    = my_open,                                                  │
│       .release = my_release,                                               │
│       .read    = my_read,                                                  │
│       .write   = my_write,                                                 │
│       .unlocked_ioctl = my_ioctl,                                          │
│   };                                                                       │
│                                                                            │
│   static int __init my_init(void) {                                        │
│       register_chrdev(MAJOR_NUM, "mydevice", &my_fops);                   │
│       return 0;                                                            │
│   }                                                                        │
│                                                                            │
│   static void __exit my_exit(void) {                                       │
│       unregister_chrdev(MAJOR_NUM, "mydevice");                           │
│   }                                                                        │
│                                                                            │
│   module_init(my_init);                                                    │
│   module_exit(my_exit);                                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Modern Linux: Device Model and sysfs

Modern Linux uses a unified device model with sysfs:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX DEVICE MODEL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   KEY CONCEPTS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   BUSES:                                                             │ │
│   │   • PCI, USB, I2C, SPI, Platform, ...                               │ │
│   │   • Provide infrastructure for device discovery                     │ │
│   │   • Match devices to drivers                                        │ │
│   │                                                                      │ │
│   │   DEVICES:                                                           │ │
│   │   • Represent physical or virtual hardware                          │ │
│   │   • Discovered by bus or explicitly registered                      │ │
│   │   • struct device                                                    │ │
│   │                                                                      │ │
│   │   DRIVERS:                                                           │ │
│   │   • Code that manages devices                                        │ │
│   │   • Probe function called when device matched                       │ │
│   │   • struct device_driver                                             │ │
│   │                                                                      │ │
│   │   CLASSES:                                                           │ │
│   │   • Categorize devices by function                                  │ │
│   │   • block, net, tty, input, ...                                     │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   SYSFS STRUCTURE:                                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   /sys/                                                                    │
│   ├── bus/                    # Buses (pci, usb, i2c, ...)               │
│   │   ├── pci/                                                            │
│   │   │   ├── devices/        # Links to devices                         │
│   │   │   └── drivers/        # Drivers for this bus                     │
│   │   └── usb/                                                            │
│   ├── class/                  # Device classes                            │
│   │   ├── block/              # Block devices                             │
│   │   ├── net/                # Network devices                           │
│   │   └── tty/                # Terminal devices                          │
│   ├── devices/                # Device hierarchy                          │
│   │   └── pci0000:00/         # PCI root bus                             │
│   │       └── 0000:00:1f.2/   # SATA controller                          │
│   │           └── ata1/                                                   │
│   │               └── host0/                                              │
│   │                   └── target0:0:0/                                   │
│   │                       └── 0:0:0:0/                                   │
│   │                           └── block/sda                              │
│   └── module/                 # Loaded kernel modules                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Terminal I/O

### Terminal Drivers and Line Disciplines

Terminals are special character devices with complex processing requirements:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TERMINAL SUBSYSTEM ARCHITECTURE                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                        USER SPACE                                    │ │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐                         │ │
│   │   │  Shell   │  │  Editor  │  │  curses  │                         │ │
│   │   │  (bash)  │  │  (vim)   │  │   app    │                         │ │
│   │   └────┬─────┘  └────┬─────┘  └────┬─────┘                         │ │
│   │        │              │              │                               │ │
│   └────────┼──────────────┼──────────────┼───────────────────────────────┘ │
│            │              │              │                                 │
│   ─────────▼──────────────▼──────────────▼───────────────────────────────  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     KERNEL SPACE                                     │ │
│   │                                                                      │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                    TTY CORE                                  │   │ │
│   │   │              (tty_io.c, tty_ioctl.c)                        │   │ │
│   │   └───────────────────────────┬─────────────────────────────────┘   │ │
│   │                               │                                      │ │
│   │   ┌───────────────────────────▼─────────────────────────────────┐   │ │
│   │   │                  LINE DISCIPLINE                             │   │ │
│   │   │     • Input processing (echo, line editing)                 │   │ │
│   │   │     • Output processing (newline translation)               │   │ │
│   │   │     • Default: N_TTY (canonical processing)                 │   │ │
│   │   │     • Others: N_SLIP, N_PPP, N_MOUSE, ...                   │   │ │
│   │   └───────────────────────────┬─────────────────────────────────┘   │ │
│   │                               │                                      │ │
│   │   ┌───────────────────────────▼─────────────────────────────────┐   │ │
│   │   │                    TTY DRIVER                                │   │ │
│   │   │     • Hardware-specific code                                │   │ │
│   │   │     • Serial, console, pty, ...                             │   │ │
│   │   └───────────────────────────┬─────────────────────────────────┘   │ │
│   │                               │                                      │ │
│   └───────────────────────────────┼─────────────────────────────────────┘ │
│                                   │                                       │
│   ────────────────────────────────▼─────────────────────────────────────  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         HARDWARE                                     │ │
│   │    Serial Port │ VGA Console │ Pseudo-terminal │ USB Serial         │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Canonical vs Non-Canonical Mode

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TERMINAL MODES                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CANONICAL MODE (Cooked Mode):                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   • Line-oriented input                                             │ │
│   │   • Input available to process when ENTER pressed                   │ │
│   │   • Line editing supported:                                         │ │
│   │     - Backspace (ERASE)                                             │ │
│   │     - Ctrl+U (KILL - erase line)                                    │ │
│   │     - Ctrl+W (WERASE - erase word)                                  │ │
│   │   • Echo enabled by default                                         │ │
│   │   • Signal generation (Ctrl+C, Ctrl+Z)                             │ │
│   │                                                                      │ │
│   │   User types:  H e l l o [BACKSPACE] o [ENTER]                      │ │
│   │   Process sees: "Hello\n"                                           │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   NON-CANONICAL MODE (Raw/Cbreak Mode):                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   • Character-oriented input                                        │ │
│   │   • Input available immediately (or based on MIN/TIME)             │ │
│   │   • No line editing by terminal                                     │ │
│   │   • Used by: editors (vim), games, ncurses applications            │ │
│   │                                                                      │ │
│   │   MIN and TIME parameters:                                          │ │
│   │   ─────────────────────────────────────────────────────────────────│ │
│   │   MIN=0, TIME=0: Return immediately (polling)                      │ │
│   │   MIN>0, TIME=0: Block until MIN bytes available                   │ │
│   │   MIN=0, TIME>0: Return after TIME or when data available          │ │
│   │   MIN>0, TIME>0: Return when MIN bytes or TIME, whichever first    │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The termios Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE termios STRUCTURE                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct termios {                                                         │
│       tcflag_t c_iflag;   /* Input modes */                               │
│       tcflag_t c_oflag;   /* Output modes */                              │
│       tcflag_t c_cflag;   /* Control modes */                             │
│       tcflag_t c_lflag;   /* Local modes */                               │
│       cc_t c_cc[NCCS];    /* Control characters */                        │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   INPUT FLAGS (c_iflag):                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│   ICRNL   - Map CR to NL on input                                         │
│   INLCR   - Map NL to CR on input                                         │
│   IGNCR   - Ignore CR on input                                            │
│   IXON    - Enable XON/XOFF flow control on output                        │
│   IXOFF   - Enable XON/XOFF flow control on input                         │
│                                                                            │
│   OUTPUT FLAGS (c_oflag):                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│   OPOST   - Enable output processing                                      │
│   ONLCR   - Map NL to CR-NL on output                                     │
│   OCRNL   - Map CR to NL on output                                        │
│                                                                            │
│   CONTROL FLAGS (c_cflag):                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│   CS5-CS8 - Character size (5-8 bits)                                     │
│   CSTOPB  - Two stop bits                                                  │
│   CREAD   - Enable receiver                                               │
│   PARENB  - Enable parity                                                  │
│   HUPCL   - Hang up on last close                                         │
│                                                                            │
│   LOCAL FLAGS (c_lflag):                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│   ICANON  - Canonical mode (line-oriented)                                │
│   ECHO    - Echo input characters                                         │
│   ECHOE   - Echo ERASE as backspace-space-backspace                       │
│   ISIG    - Enable signals (INTR, QUIT, SUSP)                             │
│   IEXTEN  - Enable extended functions                                     │
│                                                                            │
│                                                                            │
│   CONTROL CHARACTERS (c_cc[]):                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│   VINTR   - Interrupt (^C)                VEOF    - End of file (^D)      │
│   VQUIT   - Quit (^\)                     VMIN    - Min chars for read    │
│   VERASE  - Erase char (^?)               VTIME   - Timeout for read      │
│   VKILL   - Kill line (^U)                VSTART  - Start output (^Q)     │
│   VSUSP   - Suspend (^Z)                  VSTOP   - Stop output (^S)      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Pseudo-Terminals (PTY)

Pseudo-terminals provide terminal semantics for programs that are not connected to real hardware terminals:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PSEUDO-TERMINAL ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A pseudo-terminal is a PAIR of devices:                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │    MASTER SIDE                         SLAVE SIDE                   │ │
│   │    (/dev/ptmx or                       (/dev/pts/N)                 │ │
│   │     /dev/ptyXX)                                                      │ │
│   │                                                                      │ │
│   │   ┌──────────────┐                   ┌──────────────┐               │ │
│   │   │   Terminal   │                   │    Shell     │               │ │
│   │   │   Emulator   │                   │   (bash)     │               │ │
│   │   │   (xterm)    │                   │              │               │ │
│   │   └──────┬───────┘                   └──────┬───────┘               │ │
│   │          │                                   │                       │ │
│   │          │ write()                           │ read()                │ │
│   │          ▼                                   ▼                       │ │
│   │   ┌──────────────┐                   ┌──────────────┐               │ │
│   │   │    PTY       │◄─────────────────►│     PTY      │               │ │
│   │   │   Master     │   kernel buffers  │    Slave     │               │ │
│   │   │  /dev/ptmx   │   + line disc     │  /dev/pts/0  │               │ │
│   │   └──────────────┘                   └──────────────┘               │ │
│   │                                                                      │ │
│   │   Data flow:                                                         │ │
│   │   - Master write() → appears as input to slave                      │ │
│   │   - Slave write() → appears as output on master                     │ │
│   │   - Line discipline applied between master and slave                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   USE CASES:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────┬───────────────────────────────────────────────────┐ │
│   │ Application     │ How PTY is Used                                   │ │
│   ├─────────────────┼───────────────────────────────────────────────────┤ │
│   │ xterm, gnome-   │ Terminal emulator opens master, spawns shell     │ │
│   │ terminal        │ connected to slave                                │ │
│   │                 │                                                    │ │
│   │ ssh, telnet     │ Remote login - server opens PTY for each session │ │
│   │                 │                                                    │ │
│   │ screen, tmux    │ Terminal multiplexer manages multiple PTYs       │ │
│   │                 │                                                    │ │
│   │ script          │ Record terminal session via PTY                   │ │
│   │                 │                                                    │ │
│   │ expect          │ Automate interactive programs                     │ │
│   └─────────────────┴───────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   PTY CREATION (Modern Unix98 Style):                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int master_fd = open("/dev/ptmx", O_RDWR);  /* Get master */            │
│   grantpt(master_fd);                         /* Set permissions */       │
│   unlockpt(master_fd);                        /* Unlock slave */          │
│   char *slave_name = ptsname(master_fd);      /* Get slave path */        │
│                                                                            │
│   if (fork() == 0) {                                                       │
│       /* Child process */                                                  │
│       setsid();                              /* New session */            │
│       int slave_fd = open(slave_name, O_RDWR);                            │
│       dup2(slave_fd, STDIN_FILENO);                                       │
│       dup2(slave_fd, STDOUT_FILENO);                                      │
│       dup2(slave_fd, STDERR_FILENO);                                      │
│       execl("/bin/bash", "bash", NULL);                                   │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Disk I/O

### Disk Structure and Geometry

Understanding physical disk structure is essential for understanding I/O:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DISK STRUCTURE (Traditional HDD)                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PHYSICAL COMPONENTS:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│                        Spindle                                             │
│                           │                                                │
│              ┌────────────┼────────────┐                                  │
│              │            │            │                                  │
│       ┌──────┴──────┬─────┴─────┬──────┴──────┐                          │
│       │   Platter   │  Platter  │   Platter   │  ◄── Multiple platters   │
│       │    0        │    1      │     2       │      stacked on spindle  │
│       └─────────────┴───────────┴─────────────┘                          │
│              │                                                             │
│              │◄── Read/Write Head (one per platter surface)               │
│              │                                                             │
│       ───────┴───────                                                      │
│              │                                                             │
│              ▼                                                             │
│       Actuator Arm (moves heads radially)                                 │
│                                                                            │
│                                                                            │
│   DISK GEOMETRY:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│             Track 0    Track 1    Track 2                                 │
│               │          │          │                                      │
│               ▼          ▼          ▼                                      │
│         ┌─────────────────────────────────┐                               │
│         │  ╭─────────────────────────╮    │                               │
│         │  │   ╭─────────────────╮   │    │                               │
│         │  │   │   ╭─────────╮   │   │    │                               │
│         │  │   │   │         │   │   │    │                               │
│         │  │   │   │    ●    │   │   │◄───┼── Spindle                     │
│         │  │   │   │         │   │   │    │                               │
│         │  │   │   ╰─────────╯   │   │    │                               │
│         │  │   ╰────────┬────────╯   │    │                               │
│         │  ╰────────────┼────────────╯    │                               │
│         └───────────────┼─────────────────┘                               │
│                         │                                                  │
│                    Sector ──► Smallest addressable unit (512B or 4KB)     │
│                                                                            │
│                                                                            │
│   ADDRESSING:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Traditional CHS (Cylinder-Head-Sector):                                  │
│   • Cylinder: Set of tracks at same radius on all platters                │
│   • Head: Which platter surface (0, 1, 2, ...)                            │
│   • Sector: Which sector within the track                                  │
│                                                                            │
│   Modern LBA (Logical Block Addressing):                                   │
│   • Linear numbering: 0, 1, 2, 3, ... N-1                                 │
│   • Abstracts physical geometry                                            │
│   • Used by all modern systems                                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### I/O Request Flow

The journey of an I/O request through the kernel:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    I/O REQUEST FLOW                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────┐                                                      │
│   │  User Process   │  read(fd, buf, 4096)                                │
│   │                 │                                                      │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │   VFS Layer     │  Generic file operations                            │
│   │                 │  vfs_read() → file->f_op->read()                   │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │  File System    │  ext4_file_read_iter()                              │
│   │   (ext4)        │  Maps file offset to disk blocks                    │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │   Page Cache    │  Check if data already in memory                    │
│   │                 │  Cache hit → return immediately                     │
│   └────────┬────────┘                                                      │
│            │ Cache miss                                                    │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │   Block Layer   │  Create bio (block I/O) structure                   │
│   │                 │  submit_bio()                                        │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │  I/O Scheduler  │  Queue and reorder requests                         │
│   │                 │  Merge adjacent requests                             │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │  Block Driver   │  sd_queue_rq() for SCSI                             │
│   │   (sd, nvme)    │  Convert to device commands                         │
│   └────────┬────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│   ┌─────────────────┐                                                      │
│   │    Hardware     │  DMA transfer                                       │
│   │   Controller    │  Interrupt on completion                            │
│   └─────────────────┘                                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Block I/O (bio) Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE BIO STRUCTURE                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct bio {                                                             │
│       struct block_device *bi_bdev;   /* Target device */                 │
│       unsigned int         bi_opf;    /* Operation and flags */           │
│       sector_t            bi_sector;  /* Starting sector */               │
│       struct bio_vec      *bi_io_vec; /* Scatter-gather list */           │
│       unsigned short      bi_vcnt;    /* Number of bio_vecs */            │
│       unsigned short      bi_idx;     /* Current index into bi_io_vec */  │
│       unsigned int        bi_size;    /* Remaining I/O size */            │
│       bio_end_io_t        *bi_end_io; /* Completion callback */           │
│       void                *bi_private;/* Private data */                  │
│       /* ... */                                                            │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   BIO WITH SCATTER-GATHER:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         struct bio                                   │ │
│   │                                                                      │ │
│   │   bi_bdev ──────► /dev/sda                                          │ │
│   │   bi_sector ────► 1000                                              │ │
│   │   bi_vcnt ──────► 3                                                 │ │
│   │   bi_io_vec ────► ┌──────────────────────────────────────────┐     │ │
│   │                   │ bio_vec[0]: page=0xffff..., offset=0, len=4096│     │ │
│   │                   │ bio_vec[1]: page=0xffff..., offset=0, len=4096│     │ │
│   │                   │ bio_vec[2]: page=0xffff..., offset=0, len=4096│     │ │
│   │                   └──────────────────────────────────────────┘     │ │
│   │                                                                      │ │
│   │   Total I/O: 12KB (3 pages) starting at sector 1000                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### I/O Scheduling Algorithms

I/O schedulers optimize the order of disk requests:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    I/O SCHEDULING ALGORITHMS                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM:                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Without scheduling, requests served in arrival order (FIFO):            │
│                                                                            │
│   Request order:  Sector 100 → Sector 50000 → Sector 200 → Sector 49000  │
│   Head movement:  ────────►──────────────────►────────►                   │
│                   Lots of seeking! (slow)                                  │
│                                                                            │
│                                                                            │
│   NOOP (No Operation):                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Simple FIFO queue                                                      │
│   • Only merges adjacent requests                                          │
│   • Good for: SSDs, virtual machines, RAM disks                           │
│   • No benefit from reordering (no seek time)                             │
│                                                                            │
│                                                                            │
│   DEADLINE:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   Read Queue (sorted by sector)  ←── Deadline: 500ms               │ │
│   │   Write Queue (sorted by sector) ←── Deadline: 5000ms              │ │
│   │                                                                      │ │
│   │   FIFO Read Queue (sorted by time)                                  │ │
│   │   FIFO Write Queue (sorted by time)                                 │ │
│   │                                                                      │ │
│   │   Algorithm:                                                         │ │
│   │   1. Check if any request has expired deadline                      │ │
│   │   2. If yes, service oldest expired request                         │ │
│   │   3. Otherwise, service from sorted queue (minimize seeking)        │ │
│   │                                                                      │ │
│   │   Benefit: Prevents starvation while optimizing seek                │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MORE I/O SCHEDULERS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CFQ (Completely Fair Queuing) - Historical:                              │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Per-process I/O queues                                                 │
│   • Round-robin service with time slices                                   │
│   • Fair bandwidth distribution among processes                            │
│   • I/O priority support (ionice)                                          │
│   • Deprecated in Linux 5.0                                                │
│                                                                            │
│                                                                            │
│   BFQ (Budget Fair Queueing) - Modern:                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Assigns "budgets" (sectors) to processes                               │
│   • Low latency for interactive applications                               │
│   • Good for desktops and mobile devices                                   │
│   • Supports I/O priorities and cgroups                                    │
│                                                                            │
│                                                                            │
│   mq-deadline (Multi-Queue Deadline) - Modern:                             │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Deadline algorithm for blk-mq (multi-queue block layer)               │
│   • Per-hardware-queue scheduling                                          │
│   • Default for many modern systems                                        │
│   • Excellent for NVMe SSDs                                                │
│                                                                            │
│                                                                            │
│   KYBER - Modern:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Token-based scheduler for fast devices                                 │
│   • Limits queue depth to control latency                                  │
│   • Separates reads (latency-sensitive) from writes                        │
│   • Good for datacenter NVMe workloads                                     │
│                                                                            │
│                                                                            │
│   SCHEDULER COMPARISON:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────┬────────────┬────────────┬────────────┬────────────┐     │
│   │ Scheduler   │ Best For   │ Latency    │ Throughput │ Fairness   │     │
│   ├─────────────┼────────────┼────────────┼────────────┼────────────┤     │
│   │ none        │ NVMe       │ Low        │ High       │ None       │     │
│   │ mq-deadline │ SSD/NVMe   │ Bounded    │ High       │ Basic      │     │
│   │ bfq         │ Desktop    │ Low        │ Moderate   │ Excellent  │     │
│   │ kyber       │ Datacenter │ Controlled │ High       │ None       │     │
│   └─────────────┴────────────┴────────────┴────────────┴────────────┘     │
│                                                                            │
│   Check/Change scheduler:                                                  │
│   $ cat /sys/block/sda/queue/scheduler                                    │
│   [mq-deadline] kyber bfq none                                            │
│   $ echo bfq > /sys/block/sda/queue/scheduler                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Direct Memory Access (DMA)

### What is DMA?

DMA allows devices to transfer data directly to/from memory without CPU involvement:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DIRECT MEMORY ACCESS (DMA)                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WITHOUT DMA (Programmed I/O):                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────┐                    ┌─────────┐                              │
│   │   CPU   │                    │  Device │                              │
│   │         │                    │         │                              │
│   └────┬────┘                    └────┬────┘                              │
│        │                              │                                    │
│        │  1. Read byte from device    │                                    │
│        │◄─────────────────────────────│                                    │
│        │  2. Write byte to memory     │                                    │
│        │──────────────────────────────►  Memory                           │
│        │  3. Repeat for each byte!    │                                    │
│        │                              │                                    │
│                                                                            │
│   Problem: CPU is busy copying every byte!                                 │
│                                                                            │
│                                                                            │
│   WITH DMA:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────┐    ┌───────────┐    ┌─────────┐                             │
│   │   CPU   │    │    DMA    │    │  Device │                             │
│   │         │    │Controller │    │         │                             │
│   └────┬────┘    └─────┬─────┘    └────┬────┘                             │
│        │               │               │                                   │
│        │  1. Setup DMA │               │                                   │
│        │──────────────►│               │                                   │
│        │ (addr, size)  │               │                                   │
│        │               │               │                                   │
│        │  CPU does     │  2. Transfer  │                                   │
│        │  other work!  │◄─────────────►│  Data moves directly            │
│        │               │   (bus master)│  device ↔ memory                 │
│        │               │               │                                   │
│        │◄──────────────│ 3. Interrupt  │                                   │
│        │  (transfer    │    complete   │                                   │
│        │   complete)   │               │                                   │
│                                                                            │
│   Benefit: CPU free to do other work during transfer!                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### DMA Memory Requirements

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DMA MEMORY REQUIREMENTS                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DMA requires special memory considerations:                              │
│                                                                            │
│                                                                            │
│   1. PHYSICAL ADDRESSES:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Devices use physical (bus) addresses, not virtual addresses!            │
│                                                                            │
│   ┌─────────────┐                    ┌─────────────┐                      │
│   │   Process   │                    │   Device    │                      │
│   │ Virtual Addr│                    │  Bus Addr   │                      │
│   │ 0x7fff0000  │                    │ 0x12340000  │                      │
│   └──────┬──────┘                    └──────┬──────┘                      │
│          │                                   │                             │
│          ▼                                   ▼                             │
│   ┌──────────────────────────────────────────────────┐                    │
│   │                 PHYSICAL MEMORY                   │                    │
│   │                  0x12340000                       │                    │
│   └──────────────────────────────────────────────────┘                    │
│                                                                            │
│   Kernel must translate: virt_to_phys(), dma_map_single()                 │
│                                                                            │
│                                                                            │
│   2. CONTIGUOUS MEMORY:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Simple DMA needs physically contiguous buffers:                          │
│                                                                            │
│   kmalloc()      → Physically contiguous (OK for DMA)                     │
│   vmalloc()      → Virtually contiguous only (NOT OK for simple DMA)      │
│   dma_alloc_coherent() → Guaranteed DMA-capable memory                    │
│                                                                            │
│                                                                            │
│   3. CACHE COHERENCY:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   CPU Cache and DMA can see different data!                                │
│                                                                            │
│   ┌──────────────┐                                                        │
│   │  CPU Cache   │◄─── CPU writes here                                    │
│   │   "HELLO"    │                                                        │
│   └──────────────┘                                                        │
│         ≠                                                                  │
│   ┌──────────────┐                                                        │
│   │    Memory    │◄─── Device reads here (stale data!)                    │
│   │   "OLD.."    │                                                        │
│   └──────────────┘                                                        │
│                                                                            │
│   Solutions:                                                               │
│   • Coherent DMA memory (hardware maintains coherency)                    │
│   • Streaming DMA with explicit sync points                               │
│   • dma_sync_single_for_device() / dma_sync_single_for_cpu()             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Scatter-Gather DMA

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCATTER-GATHER DMA                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Modern devices support scatter-gather DMA:                               │
│   Transfer to/from multiple non-contiguous memory regions in one DMA      │
│                                                                            │
│                                                                            │
│   TRADITIONAL DMA (single buffer):                                         │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Must allocate one large contiguous buffer:                               │
│                                                                            │
│   Memory: [    ...    |████████████████████████|    ...    ]              │
│                        └─────────────────────────┘                         │
│                         One contiguous 64KB buffer                         │
│                         (hard to allocate after system runs a while)       │
│                                                                            │
│                                                                            │
│   SCATTER-GATHER DMA:                                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   Use multiple smaller buffers:                                            │
│                                                                            │
│   Memory: [█████|...|████|...|████████|...|████|...|██████]               │
│             │         │         │           │        │                     │
│             └─────────┴─────────┴───────────┴────────┘                     │
│                    Scatter-Gather List (SGL)                               │
│                                                                            │
│                                                                            │
│   struct scatterlist {                                                     │
│       unsigned long  page_link;   /* Page containing buffer */            │
│       unsigned int   offset;      /* Offset within page */                │
│       unsigned int   length;      /* Length of this segment */            │
│       dma_addr_t     dma_address; /* DMA address */                       │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   SCATTER-GATHER LIST EXAMPLE:                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  SG Entry 0     SG Entry 1     SG Entry 2     SG Entry 3            │ │
│   │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐          │ │
│   │  │page: 0x1 │   │page: 0x5 │   │page: 0x8 │   │page: 0xC │          │ │
│   │  │off: 0    │   │off: 512  │   │off: 0    │   │off: 2048 │          │ │
│   │  │len: 4096 │   │len: 3584 │   │len: 8192 │   │len: 2048 │          │ │
│   │  └──────────┘   └──────────┘   └──────────┘   └──────────┘          │ │
│   │                                                                      │ │
│   │  Total transfer: 4096 + 3584 + 8192 + 2048 = 17920 bytes            │ │
│   │  DMA controller reads list and transfers all segments                │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### DMA Mapping API

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX DMA MAPPING API                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   COHERENT DMA MAPPING:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Hardware maintains cache coherency                                     │
│   • Suitable for long-lived buffers (DMA descriptors, ring buffers)       │
│   • More expensive to set up                                               │
│                                                                            │
│   void *dma_alloc_coherent(                                                │
│       struct device *dev,                                                  │
│       size_t size,                                                         │
│       dma_addr_t *dma_handle,   /* OUT: DMA address for device */        │
│       gfp_t flag                                                           │
│   );                                                                       │
│                                                                            │
│   void dma_free_coherent(                                                  │
│       struct device *dev,                                                  │
│       size_t size,                                                         │
│       void *cpu_addr,                                                      │
│       dma_addr_t dma_handle                                                │
│   );                                                                       │
│                                                                            │
│                                                                            │
│   STREAMING DMA MAPPING:                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│   • For one-shot transfers                                                 │
│   • Requires explicit sync operations                                      │
│   • More efficient for single transfers                                    │
│                                                                            │
│   dma_addr_t dma_map_single(                                               │
│       struct device *dev,                                                  │
│       void *cpu_addr,           /* Virtual address */                     │
│       size_t size,                                                         │
│       enum dma_data_direction dir                                          │
│   );                                                                       │
│                                                                            │
│   enum dma_data_direction {                                                │
│       DMA_BIDIRECTIONAL = 0,                                               │
│       DMA_TO_DEVICE = 1,        /* CPU → Device (write) */               │
│       DMA_FROM_DEVICE = 2,      /* Device → CPU (read) */                │
│       DMA_NONE = 3,                                                        │
│   };                                                                       │
│                                                                            │
│   void dma_unmap_single(dev, dma_addr, size, dir);                        │
│                                                                            │
│                                                                            │
│   USAGE PATTERN:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   /* Sending data to device */                                             │
│   buffer = kmalloc(size, GFP_KERNEL);                                      │
│   memcpy(buffer, data, size);                                              │
│   dma_addr = dma_map_single(dev, buffer, size, DMA_TO_DEVICE);            │
│   /* Tell device about dma_addr, start transfer */                        │
│   /* Wait for completion */                                                │
│   dma_unmap_single(dev, dma_addr, size, DMA_TO_DEVICE);                   │
│   kfree(buffer);                                                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. The VFS and I/O

### The Virtual File System Layer

The VFS provides a uniform interface to all file systems:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    VIRTUAL FILE SYSTEM (VFS)                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                        USER SPACE                                    │ │
│   │                                                                      │ │
│   │              read()  write()  open()  close()                       │ │
│   └───────────────────────────┬─────────────────────────────────────────┘ │
│                               │                                            │
│   ────────────────────────────┼──────────────────────────────────────────  │
│                               │ System Call Interface                      │
│                               ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │                     VIRTUAL FILE SYSTEM (VFS)                        │ │
│   │                                                                      │ │
│   │   • Provides uniform API to user space                              │ │
│   │   • Manages file descriptors                                        │ │
│   │   • Caches: dentry cache, inode cache                               │ │
│   │   • Routes operations to correct filesystem                         │ │
│   │                                                                      │ │
│   └───────────────────────────┬─────────────────────────────────────────┘ │
│                               │                                            │
│         ┌─────────────────────┼─────────────────────┐                     │
│         │                     │                     │                     │
│         ▼                     ▼                     ▼                     │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐                 │
│   │  ext4    │         │   XFS    │         │   NFS    │                 │
│   │          │         │          │         │(network) │                 │
│   └────┬─────┘         └────┬─────┘         └────┬─────┘                 │
│        │                    │                    │                        │
│        ▼                    ▼                    ▼                        │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐                 │
│   │  Block   │         │  Block   │         │ Network  │                 │
│   │  Device  │         │  Device  │         │  Stack   │                 │
│   └──────────┘         └──────────┘         └──────────┘                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### VFS Objects

The VFS uses four primary data structures:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    VFS OBJECT HIERARCHY                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                        SUPERBLOCK                                    │ │
│   │                    (struct super_block)                              │ │
│   │                                                                      │ │
│   │   • One per mounted filesystem                                      │ │
│   │   • Contains filesystem metadata                                    │ │
│   │   • Points to root inode                                            │ │
│   │                                                                      │ │
│   │   struct super_block {                                               │ │
│   │       dev_t              s_dev;       /* Device identifier */       │ │
│   │       unsigned long      s_blocksize; /* Block size */              │ │
│   │       struct file_system_type *s_type;/* Filesystem type */         │ │
│   │       struct super_operations *s_op;  /* Superblock operations */   │ │
│   │       struct dentry     *s_root;      /* Root dentry */             │ │
│   │       ...                                                            │ │
│   │   };                                                                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                       │
│                                    ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                          INODE                                       │ │
│   │                      (struct inode)                                  │ │
│   │                                                                      │ │
│   │   • One per file/directory/etc                                      │ │
│   │   • Contains file metadata (permissions, size, timestamps)          │ │
│   │   • Points to data blocks (via address_space)                       │ │
│   │                                                                      │ │
│   │   struct inode {                                                     │ │
│   │       umode_t            i_mode;      /* File type and permissions */│ │
│   │       uid_t              i_uid;       /* Owner user ID */           │ │
│   │       gid_t              i_gid;       /* Owner group ID */          │ │
│   │       unsigned long      i_ino;       /* Inode number */            │ │
│   │       loff_t             i_size;      /* File size in bytes */      │ │
│   │       struct timespec64  i_atime;     /* Access time */             │ │
│   │       struct timespec64  i_mtime;     /* Modification time */       │ │
│   │       struct inode_operations *i_op;  /* Inode operations */        │ │
│   │       struct file_operations  *i_fop; /* File operations */         │ │
│   │       struct address_space    *i_mapping; /* Page cache */          │ │
│   │       ...                                                            │ │
│   │   };                                                                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                       │
│                  ┌─────────────────┴─────────────────┐                    │
│                  ▼                                   ▼                    │
│   ┌─────────────────────────────┐     ┌─────────────────────────────┐    │
│   │         DENTRY              │     │           FILE              │    │
│   │     (struct dentry)         │     │       (struct file)         │    │
│   │                             │     │                             │    │
│   │ • Directory entry cache     │     │ • Open file instance        │    │
│   │ • Links name to inode       │     │ • Contains file position    │    │
│   │ • Forms directory tree      │     │ • One per open()            │    │
│   │                             │     │                             │    │
│   │ struct dentry {             │     │ struct file {               │    │
│   │   struct inode *d_inode;    │     │   struct path   f_path;     │    │
│   │   struct dentry *d_parent;  │     │   struct inode *f_inode;    │    │
│   │   struct qstr d_name;       │     │   loff_t  f_pos;            │    │
│   │   ...                       │     │   unsigned int f_flags;     │    │
│   │ };                          │     │   const struct              │    │
│   │                             │     │     file_operations *f_op;  │    │
│   └─────────────────────────────┘     └─────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   RELATIONSHIP EXAMPLE:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   open("/home/user/file.txt", O_RDONLY)                                   │
│                                                                            │
│   1. VFS looks up path: "/" → "home" → "user" → "file.txt"               │
│   2. Each component lookup uses dentry cache                              │
│   3. Final dentry points to inode for file.txt                           │
│   4. New struct file created, points to inode                             │
│   5. File descriptor returned to user                                     │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │  fd table    struct file        dentry           inode            │  │
│   │  ┌─────┐     ┌─────────┐       ┌─────────┐      ┌─────────┐       │  │
│   │  │ 0   │     │ f_pos   │       │ d_name  │      │ i_mode  │       │  │
│   │  │ 1   │     │ f_flags │       │"file.txt│      │ i_size  │       │  │
│   │  │ 2   │     │ f_inode─┼───────┼─d_inode─┼─────►│ i_blocks│       │  │
│   │  │ 3 ──┼────►│ f_op    │       │ d_parent│      │ i_mapping│      │  │
│   │  └─────┘     └─────────┘       └─────────┘      └─────────┘       │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The file_operations Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    struct file_operations                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The file_operations structure contains function pointers for all        │
│   operations that can be performed on a file:                             │
│                                                                            │
│   struct file_operations {                                                 │
│       struct module *owner;                                                │
│                                                                            │
│       /* Position operations */                                            │
│       loff_t (*llseek)(struct file *, loff_t, int);                       │
│                                                                            │
│       /* Read operations */                                                │
│       ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);   │
│       ssize_t (*read_iter)(struct kiocb *, struct iov_iter *);           │
│                                                                            │
│       /* Write operations */                                               │
│       ssize_t (*write)(struct file *, const char __user *,               │
│                        size_t, loff_t *);                                  │
│       ssize_t (*write_iter)(struct kiocb *, struct iov_iter *);          │
│                                                                            │
│       /* Directory operations */                                           │
│       int (*iterate_shared)(struct file *, struct dir_context *);        │
│                                                                            │
│       /* Poll/select */                                                    │
│       __poll_t (*poll)(struct file *, struct poll_table_struct *);       │
│                                                                            │
│       /* ioctl */                                                          │
│       long (*unlocked_ioctl)(struct file *, unsigned int, unsigned long);│
│       long (*compat_ioctl)(struct file *, unsigned int, unsigned long);  │
│                                                                            │
│       /* Memory mapping */                                                 │
│       int (*mmap)(struct file *, struct vm_area_struct *);               │
│                                                                            │
│       /* Open/close */                                                     │
│       int (*open)(struct inode *, struct file *);                         │
│       int (*release)(struct inode *, struct file *);                      │
│       int (*flush)(struct file *, fl_owner_t id);                         │
│                                                                            │
│       /* Sync */                                                           │
│       int (*fsync)(struct file *, loff_t, loff_t, int datasync);         │
│                                                                            │
│       /* Async I/O */                                                      │
│       ssize_t (*splice_read)(struct file *, loff_t *,                    │
│                              struct pipe_inode_info *, size_t, unsigned);│
│       ssize_t (*splice_write)(struct pipe_inode_info *,                  │
│                               struct file *, loff_t *, size_t, unsigned);│
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   CALL FLOW EXAMPLE (read):                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   User: read(fd, buf, count)                                              │
│            │                                                               │
│            ▼                                                               │
│   Kernel: sys_read()                                                       │
│            │                                                               │
│            ▼                                                               │
│   VFS: vfs_read()                                                          │
│            │                                                               │
│            ▼                                                               │
│   file->f_op->read() or file->f_op->read_iter()                           │
│            │                                                               │
│            ▼                                                               │
│   Filesystem-specific read (e.g., ext4_file_read_iter)                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The address_space_operations Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    struct address_space_operations                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The address_space connects a file's inode to its cached pages:          │
│                                                                            │
│   struct address_space {                                                   │
│       struct inode           *host;      /* Owner inode */                │
│       struct xarray          i_pages;    /* Cached pages */               │
│       gfp_t                  gfp_mask;   /* Memory allocation flags */    │
│       atomic_t               i_mmap_writable; /* Writable mappings */     │
│       const struct address_space_operations *a_ops;                       │
│       unsigned long          nrpages;    /* Number of cached pages */     │
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   struct address_space_operations {                                        │
│       /* Write dirty page to disk */                                       │
│       int (*writepage)(struct page *, struct writeback_control *);        │
│                                                                            │
│       /* Read page from disk */                                            │
│       int (*read_folio)(struct file *, struct folio *);                   │
│                                                                            │
│       /* Write multiple pages */                                           │
│       int (*writepages)(struct address_space *,                           │
│                         struct writeback_control *);                       │
│                                                                            │
│       /* Mark page dirty */                                                │
│       bool (*dirty_folio)(struct address_space *, struct folio *);        │
│                                                                            │
│       /* Read multiple pages ahead */                                      │
│       void (*readahead)(struct readahead_control *);                      │
│                                                                            │
│       /* Prepare to write to page */                                       │
│       int (*write_begin)(struct file *, struct address_space *,           │
│                          loff_t pos, unsigned len,                        │
│                          struct page **, void **);                        │
│                                                                            │
│       /* Finish write to page */                                           │
│       int (*write_end)(struct file *, struct address_space *,             │
│                        loff_t pos, unsigned len, unsigned copied,         │
│                        struct page *, void *);                            │
│                                                                            │
│       /* Direct I/O */                                                     │
│       ssize_t (*direct_IO)(struct kiocb *, struct iov_iter *);           │
│       ...                                                                  │
│   };                                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Page Cache and I/O

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE CACHE AND I/O                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   READ PATH:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   read(fd, buf, 4096)                                                      │
│        │                                                                   │
│        ▼                                                                   │
│   ┌────────────────┐                                                      │
│   │ VFS: vfs_read  │                                                      │
│   └───────┬────────┘                                                      │
│           │                                                                │
│           ▼                                                                │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │                      Page Cache Lookup                          │      │
│   │                                                                  │      │
│   │   find_get_page(mapping, index)                                 │      │
│   │        │                                                         │      │
│   │        ├─── Page found → copy_to_user() → return                │      │
│   │        │                                                         │      │
│   │        └─── Page not found (cache miss)                         │      │
│   │                    │                                             │      │
│   │                    ▼                                             │      │
│   │             Allocate new page                                    │      │
│   │                    │                                             │      │
│   │                    ▼                                             │      │
│   │             a_ops->read_folio()                                  │      │
│   │                    │                                             │      │
│   │                    ▼                                             │      │
│   │             Submit bio to block layer                            │      │
│   │                    │                                             │      │
│   │                    ▼                                             │      │
│   │             Wait for I/O completion                              │      │
│   │                    │                                             │      │
│   │                    ▼                                             │      │
│   │             copy_to_user() → return                              │      │
│   │                                                                  │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
│                                                                            │
│   WRITE PATH:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   write(fd, buf, 4096)                                                     │
│        │                                                                   │
│        ▼                                                                   │
│   ┌────────────────┐                                                      │
│   │VFS: vfs_write  │                                                      │
│   └───────┬────────┘                                                      │
│           │                                                                │
│           ▼                                                                │
│   ┌────────────────────────────────────────────────────────────────┐      │
│   │                      Page Cache Write                           │      │
│   │                                                                  │      │
│   │   a_ops->write_begin()                                          │      │
│   │        │                                                         │      │
│   │        ▼                                                         │      │
│   │   Find or allocate page in cache                                │      │
│   │        │                                                         │      │
│   │        ▼                                                         │      │
│   │   copy_from_user() to page                                      │      │
│   │        │                                                         │      │
│   │        ▼                                                         │      │
│   │   a_ops->write_end()                                            │      │
│   │        │                                                         │      │
│   │        ▼                                                         │      │
│   │   Mark page dirty                                               │      │
│   │        │                                                         │      │
│   │        ▼                                                         │      │
│   │   Return to user (write complete from user's view)              │      │
│   │        │                                                         │      │
│   │        │    (later, asynchronously)                             │      │
│   │        ▼                                                         │      │
│   │   ┌────────────────────────────────────────────────────────┐    │      │
│   │   │        Background Writeback (pdflush/flush threads)     │    │      │
│   │   │                                                         │    │      │
│   │   │   • Triggered by: dirty ratio, sync, periodic flush    │    │      │
│   │   │   • Calls a_ops->writepages()                          │    │      │
│   │   │   • Writes dirty pages to disk                         │    │      │
│   │   └────────────────────────────────────────────────────────┘    │      │
│   │                                                                  │      │
│   └────────────────────────────────────────────────────────────────┘      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. I/O System Calls

### The read() and write() System Calls

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    read() AND write() SYSTEM CALLS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FUNCTION SIGNATURES:                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ssize_t read(int fd, void *buf, size_t count);                          │
│   ssize_t write(int fd, const void *buf, size_t count);                   │
│                                                                            │
│   Returns:                                                                 │
│   • > 0  : Number of bytes read/written                                   │
│   • 0    : EOF (for read) or nothing written                              │
│   • -1   : Error (errno set)                                              │
│                                                                            │
│                                                                            │
│   KERNEL IMPLEMENTATION (simplified):                                      │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   SYSCALL_DEFINE3(read, unsigned int, fd, char __user *, buf,             │
│                   size_t, count)                                           │
│   {                                                                        │
│       struct fd f = fdget(fd);           /* Get file from fd */           │
│       if (!f.file)                                                         │
│           return -EBADF;                                                   │
│                                                                            │
│       loff_t pos = file_pos_read(f.file); /* Get current position */      │
│       ret = vfs_read(f.file, buf, count, &pos);                           │
│       if (ret >= 0)                                                        │
│           file_pos_write(f.file, pos);   /* Update position */            │
│                                                                            │
│       fdput(f);                                                            │
│       return ret;                                                          │
│   }                                                                        │
│                                                                            │
│   ssize_t vfs_read(struct file *file, char __user *buf,                   │
│                    size_t count, loff_t *pos)                              │
│   {                                                                        │
│       /* Check permissions, validate arguments */                          │
│       if (!(file->f_mode & FMODE_READ))                                   │
│           return -EBADF;                                                   │
│                                                                            │
│       /* Call filesystem-specific read */                                  │
│       if (file->f_op->read)                                               │
│           ret = file->f_op->read(file, buf, count, pos);                  │
│       else if (file->f_op->read_iter)                                     │
│           ret = new_sync_read(file, buf, count, pos);                     │
│       else                                                                 │
│           ret = -EINVAL;                                                   │
│                                                                            │
│       return ret;                                                          │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Vectored I/O: readv() and writev()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    VECTORED I/O: readv() AND writev()                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Vectored I/O allows reading/writing multiple buffers in a single call:  │
│                                                                            │
│   struct iovec {                                                           │
│       void  *iov_base;    /* Starting address */                          │
│       size_t iov_len;     /* Number of bytes */                           │
│   };                                                                       │
│                                                                            │
│   ssize_t readv(int fd, const struct iovec *iov, int iovcnt);             │
│   ssize_t writev(int fd, const struct iovec *iov, int iovcnt);            │
│                                                                            │
│                                                                            │
│   TRADITIONAL vs VECTORED:                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   TRADITIONAL (3 write() calls):                                           │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │   write(fd, header, sizeof(header));   /* System call 1 */      │    │
│   │   write(fd, data, data_len);           /* System call 2 */      │    │
│   │   write(fd, footer, sizeof(footer));   /* System call 3 */      │    │
│   │                                                                   │    │
│   │   Problem: 3 system calls = 3 context switches!                  │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   VECTORED (1 writev() call):                                              │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │   struct iovec iov[3] = {                                        │    │
│   │       { header, sizeof(header) },                                │    │
│   │       { data, data_len },                                        │    │
│   │       { footer, sizeof(footer) }                                 │    │
│   │   };                                                              │    │
│   │   writev(fd, iov, 3);                  /* Single system call! */ │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   VISUALIZATION:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   User Space:                                                              │
│   ┌────────┐  ┌─────────────────┐  ┌────────┐                             │
│   │ Header │  │      Data       │  │ Footer │                             │
│   │ 64B    │  │      1024B      │  │ 32B    │                             │
│   └────────┘  └─────────────────┘  └────────┘                             │
│        │               │               │                                   │
│        └───────────────┼───────────────┘                                   │
│                        ▼                                                   │
│   iovec[]:  [ (ptr, 64), (ptr, 1024), (ptr, 32) ]                         │
│                        │                                                   │
│                        ▼                                                   │
│   Kernel:   Atomic write of 1120 bytes                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Positioned I/O: pread() and pwrite()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSITIONED I/O: pread() AND pwrite()                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Read/write at a specific offset WITHOUT changing file position:         │
│                                                                            │
│   ssize_t pread(int fd, void *buf, size_t count, off_t offset);           │
│   ssize_t pwrite(int fd, const void *buf, size_t count, off_t offset);    │
│                                                                            │
│                                                                            │
│   TRADITIONAL vs POSITIONED:                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   TRADITIONAL (race condition possible):                                   │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │   /* Thread 1 */              /* Thread 2 */                     │    │
│   │   lseek(fd, 100, SEEK_SET);   lseek(fd, 200, SEEK_SET);         │    │
│   │   read(fd, buf1, 50);         read(fd, buf2, 50);               │    │
│   │                                                                   │    │
│   │   Problem: Threads share file position!                          │    │
│   │            Race between lseek and read                           │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   POSITIONED (thread-safe):                                                │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │   /* Thread 1 */              /* Thread 2 */                     │    │
│   │   pread(fd, buf1, 50, 100);   pread(fd, buf2, 50, 200);         │    │
│   │                                                                   │    │
│   │   Atomic: position specified in call, not shared                 │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   USE CASES:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Database random access                                                 │
│   • Multi-threaded file access                                            │
│   • Log files (append without seeking)                                    │
│   • Memory-mapped file alternatives                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Asynchronous I/O: POSIX AIO

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    POSIX ASYNCHRONOUS I/O (AIO)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   POSIX AIO allows I/O to proceed without blocking:                       │
│                                                                            │
│   struct aiocb {                                                           │
│       int           aio_fildes;     /* File descriptor */                 │
│       off_t         aio_offset;     /* File offset */                     │
│       volatile void *aio_buf;       /* Buffer */                          │
│       size_t        aio_nbytes;     /* Number of bytes */                 │
│       int           aio_reqprio;    /* Request priority */                │
│       struct sigevent aio_sigevent; /* Notification method */             │
│       int           aio_lio_opcode; /* Operation (LIO_READ/WRITE) */      │
│   };                                                                       │
│                                                                            │
│                                                                            │
│   KEY FUNCTIONS:                                                           │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int aio_read(struct aiocb *aiocbp);      /* Start async read */         │
│   int aio_write(struct aiocb *aiocbp);     /* Start async write */        │
│   int aio_error(const struct aiocb *);     /* Check status */             │
│   ssize_t aio_return(struct aiocb *);      /* Get return value */         │
│   int aio_suspend(const struct aiocb *const[], int,                       │
│                   const struct timespec *); /* Wait for completion */     │
│   int aio_cancel(int fd, struct aiocb *);  /* Cancel operation */         │
│                                                                            │
│                                                                            │
│   WORKFLOW:                                                                │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │                                                                    │   │
│   │   1. Setup aiocb structure                                        │   │
│   │      │                                                             │   │
│   │      ▼                                                             │   │
│   │   2. aio_read(&cb)  ───────► Returns immediately                  │   │
│   │      │                              │                              │   │
│   │      ▼                              ▼                              │   │
│   │   3. Do other work           Kernel performs I/O                  │   │
│   │      │                              │                              │   │
│   │      ▼                              ▼                              │   │
│   │   4. Check completion:       I/O completes                        │   │
│   │      • aio_error() == EINPROGRESS? Still running                  │   │
│   │      • aio_error() == 0? Done, call aio_return()                  │   │
│   │      • aio_suspend()? Block until done                            │   │
│   │                                                                    │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   NOTE: Linux POSIX AIO is implemented in glibc using threads,            │
│         not true kernel AIO. For true async I/O, use io_uring.            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Modern Linux I/O

### io_uring: The Modern Async I/O Interface

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    io_uring: MODERN ASYNC I/O                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   io_uring (Linux 5.1+) provides truly asynchronous I/O:                  │
│                                                                            │
│   KEY FEATURES:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Zero-copy submission/completion using shared memory rings              │
│   • Batching: multiple operations per system call                         │
│   • Kernel-side polling (SQPOLL) eliminates syscalls entirely            │
│   • Unified interface for files, sockets, timers, and more               │
│   • True kernel async I/O (not user-space threads like POSIX AIO)        │
│                                                                            │
│                                                                            │
│   ARCHITECTURE:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                         USER SPACE                                  │  │
│   │                                                                     │  │
│   │   ┌─────────────────────┐         ┌─────────────────────┐          │  │
│   │   │  Submission Queue   │         │  Completion Queue   │          │  │
│   │   │       (SQ)          │         │       (CQ)          │          │  │
│   │   │                     │         │                     │          │  │
│   │   │ ┌───┬───┬───┬───┐  │         │ ┌───┬───┬───┬───┐  │          │  │
│   │   │ │ 0 │ 1 │ 2 │...│  │         │ │ 0 │ 1 │ 2 │...│  │          │  │
│   │   │ └─┬─┴─┬─┴───┴───┘  │         │ └───┴───┴───┴───┘  │          │  │
│   │   │   │   │             │         │         ▲          │          │  │
│   │   └───┼───┼─────────────┘         └─────────┼──────────┘          │  │
│   │       │   │                                  │                     │  │
│   │───────┼───┼──────────────────────────────────┼─────────────────────│  │
│   │       ▼   ▼                                  │                     │  │
│   │       SHARED MEMORY (mmap'd rings)                                 │  │
│   │───────────────────────────────────────────────────────────────────│  │
│   │                                                                     │  │
│   │                        KERNEL SPACE                                 │  │
│   │                                                                     │  │
│   │   io_uring_enter()                                                 │  │
│   │        │                                                            │  │
│   │        ▼                                                            │  │
│   │   ┌─────────────────────────────────────────────────────────┐      │  │
│   │   │              io_uring Worker Threads                     │      │  │
│   │   │                                                          │      │  │
│   │   │   Process SQEs → Perform I/O → Generate CQEs            │      │  │
│   │   └─────────────────────────────────────────────────────────┘      │  │
│   │                                                                     │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### io_uring Usage Example

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    io_uring USAGE EXAMPLE                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <liburing.h>                                                    │
│                                                                            │
│   struct io_uring ring;                                                    │
│                                                                            │
│   /* Setup io_uring with 32 entries */                                    │
│   io_uring_queue_init(32, &ring, 0);                                      │
│                                                                            │
│   /* Get a submission queue entry (SQE) */                                │
│   struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);                     │
│                                                                            │
│   /* Prepare a read operation */                                           │
│   io_uring_prep_read(sqe, fd, buf, count, offset);                        │
│   io_uring_sqe_set_data(sqe, user_data);  /* Attach user data */          │
│                                                                            │
│   /* Submit (can batch multiple SQEs before submitting) */                │
│   io_uring_submit(&ring);                                                 │
│                                                                            │
│   /* Wait for completion */                                                │
│   struct io_uring_cqe *cqe;                                               │
│   io_uring_wait_cqe(&ring, &cqe);                                         │
│                                                                            │
│   /* Process result */                                                     │
│   int result = cqe->res;        /* Bytes read or error */                 │
│   void *data = io_uring_cqe_get_data(cqe);                                │
│                                                                            │
│   /* Mark completion as seen */                                            │
│   io_uring_cqe_seen(&ring, cqe);                                          │
│                                                                            │
│   /* Cleanup */                                                            │
│   io_uring_queue_exit(&ring);                                             │
│                                                                            │
│                                                                            │
│   SUPPORTED OPERATIONS:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│   • IORING_OP_READ, IORING_OP_WRITE                                       │
│   • IORING_OP_READV, IORING_OP_WRITEV                                     │
│   • IORING_OP_FSYNC, IORING_OP_FDATASYNC                                  │
│   • IORING_OP_ACCEPT, IORING_OP_CONNECT                                   │
│   • IORING_OP_SEND, IORING_OP_RECV                                        │
│   • IORING_OP_TIMEOUT, IORING_OP_POLL_ADD                                 │
│   • IORING_OP_OPENAT, IORING_OP_CLOSE                                     │
│   • And many more...                                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Direct I/O (O_DIRECT)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DIRECT I/O (O_DIRECT)                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   O_DIRECT bypasses the page cache for direct disk access:               │
│                                                                            │
│                                                                            │
│   NORMAL I/O:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   User Buffer  ──copy──►  Page Cache  ──writeback──►  Disk                │
│                                                                            │
│   • Double buffering (user buffer + page cache)                           │
│   • Kernel manages caching, readahead, writeback                         │
│   • Good for general-purpose I/O                                          │
│                                                                            │
│                                                                            │
│   DIRECT I/O (O_DIRECT):                                                   │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   User Buffer  ─────────────────direct──────────────►  Disk               │
│                                                                            │
│   • Zero-copy: data goes directly to/from user buffer                    │
│   • Application manages its own caching                                   │
│   • Good for databases that do their own cache management                │
│                                                                            │
│                                                                            │
│   REQUIREMENTS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Buffer must be aligned (typically 512 bytes or filesystem block)     │
│   • Transfer size must be multiple of alignment                          │
│   • File offset must be aligned                                           │
│                                                                            │
│   int fd = open("/dev/sda", O_RDONLY | O_DIRECT);                         │
│   void *buf;                                                               │
│   posix_memalign(&buf, 4096, size);  /* Aligned allocation */            │
│   read(fd, buf, size);                /* size must be aligned */         │
│                                                                            │
│                                                                            │
│   USE CASES:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   • Databases (PostgreSQL, MySQL InnoDB)                                  │
│   • Custom caching applications                                           │
│   • Real-time systems needing predictable latency                        │
│   • Memory-constrained systems                                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Memory-Mapped I/O (mmap)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMORY-MAPPED I/O (mmap)                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   mmap() maps file contents directly into process address space:          │
│                                                                            │
│   void *mmap(void *addr, size_t length, int prot, int flags,             │
│              int fd, off_t offset);                                        │
│                                                                            │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     PROCESS VIRTUAL MEMORY                           │ │
│   │                                                                      │ │
│   │   ┌───────────┬───────────┬───────────┬───────────────────────────┐ │ │
│   │   │   Text    │   Data    │   Heap    │         mmap'd region     │ │ │
│   │   │           │           │           │                           │ │ │
│   │   └───────────┴───────────┴───────────┴─────────────┬─────────────┘ │ │
│   │                                                      │               │ │
│   │                                              Page Table               │ │
│   │                                                      │               │ │
│   │                                                      ▼               │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                       PAGE CACHE                              │  │ │
│   │   │                                                               │  │ │
│   │   │   ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐     │  │ │
│   │   │   │Page 0 │  │Page 1 │  │Page 2 │  │Page 3 │  │Page 4 │     │  │ │
│   │   │   └───────┘  └───────┘  └───────┘  └───────┘  └───────┘     │  │ │
│   │   │       │          │          │          │          │          │  │ │
│   │   └───────┼──────────┼──────────┼──────────┼──────────┼──────────┘  │ │
│   │           │          │          │          │          │              │ │
│   │           ▼          ▼          ▼          ▼          ▼              │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │                         FILE ON DISK                          │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│                                                                            │
│   EXAMPLE:                                                                 │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   int fd = open("file.dat", O_RDWR);                                      │
│   struct stat sb;                                                          │
│   fstat(fd, &sb);                                                          │
│                                                                            │
│   char *data = mmap(NULL, sb.st_size, PROT_READ | PROT_WRITE,             │
│                     MAP_SHARED, fd, 0);                                    │
│                                                                            │
│   /* Access file like memory - no read()/write() needed! */               │
│   data[0] = 'H';                                                          │
│   data[1] = 'i';                                                          │
│   printf("%s\n", data);                                                   │
│                                                                            │
│   munmap(data, sb.st_size);                                               │
│   close(fd);                                                               │
│                                                                            │
│                                                                            │
│   ADVANTAGES:                                                              │
│   • No system calls for data access after mmap()                         │
│   • Shared between processes (MAP_SHARED)                                 │
│   • Zero-copy (data read directly from page cache)                       │
│   • Lazy loading (pages loaded on demand via page faults)                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Splice, Tee, and Copy File Range

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY DATA MOVEMENT                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   splice(), tee(), and copy_file_range() move data without copying       │
│   through user space:                                                      │
│                                                                            │
│                                                                            │
│   splice() - Move data between pipe and file descriptor:                  │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ssize_t splice(int fd_in, loff_t *off_in,                               │
│                  int fd_out, loff_t *off_out,                              │
│                  size_t len, unsigned int flags);                          │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │   TRADITIONAL COPY:                                              │    │
│   │   File ──read()──► User Buffer ──write()──► Socket               │    │
│   │         (copy)                    (copy)                          │    │
│   │                                                                   │    │
│   │   WITH splice():                                                  │    │
│   │   File ──splice()──► Pipe ──splice()──► Socket                   │    │
│   │         (no copy, just page reference)                            │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   Example (file to socket):                                                │
│   int pipefd[2];                                                           │
│   pipe(pipefd);                                                            │
│   splice(file_fd, NULL, pipefd[1], NULL, len, 0);  /* file → pipe */      │
│   splice(pipefd[0], NULL, socket_fd, NULL, len, 0); /* pipe → socket */   │
│                                                                            │
│                                                                            │
│   tee() - Duplicate pipe data without consuming:                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ssize_t tee(int fd_in, int fd_out, size_t len, unsigned int flags);     │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                                                                   │    │
│   │   Pipe 1  ───tee()───►  Pipe 2                                   │    │
│   │     │                      │                                      │    │
│   │     │                      │                                      │    │
│   │     ▼                      ▼                                      │    │
│   │   Output 1             Output 2                                   │    │
│   │                                                                   │    │
│   │   Data is NOT consumed from Pipe 1 (duplicated)                  │    │
│   │                                                                   │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│                                                                            │
│   copy_file_range() - Copy between files in kernel:                       │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   ssize_t copy_file_range(int fd_in, loff_t *off_in,                      │
│                           int fd_out, loff_t *off_out,                     │
│                           size_t len, unsigned int flags);                 │
│                                                                            │
│   • Copy data between files without going through user space              │
│   • Can use filesystem-specific optimizations (reflinks, server-side)    │
│   • Works across different filesystems                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Summary and Appendix

### I/O System Calls Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    I/O SYSTEM CALLS QUICK REFERENCE                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BASIC FILE I/O:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│   open()           Open a file                                             │
│   close()          Close a file descriptor                                 │
│   read()           Read from file descriptor                              │
│   write()          Write to file descriptor                               │
│   lseek()          Reposition file offset                                 │
│   fsync()          Synchronize file to disk                               │
│   fdatasync()      Sync data (not metadata)                               │
│                                                                            │
│                                                                            │
│   POSITIONED I/O:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│   pread()          Read at offset (no position change)                    │
│   pwrite()         Write at offset (no position change)                   │
│                                                                            │
│                                                                            │
│   VECTORED I/O:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│   readv()          Read into multiple buffers                             │
│   writev()         Write from multiple buffers                            │
│   preadv()         Positioned vectored read                               │
│   pwritev()        Positioned vectored write                              │
│   preadv2()        Positioned vectored read with flags                    │
│   pwritev2()       Positioned vectored write with flags                   │
│                                                                            │
│                                                                            │
│   MEMORY-MAPPED I/O:                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│   mmap()           Map file into memory                                   │
│   munmap()         Unmap memory region                                    │
│   msync()          Sync mapped memory to file                             │
│   madvise()        Advise kernel about memory usage                       │
│   mlock()          Lock pages in memory                                   │
│                                                                            │
│                                                                            │
│   ZERO-COPY:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   sendfile()       Transfer between file descriptors                      │
│   splice()         Move data to/from pipe                                 │
│   tee()            Duplicate pipe data                                    │
│   copy_file_range() Copy between files in kernel                          │
│                                                                            │
│                                                                            │
│   ASYNCHRONOUS:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│   io_uring_setup()    Setup io_uring context                              │
│   io_uring_enter()    Submit/wait for I/O                                 │
│   io_uring_register() Register buffers/files                              │
│                                                                            │
│                                                                            │
│   DEVICE CONTROL:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│   ioctl()          Device-specific operations                             │
│   fcntl()          File descriptor operations                             │
│   poll()           Wait for events on multiple fds                        │
│   select()         Synchronous I/O multiplexing                           │
│   epoll_*()        Scalable I/O multiplexing                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE I/O SUBSYSTEM: THE BIG PICTURE                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         USER SPACE                                   │ │
│   │                                                                      │ │
│   │   Application                                                        │ │
│   │       │                                                              │ │
│   │       │  read(), write(), mmap(), ioctl(), io_uring_enter()         │ │
│   │       ▼                                                              │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                       │
│   ═══════════════════════════════════════════════════════════════════════ │
│                            System Call Interface                           │
│   ═══════════════════════════════════════════════════════════════════════ │
│                                    │                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                       VIRTUAL FILE SYSTEM                            │ │
│   │   • Uniform interface       • Dentry cache                          │ │
│   │   • Inode cache             • File operations dispatch              │ │
│   └────────────────────────────────┬────────────────────────────────────┘ │
│            ┌───────────────────────┼───────────────────────┐              │
│            │                       │                       │              │
│            ▼                       ▼                       ▼              │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│   │   Filesystem    │    │   Filesystem    │    │    Network      │      │
│   │   (ext4, XFS)   │    │   (tmpfs, proc) │    │    Stack        │      │
│   └────────┬────────┘    └─────────────────┘    └────────┬────────┘      │
│            │                                              │               │
│            ▼                                              │               │
│   ┌─────────────────────────────────────────────────┐    │               │
│   │              PAGE CACHE                          │    │               │
│   │   • Caches file data in memory                   │    │               │
│   │   • Manages dirty pages and writeback            │    │               │
│   │   • Indexed by (inode, offset)                   │    │               │
│   └────────────────────┬────────────────────────────┘    │               │
│                        │                                  │               │
│                        ▼                                  │               │
│   ┌─────────────────────────────────────────────────┐    │               │
│   │              BLOCK LAYER                         │    │               │
│   │   • Block I/O requests (struct bio)              │    │               │
│   │   • I/O scheduling                               │    │               │
│   │   • Request merging                              │    │               │
│   └────────────────────┬────────────────────────────┘    │               │
│                        │                                  │               │
│            ┌───────────┴───────────┐                     │               │
│            ▼                       ▼                     ▼               │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│   │  Block Device   │    │  Block Device   │    │ Network Device  │      │
│   │    Driver       │    │    Driver       │    │    Driver       │      │
│   │  (SCSI, NVMe)   │    │  (virtio-blk)   │    │  (e1000, ixgbe) │      │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘      │
│            │                      │                      │               │
│   ═════════╪══════════════════════╪══════════════════════╪═══════════════ │
│            │          Hardware Interface                 │               │
│   ═════════╪══════════════════════╪══════════════════════╪═══════════════ │
│            │                      │                      │               │
│            ▼                      ▼                      ▼               │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│   │    SSD/HDD      │    │   Virtual Disk  │    │      NIC        │      │
│   │                 │    │                 │    │                 │      │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 13. References

### Books

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED READING                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FOUNDATIONAL:                                                            │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Bach, Maurice J.                                                       │
│     "The Design of the UNIX Operating System" (1986)                      │
│     - The definitive reference for traditional UNIX I/O subsystem         │
│     - Buffer cache algorithms and device drivers                          │
│                                                                            │
│   • Bovet, Daniel P. & Cesati, Marco                                      │
│     "Understanding the Linux Kernel" (3rd Edition, 2005)                  │
│     - Deep dive into Linux kernel internals                               │
│     - VFS, page cache, block I/O layer                                    │
│                                                                            │
│                                                                            │
│   PRACTICAL:                                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Stevens, W. Richard & Rago, Stephen A.                                │
│     "Advanced Programming in the UNIX Environment" (3rd Edition)          │
│     - System call interfaces and programming                              │
│     - Terminal I/O, advanced I/O                                          │
│                                                                            │
│   • Kerrisk, Michael                                                       │
│     "The Linux Programming Interface" (2010)                              │
│     - Comprehensive Linux/UNIX system programming                         │
│     - File I/O, signals, memory mappings                                  │
│                                                                            │
│   • Love, Robert                                                           │
│     "Linux Kernel Development" (3rd Edition)                              │
│     - Modern Linux kernel internals                                       │
│     - Block I/O layer, VFS, memory management                             │
│                                                                            │
│                                                                            │
│   DEVICE DRIVERS:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│                                                                            │
│   • Corbet, Jonathan; Rubini, Alessandro; Kroah-Hartman, Greg             │
│     "Linux Device Drivers" (3rd Edition)                                  │
│     - Character and block device drivers                                  │
│     - DMA, memory mapping, interrupts                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Source Files

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KEY KERNEL SOURCE FILES                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   VFS AND FILE I/O:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│   fs/read_write.c          read(), write(), pread(), pwrite()            │
│   fs/open.c                open(), close()                                │
│   fs/file_table.c          File table management                          │
│   fs/namei.c               Path name lookup                               │
│   fs/dcache.c              Directory entry cache                          │
│   fs/inode.c               Inode operations                               │
│   include/linux/fs.h       VFS structures and definitions                 │
│                                                                            │
│                                                                            │
│   PAGE CACHE:                                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│   mm/filemap.c             Page cache core operations                     │
│   mm/readahead.c           Readahead logic                                │
│   mm/page-writeback.c      Dirty page writeback                          │
│   include/linux/pagemap.h  Page cache definitions                         │
│                                                                            │
│                                                                            │
│   BLOCK LAYER:                                                             │
│   ─────────────────────────────────────────────────────────────────────   │
│   block/bio.c              Block I/O (struct bio)                        │
│   block/blk-core.c         Block layer core                               │
│   block/blk-mq.c           Multi-queue block layer                        │
│   block/elevator.c         I/O scheduler framework                        │
│   block/mq-deadline.c      mq-deadline scheduler                          │
│   block/bfq-iosched.c      BFQ scheduler                                  │
│   include/linux/blkdev.h   Block device definitions                       │
│   include/linux/bio.h      Block I/O definitions                          │
│                                                                            │
│                                                                            │
│   DEVICE DRIVERS:                                                          │
│   ─────────────────────────────────────────────────────────────────────   │
│   drivers/block/           Block device drivers                           │
│   drivers/char/            Character device drivers                       │
│   drivers/tty/             TTY/terminal drivers                           │
│   drivers/nvme/            NVMe drivers                                   │
│   drivers/scsi/            SCSI drivers                                   │
│                                                                            │
│                                                                            │
│   DMA:                                                                     │
│   ─────────────────────────────────────────────────────────────────────   │
│   kernel/dma/              DMA subsystem                                  │
│   include/linux/dma-mapping.h  DMA API                                    │
│                                                                            │
│                                                                            │
│   MODERN ASYNC I/O:                                                        │
│   ─────────────────────────────────────────────────────────────────────   │
│   io_uring/io_uring.c      io_uring implementation                        │
│   io_uring/rw.c            io_uring read/write                            │
│   include/uapi/linux/io_uring.h  io_uring user API                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Man Pages

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ESSENTIAL MAN PAGES                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SECTION 2 (SYSTEM CALLS):                                               │
│   ─────────────────────────────────────────────────────────────────────   │
│   open(2)         Opening files                                           │
│   close(2)        Closing file descriptors                                │
│   read(2)         Reading from files                                      │
│   write(2)        Writing to files                                        │
│   lseek(2)        Repositioning file offset                              │
│   pread(2)        Positioned read                                         │
│   pwrite(2)       Positioned write                                        │
│   readv(2)        Vectored read                                           │
│   writev(2)       Vectored write                                          │
│   mmap(2)         Memory mapping                                          │
│   munmap(2)       Unmapping memory                                        │
│   msync(2)        Synchronize mapped memory                              │
│   fsync(2)        Synchronize file to disk                               │
│   fdatasync(2)    Synchronize file data                                  │
│   ioctl(2)        Device control                                          │
│   fcntl(2)        File descriptor manipulation                           │
│   select(2)       I/O multiplexing                                       │
│   poll(2)         I/O multiplexing                                       │
│   splice(2)       Zero-copy data transfer                                │
│   tee(2)          Duplicate pipe data                                    │
│   sendfile(2)     Transfer between file descriptors                      │
│   copy_file_range(2)  Copy between files                                 │
│   io_uring_setup(2)   Setup io_uring                                     │
│   io_uring_enter(2)   Submit/wait io_uring                               │
│                                                                            │
│   SECTION 7 (MISCELLANEOUS):                                              │
│   ─────────────────────────────────────────────────────────────────────   │
│   epoll(7)        Scalable I/O event notification                        │
│   io_uring(7)     Modern async I/O interface                             │
│   aio(7)          POSIX asynchronous I/O                                 │
│   pipe(7)         Pipe semantics                                          │
│   pty(7)          Pseudo-terminal interfaces                             │
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
│   ─────────────────────────────────────────────────────────────────────   │
│   • kernel.org/doc/html/latest/                                           │
│     - Official Linux kernel documentation                                 │
│   • kernel.org/doc/html/latest/filesystems/                              │
│     - Filesystem and VFS documentation                                    │
│   • kernel.org/doc/html/latest/block/                                    │
│     - Block layer documentation                                           │
│   • kernel.org/doc/html/latest/driver-api/                               │
│     - Device driver API                                                   │
│                                                                            │
│                                                                            │
│   SOURCE CODE BROWSERS:                                                    │
│   ─────────────────────────────────────────────────────────────────────   │
│   • elixir.bootlin.com/linux/latest/source                               │
│     - Cross-referenced Linux kernel source                                │
│   • github.com/torvalds/linux                                            │
│     - Official Linux kernel repository                                    │
│                                                                            │
│                                                                            │
│   ARTICLES AND TUTORIALS:                                                  │
│   ─────────────────────────────────────────────────────────────────────   │
│   • lwn.net                                                               │
│     - Linux Weekly News - excellent kernel articles                       │
│     - In-depth coverage of io_uring, block layer, VFS                    │
│   • kernelnewbies.org                                                     │
│     - Getting started with kernel development                             │
│   • linux-kernel-labs.github.io                                          │
│     - Kernel development labs and tutorials                              │
│                                                                            │
│                                                                            │
│   io_uring SPECIFIC:                                                       │
│   ─────────────────────────────────────────────────────────────────────   │
│   • kernel.dk/io_uring.pdf                                               │
│     - io_uring design document by Jens Axboe                             │
│   • github.com/axboe/liburing                                            │
│     - io_uring library and examples                                      │
│   • unixism.net/loti/                                                    │
│     - Lord of the io_uring tutorial                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

_The I/O Subsystem is the bridge between the abstract world of files and processes
and the concrete world of hardware devices. From Bach's buffer cache to modern
io_uring, the evolution of I/O in Unix reflects the constant pursuit of performance
while maintaining the elegance of the "everything is a file" philosophy._
