# Zero-Copy Mechanisms in Unix/Linux Systems

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Kernel Internals, Memory Management, DMA, System Calls, and Performance Optimization

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The Data Copy Problem](#the-data-copy-problem)
   - [What is Zero-Copy?](#what-is-zero-copy)
   - [Historical Context](#historical-context)
   - [Document Organization](#document-organization)

2. [Fundamental Concepts](#2-fundamental-concepts)
   - [User Space vs Kernel Space](#user-space-vs-kernel-space)
   - [Virtual Memory and Page Tables](#virtual-memory-and-page-tables)
   - [DMA (Direct Memory Access)](#dma-direct-memory-access)
   - [Buffer Cache and Page Cache](#buffer-cache-and-page-cache)
   - [Memory-Mapped I/O](#memory-mapped-io)

3. [The Traditional I/O Path](#3-the-traditional-io-path)
   - [Reading a File: The Costly Journey](#reading-a-file-the-costly-journey)
   - [Sending Data Over Network: Double Trouble](#sending-data-over-network-double-trouble)
   - [Context Switches and Their Cost](#context-switches-and-their-cost)
   - [CPU Cache Pollution](#cpu-cache-pollution)

4. [Zero-Copy Techniques](#4-zero-copy-techniques)
   - [mmap() + write()](#mmap--write)
   - [sendfile()](#sendfile)
   - [sendfile() with DMA Scatter-Gather](#sendfile-with-dma-scatter-gather)
   - [splice() and tee()](#splice-and-tee)
   - [vmsplice()](#vmsplice)
   - [copy_file_range()](#copy_file_range)
   - [io_uring with Fixed Buffers](#io_uring-with-fixed-buffers)

5. [sendfile() Deep Dive](#5-sendfile-deep-dive)
   - [System Call Interface](#system-call-interface)
   - [Kernel Implementation](#kernel-implementation)
   - [The Page Cache Role](#the-page-cache-role)
   - [DMA and Network Stack Integration](#dma-and-network-stack-integration)
   - [Limitations and Edge Cases](#limitations-and-edge-cases)

6. [splice() Deep Dive](#6-splice-deep-dive)
   - [The Pipe Buffer Abstraction](#the-pipe-buffer-abstraction)
   - [splice() System Call](#splice-system-call)
   - [tee() System Call](#tee-system-call)
   - [vmsplice() System Call](#vmsplice-system-call)
   - [Building Zero-Copy Pipelines](#building-zero-copy-pipelines)

7. [Memory Mapping (mmap)](#7-memory-mapping-mmap)
   - [How mmap() Works](#how-mmap-works)
   - [Page Fault Handling](#page-fault-handling)
   - [Shared vs Private Mappings](#shared-vs-private-mappings)
   - [mmap() for Zero-Copy I/O](#mmap-for-zero-copy-io)
   - [Pitfalls and Considerations](#pitfalls-and-considerations)

8. [DMA and Hardware Support](#8-dma-and-hardware-support)
   - [DMA Controller Architecture](#dma-controller-architecture)
   - [Scatter-Gather DMA](#scatter-gather-dma)
   - [IOMMU and DMA Remapping](#iommu-and-dma-remapping)
   - [Network Interface Cards](#network-interface-cards)
   - [NVMe and Modern Storage](#nvme-and-modern-storage)

9. [Network Stack Zero-Copy](#9-network-stack-zero-copy)
   - [Socket Buffer (sk_buff) Architecture](#socket-buffer-sk_buff-architecture)
   - [TCP Zero-Copy Send](#tcp-zero-copy-send)
   - [TCP Zero-Copy Receive](#tcp-zero-copy-receive)
   - [MSG_ZEROCOPY Flag](#msg_zerocopy-flag)
   - [AF_XDP and eBPF](#af_xdp-and-ebpf)

10. [Kernel Data Structures](#10-kernel-data-structures)
    - [struct page](#struct-page)
    - [struct bio](#struct-bio)
    - [struct sk_buff](#struct-sk_buff)
    - [struct pipe_buffer](#struct-pipe_buffer)
    - [Page Reference Counting](#page-reference-counting)

11. [Real-World Applications](#11-real-world-applications)
    - [Web Servers (nginx, Apache)](#web-servers-nginx-apache)
    - [Databases (PostgreSQL, MySQL)](#databases-postgresql-mysql)
    - [Message Queues (Kafka)](#message-queues-kafka)
    - [Video Streaming](#video-streaming)
    - [File Servers (Samba, NFS)](#file-servers-samba-nfs)

12. [Performance Analysis](#12-performance-analysis)
    - [Benchmarking Methodology](#benchmarking-methodology)
    - [Throughput Comparisons](#throughput-comparisons)
    - [CPU Utilization](#cpu-utilization)
    - [Latency Considerations](#latency-considerations)
    - [When Zero-Copy Hurts](#when-zero-copy-hurts)

13. [Practical Implementation](#13-practical-implementation)
    - [Building a Zero-Copy File Server](#building-a-zero-copy-file-server)
    - [Error Handling Patterns](#error-handling-patterns)
    - [Fallback Strategies](#fallback-strategies)
    - [Platform Portability](#platform-portability)

14. [Summary and Appendix](#14-summary-and-appendix)
    - [Zero-Copy Decision Tree](#zero-copy-decision-tree)
    - [System Call Quick Reference](#system-call-quick-reference)
    - [Performance Comparison Table](#performance-comparison-table)
    - [The Big Picture](#the-big-picture)

15. [References](#15-references)

---

## 1. Introduction

### The Data Copy Problem

In traditional Unix I/O, data takes a long and expensive journey. Consider a simple web server sending a 
static file to a client:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE TRADITIONAL FILE TRANSFER PROBLEM                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   APPLICATION CODE:                                                        │
│   ─────────────────                                                        │
│   char buffer[64KB];                                                       │
│   read(file_fd, buffer, 64KB);    // Read from disk                       │
│   write(socket_fd, buffer, 64KB); // Send to network                      │
│                                                                            │
│   WHAT ACTUALLY HAPPENS:                                                   │
│   ──────────────────────                                                   │
│                                                                            │
│   ┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐    │
│   │  DISK   │────►│ KERNEL      │────►│ USER SPACE  │────►│ KERNEL  │    │
│   │         │     │ PAGE CACHE  │     │ BUFFER      │     │ SOCKET  │    │
│   │         │     │             │     │             │     │ BUFFER  │    │
│   └─────────┘     └─────────────┘     └─────────────┘     └────┬────┘    │
│       │                 │                   │                   │         │
│       │    DMA COPY     │    CPU COPY       │    CPU COPY       │         │
│       │    (Copy 1)     │    (Copy 2)       │    (Copy 3)       │         │
│       ▼                 ▼                   ▼                   ▼         │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                         NETWORK CARD                             │    │
│   │                         (DMA Copy 4)                             │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   TOTAL: 4 DATA COPIES + 4 CONTEXT SWITCHES                               │
│                                                                            │


Let's trace each step in detail:

```

```

┌───────────────────────────────────────────────────────────────────────────┐
│                    STEP-BY-STEP: TRADITIONAL read() + write()              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   STEP 1: read(file_fd, buffer, size)                                     │
│   ────────────────────────────────────                                     │
│                                                                            │
│   User Process                    Kernel                                   │
│   ────────────                    ──────                                   │
│        │                             │                                     │
│        │  read() syscall             │                                     │
│        │ ──────────────────────────► │                                     │
│        │                             │                                     │
│        │  [CONTEXT SWITCH 1]         │                                     │
│        │                             │                                     │
│        │                             │  Check page cache                   │
│        │                             │  ┌─────────────────┐                │
│        │                             │  │ Page in cache?  │                │
│        │                             │  └────────┬────────┘                │
│        │                             │           │                         │
│        │                             │     NO    │    YES                  │
│        │                             │     ▼     │     │                   │
│        │                             │  ┌────────┴──┐  │                   │
│        │                             │  │ DMA from  │  │                   │
│        │                             │  │ disk to   │  │                   │
│        │                             │  │ page cache│  │                   │
│        │                             │  │ (COPY 1)  │  │                   │
│        │                             │  └───────────┘  │                   │
│        │                             │           │     │                   │
│        │                             │           ▼     ▼                   │
│        │                             │  ┌─────────────────┐                │
│        │                             │  │ CPU copy from   │                │
│        │                             │  │ page cache to   │                │
│        │                             │  │ user buffer     │                │
│        │                             │  │ (COPY 2)        │                │
│        │                             │  └─────────────────┘                │
│        │                             │           │                         │
│        │  [CONTEXT SWITCH 2]         │           │                         │
│        │ ◄────────────────────────── │ ◄─────────┘                         │
│        │  return bytes_read          │                                     │
│        │                             │                                     │
│                                                                            │
│   STEP 2: write(socket_fd, buffer, size)                                  │
│   ──────────────────────────────────────                                   │
│                                                                            │
│   User Process                    Kernel                                   │
│   ────────────                    ──────                                   │
│        │                             │                                     │
│        │  write() syscall            │                                     │
│        │ ──────────────────────────► │                                     │
│        │                             │                                     │
│        │  [CONTEXT SWITCH 3]         │                                     │
│        │                             │                                     │
│        │                             │  ┌─────────────────┐                │
│        │                             │  │ CPU copy from   │                │
│        │                             │  │ user buffer to  │                │
│        │                             │  │ socket buffer   │                │
│        │                             │  │ (COPY 3)        │                │
│        │                             │  └─────────────────┘                │
│        │                             │           │                         │
│        │                             │           ▼                         │
│        │                             │  ┌─────────────────┐                │
│        │                             │  │ TCP/IP stack    │                │
│        │                             │  │ adds headers    │                │
│        │                             │  └─────────────────┘                │
│        │                             │           │                         │
│        │                             │           ▼                         │
│        │                             │  ┌─────────────────┐                │
│        │                             │  │ DMA from socket │                │
│        │                             │  │ buffer to NIC   │                │
│        │                             │  │ (COPY 4)        │                │
│        │                             │  └─────────────────┘                │
│        │                             │           │                         │
│        │  [CONTEXT SWITCH 4]         │           │                         │
│        │ ◄────────────────────────── │ ◄─────────┘                         │
│        │  return bytes_written       │                                     │
│        │                             │                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**The Cost Breakdown:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         COST ANALYSIS                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   OPERATION              │ TIME (approx)  │ NOTES                         │
│   ───────────────────────┼────────────────┼─────────────────────────────  │
│   Context switch         │ 1-10 μs        │ TLB flush, cache pollution    │
│   CPU memory copy (64KB) │ 10-30 μs       │ Depends on cache state        │
│   DMA transfer (64KB)    │ 5-20 μs        │ No CPU involvement            │
│   ───────────────────────┼────────────────┼─────────────────────────────  │
│                                                                           │
│   TRADITIONAL PATH (4 copies, 4 context switches):                        │
│   ─────────────────────────────────────────────────                       │
│   • 4 context switches:     4-40 μs                                       │
│   • 2 CPU copies (64KB):    20-60 μs                                      │
│   • 2 DMA transfers:        10-40 μs                                      │
│   • TOTAL:                  ~34-140 μs per 64KB                           │
│                                                                           │
│   ADDITIONAL HIDDEN COSTS:                                                │
│   ────────────────────────                                                │
│   • CPU cache pollution (data copied through L1/L2/L3)                    │
│   • Memory bandwidth consumption                                           │
│   • TLB misses after context switches                                     │
│   • Increased memory pressure                                              │
│                                                                            │
│   AT 10 Gbps LINE RATE:                                                   │
│   ─────────────────────                                                    │
│   • Need to transfer ~1.25 GB/s                                           │
│   • With 64KB buffers: ~19,000 transfers/second                           │
│   • CPU copies alone: 380-1140 ms of CPU time per second!                │
│   • This is why zero-copy matters                                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### What is Zero-Copy?

**Zero-copy** refers to techniques that eliminate unnecessary data copies between memory regions, particularly 
between user space and kernel space. The goal is to transfer data directly from source to destination with 
minimal CPU involvement.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         ZERO-COPY DEFINITION                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TRADITIONAL I/O:                                                         │
│   ────────────────                                                         │
│                                                                            │
│   ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────┐   │
│   │ Disk │───►│ Page     │───►│ User     │───►│ Socket   │───►│ NIC │   │
│   │      │DMA │ Cache    │CPU │ Buffer   │CPU │ Buffer   │DMA │     │   │
│   └──────┘    └──────────┘    └──────────┘    └──────────┘    └─────┘   │
│                                                                            │
│              Copy 1       Copy 2       Copy 3       Copy 4                │
│                                                                            │
│   ZERO-COPY I/O (sendfile with scatter-gather DMA):                       │
│   ─────────────────────────────────────────────────                        │
│                                                                            │
│   ┌──────┐    ┌──────────┐                            ┌─────┐            │
│   │ Disk │───►│ Page     │───────────────────────────►│ NIC │            │
│   │      │DMA │ Cache    │         DMA                │     │            │
│   └──────┘    └──────────┘                            └─────┘            │
│                                                                            │
│              Copy 1                   Copy 2                               │
│                                                                            │
│   RESULT: 2 copies instead of 4, both via DMA (no CPU involvement)        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key Principles of Zero-Copy:**

1. **Avoid crossing the user-kernel boundary** - Data stays in kernel space
2. **Use DMA instead of CPU** - Let hardware do the copying
3. **Share pages instead of copying** - Reference counting, not duplication
4. **Minimize context switches** - Fewer system calls

### Historical Context

The evolution of zero-copy techniques in Unix/Linux:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY EVOLUTION TIMELINE                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1983 ─── BSD 4.2                                                        │
│            └── mmap() introduced                                          │
│                Memory-mapped files, first step toward zero-copy           │
│                                                                            │
│   1998 ─── HP-UX                                                          │
│            └── sendfile() introduced                                      │
│                First dedicated zero-copy system call                       │
│                                                                            │
│   1999 ─── Linux 2.2                                                      │
│            └── sendfile() added to Linux                                  │
│                Initially required intermediate copy                        │
│                                                                            │
│   2001 ─── Linux 2.4                                                      │
│            └── sendfile() with scatter-gather DMA                         │
│                True zero-copy with hardware support                        │
│                                                                            │
│   2006 ─── Linux 2.6.17                                                   │
│            └── splice(), tee(), vmsplice() added                          │
│                Flexible zero-copy between arbitrary fds                    │
│                                                                            │
│   2016 ─── Linux 4.6                                                      │
│            └── copy_file_range() added                                    │
│                Server-side copy for network filesystems                    │
│                                                                            │
│   2017 ─── Linux 4.14                                                     │
│            └── MSG_ZEROCOPY for sockets                                   │
│                Zero-copy send() for TCP/UDP                               │
│                                                                            │
│   2019 ─── Linux 5.1                                                      │
│            └── io_uring introduced                                        │
│                Async I/O with registered buffers                          │
│                                                                            │
│   2020 ─── Linux 5.6                                                      │
│            └── io_uring fixed buffers                                     │
│                Pre-registered buffers for true zero-copy                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Document Organization

This document follows the structure established by Maurice Bach, proceeding from fundamental concepts through 
system call implementation to practical application:

1. **Fundamental Concepts**: Memory architecture, DMA, page cache
2. **Traditional I/O Path**: Understanding what we're optimizing
3. **Zero-Copy Techniques**: Each mechanism in detail
4. **Kernel Data Structures**: The structures that enable zero-copy
5. **Real-World Applications**: How production systems use zero-copy
6. **Practical Implementation**: Building zero-copy applications

---

## 2. Fundamental Concepts

### User Space vs Kernel Space

The separation between user space and kernel space is fundamental to understanding why zero-copy matters:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MEMORY SPACE SEPARATION                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   VIRTUAL ADDRESS SPACE (64-bit Linux):                                   │
│   ─────────────────────────────────────                                    │
│                                                                            │
│   0xFFFFFFFFFFFFFFFF ┌─────────────────────────────────────┐              │
│                      │                                     │              │
│                      │         KERNEL SPACE                │              │
│                      │                                     │              │
│                      │  • Page cache                       │              │
│                      │  • Socket buffers                   │              │
│                      │  • Device drivers                   │              │
│                      │  • Kernel code                      │              │
│                      │                                     │              │
│   0xFFFF800000000000 ├─────────────────────────────────────┤              │
│                      │         (Non-canonical hole)        │              │
│   0x00007FFFFFFFFFFF ├─────────────────────────────────────┤              │
│                      │                                     │              │
│                      │         USER SPACE                  │              │
│                      │                                     │              │
│                      │  • Application code                 │              │
│                      │  • Application data                 │              │
│                      │  • Heap, stack                      │              │
│                      │  • Memory-mapped files              │              │
│                      │                                     │              │
│   0x0000000000000000 └─────────────────────────────────────┘              │
│                                                                            │
│   WHY THIS MATTERS FOR ZERO-COPY:                                         │
│   ────────────────────────────────                                         │
│                                                                            │
│   • User space CANNOT directly access kernel memory                       │
│   • Every read()/write() crosses this boundary                            │
│   • Crossing requires: context switch + data copy                         │
│   • Zero-copy avoids crossing by keeping data in kernel                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Virtual Memory and Page Tables

Understanding virtual memory is crucial for zero-copy, as many techniques rely on page table manipulation:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    VIRTUAL MEMORY ARCHITECTURE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   VIRTUAL TO PHYSICAL MAPPING:                                            │
│   ─────────────────────────────                                            │
│                                                                            │
│   Process A                    Physical Memory                             │
│   ─────────                    ───────────────                             │
│   ┌─────────────┐                                                         │
│   │ Virtual     │              ┌─────────────┐                            │
│   │ Page 0      │─────────────►│ Phys Frame  │                            │
│   ├─────────────┤              │ 0x1000      │                            │
│   │ Virtual     │              └─────────────┘                            │
│   │ Page 1      │──┐                                                      │
│   ├─────────────┤  │           ┌─────────────┐                            │
│   │ Virtual     │  └──────────►│ Phys Frame  │◄──┐                        │
│   │ Page 2      │──┐           │ 0x5000      │   │                        │
│   └─────────────┘  │           └─────────────┘   │                        │
│                    │                              │                        │
│   Process B        │           ┌─────────────┐   │                        │
│   ─────────        │           │ Phys Frame  │   │                        │
│   ┌─────────────┐  └──────────►│ 0x8000      │   │                        │
│   │ Virtual     │              └─────────────┘   │                        │
│   │ Page 0      │──────────────────────────────┘                         │
│   └─────────────┘                                                         │
│                                                                            │
│   KEY INSIGHT: Multiple virtual pages can map to SAME physical frame     │
│   This enables zero-copy through page sharing!                            │
│                                                                            │
│   PAGE TABLE ENTRY (x86-64):                                              │
│   ──────────────────────────                                               │
│   ┌────┬────┬───┬───┬───┬───┬───┬───┬────────────────────────────────┐   │
│   │ NX │ .. │ G │ D │ A │PCD│PWT│U/S│ Physical Frame Number (PFN)    │   │
│   └────┴────┴───┴───┴───┴───┴───┴───┴────────────────────────────────┘   │
│   63   62   8   7   6   5   4   3   2   1   0                             │
│                                                                            │
│   Key bits:                                                               │
│   • P (Present): Page is in physical memory                               │
│   • R/W: Read/Write permission                                            │
│   • U/S: User/Supervisor (user space accessible?)                        │
│   • A (Accessed): Page has been read                                      │
│   • D (Dirty): Page has been written                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Copy-on-Write (COW) - A Zero-Copy Technique:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COPY-ON-WRITE MECHANISM                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   INITIAL STATE (after fork()):                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   Parent Process              Physical Memory         Child Process       │
│   ──────────────              ───────────────         ─────────────       │
│   ┌─────────────┐             ┌─────────────┐         ┌─────────────┐    │
│   │ Page 0 (RO) │────────────►│ Frame 0x100 │◄────────│ Page 0 (RO) │    │
│   ├─────────────┤             │ refcount=2  │         ├─────────────┤    │
│   │ Page 1 (RO) │────────────►├─────────────┤◄────────│ Page 1 (RO) │    │
│   ├─────────────┤             │ Frame 0x200 │         ├─────────────┤    │
│   │ Page 2 (RO) │────────────►│ refcount=2  │◄────────│ Page 2 (RO) │    │
│   └─────────────┘             ├─────────────┤         └─────────────┘    │
│                               │ Frame 0x300 │                             │
│   Both processes share        │ refcount=2  │         No data copied!    │
│   same physical pages         └─────────────┘                             │
│   (marked read-only)                                                      │
│                                                                            │
│   AFTER CHILD WRITES TO PAGE 1:                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   Parent Process              Physical Memory         Child Process       │
│   ──────────────              ───────────────         ─────────────       │
│   ┌─────────────┐             ┌─────────────┐         ┌─────────────┐    │
│   │ Page 0 (RO) │────────────►│ Frame 0x100 │◄────────│ Page 0 (RO) │    │
│   ├─────────────┤             │ refcount=2  │         ├─────────────┤    │
│   │ Page 1 (RW) │────────────►├─────────────┤         │ Page 1 (RW) │───┐│
│   ├─────────────┤             │ Frame 0x200 │         ├─────────────┤   ││
│   │ Page 2 (RO) │────────────►│ refcount=1  │◄────────│ Page 2 (RO) │   ││
│   └─────────────┘             ├─────────────┤         └─────────────┘   ││
│                               │ Frame 0x300 │                            ││
│                               │ refcount=2  │         ┌─────────────┐   ││
│                               ├─────────────┤         │ Frame 0x400 │◄──┘│
│                               │ Frame 0x400 │◄────────│ refcount=1  │    │
│                               │ (NEW COPY)  │         │ (COPIED)    │    │
│                               └─────────────┘         └─────────────┘    │
│                                                                            │
│   Only the modified page is copied - "copy on write"                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### DMA (Direct Memory Access)

DMA is the hardware foundation of zero-copy:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DMA (DIRECT MEMORY ACCESS)                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WITHOUT DMA (Programmed I/O):                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   ┌─────────┐                                                             │
│   │   CPU   │◄────────────────────────────────────────┐                   │
│   └────┬────┘                                         │                   │
│        │                                              │                   │
│        │ 1. Read byte from device                     │                   │
│        ▼                                              │                   │
│   ┌─────────┐     2. Transfer byte     ┌─────────┐   │                   │
│   │ Device  │─────────────────────────►│ Memory  │   │                   │
│   │ (Disk)  │                          │         │   │                   │
│   └─────────┘                          └─────────┘   │                   │
│        │                                              │                   │
│        └──────────────────────────────────────────────┘                   │
│                    3. Repeat for each byte                                │
│                                                                            │
│   CPU is 100% busy during entire transfer!                                │
│                                                                            │
│   WITH DMA:                                                               │
│   ─────────                                                                │
│                                                                            │
│   ┌─────────┐  1. Setup DMA    ┌─────────────┐                           │
│   │   CPU   │─────────────────►│ DMA         │                           │
│   └────┬────┘  (src, dst, len) │ Controller  │                           │
│        │                       └──────┬──────┘                           │
│        │                              │                                   │
│        │ 4. Interrupt                 │ 2. Transfer data                 │
│        │    "Transfer complete"       │    (no CPU involvement)          │
│        │                              ▼                                   │
│   ┌────┴────┐                  ┌─────────┐     ┌─────────┐              │
│   │   CPU   │                  │ Device  │────►│ Memory  │              │
│   │ (free!) │                  │ (Disk)  │     │         │              │
│   └─────────┘                  └─────────┘     └─────────┘              │
│                                                                            │
│   CPU is FREE during transfer - can do other work!                        │
│                                                                            │
│   DMA TRANSFER SETUP:                                                     │
│   ───────────────────                                                      │
│   struct dma_descriptor {                                                 │
│       void *source_addr;      // Physical address of source              │
│       void *dest_addr;        // Physical address of destination         │
│       size_t length;          // Number of bytes to transfer             │
│       uint32_t flags;         // Direction, interrupt enable, etc.       │
│   };                                                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffer Cache and Page Cache

The page cache is central to zero-copy file operations. Before diving into the architecture, let's
understand what the page cache actually is and why it exists.

**What is the Page Cache?**

The **page cache** is a region of RAM that the kernel uses to cache file data from disk. It acts as a
buffer between your application and the slow disk, dramatically speeding up file access.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         MEMORY HIERARCHY                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Speed        Component              Typical Access Time                 │
│   ─────        ─────────              ───────────────────                 │
│                                                                            │
│   FASTEST  →   CPU Registers          < 1 nanosecond                      │
│            →   L1 Cache               ~ 1 nanosecond                      │
│            →   L2 Cache               ~ 4 nanoseconds                     │
│            →   L3 Cache               ~ 12 nanoseconds                    │
│            →   RAM (Page Cache)       ~ 100 nanoseconds                   │
│   SLOWEST  →   SSD Disk               ~ 100,000 nanoseconds (100 μs)     │
│            →   HDD Disk               ~ 10,000,000 nanoseconds (10 ms)   │
│                                                                            │
│   The page cache lives in RAM - 1000x faster than SSD, 100,000x than HDD!│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Why Does the Page Cache Exist?**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      WITHOUT PAGE CACHE                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Every read() goes to disk - SLOW!                                       │
│                                                                            │
│   Application              Kernel                    Disk                 │
│       │                       │                        │                  │
│       │ read(file, buf)       │                        │                  │
│       │──────────────────────►│                        │                  │
│       │                       │  Read sectors          │                  │
│       │                       │───────────────────────►│                  │
│       │                       │                        │ (10ms for HDD!)  │
│       │                       │◄───────────────────────│                  │
│       │◄──────────────────────│                        │                  │
│       │                       │                        │                  │
│       │ read(file, buf)       │  (same file again)     │                  │
│       │──────────────────────►│                        │                  │
│       │                       │  Read AGAIN from disk! │                  │
│       │                       │───────────────────────►│                  │
│       │                       │                        │ (another 10ms!)  │
│       │                       │◄───────────────────────│                  │
│       │◄──────────────────────│                        │                  │
│                                                                            │
│   Reading the same file twice = 20ms total. Wasteful!                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                       WITH PAGE CACHE                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   First read goes to disk, subsequent reads served from RAM - FAST!       │
│                                                                            │
│   Application              Kernel                    Disk                 │
│       │                       │                        │                  │
│       │ read(file, buf)       │                        │                  │
│       │──────────────────────►│                        │                  │
│       │                       │ Check page cache       │                  │
│       │                       │ (MISS - not cached)    │                  │
│       │                       │                        │                  │
│       │                       │  Read sectors          │                  │
│       │                       │───────────────────────►│                  │
│       │                       │◄───────────────────────│                  │
│       │                       │                        │                  │
│       │                       │ Store in page cache    │                  │
│       │                       │ (keep copy in RAM)     │                  │
│       │◄──────────────────────│                        │                  │
│       │                       │                        │                  │
│       │ read(file, buf)       │  (same file again)     │                  │
│       │──────────────────────►│                        │                  │
│       │                       │ Check page cache       │                  │
│       │                       │ (HIT! Found in RAM!)   │                  │
│       │◄──────────────────────│  No disk access needed!│                  │
│       │   (100ns vs 10ms!)    │                        │                  │
│                                                                            │
│   Reading the same file twice = 10ms + 100ns ≈ 10ms total. 2x faster!    │
│   Reading it 100 times = 10ms + 99×100ns ≈ 10ms total. 100x faster!      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Page Cache in Physical Memory:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      PHYSICAL RAM LAYOUT                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Physical RAM (e.g., 16 GB)                                              │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │  ┌────────────────┐  Kernel code, data structures                 │  │
│   │  │  Kernel Space  │  (fixed, always in memory)                    │  │
│   │  └────────────────┘                                                │  │
│   │                                                                    │  │
│   │  ┌────────────────────────────────────────────────────────────┐  │  │
│   │  │                     PAGE CACHE                              │  │  │
│   │  │                                                             │  │  │
│   │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │  │  │
│   │  │  │  Page 0  │ │  Page 1  │ │  Page 2  │ │  Page 3  │      │  │  │
│   │  │  │ file.txt │ │ file.txt │ │ data.db  │ │ data.db  │      │  │  │
│   │  │  │ offset 0 │ │ off 4KB  │ │ offset 0 │ │ off 4KB  │      │  │  │
│   │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │  │  │
│   │  │                                                             │  │  │
│   │  │  These are copies of disk blocks, kept in RAM for fast     │  │  │
│   │  │  access. Each page is typically 4KB in size.               │  │  │
│   │  │                                                             │  │  │
│   │  │  The page cache grows/shrinks dynamically based on:        │  │  │
│   │  │  • Available free memory                                    │  │  │
│   │  │  • File access patterns                                     │  │  │
│   │  │  • Memory pressure from applications                        │  │  │
│   │  └────────────────────────────────────────────────────────────┘  │  │
│   │                                                                    │  │
│   │  ┌────────────────┐  Process A's heap, stack, code               │  │
│   │  │   Process A    │                                               │  │
│   │  └────────────────┘                                               │  │
│   │                                                                    │  │
│   │  ┌────────────────┐  Process B's heap, stack, code               │  │
│   │  │   Process B    │                                               │  │
│   │  └────────────────┘                                               │  │
│   │                                                                    │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Why Page Cache Matters for Zero-Copy:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                WHY PAGE CACHE MATTERS FOR ZERO-COPY                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TRADITIONAL read() + write():                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   ┌──────┐      ┌────────────┐      ┌────────────┐      ┌───────┐        │
│   │ DISK │─────►│ PAGE CACHE │─────►│ USER BUFFER│─────►│SOCKET │        │
│   └──────┘ DMA  └────────────┘ CPU  └────────────┘ CPU  └───────┘        │
│                    (in RAM)       (in RAM, app's)    (in RAM)             │
│                                                                            │
│   Data exists in 3 places in RAM simultaneously! Wasteful!                │
│                                                                            │
│                                                                            │
│   ZERO-COPY with sendfile():                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌──────┐      ┌────────────┐                              ┌───────┐    │
│   │ DISK │─────►│ PAGE CACHE │─────────────────────────────►│  NIC  │    │
│   └──────┘ DMA  └────────────┘      DMA (scatter-gather)    └───────┘    │
│                    (in RAM)                                               │
│                                                                            │
│   Data exists in only 1 place in RAM!                                     │
│   NIC reads directly from page cache pages via DMA.                       │
│   No CPU involvement in data movement!                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Simple Analogy - The Library:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         LIBRARY ANALOGY                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DISK        = Warehouse (huge storage, slow to access - far away)       │
│   PAGE CACHE  = Library shelf (smaller, fast to access - nearby)          │
│   USER BUFFER = Your desk (very small, immediate access)                  │
│                                                                            │
│   Traditional approach (read + write):                                    │
│   ────────────────────────────────────                                     │
│   1. Go to warehouse, get book              (disk read)                   │
│   2. Put book on library shelf              (store in page cache)         │
│   3. Copy book contents to your notebook    (copy to user buffer)         │
│   4. Copy from notebook to send to friend   (copy to socket buffer)       │
│                                                                            │
│   Zero-copy approach (sendfile):                                          │
│   ──────────────────────────────                                           │
│   1. Go to warehouse, get book              (disk read)                   │
│   2. Put book on library shelf              (store in page cache)         │
│   3. Friend picks up book directly from shelf! (DMA from page cache)     │
│                                                                            │
│   No copying to your desk, no copying to send - much more efficient!     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key Points About Page Cache:**

1. **Page cache = RAM used to cache disk data** - managed entirely by the kernel
2. **A "page" is typically 4KB** - the fundamental unit of memory management
3. **Kernel manages it automatically** - you don't allocate it directly
4. **It speeds up repeated file access** - first read is slow (disk), subsequent reads are fast (RAM)
5. **Zero-copy techniques share page cache pages** - instead of copying data out of them

Now let's look at the page cache architecture in more detail:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE CACHE ARCHITECTURE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   The page cache sits between user space and disk:                        │
│   ────────────────────────────────────────────────                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         USER SPACE                                   │ │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │ │
│   │  │ Process  │  │ Process  │  │ Process  │  │ Process  │           │ │
│   │  │    A     │  │    B     │  │    C     │  │    D     │           │ │
│   │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │ │
│   └───────┼─────────────┼─────────────┼─────────────┼───────────────────┘ │
│           │             │             │             │                      │
│   ════════╪═════════════╪═════════════╪═════════════╪══════════════════   │
│           │    SYSTEM CALL BOUNDARY   │             │                      │
│   ════════╪═════════════╪═════════════╪═════════════╪══════════════════   │
│           │             │             │             │                      │
│   ┌───────┴─────────────┴─────────────┴─────────────┴───────────────────┐ │
│   │                        KERNEL SPACE                                  │ │
│   │                                                                      │ │
│   │  ┌────────────────────────────────────────────────────────────────┐ │ │
│   │  │                      PAGE CACHE                                │ │ │
│   │  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐    │ │ │
│   │  │  │Page│ │Page│ │Page│ │Page│ │Page│ │Page│ │Page│ │Page│    │ │ │
│   │  │  │ 0  │ │ 1  │ │ 2  │ │ 3  │ │ 4  │ │ 5  │ │ 6  │ │ 7  │    │ │ │
│   │  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘    │ │ │
│   │  │    │       file1.txt       │  │      file2.txt       │        │ │ │
│   │  └────┼───────────────────────┼──┼──────────────────────┼────────┘ │ │
│   │       │                       │  │                      │          │ │
│   │  ┌────┴───────────────────────┴──┴──────────────────────┴────────┐ │ │
│   │  │                   BLOCK I/O LAYER                             │ │ │
│   │  └─────────────────────────────┬────────────────────────────────┘ │ │
│   │                                │                                   │ │
│   └────────────────────────────────┼───────────────────────────────────┘ │
│                                    │                                      │
│                                    ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                              DISK                                    │ │
│   │    ┌───────────────────────────────────────────────────────────┐   │ │
│   │    │  Block 0 │ Block 1 │ Block 2 │ Block 3 │ Block 4 │ ...   │   │ │
│   │    └───────────────────────────────────────────────────────────┘   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY INSIGHT: Page cache pages can be shared with:                       │
│   • Multiple processes (via mmap)                                         │
│   • Network stack (via sendfile)                                          │
│   • Other kernel subsystems (via splice)                                  │
│   This is the foundation of zero-copy!                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Page Cache Data Structures:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE CACHE DATA STRUCTURES                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct address_space {                                                  │
│       struct inode           *host;        /* Owner inode */              │
│       struct xarray          i_pages;      /* Cached pages (radix tree) */│
│       atomic_t               i_mmap_writable; /* Writable mmaps */        │
│       struct rb_root_cached  i_mmap;       /* Private & shared mappings */│
│       unsigned long          nrpages;      /* Number of pages */          │
│       const struct address_space_operations *a_ops;                       │
│   };                                                                      │
│                                                                            │
│   RADIX TREE FOR PAGE LOOKUP:                                             │
│   ───────────────────────────                                              │
│                                                                            │
│                    ┌─────────────────┐                                    │
│                    │   Root Node     │                                    │
│                    └────────┬────────┘                                    │
│              ┌──────────────┼──────────────┐                              │
│              ▼              ▼              ▼                              │
│        ┌─────────┐    ┌─────────┐    ┌─────────┐                         │
│        │ Node[0] │    │ Node[1] │    │ Node[2] │                         │
│        └────┬────┘    └────┬────┘    └────┬────┘                         │
│             │              │              │                               │
│        ┌────┴────┐    ┌────┴────┐    ┌────┴────┐                         │
│        ▼         ▼    ▼         ▼    ▼         ▼                         │
│   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐          │
│   │ Page 0 ││ Page 1 ││ Page 2 ││ Page 3 ││ Page 4 ││ Page 5 │          │
│   │offset=0││off=4K  ││off=8K  ││off=12K ││off=16K ││off=20K │          │
│   └────────┘└────────┘└────────┘└────────┘└────────┘└────────┘          │
│                                                                            │
│   O(log n) lookup by file offset → page                                  │
│                                                                            │
│   struct page {                                                           │
│       unsigned long flags;           /* Page status flags */              │
│       atomic_t      _refcount;       /* Reference count */                │
│       atomic_t      _mapcount;       /* Count of page table mappings */   │
│       struct address_space *mapping; /* If in page cache, points to it */ │
│       pgoff_t       index;           /* Offset within mapping */          │
│       struct list_head lru;          /* LRU list for reclaim */           │
│   };                                                                      │
│                                                                            │
│   Page flags relevant to zero-copy:                                       │
│   • PG_referenced: Recently accessed                                      │
│   • PG_uptodate:   Contains valid data                                    │
│   • PG_dirty:      Modified, needs writeback                              │
│   • PG_locked:     I/O in progress                                        │
│   • PG_writeback:  Being written to disk                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The Traditional I/O Path

Before diving into zero-copy techniques, let's thoroughly understand the traditional I/O path and its 
inefficiencies.

### Reading a File: The Costly Journey

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL FILE READ PATH                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Application calls: ssize_t n = read(fd, buffer, 4096);                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ USER SPACE                                                           │ │
│   │                                                                      │ │
│   │   Application                                                        │ │
│   │   ┌──────────────┐                                                   │ │
│   │   │ char buffer  │ ◄─────── This is where data ends up             │ │
│   │   │   [4096]     │                                                   │ │
│   │   └──────────────┘                                                   │ │
│   │          ▲                                                           │ │
│   │          │                                                           │ │
│   └──────────┼──────────────────────────────────────────────────────────┘ │
│              │                                                             │
│   ═══════════╪═══════════════════════════════════════════════════════════ │
│              │ CONTEXT SWITCH #1: User → Kernel                           │
│   ═══════════╪═══════════════════════════════════════════════════════════ │
│              │                                                             │
│   ┌──────────┼──────────────────────────────────────────────────────────┐ │
│   │ KERNEL SPACE                                                         │ │
│   │          │                                                           │ │
│   │    ┌─────┴─────┐                                                     │ │
│   │    │ sys_read  │                                                     │ │
│   │    └─────┬─────┘                                                     │ │
│   │          │                                                           │ │
│   │          ▼                                                           │ │
│   │    ┌───────────────────┐                                             │ │
│   │    │ VFS: vfs_read()   │                                             │ │
│   │    └─────────┬─────────┘                                             │ │
│   │              │                                                       │ │
│   │              ▼                                                       │ │
│   │    ┌───────────────────┐     ┌─────────────────────────────────┐    │ │
│   │    │ Page Cache Lookup │────►│ Page found?                     │    │ │
│   │    └───────────────────┘     │ YES: copy_to_user (CPU COPY 2)  │    │ │
│   │              │               │ NO:  Continue below...          │    │ │
│   │              │               └─────────────────────────────────┘    │ │
│   │              ▼                                                       │ │
│   │    ┌───────────────────┐                                             │ │
│   │    │ Filesystem:       │                                             │ │
│   │    │ ext4_file_read()  │                                             │ │
│   │    └─────────┬─────────┘                                             │ │
│   │              │                                                       │ │
│   │              ▼                                                       │ │
│   │    ┌───────────────────┐                                             │ │
│   │    │ Block Layer:      │                                             │ │
│   │    │ submit_bio()      │                                             │ │
│   │    └─────────┬─────────┘                                             │ │
│   │              │                                                       │ │
│   │              ▼                                                       │ │
│   │    ┌───────────────────┐                                             │ │
│   │    │ DMA COPY #1       │◄─── Disk → Page Cache (via DMA)            │ │
│   │    │ (Disk to Memory)  │                                             │ │
│   │    └─────────┬─────────┘                                             │ │
│   │              │                                                       │ │
│   │              ▼                                                       │ │
│   │    ┌───────────────────┐                                             │ │
│   │    │ Page Cache        │                                             │ │
│   │    │ ┌─────┬─────┬───┐ │                                             │ │
│   │    │ │Page0│Page1│...│ │◄─── Data now in kernel memory              │ │
│   │    │ └─────┴─────┴───┘ │                                             │ │
│   │    └─────────┬─────────┘                                             │ │
│   │              │                                                       │ │
│   │              ▼                                                       │ │
│   │    ┌───────────────────┐                                             │ │
│   │    │ CPU COPY #2       │◄─── Page Cache → User Buffer (CPU)         │ │
│   │    │ copy_to_user()    │     THIS IS THE EXPENSIVE COPY!            │ │
│   │    └───────────────────┘                                             │ │
│   │                                                                      │ │
│   └──────────────────────────────────────────────────────────────────────┘ │
│              │                                                             │
│   ═══════════╪═══════════════════════════════════════════════════════════ │
│              │ CONTEXT SWITCH #2: Kernel → User                           │
│   ═══════════╪═══════════════════════════════════════════════════════════ │
│              │                                                             │
│              ▼                                                             │
│        Return to application with data in buffer                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Sending Data Over Network: Double Trouble

When sending file data over the network, the traditional path doubles the inefficiency:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL FILE → NETWORK PATH                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Application code:                                                       │
│   while ((n = read(file_fd, buffer, 4096)) > 0) {                        │
│       write(socket_fd, buffer, n);                                        │
│   }                                                                       │
│                                                                            │
│   DATA JOURNEY (for each buffer):                                         │
│   ════════════════════════════════                                        │
│                                                                            │
│   ┌─────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────┐ │
│   │         │ DMA  │             │ CPU  │             │ CPU  │         │ │
│   │  DISK   │─────►│ PAGE CACHE  │─────►│ USER BUFFER │─────►│ SOCKET  │ │
│   │         │      │             │      │             │      │ BUFFER  │ │
│   └─────────┘      └─────────────┘      └─────────────┘      └────┬────┘ │
│                                                                    │      │
│      Copy 1           Copy 2              Copy 3                   │      │
│    (Disk→Kernel)   (Kernel→User)       (User→Kernel)               │      │
│                                                                    │      │
│                                                          ┌─────────┴────┐ │
│                                                          │              │ │
│                                                          │     NIC      │ │
│                                                          │              │ │
│                                                          └──────────────┘ │
│                                                                    ▲      │
│                                                                    │      │
│                                                            Copy 4  │      │
│                                                          (DMA)     │      │
│                                                                    │      │
│   CONTEXT SWITCHES:                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   Time ──────────────────────────────────────────────────────────────►    │
│                                                                            │
│   User:  ████░░░░░░░░░░████░░░░░░░░░░████░░░░░░░░░░████                   │
│          │   │         │   │         │   │         │                      │
│   Kernel:░░░░██████████░░░░██████████░░░░██████████░░░░                   │
│          │   │         │   │         │   │         │                      │
│          │   └─read()──┘   └─write()─┘   └─read()──┘                      │
│          │                                                                │
│          └─ Each transition costs 1-10 μs (TLB flush, cache pollution)   │
│                                                                            │
│   PER 4KB BUFFER:                                                         │
│   • 4 context switches (read in + out, write in + out)                   │
│   • 2 CPU copies (kernel→user, user→kernel)                              │
│   • 2 DMA transfers (disk→kernel, kernel→NIC)                            │
│   • CPU cache pollution from copying through L1/L2/L3                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Context Switch Cost Analysis

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT SWITCH OVERHEAD                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHAT HAPPENS DURING A CONTEXT SWITCH:                                   │
│   ──────────────────────────────────────                                   │
│                                                                            │
│   1. REGISTER SAVE                                                        │
│      ┌───────────────────────────────────────────────────────────────┐   │
│      │ Save all CPU registers to kernel stack                        │   │
│      │ • General purpose: RAX, RBX, RCX, RDX, RSI, RDI, RBP, RSP    │   │
│      │ • Segment: CS, DS, ES, FS, GS, SS                             │   │
│      │ • Control: RIP, RFLAGS, CR3                                   │   │
│      │ • FPU/SSE/AVX state (if used): 512-2048 bytes                 │   │
│      └───────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   2. PAGE TABLE SWITCH (User ↔ Kernel)                                    │
│      ┌───────────────────────────────────────────────────────────────┐   │
│      │ • Switch CR3 register to kernel page tables                   │   │
│      │ • With KPTI (Meltdown mitigation): FULL TLB FLUSH            │   │
│      │ • Without KPTI: Partial TLB flush                            │   │
│      │                                                               │   │
│      │ TLB Miss Cost:                                                │   │
│      │ • L1 TLB miss + L2 TLB hit:  ~7 cycles                       │   │
│      │ • L2 TLB miss (page walk):   ~50-100 cycles per level       │   │
│      │ • 4-level page table:        ~200-400 cycles total           │   │
│      └───────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   3. CPU CACHE POLLUTION                                                  │
│      ┌───────────────────────────────────────────────────────────────┐   │
│      │ Before switch:                                                │   │
│      │ ┌─────────────────────────────────────────┐                   │   │
│      │ │ L1 Cache: Hot user data/code ████████  │                   │   │
│      │ │ L2 Cache: User working set   ████████  │                   │   │
│      │ └─────────────────────────────────────────┘                   │   │
│      │                                                               │   │
│      │ After switch to kernel:                                       │   │
│      │ ┌─────────────────────────────────────────┐                   │   │
│      │ │ L1 Cache: Mixed kernel/user  ████░░░░  │                   │   │
│      │ │ L2 Cache: Kernel data evicting user    │                   │   │
│      │ └─────────────────────────────────────────┘                   │   │
│      │                                                               │   │
│      │ After return to user:                                         │   │
│      │ • User data must be re-fetched from L3/RAM                   │   │
│      │ • Cache miss: L3 ~40 cycles, RAM ~200+ cycles                │   │
│      └───────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   MEASURED CONTEXT SWITCH TIMES:                                          │
│   ───────────────────────────────                                          │
│   │ System                          │ Time (approx)  │                    │
│   │─────────────────────────────────┼────────────────│                    │
│   │ System call (minimal)           │ 100-300 ns     │                    │
│   │ System call with KPTI           │ 500-1000 ns    │                    │
│   │ Full process context switch     │ 1-10 μs        │                    │
│   │ Context switch + cache misses   │ 10-50 μs       │                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Zero-Copy Techniques Overview

Linux provides several zero-copy mechanisms, each suited for different use cases:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY TECHNIQUES COMPARISON                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TECHNIQUE         │ COPIES │ CONTEXT  │ USE CASE                       │
│                     │        │ SWITCHES │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   Traditional       │   4    │    4     │ N/A (baseline)                 │
│   read()+write()    │        │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   mmap()+write()    │   3    │    4     │ Random access, repeated reads  │
│                     │        │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   sendfile()        │   2    │    2     │ File → Socket (web servers)    │
│                     │        │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   sendfile() +      │   2    │    2     │ File → Socket (true zero-copy) │
│   scatter-gather    │ (DMA)  │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   splice()          │   2    │    2     │ FD → FD via pipe buffer        │
│                     │        │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   vmsplice()        │   1    │    2     │ User memory → Pipe             │
│                     │        │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   copy_file_range() │   0*   │    2     │ Server-side copy (NFS, etc.)   │
│                     │        │          │ *on same filesystem            │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   MSG_ZEROCOPY      │   0    │    2     │ Socket send without copy       │
│                     │        │          │                                 │
│   ──────────────────┼────────┼──────────┼─────────────────────────────── │
│   io_uring +        │   0    │    0*    │ Async I/O with pre-registered  │
│   fixed buffers     │        │          │ buffers (*amortized)           │
│                     │        │          │                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

### mmap() + write(): The First Step

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    mmap() + write() APPROACH                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Code:                                                                   │
│   void *addr = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);          │
│   write(socket_fd, addr, size);                                           │
│                                                                            │
│   DATA PATH:                                                              │
│   ──────────                                                               │
│                                                                            │
│   ┌─────────┐      ┌─────────────┐                  ┌─────────────┐      │
│   │         │ DMA  │             │                  │             │      │
│   │  DISK   │─────►│ PAGE CACHE  │                  │   SOCKET    │      │
│   │         │      │             │                  │   BUFFER    │      │
│   └─────────┘      └──────┬──────┘                  └──────┬──────┘      │
│                           │                                 │             │
│      Copy 1               │ User virtual memory             │             │
│    (DMA)                  │ maps to same pages              │             │
│                           ▼                                 ▼             │
│                    ┌─────────────┐      CPU         ┌─────────────┐      │
│                    │ USER SPACE  │─────────────────►│   SOCKET    │      │
│                    │ (via mmap)  │     Copy 2       │   BUFFER    │      │
│                    └─────────────┘                  └──────┬──────┘      │
│                                                            │             │
│                                                     Copy 3 │ DMA         │
│                                                            ▼             │
│                                                     ┌─────────────┐      │
│                                                     │     NIC     │      │
│                                                     └─────────────┘      │
│                                                                            │
│   ADVANTAGE: Eliminated one CPU copy (page cache → user buffer)          │
│   REMAINING: Still need CPU copy for write() to socket buffer           │
│                                                                            │
│   WHEN TO USE:                                                            │
│   • Repeated access to same file region                                   │
│   • Random access patterns                                                │
│   • Application needs to examine/modify data                              │
│                                                                            │
│   DRAWBACKS:                                                              │
│   • Page faults on first access                                           │
│   • TLB pressure for large mappings                                       │
│   • Still requires write() copy                                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### sendfile(): File to Socket Zero-Copy

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sendfile() SYSTEM CALL                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ssize_t sendfile(int out_fd, int in_fd, off_t *offset, size_t count);  │
│                                                                            │
│   DATA PATH (with scatter-gather DMA):                                    │
│   ─────────────────────────────────────                                    │
│                                                                            │
│   ┌─────────┐      ┌─────────────┐                                        │
│   │         │ DMA  │             │                                        │
│   │  DISK   │─────►│ PAGE CACHE  │─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐             │
│   │         │      │             │                         │             │
│   └─────────┘      └─────────────┘                         │             │
│                           │                                │             │
│      Copy 1               │ Page descriptors               │ Scatter-    │
│    (DMA)                  │ passed to NIC                  │ Gather      │
│                           ▼                                │ DMA         │
│                    ┌─────────────┐                         │             │
│                    │ TCP Headers │                         │             │
│                    │   (small)   │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│             │
│                    └─────────────┘                         │             │
│                                                            │             │
│                                                            ▼             │
│                                                     ┌─────────────┐      │
│                                                     │     NIC     │      │
│                                                     │ Reads from  │      │
│                                                     │ page cache  │      │
│                                                     │ directly!   │      │
│                                                     └─────────────┘      │
│                                                            │             │
│                                                    Copy 2  │ DMA         │
│                                                            ▼             │
│                                                     ┌─────────────┐      │
│                                                     │   NETWORK   │      │
│                                                     └─────────────┘      │
│                                                                            │
│   ONLY 2 COPIES, BOTH DMA - CPU NEVER TOUCHES THE DATA!                  │
│                                                                            │
│   Requirements for true zero-copy sendfile():                             │
│   • NIC must support scatter-gather DMA                                   │
│   • Socket buffer holds only metadata (page descriptors)                  │
│   • TCP headers from socket buffer + data from page cache                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### splice(), tee(), and vmsplice(): The Flexible Trio

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SPLICE FAMILY SYSTEM CALLS                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PIPE BUFFER ABSTRACTION:                                            │
│   ────────────────────────────                                             │
│                                                                            │
│   The splice family uses pipes as a kernel buffer abstraction.            │
│   Pipe buffers hold references to pages, not copies of data.              │
│                                                                            │
│   struct pipe_buffer {                                                    │
│       struct page *page;      /* Reference to page */                     │
│       unsigned int offset;    /* Offset within page */                    │
│       unsigned int len;       /* Length of data */                        │
│       const struct pipe_buf_operations *ops;                              │
│       unsigned int flags;                                                 │
│   };                                                                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                        PIPE (Kernel)                                 │ │
│   │  ┌────────────┬────────────┬────────────┬────────────┬─────────┐   │ │
│   │  │ pipe_buf 0 │ pipe_buf 1 │ pipe_buf 2 │ pipe_buf 3 │   ...   │   │ │
│   │  │   ┌─┐      │   ┌─┐      │   ┌─┐      │   ┌─┐      │         │   │ │
│   │  │   │●│      │   │●│      │   │●│      │   │●│      │         │   │ │
│   │  │   └┼┘      │   └┼┘      │   └┼┘      │   └┼┘      │         │   │ │
│   │  └────┼───────┴────┼───────┴────┼───────┴────┼───────┴─────────┘   │ │
│   │       │            │            │            │                      │ │
│   │       ▼            ▼            ▼            ▼                      │ │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                │ │
│   │  │ Page A  │  │ Page B  │  │ Page C  │  │ Page D  │   Physical    │ │
│   │  │(file pg)│  │(file pg)│  │(user pg)│  │(sock pg)│   Memory      │ │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘                │ │
│   │                                                                     │ │
│   │  Pages come from different sources but are referenced uniformly    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THREE SYSTEM CALLS:                                                     │
│   ───────────────────                                                      │
│                                                                            │
│   1. splice() - Move data between fd and pipe                            │
│      ssize_t splice(int fd_in, off_t *off_in,                            │
│                     int fd_out, off_t *off_out,                           │
│                     size_t len, unsigned int flags);                      │
│                                                                            │
│   2. tee() - Duplicate pipe contents (zero-copy fork)                    │
│      ssize_t tee(int fd_in, int fd_out, size_t len, unsigned int flags); │
│                                                                            │
│   3. vmsplice() - Move user memory into pipe                             │
│      ssize_t vmsplice(int fd, const struct iovec *iov,                   │
│                       unsigned long nr_segs, unsigned int flags);         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Zero-Copy Pipeline Example:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BUILDING A ZERO-COPY PIPELINE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO: Send file to multiple clients (fan-out)                       │
│                                                                            │
│   Traditional approach (4 copies per client):                             │
│   ────────────────────────────────────────────                             │
│   read(file_fd, buffer, size);                                            │
│   for (int i = 0; i < num_clients; i++) {                                │
│       write(client_fd[i], buffer, size);    // Copy per client           │
│   }                                                                       │
│                                                                            │
│   Zero-copy with splice + tee:                                            │
│   ────────────────────────────                                             │
│                                                                            │
│   // Create pipe                                                          │
│   int pipefd[2];                                                          │
│   pipe(pipefd);                                                           │
│                                                                            │
│   // Move file data into pipe (zero-copy reference)                       │
│   splice(file_fd, NULL, pipefd[1], NULL, size, 0);                       │
│                                                                            │
│   // Send to all clients                                                  │
│   for (int i = 0; i < num_clients - 1; i++) {                            │
│       // Duplicate pipe contents (zero-copy)                              │
│       tee(pipefd[0], client_pipe[i][1], size, 0);                        │
│       splice(client_pipe[i][0], NULL, client_fd[i], NULL, size, 0);      │
│   }                                                                       │
│   // Last client gets the original pipe                                   │
│   splice(pipefd[0], NULL, client_fd[num_clients-1], NULL, size, 0);      │
│                                                                            │
│   DATA FLOW (3 clients):                                                  │
│   ───────────────────────                                                  │
│                                                                            │
│   ┌──────┐                                                                │
│   │ File │                                                                │
│   │ Page │━━━━━━━━━━┓                                                     │
│   │Cache │          ┃ splice()                                            │
│   └──────┘          ┃                                                     │
│                     ▼                                                     │
│              ┌─────────────┐                                              │
│              │    Pipe     │                                              │
│              │ (page refs) │                                              │
│              └──────┬──────┘                                              │
│        ┌────────────┼────────────┐                                        │
│        │ tee()      │ tee()      │ splice()                               │
│        ▼            ▼            ▼                                        │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐                                  │
│   │Socket 1 │  │Socket 2 │  │Socket 3 │                                  │
│   └─────────┘  └─────────┘  └─────────┘                                  │
│                                                                            │
│   THE PAGE IS NEVER COPIED - Only references are moved/duplicated!       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. sendfile() Deep Dive

### System Call Interface

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sendfile() SYSTEM CALL DETAILS                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #include <sys/sendfile.h>                                               │
│                                                                            │
│   ssize_t sendfile(int out_fd,        /* Output file descriptor */        │
│                    int in_fd,         /* Input file descriptor */         │
│                    off_t *offset,     /* Offset in input file */          │
│                    size_t count);     /* Bytes to transfer */             │
│                                                                            │
│   RETURN VALUE:                                                           │
│   • Success: Number of bytes written to out_fd                            │
│   • Error: -1 with errno set                                              │
│                                                                            │
│   PARAMETERS:                                                             │
│   ───────────                                                              │
│   out_fd:  Must be a socket (Linux 2.6.33+: can be any file)             │
│   in_fd:   Must support mmap (regular file, block device)                 │
│   offset:  If non-NULL, starting position (updated after call)            │
│            If NULL, use and update current file position                  │
│   count:   Maximum bytes to transfer                                      │
│                                                                            │
│   EXAMPLE USAGE:                                                          │
│   ───────────────                                                          │
│                                                                            │
│   int file_fd = open("large_file.dat", O_RDONLY);                        │
│   int sock_fd = accept(listen_fd, NULL, NULL);                            │
│                                                                            │
│   struct stat st;                                                         │
│   fstat(file_fd, &st);                                                    │
│                                                                            │
│   off_t offset = 0;                                                       │
│   ssize_t sent = 0;                                                       │
│   size_t remaining = st.st_size;                                          │
│                                                                            │
│   while (remaining > 0) {                                                 │
│       sent = sendfile(sock_fd, file_fd, &offset, remaining);              │
│       if (sent <= 0) {                                                    │
│           if (errno == EAGAIN) continue;  // Non-blocking                 │
│           break;  // Error                                                │
│       }                                                                   │
│       remaining -= sent;                                                  │
│   }                                                                       │
│                                                                            │
│   IMPORTANT FLAGS (Linux-specific variations):                            │
│   ─────────────────────────────────────────────                            │
│   • TCP_CORK on socket: Batch small writes into larger TCP segments      │
│   • O_NONBLOCK: Returns EAGAIN if socket would block                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Implementation

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sendfile() KERNEL PATH                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SYSCALL_DEFINE4(sendfile, ...)                                          │
│        │                                                                  │
│        ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  do_sendfile(out_fd, in_fd, offset, count)                          │ │
│   │       │                                                              │ │
│   │       ├── 1. Get file structs: in_file, out_file                   │ │
│   │       │                                                              │ │
│   │       ├── 2. Verify in_file supports splice_read                    │ │
│   │       │       (generic_file_splice_read for regular files)          │ │
│   │       │                                                              │ │
│   │       ├── 3. Verify out_file supports splice_write                  │ │
│   │       │       (iter_file_splice_write or sock_splice_write)         │ │
│   │       │                                                              │ │
│   │       └── 4. Call do_splice_direct()                                │ │
│   │                    │                                                 │ │
│   └────────────────────┼────────────────────────────────────────────────┘ │
│                        ▼                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  do_splice_direct(in_file, offset, out_file, ooffset, len, flags)   │ │
│   │       │                                                              │ │
│   │       ├── 1. Create a "direct" pipe for kernel use                  │ │
│   │       │       (PIPE_DEF_BUFFERS = 16 pages = 64KB default)          │ │
│   │       │                                                              │ │
│   │       ├── 2. Loop: splice_to_pipe() + splice_from_pipe()           │ │
│   │       │       │                                                      │ │
│   │       │       ├── splice_to_pipe():                                 │ │
│   │       │       │   • Find/allocate page cache pages                  │ │
│   │       │       │   • Add page references to pipe buffers             │ │
│   │       │       │   • NO DATA COPY - just page references             │ │
│   │       │       │                                                      │ │
│   │       │       └── splice_from_pipe():                               │ │
│   │       │           • Pass page refs to socket layer                  │ │
│   │       │           • Socket builds sk_buff with page frags           │ │
│   │       │           • NO DATA COPY - sk_buff points to pages          │ │
│   │       │                                                              │ │
│   │       └── 3. Release pipe resources                                 │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE KEY: Data stays in page cache pages throughout!                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Page Cache Role in sendfile()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PAGE CACHE IN SENDFILE                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CASE 1: Page is in cache (HOT PATH)                                     │
│   ─────────────────────────────────────                                    │
│                                                                            │
│   ┌─────────────┐                                                         │
│   │  sendfile() │                                                         │
│   └──────┬──────┘                                                         │
│          │                                                                │
│          ▼                                                                │
│   ┌─────────────────────────┐     ┌─────────────────────────────────┐    │
│   │ Page Cache Lookup       │     │                                 │    │
│   │ find_get_page(mapping,  │────►│  PAGE FOUND                     │    │
│   │               index)    │     │  • Increment refcount           │    │
│   └─────────────────────────┘     │  • Return page immediately      │    │
│                                   │  • NO DISK I/O                  │    │
│                                   └─────────────────────────────────┘    │
│                                                                            │
│   CASE 2: Page not in cache (COLD PATH)                                   │
│   ──────────────────────────────────────                                   │
│                                                                            │
│   ┌─────────────┐                                                         │
│   │  sendfile() │                                                         │
│   └──────┬──────┘                                                         │
│          │                                                                │
│          ▼                                                                │
│   ┌─────────────────────────┐     ┌─────────────────────────────────┐    │
│   │ Page Cache Lookup       │     │                                 │    │
│   │ find_get_page(mapping,  │────►│  PAGE NOT FOUND                 │    │
│   │               index)    │     │                                 │    │
│   └─────────────────────────┘     └─────────────┬───────────────────┘    │
│                                                  │                        │
│                                                  ▼                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  1. Allocate new page                                               │ │
│   │  2. Add to page cache (address_space)                               │ │
│   │  3. Submit read I/O (submit_bio)                                    │ │
│   │  4. Wait for DMA completion                                         │ │
│   │  5. Mark page PG_uptodate                                           │ │
│   │  6. Return page                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   READ-AHEAD OPTIMIZATION:                                                │
│   ─────────────────────────                                                │
│   When sendfile() accesses sequential pages:                              │
│   • Kernel detects sequential pattern                                     │
│   • Triggers read-ahead (default: 128KB)                                  │
│   • Future pages are pre-fetched before needed                            │
│   • Subsequent sendfile() calls find pages already in cache              │
│                                                                            │
│   sysctl vm.read_ahead_kb=128  # Default read-ahead window               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### DMA and Network Stack Integration

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCATTER-GATHER DMA IN SENDFILE                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Modern NICs support "scatter-gather" DMA, allowing them to read         │
│   data from non-contiguous memory locations and assemble into packets.    │
│                                                                            │
│   WITHOUT Scatter-Gather (requires copy to socket buffer):                │
│   ──────────────────────────────────────────────────────────               │
│                                                                            │
│   ┌──────────────┐    CPU     ┌──────────────┐    DMA    ┌─────────┐     │
│   │  Page Cache  │───────────►│ Socket Buffer │──────────►│   NIC   │     │
│   │ (scattered)  │   COPY     │ (contiguous)  │          └─────────┘     │
│   └──────────────┘            └──────────────┘                            │
│                                                                            │
│   WITH Scatter-Gather (true zero-copy):                                   │
│   ────────────────────────────────────────                                 │
│                                                                            │
│   ┌──────────────┐                                                        │
│   │ Page Cache   │                                                        │
│   │  ┌────────┐  │                                                        │
│   │  │ Page 0 │──┼───────────────────────────────────┐                   │
│   │  ├────────┤  │                                   │                   │
│   │  │ Page 1 │──┼─────────────────────────┐         │                   │
│   │  ├────────┤  │                         │         │                   │
│   │  │ Page 2 │──┼───────────────┐         │         │                   │
│   │  └────────┘  │               │         │         │                   │
│   └──────────────┘               │         │         │                   │
│                                  │         │         │                   │
│   ┌──────────────────────────────┼─────────┼─────────┼───────────────┐   │
│   │         sk_buff (Socket Buffer Descriptor)       │               │   │
│   │                              │         │         │               │   │
│   │   ┌────────────────────────────────────────────────────────┐     │   │
│   │   │  TCP/IP Headers (14+20+20 = 54 bytes typical)          │     │   │
│   │   │  (small, inline in sk_buff head)                       │     │   │
│   │   └────────────────────────────────────────────────────────┘     │   │
│   │                                                                   │   │
│   │   skb_frag_t frags[]:      │         │         │                 │   │
│   │   ┌───────────────────┐    │         │         │                 │   │
│   │   │ frag[0]: page ptr ├────┘         │         │                 │   │
│   │   │          offset   │              │         │                 │   │
│   │   │          len      │              │         │                 │   │
│   │   ├───────────────────┤              │         │                 │   │
│   │   │ frag[1]: page ptr ├──────────────┘         │                 │   │
│   │   │          offset   │                        │                 │   │
│   │   │          len      │                        │                 │   │
│   │   ├───────────────────┤                        │                 │   │
│   │   │ frag[2]: page ptr ├────────────────────────┘                 │   │
│   │   │          offset   │                                          │   │
│   │   │          len      │                                          │   │
│   │   └───────────────────┘                                          │   │
│   │                                                                   │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                    │                                                       │
│                    │ DMA descriptor ring                                   │
│                    ▼                                                       │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │  NIC DMA Engine                                                     │  │
│   │  ┌──────────────────────────────────────────────────────────────┐  │  │
│   │  │  DMA Descriptor Ring:                                         │  │  │
│   │  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐         │  │  │
│   │  │  │ Desc 0  │ Desc 1  │ Desc 2  │ Desc 3  │   ...   │         │  │  │
│   │  │  │ hdr_ptr │ pg0_ptr │ pg1_ptr │ pg2_ptr │         │         │  │  │
│   │  │  │ hdr_len │ pg0_len │ pg1_len │ pg2_len │         │         │  │  │
│   │  │  └─────────┴─────────┴─────────┴─────────┴─────────┘         │  │  │
│   │  └──────────────────────────────────────────────────────────────┘  │  │
│   │                                                                     │  │
│   │  NIC reads headers + data pages in order, assembles packet         │  │
│   │  CPU never touches the file data!                                   │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Limitations and Edge Cases

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sendfile() LIMITATIONS                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   1. INPUT FILE MUST SUPPORT mmap()                                       │
│   ───────────────────────────────────                                      │
│   ✓ Regular files                                                         │
│   ✓ Block devices                                                         │
│   ✗ Pipes (use splice() instead)                                          │
│   ✗ Sockets (use splice() instead)                                        │
│   ✗ Special devices that don't support mmap                               │
│                                                                            │
│   2. OUTPUT CONSTRAINTS (Linux-specific)                                  │
│   ──────────────────────────────────────                                   │
│   Linux < 2.6.33: out_fd must be a socket                                 │
│   Linux >= 2.6.33: out_fd can be any file supporting splice_write         │
│                                                                            │
│   3. NO TRANSFORMATION POSSIBLE                                           │
│   ────────────────────────────────                                         │
│   sendfile() cannot:                                                      │
│   • Compress data (use gzip + write() instead)                            │
│   • Encrypt data (use kernel TLS or copy + encrypt)                       │
│   • Modify content (must use read() + modify + write())                   │
│                                                                            │
│   4. FILE MODIFICATION DURING SENDFILE                                    │
│   ─────────────────────────────────────                                    │
│   If file is modified while sendfile() is in progress:                    │
│   • Pages already in socket buffer: OLD data sent                         │
│   • Pages not yet read: NEW data sent                                     │
│   • Result: Potentially corrupted/inconsistent data                       │
│                                                                            │
│   Solution: Use file locking or ensure no concurrent writes               │
│                                                                            │
│   5. LARGE FILE CONSIDERATIONS                                            │
│   ───────────────────────────────                                          │
│   • sendfile() may not transfer all bytes in one call                     │
│   • Socket buffer full → returns partial count                            │
│   • Non-blocking socket → returns EAGAIN                                  │
│   • Always loop until all data sent                                       │
│                                                                            │
│   6. WHEN ZERO-COPY FAILS                                                 │
│   ────────────────────────                                                 │
│   Kernel may fall back to copying when:                                   │
│   • NIC doesn't support scatter-gather                                    │
│   • TCP checksum offload unavailable                                      │
│   • Data needs transformation (encryption, etc.)                          │
│   • Memory pressure forces page reclaim                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. splice() Deep Dive

### The Pipe Buffer Abstraction

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PIPE BUFFERS: THE UNIVERSAL CONNECTOR                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   splice() uses pipe buffers as a kernel-space intermediary.              │
│   Unlike sendfile(), it can connect ANY two file descriptors.             │
│                                                                            │
│   struct pipe_inode_info {                                                │
│       struct mutex mutex;           /* Protects pipe operations */        │
│       wait_queue_head_t rd_wait;    /* Readers waiting */                 │
│       wait_queue_head_t wr_wait;    /* Writers waiting */                 │
│       unsigned int head;            /* Write position (producer) */       │
│       unsigned int tail;            /* Read position (consumer) */        │
│       unsigned int ring_size;       /* Number of pipe_buffer slots */     │
│       struct pipe_buffer *bufs;     /* Circular buffer of page refs */    │
│   };                                                                      │
│                                                                            │
│   PIPE AS CIRCULAR BUFFER:                                                │
│   ─────────────────────────                                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │       tail                                       head               │ │
│   │         │                                          │                │ │
│   │         ▼                                          ▼                │ │
│   │   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐   │ │
│   │   │  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │ ... │ N-1 │   │ │
│   │   │     │ ref │ ref │ ref │ ref │ ref │     │     │     │     │   │ │
│   │   │empty│────►│────►│────►│────►│────►│empty│empty│empty│empty│   │ │
│   │   └─────┴──┼──┴──┼──┴──┼──┴──┼──┴──┼──┴─────┴─────┴─────┴─────┘   │ │
│   │            │     │     │     │     │                              │ │
│   │            ▼     ▼     ▼     ▼     ▼                              │ │
│   │         ┌─────────────────────────────┐                           │ │
│   │         │    Physical Memory Pages    │                           │ │
│   │         │  (from file, socket, user)  │                           │ │
│   │         └─────────────────────────────┘                           │ │
│   │                                                                     │ │
│   │   • tail → head: Contains page references (data available)        │ │
│   │   • head → tail: Empty slots (space available)                    │ │
│   │   • Default: 16 slots (64KB), max: 1MB (F_SETPIPE_SZ)            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   struct pipe_buffer {                                                    │
│       struct page *page;                  /* Physical page reference */   │
│       unsigned int offset;                /* Offset within page */        │
│       unsigned int len;                   /* Data length in this page */  │
│       const struct pipe_buf_operations *ops;  /* Buffer operations */    │
│       unsigned int flags;                 /* PIPE_BUF_FLAG_* */           │
│   };                                                                      │
│                                                                            │
│   FLAGS:                                                                  │
│   ──────                                                                   │
│   PIPE_BUF_FLAG_CAN_MERGE  - Data can be appended to this buffer         │
│   PIPE_BUF_FLAG_PACKET     - Buffer is a discrete packet                 │
│   PIPE_BUF_FLAG_GIFT       - Page ownership transferred to receiver      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### splice() System Call Details

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    splice() SYSTEM CALL                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   #define _GNU_SOURCE                                                     │
│   #include <fcntl.h>                                                      │
│                                                                            │
│   ssize_t splice(int fd_in,         /* Input file descriptor */           │
│                  off64_t *off_in,   /* Input offset (or NULL) */          │
│                  int fd_out,        /* Output file descriptor */          │
│                  off64_t *off_out,  /* Output offset (or NULL) */         │
│                  size_t len,        /* Maximum bytes to transfer */       │
│                  unsigned int flags);                                     │
│                                                                            │
│   REQUIREMENT: At least one of fd_in or fd_out MUST be a pipe!           │
│                                                                            │
│   FLAGS:                                                                  │
│   ──────                                                                   │
│   SPLICE_F_MOVE      Hint: move pages instead of copy (often ignored)    │
│   SPLICE_F_NONBLOCK  Don't block on pipe operations                       │
│   SPLICE_F_MORE      More data coming (like TCP_CORK effect)             │
│   SPLICE_F_GIFT      Pages given to pipe, caller must not modify         │
│                                                                            │
│   RETURN VALUE:                                                           │
│   ─────────────                                                            │
│   > 0: Number of bytes transferred                                        │
│   0:   End of input (fd_in reached EOF)                                   │
│   -1:  Error (check errno)                                                │
│                                                                            │
│   COMMON ERRORS:                                                          │
│   ──────────────                                                           │
│   EBADF    - Invalid file descriptor                                      │
│   EINVAL   - Neither fd is a pipe, or both are pipes                      │
│   ENOMEM   - Out of memory                                                │
│   ESPIPE   - Offset used with pipe (offsets only for seekable fds)       │
│   EAGAIN   - Non-blocking and operation would block                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### tee() and vmsplice()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    tee() - DUPLICATE PIPE CONTENTS                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ssize_t tee(int fd_in,        /* Source pipe (read end) */              │
│               int fd_out,       /* Destination pipe (write end) */        │
│               size_t len,       /* Maximum bytes to duplicate */          │
│               unsigned int flags);                                        │
│                                                                            │
│   BOTH fd_in and fd_out MUST be pipes!                                    │
│                                                                            │
│   HOW tee() WORKS:                                                        │
│   ─────────────────                                                        │
│                                                                            │
│   BEFORE tee():                                                           │
│   ┌──────────────────────┐      ┌──────────────────────┐                  │
│   │   Source Pipe        │      │   Dest Pipe          │                  │
│   │  ┌───┬───┬───┬───┐   │      │  ┌───┬───┬───┬───┐   │                  │
│   │  │ A │ B │ C │   │   │      │  │   │   │   │   │   │                  │
│   │  └─┬─┴─┬─┴─┬─┴───┘   │      │  └───┴───┴───┴───┘   │                  │
│   │    │   │   │         │      │                      │                  │
│   │    ▼   ▼   ▼         │      │                      │                  │
│   │  [Page][Page][Page]  │      │                      │                  │
│   └──────────────────────┘      └──────────────────────┘                  │
│                                                                            │
│   AFTER tee():                                                            │
│   ┌──────────────────────┐      ┌──────────────────────┐                  │
│   │   Source Pipe        │      │   Dest Pipe          │                  │
│   │  ┌───┬───┬───┬───┐   │      │  ┌───┬───┬───┬───┐   │                  │
│   │  │ A │ B │ C │   │   │      │  │ A │ B │ C │   │   │                  │
│   │  └─┬─┴─┬─┴─┬─┴───┘   │      │  └─┬─┴─┬─┴─┬─┴───┘   │                  │
│   │    │   │   │         │      │    │   │   │         │                  │
│   │    │   │   │         │      │    │   │   │         │                  │
│   │    └───┼───┼─────────┼──────┼────┘   │   │         │                  │
│   │        └───┼─────────┼──────┼────────┘   │         │                  │
│   │            └─────────┼──────┼────────────┘         │                  │
│   │                      │      │                      │                  │
│   │    ▼   ▼   ▼         │      │                      │                  │
│   │  [Page][Page][Page]  │ ◄────┼── SAME PAGES!        │                  │
│   │  (refcount += 1)     │      │                      │                  │
│   └──────────────────────┘      └──────────────────────┘                  │
│                                                                            │
│   KEY POINT: No data copied! Only page reference counts incremented.      │
│                                                                            │
│   USE CASE: Send same data to multiple destinations (fan-out)            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    vmsplice() - USER MEMORY TO PIPE                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ssize_t vmsplice(int fd,                /* Pipe fd */                   │
│                    const struct iovec *iov,/* User memory regions */      │
│                    unsigned long nr_segs,  /* Number of iovec entries */  │
│                    unsigned int flags);                                   │
│                                                                            │
│   struct iovec {                                                          │
│       void *iov_base;    /* Starting address */                           │
│       size_t iov_len;    /* Number of bytes */                            │
│   };                                                                      │
│                                                                            │
│   TWO MODES:                                                              │
│   ──────────                                                               │
│                                                                            │
│   1. WITHOUT SPLICE_F_GIFT (default - copy mode):                         │
│      - Kernel copies user data to pipe buffer pages                       │
│      - User can modify/free memory after call returns                     │
│      - NOT zero-copy (but useful for gather writes)                       │
│                                                                            │
│   2. WITH SPLICE_F_GIFT (gift mode - zero-copy):                          │
│      - User pages directly referenced by pipe                             │
│      - User MUST NOT modify memory until pipe consumed                    │
│      - Pages must be allocated (e.g., mmap with MAP_PRIVATE)              │
│      - True zero-copy transfer                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   User Space Memory:                                                │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ iov[0]                  iov[1]              iov[2]          │   │ │
│   │   │ ┌──────────────┐       ┌────────────┐      ┌──────────┐     │   │ │
│   │   │ │ Page A       │       │ Page B     │      │ Page C   │     │   │ │
│   │   │ │ (user data)  │       │ (user data)│      │(user data│     │   │ │
│   │   │ └──────────────┘       └────────────┘      └──────────┘     │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │            │                      │                  │              │ │
│   │            │ SPLICE_F_GIFT        │                  │              │ │
│   │            ▼                      ▼                  ▼              │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                        PIPE                                 │   │ │
│   │   │   ┌────────┬────────┬────────┐                              │   │ │
│   │   │   │ ref→A  │ ref→B  │ ref→C  │  (no copy, direct refs)     │   │ │
│   │   │   └────────┴────────┴────────┘                              │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WARNING: With SPLICE_F_GIFT, modifying user memory before pipe          │
│   is consumed leads to undefined behavior (data corruption)!              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Implementation of splice()

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    splice() KERNEL PATH                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SYSCALL_DEFINE6(splice, ...)                                            │
│        │                                                                  │
│        ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  __do_splice()                                                      │ │
│   │       │                                                              │ │
│   │       ├── Validate file descriptors                                  │ │
│   │       │                                                              │ │
│   │       ├── Check: Is fd_in a pipe OR fd_out a pipe?                  │ │
│   │       │   (at least one must be)                                     │ │
│   │       │                                                              │ │
│   │       └── Route to appropriate handler:                             │ │
│   │                                                                      │ │
│   │   CASE 1: fd_in is pipe, fd_out is not                              │ │
│   │   ─────────────────────────────────────                              │ │
│   │   splice_from_pipe() → out_file->f_op->splice_write()               │ │
│   │       │                                                              │ │
│   │       │  For sockets: sock_splice_write()                           │ │
│   │       │  For files:   iter_file_splice_write()                      │ │
│   │       │                                                              │ │
│   │       └── Takes page refs from pipe, passes to output               │ │
│   │                                                                      │ │
│   │   CASE 2: fd_out is pipe, fd_in is not                              │ │
│   │   ─────────────────────────────────────                              │ │
│   │   in_file->f_op->splice_read() → splice_to_pipe()                   │ │
│   │       │                                                              │ │
│   │       │  For files:   generic_file_splice_read()                    │ │
│   │       │  For sockets: sock_splice_read()                            │ │
│   │       │                                                              │ │
│   │       └── Gets page refs from input, adds to pipe                   │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Memory Mapping (mmap)

### How mmap() Works

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    mmap() MEMORY MAPPING                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   void *mmap(void *addr,      /* Suggested address (or NULL) */           │
│              size_t length,   /* Length of mapping */                     │
│              int prot,        /* Memory protection (PROT_READ, etc.) */   │
│              int flags,       /* MAP_SHARED, MAP_PRIVATE, etc. */         │
│              int fd,          /* File descriptor */                       │
│              off_t offset);   /* Offset in file */                        │
│                                                                            │
│   WHAT mmap() DOES:                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   Creates a mapping between a region of virtual address space             │
│   and a file (or device). File I/O becomes memory access!                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Virtual Address Space                    Physical Memory         │ │
│   │   ┌─────────────────────┐                                          │ │
│   │   │                     │                                          │ │
│   │   │   Stack             │                                          │ │
│   │   ├─────────────────────┤                                          │ │
│   │   │                     │                                          │ │
│   │   │   (unmapped)        │                                          │ │
│   │   │                     │                                          │ │
│   │   ├─────────────────────┤                  ┌───────────────────┐   │ │
│   │   │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │◄─── mmap() ────►│ Page Cache Pages  │   │ │
│   │   │ ▓  mmap region    ▓ │     region       │ (file data)       │   │ │
│   │   │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │                  │                   │   │ │
│   │   ├─────────────────────┤                  └───────────────────┘   │ │
│   │   │                     │                           │              │ │
│   │   │   Heap              │                           │              │ │
│   │   ├─────────────────────┤                           │              │ │
│   │   │   Data              │                           ▼              │ │
│   │   ├─────────────────────┤                  ┌───────────────────┐   │ │
│   │   │   Text              │                  │    Disk File      │   │ │
│   │   └─────────────────────┘                  └───────────────────┘   │ │
│   │                                                                     │ │
│   │   Process virtual pages point directly to page cache pages!        │ │
│   │   No read() needed - CPU just accesses memory.                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Page Fault Handling

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DEMAND PAGING WITH mmap()                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   mmap() doesn't read the file immediately. Pages are faulted in          │
│   on demand when first accessed.                                          │
│                                                                            │
│   TIMELINE:                                                               │
│   ─────────                                                                │
│                                                                            │
│   Time 0: mmap() called                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Process Page Table:                                                 │ │
│   │  ┌─────────────────────────────────────────────────────────────┐     │ │
│   │  │ VPN 100 │ Present=0 │ Page not mapped yet                   │     │ │
│   │  │ VPN 101 │ Present=0 │ Page not mapped yet                   │     │ │
│   │  │ VPN 102 │ Present=0 │ Page not mapped yet                   │     │ │
│   │  └─────────────────────────────────────────────────────────────┘     │ │
│   │                                                                      │ │
│   │  Kernel creates VMA (Virtual Memory Area) but no pages allocated    │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Time 1: Process reads from mmap region (e.g., addr = VPN 100)          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                      │ │
│   │   CPU: "Load from VPN 100"                                          │ │
│   │      │                                                               │ │
│   │      ▼                                                               │ │
│   │   MMU: Present=0 → PAGE FAULT!                                      │ │
│   │      │                                                               │ │
│   │      ▼                                                               │ │
│   │   Kernel Page Fault Handler (do_page_fault)                         │ │
│   │      │                                                               │ │
│   │      ├── 1. Look up VMA for address                                 │ │
│   │      │                                                               │ │
│   │      ├── 2. VMA says: "This is file-backed mapping"                 │ │
│   │      │                                                               │ │
│   │      ├── 3. Look up page in page cache:                             │ │
│   │      │      • Found: Use cached page                                 │ │
│   │      │      • Not found: Read from disk                              │ │
│   │      │                                                               │ │
│   │      ├── 4. Update page table: VPN 100 → PFN, Present=1            │ │
│   │      │                                                               │ │
│   │      └── 5. Return to userspace, retry instruction                  │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Time 2: Subsequent accesses to same page → NO fault (page present)     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### MAP_SHARED vs MAP_PRIVATE

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MAPPING TYPES                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   MAP_SHARED:                                                             │
│   ───────────                                                              │
│   • Updates visible to other processes mapping same file                  │
│   • Writes propagate to underlying file (on msync/munmap)                 │
│   • Multiple processes share SAME physical pages                          │
│   • Good for: IPC, shared databases, memory-mapped files                  │
│                                                                            │
│   ┌────────────┐     ┌────────────┐     ┌────────────┐                   │
│   │ Process A  │     │ Process B  │     │ Process C  │                   │
│   │ ┌────────┐ │     │ ┌────────┐ │     │ ┌────────┐ │                   │
│   │ │ VPN 50 │─┼─────┼─│ VPN 80 │─┼─────┼─│ VPN 20 │ │                   │
│   │ └────────┘ │     │ └────────┘ │     │ └────────┘ │                   │
│   └────────────┘     └────────────┘     └─────┬──────┘                   │
│         │                  │                  │                           │
│         └──────────────────┼──────────────────┘                           │
│                            ▼                                              │
│                    ┌───────────────┐                                      │
│                    │ SAME Physical │                                      │
│                    │     Page      │                                      │
│                    └───────────────┘                                      │
│                                                                            │
│   MAP_PRIVATE:                                                            │
│   ────────────                                                             │
│   • Copy-on-Write (COW) semantics                                         │
│   • Initially shares pages with other readers                             │
│   • On write: private copy made, original unchanged                       │
│   • Writes NOT visible to others, NOT written to file                     │
│   • Good for: Reading files, process fork()                               │
│                                                                            │
│   BEFORE WRITE:                          AFTER WRITE by Process A:       │
│   ┌────────────┐  ┌────────────┐         ┌────────────┐  ┌────────────┐  │
│   │ Process A  │  │ Process B  │         │ Process A  │  │ Process B  │  │
│   │ ┌────────┐ │  │ ┌────────┐ │         │ ┌────────┐ │  │ ┌────────┐ │  │
│   │ │ VPN 50 │─┼──┼─│ VPN 80 │ │         │ │ VPN 50 │ │  │ │ VPN 80 │ │  │
│   │ └────────┘ │  │ └────────┘ │         │ └───┬────┘ │  │ └───┬────┘ │  │
│   └────────────┘  └─────┬──────┘         └─────┼──────┘  └─────┼──────┘  │
│         │               │                      │               │          │
│         └───────┬───────┘                      ▼               ▼          │
│                 ▼                        ┌─────────┐     ┌─────────┐     │
│          ┌───────────┐                   │ PRIVATE │     │ORIGINAL │     │
│          │   SAME    │                   │  COPY   │     │  PAGE   │     │
│          │   PAGE    │                   │(modified│     │         │     │
│          └───────────┘                   └─────────┘     └─────────┘     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### mmap() for Zero-Copy I/O

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    mmap() + write() ZERO-COPY PATTERN                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   // Traditional (4 copies):                                              │
│   char buf[SIZE];                                                         │
│   read(file_fd, buf, SIZE);        // Copy 1: disk→kernel, Copy 2: k→u   │
│   write(sock_fd, buf, SIZE);       // Copy 3: u→kernel, Copy 4: DMA      │
│                                                                            │
│   // mmap() approach (3 copies):                                          │
│   void *ptr = mmap(NULL, SIZE, PROT_READ, MAP_PRIVATE, file_fd, 0);      │
│   write(sock_fd, ptr, SIZE);       // Still copies to socket buffer      │
│                                                                            │
│   WHY USE mmap() FOR ZERO-COPY?                                           │
│   ─────────────────────────────                                            │
│                                                                            │
│   1. Random access patterns                                               │
│      - read() requires seeking, mmap() just access memory                 │
│      - Database indices, hash tables in files                             │
│                                                                            │
│   2. Repeated access to same data                                         │
│      - read() copies every time                                           │
│      - mmap() faults in once, then memory access                          │
│                                                                            │
│   3. Shared memory between processes                                      │
│      - MAP_SHARED for IPC                                                 │
│      - No pipe/socket overhead                                            │
│                                                                            │
│   4. Large files                                                          │
│      - 64-bit address space can map TB                                    │
│      - No buffer management needed                                        │
│                                                                            │
│   PITFALLS:                                                               │
│   ─────────                                                                │
│   • Page faults can cause unpredictable latency                           │
│   • TLB pressure with many mappings                                       │
│   • File truncation while mapped → SIGBUS                                 │
│   • Not suitable for all file types (network files, etc.)                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DMA and Hardware Support

### DMA Controller Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DMA CONTROLLER ARCHITECTURE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DMA (Direct Memory Access) allows devices to transfer data              │
│   directly to/from memory without CPU involvement.                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │                         SYSTEM BUS                                  │ │
│   │   ════════════════════════════════════════════════════════════════ │ │
│   │         │              │              │              │              │ │
│   │         │              │              │              │              │ │
│   │   ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐       │ │
│   │   │           │  │           │  │           │  │           │       │ │
│   │   │    CPU    │  │   Memory  │  │    NIC    │  │   Disk    │       │ │
│   │   │           │  │           │  │ Controller│  │ Controller│       │ │
│   │   │           │  │           │  │           │  │           │       │ │
│   │   └───────────┘  └───────────┘  └─────┬─────┘  └─────┬─────┘       │ │
│   │                                       │              │              │ │
│   │                                       │              │              │ │
│   │                           ┌───────────┴──────────────┘              │ │
│   │                           │                                         │ │
│   │                           ▼                                         │ │
│   │                    ┌─────────────┐                                  │ │
│   │                    │ DMA Engine  │                                  │ │
│   │                    │ (per device)│                                  │ │
│   │                    └─────────────┘                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DMA OPERATION FLOW:                                                     │
│   ───────────────────                                                      │
│                                                                            │
│   1. CPU sets up DMA descriptor:                                          │
│      • Source address (physical)                                          │
│      • Destination address (physical)                                     │
│      • Transfer size                                                      │
│      • Direction (read/write)                                             │
│                                                                            │
│   2. CPU signals device: "Start DMA"                                      │
│                                                                            │
│   3. Device DMA engine:                                                   │
│      • Arbitrates for bus access                                          │
│      • Transfers data directly memory ↔ device                            │
│      • CPU can do other work!                                             │
│                                                                            │
│   4. Device raises interrupt: "DMA complete"                              │
│                                                                            │
│   5. CPU handles completion                                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Scatter-Gather DMA

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SCATTER-GATHER DMA                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Without scatter-gather, DMA requires contiguous physical memory.        │
│   With scatter-gather, device can DMA from/to multiple memory regions.    │
│                                                                            │
│   WITHOUT SCATTER-GATHER:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   Physical Memory:                       Device needs contiguous buffer  │
│   ┌─────┬─────┬─────┬─────┬─────┐       ┌───────────────────────────┐   │
│   │ A   │ B   │ C   │ D   │ E   │       │                           │   │
│   │used │FREE │FREE │used │FREE │       │    KERNEL MUST COPY       │   │
│   └─────┴─────┴─────┴─────┴─────┘       │    TO CONTIGUOUS BUFFER   │   │
│                                          └───────────────────────────┘   │
│                                                                            │
│   WITH SCATTER-GATHER:                                                    │
│   ────────────────────                                                     │
│                                                                            │
│   Physical Memory:                       DMA Descriptor List:             │
│   ┌─────┬─────┬─────┬─────┬─────┐       ┌───────────────────────────┐   │
│   │ A   │     │     │ D   │     │       │ desc[0]: addr=A, len=4K   │   │
│   │data │ ... │ ... │data │ ... │       │ desc[1]: addr=D, len=4K   │   │
│   └──┬──┴─────┴─────┴──┬──┴─────┘       │ desc[2]: addr=H, len=4K   │   │
│      │                 │                 └──────────────┬────────────┘   │
│      │                 │                                │               │
│      │     ┌─────┬─────┬─────┐                          │               │
│      │     │     │ H   │     │                          │               │
│      │     │ ... │data │ ... │                          │               │
│      │     └─────┴──┬──┴─────┘                          │               │
│      │              │                                   │               │
│      └──────────────┼───────────────────────────────────┘               │
│                     │                                                    │
│                     ▼                                                    │
│   Device DMA engine reads descriptors, fetches from each address        │
│   NO COPY NEEDED - data stays in original locations!                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### IOMMU and DMA Remapping

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    IOMMU (I/O MEMORY MANAGEMENT UNIT)                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Problem: Devices use PHYSICAL addresses for DMA.                        │
│   - Virtual addresses must be translated                                  │
│   - Pages must be pinned (can't be swapped)                               │
│   - Security: device could DMA to any memory!                             │
│                                                                            │
│   Solution: IOMMU provides address translation for devices.               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU Side:                         Device Side:                    │ │
│   │   ┌─────────────┐                   ┌─────────────┐                │ │
│   │   │   Process   │                   │   Device    │                │ │
│   │   │  Virtual    │                   │   (NIC)     │                │ │
│   │   │  Address    │                   └──────┬──────┘                │ │
│   │   └──────┬──────┘                          │                        │ │
│   │          │                                  │ DMA using             │ │
│   │          ▼                                  │ "I/O Virtual Address" │ │
│   │   ┌─────────────┐                          │                        │ │
│   │   │    MMU      │                          ▼                        │ │
│   │   │ (CPU's TLB) │                   ┌─────────────┐                │ │
│   │   └──────┬──────┘                   │   IOMMU     │                │ │
│   │          │                           │ (Device TLB)│                │ │
│   │          ▼                           └──────┬──────┘                │ │
│   │   ┌─────────────┐                          │                        │ │
│   │   │  Physical   │◄─────────────────────────┘                        │ │
│   │   │   Memory    │                                                   │ │
│   │   └─────────────┘                                                   │ │
│   │                                                                     │ │
│   │   IOMMU translates device addresses → physical addresses           │ │
│   │   Just like MMU does for CPU!                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BENEFITS FOR ZERO-COPY:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   1. Device can use "virtual" addresses                                   │
│      - No need to allocate contiguous physical memory                     │
│      - Scatter-gather becomes transparent                                  │
│                                                                            │
│   2. Security isolation                                                   │
│      - Device can only access pages mapped in its IOMMU page table        │
│      - Prevents malicious device from accessing arbitrary memory          │
│                                                                            │
│   3. User-space DMA (VFIO, DPDK)                                          │
│      - IOMMU allows safe direct device access from user space             │
│      - Kernel maps user pages into device's IOMMU page table              │
│      - True zero-copy: user buffer → device, no kernel involvement        │
│                                                                            │
│   LINUX APIs:                                                             │
│   ───────────                                                              │
│   • dma_map_single()  - Map a buffer for DMA                              │
│   • dma_map_sg()      - Map scatter-gather list                           │
│   • dma_unmap_*()     - Unmap when DMA complete                           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Network Interface Cards (NICs)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NIC RING BUFFER ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Modern NICs use ring buffers (circular queues) for zero-copy DMA.       │
│                                                                            │
│   RX (Receive) Ring:                                                      │
│   ──────────────────                                                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   DRIVER SETUP:                                                     │ │
│   │   1. Allocate ring of descriptors                                   │ │
│   │   2. Allocate pages for packet data                                 │ │
│   │   3. Fill descriptors with page physical addresses                  │ │
│   │   4. Tell NIC: "Ring base address, ring size"                       │ │
│   │                                                                     │ │
│   │                         RX Descriptor Ring                          │ │
│   │   ┌────────┬────────┬────────┬────────┬────────┬────────┐          │ │
│   │   │ desc 0 │ desc 1 │ desc 2 │ desc 3 │ desc 4 │ desc 5 │          │ │
│   │   │ addr=A │ addr=B │ addr=C │ addr=D │ addr=E │ addr=F │          │ │
│   │   │ own=HW │ own=HW │ own=SW │ own=SW │ own=HW │ own=HW │          │ │
│   │   └───┬────┴───┬────┴───┬────┴───┬────┴───┬────┴───┬────┘          │ │
│   │       │        │        │        │        │        │                │ │
│   │       ▼        ▼        ▼        ▼        ▼        ▼                │ │
│   │   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │ │
│   │   │Page A│ │Page B│ │Page C│ │Page D│ │Page E│ │Page F│            │ │
│   │   │(wait)│ │(wait)│ │(data)│ │(data)│ │(wait)│ │(wait)│            │ │
│   │   └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │ │
│   │                       ▲  ▲                                          │ │
│   │                       │  │                                          │ │
│   │              NIC DMAs │  │ Driver reads                             │ │
│   │              packets  │  │ from pages                               │ │
│   │              here     │  │                                          │ │
│   │                                                                     │ │
│   │   PACKET RECEPTION:                                                 │ │
│   │   1. Packet arrives at NIC                                          │ │
│   │   2. NIC reads next descriptor from ring                            │ │
│   │   3. NIC DMAs packet to physical address in descriptor              │ │
│   │   4. NIC updates descriptor: length, status, own=SW                 │ │
│   │   5. NIC raises interrupt                                           │ │
│   │   6. Driver processes packet from page (ZERO COPY to page cache!)   │ │
│   │   7. Driver allocates new page, updates descriptor, own=HW          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TX (Transmit) Ring - Similar but reverse:                               │
│   ─────────────────────────────────────────                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Driver fills descriptor with packet page address               │ │
│   │   2. Driver sets own=HW, signals NIC                                │ │
│   │   3. NIC reads descriptor, DMAs from page address                   │ │
│   │   4. NIC transmits packet                                           │ │
│   │   5. NIC sets own=SW (descriptor now free)                          │ │
│   │                                                                     │ │
│   │   ZERO-COPY TX with sendfile():                                     │ │
│   │   • Page cache pages can be referenced in TX descriptors            │ │
│   │   • Data flows: disk → page cache → NIC DMA                         │ │
│   │   • No CPU copy at all!                                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### NVMe and Modern Storage

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NVMe ZERO-COPY ARCHITECTURE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NVMe (Non-Volatile Memory Express) is designed for zero-copy from       │
│   the ground up, unlike legacy SATA/AHCI.                                 │
│                                                                            │
│   KEY DIFFERENCES FROM LEGACY STORAGE:                                    │
│   ────────────────────────────────────                                     │
│                                                                            │
│   SATA/AHCI:                          NVMe:                               │
│   ┌──────────────────────┐            ┌──────────────────────┐            │
│   │ • Single command     │            │ • 65,535 queues      │            │
│   │   queue               │            │ • 65,536 cmds/queue  │            │
│   │ • Max 32 commands    │            │ • Direct PCIe attach │            │
│   │ • SATA layer overhead│            │ • Minimal protocol   │            │
│   │ • Register-based     │            │ • Memory-mapped      │            │
│   └──────────────────────┘            └──────────────────────┘            │
│                                                                            │
│   NVMe SUBMISSION/COMPLETION QUEUE ARCHITECTURE:                          │
│   ──────────────────────────────────────────────                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU/Driver                              NVMe Controller           │ │
│   │   ┌───────────────────┐                  ┌───────────────────┐     │ │
│   │   │ Submission Queue  │────────────────► │  Command          │     │ │
│   │   │ (in host memory)  │    Doorbell      │  Processing       │     │ │
│   │   └───────────────────┘                  │                   │     │ │
│   │           │                               │                   │     │ │
│   │           │ Commands contain:            │                   │     │ │
│   │           │ • Physical Region Pages (PRP)│         │         │     │ │
│   │           │   or Scatter-Gather Lists    │         │ DMA     │     │ │
│   │           │ • LBA (disk location)        │         ▼         │     │ │
│   │           │ • Operation (read/write)     │  ┌───────────┐    │     │ │
│   │           │                               │  │ NVMe DMA  │    │     │ │
│   │           ▼                               │  │  Engine   │    │     │ │
│   │   ┌───────────────────┐                  │  └───────────┘    │     │ │
│   │   │ Data Buffers      │◄─────────────────┼──────────┘        │     │ │
│   │   │ (page cache)      │    Direct DMA    │                   │     │ │
│   │   └───────────────────┘                  │                   │     │ │
│   │                                           │                   │     │ │
│   │   ┌───────────────────┐                  │                   │     │ │
│   │   │ Completion Queue  │◄─────────────────┤  Completion       │     │ │
│   │   │ (in host memory)  │    DMA + IRQ     │  Posted           │     │ │
│   │   └───────────────────┘                  └───────────────────┘     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PHYSICAL REGION PAGES (PRP):                                            │
│   ────────────────────────────                                             │
│                                                                            │
│   NVMe commands include PRP entries pointing to data locations:           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────┐             │
│   │  NVMe Command (64 bytes)                                 │             │
│   │  ┌─────────────────────────────────────────────────────┐│             │
│   │  │ Opcode: Read                                         ││             │
│   │  │ NSID: 1 (namespace)                                  ││             │
│   │  │ SLBA: 1000 (starting LBA)                            ││             │
│   │  │ NLB: 8 (8 blocks = 4KB each = 32KB)                  ││             │
│   │  │ PRP1: 0x1000000 (first 4KB page physical addr)       ││             │
│   │  │ PRP2: 0x2000000 (PRP list for remaining pages)       ││             │
│   │  └─────────────────────────────────────────────────────┘│             │
│   └─────────────────────────────────────────────────────────┘             │
│                                                                            │
│   Controller DMAs directly to/from specified pages = ZERO COPY!           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Network Stack Zero-Copy

### Socket Buffer (sk_buff) Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sk_buff STRUCTURE FOR ZERO-COPY                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   sk_buff is the fundamental network packet structure in Linux.           │
│   It's designed to minimize copying as packets traverse the stack.        │
│                                                                            │
│   struct sk_buff {                                                        │
│       /* Packet metadata */                                               │
│       struct sk_buff *next, *prev;    /* Queue linkage */                 │
│       struct sock *sk;                 /* Owning socket */                 │
│       struct net_device *dev;          /* Device */                        │
│                                                                            │
│       /* Pointers into data buffer */                                     │
│       unsigned char *head;             /* Start of buffer */              │
│       unsigned char *data;             /* Start of data */                │
│       unsigned char *tail;             /* End of data */                  │
│       unsigned char *end;              /* End of buffer */                │
│                                                                            │
│       /* ZERO-COPY SUPPORT: Page fragments */                             │
│       struct skb_shared_info *shinfo;  /* Shared data */                  │
│   };                                                                       │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  sk_buff memory layout:                                              │ │
│   │                                                                      │ │
│   │  ┌────────────────────────────────────────────────────────────────┐ │ │
│   │  │ sk_buff structure (metadata)                                   │ │ │
│   │  └──────────────────────────────────┬─────────────────────────────┘ │ │
│   │                                      │                               │ │
│   │                                      ▼ points to                    │ │
│   │  ┌────────────────────────────────────────────────────────────────┐ │ │
│   │  │◄──head                                                         │ │ │
│   │  │   [headroom - for adding headers]                              │ │ │
│   │  │◄──data                                                         │ │ │
│   │  │   [packet data - headers + payload]                            │ │ │
│   │  │◄──tail                                                         │ │ │
│   │  │   [tailroom - for adding trailers]                             │ │ │
│   │  │◄──end                                                          │ │ │
│   │  │   [skb_shared_info structure]                                  │ │ │
│   │  └────────────────────────────────────────────────────────────────┘ │ │
│   │                                                                      │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### skb_shared_info and Page Fragments

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY WITH PAGE FRAGMENTS                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct skb_shared_info {                                                │
│       __u8 nr_frags;                      /* Number of fragments */       │
│       __u8 tx_flags;                                                      │
│       struct sk_buff *frag_list;          /* List of skbs */              │
│       skb_frag_t frags[MAX_SKB_FRAGS];    /* Page fragments */            │
│   };                                                                       │
│                                                                            │
│   typedef struct skb_frag {                                               │
│       struct page *page;                   /* Reference to page */        │
│       __u32 page_offset;                   /* Offset in page */           │
│       __u32 size;                          /* Size of fragment */         │
│   } skb_frag_t;                                                           │
│                                                                            │
│   PAGE FRAGMENT ZERO-COPY:                                                │
│   ────────────────────────                                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sk_buff                                                           │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │ head ──► [Linear buffer: Ethernet + IP + TCP headers]       │  │ │
│   │   │ data                                                         │  │ │
│   │   │ tail                                                         │  │ │
│   │   │ end ───► skb_shared_info                                    │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   skb_shared_info                                                   │ │
│   │   ┌──────────────────────────────────────────────────────────────┐  │ │
│   │   │ nr_frags = 2                                                 │  │ │
│   │   │ frags[0]: page=0x1234, offset=0, size=4096                   │  │ │
│   │   │ frags[1]: page=0x5678, offset=2048, size=2048                │  │ │
│   │   └──────────────────────────────────────────────────────────────┘  │ │
│   │            │                    │                                   │ │
│   │            ▼                    ▼                                   │ │
│   │   ┌─────────────────┐  ┌─────────────────┐                         │ │
│   │   │   Page Cache    │  │   Page Cache    │                         │ │
│   │   │   Page 0x1234   │  │   Page 0x5678   │                         │ │
│   │   │   [file data]   │  │   [file data]   │                         │ │
│   │   └─────────────────┘  └─────────────────┘                         │ │
│   │                                                                     │ │
│   │   DATA NEVER COPIED! sk_buff just references page cache pages.     │ │
│   │   NIC uses scatter-gather to DMA directly from these pages.        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### TCP Zero-Copy Send

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TCP ZERO-COPY SEND PATH                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   With sendfile() or MSG_ZEROCOPY, TCP can send data without copying.    │
│                                                                            │
│   SENDFILE() ZERO-COPY SEND:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  User:  sendfile(sock_fd, file_fd, NULL, 1MB)                      │ │
│   │            │                                                        │ │
│   │            ▼                                                        │ │
│   │  Kernel: do_sendfile()                                             │ │
│   │            │                                                        │ │
│   │            ├──► Find file's pages in page cache                    │ │
│   │            │    (or read from disk into page cache)                │ │
│   │            │                                                        │ │
│   │            ├──► For each page:                                     │ │
│   │            │    ┌─────────────────────────────────────────────┐    │ │
│   │            │    │ 1. Get reference to page (page_ref_inc)    │    │ │
│   │            │    │ 2. Create sk_buff with page fragment       │    │ │
│   │            │    │ 3. Add TCP/IP headers to linear buffer     │    │ │
│   │            │    │ 4. Queue sk_buff for transmission          │    │ │
│   │            │    └─────────────────────────────────────────────┘    │ │
│   │            │                                                        │ │
│   │            └──► Return to user space                               │ │
│   │                                                                     │ │
│   │  Later, when NIC is ready:                                         │ │
│   │  ┌─────────────────────────────────────────────────────────────┐   │ │
│   │  │ 1. NIC driver builds TX descriptor                          │   │ │
│   │  │    - Linear buffer address (headers)                        │   │ │
│   │  │    - Page fragment addresses (from skb_shared_info)         │   │ │
│   │  │ 2. NIC DMAs headers from linear buffer                      │   │ │
│   │  │ 3. NIC DMAs payload directly from page cache pages!         │   │ │
│   │  │ 4. NIC sends packet                                         │   │ │
│   │  │ 5. sk_buff freed, page references dropped                   │   │ │
│   │  └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │  RESULT: File data went from disk → page cache → NIC               │ │
│   │          without a single CPU copy!                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### MSG_ZEROCOPY Flag

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    MSG_ZEROCOPY FOR USER BUFFERS                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   sendfile() only works for file → socket.                                │
│   MSG_ZEROCOPY enables zero-copy send() from USER buffers.                │
│                                                                            │
│   USAGE:                                                                   │
│   ──────                                                                   │
│                                                                            │
│   // Enable zero-copy on socket                                           │
│   int one = 1;                                                            │
│   setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));             │
│                                                                            │
│   // Send with MSG_ZEROCOPY flag                                          │
│   send(fd, buffer, size, MSG_ZEROCOPY);                                   │
│                                                                            │
│   // IMPORTANT: Buffer must remain valid until completion!                │
│   // Must poll for completion notification:                               │
│   struct pollfd pfd = { .fd = fd, .events = POLLERR };                    │
│   poll(&pfd, 1, -1);                                                      │
│                                                                            │
│   // Read completion notification from error queue                        │
│   char control[100];                                                      │
│   struct msghdr msg = { .msg_control = control, ... };                    │
│   recvmsg(fd, &msg, MSG_ERRQUEUE);                                        │
│   // Parse SO_EE_ORIGIN_ZEROCOPY notification                             │
│                                                                            │
│   HOW IT WORKS:                                                           │
│   ──────────────                                                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   User Space:                                                       │ │
│   │   ┌─────────────────┐                                              │ │
│   │   │ Application     │                                              │ │
│   │   │ Buffer          │ ◄── User must not modify!                    │ │
│   │   │ (pinned pages)  │                                              │ │
│   │   └────────┬────────┘                                              │ │
│   │            │                                                        │ │
│   │   Kernel: │                                                        │ │
│   │            ▼                                                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │ 1. Pin user pages (get_user_pages)                          │  │ │
│   │   │ 2. Create sk_buff referencing user pages                    │  │ │
│   │   │ 3. Queue for transmission                                   │  │ │
│   │   │ 4. NIC DMAs directly from user pages!                       │  │ │
│   │   │ 5. After transmit, notify user via error queue              │  │ │
│   │   │ 6. User can now reuse/free buffer                           │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   CAVEATS:                                                         │ │
│   │   • Only beneficial for large sends (>10KB typically)              │ │
│   │   • Page pinning has overhead                                      │ │
│   │   • Completion handling adds complexity                            │ │
│   │   • Not all NICs support it efficiently                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### AF_XDP and eBPF

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    AF_XDP: KERNEL-BYPASS ZERO-COPY                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   AF_XDP is an address family for ultra-high-performance networking.     │
│   Combines eBPF with shared memory for true zero-copy to user space.     │
│                                                                            │
│   ARCHITECTURE:                                                           │
│   ─────────────                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   User Space Application                                            │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │                                                               ││ │
│   │   │   ┌───────────────────────────────────────────────────────┐  ││ │
│   │   │   │           UMEM (User Memory)                          │  ││ │
│   │   │   │   ┌───────┬───────┬───────┬───────┬───────┬───────┐  │  ││ │
│   │   │   │   │ frame │ frame │ frame │ frame │ frame │ frame │  │  ││ │
│   │   │   │   │   0   │   1   │   2   │   3   │   4   │   5   │  │  ││ │
│   │   │   │   └───────┴───────┴───────┴───────┴───────┴───────┘  │  ││ │
│   │   │   └───────────────────────────────────────────────────────┘  ││ │
│   │   │                                                               ││ │
│   │   │   ┌──────────────┐  ┌──────────────┐                         ││ │
│   │   │   │ RX Ring      │  │ TX Ring      │   Rings are in         ││ │
│   │   │   │ (receive)    │  │ (transmit)   │   shared memory        ││ │
│   │   │   └──────┬───────┘  └──────┬───────┘                         ││ │
│   │   │          │                 │                                  ││ │
│   │   └──────────┼─────────────────┼──────────────────────────────────┘│ │
│   │              │                 │                                   │ │
│   │   ═══════════╪═════════════════╪═════════════════════════════════ │ │
│   │              │                 │          User/Kernel Boundary    │ │
│   │   Kernel:    │                 │                                   │ │
│   │              │                 │                                   │ │
│   │   ┌──────────▼─────────────────▼──────────────────────────────┐   │ │
│   │   │              XDP Program (eBPF)                           │   │ │
│   │   │   if (should_redirect(packet)) {                          │   │ │
│   │   │       return bpf_redirect_map(&xsks_map, queue_id, 0);    │   │ │
│   │   │   }                                                       │   │ │
│   │   └────────────────────────────┬──────────────────────────────┘   │ │
│   │                                │                                   │ │
│   │   ┌────────────────────────────▼──────────────────────────────┐   │ │
│   │   │                    NIC Driver                             │   │ │
│   │   │   • NIC DMAs directly to UMEM frames                      │   │ │
│   │   │   • No sk_buff allocation                                 │   │ │
│   │   │   • XDP program runs at driver level                      │   │ │
│   │   └───────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BENEFITS:                                                               │
│   ─────────                                                                │
│   • Packets land directly in user memory (true zero-copy)                 │
│   • No system calls in fast path                                          │
│   • No sk_buff overhead                                                   │
│   • 10-100x faster than traditional sockets                               │
│                                                                            │
│   USE CASES:                                                              │
│   ──────────                                                               │
│   • High-frequency trading                                                │
│   • Software routers/firewalls                                            │
│   • DDoS mitigation                                                       │
│   • Custom protocol implementations                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Kernel Data Structures

### struct page

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    struct page - THE FUNDAMENTAL UNIT                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct page is the kernel's representation of a physical page frame.   │
│   It's central to all zero-copy mechanisms.                              │
│                                                                            │
│   struct page {                                                           │
│       unsigned long flags;           /* Page state flags */               │
│       atomic_t _refcount;            /* Reference count */                │
│       atomic_t _mapcount;            /* Number of mappings */             │
│                                                                            │
│       union {                                                              │
│           struct {                   /* Page cache pages */               │
│               struct address_space *mapping;                              │
│               pgoff_t index;         /* Offset in file */                 │
│           };                                                               │
│           struct {                   /* Slab allocator */                 │
│               struct kmem_cache *slab_cache;                              │
│               void *freelist;                                             │
│           };                                                               │
│       };                                                                   │
│                                                                            │
│       struct list_head lru;          /* LRU list linkage */               │
│       void *virtual;                  /* Kernel virtual address */        │
│   };                                                                       │
│                                                                            │
│   KEY FIELDS FOR ZERO-COPY:                                               │
│   ─────────────────────────                                                │
│                                                                            │
│   _refcount: How many users reference this page                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   refcount = 1: Only page cache holds it                           │ │
│   │   refcount = 2: Page cache + one user (e.g., mmap)                 │ │
│   │   refcount = 3: Page cache + sendfile + sk_buff                    │ │
│   │                                                                     │ │
│   │   Page can only be freed when refcount drops to 0!                 │ │
│   │   This is how zero-copy works safely:                              │ │
│   │   • Multiple users share the same physical page                    │ │
│   │   • Reference counting prevents premature freeing                   │ │
│   │   • No copy needed - just increment refcount                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   mapping + index: Identifies which file this page belongs to             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   address_space = file's page cache                                │ │
│   │   index = page number within file (offset / PAGE_SIZE)             │ │
│   │                                                                     │ │
│   │   This lets kernel find pages by (file, offset) tuple.             │ │
│   │   Different processes mapping same file share same pages!          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### struct bio

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    struct bio - BLOCK I/O ABSTRACTION                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct bio represents a block I/O request, optimized for zero-copy.    │
│                                                                            │
│   struct bio {                                                            │
│       struct bio *bi_next;              /* Next bio in chain */           │
│       struct block_device *bi_bdev;     /* Target device */               │
│       unsigned int bi_opf;               /* Operation flags */            │
│       sector_t bi_iter.bi_sector;        /* Starting sector */            │
│       unsigned int bi_iter.bi_size;      /* Remaining bytes */            │
│                                                                            │
│       /* Zero-copy segment array */                                       │
│       unsigned short bi_vcnt;            /* Segment count */              │
│       struct bio_vec *bi_io_vec;         /* Segment array */              │
│   };                                                                       │
│                                                                            │
│   struct bio_vec {                                                        │
│       struct page *bv_page;              /* Page containing data */       │
│       unsigned int bv_len;               /* Segment length */             │
│       unsigned int bv_offset;            /* Offset in page */             │
│   };                                                                       │
│                                                                            │
│   HOW BIO ENABLES ZERO-COPY:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct bio                                                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ bi_bdev: /dev/sda                                           │   │ │
│   │   │ bi_sector: 1000                                             │   │ │
│   │   │ bi_vcnt: 3                                                  │   │ │
│   │   │ bi_io_vec:                                                  │   │ │
│   │   │   [0]: page=0x1000, offset=0, len=4096                      │   │ │
│   │   │   [1]: page=0x2000, offset=0, len=4096                      │   │ │
│   │   │   [2]: page=0x3000, offset=0, len=4096                      │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │           │           │           │                                 │ │
│   │           ▼           ▼           ▼                                 │ │
│   │   ┌───────────┐ ┌───────────┐ ┌───────────┐                        │ │
│   │   │Page Cache │ │Page Cache │ │Page Cache │                        │ │
│   │   │ Page A    │ │ Page B    │ │ Page C    │                        │ │
│   │   └───────────┘ └───────────┘ └───────────┘                        │ │
│   │                                                                     │ │
│   │   Block device driver converts bio_vecs to DMA descriptors.        │ │
│   │   Data transfers directly between page cache and disk!             │ │
│   │                                                                     │ │
│   │   For NVMe:                                                        │ │
│   │   • bio_vecs → Physical Region Pages (PRPs)                        │ │
│   │   • NVMe controller DMAs directly to/from these pages              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### struct pipe_buffer

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    struct pipe_buffer - SPLICE FOUNDATION                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   struct pipe_buffer is the core of splice() zero-copy.                  │
│                                                                            │
│   struct pipe_inode_info {                                                │
│       struct mutex mutex;                 /* Protects pipe */             │
│       wait_queue_head_t rd_wait, wr_wait; /* Reader/writer queues */     │
│       unsigned int head, tail;            /* Ring buffer indices */       │
│       unsigned int ring_size;             /* Number of slots */           │
│       struct pipe_buffer *bufs;           /* Buffer array */              │
│   };                                                                       │
│                                                                            │
│   struct pipe_buffer {                                                    │
│       struct page *page;                  /* Data page */                 │
│       unsigned int offset;                /* Offset in page */            │
│       unsigned int len;                   /* Data length */               │
│       const struct pipe_buf_operations *ops;  /* Operations */           │
│       unsigned int flags;                 /* Buffer flags */              │
│   };                                                                       │
│                                                                            │
│   ZERO-COPY SPLICE MECHANISM:                                             │
│   ───────────────────────────                                              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   File A                    Pipe                     Socket B      │ │
│   │   ┌─────────┐              ┌──────────────────┐      ┌─────────┐   │ │
│   │   │ Page    │              │ pipe_inode_info  │      │ sk_buff │   │ │
│   │   │ Cache   │              │ ┌──────────────┐ │      │ with    │   │ │
│   │   │         │              │ │ pipe_buffer  │ │      │ page    │   │ │
│   │   │ Page X ─┼──────────────┼─┤  page=X      ├─┼──────┼► frags  │   │ │
│   │   │         │    splice    │ │  offset=0    │ │splice│         │   │ │
│   │   │         │  (no copy!)  │ │  len=4096    │ │      │         │   │ │
│   │   │         │              │ └──────────────┘ │      │         │   │ │
│   │   └─────────┘              └──────────────────┘      └─────────┘   │ │
│   │                                                                     │ │
│   │   Page X stays in place throughout the entire transfer!            │ │
│   │   Only metadata (pointers, offsets) is passed through the pipe.    │ │
│   │                                                                     │ │
│   │   Reference counting ensures safety:                               │ │
│   │   • File A: holds page reference in page cache                     │ │
│   │   • Pipe: increments refcount when receiving                       │ │
│   │   • Socket: increments refcount when building sk_buff              │ │
│   │   • Page freed only when all drop references                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Real-World Applications

### Web Servers (nginx, Apache)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NGINX ZERO-COPY CONFIGURATION                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   nginx uses sendfile() extensively for static file serving.             │
│                                                                            │
│   CONFIGURATION:                                                          │
│   ──────────────                                                           │
│                                                                            │
│   http {                                                                  │
│       sendfile on;           # Enable sendfile() system call              │
│       tcp_nopush on;         # Use TCP_CORK for header coalescing         │
│       tcp_nodelay on;        # Disable Nagle for final packet             │
│                                                                            │
│       # For very large files                                              │
│       sendfile_max_chunk 1m; # Limit per sendfile() call                  │
│       aio threads;           # Use thread pool for disk I/O               │
│       directio 10m;          # Use O_DIRECT for files > 10MB              │
│   }                                                                        │
│                                                                            │
│   REQUEST FLOW:                                                           │
│   ─────────────                                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Client Request: GET /large-video.mp4                             │ │
│   │                                                                     │ │
│   │   1. nginx parses request, determines static file                  │ │
│   │                                                                     │ │
│   │   2. nginx builds HTTP headers in user-space buffer               │ │
│   │      ┌──────────────────────────────────┐                          │ │
│   │      │ HTTP/1.1 200 OK                  │                          │ │
│   │      │ Content-Type: video/mp4          │                          │ │
│   │      │ Content-Length: 1073741824       │                          │ │
│   │      │ ...                              │                          │ │
│   │      └──────────────────────────────────┘                          │ │
│   │                                                                     │ │
│   │   3. Send headers with write() [small copy is fine]               │ │
│   │                                                                     │ │
│   │   4. sendfile(client_fd, file_fd, &offset, 1GB)                   │ │
│   │      ┌─────────────────────────────────────────────────────────┐   │ │
│   │      │ Kernel:                                                  │   │ │
│   │      │ • Find/load pages in page cache                         │   │ │
│   │      │ • Reference pages in sk_buff structures                 │   │ │
│   │      │ • NIC DMAs directly from page cache                     │   │ │
│   │      │ • 1GB transferred with ZERO CPU copies!                 │   │ │
│   │      └─────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   5. Worker can handle other connections while I/O happens        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PERFORMANCE IMPACT:                                                     │
│   ───────────────────                                                      │
│   • Without sendfile: ~500 Mbps (CPU-bound copying)                       │
│   • With sendfile: ~10 Gbps (NIC line rate)                               │
│   • CPU usage drops from 100% to <10%                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Databases (PostgreSQL, MySQL)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DATABASE ZERO-COPY TECHNIQUES                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Databases use mmap() and direct I/O for zero-copy data access.         │
│                                                                            │
│   PostgreSQL SHARED BUFFERS:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   PostgreSQL Backend               Shared Memory                   │ │
│   │   ┌─────────────────┐             ┌──────────────────────┐         │ │
│   │   │ Query Executor  │             │   Shared Buffers     │         │ │
│   │   │                 │             │ ┌───────────────────┐│         │ │
│   │   │ "SELECT * FROM  │──────────►  │ │ Page 0 (table A) ││         │ │
│   │   │  large_table"   │   mmap'd   │ │ Page 1 (table A) ││         │ │
│   │   │                 │   access    │ │ Page 2 (index B) ││         │ │
│   │   └─────────────────┘             │ │ ...              ││         │ │
│   │                                    │ └───────────────────┘│         │ │
│   │                                    └───────────┬──────────┘         │ │
│   │                                                │                    │ │
│   │                                                │ mmap()             │ │
│   │                                                ▼                    │ │
│   │                                    ┌──────────────────────┐         │ │
│   │                                    │   Data Files         │         │ │
│   │                                    │   (on disk)          │         │ │
│   │                                    └──────────────────────┘         │ │
│   │                                                                     │ │
│   │   Benefits:                                                        │ │
│   │   • Multiple backends share same buffer cache                      │ │
│   │   • Pages loaded on demand (page fault handling)                   │ │
│   │   • Dirty pages written back asynchronously                        │ │
│   │   • OS page cache provides second level caching                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MySQL InnoDB BUFFER POOL:                                               │
│   ─────────────────────────                                                │
│                                                                            │
│   InnoDB uses its own buffer pool but can leverage:                       │
│   • O_DIRECT for bypassing OS page cache (double buffering issue)         │
│   • mmap() for certain operations                                         │
│   • AIO for asynchronous I/O                                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Message Queues (Apache Kafka)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KAFKA ZERO-COPY ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Apache Kafka is famous for its zero-copy optimizations.                 │
│   Key insight: Messages are stored in segment files and transferred       │
│   directly to consumers using sendfile().                                  │
│                                                                            │
│   BROKER ARCHITECTURE:                                                    │
│   ────────────────────                                                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Producer                 Kafka Broker              Consumer      │ │
│   │   ┌─────────┐             ┌─────────────┐           ┌─────────┐   │ │
│   │   │ App     │             │             │           │ App     │   │ │
│   │   │         │   write()   │  Segment    │ sendfile  │         │   │ │
│   │   │ Message ├────────────►│  Files      ├──────────►│ Message │   │ │
│   │   │         │  (to page   │             │ (zero-    │         │   │ │
│   │   │         │   cache)    │  .log       │  copy!)   │         │   │ │
│   │   └─────────┘             │  .index     │           └─────────┘   │ │
│   │                           │  .timeindex │                         │ │
│   │                           └─────────────┘                         │ │
│   │                                                                     │ │
│   │   WRITE PATH:                                                      │ │
│   │   ───────────                                                       │ │
│   │   1. Producer sends message over network                           │ │
│   │   2. Broker receives into socket buffer                            │ │
│   │   3. Appends to segment file (via page cache)                      │ │
│   │   4. Returns acknowledgment                                        │ │
│   │                                                                     │ │
│   │   READ PATH (ZERO-COPY):                                           │ │
│   │   ──────────────────────                                            │ │
│   │   1. Consumer requests messages at offset X                        │ │
│   │   2. Broker finds offset in index file                             │ │
│   │   3. sendfile(consumer_socket, segment_file, offset, length)       │ │
│   │   4. Data goes directly from page cache to NIC!                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DATA FLOW COMPARISON:                                                   │
│   ─────────────────────                                                    │
│                                                                            │
│   WITHOUT Zero-Copy:                                                      │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    │
│   │ Disk   │───►│ Page   │───►│ User   │───►│ Socket │───►│ NIC    │    │
│   │        │DMA │ Cache  │CPU │ Buffer │CPU │ Buffer │DMA │        │    │
│   └────────┘    └────────┘    └────────┘    └────────┘    └────────┘    │
│                    4 copies, 4 context switches                           │
│                                                                            │
│   WITH sendfile() Zero-Copy:                                              │
│   ┌────────┐    ┌────────┐    ┌────────┐                                  │
│   │ Disk   │───►│ Page   │───►│ NIC    │                                  │
│   │        │DMA │ Cache  │DMA │        │                                  │
│   └────────┘    └────────┘    └────────┘                                  │
│                    2 copies (both DMA), 2 context switches                │
│                                                                            │
│   PERFORMANCE NUMBERS:                                                    │
│   ────────────────────                                                     │
│   • Kafka can sustain 100+ MB/s per consumer with <5% CPU                 │
│   • Without zero-copy: 20-30 MB/s per consumer at 100% CPU                │
│   • Single broker can serve thousands of consumers simultaneously        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Video Streaming

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    VIDEO STREAMING ZERO-COPY                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Video streaming servers must deliver massive throughput efficiently.    │
│                                                                            │
│   ADAPTIVE BITRATE STREAMING (HLS/DASH):                                  │
│   ──────────────────────────────────────                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Storage                 CDN Edge Server              Client      │ │
│   │   ┌─────────┐            ┌────────────────┐          ┌─────────┐  │ │
│   │   │ Video   │            │                │          │ Video   │  │ │
│   │   │ Chunks  │            │  sendfile()    │          │ Player  │  │ │
│   │   │         │            │  per chunk     │          │         │  │ │
│   │   │ 720p/   │───────────►│                ├─────────►│ Buffer  │  │ │
│   │   │ 1080p/  │  Zero-copy │  No CPU for    │ HTTP     │ Decode  │  │ │
│   │   │ 4K      │            │  data path     │          │ Display │  │ │
│   │   └─────────┘            └────────────────┘          └─────────┘  │ │
│   │                                                                     │ │
│   │   Each video is split into 2-10 second chunks (segments).         │ │
│   │   Each chunk is a separate file served via sendfile().            │ │
│   │                                                                     │ │
│   │   WHY CHUNKING + SENDFILE WORKS:                                   │ │
│   │   ──────────────────────────────                                    │ │
│   │   • Chunks are 2-20 MB each (perfect for sendfile)                │ │
│   │   • Hot chunks stay in page cache                                  │ │
│   │   • CDN can serve thousands of viewers from cache                  │ │
│   │   • No encoding/decoding at CDN level                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LIVE STREAMING (RTMP → HLS):                                            │
│   ────────────────────────────                                             │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Encoder        Origin Server              Edge CDN    Viewers    │ │
│   │   ┌──────┐      ┌─────────────┐            ┌───────┐   ┌───────┐  │ │
│   │   │      │      │             │            │       │   │       │  │ │
│   │   │ Live │ RTMP │ Transcoder  │  splice()  │       │   │       │  │ │
│   │   │ Feed ├─────►│ + Segmenter ├───────────►│ Cache ├──►│ 1000s │  │ │
│   │   │      │      │             │ zero-copy  │       │   │ of    │  │ │
│   │   │      │      │ Writes to   │ to edges   │       │   │viewers│  │ │
│   │   └──────┘      │ segment     │            └───────┘   └───────┘  │ │
│   │                 │ files       │                                    │ │
│   │                 └─────────────┘                                    │ │
│   │                                                                     │ │
│   │   Live video uses splice() to move data between connections:      │ │
│   │   • RTMP input → pipe → HLS segment file                          │ │
│   │   • Segment file → sendfile() → viewer connections                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### File Servers (Samba, NFS)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILE SERVER ZERO-COPY                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Network file systems use zero-copy for high-performance file transfer. │
│                                                                            │
│   NFS (Network File System):                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   NFS Client                           NFS Server                  │ │
│   │   ┌─────────────┐                     ┌─────────────────┐          │ │
│   │   │ Application │                     │                 │          │ │
│   │   │     │       │                     │   nfsd kernel   │          │ │
│   │   │     ▼       │                     │   thread        │          │ │
│   │   │ VFS Layer   │                     │       │         │          │ │
│   │   │     │       │                     │       ▼         │          │ │
│   │   │     ▼       │     READ request    │   VFS Layer     │          │ │
│   │   │ NFS Client  │ ──────────────────► │       │         │          │ │
│   │   │ (nfs.ko)    │                     │       ▼         │          │ │
│   │   │     │       │     DATA response   │   splice()      │          │ │
│   │   │     ▼       │ ◄────────────────── │   or sendfile() │          │ │
│   │   │ Network     │    (zero-copy)      │                 │          │ │
│   │   └─────────────┘                     └─────────────────┘          │ │
│   │                                                                     │ │
│   │   Linux NFS server uses splice() for READ operations:              │ │
│   │   • File pages read into page cache                                │ │
│   │   • splice() moves page references to socket                       │ │
│   │   • NIC DMAs directly from page cache                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SMB/CIFS (Samba):                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Samba supports multiple I/O backends:                            │ │
│   │                                                                     │ │
│   │   1. Traditional:  read() → user buffer → write()                  │ │
│   │      • Works everywhere, but copies data twice                     │ │
│   │                                                                     │ │
│   │   2. sendfile:     sendfile() for reads                            │ │
│   │      • Zero-copy read path                                         │ │
│   │      • Configure: use sendfile = yes                               │ │
│   │                                                                     │ │
│   │   3. splice:       splice() for reads                              │ │
│   │      • Most flexible zero-copy                                     │ │
│   │      • Works with pipes for complex routing                        │ │
│   │                                                                     │ │
│   │   Configuration (smb.conf):                                        │ │
│   │   ─────────────────────────                                         │ │
│   │   [global]                                                          │ │
│   │       use sendfile = yes        # Enable sendfile for reads        │ │
│   │       min receivefile size = 0  # Enable splice for writes         │ │
│   │       aio read size = 16384     # Async I/O threshold              │ │
│   │       aio write size = 16384                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Performance Analysis

### Benchmarking Methodology

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BENCHMARKING ZERO-COPY                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Accurate benchmarking requires careful methodology.                     │
│                                                                            │
│   KEY METRICS:                                                            │
│   ────────────                                                             │
│                                                                            │
│   1. Throughput (MB/s or Gbps)                                            │
│      • Measure actual data transferred over time                          │
│      • Ensure network is not the bottleneck                               │
│                                                                            │
│   2. CPU Utilization (% CPU per MB)                                       │
│      • Most important metric for zero-copy effectiveness                  │
│      • Use `perf` or `vmstat` to measure                                  │
│                                                                            │
│   3. Latency (microseconds)                                               │
│      • First-byte latency vs total transfer time                          │
│      • Important for interactive applications                             │
│                                                                            │
│   4. Memory Bandwidth                                                     │
│      • Zero-copy saves memory bandwidth for other tasks                   │
│      • Measure with `perf stat -e cache-misses`                           │
│                                                                            │
│   BENCHMARK SETUP:                                                        │
│   ────────────────                                                         │
│                                                                            │
│   # Warm up page cache                                                    │
│   dd if=/dev/sda of=/dev/null bs=1M count=1000                            │
│                                                                            │
│   # Traditional copy benchmark                                            │
│   time cat /mnt/largefile | nc remote-host 9000                           │
│                                                                            │
│   # sendfile benchmark (using custom tool)                                │
│   time ./sendfile_bench /mnt/largefile remote-host 9000                   │
│                                                                            │
│   # Measure CPU usage                                                     │
│   perf stat -e cycles,instructions,cache-misses ./benchmark               │
│                                                                            │
│   IMPORTANT CONSIDERATIONS:                                               │
│   ─────────────────────────                                                │
│   • Disable CPU frequency scaling (constant clock)                        │
│   • Drop caches between runs: echo 3 > /proc/sys/vm/drop_caches           │
│   • Use large enough files (>1GB) for accurate measurement                │
│   • Run multiple iterations and report variance                           │
│   • Test with both cold cache and warm cache scenarios                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Throughput Comparisons

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THROUGHPUT COMPARISON TABLE                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Test Environment: Linux 5.15, Intel Xeon E5-2680, 10GbE NIC, NVMe SSD  │
│   File Size: 1GB, Warm Page Cache                                         │
│                                                                            │
│   ┌────────────────────┬────────────────┬────────────┬────────────────┐   │
│   │ Method             │ Throughput     │ CPU Usage  │ Context Switch │   │
│   ├────────────────────┼────────────────┼────────────┼────────────────┤   │
│   │ read() + write()   │    2.1 GB/s    │   100%     │    4 per I/O   │   │
│   │ mmap() + write()   │    3.2 GB/s    │    85%     │    2 per I/O   │   │
│   │ sendfile()         │    9.4 GB/s    │    15%     │    2 per I/O   │   │
│   │ splice()           │    9.2 GB/s    │    18%     │    2 per I/O   │   │
│   │ io_uring + splice  │    9.6 GB/s    │    12%     │    ~0          │   │
│   │ AF_XDP             │   10.0 GB/s    │     8%     │    ~0          │   │
│   └────────────────────┴────────────────┴────────────┴────────────────┘   │
│                                                                            │
│   ANALYSIS:                                                               │
│   ─────────                                                                │
│                                                                            │
│   • read()+write(): CPU-bound at 100%, limited to memory copy speed       │
│   • mmap()+write(): Saves one copy, but still copies to socket buffer     │
│   • sendfile(): Near line rate, dramatic CPU reduction                    │
│   • splice(): Similar to sendfile, more flexible                          │
│   • io_uring: Eliminates system call overhead                             │
│   • AF_XDP: Kernel bypass achieves theoretical maximum                    │
│                                                                            │
│   FILE SIZE IMPACT:                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   ┌────────────────┬────────────────────────────────────────────────────┐ │
│   │ File Size      │ Zero-Copy Benefit                                  │ │
│   ├────────────────┼────────────────────────────────────────────────────┤ │
│   │ < 4 KB         │ Minimal - system call overhead dominates           │ │
│   │ 4 KB - 64 KB   │ Small - copy is cheap, setup overhead matters      │ │
│   │ 64 KB - 1 MB   │ Moderate - zero-copy starts winning                │ │
│   │ 1 MB - 100 MB  │ Significant - clear throughput improvement         │ │
│   │ > 100 MB       │ Dramatic - CPU savings enable parallelism          │ │
│   └────────────────┴────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### CPU Utilization

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CPU COST ANALYSIS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CPU cycles spent per MB of data transferred:                            │
│                                                                            │
│   TRADITIONAL I/O (read + send):                                          │
│   ──────────────────────────────                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU Operation               Cycles (approx)    % of Total        │ │
│   │   ─────────────────────────────────────────────────────────────    │ │
│   │   read() system call          ~1,000              1%               │ │
│   │   Page cache lookup           ~500                <1%              │ │
│   │   memcpy kernel→user          ~2,000,000          45%              │ │
│   │   send() system call          ~1,000              1%               │ │
│   │   memcpy user→kernel          ~2,000,000          45%              │ │
│   │   TCP/IP processing           ~300,000            7%               │ │
│   │   ───────────────────────────────────────────────────────────      │ │
│   │   TOTAL per MB                ~4,302,500                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SENDFILE() ZERO-COPY:                                                   │
│   ─────────────────────                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU Operation               Cycles (approx)    % of Total        │ │
│   │   ─────────────────────────────────────────────────────────────    │ │
│   │   sendfile() system call      ~1,500              <1%              │ │
│   │   Page cache lookup           ~500                <1%              │ │
│   │   Page reference management   ~5,000              2%               │ │
│   │   sk_buff setup               ~10,000             4%               │ │
│   │   TCP/IP processing           ~300,000            93%              │ │
│   │   memcpy (NONE!)              0                   0%               │ │
│   │   ───────────────────────────────────────────────────────────      │ │
│   │   TOTAL per MB                ~317,000                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IMPROVEMENT: 4,302,500 / 317,000 = 13.6x fewer CPU cycles!             │
│                                                                            │
│   This means:                                                             │
│   • Same CPU can handle 13x more concurrent transfers                    │
│   • More CPU available for application logic                              │
│   • Lower power consumption (important for data centers)                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Latency Considerations

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LATENCY ANALYSIS                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Zero-copy affects latency in nuanced ways.                              │
│                                                                            │
│   FIRST-BYTE LATENCY:                                                     │
│   ───────────────────                                                      │
│                                                                            │
│   Traditional:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ syscall → page lookup → copy to user → syscall → copy to kernel →  │ │
│   │ → TCP → NIC queue → FIRST BYTE OUT                                  │ │
│   │                                                                     │ │
│   │ Time: ~20-50 microseconds                                           │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   sendfile():                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ syscall → page lookup → sk_buff setup → TCP → NIC queue → FIRST    │ │
│   │ BYTE OUT                                                            │ │
│   │                                                                     │ │
│   │ Time: ~10-20 microseconds                                           │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HOWEVER - PAGE FAULT CASE:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   If page is NOT in cache:                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sendfile() with COLD cache:                                       │ │
│   │                                                                     │ │
│   │   syscall → page lookup → PAGE FAULT → disk I/O → wait ~5-10ms →   │ │
│   │   → sk_buff setup → TCP → NIC                                      │ │
│   │                                                                     │ │
│   │   With mmap() + read-ahead, you might pre-fault pages              │ │
│   │   before the sendfile() call.                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LATENCY OPTIMIZATION TECHNIQUES:                                        │
│   ────────────────────────────────                                         │
│                                                                            │
│   1. posix_fadvise(fd, 0, len, POSIX_FADV_WILLNEED)                       │
│      • Hint to kernel to prefetch pages                                   │
│                                                                            │
│   2. madvise(addr, len, MADV_WILLNEED)                                    │
│      • For mmap'd regions, trigger read-ahead                             │
│                                                                            │
│   3. io_uring with IORING_OP_READ + IOSQE_ASYNC                           │
│      • Async prefetch before sendfile                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### When Zero-Copy Hurts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHEN ZERO-COPY IS NOT BENEFICIAL                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Zero-copy is not always the best choice. Understanding the trade-offs  │
│   helps choose the right approach.                                        │
│                                                                            │
│   SITUATIONS WHERE ZERO-COPY HURTS:                                       │
│   ──────────────────────────────────                                       │
│                                                                            │
│   1. SMALL DATA TRANSFERS (< 16 KB)                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Why: System call overhead dominates                               │ │
│   │        sendfile() setup cost > memcpy cost                          │ │
│   │                                                                     │ │
│   │   Better: Just use write() - simple and fast                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   2. DATA REQUIRES TRANSFORMATION                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Examples:                                                         │ │
│   │   • Compression (gzip, zstd)                                        │ │
│   │   • Encryption (TLS in userspace)                                   │ │
│   │   • Transcoding (video format conversion)                           │ │
│   │   • Protocol transformation                                         │ │
│   │                                                                     │ │
│   │   You MUST read data to transform it - zero-copy impossible         │ │
│   │                                                                     │ │
│   │   Exception: Kernel TLS (kTLS) enables zero-copy with encryption!  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   3. RANDOM ACCESS PATTERNS                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sendfile() is optimized for sequential access                     │ │
│   │                                                                     │ │
│   │   Random access causes:                                             │ │
│   │   • Poor page cache utilization                                     │ │
│   │   • Many small sendfile() calls                                     │ │
│   │   • System call overhead accumulates                                │ │
│   │                                                                     │ │
│   │   Better: mmap() + manual buffer management                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   4. MEMORY-CONSTRAINED SYSTEMS                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   mmap() and page cache tie up memory                               │ │
│   │                                                                     │ │
│   │   Issues:                                                           │ │
│   │   • Large files can evict other useful pages                        │ │
│   │   • Page pinning prevents memory reclaim                            │ │
│   │   • MSG_ZEROCOPY requires keeping user pages pinned                 │ │
│   │                                                                     │ │
│   │   Consider: O_DIRECT + userspace buffer pooling                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   5. HIGH-LATENCY NETWORKS                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   With high RTT, TCP congestion window limits throughput            │ │
│   │   Zero-copy benefits diminish when network is the bottleneck        │ │
│   │                                                                     │ │
│   │   Zero-copy shines: High-bandwidth, low-latency (data center)       │ │
│   │   Less impact: WAN, mobile networks, high-latency links             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Practical Implementation

### Building a Zero-Copy File Server

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY FILE SERVER EXAMPLE                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   A production-quality zero-copy file server implementation.              │
│                                                                            │
│   #include <sys/sendfile.h>                                               │
│   #include <sys/socket.h>                                                 │
│   #include <sys/stat.h>                                                   │
│   #include <fcntl.h>                                                      │
│   #include <errno.h>                                                      │
│                                                                            │
│   int serve_file_zerocopy(int client_fd, const char *filepath) {          │
│       struct stat st;                                                     │
│       int file_fd;                                                        │
│       off_t offset = 0;                                                   │
│       ssize_t sent, total = 0;                                            │
│                                                                            │
│       // Open file                                                        │
│       file_fd = open(filepath, O_RDONLY);                                 │
│       if (file_fd < 0) {                                                  │
│           return -1;                                                      │
│       }                                                                    │
│                                                                            │
│       // Get file size                                                    │
│       if (fstat(file_fd, &st) < 0) {                                      │
│           close(file_fd);                                                 │
│           return -1;                                                      │
│       }                                                                    │
│                                                                            │
│       // Hint kernel to prefetch (optional but helps latency)            │
│       posix_fadvise(file_fd, 0, st.st_size, POSIX_FADV_SEQUENTIAL);       │
│       posix_fadvise(file_fd, 0, st.st_size, POSIX_FADV_WILLNEED);         │
│                                                                            │
│       // Enable TCP_CORK to coalesce headers with data                   │
│       int cork = 1;                                                       │
│       setsockopt(client_fd, IPPROTO_TCP, TCP_CORK, &cork, sizeof(cork));  │
│                                                                            │
│       // Send HTTP headers (small - regular write is fine)               │
│       char headers[256];                                                  │
│       int hlen = snprintf(headers, sizeof(headers),                       │
│           "HTTP/1.1 200 OK\r\n"                                           │
│           "Content-Length: %ld\r\n"                                       │
│           "Content-Type: application/octet-stream\r\n\r\n",               │
│           (long)st.st_size);                                              │
│       write(client_fd, headers, hlen);                                    │
│                                                                            │
│       // ZERO-COPY TRANSFER                                               │
│       while (total < st.st_size) {                                        │
│           sent = sendfile(client_fd, file_fd, &offset,                    │
│                           st.st_size - total);                            │
│           if (sent < 0) {                                                 │
│               if (errno == EINTR) continue;  // Interrupted              │
│               if (errno == EAGAIN) {                                      │
│                   // Socket buffer full - wait for writability           │
│                   // (in production, use epoll here)                     │
│                   usleep(1000);                                           │
│                   continue;                                               │
│               }                                                            │
│               break;  // Real error                                       │
│           }                                                                │
│           total += sent;                                                  │
│       }                                                                    │
│                                                                            │
│       // Disable TCP_CORK to flush remaining data                        │
│       cork = 0;                                                           │
│       setsockopt(client_fd, IPPROTO_TCP, TCP_CORK, &cork, sizeof(cork));  │
│                                                                            │
│       close(file_fd);                                                     │
│       return (total == st.st_size) ? 0 : -1;                              │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Error Handling Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY ERROR HANDLING                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Robust error handling is critical for production zero-copy code.        │
│                                                                            │
│   COMMON ERROR CONDITIONS:                                                │
│   ────────────────────────                                                 │
│                                                                            │
│   ┌──────────────┬────────────────────────────────────────────────────┐   │
│   │ Error        │ Meaning and Response                                │   │
│   ├──────────────┼────────────────────────────────────────────────────┤   │
│   │ EAGAIN       │ Socket buffer full, non-blocking mode.             │   │
│   │              │ → Wait for EPOLLOUT, retry sendfile.               │   │
│   ├──────────────┼────────────────────────────────────────────────────┤   │
│   │ EINTR        │ Signal interrupted the call.                       │   │
│   │              │ → Retry immediately from current offset.           │   │
│   ├──────────────┼────────────────────────────────────────────────────┤   │
│   │ EINVAL       │ Invalid arguments (bad fd type, etc).              │   │
│   │              │ → Fall back to read()+write().                     │   │
│   ├──────────────┼────────────────────────────────────────────────────┤   │
│   │ ENOSYS       │ sendfile() not supported on this kernel.           │   │
│   │              │ → Fall back to read()+write().                     │   │
│   ├──────────────┼────────────────────────────────────────────────────┤   │
│   │ EPIPE/       │ Connection closed by peer.                         │   │
│   │ ECONNRESET   │ → Clean up and close connection.                   │   │
│   ├──────────────┼────────────────────────────────────────────────────┤   │
│   │ EIO          │ Disk I/O error while reading file.                 │   │
│   │              │ → Log error, return 500 to client.                 │   │
│   └──────────────┴────────────────────────────────────────────────────┘   │
│                                                                            │
│   ROBUST SENDFILE WRAPPER:                                                │
│   ────────────────────────                                                 │
│                                                                            │
│   ssize_t safe_sendfile(int out_fd, int in_fd,                            │
│                         off_t *offset, size_t count) {                    │
│       ssize_t written;                                                    │
│                                                                            │
│   retry:                                                                  │
│       written = sendfile(out_fd, in_fd, offset, count);                   │
│                                                                            │
│       if (written < 0) {                                                  │
│           switch (errno) {                                                │
│           case EINTR:                                                     │
│               goto retry;                                                 │
│                                                                            │
│           case EAGAIN:                                                    │
│               return 0;  // Caller should poll for EPOLLOUT              │
│                                                                            │
│           case EINVAL:                                                    │
│           case ENOSYS:                                                    │
│               return -2; // Signal: use fallback method                  │
│                                                                            │
│           default:                                                        │
│               return -1; // Real error                                   │
│           }                                                                │
│       }                                                                    │
│                                                                            │
│       return written;                                                     │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Fallback Strategies

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FALLBACK STRATEGY PATTERN                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Production code should gracefully degrade when zero-copy fails.         │
│                                                                            │
│   FALLBACK HIERARCHY:                                                     │
│   ────────────────────                                                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Try sendfile()                                                    │ │
│   │        │                                                            │ │
│   │        ├── Success ──► Done (optimal)                               │ │
│   │        │                                                            │ │
│   │        └── EINVAL/ENOSYS ──► Try mmap()+write()                     │ │
│   │                                    │                                │ │
│   │                                    ├── Success ──► Done (good)      │ │
│   │                                    │                                │ │
│   │                                    └── Failed ──► read()+write()    │ │
│   │                                                        │            │ │
│   │                                                        └─► Done     │ │
│   │                                                           (works    │ │
│   │                                                          everywhere)│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IMPLEMENTATION:                                                         │
│   ───────────────                                                          │
│                                                                            │
│   typedef enum {                                                          │
│       TRANSFER_SENDFILE,                                                  │
│       TRANSFER_MMAP,                                                      │
│       TRANSFER_READWRITE                                                  │
│   } transfer_method_t;                                                    │
│                                                                            │
│   static transfer_method_t preferred_method = TRANSFER_SENDFILE;          │
│                                                                            │
│   ssize_t transfer_file(int out_fd, int in_fd, size_t size) {             │
│       ssize_t result;                                                     │
│                                                                            │
│       switch (preferred_method) {                                         │
│       case TRANSFER_SENDFILE:                                             │
│           result = try_sendfile(out_fd, in_fd, size);                     │
│           if (result >= 0) return result;                                 │
│           if (result == -2) {  // Not supported                          │
│               preferred_method = TRANSFER_MMAP;                           │
│               // Fall through                                             │
│           } else {                                                        │
│               return result;  // Real error                              │
│           }                                                                │
│           // FALLTHROUGH                                                  │
│                                                                            │
│       case TRANSFER_MMAP:                                                 │
│           result = try_mmap_write(out_fd, in_fd, size);                   │
│           if (result >= 0) return result;                                 │
│           preferred_method = TRANSFER_READWRITE;                          │
│           // FALLTHROUGH                                                  │
│                                                                            │
│       case TRANSFER_READWRITE:                                            │
│           return do_read_write(out_fd, in_fd, size);                      │
│       }                                                                    │
│       return -1;                                                          │
│   }                                                                        │
│                                                                            │
│   KEY INSIGHT: Cache the preferred method!                                │
│   Don't retry sendfile() if it already failed with ENOSYS.                │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Platform Portability

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CROSS-PLATFORM ZERO-COPY                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Zero-copy APIs vary significantly across operating systems.             │
│                                                                            │
│   ┌─────────────┬───────────────────────────────────────────────────────┐ │
│   │ Platform    │ Zero-Copy APIs                                        │ │
│   ├─────────────┼───────────────────────────────────────────────────────┤ │
│   │ Linux       │ sendfile(), splice(), tee(), vmsplice()               │ │
│   │             │ io_uring, AF_XDP                                      │ │
│   ├─────────────┼───────────────────────────────────────────────────────┤ │
│   │ FreeBSD     │ sendfile() with different signature!                  │ │
│   │             │ sf_hdtr for headers/trailers                          │ │
│   ├─────────────┼───────────────────────────────────────────────────────┤ │
│   │ macOS       │ sendfile() similar to FreeBSD                         │ │
│   │             │ Limited compared to Linux                             │ │
│   ├─────────────┼───────────────────────────────────────────────────────┤ │
│   │ Windows     │ TransmitFile()                                        │ │
│   │             │ Different API entirely                                │ │
│   ├─────────────┼───────────────────────────────────────────────────────┤ │
│   │ Solaris     │ sendfilev() - scatter-gather sendfile                 │ │
│   └─────────────┴───────────────────────────────────────────────────────┘ │
│                                                                            │
│   LINUX vs BSD SENDFILE:                                                  │
│   ──────────────────────                                                   │
│                                                                            │
│   // Linux                                                                │
│   ssize_t sendfile(int out_fd, int in_fd,                                 │
│                    off_t *offset, size_t count);                          │
│                                                                            │
│   // FreeBSD/macOS                                                        │
│   int sendfile(int fd, int s, off_t offset, size_t nbytes,                │
│                struct sf_hdtr *hdtr, off_t *sbytes, int flags);           │
│                                                                            │
│   Note: Arguments are in DIFFERENT ORDER!                                 │
│         Return value semantics differ!                                    │
│                                                                            │
│   PORTABLE WRAPPER:                                                       │
│   ─────────────────                                                        │
│                                                                            │
│   #if defined(__linux__)                                                  │
│   ssize_t portable_sendfile(int sockfd, int filefd,                       │
│                             off_t offset, size_t count) {                 │
│       return sendfile(sockfd, filefd, &offset, count);                    │
│   }                                                                        │
│   #elif defined(__FreeBSD__) || defined(__APPLE__)                        │
│   ssize_t portable_sendfile(int sockfd, int filefd,                       │
│                             off_t offset, size_t count) {                 │
│       off_t sent = 0;                                                     │
│       int rc = sendfile(filefd, sockfd, offset, count, NULL, &sent, 0);   │
│       return (rc == 0 || errno == EAGAIN) ? sent : -1;                    │
│   }                                                                        │
│   #else                                                                   │
│   // Fallback to read()+write()                                           │
│   #endif                                                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Summary and Appendix

### Zero-Copy Decision Tree

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY DECISION TREE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Use this flowchart to choose the right zero-copy technique.             │
│                                                                            │
│                        ┌─────────────────────┐                             │
│                        │  Need to transfer   │                             │
│                        │       data?         │                             │
│                        └─────────┬───────────┘                             │
│                                  │                                         │
│                                  ▼                                         │
│                   ┌──────────────────────────────┐                         │
│                   │  Does data need to be        │                         │
│                   │  transformed (compress,      │                         │
│                   │  encrypt, transcode)?        │                         │
│                   └──────────────┬───────────────┘                         │
│                                  │                                         │
│              ┌───────────────────┴───────────────────┐                     │
│              │YES                                 NO │                     │
│              ▼                                       ▼                     │
│   ┌──────────────────────┐            ┌──────────────────────┐            │
│   │ Zero-copy won't help │            │ What's the source?   │            │
│   │ Use read()+transform │            └──────────┬───────────┘            │
│   │ +write()             │                       │                        │
│   │                      │      ┌────────────────┼────────────────┐       │
│   │ Exception: kTLS for  │      │                │                │       │
│   │ encryption!          │      ▼                ▼                ▼       │
│   └──────────────────────┘   FILE           PIPE/FD          USER BUF     │
│                               │                │                │         │
│                               ▼                ▼                ▼         │
│                    ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐   │
│                    │ What's the      │ │ splice()    │ │ MSG_ZEROCOPY │   │
│                    │ destination?    │ │ (Linux)     │ │ or vmsplice()│   │
│                    └───────┬─────────┘ └─────────────┘ │ (if large)   │   │
│                            │                           └──────────────┘   │
│           ┌────────────────┼────────────────┐                             │
│           │                │                │                             │
│           ▼                ▼                ▼                             │
│        SOCKET           FILE         ANOTHER PIPE                         │
│           │                │                │                             │
│           ▼                ▼                ▼                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                       │
│   │ sendfile()  │  │ copy_file   │  │ splice()    │                       │
│   │ (Linux/BSD) │  │ _range()    │  │ or tee()    │                       │
│   └──────┬──────┘  └─────────────┘  └─────────────┘                       │
│          │                                                                 │
│          ▼                                                                 │
│   ┌──────────────────────────────┐                                        │
│   │ Is it high-throughput?       │                                        │
│   │ (> 10 Gbps network)          │                                        │
│   └──────────────┬───────────────┘                                        │
│                  │                                                         │
│     ┌────────────┴────────────┐                                           │
│     │YES                   NO │                                           │
│     ▼                         ▼                                           │
│  ┌─────────────────┐   ┌─────────────────┐                                │
│  │ Consider:       │   │ sendfile() is   │                                │
│  │ • AF_XDP        │   │ probably enough │                                │
│  │ • io_uring      │   └─────────────────┘                                │
│  │ • DPDK          │                                                      │
│  └─────────────────┘                                                      │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### System Call Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY SYSTEM CALL REFERENCE                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SENDFILE (Linux)                                                        │
│   ────────────────                                                         │
│   #include <sys/sendfile.h>                                               │
│                                                                            │
│   ssize_t sendfile(int out_fd,        // Destination (socket)             │
│                    int in_fd,         // Source (regular file)            │
│                    off_t *offset,     // Starting position (updated)      │
│                    size_t count);     // Bytes to transfer                │
│                                                                            │
│   Returns: Bytes sent, or -1 on error                                     │
│   Key Errors: EAGAIN, EINVAL (bad fd type), ENOSYS                        │
│   Notes: in_fd must support mmap (regular file)                           │
│          out_fd must be a socket                                          │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   SPLICE (Linux 2.6.17+)                                                  │
│   ──────────────────────                                                   │
│   #include <fcntl.h>                                                      │
│                                                                            │
│   ssize_t splice(int fd_in,           // Source fd                        │
│                  off64_t *off_in,     // Source offset (or NULL)          │
│                  int fd_out,          // Destination fd                   │
│                  off64_t *off_out,    // Dest offset (or NULL)            │
│                  size_t len,          // Bytes to transfer                │
│                  unsigned int flags); // SPLICE_F_MOVE, SPLICE_F_NONBLOCK │
│                                                                            │
│   Returns: Bytes transferred, 0 on EOF, -1 on error                       │
│   Requirement: At least one fd must be a pipe                             │
│   Flags:                                                                  │
│     SPLICE_F_MOVE     - Hint to move pages (rarely works)                 │
│     SPLICE_F_NONBLOCK - Don't block on pipe                               │
│     SPLICE_F_MORE     - More data coming (like MSG_MORE)                  │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   TEE (Linux 2.6.17+)                                                     │
│   ───────────────────                                                      │
│   #include <fcntl.h>                                                      │
│                                                                            │
│   ssize_t tee(int fd_in,              // Source pipe                      │
│               int fd_out,             // Destination pipe                 │
│               size_t len,             // Max bytes to duplicate           │
│               unsigned int flags);    // SPLICE_F_NONBLOCK                │
│                                                                            │
│   Returns: Bytes duplicated, -1 on error                                  │
│   Notes: Does NOT consume data from source pipe                           │
│          Both fds must be pipe read/write ends                            │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   VMSPLICE (Linux 2.6.17+)                                                │
│   ────────────────────────                                                 │
│   #include <fcntl.h>                                                      │
│                                                                            │
│   ssize_t vmsplice(int fd,            // Pipe fd                          │
│                    const struct iovec *iov,  // User buffers              │
│                    size_t nr_segs,    // Number of segments               │
│                    unsigned int flags);                                   │
│                                                                            │
│   Flags:                                                                  │
│     SPLICE_F_GIFT - Transfer ownership of pages to kernel                 │
│                     (caller must not modify buffer!)                      │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   MMAP                                                                    │
│   ────                                                                     │
│   #include <sys/mman.h>                                                   │
│                                                                            │
│   void *mmap(void *addr,              // Suggested address (usually NULL) │
│              size_t length,           // Mapping size                     │
│              int prot,                // PROT_READ, PROT_WRITE            │
│              int flags,               // MAP_SHARED, MAP_PRIVATE          │
│              int fd,                  // File descriptor                  │
│              off_t offset);           // File offset                      │
│                                                                            │
│   Returns: Mapped address, or MAP_FAILED on error                         │
│   Related: munmap(), madvise(), mlock()                                   │
│                                                                            │
│   ─────────────────────────────────────────────────────────────────────── │
│                                                                            │
│   COPY_FILE_RANGE (Linux 4.5+)                                            │
│   ────────────────────────────                                             │
│   #include <unistd.h>                                                     │
│                                                                            │
│   ssize_t copy_file_range(int fd_in,          // Source file              │
│                           off64_t *off_in,    // Source offset            │
│                           int fd_out,         // Destination file         │
│                           off64_t *off_out,   // Dest offset              │
│                           size_t len,         // Bytes to copy            │
│                           unsigned int flags);// Reserved (0)            │
│                                                                            │
│   Notes: Server-side copy on NFS/SMB                                      │
│          CoW reflink on Btrfs/XFS                                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### Performance Comparison Summary

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ZERO-COPY PERFORMANCE SUMMARY                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TECHNIQUE COMPARISON:                                                   │
│   ─────────────────────                                                    │
│                                                                            │
│   ┌────────────────┬────────┬─────────┬────────┬──────────┬────────────┐  │
│   │ Technique      │ Copies │ Context │ CPU    │ Best For │ Limitation │  │
│   │                │        │ Switch  │ Usage  │          │            │  │
│   ├────────────────┼────────┼─────────┼────────┼──────────┼────────────┤  │
│   │ read()+write() │   4    │    4    │ HIGH   │ Small    │ Copies     │  │
│   │                │        │         │        │ data     │ data twice │  │
│   ├────────────────┼────────┼─────────┼────────┼──────────┼────────────┤  │
│   │ mmap()+write() │   3    │    2    │ MEDIUM │ Random   │ Page fault │  │
│   │                │        │         │        │ access   │ latency    │  │
│   ├────────────────┼────────┼─────────┼────────┼──────────┼────────────┤  │
│   │ sendfile()     │   2    │    2    │ LOW    │ File to  │ Socket     │  │
│   │                │        │         │        │ socket   │ only dest  │  │
│   ├────────────────┼────────┼─────────┼────────┼──────────┼────────────┤  │
│   │ splice()       │   2    │    2    │ LOW    │ Pipe-    │ Need pipe  │  │
│   │                │        │         │        │ based    │ buffer     │  │
│   ├────────────────┼────────┼─────────┼────────┼──────────┼────────────┤  │
│   │ MSG_ZEROCOPY   │   0    │    2    │ V.LOW  │ Large    │ Completion │  │
│   │                │        │         │        │ sends    │ handling   │  │
│   ├────────────────┼────────┼─────────┼────────┼──────────┼────────────┤  │
│   │ AF_XDP         │   0    │    ~0   │ V.LOW  │ Extreme  │ Complexity │  │
│   │                │        │         │        │ perf     │            │  │
│   └────────────────┴────────┴─────────┴────────┴──────────┴────────────┘  │
│                                                                            │
│   WHERE COPIES HAPPEN:                                                    │
│   ────────────────────                                                     │
│                                                                            │
│   Traditional (4 copies):                                                 │
│     Disk ─DMA→ Page Cache ─CPU→ User Buffer ─CPU→ Socket ─DMA→ NIC        │
│                                                                            │
│   sendfile() with DMA gather (2 copies):                                  │
│     Disk ─DMA→ Page Cache ──────────────────────────────DMA→ NIC          │
│                               (page references only)                      │
│                                                                            │
│   AF_XDP (0 copies):                                                      │
│     NIC ←─────── Shared UMEM ───────→ User Space                          │
│           (same physical memory)                                          │
│                                                                            │
│   FILE SIZE RECOMMENDATIONS:                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   ┌──────────────────┬───────────────────────────────────────────────┐    │
│   │ File Size        │ Recommended Approach                          │    │
│   ├──────────────────┼───────────────────────────────────────────────┤    │
│   │ < 4 KB           │ Just use write() - overhead not worth it      │    │
│   │ 4 KB - 64 KB     │ Consider sendfile() if many concurrent reqs   │    │
│   │ 64 KB - 100 MB   │ Use sendfile() - clear benefit                │    │
│   │ > 100 MB         │ sendfile() + posix_fadvise() for prefetch     │    │
│   │ Streaming (TB+)  │ splice() with chunked transfer                │    │
│   └──────────────────┴───────────────────────────────────────────────┘    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```



### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE COMPLETE ZERO-COPY ARCHITECTURE                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   This diagram shows how all zero-copy components work together.          │
│                                                                            │
│  ═══════════════════════════════════════════════════════════════════════  │
│  ║                           USER SPACE                                 ║  │
│  ║                                                                      ║  │
│  ║  ┌────────────────────────────────────────────────────────────────┐ ║  │
│  ║  │                     APPLICATION                                 │ ║  │
│  ║  │                                                                 │ ║  │
│  ║  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │ ║  │
│  ║  │   │  User       │  │   mmap'd    │  │    AF_XDP           │   │ ║  │
│  ║  │   │  Buffers    │  │   Region    │  │    UMEM             │   │ ║  │
│  ║  │   └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │ ║  │
│  ║  │          │                │                    │               │ ║  │
│  ║  │          │ vmsplice()     │ write()            │ XDP socket   │ ║  │
│  ║  │          │ MSG_ZEROCOPY   │ (zero-copy if      │ (complete    │ ║  │
│  ║  │          ▼                │  same pages)       │  bypass)     │ ║  │
│  ║  └──────────┼────────────────┼────────────────────┼───────────────┘ ║  │
│  ║             │                │                    │                 ║  │
│  ═══════════════════════════════╪════════════════════╪═════════════════  │
│  ───────────── │ ───────────────│─────────────────── │ ────────────────  │
│                │                │                    │                   │
│  SYSTEM CALL   │ splice()       │ sendfile()         │                   │
│  INTERFACE     │ vmsplice()     │                    │                   │
│                │ tee()          │                    │                   │
│  ───────────── ▼ ───────────────▼─────────────────── │ ────────────────  │
│  ═══════════════════════════════════════════════════╪═════════════════  │
│  ║                       KERNEL SPACE               │                 ║  │
│  ║                                                  │                 ║  │
│  ║  ┌─────────────────────────────────────────┐    │                 ║  │
│  ║  │           VIRTUAL FILE SYSTEM (VFS)      │    │                 ║  │
│  ║  │                                          │    │                 ║  │
│  ║  │   file_operations:                       │    │                 ║  │
│  ║  │     .splice_read()   .splice_write()    │    │                 ║  │
│  ║  │     .sendfile()      .mmap()            │    │                 ║  │
│  ║  └──────────────────────┬───────────────────┘    │                 ║  │
│  ║                         │                        │                 ║  │
│  ║           ┌─────────────┴─────────────┐          │                 ║  │
│  ║           │                           │          │                 ║  │
│  ║           ▼                           ▼          │                 ║  │
│  ║  ┌─────────────────┐        ┌─────────────────┐  │                 ║  │
│  ║  │  PAGE CACHE     │        │  PIPE BUFFERS   │  │                 ║  │
│  ║  │                 │        │                 │  │                 ║  │
│  ║  │  ┌───┬───┬───┐  │        │ ┌─────────────┐ │  │                 ║  │
│  ║  │  │pg │pg │pg │  │◄───────┤ │pipe_buffer[]│ │  │                 ║  │
│  ║  │  │ 0 │ 1 │ 2 │  │ ref    │ │  .page      │ │  │                 ║  │
│  ║  │  └───┴───┴───┘  │ only   │ │  .offset    │ │  │                 ║  │
│  ║  │      │          │        │ │  .len       │ │  │                 ║  │
│  ║  │      │          │        │ └─────────────┘ │  │                 ║  │
│  ║  │      ▼          │        └────────┬────────┘  │                 ║  │
│  ║  │  struct page    │                 │           │                 ║  │
│  ║  │   .refcount     │                 │           │                 ║  │
│  ║  │   .flags        │                 │           │                 ║  │
│  ║  └────────┬────────┘                 │           │                 ║  │
│  ║           │                          │           │                 ║  │
│  ║           └──────────┬───────────────┘           │                 ║  │
│  ║                      │                           │                 ║  │
│  ║                      ▼                           │                 ║  │
│  ║           ┌─────────────────────────┐            │                 ║  │
│  ║           │     NETWORK STACK       │            │                 ║  │
│  ║           │                         │            │                 ║  │
│  ║           │  sk_buff:               │            │                 ║  │
│  ║           │   ├─ linear data        │            │                 ║  │
│  ║           │   └─ skb_shared_info:   │◄───────────┘                 ║  │
│  ║           │        └─ frags[]:      │   (AF_XDP                    ║  │
│  ║           │             .page ──────┼── bypasses                   ║  │
│  ║           │             .offset     │   this!)                     ║  │
│  ║           │             .size       │                              ║  │
│  ║           └────────────┬────────────┘                              ║  │
│  ║                        │                                           ║  │
│  ║                        ▼                                           ║  │
│  ║           ┌─────────────────────────┐                              ║  │
│  ║           │     TCP/IP STACK        │                              ║  │
│  ║           │                         │                              ║  │
│  ║           │   • Checksum offload    │                              ║  │
│  ║           │   • TSO/GSO             │                              ║  │
│  ║           │   • Header generation   │                              ║  │
│  ║           └────────────┬────────────┘                              ║  │
│  ║                        │                                           ║  │
│  ═════════════════════════╪═══════════════════════════════════════════  │
│                           │                                              │
│  ┌────────────────────────▼────────────────────────────────────────────┐ │
│  │                        NIC DRIVER                                   │ │
│  │                                                                     │ │
│  │   DMA Descriptors:                                                  │ │
│  │   ┌────────────────────────────────────────────────────────────┐   │ │
│  │   │ desc[0]: addr=0x1000, len=1500  ─┐                         │   │ │
│  │   │ desc[1]: addr=0x2000, len=1500  ─┼── Scatter-Gather DMA    │   │ │
│  │   │ desc[2]: addr=0x3000, len=500   ─┘   (pages stay in place) │   │ │
│  │   └────────────────────────────────────────────────────────────┘   │ │
│  │                                                                     │ │
│  └─────────────────────────────────┬───────────────────────────────────┘ │
│                                    │                                     │
│  ══════════════════════════════════╪═════════════════════════════════    │
│                                    │                                     │
│  ┌─────────────────────────────────▼───────────────────────────────────┐ │
│  │                           HARDWARE                                   │ │
│  │                                                                      │ │
│  │   ┌────────────┐    ┌────────────┐    ┌────────────────────────┐   │ │
│  │   │   DISK     │    │   MEMORY   │    │     NETWORK CARD       │   │ │
│  │   │            │    │            │    │                        │   │ │
│  │   │  Storage   │    │  DRAM      │    │  TX Ring    DMA        │   │ │
│  │   │  Media     │◄──►│  (Physical │◄──►│  Buffers    Engine     │   │ │
│  │   │            │DMA │   Pages)   │DMA │            ────►Wire   │   │ │
│  │   └────────────┘    └────────────┘    └────────────────────────┘   │ │
│  │                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY INSIGHT:                                                            │
│   ────────────                                                             │
│   In zero-copy, the SAME physical memory pages flow through the entire   │
│   stack. No CPU cycles wasted copying data - only metadata (pointers,    │
│   lengths, refcounts) is manipulated.                                    │
│                                                                            │
│   The kernel moves "struct page" references, not actual bytes!           │
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
│   1. "The Design of the UNIX Operating System"                            │
│      Maurice J. Bach, 1986                                                │
│      - Foundational understanding of buffer cache and I/O subsystem       │
│      - Chapter 3: Buffer Cache                                            │
│      - Chapter 5: System Calls for the File System                        │
│                                                                            │
│   2. "UNIX Network Programming, Volume 1" (3rd Edition)                   │
│      W. Richard Stevens, Bill Fenner, Andrew M. Rudoff, 2003              │
│      - Socket programming fundamentals                                    │
│      - Advanced I/O techniques                                            │
│                                                                            │
│   3. "Linux Kernel Development" (3rd Edition)                             │
│      Robert Love, 2010                                                    │
│      - Chapter 16: Page Cache and Page Writeback                          │
│      - Chapter 17: Devices and Modules                                    │
│                                                                            │
│   4. "The Linux Programming Interface"                                    │
│      Michael Kerrisk, 2010                                                │
│      - Chapter 49: Memory Mappings                                        │
│      - Chapter 59: Sockets (sendfile, splice)                             │
│                                                                            │
│   5. "Understanding the Linux Kernel" (3rd Edition)                       │
│      Daniel P. Bovet, Marco Cesati, 2005                                  │
│      - Chapter 15: Page Cache                                             │
│      - Chapter 16: Block Device Drivers                                   │
│                                                                            │
│   6. "Linux Device Drivers" (3rd Edition)                                 │
│      Jonathan Corbet, Alessandro Rubini, Greg Kroah-Hartman, 2005         │
│      - DMA operations                                                     │
│      - Memory mapping                                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Kernel Source Code

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LINUX KERNEL SOURCE FILES                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SENDFILE / SPLICE:                                                      │
│   ──────────────────                                                       │
│   fs/splice.c                  - splice(), tee(), vmsplice()              │
│   fs/read_write.c              - sendfile() entry point                   │
│   include/linux/splice.h       - splice data structures                   │
│   include/linux/pipe_fs_i.h    - pipe_buffer, pipe_inode_info             │
│                                                                            │
│   MEMORY MAPPING:                                                         │
│   ───────────────                                                          │
│   mm/mmap.c                    - mmap() implementation                    │
│   mm/memory.c                  - page fault handling                      │
│   mm/filemap.c                 - file-backed page operations              │
│   include/linux/mm.h           - memory management structures             │
│                                                                            │
│   PAGE CACHE:                                                             │
│   ───────────                                                              │
│   mm/filemap.c                 - page cache core                          │
│   include/linux/pagemap.h      - page cache API                           │
│   include/linux/fs.h           - address_space definition                 │
│                                                                            │
│   NETWORK STACK:                                                          │
│   ──────────────                                                           │
│   net/core/skbuff.c            - sk_buff operations                       │
│   net/socket.c                 - socket system calls                      │
│   net/ipv4/tcp.c               - TCP implementation                       │
│   include/linux/skbuff.h       - sk_buff, skb_shared_info                 │
│                                                                            │
│   DMA:                                                                    │
│   ────                                                                     │
│   kernel/dma/                  - DMA core subsystem                       │
│   include/linux/dma-mapping.h  - DMA API                                  │
│   drivers/iommu/               - IOMMU drivers                            │
│                                                                            │
│   AF_XDP:                                                                 │
│   ───────                                                                  │
│   net/xdp/                     - XDP core                                 │
│   net/xdp/xsk.c                - XDP socket implementation                │
│   include/net/xdp.h            - XDP structures                           │
│   include/uapi/linux/if_xdp.h  - User-space XDP API                       │
│                                                                            │
│   BLOCK I/O:                                                              │
│   ──────────                                                               │
│   block/bio.c                  - bio operations                           │
│   include/linux/bio.h          - bio, bio_vec structures                  │
│   include/linux/blkdev.h       - block device API                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Online Resources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ONLINE RESOURCES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DOCUMENTATION:                                                          │
│   ──────────────                                                           │
│   • Linux Kernel Documentation                                            │
│     https://www.kernel.org/doc/html/latest/                               │
│                                                                            │
│   • LWN.net Articles:                                                     │
│     - "Zero-copy networking" (2019)                                       │
│     - "The tale of one latency metric" (io_uring, 2019)                   │
│     - "splice() and sendfile() implementation" (2006)                     │
│                                                                            │
│   • man pages:                                                            │
│     sendfile(2), splice(2), tee(2), vmsplice(2)                           │
│     mmap(2), madvise(2), posix_fadvise(2)                                 │
│                                                                            │
│   PAPERS:                                                                 │
│   ───────                                                                  │
│   • "Efficient Data Copy-Free Network I/O"                                │
│     Proceedings of SIGCOMM, 1993                                          │
│                                                                            │
│   • "The Design and Implementation of the XDP Socket API"                 │
│     Proceedings of SIGCOMM, 2018                                          │
│                                                                            │
│   • "io_uring: Efficient Asynchronous I/O for the Linux Kernel"           │
│     Linux Plumbers Conference, 2019                                       │
│                                                                            │
│   BENCHMARKS AND CASE STUDIES:                                            │
│   ────────────────────────────                                             │
│   • nginx sendfile documentation                                          │
│   • Apache Kafka design documentation                                     │
│   • HAProxy architecture documentation                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Related RFCs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RELEVANT RFCs                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   While zero-copy is an implementation technique, these RFCs define       │
│   the protocols where zero-copy is most beneficial:                       │
│                                                                            │
│   TCP/IP:                                                                 │
│   ───────                                                                  │
│   RFC 793   - Transmission Control Protocol                               │
│   RFC 1323  - TCP Extensions for High Performance                         │
│   RFC 5681  - TCP Congestion Control                                      │
│   RFC 7323  - TCP Extensions for High Performance (updated)               │
│                                                                            │
│   HTTP:                                                                   │
│   ─────                                                                    │
│   RFC 7230  - HTTP/1.1 Message Syntax and Routing                         │
│   RFC 7540  - HTTP/2                                                      │
│   RFC 9114  - HTTP/3                                                      │
│                                                                            │
│   NFS (Server-Side Copy):                                                 │
│   ───────────────────────                                                  │
│   RFC 7862  - NFSv4.2 (includes server-side copy operations)              │
│                                                                            │
│   iSCSI:                                                                  │
│   ──────                                                                   │
│   RFC 7143  - iSCSI Protocol                                              │
│                                                                            │
│   RDMA:                                                                   │
│   ─────                                                                    │
│   RFC 5040  - Remote Direct Memory Access Protocol                        │
│   RFC 5041  - Direct Data Placement over Reliable Transports              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

*This document is part of a series on Unix/Linux kernel internals, following
the style of Maurice Bach's "The Design of the UNIX Operating System".*

*Related documents in this series:*
- *unix-pipes-and-ipc.md - Pipes and Inter-Process Communication*
- *blocking-nonblocking-io.md - Blocking and Non-Blocking I/O*
- *unix-sockets.md - Unix Socket Programming and Internals*
- *nginx-architecture.md - Nginx Architecture and Internals*
