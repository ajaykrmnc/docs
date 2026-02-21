# Nginx Architecture and Internals

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Event-Driven Architecture, Master-Worker Model, Request Processing, and Performance Optimization

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The C10K Problem and Nginx's Solution](#the-c10k-problem-and-nginxs-solution)
   - [Why Nginx Was Created](#why-nginx-was-created)
   - [Historical Context](#historical-context)
   - [Document Organization](#document-organization)

2. [Fundamental Architecture](#2-fundamental-architecture)
   - [The Master-Worker Model](#the-master-worker-model)
   - [Process Roles and Responsibilities](#process-roles-and-responsibilities)
   - [Memory Architecture](#memory-architecture)
   - [Configuration Reload Without Downtime](#configuration-reload-without-downtime)

3. [Event-Driven Model](#3-event-driven-model)
   - [Why Not Thread-Per-Connection?](#why-not-thread-per-connection)
   - [The Event Loop](#the-event-loop)
   - [Connection State Machine](#connection-state-machine)
   - [Platform-Specific Event Mechanisms](#platform-specific-event-mechanisms)

4. [Connection Handling](#4-connection-handling)
   - [Accept Queue and Listen Socket](#accept-queue-and-listen-socket)
   - [Connection Pooling](#connection-pooling)
   - [Keep-Alive Connections](#keep-alive-connections)
   - [Connection Limits and Backpressure](#connection-limits-and-backpressure)

5. [Request Processing Pipeline](#5-request-processing-pipeline)
   - [HTTP Request Parsing](#http-request-parsing)
   - [The Phases of Request Processing](#the-phases-of-request-processing)
   - [Location Matching](#location-matching)
   - [Content Handlers](#content-handlers)
   - [Filter Chain](#filter-chain)

6. [Upstream and Proxy](#6-upstream-and-proxy)
   - [Reverse Proxy Architecture](#reverse-proxy-architecture)
   - [Load Balancing Algorithms](#load-balancing-algorithms)
   - [Upstream Connection Pooling](#upstream-connection-pooling)
   - [Health Checks](#health-checks)
   - [Buffering and Streaming](#buffering-and-streaming)

7. [Memory Management](#7-memory-management)
   - [Pool Allocator](#pool-allocator)
   - [Shared Memory Zones](#shared-memory-zones)
   - [Buffer Chains](#buffer-chains)
   - [Slab Allocator](#slab-allocator)

8. [Caching](#8-caching)
   - [Proxy Cache Architecture](#proxy-cache-architecture)
   - [Cache Keys and Zones](#cache-keys-and-zones)
   - [Cache Manager and Loader](#cache-manager-and-loader)
   - [Cache Locking and Thundering Herd](#cache-locking-and-thundering-herd)

9. [SSL/TLS Handling](#9-ssltls-handling)
   - [SSL Termination](#ssl-termination)
   - [Session Resumption](#session-resumption)
   - [OCSP Stapling](#ocsp-stapling)
   - [HTTP/2 and ALPN](#http2-and-alpn)

10. [Performance Optimization](#10-performance-optimization)
    - [sendfile() and Zero-Copy](#sendfile-and-zero-copy)
    - [TCP_CORK and TCP_NODELAY](#tcp_cork-and-tcp_nodelay)
    - [Worker Tuning](#worker-tuning)
    - [Buffer Tuning](#buffer-tuning)

11. [Practical Configuration](#11-practical-configuration)
    - [Common Patterns](#common-patterns)
    - [Performance Tuning Checklist](#performance-tuning-checklist)
    - [Debugging and Troubleshooting](#debugging-and-troubleshooting)

12. [Summary and Appendix](#12-summary-and-appendix)
    - [Architecture Quick Reference](#architecture-quick-reference)
    - [Directive Quick Reference](#directive-quick-reference)
    - [The Big Picture](#the-big-picture)

13. [References](#13-references)

---

## 1. Introduction

### The C10K Problem and Nginx's Solution

In the early 2000s, the internet faced a fundamental scaling challenge: **How do you handle 10,000 concurrent
connections on a single server?**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE C10K PROBLEM                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Traditional Web Server (Apache prefork):                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Client 1  ────────────────────────────────>  Process 1            │ │
│   │   Client 2  ────────────────────────────────>  Process 2            │ │
│   │   Client 3  ────────────────────────────────>  Process 3            │ │
│   │      ...                                          ...               │ │
│   │   Client 10000 ─────────────────────────────>  Process 10000        │ │
│   │                                                                     │ │
│   │   PROBLEM:                                                          │ │
│   │   • Each process: ~2-10 MB memory                                   │ │
│   │   • 10,000 processes = 20-100 GB RAM!                               │ │
│   │   • Context switching overhead: catastrophic                        │ │
│   │   • Most processes are IDLE (waiting for I/O)                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Nginx Solution:                                                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Client 1  ──┐                                                     │ │
│   │   Client 2  ──┤                                                     │ │
│   │   Client 3  ──┼──────────────────────────────>  Worker 1            │ │
│   │      ...      │                                 (single process,    │ │
│   │   Client 2500 ┘                                  event loop)        │ │
│   │                                                                     │ │
│   │   Client 2501 ┐                                                     │ │
│   │      ...      ├─────────────────────────────>   Worker 2            │ │
│   │   Client 5000 ┘                                                     │ │
│   │                                                                     │ │
│   │   (... 4 workers handle 10,000+ connections)                        │ │
│   │                                                                     │ │
│   │   SOLUTION:                                                         │ │
│   │   • 4 workers × ~10 MB = 40 MB RAM                                  │ │
│   │   • Non-blocking I/O: never wait, always work                       │ │
│   │   • Event-driven: kernel notifies when fd is ready                  │ │
│   │   • Minimal context switching                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Why Nginx Was Created

Igor Sysoev, a system administrator at Rambler (a Russian internet company), faced a practical problem: their
Apache servers couldn't handle the growing traffic. The **process-per-connection model** was fundamentally
broken for modern web workloads.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE PROBLEM IGOR FACED                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   RAMBLER.RU (2002):                                                       │
│   • One of Russia's largest portals                                        │
│   • Millions of daily users                                                │
│   • Apache servers constantly overloaded                                   │
│                                                                            │
│   WHAT HAPPENS UNDER LOAD (Apache):                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Time ─────────────────────────────────────────────────────────>   │ │
│   │                                                                     │ │
│   │   Load increases:                                                   │ │
│   │   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                               │ │
│   │   │ 10 │→│100 │→│500 │→│1000│→│2000│ concurrent connections        │ │
│   │   └────┘ └────┘ └────┘ └────┘ └────┘                               │ │
│   │                                                                     │ │
│   │   Process count follows:                                            │ │
│   │   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                               │ │
│   │   │ 10 │→│100 │→│500 │→│1000│→│2000│ processes                     │ │
│   │   └────┘ └────┘ └────┘ └────┘ └────┘                               │ │
│   │                                                                     │ │
│   │   Memory usage:                                                     │ │
│   │   ┌────┐ ┌────┐ ┌─────┐ ┌─────┐ ┌─────┐                            │ │
│   │   │20MB│→│200M│→│ 1GB │→│ 2GB │→│ 4GB │ ... then SWAP → DEATH      │ │
│   │   └────┘ └────┘ └─────┘ └─────┘ └─────┘                            │ │
│   │                                                                     │ │
│   │   Context switch overhead:                                          │ │
│   │   ┌────┐ ┌────┐ ┌─────┐ ┌──────┐ ┌─────────┐                       │ │
│   │   │tiny│→│ OK │→│ bad │→│awful │→│ system  │                       │ │
│   │   │    │ │    │ │     │ │      │ │ unusable│                       │ │
│   │   └────┘ └────┘ └─────┘ └──────┘ └─────────┘                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE INSIGHT:                                                             │
│   "Most of these processes are doing NOTHING. They're waiting for:         │
│    • Network I/O (client is slow, packet in transit)                       │
│    • Disk I/O (reading file from disk)                                     │
│    • Upstream response (backend server processing)                         │
│                                                                            │
│    Why have 2000 processes waiting when 4 processes could handle           │
│    all the actual WORK?"                                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NGINX TIMELINE                                          │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   2002    Igor Sysoev begins development                                   │
│     │     • Working evenings/weekends while at Rambler                     │
│     │     • Goal: handle 10,000+ concurrent connections                    │
│     │                                                                      │
│     ▼                                                                      │
│   2004    First public release (0.1.0)                                     │
│     │     • Open source (BSD license)                                      │
│     │     • Basic HTTP server and reverse proxy                            │
│     │                                                                      │
│     ▼                                                                      │
│   2008    Nginx surpasses 1% market share                                  │
│     │     • Major sites adopting: WordPress.com, Hulu                      │
│     │                                                                      │
│     ▼                                                                      │
│   2011    Nginx Inc. founded                                               │
│     │     • Commercial support and Nginx Plus                              │
│     │                                                                      │
│     ▼                                                                      │
│   2019    F5 Networks acquires Nginx Inc.                                  │
│     │     • $670 million acquisition                                       │
│     │                                                                      │
│     ▼                                                                      │
│   2024    Nginx powers ~34% of all web servers                             │
│           • #1 or #2 depending on measurement method                       │
│           • Powers: Netflix, Airbnb, Dropbox, GitHub, NASA...              │
│                                                                            │
├───────────────────────────────────────────────────────────────────────────┤
│   KEY DESIGN DECISIONS:                                                    │
│                                                                            │
│   1. Event-driven, asynchronous architecture                               │
│   2. Master-worker process model (not threads)                             │
│   3. Modular design with phases and filters                                │
│   4. Minimal memory footprint per connection                               │
│   5. Zero-copy where possible                                              │
│   6. Configuration without downtime reload                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Document Organization

This document explores nginx internals in depth:

| Section              | Focus                                              |
| -------------------- | -------------------------------------------------- |
| **Architecture**     | Master-worker model, process roles, memory layout  |
| **Event Model**      | Event loop, connection state machine, epoll/kqueue |
| **Connections**      | Accept queue, keep-alive, connection limits        |
| **Request Pipeline** | Phases, location matching, handlers, filters       |
| **Upstream**         | Reverse proxy, load balancing, connection pooling  |
| **Memory**           | Pool allocator, shared zones, buffer chains        |
| **Caching**          | Proxy cache, cache zones, cache manager            |
| **SSL/TLS**          | Termination, session resumption, HTTP/2            |
| **Performance**      | sendfile, TCP tuning, worker optimization          |

---

## 2. Fundamental Architecture

### The Master-Worker Model

Nginx uses a **multi-process architecture** with distinct roles:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NGINX PROCESS ARCHITECTURE                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                          ┌─────────────────────┐                           │
│                          │    MASTER PROCESS   │                           │
│                          │      (PID 1234)     │                           │
│                          │                     │                           │
│                          │  • Reads config     │                           │
│                          │  • Binds ports      │                           │
│                          │  • Spawns workers   │                           │
│                          │  • Handles signals  │                           │
│                          │  • Never handles    │                           │
│                          │    client requests  │                           │
│                          └──────────┬──────────┘                           │
│                                     │                                      │
│              ┌──────────────────────┼──────────────────────┐               │
│              │                      │                      │               │
│              ▼                      ▼                      ▼               │
│   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐      │
│   │  WORKER PROCESS  │   │  WORKER PROCESS  │   │  WORKER PROCESS  │      │
│   │    (PID 1235)    │   │    (PID 1236)    │   │    (PID 1237)    │      │
│   │                  │   │                  │   │                  │      │
│   │  • Event loop    │   │  • Event loop    │   │  • Event loop    │      │
│   │  • Handle conns  │   │  • Handle conns  │   │  • Handle conns  │      │
│   │  • Process reqs  │   │  • Process reqs  │   │  • Process reqs  │      │
│   │  • Send response │   │  • Send response │   │  • Send response │      │
│   │                  │   │                  │   │                  │      │
│   │  Connections:    │   │  Connections:    │   │  Connections:    │      │
│   │  ~3000           │   │  ~3000           │   │  ~3000           │      │
│   └──────────────────┘   └──────────────────┘   └──────────────────┘      │
│                                                                            │
│   Optional helper processes:                                               │
│   ┌──────────────────┐   ┌──────────────────┐                              │
│   │  CACHE MANAGER   │   │  CACHE LOADER    │                              │
│   │    (PID 1238)    │   │    (PID 1239)    │                              │
│   │                  │   │                  │                              │
│   │  • Prunes cache  │   │  • Loads cache   │                              │
│   │  • Enforces size │   │    metadata on   │                              │
│   │    limits        │   │    startup       │                              │
│   └──────────────────┘   └──────────────────┘                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Process Roles and Responsibilities

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESS RESPONSIBILITIES                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ╔══════════════════════════════════════════════════════════════════╗    │
│   ║  MASTER PROCESS                                                   ║    │
│   ╠══════════════════════════════════════════════════════════════════╣    │
│   ║                                                                   ║    │
│   ║  Startup:                                                         ║    │
│   ║  1. Read and validate configuration file                          ║    │
│   ║  2. Create listening sockets (bind to ports 80, 443, etc.)        ║    │
│   ║  3. Fork worker processes                                         ║    │
│   ║  4. Fork cache manager/loader if configured                       ║    │
│   ║                                                                   ║    │
│   ║  Runtime:                                                         ║    │
│   ║  • Monitor worker health (SIGCHLD handling)                       ║    │
│   ║  • Respawn crashed workers                                        ║    │
│   ║  • Handle signals from administrator:                             ║    │
│   ║    - SIGHUP:  Reload configuration                                ║    │
│   ║    - SIGUSR1: Reopen log files                                    ║    │
│   ║    - SIGUSR2: Upgrade binary                                      ║    │
│   ║    - SIGTERM: Graceful shutdown                                   ║    │
│   ║    - SIGQUIT: Immediate shutdown                                  ║    │
│   ║                                                                   ║    │
│   ║  NEVER:                                                           ║    │
│   ║  • Handle client connections                                      ║    │
│   ║  • Process HTTP requests                                          ║    │
│   ║  • Runs as root (to bind ports <1024), then workers drop privs    ║    │
│   ║                                                                   ║    │
│   ╚══════════════════════════════════════════════════════════════════╝    │
│                                                                            │
│   ╔══════════════════════════════════════════════════════════════════╗    │
│   ║  WORKER PROCESS                                                   ║    │
│   ╠══════════════════════════════════════════════════════════════════╣    │
│   ║                                                                   ║    │
│   ║  Core responsibilities:                                           ║    │
│   ║  1. Accept new connections (from inherited listen socket)         ║    │
│   ║  2. Run event loop (epoll_wait/kqueue)                           ║    │
│   ║  3. Process HTTP requests through phases                          ║    │
│   ║  4. Send responses to clients                                     ║    │
│   ║  5. Proxy requests to upstreams                                   ║    │
│   ║  6. Serve static files                                            ║    │
│   ║  7. Handle SSL/TLS                                                ║    │
│   ║                                                                   ║    │
│   ║  Key characteristics:                                             ║    │
│   ║  • Single-threaded (one event loop per worker)                    ║    │
│   ║  • Handles thousands of connections simultaneously                 ║    │
│   ║  • No locks needed (no shared mutable state between workers)      ║    │
│   ║  • Runs as unprivileged user (www-data, nginx)                    ║    │
│   ║                                                                   ║    │
│   ╚══════════════════════════════════════════════════════════════════╝    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Why Workers, Not Threads?**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROCESSES vs THREADS: THE NGINX CHOICE                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THREADS (what nginx DOESN'T use for request handling):                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Process                                                            │ │
│   │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │ │
│   │  │  Thread 1   │ │  Thread 2   │ │  Thread 3   │                   │ │
│   │  │             │ │             │ │             │                   │ │
│   │  │ Connection  │ │ Connection  │ │ Connection  │                   │ │
│   │  │    Pool     │ │    Pool     │ │    Pool     │                   │ │
│   │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                   │ │
│   │         │               │               │                           │ │
│   │         └───────────────┼───────────────┘                           │ │
│   │                         │                                           │ │
│   │                         ▼                                           │ │
│   │              ┌─────────────────────┐                                │ │
│   │              │   SHARED MEMORY     │  ← Requires LOCKS!             │ │
│   │              │   (config, cache,   │  ← Race conditions!            │ │
│   │              │    connection pool) │  ← Deadlock risk!              │ │
│   │              └─────────────────────┘                                │ │
│   │                                                                     │ │
│   │  PROBLEMS:                                                          │ │
│   │  • Need mutexes for shared data → contention                        │ │
│   │  • One thread crash = whole process dies                            │ │
│   │  • Complex debugging (race conditions)                              │ │
│   │  • Thread-safe libraries required                                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PROCESSES (what nginx DOES use):                                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │ │
│   │  │   Worker 1    │    │   Worker 2    │    │   Worker 3    │       │ │
│   │  │               │    │               │    │               │       │ │
│   │  │ Own memory    │    │ Own memory    │    │ Own memory    │       │ │
│   │  │ Own event loop│    │ Own event loop│    │ Own event loop│       │ │
│   │  │ Own conns     │    │ Own conns     │    │ Own conns     │       │ │
│   │  │               │    │               │    │               │       │ │
│   │  │ NO LOCKS!     │    │ NO LOCKS!     │    │ NO LOCKS!     │       │ │
│   │  └───────────────┘    └───────────────┘    └───────────────┘       │ │
│   │         │                    │                    │                 │ │
│   │         └────────────────────┼────────────────────┘                 │ │
│   │                              │                                      │ │
│   │                              ▼                                      │ │
│   │                   ┌─────────────────────┐                           │ │
│   │                   │   SHARED MEMORY     │ ← Read-mostly            │ │
│   │                   │   (cache zones,     │ ← Atomic operations      │ │
│   │                   │    limit counters)  │ ← Minimal contention     │ │
│   │                   └─────────────────────┘                           │ │
│   │                                                                     │ │
│   │  ADVANTAGES:                                                        │ │
│   │  • Each worker is independent - no locks for request processing    │ │
│   │  • One worker crash doesn't affect others                          │ │
│   │  • Simple, debuggable code                                         │ │
│   │  • CPU affinity: pin worker to core (no cache thrashing)          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Memory Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NGINX MEMORY LAYOUT                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                        PHYSICAL MEMORY                                     │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │  ┌────────────────────────────────────────────────────────────┐   │  │
│   │  │              SHARED MEMORY (mmap)                           │   │  │
│   │  │                                                             │   │  │
│   │  │  • Proxy cache zones (proxy_cache_path zone=...)            │   │  │
│   │  │  • Rate limit zones (limit_req_zone)                        │   │  │
│   │  │  • Connection limit zones (limit_conn_zone)                 │   │  │
│   │  │  • Upstream health check state                              │   │  │
│   │  │  • SSL session cache                                        │   │  │
│   │  │                                                             │   │  │
│   │  │  Accessed by: ALL WORKERS                                   │   │  │
│   │  │  Synchronization: Atomic ops, spinlocks                     │   │  │
│   │  │                                                             │   │  │
│   │  └────────────────────────────────────────────────────────────┘   │  │
│   │                                                                    │  │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│   │  │   Worker 1   │  │   Worker 2   │  │   Worker 3   │            │  │
│   │  │   Memory     │  │   Memory     │  │   Memory     │            │  │
│   │  │              │  │              │  │              │            │  │
│   │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │  │
│   │  │ │Connection│ │  │ │Connection│ │  │ │Connection│ │            │  │
│   │  │ │  Pool    │ │  │ │  Pool    │ │  │ │  Pool    │ │            │  │
│   │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │  │
│   │  │              │  │              │  │              │            │  │
│   │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │  │
│   │  │ │ Request  │ │  │ │ Request  │ │  │ │ Request  │ │            │  │
│   │  │ │  Pools   │ │  │ │  Pools   │ │  │ │  Pools   │ │            │  │
│   │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │  │
│   │  │              │  │              │  │              │            │  │
│   │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │            │  │
│   │  │ │ Buffers  │ │  │ │ Buffers  │ │  │ │ Buffers  │ │            │  │
│   │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │            │  │
│   │  │              │  │              │  │              │            │  │
│   │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│   │    PRIVATE          PRIVATE          PRIVATE                      │  │
│   │    (copy-on-write from fork, then diverges)                       │  │
│   │                                                                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   MEMORY USAGE BREAKDOWN (typical):                                        │
│                                                                            │
│   Component                    Per-Worker        Shared                    │
│   ─────────────────────────────────────────────────────────               │
│   Base process                 ~10 MB            -                         │
│   Connection structures        ~256 bytes/conn   -                         │
│   Request pools                ~4-16 KB/request  -                         │
│   Proxy buffers                ~32 KB/proxied    -                         │
│   Cache metadata               -                 Configurable              │
│   SSL session cache            -                 1 MB = ~4000 sessions     │
│                                                                            │
│   EXAMPLE: 10,000 connections across 4 workers:                            │
│   • Per worker: ~10 MB + (2500 × 256 bytes) ≈ 10.6 MB                     │
│   • Total workers: 4 × 10.6 MB ≈ 42 MB                                     │
│   • Shared: ~10 MB cache zone                                              │
│   • TOTAL: ~52 MB for 10,000 connections!                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Configuration Reload Without Downtime

One of nginx's most impressive features: **zero-downtime configuration reload**.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    GRACEFUL CONFIGURATION RELOAD                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   $ nginx -s reload    (or: kill -SIGHUP <master_pid>)                     │
│                                                                            │
│   STEP 1: Admin sends SIGHUP to master                                     │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │   Admin ─── SIGHUP ───> MASTER                                     │  │
│   │                           │                                        │  │
│   │                           ▼                                        │  │
│   │                    Parse new config                                │  │
│   │                    Validate syntax                                 │  │
│   │                    Check permissions                               │  │
│   │                           │                                        │  │
│   │                      ┌────┴────┐                                   │  │
│   │                      │ Valid?  │                                   │  │
│   │                      └────┬────┘                                   │  │
│   │                   No ◄────┴────► Yes                               │  │
│   │                   │              │                                 │  │
│   │                   ▼              ▼                                 │  │
│   │              Log error      Continue                               │  │
│   │              Keep running   with reload                            │  │
│   │              old config                                            │  │
│   │                                                                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   STEP 2: Spawn new workers with new config                                │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │   BEFORE:                         AFTER SPAWN:                     │  │
│   │                                                                    │  │
│   │   MASTER                          MASTER                           │  │
│   │      │                               │                             │  │
│   │      ├── Worker 1 (old)              ├── Worker 1 (old)            │  │
│   │      ├── Worker 2 (old)              ├── Worker 2 (old)            │  │
│   │      └── Worker 3 (old)              ├── Worker 3 (old)            │  │
│   │                                      ├── Worker 4 (NEW) ←          │  │
│   │                                      ├── Worker 5 (NEW) ←          │  │
│   │                                      └── Worker 6 (NEW) ←          │  │
│   │                                                                    │  │
│   │   New workers start accepting connections with NEW config          │  │
│   │   Old workers still handling existing connections                  │  │
│   │                                                                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   STEP 3: Graceful shutdown of old workers                                 │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │   MASTER ─── SIGQUIT ───> Old Workers                              │  │
│   │                                                                    │  │
│   │   Old workers:                                                     │  │
│   │   1. Stop accepting NEW connections                                │  │
│   │   2. Finish processing EXISTING requests                           │  │
│   │   3. Close keep-alive connections gracefully                       │  │
│   │   4. Exit when all requests complete                               │  │
│   │                                                                    │  │
│   │   Timeline:                                                        │  │
│   │                                                                    │  │
│   │   Time ──────────────────────────────────────────────────────>     │  │
│   │                                                                    │  │
│   │   │ SIGHUP │   New workers start   │  Old workers    │  Done      │  │
│   │   │ recv'd │   accepting traffic   │  drain out      │            │  │
│   │   │        │                       │                 │            │  │
│   │   ├────────┼───────────────────────┼─────────────────┤            │  │
│   │   │   0s   │       ~10ms           │   0-60 sec      │            │  │
│   │   │        │                       │   (depends on   │            │  │
│   │   │        │                       │    traffic)     │            │  │
│   │                                                                    │  │
│   │   NO DROPPED CONNECTIONS!                                          │  │
│   │   NO DOWNTIME!                                                     │  │
│   │                                                                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   FINAL STATE:                                                             │
│                                                                            │
│   MASTER                                                                   │
│      │                                                                     │
│      ├── Worker 4 (new config)                                             │
│      ├── Worker 5 (new config)                                             │
│      └── Worker 6 (new config)                                             │
│                                                                            │
│   Workers 1, 2, 3 have exited.                                             │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Binary Upgrade (SIGUSR2):**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BINARY UPGRADE PROCESS                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   $ kill -SIGUSR2 <master_pid>                                             │
│                                                                            │
│   This allows upgrading nginx itself without dropping connections!         │
│                                                                            │
│   1. Old master forks new master (running new binary)                      │
│   2. New master inherits listen sockets                                    │
│   3. New master spawns new workers                                         │
│   4. Admin sends SIGQUIT to old master                                     │
│   5. Old master + old workers gracefully exit                              │
│                                                                            │
│   BEFORE:                                                                  │
│   ┌──────────────────┐                                                     │
│   │  Old Master      │ ──── listen socket (fd 3) ───► port 80             │
│   │  (old binary)    │                                                     │
│   │       │          │                                                     │
│   │       ├── Old Worker 1                                                 │
│   │       └── Old Worker 2                                                 │
│   └──────────────────┘                                                     │
│                                                                            │
│   DURING (two masters running):                                            │
│   ┌──────────────────┐    ┌──────────────────┐                             │
│   │  Old Master      │    │  NEW Master      │                             │
│   │  (old binary)    │    │  (new binary)    │                             │
│   │       │          │    │       │          │                             │
│   │       ├── Old W1 │    │       ├── New W1 │                             │
│   │       └── Old W2 │    │       └── New W2 │                             │
│   └────────┬─────────┘    └────────┬─────────┘                             │
│            │                       │                                       │
│            └───────────┬───────────┘                                       │
│                        │                                                   │
│                        ▼                                                   │
│                 SHARED listen socket!                                      │
│                 (fd passed via SIGUSR2)                                    │
│                                                                            │
│   AFTER (old master quit):                                                 │
│   ┌──────────────────┐                                                     │
│   │  New Master      │ ──── listen socket ───► port 80                    │
│   │  (new binary)    │                                                     │
│   │       │          │                                                     │
│   │       ├── New Worker 1                                                 │
│   │       └── New Worker 2                                                 │
│   └──────────────────┘                                                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Event-Driven Model

### Why Not Thread-Per-Connection?

The traditional web server model creates one thread or process per connection. This seems intuitive but breaks
down at scale:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREAD-PER-CONNECTION vs EVENT-DRIVEN                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THREAD-PER-CONNECTION (Apache prefork/worker):                           │
│                                                                            │
│   Thread 1:                                                                │
│   ┌────────┬─────────────────────────────────────────────┬────────┐       │
│   │ accept │░░░░░░░░░ BLOCKED waiting for request ░░░░░░│ process│       │
│   └────────┴─────────────────────────────────────────────┴────────┘       │
│                                                                            │
│   Thread 2:                                                                │
│   ┌────────┬───────┬────────────────────────────────────┬─────────┐      │
│   │ accept │process│░░░░░ BLOCKED on disk I/O ░░░░░░░░░│ send    │      │
│   └────────┴───────┴────────────────────────────────────┴─────────┘      │
│                                                                            │
│   Thread 3:                                                                │
│   ┌────────┬───────┬─────────────────────────────────────┬────────┐      │
│   │ accept │process│░░░░░░ BLOCKED on backend ░░░░░░░░░░│ send   │      │
│   └────────┴───────┴─────────────────────────────────────┴────────┘      │
│                                                                            │
│   █ = doing work    ░ = blocked (thread exists but does nothing)          │
│                                                                            │
│   PROBLEMS:                                                                │
│   • Each thread consumes ~1-8 MB stack space                               │
│   • 10,000 connections = 10,000 threads = 10-80 GB RAM just for stacks!   │
│   • Context switching overhead: 1-10 μs per switch                        │
│   • With 10,000 threads, scheduler spends more time switching than working│
│   • Most threads are IDLE (waiting for I/O)                               │
│                                                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   EVENT-DRIVEN (Nginx):                                                    │
│                                                                            │
│   Single Worker Thread:                                                    │
│                                                                            │
│   Time ───────────────────────────────────────────────────────────────>   │
│                                                                            │
│   ┌──────┬────────┬──────┬────────┬──────┬────────┬──────┬────────┬───   │
│   │accept│ read   │accept│ read   │write │ read   │accept│ write  │...   │
│   │conn 1│ conn 1 │conn 2│ conn 2 │conn 1│ conn 3 │conn 4│ conn 2 │      │
│   └──────┴────────┴──────┴────────┴──────┴────────┴──────┴────────┴───   │
│    █████████████████████████████████████████████████████████████████      │
│                                                                            │
│   █ = doing work (100% utilization!)                                       │
│                                                                            │
│   HOW IT WORKS:                                                            │
│   1. Set ALL sockets to non-blocking                                       │
│   2. Register interest in events (read, write, accept)                     │
│   3. Call epoll_wait() - blocks until ANY socket is ready                 │
│   4. epoll returns: "conn 1 has data, conn 5 is writable"                 │
│   5. Process those connections (quick! non-blocking!)                      │
│   6. Go back to step 3                                                     │
│                                                                            │
│   ADVANTAGES:                                                              │
│   • One worker handles 10,000+ connections                                 │
│   • Memory: ~256 bytes per connection (not 1-8 MB!)                       │
│   • No context switching between connections (same thread)                 │
│   • 100% CPU utilization (no blocked threads)                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Event Loop

The heart of nginx is its event loop. Each worker runs this loop:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NGINX EVENT LOOP                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   void ngx_worker_process_cycle(void) {                                    │
│                                                                            │
│       for ( ;; ) {    /* Infinite loop */                                  │
│                                                                            │
│           /* 1. Process timers (keepalive, timeouts) */                    │
│           ngx_process_events_and_timers();                                 │
│                                                                            │
│           /* 2. Check for signals (reload, shutdown) */                    │
│           if (ngx_terminate || ngx_quit) {                                 │
│               /* Graceful shutdown */                                      │
│               ngx_worker_process_exit();                                   │
│           }                                                                │
│                                                                            │
│           if (ngx_reopen) {                                                │
│               /* Reopen log files */                                       │
│               ngx_reopen_files();                                          │
│           }                                                                │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   INSIDE ngx_process_events_and_timers():                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  1. Calculate timeout for epoll_wait                                │ │
│   │     (time until next timer expires)                                 │ │
│   │                                                                     │ │
│   │  2. Call epoll_wait(timeout)                                        │ │
│   │     ┌────────────────────────────────────────────────────────────┐  │ │
│   │     │                                                            │  │ │
│   │     │  WORKER SLEEPS HERE                                        │  │ │
│   │     │                                                            │  │ │
│   │     │  Kernel wakes us when:                                     │  │ │
│   │     │  • A socket has data to read                               │  │ │
│   │     │  • A socket is writable                                    │  │ │
│   │     │  • A new connection is pending                             │  │ │
│   │     │  • Timeout expires                                         │  │ │
│   │     │                                                            │  │ │
│   │     └────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │  3. Process ready events                                            │ │
│   │     for each event returned by epoll:                               │ │
│   │         if (event.fd == listen_socket)                              │ │
│   │             accept_new_connection();                                │ │
│   │         else if (event.events & EPOLLIN)                            │ │
│   │             read_from_client();                                     │ │
│   │         else if (event.events & EPOLLOUT)                           │ │
│   │             write_to_client();                                      │ │
│   │                                                                     │ │
│   │  4. Process expired timers                                          │ │
│   │     for each expired timer:                                         │ │
│   │         call timer->handler()                                       │ │
│   │         (e.g., close idle connection)                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Event Loop Visualization:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVENT LOOP VISUALIZATION                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                          ┌─────────────────┐                               │
│              ┌──────────►│  epoll_wait()   │◄─────────┐                   │
│              │           │  (block here)   │          │                   │
│              │           └────────┬────────┘          │                   │
│              │                    │                   │                   │
│              │                    ▼                   │                   │
│              │           ┌─────────────────┐          │                   │
│              │           │ Events returned │          │                   │
│              │           │  fd 5: READ     │          │                   │
│              │           │  fd 8: WRITE    │          │                   │
│              │           │  fd 3: ACCEPT   │          │                   │
│              │           └────────┬────────┘          │                   │
│              │                    │                   │                   │
│              │                    ▼                   │                   │
│              │    ┌───────────────┴───────────────┐   │                   │
│              │    │     Process each event        │   │                   │
│              │    └───────────────┬───────────────┘   │                   │
│              │                    │                   │                   │
│              │    ┌───────────────┼───────────────┐   │                   │
│              │    │               │               │   │                   │
│              │    ▼               ▼               ▼   │                   │
│              │ ┌──────┐      ┌─────────┐     ┌──────┐ │                   │
│              │ │ACCEPT│      │  READ   │     │WRITE │ │                   │
│              │ │new   │      │ request │     │respon│ │                   │
│              │ │conn  │      │ data    │     │se    │ │                   │
│              │ └───┬──┘      └────┬────┘     └───┬──┘ │                   │
│              │     │              │              │    │                   │
│              │     └──────────────┴──────────────┘    │                   │
│              │                    │                   │                   │
│              │                    ▼                   │                   │
│              │           ┌─────────────────┐          │                   │
│              │           │ Process timers  │          │                   │
│              │           │ (cleanup idle   │          │                   │
│              │           │  connections)   │          │                   │
│              │           └────────┬────────┘          │                   │
│              │                    │                   │                   │
│              └────────────────────┴───────────────────┘                   │
│                                                                            │
│   KEY INSIGHT:                                                             │
│   The worker NEVER blocks on individual connections.                       │
│   It only blocks in epoll_wait(), waiting for ANY socket to be ready.     │
│   When epoll returns, SOMETHING is ready - so we do work immediately.     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Connection State Machine

Nginx tracks each connection through a state machine:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION STATE MACHINE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │            ┌──────────┐                                            │ │
│   │            │   NEW    │                                            │ │
│   │            │(accepted)│                                            │ │
│   │            └────┬─────┘                                            │ │
│   │                 │                                                   │ │
│   │                 ▼                                                   │ │
│   │        ┌────────────────┐                                          │ │
│   │        │ READING_HEADERS│◄─────────────────────┐                   │ │
│   │        │                │                      │                   │ │
│   │        │ Waiting for    │                      │                   │ │
│   │        │ complete HTTP  │                      │                   │ │
│   │        │ request headers│                      │                   │ │
│   │        └───────┬────────┘                      │                   │ │
│   │                │ Headers complete              │                   │ │
│   │                ▼                               │                   │ │
│   │        ┌────────────────┐                      │                   │ │
│   │        │ READING_BODY   │                      │                   │ │
│   │        │ (if POST/PUT)  │                      │                   │ │
│   │        └───────┬────────┘                      │                   │ │
│   │                │                               │                   │ │
│   │                ▼                               │ Keep-alive:       │ │
│   │        ┌────────────────┐                      │ reuse connection  │ │
│   │        │  PROCESSING    │                      │                   │ │
│   │        │                │                      │                   │ │
│   │        │ • Location     │                      │                   │ │
│   │        │   matching     │                      │                   │ │
│   │        │ • Run phases   │                      │                   │ │
│   │        │ • Call handler │                      │                   │ │
│   │        └───────┬────────┘                      │                   │ │
│   │                │                               │                   │ │
│   │                ▼                               │                   │ │
│   │        ┌────────────────┐                      │                   │ │
│   │        │WRITING_RESPONSE│                      │                   │ │
│   │        │                │                      │                   │ │
│   │        │ Send headers   │                      │                   │ │
│   │        │ Send body      │                      │                   │ │
│   │        │ (may be chunked│                      │                   │ │
│   │        │  or streaming) │                      │                   │ │
│   │        └───────┬────────┘                      │                   │ │
│   │                │                               │                   │ │
│   │                ▼                               │                   │ │
│   │        ┌────────────────┐       ┌─────────┐   │                   │ │
│   │        │   LINGERING    │       │KEEPALIVE│───┘                   │ │
│   │        │   (optional)   │       │ (idle)  │                       │ │
│   │        └───────┬────────┘       └────┬────┘                       │ │
│   │                │                     │ Timeout                    │ │
│   │                │                     │ or close                   │ │
│   │                ▼                     ▼                            │ │
│   │            ┌──────────┐                                            │ │
│   │            │  CLOSED  │                                            │ │
│   │            └──────────┘                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY INSIGHT:                                                             │
│   State transitions happen based on EVENTS, not blocking calls.           │
│   If we can't complete a state (e.g., not enough data), we save state    │
│   and return to epoll_wait. When more data arrives, we resume.           │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Connection Structure (simplified):**

```c
struct ngx_connection_s {
  ngx_socket_t        fd;           /* Socket file descriptor */

  ngx_event_t        *read;         /* Read event */
  ngx_event_t        *write;        /* Write event */

  ngx_recv_pt         recv;         /* Receive function pointer */
  ngx_send_pt         send;         /* Send function pointer */

  ngx_pool_t         *pool;         /* Memory pool for this connection */

  struct sockaddr    *sockaddr;     /* Client address */
  socklen_t           socklen;

  ngx_buf_t          *buffer;       /* Receive buffer */

  void               *data;         /* Connection-specific data */
  /* (e.g., ngx_http_request_t) */

  unsigned            ssl:1;        /* Is SSL connection? */
  unsigned            sendfile:1;   /* Can use sendfile? */
  unsigned            tcp_nodelay:2;/* TCP_NODELAY state */
  unsigned            tcp_nopush:2; /* TCP_NOPUSH/CORK state */
};
```

### Platform-Specific Event Mechanisms

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PLATFORM-SPECIFIC EVENT MECHANISMS                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Nginx abstracts event handling. The core sees:                           │
│                                                                            │
│       ngx_add_event(ev, event, flags)                                      │
│       ngx_del_event(ev, event, flags)                                      │
│       ngx_process_events(timer, flags)                                     │
│                                                                            │
│   Underneath, platform-specific code implements these:                     │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   LINUX: epoll                                                      │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │   ngx_epoll_module.c                                                │ │
│   │                                                                     │ │
│   │   • O(1) add/remove events                                          │ │
│   │   • O(ready) - returns only ready fds                               │ │
│   │   • Supports EPOLLET (edge-triggered)                               │ │
│   │   • EPOLLONESHOT for thread safety                                  │ │
│   │   • Can watch >100,000 fds                                          │ │
│   │                                                                     │ │
│   │   Key calls:                                                        │ │
│   │   • epoll_create1()                                                 │ │
│   │   • epoll_ctl(EPOLL_CTL_ADD/MOD/DEL)                               │ │
│   │   • epoll_wait()                                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   BSD/macOS: kqueue                                                 │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │   ngx_kqueue_module.c                                               │ │
│   │                                                                     │ │
│   │   • Similar performance to epoll                                    │ │
│   │   • Can watch multiple event types (fd, signals, files, timers)     │ │
│   │   • EV_CLEAR for edge-triggered semantics                           │ │
│   │   • Batch event registration in kevent() call                       │ │
│   │                                                                     │ │
│   │   Key calls:                                                        │ │
│   │   • kqueue()                                                        │ │
│   │   • kevent() - add events AND retrieve events in one call           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   FALLBACK: select/poll                                             │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │   ngx_select_module.c, ngx_poll_module.c                           │ │
│   │                                                                     │ │
│   │   • Portable (works everywhere)                                     │ │
│   │   • O(n) per event loop iteration                                   │ │
│   │   • select: limited to FD_SETSIZE (1024 usually)                   │ │
│   │   • poll: no fd limit but still O(n)                               │ │
│   │                                                                     │ │
│   │   Used only when epoll/kqueue unavailable                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│                                                                            │
│   events {                                                                 │
│       use epoll;        # or kqueue, poll, select                         │
│       worker_connections 10000;                                            │
│       multi_accept on;  # Accept multiple connections per event           │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Connection Handling

### Accept Queue and Listen Socket

When a client connects to nginx, the connection goes through the kernel's TCP stack before nginx sees it:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION ACCEPTANCE FLOW                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CLIENT                     KERNEL                         NGINX          │
│                                                                            │
│   ┌──────────┐    SYN    ┌───────────────────────────────┐                │
│   │          │──────────►│                               │                │
│   │          │           │   SYN QUEUE (half-open)       │                │
│   │          │◄──────────│   ┌───┬───┬───┬───┬───┐      │                │
│   │  Client  │  SYN+ACK  │   │ C1│ C2│ C3│...│   │      │                │
│   │          │           │   └───┴───┴───┴───┴───┘      │                │
│   │          │──────────►│          │                    │                │
│   │          │    ACK    │          │ 3-way handshake    │                │
│   └──────────┘           │          │ complete           │                │
│                          │          ▼                    │                │
│                          │   ACCEPT QUEUE (completed)    │  ┌──────────┐ │
│                          │   ┌───┬───┬───┬───┬───┐      │  │          │ │
│                          │   │ C1│ C2│ C3│...│   │──────┼─►│  accept()│ │
│                          │   └───┴───┴───┴───┴───┘      │  │          │ │
│                          │                               │  │ Worker   │ │
│                          │      ▲                        │  │ Process  │ │
│                          │      │ somaxconn / backlog    │  │          │ │
│                          │                               │  └──────────┘ │
│                          └───────────────────────────────┘                │
│                                                                            │
│   KERNEL PARAMETERS:                                                       │
│   • net.core.somaxconn = 65535     (max accept queue size)                │
│   • net.ipv4.tcp_max_syn_backlog = 65535  (max SYN queue size)           │
│                                                                            │
│   NGINX CONFIG:                                                            │
│   listen 80 backlog=65535;    (sets SO_BACKLOG for this socket)          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**What happens when queues overflow?**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    QUEUE OVERFLOW SCENARIOS                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SCENARIO 1: SYN Queue Full                                              │
│   ───────────────────────────────────────────────────────────────────     │
│   New SYN arrives, but SYN queue is full:                                 │
│                                                                            │
│   Default behavior: DROP the SYN (client sees timeout)                    │
│                                                                            │
│   With SYN cookies enabled (tcp_syncookies = 1):                          │
│   • Kernel encodes connection state in SYN+ACK sequence number            │
│   • No state stored until ACK received                                    │
│   • Protects against SYN flood attacks                                    │
│                                                                            │
│   SCENARIO 2: Accept Queue Full                                           │
│   ───────────────────────────────────────────────────────────────────     │
│   Handshake completes, but accept queue is full:                          │
│                                                                            │
│   tcp_abort_on_overflow = 0 (default):                                    │
│   • Kernel ignores the final ACK                                          │
│   • Retransmits SYN+ACK (pretends handshake not complete)                 │
│   • Client sees delay, eventually connection succeeds                     │
│                                                                            │
│   tcp_abort_on_overflow = 1:                                              │
│   • Kernel sends RST to client                                            │
│   • Client immediately knows server is overloaded                         │
│   • Faster failure, but less graceful                                     │
│                                                                            │
│   MONITORING:                                                              │
│   $ ss -ltn sport = :80                                                   │
│   Recv-Q = current accept queue length                                    │
│   Send-Q = backlog (max accept queue size)                                │
│                                                                            │
│   $ netstat -s | grep -i listen                                           │
│   Shows overflows and drops                                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Accept Mutex and Thundering Herd

When multiple workers listen on the same socket, a new connection could wake ALL workers (thundering herd).
Nginx solves this:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ACCEPT MUTEX                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WITHOUT ACCEPT MUTEX (thundering herd):                                  │
│   ────────────────────────────────────────                                 │
│                                                                            │
│   New connection arrives                                                   │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Kernel wakes ALL workers blocked in epoll_wait()                   │ │
│   │                                                                     │ │
│   │  Worker 1: WAKE ──► epoll_wait returns ──► try accept() ──► FAIL   │ │
│   │  Worker 2: WAKE ──► epoll_wait returns ──► try accept() ──► FAIL   │ │
│   │  Worker 3: WAKE ──► epoll_wait returns ──► try accept() ──► SUCCESS│ │
│   │  Worker 4: WAKE ──► epoll_wait returns ──► try accept() ──► FAIL   │ │
│   │                                                                     │ │
│   │  Problem: 4 context switches, 4 system calls, only 1 wins          │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WITH ACCEPT MUTEX:                                                       │
│   ──────────────────                                                       │
│                                                                            │
│   Only ONE worker listens for new connections at a time:                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Worker 1: Has mutex ──► listening on port 80                      │ │
│   │  Worker 2: No mutex ──► only watching client connections           │ │
│   │  Worker 3: No mutex ──► only watching client connections           │ │
│   │  Worker 4: No mutex ──► only watching client connections           │ │
│   │                                                                     │ │
│   │  New connection arrives:                                            │ │
│   │  Worker 1: accept() ──► SUCCESS                                    │ │
│   │  Others: sleeping peacefully                                        │ │
│   │                                                                     │ │
│   │  After processing, Worker 1 releases mutex                          │ │
│   │  Worker 2 acquires mutex on next event loop iteration              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│   events {                                                                 │
│       accept_mutex on;           # Enable accept mutex (off by default)   │
│       accept_mutex_delay 500ms;  # Delay before trying to acquire mutex  │
│   }                                                                        │
│                                                                            │
│   MODERN LINUX (3.9+): REUSEPORT                                          │
│   ─────────────────────────────────                                        │
│   listen 80 reuseport;                                                    │
│                                                                            │
│   Kernel gives EACH worker its own accept queue:                          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  Worker 1: listen socket ──► accept queue 1                        │ │
│   │  Worker 2: listen socket ──► accept queue 2                        │ │
│   │  Worker 3: listen socket ──► accept queue 3                        │ │
│   │  Worker 4: listen socket ──► accept queue 4                        │ │
│   │                                                                     │ │
│   │  Kernel distributes incoming connections across queues              │ │
│   │  No thundering herd, no mutex needed!                               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Connection Pooling

Nginx pre-allocates connection structures to avoid malloc() during request handling:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION POOL                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   At startup, each worker allocates worker_connections connection slots:  │
│                                                                            │
│   worker_connections 10000;                                                │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   connections[] array:                                              │ │
│   │   ┌────┬────┬────┬────┬────┬────┬────┬────┬───────┬────┐           │ │
│   │   │ 0  │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ ..... │9999│           │ │
│   │   └────┴────┴────┴────┴────┴────┴────┴────┴───────┴────┘           │ │
│   │     │                                                               │ │
│   │     ▼                                                               │ │
│   │   ngx_connection_t structure (each ~256 bytes)                      │ │
│   │   ┌──────────────────────────────────────────────────────────────┐ │ │
│   │   │ fd          = -1  (not connected)                           │ │ │
│   │   │ read_event  = &events[0]                                    │ │ │
│   │   │ write_event = &events[10000]                                │ │ │
│   │   │ pool        = NULL                                          │ │ │
│   │   │ data        = NULL                                          │ │ │
│   │   │ next        ──────► (next free connection)                  │ │ │
│   │   └──────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   Free list:                                                        │ │
│   │   free_connections ──► [0] ──► [1] ──► [2] ──► ... ──► [9999]      │ │
│   │                                                                     │ │
│   │   When accept() succeeds:                                           │ │
│   │   1. Pop connection from free list                                  │ │
│   │   2. Initialize connection fields                                   │ │
│   │   3. Allocate memory pool for this connection                      │ │
│   │                                                                     │ │
│   │   When connection closes:                                           │ │
│   │   1. Free memory pool                                               │ │
│   │   2. Reset connection fields                                        │ │
│   │   3. Push connection back to free list                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MEMORY CALCULATION:                                                      │
│   • Each connection: ~256 bytes (ngx_connection_t)                        │
│   • Each event: ~96 bytes (ngx_event_t)                                   │
│   • 2 events per connection (read + write)                                │
│   • Total per connection: 256 + 96*2 = ~450 bytes                         │
│   • 10,000 connections: ~4.5 MB                                           │
│   • This is allocated ONCE at startup, not per-request!                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Keep-Alive Connections

HTTP keep-alive allows multiple requests on a single TCP connection:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KEEP-ALIVE CONNECTIONS                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WITHOUT KEEP-ALIVE:                                                      │
│   ───────────────────                                                      │
│                                                                            │
│   Request 1:  [TCP handshake] [Request] [Response] [TCP close]            │
│   Request 2:  [TCP handshake] [Request] [Response] [TCP close]            │
│   Request 3:  [TCP handshake] [Request] [Response] [TCP close]            │
│                                                                            │
│   Cost: 3 handshakes, 3 slow starts, 3 TIME_WAITs                         │
│                                                                            │
│   WITH KEEP-ALIVE:                                                         │
│   ────────────────                                                         │
│                                                                            │
│   [TCP handshake] [Req1][Resp1] [Req2][Resp2] [Req3][Resp3] [TCP close]   │
│                                                                            │
│   Cost: 1 handshake, 1 slow start, 1 TIME_WAIT                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Keep-Alive State Machine:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    KEEP-ALIVE STATE MACHINE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │            Connection established                                   │ │
│   │                     │                                               │ │
│   │                     ▼                                               │ │
│   │         ┌───────────────────────┐                                   │ │
│   │         │   READING_REQUEST     │◄──────────────────────────────┐   │ │
│   │         │                       │                               │   │ │
│   │         │ read_timeout active   │                               │   │ │
│   │         └───────────┬───────────┘                               │   │ │
│   │                     │ Request received                          │   │ │
│   │                     ▼                                           │   │ │
│   │         ┌───────────────────────┐                               │   │ │
│   │         │     PROCESSING        │                               │   │ │
│   │         │                       │                               │   │ │
│   │         │ (phases, handlers)    │                               │   │ │
│   │         └───────────┬───────────┘                               │   │ │
│   │                     │                                           │   │ │
│   │                     ▼                                           │   │ │
│   │         ┌───────────────────────┐                               │   │ │
│   │         │  WRITING_RESPONSE     │                               │   │ │
│   │         │                       │                               │   │ │
│   │         │ send_timeout active   │                               │   │ │
│   │         └───────────┬───────────┘                               │   │ │
│   │                     │                                           │   │ │
│   │                     ▼                                           │   │ │
│   │              Connection:         keepalive_requests              │   │ │
│   │              keep-alive? ───────────exceeded?──────────┐        │   │ │
│   │                     │                                  │        │   │ │
│   │                   Yes│                               Yes│        │   │ │
│   │                     │                                  │        │   │ │
│   │                     ▼                                  ▼        │   │ │
│   │         ┌───────────────────────┐          ┌──────────────┐    │   │ │
│   │         │      KEEPALIVE        │          │    CLOSE     │    │   │ │
│   │         │                       │          │              │    │   │ │
│   │         │ keepalive_timeout     │          │ shutdown()   │    │   │ │
│   │         │ timer running         │          │ close()      │    │   │ │
│   │         └───────────┬───────────┘          └──────────────┘    │   │ │
│   │                     │                                           │   │ │
│   │             New request│                                        │   │ │
│   │              arrives   │                                        │   │ │
│   │                     └──────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   Timeout expires:                                                  │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │ keepalive_timeout reached ──► Close connection gracefully    ││ │
│   │   └───────────────────────────────────────────────────────────────┘│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│   keepalive_timeout 65;      # Close idle connections after 65 seconds   │
│   keepalive_requests 1000;   # Max requests per connection               │
│   keepalive_time 1h;         # Max time to keep connection open          │
│                                                                            │
│   WHY LIMIT REQUESTS?                                                      │
│   • Memory: Each connection accumulates state over time                   │
│   • Load balancing: Distribute requests across upstream servers          │
│   • Graceful reload: Eventually all connections close                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Connection Limits and Backpressure

Nginx provides multiple mechanisms to limit connections:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONNECTION LIMITS                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   LIMIT 1: worker_connections                                             │
│   ────────────────────────────                                            │
│   Per-worker connection limit (structure pool size)                       │
│                                                                            │
│   worker_connections 10000;                                                │
│                                                                            │
│   If all slots used:                                                       │
│   • Worker cannot accept() new connections                                 │
│   • Connections queue in kernel accept queue                              │
│   • Eventually kernel rejects connections (RST)                           │
│                                                                            │
│   LIMIT 2: limit_conn                                                      │
│   ────────────────────                                                     │
│   Limit connections per key (IP, server, etc.)                            │
│                                                                            │
│   limit_conn_zone $binary_remote_addr zone=addr:10m;                      │
│   server {                                                                 │
│       limit_conn addr 100;   # Max 100 connections per IP                │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Shared memory zone "addr" (10MB):                                 │ │
│   │   ┌──────────────────┬──────────────────┬─────────────────────────┐ │ │
│   │   │ Key (binary IP)  │ Connection Count │ Slot status             │ │ │
│   │   ├──────────────────┼──────────────────┼─────────────────────────┤ │ │
│   │   │ 192.168.1.1      │        45        │ OK                      │ │ │
│   │   │ 192.168.1.2      │       100        │ LIMIT REACHED           │ │ │
│   │   │ 10.0.0.5         │         3        │ OK                      │ │ │
│   │   └──────────────────┴──────────────────┴─────────────────────────┘ │ │
│   │                                                                     │ │
│   │   New connection from 192.168.1.2:                                  │ │
│   │   • Check: count(192.168.1.2) >= 100? YES                          │ │
│   │   • Return 503 Service Unavailable                                  │ │
│   │   • Log: "limiting connections by zone \"addr\""                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   LIMIT 3: limit_req                                                       │
│   ────────────────────                                                     │
│   Rate limiting (requests per second)                                      │
│                                                                            │
│   limit_req_zone $binary_remote_addr zone=req:10m rate=10r/s;            │
│   server {                                                                 │
│       limit_req zone=req burst=20 nodelay;                               │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   Leaky bucket algorithm:                                           │ │
│   │                                                                     │ │
│   │   rate=10r/s means: 1 request allowed every 100ms                  │ │
│   │                                                                     │ │
│   │        ┌──────────────────────┐                                    │ │
│   │        │  Incoming requests   │                                    │ │
│   │        │   ▼ ▼ ▼ ▼ ▼ ▼ ▼ ▼   │                                    │ │
│   │        └─────────┬────────────┘                                    │ │
│   │                  │                                                  │ │
│   │                  ▼                                                  │ │
│   │        ┌──────────────────────┐  burst=20                          │ │
│   │        │ ████████████░░░░░░░░ │  (can hold 20 excess requests)    │ │
│   │        │ ████████████░░░░░░░░ │                                    │ │
│   │        └─────────┬────────────┘                                    │ │
│   │                  │ Leak rate: 10/sec                               │ │
│   │                  ▼                                                  │ │
│   │        ┌──────────────────────┐                                    │ │
│   │        │     Processing       │                                    │ │
│   │        └──────────────────────┘                                    │ │
│   │                                                                     │ │
│   │   Bucket full? Return 503                                          │ │
│   │   nodelay: Process burst immediately, don't queue                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Request Processing Pipeline

### HTTP Request Parsing

Nginx parses HTTP requests using a state machine:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HTTP REQUEST PARSING                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   HTTP Request Structure:                                                  │
│   ──────────────────────                                                   │
│   GET /index.html HTTP/1.1\r\n                 ◄── Request line           │
│   Host: example.com\r\n                        ◄── Headers                │
│   User-Agent: Mozilla/5.0\r\n                                             │
│   Accept: text/html\r\n                                                   │
│   \r\n                                         ◄── Empty line (end)       │
│   [optional body]                              ◄── Body (for POST/PUT)    │
│                                                                            │
│   PARSING STATE MACHINE:                                                   │
│   ──────────────────────                                                   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │  ┌───────────┐   G,H,P,D... ┌───────────┐  space  ┌───────────┐   │ │
│   │  │   START   │────────────►│  METHOD   │────────►│   URI     │   │ │
│   │  └───────────┘              └───────────┘         └─────┬─────┘   │ │
│   │                                                         │ space   │ │
│   │                                                         ▼         │ │
│   │                               \r         ┌───────────────────────┐│ │
│   │                              found       │  HTTP/1.x             ││ │
│   │                                ▲         │  (Protocol Version)   ││ │
│   │                                │         └───────────┬───────────┘│ │
│   │                                │                     │ \r\n       │ │
│   │                                │                     ▼            │ │
│   │  ┌───────────────────────────────────────────────────────────────┐│ │
│   │  │                                                               ││ │
│   │  │                   HEADER PARSING LOOP                         ││ │
│   │  │                                                               ││ │
│   │  │  For each header line:                                        ││ │
│   │  │  ┌─────────────┐  :   ┌─────────────┐ \r\n ┌───────────────┐ ││ │
│   │  │  │ Header Name │────►│Header Value │────►│ Next Header   │ ││ │
│   │  │  └─────────────┘      └─────────────┘     └───────┬───────┘ ││ │
│   │  │                                                   │          ││ │
│   │  │       \r\n\r\n (empty line) ◄─────────────────────┘          ││ │
│   │  │           │                                                   ││ │
│   │  │           ▼                                                   ││ │
│   │  │  ┌───────────────────────────────────────────────────────┐   ││ │
│   │  │  │  HEADERS COMPLETE - Ready for processing              │   ││ │
│   │  │  │  (or read body if Content-Length > 0)                 │   ││ │
│   │  │  └───────────────────────────────────────────────────────┘   ││ │
│   │  │                                                               ││ │
│   │  └───────────────────────────────────────────────────────────────┘│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KEY INSIGHT: STREAMING PARSER                                           │
│   The parser processes data AS IT ARRIVES. If we only receive half a     │
│   header, we save state and return to epoll_wait(). When more data       │
│   arrives, we resume from where we left off. NO BLOCKING!                │
│                                                                            │
│   ngx_http_request_t structure stores parsing state:                      │
│   • parse_state: Current position in state machine                        │
│   • header_in: Buffer containing raw request bytes                       │
│   • headers_in: Parsed headers (linked list)                             │
│   • uri, args, exten: Parsed URI components                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The 11 Phases of Request Processing

Nginx processes each request through a series of phases:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE 11 PHASES OF REQUEST PROCESSING                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Phase                     │ Purpose                    │ Modules         │
│  ──────────────────────────┼────────────────────────────┼─────────────────│
│                                                                            │
│  1. NGX_HTTP_POST_READ     │ First phase after headers  │ realip          │
│     PHASE                  │ received. Read real IP.    │                 │
│                            │                            │                 │
│  2. NGX_HTTP_SERVER_REWRITE│ Server-level rewrites     │ rewrite         │
│     PHASE                  │ (before location match)    │                 │
│                            │                            │                 │
│  3. NGX_HTTP_FIND_CONFIG   │ Location matching          │ (core only)     │
│     PHASE                  │ (cannot add handlers)      │                 │
│                            │                            │                 │
│  4. NGX_HTTP_REWRITE       │ Location-level rewrites    │ rewrite         │
│     PHASE                  │ (inside location block)    │                 │
│                            │                            │                 │
│  5. NGX_HTTP_POST_REWRITE  │ Jump back for internal     │ (core only)     │
│     PHASE                  │ redirects (max 10 cycles)  │                 │
│                            │                            │                 │
│  6. NGX_HTTP_PREACCESS     │ Before access control      │ limit_conn,     │
│     PHASE                  │ (rate limiting)            │ limit_req       │
│                            │                            │                 │
│  7. NGX_HTTP_ACCESS        │ Access control             │ access, auth,   │
│     PHASE                  │ (allow/deny, auth)         │ auth_request    │
│                            │                            │                 │
│  8. NGX_HTTP_POST_ACCESS   │ After access control       │ (core only)     │
│     PHASE                  │ (satisfy any/all logic)    │                 │
│                            │                            │                 │
│  9. NGX_HTTP_PRECONTENT    │ Before content             │ try_files,      │
│     PHASE                  │ generation                 │ mirror          │
│                            │                            │                 │
│ 10. NGX_HTTP_CONTENT       │ Generate response          │ static, proxy,  │
│     PHASE                  │ (only one handler runs)    │ fastcgi, uwsgi  │
│                            │                            │                 │
│ 11. NGX_HTTP_LOG           │ Request complete, log it   │ access_log      │
│     PHASE                  │                            │                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

**Phase Handler Execution Flow:**

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PHASE HANDLER EXECUTION                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Request arrives (headers parsed)                                         │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Phase 1: POST_READ                                                 │ │
│   │  ┌──────────┐                                                       │ │
│   │  │ realip   │ ──► Update client IP from X-Real-IP header           │ │
│   │  └──────────┘                                                       │ │
│   │  Return: NGX_OK (continue to next phase)                            │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Phase 2: SERVER_REWRITE                                            │ │
│   │  ┌──────────┐                                                       │ │
│   │  │ rewrite  │ ──► Apply server-level rewrites                       │ │
│   │  └──────────┘                                                       │ │
│   │  Return: NGX_OK or NGX_DECLINED (no rewrite needed)                 │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Phase 3: FIND_CONFIG                                               │ │
│   │                                                                     │ │
│   │  Match request URI to location block:                               │ │
│   │                                                                     │ │
│   │  location = /exact     { }   ◄── Exact match (highest priority)    │ │
│   │  location ^~ /prefix   { }   ◄── Prefix (stops regex search)       │ │
│   │  location ~ \.php$     { }   ◄── Regex (case sensitive)            │ │
│   │  location ~* \.jpg$    { }   ◄── Regex (case insensitive)          │ │
│   │  location /prefix      { }   ◄── Prefix (lowest priority)          │ │
│   │                                                                     │ │
│   │  Selected location stored in r->loc_conf                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Phases 4-9: REWRITE, ACCESS, PRECONTENT                            │ │
│   │                                                                     │ │
│   │  Each phase can:                                                    │ │
│   │  • NGX_OK: Handler done, continue                                   │ │
│   │  • NGX_DECLINED: Handler skipped, try next handler                 │ │
│   │  • NGX_AGAIN: Handler busy, add to event loop, resume later        │ │
│   │  • NGX_HTTP_xxx: Error or redirect (stop processing)               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Phase 10: CONTENT                                                  │ │
│   │                                                                     │ │
│   │  ONLY ONE content handler runs!                                     │ │
│   │                                                                     │ │
│   │  Priority:                                                          │ │
│   │  1. Location-specific handler (proxy_pass, fastcgi_pass, etc.)     │ │
│   │  2. Random index                                                    │ │
│   │  3. Index module                                                    │ │
│   │  4. Autoindex module                                                │ │
│   │  5. Static file handler (ngx_http_static_module)                   │ │
│   │                                                                     │ │
│   │  Content handler generates response headers + body                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│         │                                                                  │
│         ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │  Phase 11: LOG                                                      │ │
│   │  ┌─────────────┐                                                    │ │
│   │  │ access_log  │ ──► Write to access log                           │ │
│   │  └─────────────┘                                                    │ │
│   │                                                                     │ │
│   │  Logging happens AFTER response sent to client                      │ │
│   │  (non-blocking buffered writes)                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Filter Chain (Output Processing)

After the content handler generates a response, it passes through filter chains:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILTER CHAIN ARCHITECTURE                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Filters are LINKED LISTS processed in order. There are TWO chains:      │
│                                                                            │
│   1. HEADER FILTERS (process response headers)                            │
│   2. BODY FILTERS (process response body)                                 │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Content Handler                                                   │ │
│   │        │                                                            │ │
│   │        │ ngx_http_output_filter(r, body_chain)                     │ │
│   │        │ ngx_http_send_header(r)                                   │ │
│   │        ▼                                                            │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                    HEADER FILTER CHAIN                      │  │ │
│   │   │                                                             │  │ │
│   │   │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐        │  │ │
│   │   │  │not_mod │──►│headers │──►│ chunked│──►│ write  │        │  │ │
│   │   │  │ified   │   │        │   │        │   │        │        │  │ │
│   │   │  └────────┘   └────────┘   └────────┘   └────────┘        │  │ │
│   │   │                                             │              │  │ │
│   │   │  Each filter can:                           │              │  │ │
│   │   │  • Modify headers (add/remove/change)       ▼              │  │ │
│   │   │  • Short-circuit (return early)        Send to socket     │  │ │
│   │   │  • Call next filter                                        │  │ │
│   │   │                                                             │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                    BODY FILTER CHAIN                        │  │ │
│   │   │                                                             │  │ │
│   │   │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐        │  │ │
│   │   │  │  gzip  │──►│ ssi    │──►│ chunked│──►│ write  │        │  │ │
│   │   │  │compress│   │ include│   │ encode │   │ socket │        │  │ │
│   │   │  └────────┘   └────────┘   └────────┘   └────────┘        │  │ │
│   │   │                                             │              │  │ │
│   │   │  Each filter can:                           │              │  │ │
│   │   │  • Transform body (compress, encrypt)       ▼              │  │ │
│   │   │  • Buffer data (wait for more)         Send to socket     │  │ │
│   │   │  • Expand body (SSI includes)                              │  │ │
│   │   │                                                             │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON FILTERS:                                                          │
│   • gzip: Compress response body                                          │
│   • gunzip: Decompress for clients that don't support gzip               │
│   • ssi: Server-side includes                                             │
│   • sub: Substitute strings in response                                   │
│   • addition: Add content before/after response                          │
│   • charset: Convert character encodings                                  │
│   • chunked: Add chunked transfer encoding                                │
│   • headers: Modify response headers                                      │
│   • not_modified: Handle 304 Not Modified                                 │
│                                                                            │
│   FILTER ORDER MATTERS:                                                    │
│   Filters are linked at compile time in reverse order:                    │
│                                                                            │
│   static ngx_http_output_header_filter_pt  ngx_http_top_header_filter;   │
│                                                                            │
│   // Each module does:                                                     │
│   ngx_http_next_header_filter = ngx_http_top_header_filter;              │
│   ngx_http_top_header_filter = my_header_filter;                         │
│                                                                            │
│   // Results in: my_filter -> previous_top -> ... -> write_filter        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Upstream and Reverse Proxy

### Reverse Proxy Architecture

When nginx proxies requests to backend servers:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    REVERSE PROXY DATA FLOW                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                                                                            │
│   Client          Nginx Worker            Upstream Server                  │
│   ──────          ────────────            ───────────────                  │
│                                                                            │
│   ┌──────┐        ┌──────────────────────────────────┐        ┌──────┐   │
│   │      │  (1)   │                                  │  (3)   │      │   │
│   │      │───────►│ Accept connection                │───────►│      │   │
│   │      │  TCP   │                                  │  TCP   │      │   │
│   │      │        │ ┌──────────────────────────────┐│        │      │   │
│   │      │  (2)   │ │                              ││  (4)   │      │   │
│   │Client│───────►│ │ Parse HTTP request           ││───────►│Server│   │
│   │      │  HTTP  │ │                              ││ HTTP   │      │   │
│   │      │ Request│ │ Determine upstream           ││Request │      │   │
│   │      │        │ │ (proxy_pass)                 ││        │      │   │
│   │      │        │ │                              ││        │      │   │
│   │      │        │ │ Connect to upstream          ││        │      │   │
│   │      │        │ │ (or reuse connection)        ││        │      │   │
│   │      │        │ │                              ││        │      │   │
│   │      │        │ │ Forward request              ││        │      │   │
│   │      │        │ └──────────────────────────────┘│        │      │   │
│   │      │        │                                  │        │      │   │
│   │      │        │ ┌──────────────────────────────┐│  (5)   │      │   │
│   │      │  (6)   │ │                              ││◄───────│      │   │
│   │      │◄───────│ │ Read upstream response       ││  HTTP  │      │   │
│   │      │  HTTP  │ │ (may be streamed/buffered)   ││Response│      │   │
│   │      │Response│ │                              ││        │      │   │
│   │      │        │ │ Apply response filters       ││        │      │   │
│   │      │        │ │ (gzip, headers, etc.)        ││        │      │   │
│   │      │        │ │                              ││        │      │   │
│   │      │        │ │ Send to client               ││        │      │   │
│   │      │        │ └──────────────────────────────┘│        │      │   │
│   └──────┘        └──────────────────────────────────┘        └──────┘   │
│                                                                            │
│   KEY DIRECTIVES:                                                          │
│   location /api/ {                                                        │
│       proxy_pass http://backend;                                          │
│       proxy_http_version 1.1;                                             │
│       proxy_set_header Host $host;                                        │
│       proxy_set_header X-Real-IP $remote_addr;                           │
│       proxy_buffering on;                                                 │
│       proxy_buffer_size 4k;                                               │
│       proxy_buffers 8 4k;                                                 │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Load Balancing Algorithms

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCING ALGORITHMS                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   upstream backend {                                                       │
│       # Load balancing method goes here                                   │
│       server 10.0.0.1:8080;                                               │
│       server 10.0.0.2:8080;                                               │
│       server 10.0.0.3:8080;                                               │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ ROUND ROBIN (default)                                               │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │ Req1 ──► Server 1                                                   │ │
│   │ Req2 ──► Server 2                                                   │ │
│   │ Req3 ──► Server 3                                                   │ │
│   │ Req4 ──► Server 1  (cycle repeats)                                  │ │
│   │                                                                     │ │
│   │ With weights:  server 10.0.0.1 weight=3;                           │ │
│   │                server 10.0.0.2 weight=1;                           │ │
│   │                                                                     │ │
│   │ Req1 ──► Server 1 │                                                │ │
│   │ Req2 ──► Server 1 │ 3 requests to server 1                         │ │
│   │ Req3 ──► Server 1 │                                                │ │
│   │ Req4 ──► Server 2                                                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ LEAST CONNECTIONS: least_conn;                                      │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │ Send to server with fewest active connections                       │ │
│   │                                                                     │ │
│   │ Server 1: ████████░░░░  (8 connections)                            │ │
│   │ Server 2: ████░░░░░░░░  (4 connections)  ◄── Next request goes here│ │
│   │ Server 3: ██████░░░░░░  (6 connections)                            │ │
│   │                                                                     │ │
│   │ Good for: Long-lived connections, variable processing times        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ IP HASH: ip_hash;                                                   │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │ Same client IP always goes to same server (session persistence)    │ │
│   │                                                                     │ │
│   │ hash(client_ip) % num_servers = server_index                       │ │
│   │                                                                     │ │
│   │ 192.168.1.1 ──► hash ──► Server 1  (always)                        │ │
│   │ 192.168.1.2 ──► hash ──► Server 3  (always)                        │ │
│   │                                                                     │ │
│   │ Good for: Session affinity, stateful applications                   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │ GENERIC HASH: hash $request_uri consistent;                         │ │
│   ├─────────────────────────────────────────────────────────────────────┤ │
│   │                                                                     │ │
│   │ Hash any variable. "consistent" uses ketama consistent hashing.    │ │
│   │                                                                     │ │
│   │ hash($request_uri) ──► Server                                      │ │
│   │                                                                     │ │
│   │ Same URI always goes to same server (good for caching)             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Upstream Connection Pooling (Keepalive)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UPSTREAM CONNECTION POOLING                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WITHOUT keepalive (default):                                            │
│   ────────────────────────────                                            │
│                                                                            │
│   Request 1:  Connect ──► Send ──► Recv ──► Close                        │
│   Request 2:  Connect ──► Send ──► Recv ──► Close                        │
│   Request 3:  Connect ──► Send ──► Recv ──► Close                        │
│               ▲                                                            │
│               └── TCP handshake overhead for EVERY request                │
│                                                                            │
│   WITH keepalive:                                                         │
│   ───────────────                                                         │
│                                                                            │
│   Request 1:  Connect ──► Send ──► Recv ──┐                              │
│   Request 2:             Send ──► Recv ──┤  (reuse connection)           │
│   Request 3:             Send ──► Recv ──┤                               │
│               ...        ...              │                               │
│   Idle timeout:                      ────► Close                          │
│                                                                            │
│   upstream backend {                                                       │
│       server 10.0.0.1:8080;                                               │
│       server 10.0.0.2:8080;                                               │
│       keepalive 32;          # Keep up to 32 idle connections per worker │
│       keepalive_timeout 60s; # Close idle connections after 60 seconds   │
│       keepalive_requests 100; # Max requests per connection              │
│   }                                                                        │
│                                                                            │
│   location /api/ {                                                        │
│       proxy_pass http://backend;                                          │
│       proxy_http_version 1.1;        # Required for keepalive            │
│       proxy_set_header Connection ""; # Clear "Connection: close"        │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Worker Process                                                    │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │  Connection Pool for "backend"                                ││ │
│   │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐       ┌─────────┐      ││ │
│   │   │  │  Conn 1 │ │  Conn 2 │ │  Conn 3 │  ...  │  Conn N │      ││ │
│   │   │  │  IDLE   │ │  BUSY   │ │  IDLE   │       │  BUSY   │      ││ │
│   │   │  │ 10.0.0.1│ │ 10.0.0.1│ │ 10.0.0.2│       │ 10.0.0.2│      ││ │
│   │   │  └─────────┘ └─────────┘ └─────────┘       └─────────┘      ││ │
│   │   │                                                               ││ │
│   │   │  New request arrives:                                         ││ │
│   │   │  1. Check pool for idle connection to target server          ││ │
│   │   │  2. If found: reuse it                                       ││ │
│   │   │  3. If not found: create new connection                      ││ │
│   │   │  4. After response: return connection to pool                ││ │
│   │   │                                                               ││ │
│   │   └───────────────────────────────────────────────────────────────┘│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BENEFITS:                                                                │
│   • Eliminates TCP handshake latency (1 RTT saved per request)           │
│   • Reduces connection count on backend servers                           │
│   • Enables HTTP/1.1 pipelining to upstream                              │
│   • Critical for high-throughput proxy scenarios                          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Health Checks

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HEALTH CHECKS                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PASSIVE HEALTH CHECKS (Open Source nginx):                              │
│   ──────────────────────────────────────────                              │
│                                                                            │
│   Monitor upstream responses for failures. Mark server as down.           │
│                                                                            │
│   upstream backend {                                                       │
│       server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;                 │
│       server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;                 │
│   }                                                                        │
│                                                                            │
│   Timeline:                                                                │
│   ─────────                                                               │
│   t=0s    Request to 10.0.0.1 → Connection refused (fail_count=1)        │
│   t=1s    Request to 10.0.0.1 → Connection refused (fail_count=2)        │
│   t=2s    Request to 10.0.0.1 → Connection refused (fail_count=3)        │
│   t=2s    ▲ Server marked UNAVAILABLE                                     │
│   t=2s-32s All requests go to 10.0.0.2 only                              │
│   t=32s   fail_timeout expires, server marked AVAILABLE                   │
│   t=32s   Next request tries 10.0.0.1 again                              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │     Server State Machine:                                           │ │
│   │                                                                     │ │
│   │     ┌──────────┐   fail_count >= max_fails   ┌─────────────┐       │ │
│   │     │          │────────────────────────────►│             │       │ │
│   │     │ AVAILABLE│                             │ UNAVAILABLE │       │ │
│   │     │          │◄────────────────────────────│             │       │ │
│   │     └──────────┘   fail_timeout expires      └─────────────┘       │ │
│   │                                                                     │ │
│   │     What counts as a failure:                                       │ │
│   │     • Connection refused                                           │ │
│   │     • Connection timeout                                            │ │
│   │     • 502, 503, 504 responses (configurable via proxy_next_upstream)│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ACTIVE HEALTH CHECKS (nginx Plus):                                      │
│   ──────────────────────────────────                                      │
│                                                                            │
│   upstream backend {                                                       │
│       zone backend 64k;                                                   │
│       server 10.0.0.1:8080;                                               │
│       server 10.0.0.2:8080;                                               │
│   }                                                                        │
│                                                                            │
│   server {                                                                 │
│       location / {                                                        │
│           proxy_pass http://backend;                                      │
│           health_check interval=5s fails=3 passes=2;                     │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │     Active probing in background:                                   │ │
│   │                                                                     │ │
│   │     Every 5 seconds:                                                │ │
│   │     ┌─────────────┐                      ┌─────────────┐           │ │
│   │     │   nginx     │  GET /health HTTP/1.1 │  Backend    │           │ │
│   │     │   worker    │─────────────────────►│  Server     │           │ │
│   │     │             │◄─────────────────────│             │           │ │
│   │     └─────────────┘  200 OK / Timeout    └─────────────┘           │ │
│   │                                                                     │ │
│   │     Shared memory zone tracks health across all workers            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffering and Streaming

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BUFFERING AND STREAMING                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Two modes: BUFFERED (default) and UNBUFFERED (streaming)                │
│                                                                            │
│   BUFFERED MODE (proxy_buffering on):                                     │
│   ────────────────────────────────────                                    │
│                                                                            │
│   ┌──────┐        ┌─────────────────────┐        ┌────────┐              │
│   │      │        │     nginx           │        │        │              │
│   │      │        │  ┌───────────────┐ │        │Backend │              │
│   │Client│◄─ slow─│  │   BUFFER      │ │◄─fast──│ Server │              │
│   │      │        │  │ (memory/disk) │ │        │        │              │
│   │      │        │  └───────────────┘ │        │        │              │
│   └──────┘        └─────────────────────┘        └────────┘              │
│                                                                            │
│   Benefits:                                                                │
│   • Backend freed quickly (not waiting for slow clients)                  │
│   • Backend connections can be reused sooner                              │
│   • Protects backends from slow clients (slowloris)                       │
│                                                                            │
│   proxy_buffering on;                                                     │
│   proxy_buffer_size 4k;      # Buffer for first part (headers)           │
│   proxy_buffers 8 4k;        # Number and size of buffers                │
│   proxy_busy_buffers_size 8k; # Max size to send while still buffering  │
│   proxy_max_temp_file_size 1024m; # Spill to disk if buffers full       │
│   proxy_temp_path /var/cache/nginx/proxy_temp;                           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Buffer Flow:                                                      │ │
│   │                                                                     │ │
│   │   Response     ┌─────┐┌─────┐┌─────┐┌─────┐   Temp File            │ │
│   │   from ──────► │ Buf ││ Buf ││ Buf ││ Buf │───► (overflow)        │ │
│   │   upstream     │  1  ││  2  ││  3  ││  4  │                        │ │
│   │                └─────┘└─────┘└─────┘└─────┘                        │ │
│   │                    │                   ▲                            │ │
│   │                    ▼                   │                            │ │
│   │                Send to              Read from                       │ │
│   │                client               temp file                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   UNBUFFERED MODE (streaming):                                            │
│   ─────────────────────────────                                           │
│                                                                            │
│   proxy_buffering off;                                                    │
│   # Or: upstream sends X-Accel-Buffering: no                             │
│                                                                            │
│   ┌──────┐        ┌─────────────────────┐        ┌────────┐              │
│   │      │        │     nginx           │        │        │              │
│   │      │        │                     │        │Backend │              │
│   │Client│◄───────│────────────────────│◄───────│ Server │              │
│   │      │        │  (pass-through)    │        │        │              │
│   │      │        │                     │        │        │              │
│   └──────┘        └─────────────────────┘        └────────┘              │
│                                                                            │
│   Good for:                                                                │
│   • Server-Sent Events (SSE)                                              │
│   • Long-polling                                                           │
│   • Streaming video/audio                                                  │
│   • WebSocket upgrades (handled separately)                               │
│                                                                            │
│   CHUNKED TRANSFER:                                                        │
│   ──────────────────                                                       │
│                                                                            │
│   When Content-Length is unknown, use chunked encoding:                   │
│                                                                            │
│   HTTP/1.1 200 OK                                                         │
│   Transfer-Encoding: chunked                                              │
│                                                                            │
│   5\r\n                                                                   │
│   Hello\r\n                                                               │
│   6\r\n                                                                   │
│   World!\r\n                                                              │
│   0\r\n                                                                   │
│   \r\n                                                                    │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Memory Management

### Pool Allocator

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NGINX POOL ALLOCATOR                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Every request gets a MEMORY POOL. When request ends, entire pool freed.│
│                                                                            │
│   WHY POOLS?                                                               │
│   ──────────                                                               │
│   • No individual free() calls needed during request processing           │
│   • No memory leaks (entire pool freed at once)                           │
│   • Fast allocation (simple pointer bump)                                 │
│   • Good cache locality (contiguous allocations)                          │
│                                                                            │
│   ngx_pool_t structure:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ngx_pool_t                                                        │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │ d (pool_data_t)                                               ││ │
│   │   │   ├─ last:    pointer to end of used memory                   ││ │
│   │   │   ├─ end:     pointer to end of pool block                    ││ │
│   │   │   ├─ next:    next pool block (for chaining)                  ││ │
│   │   │   └─ failed:  allocation failures (triggers new block)        ││ │
│   │   │                                                               ││ │
│   │   │ max:       max small allocation size (< page size)           ││ │
│   │   │ current:   current pool block for allocations                 ││ │
│   │   │ chain:     free buffer chains                                 ││ │
│   │   │ large:     linked list of large allocations                  ││ │
│   │   │ cleanup:   cleanup handlers (called on destroy)              ││ │
│   │   │ log:       logger                                             ││ │
│   │   └───────────────────────────────────────────────────────────────┘│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ALLOCATION ALGORITHM:                                                    │
│   ─────────────────────                                                    │
│                                                                            │
│   ngx_palloc(pool, size):                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   if (size <= pool->max) {                                         │ │
│   │       // SMALL ALLOCATION - from pool block                        │ │
│   │       p = pool->current;                                           │ │
│   │       while (p) {                                                  │ │
│   │           if (p->d.end - p->d.last >= size) {                     │ │
│   │               m = p->d.last;                                       │ │
│   │               p->d.last += size;  // Simple pointer bump!         │ │
│   │               return m;                                            │ │
│   │           }                                                        │ │
│   │           p = p->d.next;                                           │ │
│   │       }                                                            │ │
│   │       // No space - allocate new block                             │ │
│   │       return ngx_palloc_block(pool, size);                         │ │
│   │   } else {                                                         │ │
│   │       // LARGE ALLOCATION - separate malloc                        │ │
│   │       return ngx_palloc_large(pool, size);                         │ │
│   │   }                                                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MEMORY LAYOUT:                                                           │
│   ───────────────                                                          │
│                                                                            │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │ Pool Block 1                                                      │   │
│   │ ┌───────┬────────────────────────────────────────────────────────┐│   │
│   │ │ Header│ Alloc1 │ Alloc2 │ Alloc3 │       Free Space           ││   │
│   │ └───────┴────────────────────────────────────────────────────────┘│   │
│   │         ▲                           ▲                     ▲       │   │
│   │      start                        last                  end       │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                    │                                                       │
│                    │ next                                                  │
│                    ▼                                                       │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │ Pool Block 2 (allocated when block 1 couldn't fit new alloc)     │   │
│   │ ┌───────┬────────────────────────────────────────────────────────┐│   │
│   │ │ Header│ Alloc4 │ Alloc5 │          Free Space                  ││   │
│   │ └───────┴────────────────────────────────────────────────────────┘│   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│   Large allocations (separate linked list):                               │
│   ┌──────────────┐    ┌──────────────┐                                   │
│   │ Large Alloc 1│───►│ Large Alloc 2│───► NULL                          │
│   │ (50KB data)  │    │ (200KB data) │                                   │
│   └──────────────┘    └──────────────┘                                   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Shared Memory Zones

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SHARED MEMORY ZONES                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Workers are separate processes. How do they share state?                │
│   Answer: SHARED MEMORY mapped into all worker address spaces.            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Master Process                                                    │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │  mmap() shared memory region                                │  │ │
│   │   │  Initialize slab allocator                                  │  │ │
│   │   │  fork() workers (they inherit the mapping)                  │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   ┌──────────────────────────────────────────────────────────────┐ │ │
│   │   │                   Shared Memory                              │ │ │
│   │   │  ┌─────────────────────────────────────────────────────────┐│ │ │
│   │   │  │  Slab Allocator Header                                  ││ │ │
│   │   │  ├─────────────────────────────────────────────────────────┤│ │ │
│   │   │  │  Zone 1: "limit_req_zone" (rate limiting counters)     ││ │ │
│   │   │  │  Zone 2: "proxy_cache_keys" (cache metadata)           ││ │ │
│   │   │  │  Zone 3: "upstream_zone" (server health status)        ││ │ │
│   │   │  │  Zone 4: "ssl_session_cache" (SSL sessions)            ││ │ │
│   │   │  └─────────────────────────────────────────────────────────┘│ │ │
│   │   └──────────────────────────────────────────────────────────────┘ │ │
│   │                │                 │                │                │ │
│   │                │                 │                │                │ │
│   │                ▼                 ▼                ▼                │ │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │ │
│   │   │   Worker 1   │  │   Worker 2   │  │   Worker N   │            │ │
│   │   │              │  │              │  │              │            │ │
│   │   │ (same vaddr) │  │ (same vaddr) │  │ (same vaddr) │            │ │
│   │   └──────────────┘  └──────────────┘  └──────────────┘            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION EXAMPLE:                                                   │
│   ──────────────────────                                                   │
│                                                                            │
│   # Rate limiting zone                                                    │
│   limit_req_zone $binary_remote_addr zone=one:10m rate=1r/s;             │
│                                                                            │
│   # Upstream health tracking                                              │
│   upstream backend {                                                       │
│       zone backend 64k;   # 64KB shared memory for this upstream         │
│       server 10.0.0.1:8080;                                               │
│       server 10.0.0.2:8080;                                               │
│   }                                                                        │
│                                                                            │
│   # Cache metadata                                                        │
│   proxy_cache_path /var/cache/nginx                                       │
│       keys_zone=my_cache:10m   # 10MB for cache keys                     │
│       max_size=10g;                                                        │
│                                                                            │
│   SYNCHRONIZATION:                                                         │
│   ─────────────────                                                        │
│                                                                            │
│   Shared memory requires LOCKING to prevent race conditions.              │
│                                                                            │
│   ngx_shmtx_t (shared memory mutex):                                      │
│   • Uses atomic operations (compare-and-swap)                             │
│   • Falls back to file-based locks on older systems                       │
│   • Spinlock with exponential backoff                                     │
│                                                                            │
│   Critical section:                                                        │
│   ngx_shmtx_lock(&shpool->mutex);                                         │
│   // ... modify shared data ...                                           │
│   ngx_shmtx_unlock(&shpool->mutex);                                       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Buffer Chains

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    BUFFER CHAINS                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Nginx processes data in BUFFER CHAINS - linked lists of buffers.       │
│                                                                            │
│   ngx_buf_t (single buffer):                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ngx_buf_t                                                         │ │
│   │   ┌───────────────────────────────────────────────────────────────┐│ │
│   │   │ pos:           current read position                          ││ │
│   │   │ last:          end of valid data                              ││ │
│   │   │ file_pos:      position in file (if file buffer)             ││ │
│   │   │ file_last:     end position in file                           ││ │
│   │   │ start:         start of buffer memory                         ││ │
│   │   │ end:           end of buffer memory                           ││ │
│   │   │ tag:           which module created this buffer               ││ │
│   │   │ file:          file descriptor (if file buffer)              ││ │
│   │   │ shadow:        related buffer (for copying)                   ││ │
│   │   │                                                               ││ │
│   │   │ FLAGS:                                                        ││ │
│   │   │ • temporary:    data can be modified                          ││ │
│   │   │ • memory:       data is in memory                             ││ │
│   │   │ • mmap:         data is memory-mapped file                    ││ │
│   │   │ • in_file:      data is in a file                             ││ │
│   │   │ • flush:        flush data after this buffer                  ││ │
│   │   │ • last_buf:     last buffer in request                        ││ │
│   │   │ • last_in_chain: last buffer in current chain                ││ │
│   │   └───────────────────────────────────────────────────────────────┘│ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ngx_chain_t (linked list):                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌─────────┐     ┌─────────┐     ┌─────────┐                     │ │
│   │   │ chain_t │────►│ chain_t │────►│ chain_t │────► NULL          │ │
│   │   │ ┌─────┐ │     │ ┌─────┐ │     │ ┌─────┐ │                     │ │
│   │   │ │ buf │ │     │ │ buf │ │     │ │ buf │ │                     │ │
│   │   │ └──┬──┘ │     │ └──┬──┘ │     │ └──┬──┘ │                     │ │
│   │   └────┼────┘     └────┼────┘     └────┼────┘                     │ │
│   │        │               │               │                           │ │
│   │        ▼               ▼               ▼                           │ │
│   │   ┌─────────┐     ┌─────────┐     ┌─────────┐                     │ │
│   │   │ Memory  │     │  File   │     │ Memory  │                     │ │
│   │   │  Block  │     │  Range  │     │  Block  │                     │ │
│   │   │ "HTTP/1"│     │ /img.png│     │ "0\r\n" │                     │ │
│   │   └─────────┘     └─────────┘     └─────────┘                     │ │
│   │                                                                     │ │
│   │   A chain can mix memory and file buffers!                         │ │
│   │   • Memory: in-memory data (headers, generated content)           │ │
│   │   • File: disk data (static files, cached content)                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY BUFFER CHAINS?                                                       │
│   ───────────────────                                                      │
│                                                                            │
│   • Zero-copy: File buffers passed directly to sendfile()               │
│   • Scatter-gather I/O: Multiple buffers → single writev() call         │
│   • Streaming: Process data incrementally, don't wait for all data      │
│   • Memory efficiency: Reuse buffers, don't allocate for every chunk    │
│                                                                            │
│   EXAMPLE: HTTP Response                                                   │
│   ───────────────────────                                                  │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                                                                  │   │
│   │  Chain for response:                                             │   │
│   │                                                                  │   │
│   │  ┌─────────┐   ┌─────────────┐   ┌─────────┐                    │   │
│   │  │ Headers │──►│  File Body  │──►│ Trailer │──► NULL           │   │
│   │  │(memory) │   │  (sendfile) │   │(memory) │                    │   │
│   │  │         │   │             │   │         │                    │   │
│   │  │"HTTP/1.1│   │/var/www/    │   │"0\r\n"  │                    │   │
│   │  │200 OK\r\n│  │index.html  │   │"\r\n"   │                    │   │
│   │  │..."     │   │offset=0    │   │         │                    │   │
│   │  │         │   │length=4096 │   │last_buf │                    │   │
│   │  └─────────┘   └─────────────┘   └─────────┘                    │   │
│   │                                                                  │   │
│   │  Sent with: writev(headers) + sendfile(body) + writev(trailer)  │   │
│   │                                                                  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Caching

### Proxy Cache Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROXY CACHE ARCHITECTURE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Nginx can cache responses from upstream servers.                        │
│                                                                            │
│   proxy_cache_path /var/cache/nginx                                       │
│       levels=1:2                 # Directory depth                        │
│       keys_zone=my_cache:10m     # Shared memory for keys                │
│       max_size=10g               # Max disk usage                         │
│       inactive=60m               # Remove unused after 60 min            │
│       use_temp_path=off;         # Write directly to cache               │
│                                                                            │
│   location /api/ {                                                        │
│       proxy_cache my_cache;                                               │
│       proxy_cache_valid 200 302 10m;   # Cache success for 10 min        │
│       proxy_cache_valid 404 1m;         # Cache 404 for 1 min            │
│       proxy_cache_key "$scheme$host$request_uri";                        │
│       proxy_pass http://backend;                                          │
│   }                                                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   REQUEST FLOW WITH CACHE:                                          │ │
│   │                                                                     │ │
│   │   ┌──────────┐                                                     │ │
│   │   │  Client  │                                                     │ │
│   │   │  Request │                                                     │ │
│   │   └────┬─────┘                                                     │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   ┌────────────────────────────────────────────────────────┐       │ │
│   │   │           Compute Cache Key                            │       │ │
│   │   │   md5("https://example.com/api/users")                │       │ │
│   │   │   = "a1b2c3d4e5f6..."                                  │       │ │
│   │   └────────────────────────────────────────────────────────┘       │ │
│   │        │                                                            │ │
│   │        ▼                                                            │ │
│   │   ┌────────────────────────────────────────────────────────┐       │ │
│   │   │           Lookup in Shared Memory                      │       │ │
│   │   │   keys_zone = { key: "a1b2...", node: {...} }         │       │ │
│   │   └────────────────────────────────────────────────────────┘       │ │
│   │        │                                                            │ │
│   │        ├─── HIT ──────────────────────┐                            │ │
│   │        │                              │                            │ │
│   │        │                              ▼                            │ │
│   │        │                    ┌───────────────────┐                  │ │
│   │        │                    │  Read from Disk   │                  │ │
│   │        │                    │  /var/cache/nginx │                  │ │
│   │        │                    │  /a/1b/a1b2c3...  │                  │ │
│   │        │                    └────────┬──────────┘                  │ │
│   │        │                             │                              │ │
│   │        ▼ MISS                        │                              │ │
│   │   ┌────────────┐                     │                              │ │
│   │   │   Proxy    │                     │                              │ │
│   │   │to upstream │                     │                              │ │
│   │   └─────┬──────┘                     │                              │ │
│   │         │                            │                              │ │
│   │         ▼                            ▼                              │ │
│   │   ┌──────────────────────────────────────────────┐                 │ │
│   │   │              Send Response to Client          │                 │ │
│   │   │         (and store in cache if cacheable)    │                 │ │
│   │   └──────────────────────────────────────────────┘                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Cache File Structure

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CACHE FILE STRUCTURE                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   DIRECTORY STRUCTURE (levels=1:2):                                       │
│   ──────────────────────────────────                                       │
│                                                                            │
│   /var/cache/nginx/                                                        │
│   ├── a/                              # First level (1 char)              │
│   │   └── 1b/                         # Second level (2 chars)            │
│   │       └── a1b2c3d4e5f67890...     # Cache file (full MD5)             │
│   ├── f/                                                                   │
│   │   └── 3e/                                                              │
│   │       └── f3e2d1c0b9a87654...                                         │
│   └── ...                                                                  │
│                                                                            │
│   CACHE FILE FORMAT:                                                       │
│   ───────────────────                                                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Cache File: /var/cache/nginx/a/1b/a1b2c3d4e5f67890...            │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │  CACHE HEADER (binary)                                      │  │ │
│   │   │  ─────────────────────                                      │  │ │
│   │   │  • version                                                  │  │ │
│   │   │  • valid_sec, valid_msec (when cache entry expires)        │  │ │
│   │   │  • last_modified, date, etag                               │  │ │
│   │   │  • body_start (offset to response body)                    │  │ │
│   │   │  • status (HTTP status code)                               │  │ │
│   │   │  • header_start, header_length                             │  │ │
│   │   │  • key (cache key string)                                   │  │ │
│   │   ├─────────────────────────────────────────────────────────────┤  │ │
│   │   │  RESPONSE HEADERS (text)                                    │  │ │
│   │   │  ───────────────────────                                    │  │ │
│   │   │  HTTP/1.1 200 OK                                            │  │ │
│   │   │  Content-Type: application/json                             │  │ │
│   │   │  Content-Length: 1234                                       │  │ │
│   │   │  ...                                                        │  │ │
│   │   ├─────────────────────────────────────────────────────────────┤  │ │
│   │   │  RESPONSE BODY                                              │  │ │
│   │   │  ─────────────                                              │  │ │
│   │   │  {"users": [...]}                                           │  │ │
│   │   │  ...                                                        │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CACHE STATUS HEADER ($upstream_cache_status):                           │
│   ──────────────────────────────────────────────                           │
│                                                                            │
│   add_header X-Cache-Status $upstream_cache_status;                       │
│                                                                            │
│   Values:                                                                  │
│   • HIT:      Served from cache                                           │
│   • MISS:     Not in cache, proxied to upstream                          │
│   • EXPIRED:  Cache entry expired, proxied to upstream                   │
│   • STALE:    Served stale while revalidating                             │
│   • UPDATING: Stale served, update in progress                            │
│   • REVALIDATED: Upstream confirmed cache still valid (304)               │
│   • BYPASS:   Cache bypassed (proxy_cache_bypass)                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Cache Manager and Loader

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CACHE MANAGER AND LOADER                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Two background processes manage the cache:                              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ┌────────────┐                                                    │ │
│   │   │   CACHE    │   Runs on startup                                  │ │
│   │   │   LOADER   │   • Scans cache directory                         │ │
│   │   │            │   • Loads cache metadata into shared memory       │ │
│   │   │            │   • Gradual loading (loader_files, loader_sleep)  │ │
│   │   └────────────┘                                                    │ │
│   │                                                                     │ │
│   │   ┌────────────┐                                                    │ │
│   │   │   CACHE    │   Runs periodically (manager_sleep)               │ │
│   │   │   MANAGER  │   • Enforces max_size (deletes oldest)           │ │
│   │   │            │   • Removes inactive entries                      │ │
│   │   │            │   • Enforces manager_files, manager_threshold    │ │
│   │   └────────────┘                                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   Configuration:                                                           │
│   ───────────────                                                          │
│                                                                            │
│   proxy_cache_path /var/cache/nginx                                       │
│       levels=1:2                                                           │
│       keys_zone=my_cache:10m                                              │
│       max_size=10g                                                         │
│       inactive=60m                                                         │
│       loader_files=100       # Files per loader iteration                 │
│       loader_sleep=50ms      # Sleep between iterations                   │
│       loader_threshold=200ms # Max time per iteration                     │
│       manager_files=100      # Files per manager iteration                │
│       manager_sleep=50ms     # Sleep between manager runs                 │
│       manager_threshold=200ms;                                             │
│                                                                            │
│   CACHE LOCK (thundering herd prevention):                                │
│   ─────────────────────────────────────────                                │
│                                                                            │
│   proxy_cache_lock on;                                                    │
│   proxy_cache_lock_timeout 5s;                                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WITHOUT proxy_cache_lock:                                        │ │
│   │   ──────────────────────────                                        │ │
│   │   Request 1 ──► MISS ──► Upstream ──┐                              │ │
│   │   Request 2 ──► MISS ──► Upstream ──┤  All hit backend!            │ │
│   │   Request 3 ──► MISS ──► Upstream ──┤                              │ │
│   │   Request 4 ──► MISS ──► Upstream ──┘                              │ │
│   │                                                                     │ │
│   │   WITH proxy_cache_lock on:                                        │ │
│   │   ─────────────────────────                                         │ │
│   │   Request 1 ──► MISS ──► Upstream ──► Cache ──┐                    │ │
│   │   Request 2 ──► WAIT ─────────────────────────┤                    │ │
│   │   Request 3 ──► WAIT ─────────────────────────┤ All get cached!    │ │
│   │   Request 4 ──► WAIT ─────────────────────────┘                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 9. SSL/TLS Handling

### SSL Termination Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SSL/TLS TERMINATION                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Nginx handles SSL/TLS encryption, backends receive plain HTTP.          │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Client              nginx                  Backend               │ │
│   │                                                                     │ │
│   │   ┌──────┐           ┌──────┐              ┌──────┐                │ │
│   │   │      │   HTTPS   │      │    HTTP      │      │                │ │
│   │   │      │═══════════│      │─────────────►│      │                │ │
│   │   │      │   (TLS)   │      │  (plaintext) │      │                │ │
│   │   └──────┘           └──────┘              └──────┘                │ │
│   │                          │                                          │ │
│   │                    ┌─────┴─────┐                                    │ │
│   │                    │ SSL/TLS   │                                    │ │
│   │                    │ Termination│                                   │ │
│   │                    │           │                                    │ │
│   │                    │ • Decrypt │                                    │ │
│   │                    │ • Verify  │                                    │ │
│   │                    │ • Compress│                                    │ │
│   │                    └───────────┘                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│   ───────────────                                                          │
│                                                                            │
│   server {                                                                 │
│       listen 443 ssl http2;                                               │
│       server_name example.com;                                            │
│                                                                            │
│       ssl_certificate     /etc/ssl/certs/example.com.crt;                │
│       ssl_certificate_key /etc/ssl/private/example.com.key;              │
│                                                                            │
│       ssl_protocols TLSv1.2 TLSv1.3;                                      │
│       ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:...;                     │
│       ssl_prefer_server_ciphers on;                                       │
│                                                                            │
│       ssl_session_cache shared:SSL:10m;                                   │
│       ssl_session_timeout 1d;                                             │
│       ssl_session_tickets off;                                            │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### SSL Session Resumption

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SSL SESSION RESUMPTION                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TLS handshake is EXPENSIVE (multiple round trips, crypto operations).   │
│   Session resumption allows clients to skip most of the handshake.        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   FULL TLS 1.2 HANDSHAKE (2 round trips):                          │ │
│   │   ─────────────────────────────────────────                         │ │
│   │                                                                     │ │
│   │   Client                                Server                      │ │
│   │      │                                     │                        │ │
│   │      │─────── ClientHello ────────────────►│                        │ │
│   │      │                                     │                        │ │
│   │      │◄────── ServerHello ─────────────────│                        │ │
│   │      │◄────── Certificate ─────────────────│                        │ │
│   │      │◄────── ServerKeyExchange ───────────│  Round trip 1         │ │
│   │      │◄────── ServerHelloDone ─────────────│                        │ │
│   │      │                                     │                        │ │
│   │      │─────── ClientKeyExchange ──────────►│                        │ │
│   │      │─────── ChangeCipherSpec ───────────►│  Round trip 2         │ │
│   │      │─────── Finished ───────────────────►│                        │ │
│   │      │                                     │                        │ │
│   │      │◄────── ChangeCipherSpec ────────────│                        │ │
│   │      │◄────── Finished ────────────────────│                        │ │
│   │      │                                     │                        │ │
│   │      │═══════ Encrypted Data ═════════════►│                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   METHOD 1: SESSION ID (server-side cache)                                │
│   ─────────────────────────────────────────────                            │
│                                                                            │
│   ssl_session_cache shared:SSL:10m;   # 10MB shared across workers       │
│   ssl_session_timeout 1d;             # Sessions valid for 1 day         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   First connection:                                                 │ │
│   │   Server generates session_id, stores session in shared memory     │ │
│   │   Client receives session_id                                        │ │
│   │                                                                     │ │
│   │   Subsequent connection:                                            │ │
│   │   Client sends session_id in ClientHello                           │ │
│   │   Server looks up session in cache                                  │ │
│   │   If found: abbreviated handshake (1 round trip)                   │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────┐          │ │
│   │   │             Shared Memory: SSL Session Cache        │          │ │
│   │   │  ┌─────────────────────────────────────────────────┐│          │ │
│   │   │  │ session_id_1 → {master_secret, cipher, expiry} ││          │ │
│   │   │  │ session_id_2 → {master_secret, cipher, expiry} ││          │ │
│   │   │  │ session_id_3 → {master_secret, cipher, expiry} ││          │ │
│   │   │  │ ...                                             ││          │ │
│   │   │  └─────────────────────────────────────────────────┘│          │ │
│   │   │       ▲           ▲           ▲                     │          │ │
│   │   │       │           │           │                     │          │ │
│   │   │   Worker 1    Worker 2    Worker N                  │          │ │
│   │   └─────────────────────────────────────────────────────┘          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   METHOD 2: SESSION TICKETS (client-side storage)                         │
│   ────────────────────────────────────────────────                         │
│                                                                            │
│   ssl_session_tickets on;                                                 │
│   ssl_session_ticket_key /etc/nginx/ticket.key;  # 48-byte key           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   First connection:                                                 │ │
│   │   Server encrypts session state with ticket_key                    │ │
│   │   Sends encrypted "ticket" to client                               │ │
│   │   Client stores ticket locally                                      │ │
│   │                                                                     │ │
│   │   Subsequent connection:                                            │ │
│   │   Client sends ticket in ClientHello                               │ │
│   │   Server decrypts ticket with ticket_key                           │ │
│   │   Restores session state: abbreviated handshake                    │ │
│   │                                                                     │ │
│   │   ADVANTAGE: No server-side storage needed                          │ │
│   │   CAUTION: Ticket key must be same across all servers/workers      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TLS 1.3: 0-RTT (Zero Round Trip Time)                                   │
│   ──────────────────────────────────────                                   │
│                                                                            │
│   ssl_early_data on;                                                      │
│                                                                            │
│   Client can send data in FIRST packet (before handshake completes)!     │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────┐       │
│   │                                                              │       │
│   │   Client                                Server               │       │
│   │      │                                     │                 │       │
│   │      │─── ClientHello + early_data ───────►│  Data sent     │       │
│   │      │    (encrypted with PSK)             │  immediately!  │       │
│   │      │                                     │                 │       │
│   │                                                              │       │
│   │   WARNING: 0-RTT is vulnerable to replay attacks!            │       │
│   │   Only safe for idempotent requests (GET).                   │       │
│   │                                                              │       │
│   │   Protect with:                                               │       │
│   │   if ($ssl_early_data) {                                     │       │
│   │       return 425;  # Too Early                                │       │
│   │   }                                                           │       │
│   │                                                              │       │
│   └──────────────────────────────────────────────────────────────┘       │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### OCSP Stapling

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    OCSP STAPLING                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   OCSP = Online Certificate Status Protocol                               │
│   Allows clients to verify certificate hasn't been revoked.               │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WITHOUT OCSP STAPLING:                                           │ │
│   │   ────────────────────────                                          │ │
│   │                                                                     │ │
│   │   Client                nginx                 CA/OCSP               │ │
│   │      │                    │                     │                   │ │
│   │      │◄── Certificate ────│                     │                   │ │
│   │      │                    │                     │                   │ │
│   │      │───────────────── OCSP Request ──────────►│ Client queries   │ │
│   │      │◄──────────────── OCSP Response ──────────│ CA directly      │ │
│   │      │                    │                     │                   │ │
│   │                                                                     │ │
│   │   PROBLEMS:                                                         │ │
│   │   • Extra latency (client waits for OCSP response)                 │ │
│   │   • Privacy leak (CA knows which sites client visits)              │ │
│   │   • If OCSP server down, client may accept revoked cert            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WITH OCSP STAPLING:                                              │ │
│   │   ─────────────────────                                             │ │
│   │                                                                     │ │
│   │   CA/OCSP              nginx                  Client               │ │
│   │      │                    │                     │                   │ │
│   │      │◄── OCSP Request ───│ (background)        │                   │ │
│   │      │─── OCSP Response ──►│                    │                   │ │
│   │      │                    │                     │                   │ │
│   │      │                    │── Certificate ─────►│ Server sends     │ │
│   │      │                    │── OCSP Response ───►│ OCSP "stapled"   │ │
│   │      │                    │   (stapled)         │ to certificate   │ │
│   │                                                                     │ │
│   │   BENEFITS:                                                         │ │
│   │   • Faster handshake (no extra round trip for client)              │ │
│   │   • Client privacy preserved                                        │ │
│   │   • Server caches OCSP response                                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│   ───────────────                                                          │
│                                                                            │
│   server {                                                                 │
│       ssl_stapling on;                                                    │
│       ssl_stapling_verify on;                                             │
│       ssl_trusted_certificate /etc/ssl/certs/ca-chain.crt;               │
│       resolver 8.8.8.8 8.8.4.4 valid=300s;  # For OCSP queries           │
│       resolver_timeout 5s;                                                │
│   }                                                                        │
│                                                                            │
│   HOW NGINX FETCHES OCSP:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   1. On first TLS handshake requiring OCSP                                │
│   2. nginx extracts OCSP responder URL from certificate                  │
│   3. Queries OCSP responder in background                                 │
│   4. Caches response (typically valid 1-7 days)                           │
│   5. Staples response to subsequent handshakes                            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### HTTP/2 and ALPN

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    HTTP/2 AND ALPN                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ALPN = Application-Layer Protocol Negotiation                           │
│   Allows client and server to agree on protocol during TLS handshake.    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Client                                Server                      │ │
│   │      │                                     │                        │ │
│   │      │─────── ClientHello ────────────────►│                        │ │
│   │      │        ALPN: [h2, http/1.1]         │  "I support h2 and    │ │
│   │      │                                     │   http/1.1"           │ │
│   │      │                                     │                        │ │
│   │      │◄────── ServerHello ─────────────────│                        │ │
│   │      │        ALPN: h2                     │  "Let's use h2"       │ │
│   │      │                                     │                        │ │
│   │      │═══════ HTTP/2 frames ══════════════►│                        │ │
│   │                                                                     │ │
│   │   Protocol negotiated INSIDE TLS handshake = no extra round trip   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│   ───────────────                                                          │
│                                                                            │
│   server {                                                                 │
│       listen 443 ssl http2;   # Enable HTTP/2                             │
│       # listen 443 ssl http2 http3;  # Also enable HTTP/3/QUIC           │
│   }                                                                        │
│                                                                            │
│   HTTP/2 FEATURES nginx supports:                                         │
│   ─────────────────────────────────                                        │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   MULTIPLEXING: Multiple requests over single TCP connection        │ │
│   │   ─────────────────────────────────────────────────────────          │ │
│   │                                                                     │ │
│   │   HTTP/1.1 (6 connections):          HTTP/2 (1 connection):        │ │
│   │   ┌─────────┐ Request 1              ┌─────────────────────────┐   │ │
│   │   ├─────────┤ Request 2              │ Stream 1 ────────────── │   │ │
│   │   ├─────────┤ Request 3              │ Stream 2 ──────────     │   │ │
│   │   ├─────────┤ Request 4              │ Stream 3 ────           │   │ │
│   │   ├─────────┤ Request 5              │ Stream 4 ────────────   │   │ │
│   │   └─────────┘ Request 6              └─────────────────────────┘   │ │
│   │                                                                     │ │
│   │   HEADER COMPRESSION (HPACK):                                       │ │
│   │   ───────────────────────────                                        │ │
│   │   • Static table: common headers pre-defined                        │ │
│   │   • Dynamic table: headers seen before are indexed                  │ │
│   │   • Huffman encoding for values                                     │ │
│   │                                                                     │ │
│   │   http2_max_header_size 16k;                                        │ │
│   │   http2_max_field_size 4k;                                          │ │
│   │                                                                     │ │
│   │   SERVER PUSH (deprecated in most browsers):                        │ │
│   │   ────────────────────────────────────────────                       │ │
│   │   http2_push /style.css;    # Push with response                   │ │
│   │   http2_push /script.js;                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HTTP/2 STREAM HANDLING:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   http2_max_concurrent_streams 128;  # Streams per connection      │ │
│   │   http2_recv_buffer_size 256k;       # Per-connection buffer       │ │
│   │   http2_idle_timeout 3m;             # Close idle connections      │ │
│   │                                                                     │ │
│   │   Connection                                                        │ │
│   │   ┌─────────────────────────────────────────────────────────────┐  │ │
│   │   │                                                             │  │ │
│   │   │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐             │  │ │
│   │   │   │Stream 1│ │Stream 3│ │Stream 5│ │Stream 7│ ...        │  │ │
│   │   │   │GET /a  │ │GET /b  │ │POST /c │ │GET /d  │             │  │ │
│   │   │   └────────┘ └────────┘ └────────┘ └────────┘             │  │ │
│   │   │                                                             │  │ │
│   │   │   Each stream = independent request/response                │  │ │
│   │   │   Odd stream IDs = client-initiated                        │  │ │
│   │   │   Even stream IDs = server-initiated (push)                │  │ │
│   │   │                                                             │  │ │
│   │   └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Performance Optimization

### sendfile() and Zero-Copy

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SENDFILE() AND ZERO-COPY                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   sendfile() is one of nginx's most important optimizations.             │
│   It sends files directly from disk to socket without user-space copy.   │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TRADITIONAL FILE SENDING (without sendfile):                     │ │
│   │   ─────────────────────────────────────────────                     │ │
│   │                                                                     │ │
│   │   ┌──────────┐       ┌──────────┐       ┌──────────┐              │ │
│   │   │   Disk   │       │  Kernel  │       │   User   │              │ │
│   │   │          │       │  Buffer  │       │  Buffer  │              │ │
│   │   └────┬─────┘       └────┬─────┘       └────┬─────┘              │ │
│   │        │                  │                  │                     │ │
│   │        │──── read() ─────►│                  │                     │ │
│   │        │    (DMA copy)    │                  │                     │ │
│   │        │                  │─── copy ────────►│  CPU copy!         │ │
│   │        │                  │  (CPU copy)      │                     │ │
│   │        │                  │                  │                     │ │
│   │        │                  │◄── write() ─────│                     │ │
│   │        │                  │   (CPU copy)     │  CPU copy!         │ │
│   │        │                  │                  │                     │ │
│   │        │                  │── send to ──────►│  Socket            │ │
│   │        │                  │   socket         │                     │ │
│   │                                                                     │ │
│   │   TOTAL: 4 copies, 2 context switches                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   WITH sendfile():                                                  │ │
│   │   ─────────────────                                                  │ │
│   │                                                                     │ │
│   │   ┌──────────┐       ┌──────────┐       ┌──────────┐              │ │
│   │   │   Disk   │       │  Kernel  │       │  Socket  │              │ │
│   │   │          │       │  Buffer  │       │  Buffer  │              │ │
│   │   └────┬─────┘       └────┬─────┘       └────┬─────┘              │ │
│   │        │                  │                  │                     │ │
│   │        │─── sendfile() ──►│──────────────────►                    │ │
│   │        │    (DMA copy)    │  (DMA gather)    │                     │ │
│   │        │                  │                  │                     │ │
│   │        │                  │                  │── to network       │ │
│   │                                                                     │ │
│   │   TOTAL: 2 copies, NO user-space involvement                       │ │
│   │                                                                     │ │
│   │   User-space (nginx) never touches the file data!                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONFIGURATION:                                                           │
│   ───────────────                                                          │
│                                                                            │
│   sendfile on;           # Enable sendfile                                │
│   sendfile_max_chunk 1m; # Limit per sendfile call (prevents monopoly)  │
│                                                                            │
│   WHEN SENDFILE IS USED:                                                  │
│   ───────────────────────                                                  │
│   ✓ Static files                                                          │
│   ✓ Cached proxy responses (from disk)                                   │
│   ✗ Dynamic content (generated in memory)                                │
│   ✗ Content with body filters (gzip, sub_filter)                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### TCP_CORK and TCP_NODELAY

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TCP_CORK AND TCP_NODELAY                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Two socket options that control how TCP buffers and sends data.        │
│                                                                            │
│   THE PROBLEM: Small writes vs. network efficiency                        │
│   ────────────────────────────────────────────────                         │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   HTTP response = headers + body                                    │ │
│   │                                                                     │ │
│   │   write(fd, headers, 200);   // Small write                        │ │
│   │   sendfile(fd, body, 4096);  // Larger data                        │ │
│   │                                                                     │ │
│   │   WITHOUT optimization:                                             │ │
│   │   ┌──────────┐  ┌──────────────────────────────────┐               │ │
│   │   │  Packet  │  │           Packet                 │               │ │
│   │   │  200B    │  │           4096B                  │               │ │
│   │   │ headers  │  │           body                   │               │ │
│   │   └──────────┘  └──────────────────────────────────┘               │ │
│   │        ↑                                                            │ │
│   │   Tiny packet! Wastes bandwidth.                                   │ │
│   │                                                                     │ │
│   │   WITH optimization:                                                │ │
│   │   ┌────────────────────────────────────────────────┐               │ │
│   │   │              Single Packet                     │               │ │
│   │   │  headers (200B) + body start (1260B)          │               │ │
│   │   └────────────────────────────────────────────────┘               │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TCP_NODELAY (disable Nagle's algorithm):                                │
│   ─────────────────────────────────────────                                │
│                                                                            │
│   tcp_nodelay on;   # Default: on                                         │
│                                                                            │
│   Nagle's algorithm: collect small writes, send when ACK received        │
│   TCP_NODELAY: send immediately, don't wait for ACK                      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Nagle ON:                    TCP_NODELAY (Nagle OFF):            │ │
│   │   ─────────                    ─────────────────────────            │ │
│   │                                                                     │ │
│   │   write(200B) ─┐               write(200B) ─────► send immediately │ │
│   │   write(100B) ─┤ wait...       write(100B) ─────► send immediately │ │
│   │   write(50B) ──┤               write(50B) ──────► send immediately │ │
│   │        ...ACK received...                                           │ │
│   │   send all ────► packet                                             │ │
│   │                                                                     │ │
│   │   Good for: bulk transfers     Good for: interactive, low-latency  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TCP_CORK (Linux) / TCP_NOPUSH (BSD):                                   │
│   ────────────────────────────────────                                     │
│                                                                            │
│   tcp_nopush on;   # Use with sendfile                                   │
│                                                                            │
│   "Cork" the socket: don't send until uncorked or buffer full           │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Algorithm nginx uses:                                             │ │
│   │                                                                     │ │
│   │   1. setsockopt(TCP_CORK, 1)     // Cork: start buffering          │ │
│   │   2. write(headers)              // Goes to buffer                  │ │
│   │   3. sendfile(body)              // Goes to buffer                  │ │
│   │   4. setsockopt(TCP_CORK, 0)     // Uncork: flush all together     │ │
│   │                                                                     │ │
│   │   Result: Headers and body sent in optimal-sized packets           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BEST PRACTICE:                                                          │
│   ───────────────                                                          │
│                                                                            │
│   sendfile on;                                                            │
│   tcp_nopush on;     # Buffer until ready (for sendfile)                 │
│   tcp_nodelay on;    # After data is ready, send immediately            │
│                                                                            │
│   These work TOGETHER:                                                    │
│   • tcp_nopush: Buffer writes to build full packets                      │
│   • tcp_nodelay: Once packet ready, send immediately                     │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Worker Tuning

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WORKER TUNING                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Key parameters for optimizing nginx worker processes:                   │
│                                                                            │
│   worker_processes auto;        # Usually = number of CPU cores          │
│   worker_cpu_affinity auto;     # Pin workers to specific CPUs           │
│   worker_rlimit_nofile 65535;   # Max open files per worker              │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   CPU AFFINITY:                                                     │ │
│   │   ─────────────                                                      │ │
│   │                                                                     │ │
│   │   Without affinity:          With affinity:                         │ │
│   │   ┌──────────────────┐       ┌──────────────────┐                  │ │
│   │   │ Worker 1 ─► CPU 0│       │ Worker 1 ─► CPU 0│ (pinned)        │ │
│   │   │         ─► CPU 1│       │                  │                  │ │
│   │   │         ─► CPU 2│       │ Worker 2 ─► CPU 1│ (pinned)        │ │
│   │   │ Worker 2 ─► CPU 0│       │                  │                  │ │
│   │   │         ─► CPU 3│       │ Worker 3 ─► CPU 2│ (pinned)        │ │
│   │   └──────────────────┘       └──────────────────┘                  │ │
│   │                                                                     │ │
│   │   Benefits of affinity:                                             │ │
│   │   • Better CPU cache utilization (L1/L2 stay warm)                 │ │
│   │   • No cache thrashing from process migration                      │ │
│   │   • Predictable performance                                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CONNECTIONS:                                                             │
│   ────────────                                                             │
│                                                                            │
│   events {                                                                 │
│       worker_connections 10000;  # Max connections per worker            │
│       use epoll;                 # Linux: epoll, BSD: kqueue             │
│       multi_accept on;           # Accept multiple connections at once   │
│   }                                                                        │
│                                                                            │
│   Total max connections = worker_processes × worker_connections          │
│                         = 4 workers × 10000 = 40,000 connections         │
│                                                                            │
│   FILE DESCRIPTOR LIMITS:                                                 │
│   ───────────────────────                                                  │
│                                                                            │
│   Each connection needs file descriptors:                                 │
│   • 1 fd for client connection                                            │
│   • 1 fd for upstream connection (if proxying)                           │
│   • 1 fd for static file (if serving files)                              │
│                                                                            │
│   worker_rlimit_nofile should be >= 2 × worker_connections               │
│                                                                            │
│   Also set system limits:                                                 │
│   $ ulimit -n 65535                                                       │
│   /etc/security/limits.conf:                                              │
│       nginx soft nofile 65535                                             │
│       nginx hard nofile 65535                                             │
│                                                                            │
│   PRIORITY:                                                                │
│   ─────────                                                                │
│                                                                            │
│   worker_priority -5;   # Nice value (-20 to 19, lower = higher priority)│
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Practical Configuration

### Common Patterns

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    COMMON CONFIGURATION PATTERNS                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PATTERN 1: Basic Reverse Proxy                                          │
│   ──────────────────────────────                                           │
│                                                                            │
│   upstream backend {                                                       │
│       server 10.0.0.1:8080 weight=5;                                      │
│       server 10.0.0.2:8080 weight=5;                                      │
│       server 10.0.0.3:8080 backup;    # Only used if others down         │
│       keepalive 32;                    # Connection pool size             │
│   }                                                                        │
│                                                                            │
│   server {                                                                 │
│       listen 80;                                                          │
│       server_name example.com;                                            │
│                                                                            │
│       location / {                                                        │
│           proxy_pass http://backend;                                      │
│           proxy_http_version 1.1;                                         │
│           proxy_set_header Connection "";                                 │
│           proxy_set_header Host $host;                                   │
│           proxy_set_header X-Real-IP $remote_addr;                       │
│           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   PATTERN 2: Static Files with Cache                                      │
│   ─────────────────────────────────                                        │
│                                                                            │
│   server {                                                                 │
│       listen 80;                                                          │
│       root /var/www/html;                                                 │
│                                                                            │
│       location / {                                                        │
│           try_files $uri $uri/ =404;                                     │
│       }                                                                    │
│                                                                            │
│       location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {                     │
│           expires 30d;                                                    │
│           add_header Cache-Control "public, immutable";                  │
│           access_log off;                                                 │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   PATTERN 3: HTTPS with Modern TLS                                        │
│   ────────────────────────────────                                         │
│                                                                            │
│   server {                                                                 │
│       listen 443 ssl http2;                                               │
│       server_name example.com;                                            │
│                                                                            │
│       ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;  │
│       ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;│
│                                                                            │
│       ssl_protocols TLSv1.2 TLSv1.3;                                      │
│       ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;│
│       ssl_prefer_server_ciphers off;                                      │
│                                                                            │
│       ssl_session_cache shared:SSL:10m;                                   │
│       ssl_session_timeout 1d;                                             │
│       ssl_stapling on;                                                    │
│       ssl_stapling_verify on;                                             │
│                                                                            │
│       # HSTS                                                               │
│       add_header Strict-Transport-Security "max-age=31536000" always;    │
│   }                                                                        │
│                                                                            │
│   # Redirect HTTP to HTTPS                                                │
│   server {                                                                 │
│       listen 80;                                                          │
│       server_name example.com;                                            │
│       return 301 https://$server_name$request_uri;                       │
│   }                                                                        │
│                                                                            │
│   PATTERN 4: Rate Limiting                                                │
│   ────────────────────────                                                 │
│                                                                            │
│   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;            │
│   limit_conn_zone $binary_remote_addr zone=conn:10m;                     │
│                                                                            │
│   server {                                                                 │
│       location /api/ {                                                    │
│           limit_req zone=api burst=20 nodelay;                           │
│           limit_conn conn 10;  # Max 10 connections per IP              │
│           proxy_pass http://backend;                                      │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
│   PATTERN 5: WebSocket Proxy                                              │
│   ──────────────────────────                                               │
│                                                                            │
│   map $http_upgrade $connection_upgrade {                                 │
│       default upgrade;                                                    │
│       ''      close;                                                      │
│   }                                                                        │
│                                                                            │
│   server {                                                                 │
│       location /ws/ {                                                     │
│           proxy_pass http://websocket_backend;                           │
│           proxy_http_version 1.1;                                         │
│           proxy_set_header Upgrade $http_upgrade;                        │
│           proxy_set_header Connection $connection_upgrade;               │
│           proxy_read_timeout 86400;  # Keep connection open             │
│       }                                                                    │
│   }                                                                        │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Performance Tuning Checklist

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE TUNING CHECKLIST                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   [ ] WORKERS                                                              │
│   ─────────────                                                            │
│   worker_processes auto;          # = number of CPU cores                 │
│   worker_cpu_affinity auto;       # Pin workers to CPUs                   │
│   worker_rlimit_nofile 65535;     # High file descriptor limit           │
│                                                                            │
│   [ ] EVENTS                                                               │
│   ──────────                                                               │
│   events {                                                                 │
│       use epoll;                  # Linux (kqueue for BSD)               │
│       worker_connections 10000;   # Connections per worker               │
│       multi_accept on;            # Accept multiple at once              │
│   }                                                                        │
│                                                                            │
│   [ ] TCP/NETWORK                                                          │
│   ───────────────                                                          │
│   sendfile on;                    # Zero-copy file serving               │
│   tcp_nopush on;                  # Optimize packet building             │
│   tcp_nodelay on;                 # Reduce latency                        │
│                                                                            │
│   [ ] BUFFERS                                                              │
│   ───────────                                                              │
│   client_body_buffer_size 16k;    # POST body buffer                     │
│   client_header_buffer_size 1k;   # Header buffer                        │
│   large_client_header_buffers 4 8k;                                      │
│   output_buffers 2 32k;           # Response output buffers              │
│                                                                            │
│   [ ] TIMEOUTS                                                             │
│   ────────────                                                             │
│   client_body_timeout 12;         # Reading client body                   │
│   client_header_timeout 12;       # Reading client headers               │
│   send_timeout 10;                # Sending response                      │
│   keepalive_timeout 65;           # Keep-alive connection timeout        │
│                                                                            │
│   [ ] COMPRESSION                                                          │
│   ───────────────                                                          │
│   gzip on;                                                                │
│   gzip_comp_level 5;              # 1-9, 5 is good balance               │
│   gzip_min_length 256;            # Don't compress tiny files            │
│   gzip_types text/plain text/css application/json application/javascript;│
│   gzip_vary on;                   # Vary header for caches               │
│                                                                            │
│   [ ] CACHING (for proxy)                                                 │
│   ───────────────────────                                                  │
│   proxy_cache_path /var/cache/nginx levels=1:2                           │
│       keys_zone=cache:10m max_size=10g inactive=60m;                     │
│   proxy_cache_valid 200 302 10m;                                         │
│   proxy_cache_valid 404 1m;                                               │
│   proxy_cache_lock on;            # Prevent thundering herd              │
│                                                                            │
│   [ ] UPSTREAM                                                             │
│   ────────────                                                             │
│   upstream backend {                                                       │
│       keepalive 32;               # Connection pool                       │
│       keepalive_requests 1000;    # Requests per connection              │
│   }                                                                        │
│   proxy_http_version 1.1;         # Required for keepalive               │
│   proxy_set_header Connection ""; # Clear Connection header              │
│                                                                            │
│   [ ] LOGGING                                                              │
│   ───────────                                                              │
│   access_log off;                 # Disable for static assets            │
│   # OR                                                                    │
│   access_log /var/log/nginx/access.log main buffer=32k flush=5s;        │
│   error_log /var/log/nginx/error.log warn;                               │
│                                                                            │
│   [ ] OS TUNING (Linux)                                                   │
│   ─────────────────────                                                    │
│   # /etc/sysctl.conf                                                      │
│   net.core.somaxconn = 65535                                              │
│   net.ipv4.tcp_max_syn_backlog = 65535                                   │
│   net.core.netdev_max_backlog = 65535                                    │
│   net.ipv4.tcp_fin_timeout = 15                                          │
│   net.ipv4.tcp_tw_reuse = 1                                               │
│   net.ipv4.ip_local_port_range = 1024 65535                              │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Summary and Appendix

### Architecture Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE QUICK REFERENCE                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROCESS MODEL:                                                           │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │   Master Process (1)                                               │  │
│   │   • Read config, bind ports                                        │  │
│   │   • Fork workers, manage lifecycle                                 │  │
│   │   • Handle signals (SIGHUP, SIGUSR1, SIGUSR2)                     │  │
│   │                    │                                               │  │
│   │   ┌────────────────┼────────────────┐                             │  │
│   │   ▼                ▼                ▼                             │  │
│   │   Worker 1      Worker 2      Worker N                            │  │
│   │   • Handle connections          • Single-threaded                 │  │
│   │   • Event loop (epoll/kqueue)   • Non-blocking I/O               │  │
│   │   • Process requests            • Independent (no locks)          │  │
│   │                                                                    │  │
│   │   Cache Manager    Cache Loader    (optional helper processes)    │  │
│   │                                                                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   EVENT-DRIVEN MODEL:                                                      │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │                                                                    │  │
│   │   while (true) {                                                   │  │
│   │       events = epoll_wait(...)  // Sleep until events             │  │
│   │       for (event in events) {                                      │  │
│   │           if (event.readable) process_read(event.fd);             │  │
│   │           if (event.writable) process_write(event.fd);            │  │
│   │       }                                                            │  │
│   │       process_timers();                                            │  │
│   │   }                                                                │  │
│   │                                                                    │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   KEY DATA STRUCTURES:                                                     │
│   ─────────────────────                                                    │
│   • ngx_connection_t   - Connection state, buffers, callbacks            │
│   • ngx_http_request_t - HTTP request: headers, body, response           │
│   • ngx_pool_t         - Memory pool for request lifetime                │
│   • ngx_buf_t          - Buffer (memory or file reference)               │
│   • ngx_chain_t        - Linked list of buffers                          │
│   • ngx_event_t        - Event descriptor for epoll                      │
│                                                                            │
│   REQUEST LIFECYCLE:                                                       │
│   ───────────────────                                                      │
│   1. Accept connection                                                    │
│   2. Read request headers                                                 │
│   3. Parse request line and headers                                       │
│   4. Find matching location                                               │
│   5. Run 11 request phases                                                │
│   6. Generate response (handler)                                          │
│   7. Filter response (header filters → body filters)                     │
│   8. Send response                                                        │
│   9. Log request                                                          │
│   10. Keep-alive or close                                                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Directive Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    DIRECTIVE QUICK REFERENCE                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   CORE DIRECTIVES:                                                         │
│   ─────────────────                                                        │
│   ┌─────────────────────────┬──────────────────────────────────────────┐  │
│   │ Directive               │ Description                              │  │
│   ├─────────────────────────┼──────────────────────────────────────────┤  │
│   │ worker_processes        │ Number of worker processes               │  │
│   │ worker_connections      │ Max connections per worker               │  │
│   │ use epoll               │ Event mechanism (epoll/kqueue)           │  │
│   │ multi_accept            │ Accept multiple connections at once      │  │
│   │ accept_mutex            │ Serialize accept() calls                 │  │
│   └─────────────────────────┴──────────────────────────────────────────┘  │
│                                                                            │
│   HTTP DIRECTIVES:                                                         │
│   ─────────────────                                                        │
│   ┌─────────────────────────┬──────────────────────────────────────────┐  │
│   │ Directive               │ Description                              │  │
│   ├─────────────────────────┼──────────────────────────────────────────┤  │
│   │ server                  │ Virtual server block                     │  │
│   │ listen                  │ IP:port to listen on                     │  │
│   │ server_name             │ Virtual host matching                    │  │
│   │ location                │ URI matching block                       │  │
│   │ root                    │ Document root                            │  │
│   │ index                   │ Default file                             │  │
│   │ try_files               │ Try files in order                       │  │
│   └─────────────────────────┴──────────────────────────────────────────┘  │
│                                                                            │
│   PROXY DIRECTIVES:                                                        │
│   ──────────────────                                                       │
│   ┌─────────────────────────┬──────────────────────────────────────────┐  │
│   │ Directive               │ Description                              │  │
│   ├─────────────────────────┼──────────────────────────────────────────┤  │
│   │ proxy_pass              │ Backend server URL                       │  │
│   │ proxy_set_header        │ Set header to backend                    │  │
│   │ proxy_http_version      │ HTTP version for upstream (1.1 for KA)  │  │
│   │ proxy_connect_timeout   │ Timeout for connecting to upstream      │  │
│   │ proxy_read_timeout      │ Timeout for reading from upstream       │  │
│   │ proxy_buffering         │ Buffer upstream responses                │  │
│   │ proxy_cache             │ Enable caching                           │  │
│   │ upstream                │ Define backend server group              │  │
│   │ keepalive               │ Upstream connection pool size            │  │
│   └─────────────────────────┴──────────────────────────────────────────┘  │
│                                                                            │
│   SSL DIRECTIVES:                                                          │
│   ────────────────                                                         │
│   ┌─────────────────────────┬──────────────────────────────────────────┐  │
│   │ Directive               │ Description                              │  │
│   ├─────────────────────────┼──────────────────────────────────────────┤  │
│   │ ssl_certificate         │ Path to certificate                      │  │
│   │ ssl_certificate_key     │ Path to private key                      │  │
│   │ ssl_protocols           │ Allowed TLS versions                     │  │
│   │ ssl_ciphers             │ Allowed cipher suites                    │  │
│   │ ssl_session_cache       │ Session cache config                     │  │
│   │ ssl_session_timeout     │ Session lifetime                         │  │
│   │ ssl_stapling            │ Enable OCSP stapling                     │  │
│   └─────────────────────────┴──────────────────────────────────────────┘  │
│                                                                            │
│   PERFORMANCE DIRECTIVES:                                                  │
│   ────────────────────────                                                 │
│   ┌─────────────────────────┬──────────────────────────────────────────┐  │
│   │ Directive               │ Description                              │  │
│   ├─────────────────────────┼──────────────────────────────────────────┤  │
│   │ sendfile                │ Zero-copy file serving                   │  │
│   │ tcp_nopush              │ TCP_CORK optimization                    │  │
│   │ tcp_nodelay             │ Disable Nagle's algorithm                │  │
│   │ gzip                    │ Enable compression                       │  │
│   │ open_file_cache         │ Cache file metadata                      │  │
│   │ keepalive_timeout       │ Keep-alive connection timeout            │  │
│   │ keepalive_requests      │ Max requests per keep-alive              │  │
│   └─────────────────────────┴──────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              NGINX ARCHITECTURE: THE BIG PICTURE                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              MASTER PROCESS                                      │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │   │
│   │  │ Config      │  │ Signal      │  │ Process     │  │ Privilege Operations   │ │   │
│   │  │ Parser      │  │ Handler     │  │ Manager     │  │ (bind ports, chroot)   │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────┘ │   │
│   └───────────────────────────────┬─────────────────────────────────────────────────┘   │
│                                   │ fork()                                               │
│           ┌───────────────────────┼───────────────────────┐                             │
│           │                       │                       │                             │
│           ▼                       ▼                       ▼                             │
│   ┌───────────────┐       ┌───────────────┐       ┌───────────────┐                     │
│   │   WORKER 1    │       │   WORKER 2    │       │   WORKER N    │                     │
│   │               │       │               │       │               │                     │
│   │ ┌───────────┐ │       │ ┌───────────┐ │       │ ┌───────────┐ │                     │
│   │ │Event Loop │ │       │ │Event Loop │ │       │ │Event Loop │ │                     │
│   │ │(epoll/    │ │       │ │(epoll/    │ │       │ │(epoll/    │ │                     │
│   │ │ kqueue)   │ │       │ │ kqueue)   │ │       │ │ kqueue)   │ │                     │
│   │ └─────┬─────┘ │       │ └─────┬─────┘ │       │ └─────┬─────┘ │                     │
│   │       │       │       │       │       │       │       │       │                     │
│   │ ┌─────▼─────┐ │       │ ┌─────▼─────┐ │       │ ┌─────▼─────┐ │                     │
│   │ │Connection │ │       │ │Connection │ │       │ │Connection │ │                     │
│   │ │  Pool     │ │       │ │  Pool     │ │       │ │  Pool     │ │                     │
│   │ └───────────┘ │       │ └───────────┘ │       │ └───────────┘ │                     │
│   │               │       │               │       │               │                     │
│   │ ┌───────────┐ │       │ ┌───────────┐ │       │ ┌───────────┐ │                     │
│   │ │Memory Pool│ │       │ │Memory Pool│ │       │ │Memory Pool│ │                     │
│   │ └───────────┘ │       │ └───────────┘ │       │ └───────────┘ │                     │
│   └───────────────┘       └───────────────┘       └───────────────┘                     │
│           │                       │                       │                             │
│           └───────────────────────┼───────────────────────┘                             │
│                                   │                                                      │
│                    ┌──────────────┴──────────────┐                                      │
│                    │      SHARED MEMORY          │                                      │
│                    │  ┌─────────┐  ┌─────────┐   │                                      │
│                    │  │SSL Sess │  │ Proxy   │   │                                      │
│                    │  │ Cache   │  │ Cache   │   │                                      │
│                    │  └─────────┘  └─────────┘   │                                      │
│                    │  ┌─────────┐  ┌─────────┐   │                                      │
│                    │  │Rate Lim │  │ Upstream│   │                                      │
│                    │  │ Zones   │  │ Health  │   │                                      │
│                    │  └─────────┘  └─────────┘   │                                      │
│                    └─────────────────────────────┘                                      │
│                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                              REQUEST PROCESSING FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   CLIENT                           NGINX WORKER                           UPSTREAM      │
│   ──────                           ────────────                           ────────      │
│                                                                                          │
│      │                                  │                                    │          │
│      │  TCP SYN ──────────────────────► │                                    │          │
│      │  ◄─────────────────── TCP SYN+ACK│                                    │          │
│      │  TCP ACK ──────────────────────► │                                    │          │
│      │                                  │                                    │          │
│      │  SSL ClientHello ──────────────► │                                    │          │
│      │  ◄──────────────── ServerHello   │                                    │          │
│      │  ◄──────────────── Certificate   │                                    │          │
│      │  Key Exchange ─────────────────► │                                    │          │
│      │  ◄──────────────── Finished      │                                    │          │
│      │                                  │                                    │          │
│      │  HTTP Request ─────────────────► │                                    │          │
│      │  "GET /api/users HTTP/1.1"       │                                    │          │
│      │                                  │                                    │          │
│      │                    ┌─────────────┴─────────────┐                      │          │
│      │                    │   REQUEST PROCESSING      │                      │          │
│      │                    │   1. Parse headers        │                      │          │
│      │                    │   2. Find location        │                      │          │
│      │                    │   3. Check cache ────────►│ CACHE HIT? ──► Skip  │          │
│      │                    │   4. Rewrite phase        │                      │          │
│      │                    │   5. Access check         │                      │          │
│      │                    │   6. Auth check           │                      │          │
│      │                    │   7. Rate limit check     │                      │          │
│      │                    └─────────────┬─────────────┘                      │          │
│      │                                  │                                    │          │
│      │                                  │  HTTP Request ───────────────────► │          │
│      │                                  │                                    │          │
│      │                                  │  ◄─────────────── HTTP Response    │          │
│      │                                  │                                    │          │
│      │                    ┌─────────────┴─────────────┐                      │          │
│      │                    │   RESPONSE PROCESSING     │                      │          │
│      │                    │   1. Header filters       │                      │          │
│      │                    │   2. Body filters         │                      │          │
│      │                    │   3. gzip (if enabled)    │                      │          │
│      │                    │   4. Chunked encoding     │                      │          │
│      │                    │   5. Cache storage        │                      │          │
│      │                    └─────────────┬─────────────┘                      │          │
│      │                                  │                                    │          │
│      │  ◄─────────── HTTP Response      │                                    │          │
│      │  "HTTP/1.1 200 OK"               │                                    │          │
│      │  ◄─────────── Response Body      │                                    │          │
│      │                                  │                                    │          │
│      │  (Keep-Alive: wait for          │                                    │          │
│      │   next request or timeout)       │                                    │          │
│      │                                  │                                    │          │
│                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                              KEY PERFORMANCE FEATURES                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                     │
│   │  Event-Driven   │    │   Zero-Copy     │    │  Memory Pools   │                     │
│   │                 │    │                 │    │                 │                     │
│   │  • Non-blocking │    │  • sendfile()   │    │  • Fast alloc   │                     │
│   │  • epoll/kqueue │    │  • No user-     │    │  • Bulk free    │                     │
│   │  • O(1) events  │    │    kernel copy  │    │  • No fragm.    │                     │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘                     │
│                                                                                          │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                     │
│   │  Connection     │    │    Response     │    │   Upstream      │                     │
│   │  Pooling        │    │    Caching      │    │   Keepalive     │                     │
│   │                 │    │                 │    │                 │                     │
│   │  • Reuse conn   │    │  • Avoid origin │    │  • Reuse to     │                     │
│   │  • Pre-alloc    │    │  • Fast local   │    │    backend      │                     │
│   │  • Quick accept │    │  • Cache lock   │    │  • Pool conns   │                     │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘                     │
│                                                                                          │
│   RESULT: 10,000+ concurrent connections per worker with minimal CPU usage              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. References

### Books

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              RECOMMENDED BOOKS                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   NGINX SPECIFIC:                                                          │
│   ───────────────                                                          │
│   • "NGINX Cookbook" - Derek DeJonghe                                     │
│     Practical recipes for high-performance load balancing                  │
│                                                                            │
│   • "Mastering NGINX" - Dimitri Aivaliotis                                │
│     Comprehensive guide to nginx configuration                             │
│                                                                            │
│   • "NGINX HTTP Server" - Clément Nedelcu                                 │
│     Covers installation, configuration, and optimization                   │
│                                                                            │
│   UNIX/LINUX SYSTEMS:                                                      │
│   ───────────────────                                                      │
│   • "The Design of the UNIX Operating System" - Maurice J. Bach          │
│     Classic text on Unix kernel internals and algorithms                   │
│                                                                            │
│   • "Advanced Programming in the UNIX Environment" - W. Richard Stevens  │
│     Definitive guide to Unix system programming                            │
│                                                                            │
│   • "UNIX Network Programming" - W. Richard Stevens                       │
│     Volume 1: Sockets and XTI - Essential for network programming         │
│                                                                            │
│   • "Linux System Programming" - Robert Love                              │
│     Modern Linux systems programming techniques                            │
│                                                                            │
│   • "The Linux Programming Interface" - Michael Kerrisk                   │
│     Comprehensive Linux/Unix system programming reference                  │
│                                                                            │
│   PERFORMANCE AND ARCHITECTURE:                                            │
│   ─────────────────────────────                                            │
│   • "Systems Performance" - Brendan Gregg                                 │
│     Enterprise and cloud performance analysis                              │
│                                                                            │
│   • "High Performance Browser Networking" - Ilya Grigorik                 │
│     Deep dive into TCP, TLS, HTTP/2 optimization                          │
│                                                                            │
│   • "Web Scalability for Startup Engineers" - Artur Ejsmont               │
│     Scalability patterns including reverse proxies                         │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Source Code Files

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           NGINX SOURCE CODE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Repository: https://github.com/nginx/nginx                              │
│                                                                            │
│   CORE FILES:                                                              │
│   ───────────                                                              │
│   src/core/nginx.c              Main entry point, master process          │
│   src/core/ngx_cycle.c          Configuration cycle, process lifecycle   │
│   src/core/ngx_connection.c     Connection handling                       │
│   src/core/ngx_palloc.c         Memory pool allocator                     │
│   src/core/ngx_buf.c            Buffer management                         │
│   src/core/ngx_slab.c           Shared memory slab allocator             │
│                                                                            │
│   EVENT SYSTEM:                                                            │
│   ─────────────                                                            │
│   src/event/ngx_event.c         Event loop core                           │
│   src/event/ngx_event_accept.c  Connection accept handling               │
│   src/event/ngx_event_connect.c Outgoing connection handling             │
│   src/event/modules/ngx_epoll_module.c    Linux epoll                    │
│   src/event/modules/ngx_kqueue_module.c   BSD/macOS kqueue              │
│                                                                            │
│   HTTP MODULE:                                                             │
│   ────────────                                                             │
│   src/http/ngx_http.c           HTTP module initialization               │
│   src/http/ngx_http_request.c   Request parsing                          │
│   src/http/ngx_http_core_module.c   Core HTTP directives                │
│   src/http/ngx_http_upstream.c  Upstream/proxy handling                  │
│   src/http/ngx_http_variables.c Variable system                          │
│   src/http/ngx_http_script.c    Rewrite engine                           │
│                                                                            │
│   FILTER CHAIN:                                                            │
│   ─────────────                                                            │
│   src/http/ngx_http_header_filter_module.c   Header filtering           │
│   src/http/ngx_http_write_filter_module.c    Output writing             │
│   src/http/ngx_http_chunked_filter_module.c  Chunked encoding           │
│   src/http/modules/ngx_http_gzip_filter_module.c   Compression          │
│                                                                            │
│   PROXY AND CACHE:                                                         │
│   ────────────────                                                         │
│   src/http/modules/ngx_http_proxy_module.c    HTTP proxy                │
│   src/http/ngx_http_upstream_round_robin.c    Load balancing            │
│   src/http/ngx_http_file_cache.c              Caching system            │
│                                                                            │
│   SSL/TLS:                                                                 │
│   ────────                                                                 │
│   src/event/ngx_event_openssl.c               OpenSSL integration       │
│   src/http/modules/ngx_http_ssl_module.c      HTTPS handling            │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Online Resources

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           ONLINE RESOURCES                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   OFFICIAL DOCUMENTATION:                                                  │
│   ───────────────────────                                                  │
│   • https://nginx.org/en/docs/                                            │
│     Official nginx documentation                                           │
│                                                                            │
│   • https://docs.nginx.com/                                               │
│     NGINX Plus commercial documentation                                    │
│                                                                            │
│   • https://www.nginx.com/resources/wiki/                                 │
│     Community wiki with tutorials and examples                             │
│                                                                            │
│   ARCHITECTURE DEEP DIVES:                                                │
│   ────────────────────────                                                 │
│   • "The Architecture of Open Source Applications: nginx"                │
│     http://www.aosabook.org/en/nginx.html                                 │
│     By Andrew Alexeev (nginx core developer)                              │
│                                                                            │
│   • "Inside NGINX: How We Designed for Performance & Scale"              │
│     https://www.nginx.com/blog/inside-nginx-how-we-designed-for-         │
│     performance-scale/                                                     │
│                                                                            │
│   • "Thread Pools in NGINX Boost Performance 9x!"                        │
│     https://www.nginx.com/blog/thread-pools-boost-performance-9x/        │
│                                                                            │
│   PERFORMANCE TUNING:                                                      │
│   ───────────────────                                                      │
│   • "Tuning NGINX for Performance"                                        │
│     https://www.nginx.com/blog/tuning-nginx/                              │
│                                                                            │
│   • "NGINX Performance Tuning Guide"                                      │
│     https://www.nginx.com/blog/performance-tuning-tips-tricks/           │
│                                                                            │
│   C10K PROBLEM:                                                            │
│   ─────────────                                                            │
│   • "The C10K Problem" - Dan Kegel                                        │
│     http://www.kegel.com/c10k.html                                        │
│     Historical context for high-concurrency server design                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Relevant RFCs

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              RELEVANT RFCs                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   HTTP PROTOCOL:                                                           │
│   ──────────────                                                           │
│   RFC 9110  HTTP Semantics                                                │
│   RFC 9111  HTTP Caching                                                  │
│   RFC 9112  HTTP/1.1                                                      │
│   RFC 9113  HTTP/2                                                        │
│   RFC 9114  HTTP/3                                                        │
│                                                                            │
│   TLS/SSL:                                                                 │
│   ────────                                                                 │
│   RFC 8446  TLS 1.3                                                       │
│   RFC 6066  TLS Extensions (SNI, OCSP Stapling)                          │
│   RFC 5077  TLS Session Resumption                                        │
│                                                                            │
│   TCP/IP:                                                                  │
│   ───────                                                                  │
│   RFC 793   Transmission Control Protocol                                 │
│   RFC 1122  Requirements for Internet Hosts                               │
│   RFC 7323  TCP Extensions for High Performance                           │
│                                                                            │
│   WEBSOCKET:                                                               │
│   ──────────                                                               │
│   RFC 6455  The WebSocket Protocol                                        │
│                                                                            │
│   OTHER:                                                                   │
│   ──────                                                                   │
│   RFC 3875  CGI/1.1                                                       │
│   RFC 3986  URI Generic Syntax                                            │
│   RFC 7540  HTTP/2 (obsoleted by RFC 9113)                               │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

_Document created in the style of Maurice J. Bach's "The Design of the UNIX Operating System"_
_Emphasizing kernel algorithms, data structures, and visual explanations_

---

**END OF DOCUMENT**
