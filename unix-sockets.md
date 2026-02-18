# Unix Sockets: Network Programming and Inter-Process Communication

## A Deep Technical Exploration in the Tradition of Maurice Bach

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Scope:** Kernel Internals, Socket Data Structures, Protocol Implementation, and Network Programming

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [The Birth of Network Programming](#the-birth-of-network-programming)
   - [The Socket Abstraction](#the-socket-abstraction)
   - [Historical Context](#historical-context)
   - [Document Organization](#document-organization)

2. [Fundamental Concepts](#2-fundamental-concepts)
   - [What Is a Socket?](#what-is-a-socket)
   - [Socket Data Structures in the Kernel](#socket-data-structures-in-the-kernel)
   - [Address Families](#address-families)
   - [Socket Types](#socket-types)
   - [Protocols](#protocols)

3. [Socket System Calls](#3-socket-system-calls)
   - [socket() - Creating a Socket](#socket---creating-a-socket)
   - [bind() - Assigning an Address](#bind---assigning-an-address)
   - [listen() - Marking as Passive](#listen---marking-as-passive)
   - [accept() - Accepting Connections](#accept---accepting-connections)
   - [connect() - Initiating Connections](#connect---initiating-connections)
   - [send() and recv()](#send-and-recv)
   - [sendto() and recvfrom()](#sendto-and-recvfrom)
   - [shutdown() vs close()](#shutdown-vs-close)

4. [TCP Sockets](#4-tcp-sockets)
   - [The Three-Way Handshake](#the-three-way-handshake)
   - [TCP Connection States](#tcp-connection-states)
   - [The TIME_WAIT State](#the-time_wait-state)
   - [Graceful vs Abortive Close](#graceful-vs-abortive-close)
   - [TCP Buffers and Flow Control](#tcp-buffers-and-flow-control)
   - [Nagle's Algorithm](#nagles-algorithm)

5. [UDP Sockets](#5-udp-sockets)
   - [Connectionless Communication](#connectionless-communication)
   - [sendto() and recvfrom() in Detail](#sendto-and-recvfrom-in-detail)
   - [Connected UDP Sockets](#connected-udp-sockets)
   - [UDP vs TCP Trade-offs](#udp-vs-tcp-trade-offs)
   - [Multicast and Broadcast](#multicast-and-broadcast)

6. [Unix Domain Sockets](#6-unix-domain-sockets)
   - [AF_UNIX / AF_LOCAL](#af_unix--af_local)
   - [Stream vs Datagram](#stream-vs-datagram)
   - [Filesystem Paths and Abstract Namespace](#filesystem-paths-and-abstract-namespace)
   - [Passing File Descriptors (SCM_RIGHTS)](#passing-file-descriptors-scm_rights)
   - [Credentials Passing (SCM_CREDENTIALS)](#credentials-passing-scm_credentials)

7. [Socket Options](#7-socket-options)
   - [setsockopt() and getsockopt()](#setsockopt-and-getsockopt)
   - [SO_REUSEADDR and SO_REUSEPORT](#so_reuseaddr-and-so_reuseport)
   - [SO_KEEPALIVE](#so_keepalive)
   - [TCP_NODELAY](#tcp_nodelay)
   - [SO_LINGER](#so_linger)
   - [Buffer Sizes (SO_SNDBUF, SO_RCVBUF)](#buffer-sizes-so_sndbuf-so_rcvbuf)

8. [Socket Buffers and Kernel Internals](#8-socket-buffers-and-kernel-internals)
   - [The sk_buff Structure](#the-sk_buff-structure)
   - [Send and Receive Queues](#send-and-receive-queues)
   - [Buffer Management](#buffer-management)
   - [Backpressure and Flow Control](#backpressure-and-flow-control)
   - [Zero-Copy Techniques](#zero-copy-techniques)

9. [Advanced Topics](#9-advanced-topics)
   - [Raw Sockets](#raw-sockets)
   - [Socket Pairs](#socket-pairs)
   - [Out-of-Band Data (MSG_OOB)](#out-of-band-data-msg_oob)
   - [Ancillary Data (cmsg)](#ancillary-data-cmsg)
   - [Non-Blocking Sockets and Multiplexing](#non-blocking-sockets-and-multiplexing)

10. [Practical Implementation](#10-practical-implementation)
    - [Building a TCP Server](#building-a-tcp-server)
    - [Building a TCP Client](#building-a-tcp-client)
    - [Error Handling Patterns](#error-handling-patterns)
    - [Common Pitfalls](#common-pitfalls)
    - [Performance Considerations](#performance-considerations)

11. [Summary and Appendix](#11-summary-and-appendix)
    - [Socket System Call Quick Reference](#socket-system-call-quick-reference)
    - [Socket Options Table](#socket-options-table)
    - [Error Codes Reference](#error-codes-reference)
    - [TCP State Diagram](#tcp-state-diagram)
    - [The Big Picture](#the-big-picture)

12. [References](#references)

---

## 1. Introduction

### The Birth of Network Programming

In the early 1980s, the computing world faced a challenge: how could programs on different machines
communicate? The answer came from the Computer Systems Research Group (CSRG) at the University of California,
Berkeley. In 1983, with the release of BSD 4.2, they introduced the **socket API**—a programming interface
that would revolutionize network programming and remain fundamentally unchanged for over four decades.

The genius of the BSD socket design lay in its integration with the Unix philosophy: **a socket is a file
descriptor**. Just as pipes extended the file abstraction to inter-process communication, sockets extended it
to network communication. Programs could use the familiar `read()` and `write()` calls, or the new
socket-specific calls that offered additional control.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE SOCKET REVOLUTION                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   BEFORE SOCKETS (Pre-1983):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Each network had its own API                                    │ │
│   │   • Programs were network-specific                                  │ │
│   │   • No unified abstraction                                          │ │
│   │   • Cannot port code between systems                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   AFTER SOCKETS (BSD 4.2, 1983):                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • ONE API for all networks                                        │ │
│   │   • Protocol-independent programming                                │ │
│   │   • File descriptor abstraction                                     │ │
│   │   • Portable across Unix systems                                    │ │
│   │   • Foundation for the Internet                                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The Socket Abstraction

A socket is an **endpoint for communication**. Just as a telephone is an endpoint for voice communication, a
socket is an endpoint for data communication. The analogy extends further:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THE TELEPHONE ANALOGY                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TELEPHONE NETWORK                        SOCKET NETWORK                  │
│   ─────────────────                        ──────────────                  │
│                                                                            │
│   Get a phone          ───────────>        socket()                        │
│   Assign phone number  ───────────>        bind()                          │
│   Wait for calls       ───────────>        listen()                        │
│   Answer a call        ───────────>        accept()                        │
│   Make a call          ───────────>        connect()                       │
│   Talk                 ───────────>        send() / recv()                 │
│   Hang up              ───────────>        close()                         │
│                                                                            │
│   ┌─────────────┐                          ┌─────────────┐                 │
│   │  PHONE A    │ ◄══════════════════════► │  PHONE B    │                 │
│   │  555-1234   │    Voice Communication   │  555-5678   │                 │
│   └─────────────┘                          └─────────────┘                 │
│                                                                            │
│   ┌─────────────┐                          ┌─────────────┐                 │
│   │  SOCKET A   │ ◄══════════════════════► │  SOCKET B   │                 │
│   │ 192.168.1.1 │    Data Communication    │ 192.168.1.2 │                 │
│   │    :8080    │                          │    :54321   │                 │
│   └─────────────┘                          └─────────────┘                 │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

But sockets offer capabilities far beyond simple communication:

1. **Multiple protocols**: TCP, UDP, raw IP, Unix domain
2. **Multiple address families**: IPv4, IPv6, local filesystem
3. **Bidirectional communication**: Unlike pipes
4. **Network transparency**: Local and remote communication through same API
5. **Advanced features**: Out-of-band data, ancillary data, file descriptor passing

### Historical Context

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OF NETWORK PROGRAMMING                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Year    Event                           Significance                     │
│   ────    ─────                           ────────────                     │
│   1969    ARPANET created                 First packet-switched network    │
│   1974    TCP/IP conceived                Vint Cerf & Bob Kahn             │
│   1981    BSD 4.1a                        Early socket prototype           │
│   1983    BSD 4.2 released                SOCKET API INTRODUCED            │
│   1985    BSD 4.3                         Performance improvements         │
│   1988    BSD 4.3-Reno                    POSIX compliance                 │
│   1989    BSD Net/2                       Clean-room TCP/IP                │
│   1993    Linux 1.0                       Sockets in Linux                 │
│   1995    WinSock 2.0                     Windows socket API               │
│   1998    IPv6 sockets                    AF_INET6 address family          │
│   2003    SCTP sockets                    Stream Control Transmission      │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Timeline:                                                         │ │
│   │                                                                     │ │
│   │   1969      1974      1983      1993      1998      2003            │ │
│   │   ─┼─────────┼─────────┼─────────┼─────────┼─────────┼───────>      │ │
│   │    │         │         │         │         │         │              │ │
│   │  ARPA     TCP/IP   BSD 4.2    Linux   IPv6      SCTP              │ │
│   │  NET               Sockets    1.0     sockets   sockets            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

The BSD socket API has remained remarkably stable. Code written for BSD 4.2 in 1983 can often compile and run
today with minimal modifications. This stability reflects the elegance of the original design.

### Document Organization

This document follows the structure established by Maurice Bach in "The Design of the UNIX Operating System":

1. **Data Structures**: Kernel tables and structures supporting sockets
2. **Algorithms**: Step-by-step procedures the kernel follows
3. **Interactions**: How system calls affect kernel state
4. **Edge Cases**: Boundary conditions and error handling
5. **Practical Application**: Real-world usage patterns

We proceed from abstract concepts to concrete implementations, building understanding layer by layer.

---

## 2. Fundamental Concepts

### What Is a Socket?

At its core, a socket is a **kernel object** that represents one endpoint of a two-way communication channel.
From the user-space perspective, it's simply a file descriptor. But inside the kernel, a socket is a complex
data structure connecting multiple subsystems:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WHAT IS A SOCKET?                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   USER SPACE VIEW:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int sockfd = socket(AF_INET, SOCK_STREAM, 0);                     │ │
│   │                                                                     │ │
│   │   To the programmer, sockfd is just a number (e.g., 3)              │ │
│   │   It can be used with read(), write(), close()                      │ │
│   │   It looks just like a file descriptor!                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL VIEW:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sockfd = 3 points to a complex hierarchy of structures:           │ │
│   │                                                                     │ │
│   │   Process FD Table                                                  │ │
│   │   ┌─────┬──────────┐                                                │ │
│   │   │  0  │ stdin    │                                                │ │
│   │   │  1  │ stdout   │                                                │ │
│   │   │  2  │ stderr   │                                                │ │
│   │   │  3  │ ─────────┼──────► struct file                             │ │
│   │   └─────┴──────────┘              │                                 │ │
│   │                                   ▼                                 │ │
│   │                            struct socket                            │ │
│   │                                   │                                 │ │
│   │                                   ▼                                 │ │
│   │                            struct sock (protocol-specific)          │ │
│   │                                   │                                 │ │
│   │                    ┌──────────────┼──────────────┐                  │ │
│   │                    ▼              ▼              ▼                  │ │
│   │               Send Queue    Receive Queue    State Machine          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Socket Data Structures in the Kernel

The Linux kernel uses a layered approach to socket implementation. Understanding these layers is crucial for
comprehending socket behavior:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SOCKET DATA STRUCTURE HIERARCHY                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                         struct file                                 │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  f_op     = &socket_file_ops  // VFS operations               │ │ │
│   │   │  f_flags  = O_RDWR            // Read-write mode              │ │ │
│   │   │  f_pos    = (not used)        // Sockets don't have position  │ │ │
│   │   │  private_data ────────────────────────────┐                   │ │ │
│   │   └───────────────────────────────────────────│───────────────────┘ │ │
│   └───────────────────────────────────────────────│─────────────────────┘ │
│                                                   │                       │
│                                                   ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                        struct socket                                │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  state    = SS_CONNECTED      // Socket state                 │ │ │
│   │   │  type     = SOCK_STREAM       // TCP                          │ │ │
│   │   │  flags    = 0                 // Socket flags                 │ │ │
│   │   │  ops      = &inet_stream_ops  // Protocol operations          │ │ │
│   │   │  file     = (back pointer)    // Points to struct file        │ │ │
│   │   │  sk       ────────────────────────────────┐                   │ │ │
│   │   └───────────────────────────────────────────│───────────────────┘ │ │
│   └───────────────────────────────────────────────│─────────────────────┘ │
│                                                   │                       │
│                                                   ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                     struct sock (sk)                                │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  sk_state      = TCP_ESTABLISHED  // TCP state                │ │ │
│   │   │  sk_rcvbuf     = 131072           // Receive buffer size      │ │ │
│   │   │  sk_sndbuf     = 131072           // Send buffer size         │ │ │
│   │   │  sk_receive_queue = (list)        // Incoming packets         │ │ │
│   │   │  sk_write_queue   = (list)        // Outgoing packets         │ │ │
│   │   │  sk_sleep      = (wait queue)     // Blocked processes        │ │ │
│   │   │  sk_prot       = &tcp_prot        // Protocol handlers        │ │ │
│   │   │  sk_socket     = (back pointer)   // Points to struct socket  │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   For TCP, this is actually embedded in struct tcp_sock:            │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  struct tcp_sock                                              │ │ │
│   │   │  ┌─────────────────────────────────────────────────────────┐ │ │ │
│   │   │  │  struct inet_connection_sock  (base)                    │ │ │ │
│   │   │  │  ┌───────────────────────────────────────────────────┐ │ │ │ │
│   │   │  │  │  struct inet_sock  (base)                         │ │ │ │ │
│   │   │  │  │  ┌─────────────────────────────────────────────┐ │ │ │ │ │
│   │   │  │  │  │  struct sock  (base)                        │ │ │ │ │ │
│   │   │  │  │  └─────────────────────────────────────────────┘ │ │ │ │ │
│   │   │  │  │  inet_saddr  = source IP address                 │ │ │ │ │
│   │   │  │  │  inet_daddr  = destination IP address            │ │ │ │ │
│   │   │  │  │  inet_sport  = source port                       │ │ │ │ │
│   │   │  │  │  inet_dport  = destination port                  │ │ │ │ │
│   │   │  │  └───────────────────────────────────────────────────┘ │ │ │ │
│   │   │  │  icsk_accept_queue = (incoming connections)            │ │ │ │
│   │   │  └─────────────────────────────────────────────────────────┘ │ │ │
│   │   │  snd_una = oldest unacknowledged sequence number            │ │ │
│   │   │  snd_nxt = next sequence number to send                     │ │ │
│   │   │  rcv_nxt = next sequence number expected                    │ │ │
│   │   │  snd_wnd = send window (flow control)                       │ │ │
│   │   │  rcv_wnd = receive window                                   │ │ │
│   │   └─────────────────────────────────────────────────────────────┘ │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

This hierarchy enables:

- **Abstraction**: Higher layers don't need protocol-specific knowledge
- **Code reuse**: Common functionality in base structures
- **Extensibility**: New protocols add their own structures

### NON-BLOCKING + MULTIPLEXING: │

```

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
│   └───────────────────────────────────────────────────Address Families

```

The **address family** (also called **domain**) specifies the communication domain and address format. The
socket() system call's first argument selects the address family:

```

┌───────────────────────────────────────────────────────────────────────────┐
│                    ADDRESS FAMILIES                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────┬─────────────────────────────────────────────────────┐   │
│   │ AF_INET     │ IPv4 Internet protocols                             │   │
│   │             │ Address: 32-bit IP + 16-bit port                    │   │
│   │             │ Example: 192.168.1.1:8080                           │   │
│   ├─────────────┼─────────────────────────────────────────────────────┤   │
│   │ AF_INET6    │ IPv6 Internet protocols                             │   │
│   │             │ Address: 128-bit IP + 16-bit port + flow + scope    │   │
│   │             │ Example: [::1]:8080                                 │   │
│   ├─────────────┼─────────────────────────────────────────────────────┤   │
│   │ AF_UNIX     │ Local communication (Unix domain)                   │   │
│   │ AF_LOCAL    │ Address: filesystem path or abstract name           │   │
│   │             │ Example: /var/run/docker.sock                       │   │
│   ├─────────────┼─────────────────────────────────────────────────────┤   │
│   │ AF_PACKET   │ Low-level packet interface (Linux)                  │   │
│   │             │ Direct access to network device                     │   │
│   ├─────────────┼─────────────────────────────────────────────────────┤   │
│   │ AF_NETLINK  │ Kernel-user communication (Linux)                   │   │
│   │             │ Configure network interfaces, routing, etc.         │   │
│   └─────────────┴─────────────────────────────────────────────────────┘   │
│                                                                            │
│   ADDRESS STRUCTURE COMPARISON:                                            │
│                                                                            │
│   struct sockaddr_in (AF_INET):          struct sockaddr_un (AF_UNIX):     │
│   ┌──────────────────────────┐           ┌──────────────────────────────┐  │
│   │ sin_family = AF_INET     │           │ sun_family = AF_UNIX         │  │
│   │ sin_port   = 8080        │           │ sun_path   = "/tmp/mysock"   │  │
│   │ sin_addr   = 192.168.1.1 │           │                              │  │
│   │ sin_zero   = (padding)   │           │                              │  │
│   └──────────────────────────┘           └──────────────────────────────┘  │
│          16 bytes                               110 bytes (Linux)          │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Socket Types

The **socket type** determines the communication semantics:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SOCKET TYPES                                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   SOCK_STREAM - Reliable, ordered, bidirectional byte stream              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A                                  Process B              │ │
│   │   ┌───────────┐                              ┌───────────┐          │ │
│   │   │           │                              │           │          │ │
│   │   │  write()  │ ════════════════════════════>│  read()   │          │ │
│   │   │  "Hello"  │     Reliable delivery        │  "Hello"  │          │ │
│   │   │           │     Order preserved          │           │          │ │
│   │   │           │     No message boundaries    │           │          │ │
│   │   └───────────┘                              └───────────┘          │ │
│   │                                                                     │ │
│   │   • Connection-oriented (must connect() or accept())                │ │
│   │   • Implemented by TCP (AF_INET) or stream sockets (AF_UNIX)        │ │
│   │   • Data may be split or coalesced                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOCK_DGRAM - Unreliable, unordered, message-preserving                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A                                  Process B              │ │
│   │   ┌───────────┐                              ┌───────────┐          │ │
│   │   │           │ ─────────────────────────────>│           │          │ │
│   │   │ sendto()  │   ┌─────────┐ May be lost    │ recvfrom()│          │ │
│   │   │  msg 1    │   │ msg 2   │ ─ ─ ─ ─ ─ ─X   │  msg 3    │          │ │
│   │   │           │ ─────────────────────────────>│  msg 1    │          │ │
│   │   │  msg 2    │   └─────────┘ Out of order!  │           │          │ │
│   │   │  msg 3    │                              │           │          │ │
│   │   └───────────┘                              └───────────┘          │ │
│   │                                                                     │ │
│   │   • Connectionless (no connect() required, but allowed)             │ │
│   │   • Implemented by UDP (AF_INET) or datagram sockets (AF_UNIX)      │ │
│   │   • Message boundaries preserved                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOCK_RAW - Raw network protocol access                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Direct access to IP layer                                       │ │
│   │   • Can craft custom packets (ICMP, custom protocols)               │ │
│   │   • Requires CAP_NET_RAW capability (usually root)                  │ │
│   │   • Used by ping, traceroute                                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOCK_SEQPACKET - Reliable, ordered, message-preserving                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Combines best of SOCK_STREAM and SOCK_DGRAM                     │ │
│   │   • Connection-oriented like TCP                                    │ │
│   │   • Preserves message boundaries like UDP                           │ │
│   │   • Supported by SCTP, Unix domain sockets                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Protocols

The third argument to socket() specifies the protocol. Usually it's 0 to select the default protocol for the
given type:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    PROTOCOL SELECTION                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   socket(AF_INET, SOCK_STREAM, 0)  →  TCP (IPPROTO_TCP)                   │
│   socket(AF_INET, SOCK_DGRAM, 0)   →  UDP (IPPROTO_UDP)                   │
│   socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)  →  ICMP                        │
│   socket(AF_UNIX, SOCK_STREAM, 0)  →  Unix stream socket                  │
│   socket(AF_UNIX, SOCK_DGRAM, 0)   →  Unix datagram socket                │
│                                                                            │
│   COMMON PROTOCOL CONSTANTS:                                               │
│   ┌───────────────┬───────────────────────────────────────────────────┐   │
│   │ IPPROTO_TCP   │ Transmission Control Protocol (6)                 │   │
│   │ IPPROTO_UDP   │ User Datagram Protocol (17)                       │   │
│   │ IPPROTO_ICMP  │ Internet Control Message Protocol (1)             │   │
│   │ IPPROTO_RAW   │ Raw IP packets (255)                              │   │
│   │ IPPROTO_SCTP  │ Stream Control Transmission Protocol (132)        │   │
│   └───────────────┴───────────────────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Socket System Calls

### socket() - Creating a Socket

The `socket()` system call creates a new socket and returns a file descriptor:

```c
int socket(int domain, int type, int protocol);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    socket() SYSTEM CALL                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   EXAMPLE:                                                                 │
│   int sockfd = socket(AF_INET, SOCK_STREAM, 0);                           │
│                       │         │           │                              │
│                       │         │           └── Protocol (0 = default)     │
│                       │         └────────────── Type (TCP stream)          │
│                       └──────────────────────── Domain (IPv4)              │
│                                                                            │
│   KERNEL ALGORITHM (simplified):                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sys_socket(domain, type, protocol):                               │ │
│   │   1. Validate arguments                                             │ │
│   │   2. Look up protocol family (AF_INET → inet_family_ops)            │ │
│   │   3. Allocate struct socket                                         │ │
│   │   4. Call family->create() to initialize socket                     │ │
│   │      └─> For AF_INET/SOCK_STREAM:                                   │ │
│   │          a. Allocate struct tcp_sock (includes struct sock)         │ │
│   │          b. Initialize TCP state machine to TCP_CLOSE               │ │
│   │          c. Set up send/receive buffers                             │ │
│   │          d. Initialize wait queues                                  │ │
│   │   5. Allocate file descriptor                                       │ │
│   │   6. Create struct file pointing to socket                          │ │
│   │   7. Install fd in process's fd table                               │ │
│   │   8. Return fd                                                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHAT GETS CREATED:                                                       │
│                                                                            │
│   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐         │
│   │ fd = 3        │      │ struct file   │      │ struct socket │         │
│   │ ──────────────┼─────>│ ─────────────┼─────>│ ─────────────│         │
│   │ (in process   │      │ f_op =        │      │ state = SS_   │         │
│   │  fd table)    │      │  socket_ops   │      │  UNCONNECTED  │         │
│   └───────────────┘      └───────────────┘      │ sk ──────────┼──┐      │
│                                                 └───────────────┘  │      │
│                                                                    │      │
│                                                                    ▼      │
│                                                 ┌───────────────────────┐ │
│                                                 │ struct tcp_sock       │ │
│                                                 │ ┌───────────────────┐ │ │
│                                                 │ │ sk_state =        │ │ │
│                                                 │ │   TCP_CLOSE       │ │ │
│                                                 │ │ sk_receive_queue  │ │ │
│                                                 │ │   = empty         │ │ │
│                                                 │ │ sk_write_queue    │ │ │
│                                                 │ │   = empty         │ │ │
│                                                 │ └───────────────────┘ │ │
│                                                 └───────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### bind() - Assigning an Address

The `bind()` system call assigns a local address to a socket:

```c
int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    bind() SYSTEM CALL                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHY BIND?                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   A socket starts with NO address. It's like a phone without        │ │
│   │   a phone number - it exists, but no one can call it.               │ │
│   │                                                                     │ │
│   │   bind() assigns:                                                   │ │
│   │   • IP address (which network interface to use)                     │ │
│   │   • Port number (which service endpoint)                            │ │
│   │                                                                     │ │
│   │   After bind(sockfd, {192.168.1.1, 8080}):                          │ │
│   │   • Socket is bound to 192.168.1.1:8080                             │ │
│   │   • Other processes cannot use this address (normally)              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SPECIAL ADDRESSES:                                                       │
│   ┌───────────────────┬─────────────────────────────────────────────────┐ │
│   │ INADDR_ANY (0)    │ Bind to ALL interfaces                          │ │
│   │ Port 0            │ Let kernel choose an available port             │ │
│   │ INADDR_LOOPBACK   │ Bind to localhost (127.0.0.1) only              │ │
│   └───────────────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
│   EXAMPLE CODE:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   struct sockaddr_in addr;                                          │ │
│   │   addr.sin_family = AF_INET;                                        │ │
│   │   addr.sin_port = htons(8080);        // Network byte order!        │ │
│   │   addr.sin_addr.s_addr = INADDR_ANY;  // All interfaces             │ │
│   │                                                                     │ │
│   │   bind(sockfd, (struct sockaddr*)&addr, sizeof(addr));              │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL ALGORITHM:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sys_bind(sockfd, addr, addrlen):                                  │ │
│   │   1. Get struct socket from sockfd                                  │ │
│   │   2. Copy address from user space to kernel                         │ │
│   │   3. Validate address format and length                             │ │
│   │   4. Check if address is already in use                             │ │
│   │      └─> If in use and SO_REUSEADDR not set: return EADDRINUSE      │ │
│   │   5. If port < 1024, check for CAP_NET_BIND_SERVICE                 │ │
│   │   6. Call protocol-specific bind (inet_bind for TCP/UDP)            │ │
│   │      └─> Store address in inet_sock structure                       │ │
│   │   7. Return 0 on success                                            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON ERRORS:                                                           │
│   ┌───────────────────┬─────────────────────────────────────────────────┐ │
│   │ EADDRINUSE        │ Address already in use                          │ │
│   │ EACCES            │ Port < 1024 requires root                       │ │
│   │ EINVAL            │ Socket already bound                            │ │
│   │ ENOENT            │ Unix socket path doesn't exist                  │ │
│   └───────────────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### listen() - Marking as Passive

The `listen()` system call marks a socket as passive—ready to accept incoming connections:

```c
int listen(int sockfd, int backlog);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    listen() SYSTEM CALL                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHAT LISTEN DOES:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Before listen():                     After listen():              │ │
│   │   ┌──────────────┐                     ┌──────────────┐             │ │
│   │   │   Socket     │                     │   Socket     │             │ │
│   │   │              │                     │              │             │ │
│   │   │ TCP_CLOSE    │    ───────────>     │ TCP_LISTEN   │             │ │
│   │   │              │    listen(fd,5)     │              │             │ │
│   │   │ No queues    │                     │ ┌──────────┐ │             │ │
│   │   │              │                     │ │ SYN Queue│ │             │ │
│   │   │              │                     │ │ (backlog)│ │             │ │
│   │   │              │                     │ └──────────┘ │             │ │
│   │   │              │                     │ ┌──────────┐ │             │ │
│   │   │              │                     │ │Accept Qu.│ │             │ │
│   │   │              │                     │ └──────────┘ │             │ │
│   │   └──────────────┘                     └──────────────┘             │ │
│   │                                                                     │ │
│   │   The socket is now PASSIVE - it can accept() but not connect()    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE BACKLOG PARAMETER:                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Modern Linux maintains TWO queues:                                │ │
│   │                                                                     │ │
│   │   1. SYN Queue (syn_backlog):                                       │ │
│   │      • Connections in SYN_RECV state (handshake in progress)        │ │
│   │      • Size controlled by /proc/sys/net/ipv4/tcp_max_syn_backlog    │ │
│   │                                                                     │ │
│   │   2. Accept Queue:                                                  │ │
│   │      • Connections in ESTABLISHED state (ready to accept)           │ │
│   │      • Size = min(backlog, /proc/sys/net/core/somaxconn)            │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │                                                             │   │ │
│   │   │   Client          Server                                    │   │ │
│   │   │   ┌────┐         ┌────────────────────────────────┐         │   │ │
│   │   │   │    │──SYN──> │ ┌────────────┐                 │         │   │ │
│   │   │   │    │         │ │ SYN Queue  │ SYN_RECV state  │         │   │ │
│   │   │   │    │<─SYN+ACK│ │ ┌───┬───┐  │                 │         │   │ │
│   │   │   │    │         │ │ │ C │...│  │                 │         │   │ │
│   │   │   │    │──ACK──> │ │ └───┴───┘  │                 │         │   │ │
│   │   │   │    │         │ └─────┬──────┘                 │         │   │ │
│   │   │   │    │         │       │                        │         │   │ │
│   │   │   │    │         │       ▼ Move to accept queue   │         │   │ │
│   │   │   │    │         │ ┌────────────┐                 │         │   │ │
│   │   │   │    │         │ │Accept Queue│ ESTABLISHED     │         │   │ │
│   │   │   │    │         │ │ ┌───┬───┐  │                 │         │   │ │
│   │   │   │    │         │ │ │ C │...│  │ ◄── accept()    │         │   │ │
│   │   │   │    │         │ │ └───┴───┘  │     takes from  │         │   │ │
│   │   │   │    │         │ └────────────┘     this queue  │         │   │ │
│   │   │   └────┘         └────────────────────────────────┘         │   │ │
│   │   │                                                             │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IF QUEUES ARE FULL:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │   • New SYN packets are dropped (or sent RST)                       │ │
│   │   • Client sees connection timeout or reset                         │ │
│   │   • This is why busy servers need larger backlogs                   │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### accept() - Accepting Connections

The `accept()` system call extracts the first connection from the accept queue:

```c
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);
int accept4(int sockfd, struct sockaddr *addr, socklen_t *addrlen, int flags);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    accept() SYSTEM CALL                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHAT ACCEPT DOES:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Listening Socket (fd=3)              New Connected Socket (fd=5)  │ │
│   │   ┌─────────────────────┐              ┌─────────────────────┐      │ │
│   │   │ Local: 0.0.0.0:8080 │              │ Local: 192.168.1.1  │      │ │
│   │   │ State: TCP_LISTEN   │              │        :8080        │      │ │
│   │   │                     │   accept()   │ Remote: 10.0.0.5    │      │ │
│   │   │ ┌─────────────────┐ │   ───────>   │        :54321       │      │ │
│   │   │ │ Accept Queue    │ │              │ State: ESTABLISHED  │      │ │
│   │   │ │ ┌───┬───┬───┐   │ │              └─────────────────────┘      │ │
│   │   │ │ │ A │ B │ C │   │ │                        │                  │ │
│   │   │ │ └─┬─┴───┴───┘   │ │    Returns new fd ─────┘                  │ │
│   │   │ │   │             │ │    for THIS connection                    │ │
│   │   │ └───│─────────────┘ │                                           │ │
│   │   │     │               │    Listening socket (fd=3) stays          │ │
│   │   │     └── Removed ────│    unchanged and can accept more!         │ │
│   │   │                     │                                           │ │
│   │   └─────────────────────┘                                           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL ALGORITHM:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sys_accept(sockfd, addr, addrlen):                                │ │
│   │   1. Get listening socket from sockfd                               │ │
│   │   2. Check socket is in LISTEN state                                │ │
│   │   3. If accept queue is empty:                                      │ │
│   │      ├─> If O_NONBLOCK: return EAGAIN immediately                   │ │
│   │      └─> Else: SLEEP until connection arrives                       │ │
│   │          (add to socket's wait queue)                               │ │
│   │   4. Dequeue first connection from accept queue                     │ │
│   │   5. Allocate new file descriptor                                   │ │
│   │   6. Create new struct file for the connected socket                │ │
│   │   7. Copy peer address to user space (if addr != NULL)              │ │
│   │   8. Return new fd                                                  │ │
│   │                                                                     │ │
│   │   NOTE: The connected socket is ALREADY created by the kernel       │ │
│   │   during the 3-way handshake. accept() just returns it!             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   accept4() FLAGS:                                                         │
│   ┌───────────────────┬─────────────────────────────────────────────────┐ │
│   │ SOCK_NONBLOCK     │ Set O_NONBLOCK on new socket (saves fcntl)      │ │
│   │ SOCK_CLOEXEC      │ Set close-on-exec flag (important for security) │ │
│   └───────────────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### connect() - Initiating Connections

The `connect()` system call initiates a connection to a remote socket:

```c
int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    connect() SYSTEM CALL                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   FOR TCP (SOCK_STREAM):                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   connect() initiates the TCP three-way handshake:                  │ │
│   │                                                                     │ │
│   │   Client                              Server                        │ │
│   │   ┌────────────────┐                  ┌────────────────┐            │ │
│   │   │ TCP_CLOSE      │                  │ TCP_LISTEN     │            │ │
│   │   │                │                  │                │            │ │
│   │   │    connect()   │                  │                │            │ │
│   │   │       │        │                  │                │            │ │
│   │   │       ▼        │                  │                │            │ │
│   │   │ TCP_SYN_SENT   │ ───── SYN ─────> │                │            │ │
│   │   │                │                  │                │            │ │
│   │   │                │ <── SYN+ACK ──── │ TCP_SYN_RECV   │            │ │
│   │   │                │                  │                │            │ │
│   │   │ TCP_ESTABLISHED│ ───── ACK ─────> │ TCP_ESTABLISHED│            │ │
│   │   │       │        │                  │                │            │ │
│   │   │       ▼        │                  │                │            │ │
│   │   │ connect() returns 0               │                │            │ │
│   │   │                │                  │                │            │ │
│   │   └────────────────┘                  └────────────────┘            │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   KERNEL ALGORITHM:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   sys_connect(sockfd, addr, addrlen):                               │ │
│   │   1. Get socket from sockfd                                         │ │
│   │   2. Copy address from user space                                   │ │
│   │   3. If socket not yet bound: auto-bind (ephemeral port)            │ │
│   │   4. Set destination address in inet_sock                           │ │
│   │   5. Send SYN packet                                                │ │
│   │   6. Set state to TCP_SYN_SENT                                      │ │
│   │   7. If blocking: SLEEP until connection completes or fails         │ │
│   │   8. If non-blocking: return EINPROGRESS                            │ │
│   │   9. On success: return 0, state = TCP_ESTABLISHED                  │ │
│   │   10. On failure: return error (ECONNREFUSED, ETIMEDOUT, etc.)      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NON-BLOCKING connect():                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   When O_NONBLOCK is set, connect() behaves differently:            │ │
│   │                                                                     │ │
│   │   ret = connect(sockfd, &addr, sizeof(addr));                       │ │
│   │   // Returns immediately with -1, errno = EINPROGRESS               │ │
│   │                                                                     │ │
│   │   // Use select/poll/epoll to wait for connection:                  │ │
│   │   // Socket becomes WRITABLE when connection completes              │ │
│   │                                                                     │ │
│   │   // Check if connection succeeded:                                 │ │
│   │   int error;                                                        │ │
│   │   socklen_t len = sizeof(error);                                    │ │
│   │   getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &error, &len);           │ │
│   │   if (error == 0) {                                                 │ │
│   │       // Connection successful!                                     │ │
│   │   } else {                                                          │ │
│   │       // Connection failed: error contains errno                    │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   FOR UDP (SOCK_DGRAM):                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   connect() on UDP doesn't establish a connection!                  │ │
│   │                                                                     │ │
│   │   It just sets the default destination address so you can:          │ │
│   │   • Use send() instead of sendto()                                  │ │
│   │   • Use recv() instead of recvfrom()                                │ │
│   │   • Receive ICMP errors (port unreachable, etc.)                    │ │
│   │                                                                     │ │
│   │   No packets are sent! It returns immediately.                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   COMMON ERRORS:                                                           │
│   ┌───────────────────┬─────────────────────────────────────────────────┐ │
│   │ ECONNREFUSED      │ Target port not listening (RST received)        │ │
│   │ ETIMEDOUT         │ No response (SYN+ACK never received)            │ │
│   │ ENETUNREACH       │ Network unreachable                             │ │
│   │ EHOSTUNREACH      │ Host unreachable                                │ │
│   │ EINPROGRESS       │ Non-blocking connect in progress (not an error) │ │
│   │ EALREADY          │ Previous connect() still in progress            │ │
│   │ EISCONN           │ Already connected                               │ │
│   └───────────────────┴─────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### send() and recv()

These calls transmit and receive data on a connected socket:

```c
ssize_t send(int sockfd, const void *buf, size_t len, int flags);
ssize_t recv(int sockfd, void *buf, size_t len, int flags);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    send() AND recv()                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THESE ARE EQUIVALENT (for connected sockets):                            │
│                                                                            │
│   send(fd, buf, len, 0)   ≡   write(fd, buf, len)                         │
│   recv(fd, buf, len, 0)   ≡   read(fd, buf, len)                          │
│                                                                            │
│   BUT send/recv ALLOW FLAGS:                                               │
│   ┌───────────────┬─────────────────────────────────────────────────────┐ │
│   │ MSG_DONTWAIT  │ Non-blocking operation (this call only)             │ │
│   │ MSG_PEEK      │ Receive data without removing from queue            │ │
│   │ MSG_WAITALL   │ Block until full amount received                    │ │
│   │ MSG_OOB       │ Send/receive out-of-band data                       │ │
│   │ MSG_NOSIGNAL  │ Don't generate SIGPIPE on broken connection         │ │
│   │ MSG_MORE      │ More data coming (TCP_CORK behavior)                │ │
│   └───────────────┴─────────────────────────────────────────────────────┘ │
│                                                                            │
│   DATA FLOW (TCP):                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Application                 Kernel                   Network      │ │
│   │   ┌─────────┐                ┌──────────────────┐                   │ │
│   │   │  send() │ ──────────────>│ Send Buffer      │ ──> TCP/IP ──>   │ │
│   │   │         │   copy data    │ ┌──────────────┐ │     Stack        │ │
│   │   └─────────┘   to kernel    │ │ DATA DATA DA │ │                  │ │
│   │                              │ └──────────────┘ │                  │ │
│   │                              │                  │                  │ │
│   │   ┌─────────┐                │ Receive Buffer   │                  │ │
│   │   │  recv() │ <──────────────│ ┌──────────────┐ │ <── TCP/IP <──   │ │
│   │   │         │   copy data    │ │ DATA DATA DA │ │     Stack        │ │
│   │   └─────────┘   from kernel  │ └──────────────┘ │                  │ │
│   │                              └──────────────────┘                  │ │
│   │                                                                     │ │
│   │   IMPORTANT:                                                        │ │
│   │   • send() copies to kernel buffer, doesn't wait for network send  │ │
│   │   • recv() copies from kernel buffer, blocks if buffer empty       │ │
│   │   • Kernel handles retransmissions, ACKs, flow control             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   PARTIAL OPERATIONS:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   send() might send LESS than requested:                            │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  n = send(fd, buffer, 1000, 0);                               │ │ │
│   │   │  // n might be 500 if send buffer only had space for 500!     │ │ │
│   │   │  // Must loop to send remainder                               │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   recv() might receive LESS than requested:                         │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │  n = recv(fd, buffer, 1000, 0);                               │ │ │
│   │   │  // n might be 100 if only 100 bytes available!               │ │ │
│   │   │  // Use MSG_WAITALL to block for full amount                  │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   recv() returns 0 means:                                           │ │
│   │   • Peer performed orderly shutdown (FIN received)                  │ │
│   │   • No more data will ever arrive on this socket                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### sendto() and recvfrom()

These calls are used for connectionless (UDP) sockets where each packet may go to/come from a different
address:

```c
ssize_t sendto(int sockfd, const void *buf, size_t len, int flags,
               const struct sockaddr *dest_addr, socklen_t addrlen);
ssize_t recvfrom(int sockfd, void *buf, size_t len, int flags,
                 struct sockaddr *src_addr, socklen_t *addrlen);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    sendto() AND recvfrom()                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   WHEN TO USE:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   TCP (connected):      UDP (connectionless):                       │ │
│   │   ┌────────────────┐    ┌────────────────────────────┐              │ │
│   │   │ send(fd, ...)  │    │ sendto(fd, ..., dest_addr) │              │ │
│   │   │ recv(fd, ...)  │    │ recvfrom(fd, ..., src_addr)│              │ │
│   │   └────────────────┘    └────────────────────────────┘              │ │
│   │   Destination known     Must specify for each packet               │ │
│   │   from connect()        (or use connected UDP)                      │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   UDP SERVER PATTERN:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Server                         Clients                            │ │
│   │   ┌──────────────┐              ┌──────────────┐                    │ │
│   │   │ socket()     │              │ Client A     │                    │ │
│   │   │ bind(:8080)  │              │ 10.0.0.1     │                    │ │
│   │   │              │              └──────┬───────┘                    │ │
│   │   │              │  sendto(A,8080)    │                             │ │
│   │   │              │ <──────────────────┘                             │ │
│   │   │              │                                                  │ │
│   │   │ recvfrom()   │   Returns: data + src_addr = 10.0.0.1           │ │
│   │   │   │          │                                                  │ │
│   │   │   ▼          │              ┌──────────────┐                    │ │
│   │   │ sendto(      │              │ Client B     │                    │ │
│   │   │  src_addr)   │              │ 10.0.0.2     │                    │ │
│   │   │   │          │              └──────┬───────┘                    │ │
│   │   │   └──────────┼── reply ───────────>│                            │ │
│   │   │              │                                                  │ │
│   │   └──────────────┘                                                  │ │
│   │                                                                     │ │
│   │   Key: Server uses recvfrom() to learn where to reply!              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   MESSAGE BOUNDARIES (UDP vs TCP):                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   UDP preserves message boundaries (each sendto = one datagram):    │ │
│   │                                                                     │ │
│   │   sendto(fd, "Hello", 5, ...)    →  recvfrom returns "Hello" (5)    │ │
│   │   sendto(fd, "World", 5, ...)    →  recvfrom returns "World" (5)    │ │
│   │                                                                     │ │
│   │   TCP is a BYTE STREAM (no message boundaries):                     │ │
│   │                                                                     │ │
│   │   send(fd, "Hello", 5, ...)      →  recv might return "HelloWorld"  │ │
│   │   send(fd, "World", 5, ...)          or "Hel" then "loWorld" etc.   │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   IF BUFFER TOO SMALL (UDP):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   // Sender sends 1000 bytes                                        │ │
│   │   sendto(fd, big_message, 1000, ...);                               │ │
│   │                                                                     │ │
│   │   // Receiver has only 500 byte buffer                              │ │
│   │   char buf[500];                                                    │ │
│   │   n = recvfrom(fd, buf, 500, ...);                                  │ │
│   │   // n = 500, REST OF DATAGRAM IS DISCARDED!                        │ │
│   │   // (Use MSG_TRUNC to detect this)                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### shutdown() vs close()

Understanding the difference between these two is critical for proper socket cleanup:

```c
int shutdown(int sockfd, int how);    /* how: SHUT_RD, SHUT_WR, SHUT_RDWR */
int close(int fd);
```

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    shutdown() vs close()                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE KEY DIFFERENCE:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   close():                                                          │ │
│   │   • Decrements reference count on file descriptor                   │ │
│   │   • Socket destroyed only when refcount reaches 0                   │ │
│   │   • If socket is shared (fork), other processes can still use it   │ │
│   │                                                                     │ │
│   │   shutdown():                                                        │ │
│   │   • Affects the SOCKET itself, not the file descriptor              │ │
│   │   • Immediately affects ALL processes sharing the socket            │ │
│   │   • Sends FIN to peer (for SHUT_WR)                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   shutdown() OPTIONS:                                                      │
│   ┌───────────────┬─────────────────────────────────────────────────────┐ │
│   │ SHUT_RD (0)   │ Disable further receives (recv returns 0)          │ │
│   │ SHUT_WR (1)   │ Disable further sends, sends FIN to peer           │ │
│   │ SHUT_RDWR (2) │ Both of the above                                   │ │
│   └───────────────┴─────────────────────────────────────────────────────┘ │
│                                                                            │
│   VISUAL COMPARISON:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   After fork():                                                     │ │
│   │   ┌─────────────┐     ┌─────────────────────────────────┐           │ │
│   │   │  Parent     │     │   Kernel                        │           │ │
│   │   │  fd=5 ──────┼────>│  ┌─────────────────┐            │           │ │
│   │   │             │     │  │   Socket        │ refcount=2 │           │ │
│   │   └─────────────┘     │  │   ┌─────────┐   │            │           │ │
│   │   ┌─────────────┐     │  │   │ Buffers │   │            │           │ │
│   │   │  Child      │     │  │   └─────────┘   │            │           │ │
│   │   │  fd=5 ──────┼────>│  │   state=ESTAB  │            │           │ │
│   │   │             │     │  └─────────────────┘            │           │ │
│   │   └─────────────┘     └─────────────────────────────────┘           │ │
│   │                                                                     │ │
│   │   Parent calls close(5):                                            │ │
│   │   • refcount becomes 1                                              │ │
│   │   • Socket still exists! Child can still use it                     │ │
│   │   • NO FIN sent yet                                                 │ │
│   │                                                                     │ │
│   │   Parent calls shutdown(5, SHUT_WR):                                │ │
│   │   • FIN sent to peer IMMEDIATELY                                    │ │
│   │   • Neither parent NOR child can send anymore                       │ │
│   │   • Socket still exists, can still receive                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   HALF-CLOSE PATTERN:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Client                              Server                        │ │
│   │   ┌──────────────────┐               ┌──────────────────┐           │ │
│   │   │                  │               │                  │           │ │
│   │   │ send(request)    │ ──────────>   │                  │           │ │
│   │   │                  │               │                  │           │ │
│   │   │ shutdown(SHUT_WR)│ ────FIN────>  │ recv() returns 0 │           │ │
│   │   │                  │               │ (knows request   │           │ │
│   │   │ // Can't send    │               │  is complete)    │           │ │
│   │   │ // but can recv  │               │                  │           │ │
│   │   │                  │               │ process request  │           │ │
│   │   │                  │ <──────────   │ send(response)   │           │ │
│   │   │ recv(response)   │               │                  │           │ │
│   │   │                  │ <───FIN────   │ close()          │           │ │
│   │   │ recv() returns 0 │               │                  │           │ │
│   │   │ close()          │               └──────────────────┘           │ │
│   │   └──────────────────┘                                              │ │
│   │                                                                     │ │
│   │   This is how HTTP/1.0 worked: client sends request, then          │ │
│   │   half-closes to signal "I'm done sending"                          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHEN TO USE EACH:                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Use shutdown() when:                                               │ │
│   │   • You need half-close (stop sending but keep receiving)           │ │
│   │   • Socket is shared after fork() and you want to close NOW         │ │
│   │   • You want to signal EOF to peer while still receiving            │ │
│   │                                                                     │ │
│   │   Use close() when:                                                  │ │
│   │   • You're completely done with the socket                          │ │
│   │   • Socket is not shared (or you don't care about timing)           │ │
│   │   • Normal cleanup                                                   │ │
│   │                                                                     │ │
│   │   Best practice: shutdown(SHUT_WR), drain recv, then close()        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. TCP Sockets

TCP (Transmission Control Protocol) provides reliable, ordered, connection-oriented byte streams.
Understanding its internals is essential for building robust network applications.

### The Three-Way Handshake

Every TCP connection begins with this sequence:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TCP THREE-WAY HANDSHAKE                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Client                                              Server               │
│   ┌──────────────────┐                          ┌──────────────────┐      │
│   │ TCP_CLOSED       │                          │ TCP_LISTEN       │      │
│   │                  │                          │ (after listen()) │      │
│   │ connect() called │                          │                  │      │
│   │       │          │                          │                  │      │
│   │       ▼          │                          │                  │      │
│   │ TCP_SYN_SENT     │ ──── SYN, seq=100 ────>  │                  │      │
│   │                  │                          │ TCP_SYN_RECV     │      │
│   │                  │                          │                  │      │
│   │                  │ <─ SYN+ACK, seq=300 ───  │ (goes to SYN     │      │
│   │                  │    ack=101               │  queue)          │      │
│   │ TCP_ESTABLISHED  │                          │                  │      │
│   │                  │ ──── ACK, ack=301 ────>  │ TCP_ESTABLISHED  │      │
│   │ connect() returns│                          │ (moves to accept │      │
│   │                  │                          │  queue)          │      │
│   └──────────────────┘                          └──────────────────┘      │
│                                                                            │
│   SEQUENCE NUMBER DETAILS:                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Step 1: Client → Server                                           │ │
│   │   • SYN flag set                                                    │ │
│   │   • seq = ISN (Initial Sequence Number, random for security)        │ │
│   │   • No data, but SYN "consumes" one sequence number                 │ │
│   │                                                                     │ │
│   │   Step 2: Server → Client                                           │ │
│   │   • SYN + ACK flags set                                             │ │
│   │   • seq = Server's ISN                                              │ │
│   │   • ack = Client's ISN + 1 (acknowledging the SYN)                  │ │
│   │                                                                     │ │
│   │   Step 3: Client → Server                                           │ │
│   │   • ACK flag set                                                    │ │
│   │   • seq = Client's ISN + 1                                          │ │
│   │   • ack = Server's ISN + 1                                          │ │
│   │   • Can include data (TCP Fast Open)                                │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHY THREE STEPS?                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Each side must:                                                    │ │
│   │   1. Send its Initial Sequence Number (ISN)                         │ │
│   │   2. Receive acknowledgment that peer received it                   │ │
│   │                                                                     │ │
│   │   SYN:      Client sends ISN                                        │ │
│   │   SYN+ACK:  Server sends ISN AND acknowledges client's ISN          │ │
│   │   ACK:      Client acknowledges server's ISN                        │ │
│   │                                                                     │ │
│   │   Both directions are now synchronized!                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### TCP State Machine

TCP has 11 states. Understanding them is crucial for debugging:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TCP STATE MACHINE                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                              ┌─────────────┐                               │
│                              │   CLOSED    │                               │
│                              └──────┬──────┘                               │
│                       ┌─────────────┴─────────────┐                        │
│                       │                           │                        │
│                       ▼                           ▼                        │
│              (passive open)              (active open)                     │
│              listen()                    connect()                         │
│                       │                           │                        │
│                       ▼                           ▼                        │
│              ┌─────────────┐             ┌─────────────┐                   │
│              │   LISTEN    │             │  SYN_SENT   │                   │
│              └──────┬──────┘             └──────┬──────┘                   │
│                     │                           │                          │
│                rcv SYN                     rcv SYN+ACK                     │
│                send SYN+ACK                send ACK                        │
│                     │                           │                          │
│                     ▼                           │                          │
│              ┌─────────────┐                    │                          │
│              │  SYN_RECV   │                    │                          │
│              └──────┬──────┘                    │                          │
│                     │                           │                          │
│                rcv ACK                          │                          │
│                     │                           │                          │
│                     └──────────┬────────────────┘                          │
│                                ▼                                           │
│                       ┌─────────────┐                                      │
│                       │ ESTABLISHED │ ◄─── Data transfer happens here     │
│                       └──────┬──────┘                                      │
│                  ┌───────────┴───────────┐                                 │
│                  │                       │                                 │
│             close()                 rcv FIN                                │
│             send FIN                send ACK                               │
│                  │                       │                                 │
│                  ▼                       ▼                                 │
│           ┌─────────────┐         ┌─────────────┐                          │
│           │  FIN_WAIT_1 │         │ CLOSE_WAIT  │                          │
│           └──────┬──────┘         └──────┬──────┘                          │
│                  │                       │                                 │
│             rcv ACK                  close()                               │
│                  │                   send FIN                              │
│                  ▼                       │                                 │
│           ┌─────────────┐                ▼                                 │
│           │  FIN_WAIT_2 │         ┌─────────────┐                          │
│           └──────┬──────┘         │  LAST_ACK   │                          │
│                  │                └──────┬──────┘                          │
│             rcv FIN                      │                                 │
│             send ACK                rcv ACK                                │
│                  │                       │                                 │
│                  ▼                       ▼                                 │
│           ┌─────────────┐         ┌─────────────┐                          │
│           │  TIME_WAIT  │         │   CLOSED    │                          │
│           └──────┬──────┘         └─────────────┘                          │
│                  │                                                         │
│              2MSL timeout                                                  │
│                  │                                                         │
│                  ▼                                                         │
│           ┌─────────────┐                                                  │
│           │   CLOSED    │                                                  │
│           └─────────────┘                                                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Connection Termination (Four-Way Close)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TCP CONNECTION TERMINATION                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Initiator (Active Close)                  Receiver (Passive Close)      │
│   ┌──────────────────────┐                  ┌──────────────────────┐      │
│   │ ESTABLISHED          │                  │ ESTABLISHED          │      │
│   │                      │                  │                      │      │
│   │ close() called       │                  │                      │      │
│   │         │            │                  │                      │      │
│   │         ▼            │                  │                      │      │
│   │ FIN_WAIT_1           │ ───── FIN ─────> │ CLOSE_WAIT           │      │
│   │                      │                  │ recv() returns 0     │      │
│   │                      │ <──── ACK ────── │                      │      │
│   │ FIN_WAIT_2           │                  │ (app still sending?) │      │
│   │ (waiting for         │                  │                      │      │
│   │  peer's FIN)         │                  │ close() called       │      │
│   │                      │                  │         │            │      │
│   │                      │ <──── FIN ────── │ LAST_ACK             │      │
│   │ TIME_WAIT            │                  │                      │      │
│   │                      │ ───── ACK ─────> │ CLOSED               │      │
│   │ (wait 2*MSL)         │                  │                      │      │
│   │         │            │                  └──────────────────────┘      │
│   │         ▼            │                                                │
│   │ CLOSED               │                                                │
│   └──────────────────────┘                                                │
│                                                                            │
│   WHY FOUR PACKETS (not 3)?                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   The ACK and FIN from the receiver CANNOT be combined because:    │ │
│   │                                                                     │ │
│   │   • FIN means "I'm done sending"                                    │ │
│   │   • But the receiver may have more data to send!                    │ │
│   │   • Receiver sends ACK immediately (acknowledging FIN)              │ │
│   │   • Receiver sends FIN later (when it's done sending)               │ │
│   │                                                                     │ │
│   │   This enables "half-close" - one direction closed while            │ │
│   │   other direction stays open.                                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### The TIME_WAIT State

Perhaps the most misunderstood TCP state:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TIME_WAIT STATE                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   TIME_WAIT lasts for 2 * MSL (Maximum Segment Lifetime)                  │
│   • Linux default MSL: 60 seconds → TIME_WAIT = 2 minutes                 │
│   • This is the ACTIVE CLOSER (who sent first FIN)                        │
│                                                                            │
│   WHY TIME_WAIT EXISTS:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Reason 1: Ensure final ACK is delivered                           │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │                                                               │ │ │
│   │   │   If our final ACK is lost:                                   │ │ │
│   │   │                                                               │ │ │
│   │   │   Client         Server                                       │ │ │
│   │   │   TIME_WAIT      LAST_ACK                                     │ │ │
│   │   │      │                │                                       │ │ │
│   │   │      │─── ACK ───X    │  (lost!)                              │ │ │
│   │   │      │                │                                       │ │ │
│   │   │      │<── FIN ────────│  (retransmit)                         │ │ │
│   │   │      │                │                                       │ │ │
│   │   │      │─── ACK ───────>│  (we can resend ACK because           │ │ │
│   │   │      │                │   we're still in TIME_WAIT!)          │ │ │
│   │   │                                                               │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   │   Reason 2: Prevent old segments from corrupting new connections   │ │
│   │   ┌───────────────────────────────────────────────────────────────┐ │ │
│   │   │                                                               │ │ │
│   │   │   If we immediately reuse the same port:                      │ │ │
│   │   │                                                               │ │ │
│   │   │   Connection 1: Client:5000 ↔ Server:80 [CLOSED]              │ │ │
│   │   │   Connection 2: Client:5000 ↔ Server:80 [NEW]                 │ │ │
│   │   │                                                               │ │ │
│   │   │   Old delayed segment from Connection 1 might arrive and      │ │ │
│   │   │   be accepted by Connection 2 (if sequence numbers match)!   │ │ │
│   │   │                                                               │ │ │
│   │   │   TIME_WAIT ensures all old segments have expired (2*MSL)     │ │ │
│   │   │                                                               │ │ │
│   │   └───────────────────────────────────────────────────────────────┘ │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE "ADDRESS ALREADY IN USE" PROBLEM:                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   // Server restarts quickly after crash                            │ │
│   │   bind(sockfd, port_8080);                                          │ │
│   │   // ERROR: Address already in use!                                 │ │
│   │                                                                     │ │
│   │   // Old socket still in TIME_WAIT state                            │ │
│   │   $ netstat -an | grep 8080                                         │ │
│   │   tcp   0   0  *.8080   10.0.0.5.54321   TIME_WAIT                  │ │
│   │                                                                     │ │
│   │   SOLUTION: SO_REUSEADDR                                            │ │
│   │   int opt = 1;                                                      │ │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)); │ │
│   │   bind(sockfd, port_8080);  // Works now!                           │ │
│   │                                                                     │ │
│   │   NOTE: SO_REUSEADDR is safe because new connection will have       │ │
│   │   different sequence numbers, so old segments won't match.          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   TIME_WAIT ACCUMULATION (busy server):                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   $ netstat -an | grep TIME_WAIT | wc -l                            │ │
│   │   35000    ← This many sockets waiting to die!                      │ │
│   │                                                                     │ │
│   │   Each TIME_WAIT socket consumes:                                   │ │
│   │   • Memory (~280 bytes in modern Linux)                             │ │
│   │   • Ephemeral port (if you were the active closer)                  │ │
│   │                                                                     │ │
│   │   Solutions:                                                         │ │
│   │   • tcp_tw_reuse: allow reusing TIME_WAIT for outgoing connections  │ │
│   │   • Let clients close first (server stays passive)                  │ │
│   │   • Use connection pooling / keep-alive                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### TCP Flow Control and Window

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    TCP FLOW CONTROL                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE SLIDING WINDOW:                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Receiver advertises: "I have X bytes of buffer space"            │ │
│   │   Sender can send up to X bytes before waiting for ACK             │ │
│   │                                                                     │ │
│   │   Sender's view:                                                    │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ Sent & ACKed │ Sent, not ACKed │ Can send │ Cannot send yet │   │ │
│   │   │  (done)      │  (in flight)    │ (window) │ (blocked)       │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                   ◄─────── Send Window ───────►                     │ │
│   │                                                                     │ │
│   │   As ACKs arrive, window "slides" right                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ZERO WINDOW (receiver full):                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Sender                               Receiver                     │ │
│   │      │                                    │                         │ │
│   │      │ ──── data ────────────────────────>│ (buffer fills up)       │ │
│   │      │ <─── ACK, window=0 ───────────────│                         │ │
│   │      │                                    │                         │ │
│   │      │ (BLOCKED - cannot send)            │ (app slowly reads)      │ │
│   │      │                                    │                         │ │
│   │      │ ─── PERSIST timer ──>              │                         │ │
│   │      │     (probe: 1 byte)                │                         │ │
│   │      │ <─── ACK, window=1000 ────────────│ (buffer drained)        │ │
│   │      │                                    │                         │ │
│   │      │ ──── data (resume) ───────────────>│                         │ │
│   │      │                                    │                         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Nagle's Algorithm

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    NAGLE'S ALGORITHM                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   PROBLEM IT SOLVES:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Interactive applications (telnet, SSH) send one byte at a time:  │ │
│   │                                                                     │ │
│   │   User types 'l': send 1 byte + 40 bytes TCP/IP headers = 41 bytes │ │
│   │   User types 's': send 1 byte + 40 bytes TCP/IP headers = 41 bytes │ │
│   │                                                                     │ │
│   │   "Silly Window Syndrome" - massive overhead for tiny data!         │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   NAGLE'S ALGORITHM (RFC 896):                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   IF there is unacknowledged data in flight:                        │ │
│   │       Buffer small segments (< MSS) instead of sending              │ │
│   │       Wait for either:                                              │ │
│   │         (a) All outstanding data is ACKed, OR                       │ │
│   │         (b) We accumulate a full segment (MSS bytes)                │ │
│   │   ELSE:                                                             │ │
│   │       Send immediately (even small segments)                        │ │
│   │                                                                     │ │
│   │   This coalesces small writes into larger segments                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE NAGLE + DELAYED ACK PROBLEM:                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   App: send(header, 100 bytes);  send(body, 1000 bytes);            │ │
│   │                                                                     │ │
│   │   Client                              Server                        │ │
│   │      │                                    │                         │ │
│   │      │ ─── header (100 bytes) ──────────>│                         │ │
│   │      │     (small, but no outstanding)    │                         │ │
│   │      │                                    │ (waiting for more data  │ │
│   │      │ body buffered (Nagle: wait        │  before ACKing -        │ │
│   │      │ for ACK of header)                │  "delayed ACK")         │ │
│   │      │                                    │                         │ │
│   │      │      ~~~ 200ms delay ~~~           │                         │ │
│   │      │                                    │                         │ │
│   │      │ <──────── ACK ────────────────────│ (delayed ACK timeout)   │ │
│   │      │ ─── body (1000 bytes) ───────────>│                         │ │
│   │      │                                    │                         │ │
│   │                                                                     │ │
│   │   200ms added latency! Both sides waiting for each other.           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOLUTIONS:                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Option 1: Disable Nagle (TCP_NODELAY)                             │ │
│   │   int flag = 1;                                                     │ │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));│ │
│   │                                                                     │ │
│   │   Option 2: Use writev() to send header+body atomically             │ │
│   │   struct iovec iov[2] = {{header, 100}, {body, 1000}};              │ │
│   │   writev(sockfd, iov, 2);  // Sends as one segment                  │ │
│   │                                                                     │ │
│   │   Option 3: TCP_CORK (Linux) - explicitly buffer                    │ │
│   │   int cork = 1;                                                     │ │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_CORK, &cork, sizeof(cork));   │ │
│   │   send(sockfd, header, ...);                                        │ │
│   │   send(sockfd, body, ...);                                          │ │
│   │   cork = 0;                                                         │ │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_CORK, &cork, sizeof(cork));   │ │
│   │   // Now it all goes out as one segment                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. UDP Sockets

UDP (User Datagram Protocol) provides connectionless, unreliable datagrams. It's simpler and faster than TCP
when you don't need reliability.

### UDP Characteristics

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UDP CHARACTERISTICS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────────────────┬──────────────────────────────────────┐  │
│   │           TCP               │              UDP                     │  │
│   ├─────────────────────────────┼──────────────────────────────────────┤  │
│   │ Connection-oriented         │ Connectionless                       │  │
│   │ Reliable delivery           │ No delivery guarantees               │  │
│   │ Ordered (in-sequence)       │ May arrive out of order              │  │
│   │ Flow control (window)       │ No flow control                      │  │
│   │ Congestion control          │ No congestion control                │  │
│   │ Byte stream (no boundaries) │ Message boundaries preserved         │  │
│   │ Heavier (20+ byte header)   │ Lighter (8 byte header)              │  │
│   │ 3-way handshake overhead    │ No handshake (just send!)            │  │
│   └─────────────────────────────┴──────────────────────────────────────┘  │
│                                                                            │
│   UDP HEADER (8 bytes only):                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │    0                   1                   2                   3    │ │
│   │    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1  │ │
│   │   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ │ │
│   │   │         Source Port         │       Destination Port        │  │ │
│   │   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ │ │
│   │   │           Length            │          Checksum             │  │ │
│   │   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ │ │
│   │   │                          Data ...                            │  │ │
│   │   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ │ │
│   │                                                                     │ │
│   │   That's it! No sequence numbers, no ACKs, no window size.          │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   WHEN TO USE UDP:                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   ✓ Real-time applications (VoIP, video streaming, gaming)         │ │
│   │     → Old data is useless, don't wait for retransmits              │ │
│   │                                                                     │ │
│   │   ✓ DNS queries                                                     │ │
│   │     → Simple request/response, app handles retries                 │ │
│   │                                                                     │ │
│   │   ✓ DHCP                                                            │ │
│   │     → No connection possible (don't have IP yet!)                   │ │
│   │                                                                     │ │
│   │   ✓ Multicast/broadcast                                             │ │
│   │     → TCP can't do one-to-many                                      │ │
│   │                                                                     │ │
│   │   ✓ When you need custom reliability                                │ │
│   │     → Build your own protocol on top (QUIC, game netcode)           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### UDP Server and Client Pattern

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UDP SERVER/CLIENT PATTERN                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   UDP SERVER:                     UDP CLIENT:                              │
│   ┌────────────────────┐          ┌────────────────────┐                  │
│   │                    │          │                    │                  │
│   │ socket(AF_INET,    │          │ socket(AF_INET,    │                  │
│   │   SOCK_DGRAM, 0)   │          │   SOCK_DGRAM, 0)   │                  │
│   │        │           │          │        │           │                  │
│   │        ▼           │          │        │           │                  │
│   │ bind(addr:port)    │          │        │ (optional)│                  │
│   │        │           │          │        │           │                  │
│   │        ▼           │          │        ▼           │                  │
│   │ recvfrom()         │ <─────── │ sendto(server_addr)│                  │
│   │   (blocks)         │          │        │           │                  │
│   │        │           │          │        ▼           │                  │
│   │        ▼           │          │ recvfrom()         │                  │
│   │ process request    │          │   (blocks for      │                  │
│   │        │           │          │    response)       │                  │
│   │        ▼           │          │        │           │                  │
│   │ sendto(client_addr)│ ───────> │        ▼           │                  │
│   │        │           │          │ process response   │                  │
│   │        ▼           │          │        │           │                  │
│   │ (loop back to      │          │        ▼           │                  │
│   │  recvfrom)         │          │ close()            │                  │
│   │                    │          │                    │                  │
│   └────────────────────┘          └────────────────────┘                  │
│                                                                            │
│   NOTE: NO listen(), NO accept()! UDP is connectionless.                  │
│                                                                            │
│   SERVER CODE:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   int sockfd = socket(AF_INET, SOCK_DGRAM, 0);                      │ │
│   │                                                                     │ │
│   │   struct sockaddr_in servaddr = {                                   │ │
│   │       .sin_family = AF_INET,                                        │ │
│   │       .sin_addr.s_addr = INADDR_ANY,                                │ │
│   │       .sin_port = htons(8080)                                       │ │
│   │   };                                                                │ │
│   │   bind(sockfd, (struct sockaddr*)&servaddr, sizeof(servaddr));      │ │
│   │                                                                     │ │
│   │   while (1) {                                                       │ │
│   │       struct sockaddr_in cliaddr;                                   │ │
│   │       socklen_t len = sizeof(cliaddr);                              │ │
│   │                                                                     │ │
│   │       // Receive request AND learn client address                   │ │
│   │       n = recvfrom(sockfd, buf, sizeof(buf), 0,                     │ │
│   │                    (struct sockaddr*)&cliaddr, &len);               │ │
│   │                                                                     │ │
│   │       // Process and send response back to THAT client             │ │
│   │       sendto(sockfd, response, resp_len, 0,                         │ │
│   │              (struct sockaddr*)&cliaddr, len);                      │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Connected UDP Sockets

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONNECTED UDP                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   You CAN call connect() on a UDP socket!                                  │
│                                                                            │
│   WHAT IT DOES:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   • Sets the default destination address                            │ │
│   │   • NO packets sent! (unlike TCP)                                   │ │
│   │   • NO handshake! (UDP doesn't have one)                            │ │
│   │   • Returns immediately                                              │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   BENEFITS:                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Can use send()/recv() instead of sendto()/recvfrom()           │ │
│   │      (simpler code, slightly faster - kernel caches route)          │ │
│   │                                                                     │ │
│   │   2. Receive ICMP errors!                                           │ │
│   │      ┌───────────────────────────────────────────────────────────┐  │ │
│   │      │                                                           │  │ │
│   │      │  Unconnected UDP:                                         │  │ │
│   │      │  sendto(sockfd, ..., server_addr);                        │  │ │
│   │      │  // If server port not listening, ICMP "port unreachable" │  │ │
│   │      │  // is received by kernel... and IGNORED (no way to       │  │ │
│   │      │  // associate with this socket!)                          │  │ │
│   │      │                                                           │  │ │
│   │      │  Connected UDP:                                           │  │ │
│   │      │  connect(sockfd, server_addr);                            │  │ │
│   │      │  send(sockfd, ...);                                       │  │ │
│   │      │  // Next recv() returns -1 with errno = ECONNREFUSED!     │  │ │
│   │      │                                                           │  │ │
│   │      └───────────────────────────────────────────────────────────┘  │ │
│   │                                                                     │ │
│   │   3. Filters incoming packets                                       │ │
│   │      Only datagrams from the connected address are delivered       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   DISCONNECT:                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   // Set address family to AF_UNSPEC to "disconnect"                │ │
│   │   struct sockaddr_in addr = { .sin_family = AF_UNSPEC };            │ │
│   │   connect(sockfd, (struct sockaddr*)&addr, sizeof(addr));           │ │
│   │   // Now back to unconnected state                                  │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Unix Domain Sockets

Unix Domain Sockets (UDS) are for inter-process communication on the **same machine**. They're faster than
TCP/UDP because they bypass the network stack.

### Unix Domain Socket Basics

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    UNIX DOMAIN SOCKETS                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ALSO KNOWN AS:                                                           │
│   • AF_UNIX sockets                                                        │
│   • AF_LOCAL sockets (same thing)                                          │
│   • IPC sockets                                                            │
│   • Local sockets                                                          │
│                                                                            │
│   WHY USE THEM:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Performance comparison (same-machine IPC):                        │ │
│   │                                                                     │ │
│   │   ┌─────────────────────────────────────────────────────────────┐   │ │
│   │   │ Method               │ Relative Speed │ Notes               │   │ │
│   │   ├──────────────────────┼────────────────┼─────────────────────┤   │ │
│   │   │ Unix Domain Socket   │ Fastest        │ No network stack    │   │ │
│   │   │ TCP loopback         │ ~2x slower     │ Full TCP processing │   │ │
│   │   │ Shared Memory        │ Even faster*   │ But no sync built-in│   │ │
│   │   │ Named Pipe (FIFO)    │ Similar to UDS │ Unidirectional only │   │ │
│   │   └─────────────────────────────────────────────────────────────┘   │ │
│   │                                                                     │ │
│   │   Unix domain sockets:                                              │ │
│   │   • No checksum calculation                                         │ │
│   │   • No routing decisions                                            │ │
│   │   • No fragmentation                                                │ │
│   │   • Direct kernel buffer-to-buffer copy                             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   ADDRESS FORMAT:                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct sockaddr_un {                                              │ │
│   │       sa_family_t sun_family;    /* AF_UNIX */                      │ │
│   │       char sun_path[108];        /* Pathname */                     │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   Two naming methods:                                               │ │
│   │                                                                     │ │
│   │   1. PATHNAME (traditional):                                        │ │
│   │      addr.sun_path = "/var/run/myapp.sock"                          │ │
│   │      • Creates file in filesystem                                   │ │
│   │      • Must unlink() before bind() if file exists                   │ │
│   │      • Subject to filesystem permissions                            │ │
│   │                                                                     │ │
│   │   2. ABSTRACT (Linux only):                                         │ │
│   │      addr.sun_path[0] = '\0';  /* First byte is NULL */             │ │
│   │      strcpy(addr.sun_path + 1, "my_socket");                        │ │
│   │      • NO filesystem entry created                                  │ │
│   │      • Automatically cleaned up when socket closes                  │ │
│   │      • Namespace isolated per network namespace                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SOCKET TYPES:                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   SOCK_STREAM:  Like TCP - connection-oriented, reliable, ordered   │ │
│   │   SOCK_DGRAM:   Like UDP - connectionless, message boundaries       │ │
│   │   SOCK_SEQPACKET: Best of both - connection + message boundaries    │ │
│   │                                                                     │ │
│   │   NOTE: Unlike UDP, SOCK_DGRAM over Unix domain IS reliable!        │ │
│   │   (No network = no packet loss)                                     │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### File Descriptor Passing (SCM_RIGHTS)

The most powerful feature of Unix domain sockets—passing open file descriptors between processes:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FILE DESCRIPTOR PASSING                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   THE PROBLEM:                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A has a file/socket open.                                 │ │
│   │   Process B wants to use it, but they're unrelated (not fork).     │ │
│   │                                                                     │ │
│   │   You CAN'T just send the fd number:                                │ │
│   │   • fd numbers are per-process                                      │ │
│   │   • Process A's fd 5 is NOT Process B's fd 5                        │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   THE SOLUTION - SCM_RIGHTS:                                               │ │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   Process A                              Process B                  │ │
│   │   ┌─────────────────┐                   ┌─────────────────┐         │ │
│   │   │ fd table:       │                   │ fd table:       │         │ │
│   │   │ 0: stdin        │                   │ 0: stdin        │         │ │
│   │   │ 1: stdout       │                   │ 1: stdout       │         │ │
│   │   │ 2: stderr       │                   │ 2: stderr       │         │ │
│   │   │ 3: unix_sock ───┼── connected to ───┼─ 3: unix_sock   │         │ │
│   │   │ 4: file.txt ────┼────── send ──────>│ 4: (empty)      │         │ │
│   │   │                 │      SCM_RIGHTS   │                 │         │ │
│   │   └─────────────────┘                   └─────────────────┘         │ │
│   │                                                                     │ │
│   │                      KERNEL MAGIC:                                  │ │
│   │                      • Looks up fd 4 in A's table                   │ │
│   │                      • Finds the kernel file structure              │ │
│   │                      • Creates NEW fd in B's table                  │ │
│   │                      • Points it to SAME kernel file                │ │
│   │                                                                     │ │
│   │   Process A                              Process B                  │ │
│   │   ┌─────────────────┐                   ┌─────────────────┐         │ │
│   │   │ fd table:       │     Kernel        │ fd table:       │         │ │
│   │   │ 4: ─────────────┼──> [struct file] <┼── 7:            │         │ │
│   │   │                 │    (file.txt)     │ (maybe diff #!) │         │ │
│   │   └─────────────────┘                   └─────────────────┘         │ │
│   │                                                                     │ │
│   │   Both processes now have access to the SAME open file!             │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   USE CASES:                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   1. Web server handing connection to worker                        │ │
│   │      Master accepts connection → passes socket fd to worker         │ │
│   │                                                                     │ │
│   │   2. Privilege separation                                           │ │
│   │      Privileged process opens file → passes fd to unprivileged      │ │
│   │                                                                     │ │
│   │   3. Container runtimes                                             │ │
│   │      Pass pre-opened fds into containers                            │ │
│   │                                                                     │ │
│   │   4. systemd socket activation                                      │ │
│   │      systemd opens socket → passes to service                       │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CODE - SENDING FD:                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   // Must use sendmsg() with control message                        │ │
│   │   struct msghdr msg = {0};                                          │ │
│   │   struct cmsghdr *cmsg;                                             │ │
│   │   char buf[CMSG_SPACE(sizeof(int))];  // Space for one fd           │ │
│   │   int fd_to_send = open("file.txt", O_RDONLY);                      │ │
│   │                                                                     │ │
│   │   // Must send at least 1 byte of real data                         │ │
│   │   char dummy = 'x';                                                 │ │
│   │   struct iovec iov = { .iov_base = &dummy, .iov_len = 1 };          │ │
│   │   msg.msg_iov = &iov;                                               │ │
│   │   msg.msg_iovlen = 1;                                               │ │
│   │                                                                     │ │
│   │   // Attach the fd as ancillary data                                │ │
│   │   msg.msg_control = buf;                                            │ │
│   │   msg.msg_controllen = sizeof(buf);                                 │ │
│   │   cmsg = CMSG_FIRSTHDR(&msg);                                       │ │
│   │   cmsg->cmsg_level = SOL_SOCKET;                                    │ │
│   │   cmsg->cmsg_type = SCM_RIGHTS;                                     │ │
│   │   cmsg->cmsg_len = CMSG_LEN(sizeof(int));                           │ │
│   │   *((int *)CMSG_DATA(cmsg)) = fd_to_send;                           │ │
│   │                                                                     │ │
│   │   sendmsg(unix_socket, &msg, 0);                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   CODE - RECEIVING FD:                                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct msghdr msg = {0};                                          │ │
│   │   struct cmsghdr *cmsg;                                             │ │
│   │   char buf[CMSG_SPACE(sizeof(int))];                                │ │
│   │   char dummy;                                                       │ │
│   │   struct iovec iov = { .iov_base = &dummy, .iov_len = 1 };          │ │
│   │                                                                     │ │
│   │   msg.msg_iov = &iov;                                               │ │
│   │   msg.msg_iovlen = 1;                                               │ │
│   │   msg.msg_control = buf;                                            │ │
│   │   msg.msg_controllen = sizeof(buf);                                 │ │
│   │                                                                     │ │
│   │   recvmsg(unix_socket, &msg, 0);                                    │ │
│   │                                                                     │ │
│   │   cmsg = CMSG_FIRSTHDR(&msg);                                       │ │
│   │   if (cmsg && cmsg->cmsg_level == SOL_SOCKET &&                     │ │
│   │       cmsg->cmsg_type == SCM_RIGHTS) {                              │ │
│   │       int received_fd = *((int *)CMSG_DATA(cmsg));                  │ │
│   │       // Now we can read/write received_fd!                         │ │
│   │   }                                                                 │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### Credential Passing (SCM_CREDENTIALS)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CREDENTIAL PASSING                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   Unix domain sockets can verify peer identity:                            │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   struct ucred {                                                    │ │
│   │       pid_t pid;    /* Process ID */                                │ │
│   │       uid_t uid;    /* User ID */                                   │ │
│   │       gid_t gid;    /* Group ID */                                  │ │
│   │   };                                                                │ │
│   │                                                                     │ │
│   │   // Enable credential passing                                      │ │
│   │   int opt = 1;                                                      │ │
│   │   setsockopt(sock, SOL_SOCKET, SO_PASSCRED, &opt, sizeof(opt));     │ │
│   │                                                                     │ │
│   │   // Credentials automatically attached to messages                 │ │
│   │   // Receive with recvmsg(), check cmsg_type == SCM_CREDENTIALS     │ │
│   │                                                                     │ │
│   │   USE CASES:                                                        │ │
│   │   • D-Bus authentication                                            │ │
│   │   • Systemd service identity verification                           │ │
│   │   • Docker socket authentication                                    │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│   SECURITY NOTE:                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐ │
│   │                                                                     │ │
│   │   The KERNEL verifies credentials - they cannot be spoofed!         │ │
│   │   (Unless you're root, who can set arbitrary credentials)           │ │
│   │                                                                     │ │
│   └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Socket Options

Socket options configure socket behavior. Set with `setsockopt()`, read with `getsockopt()`.

```c
int setsockopt(int sockfd, int level, int optname, const void *optval, socklen_t optlen);
int getsockopt(int sockfd, int level, int optname, void *optval, socklen_t *optlen);
```

### Option Levels

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SOCKET OPTION LEVELS                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌─────────────────┐                                                          │
│   │   Application   │                                                          │
│   └────────┬────────┘                                                          │
│            │                                                                   │
│            ▼                                                                   │
│   ┌─────────────────┐     SOL_SOCKET options apply here                        │
│   │  Socket Layer   │     (SO_REUSEADDR, SO_KEEPALIVE, SO_RCVBUF, etc.)        │
│   └────────┬────────┘                                                          │
│            │                                                                   │
│            ▼                                                                   │
│   ┌─────────────────┐     IPPROTO_TCP options apply here                       │
│   │   TCP Layer     │     (TCP_NODELAY, TCP_CORK, TCP_KEEPIDLE, etc.)          │
│   └────────┬────────┘                                                          │
│            │                                                                   │
│   ┌─────────────────┐     IPPROTO_IP / IPPROTO_IPV6 options apply here         │
│   │   IP Layer      │     (IP_TTL, IP_TOS, IPV6_V6ONLY, etc.)                  │
│   └────────┬────────┘                                                          │
│            │                                                                   │
│            ▼                                                                   │
│   ┌─────────────────┐                                                          │
│   │  Network I/F    │                                                          │
│   └─────────────────┘                                                          │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### SO_REUSEADDR and SO_REUSEPORT

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SO_REUSEADDR                                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   THE PROBLEM:                                                                 │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Server crashes or restarts:                                         │   │
│   │                                                                       │   │
│   │   1. Server was bound to port 8080                                    │   │
│   │   2. Server crashes (or intentionally shuts down)                     │   │
│   │   3. Socket enters TIME_WAIT state (waits 2*MSL ≈ 60 seconds)         │   │
│   │   4. Server restarts, tries to bind() to port 8080...                 │   │
│   │   5. ERROR: "Address already in use" (EADDRINUSE)                     │   │
│   │                                                                       │   │
│   │   WHY? The old socket is still in TIME_WAIT, holding the port.        │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   THE SOLUTION:                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   int opt = 1;                                                        │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));    │   │
│   │                                                                       │   │
│   │   MUST be set BEFORE bind()!                                          │   │
│   │                                                                       │   │
│   │   WHAT IT DOES:                                                       │   │
│   │   • Allows binding to address in TIME_WAIT                            │   │
│   │   • Allows binding to 0.0.0.0 even if specific IP is bound            │   │
│   │   • Does NOT allow two active sockets on same port                    │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   ALWAYS USE SO_REUSEADDR FOR SERVERS!                                         │
│                                                                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                    SO_REUSEPORT (Linux 3.9+)                                   │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   DIFFERENT from SO_REUSEADDR! Allows multiple sockets to bind same port:     │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   WITHOUT SO_REUSEPORT:              WITH SO_REUSEPORT:               │   │
│   │                                                                       │   │
│   │   ┌─────────┐                        ┌─────────┐ ┌─────────┐          │   │
│   │   │ Process │                        │ Worker1 │ │ Worker2 │ ...      │   │
│   │   └────┬────┘                        └────┬────┘ └────┬────┘          │   │
│   │        │                                  │           │               │   │
│   │        ▼                                  ▼           ▼               │   │
│   │   [ Port 80 ]                        [ Port 80 ][ Port 80 ]           │   │
│   │   One socket only                    Multiple sockets!                │   │
│   │                                      Kernel load-balances             │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   USE CASE: Multiple nginx workers accepting on same port                      │
│                                                                                │
│   int opt = 1;                                                                 │
│   setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt));             │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### SO_KEEPALIVE

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SO_KEEPALIVE                                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   PROBLEM: Detecting dead connections                                          │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Client ◄──────────────────────────────────────────► Server          │   │
│   │                        TCP Connection                                 │   │
│   │                                                                       │   │
│   │   Client's network dies (cable unplugged, crash, power loss)          │   │
│   │   NO FIN sent! Server doesn't know the connection is dead.            │   │
│   │                                                                       │   │
│   │   Server's recv() blocks FOREVER waiting for data that won't come.   │   │
│   │   Connection resources leaked.                                        │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   SOLUTION: TCP Keepalive probes                                               │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   int opt = 1;                                                        │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_KEEPALIVE, &opt, sizeof(opt));    │   │
│   │                                                                       │   │
│   │   WHAT HAPPENS:                                                       │   │
│   │                                                                       │   │
│   │   Time ─────────────────────────────────────────────────────────────> │   │
│   │                                                                       │   │
│   │   │<────── idle time ──────>│                                         │   │
│   │   Last                      First    Probe   Probe   Connection       │   │
│   │   Data                      Probe    #2      #3      declared dead    │   │
│   │    │                          │        │       │           │          │   │
│   │    ▼                          ▼        ▼       ▼           ▼          │   │
│   │   ════════════════════════════╤════════╤═══════╤═══════════╤          │   │
│   │                               │        │       │           │          │   │
│   │                              ACK?     ACK?    ACK?      No ACKs!      │   │
│   │                               │        │       │           │          │   │
│   │                               ▼        ▼       ▼           ▼          │   │
│   │                          (no response from peer)       ETIMEDOUT      │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   TUNING (Linux-specific):                                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   // Time before first probe (default: 7200 seconds = 2 hours!)       │   │
│   │   int idle = 60;  // 60 seconds                                       │   │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPIDLE, &idle, sizeof(idle)); │   │
│   │                                                                       │   │
│   │   // Interval between probes (default: 75 seconds)                    │   │
│   │   int interval = 10;  // 10 seconds                                   │   │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPINTVL, &interval, ...);     │   │
│   │                                                                       │   │
│   │   // Number of failed probes before declaring dead (default: 9)       │   │
│   │   int count = 5;                                                      │   │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPCNT, &count, sizeof(count));│   │
│   │                                                                       │   │
│   │   Total detection time = idle + (interval × count)                    │   │
│   │                        = 60 + (10 × 5) = 110 seconds                  │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### SO_RCVBUF and SO_SNDBUF

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SOCKET BUFFER SIZES                                         │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   Every socket has two buffers:                                                │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Application                                                         │   │
│   │       │                                                               │   │
│   │       │  send()                          recv()                       │   │
│   │       ▼                                    ▲                          │   │
│   │   ┌─────────────────────┐    ┌─────────────────────┐                  │   │
│   │   │   Send Buffer       │    │   Receive Buffer    │                  │   │
│   │   │   (SO_SNDBUF)       │    │   (SO_RCVBUF)       │                  │   │
│   │   │                     │    │                     │                  │   │
│   │   │  ████████░░░░░░░░░  │    │  ██████████████░░░  │                  │   │
│   │   │  ↑ data waiting     │    │  ↑ data waiting     │                  │   │
│   │   │    to be sent       │    │    to be read       │                  │   │
│   │   └─────────┬───────────┘    └─────────────────────┘                  │   │
│   │             │                          ▲                              │   │
│   │             ▼                          │                              │   │
│   │   ═══════════════════════════════════════════════ Network             │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   SETTING BUFFER SIZES:                                                        │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   int size = 256 * 1024;  // 256 KB                                   │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size));     │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size));     │   │
│   │                                                                       │   │
│   │   NOTE: Linux DOUBLES the value you set!                              │   │
│   │         (Half for data, half for kernel bookkeeping)                  │   │
│   │                                                                       │   │
│   │   LIMITS (Linux):                                                     │   │
│   │   /proc/sys/net/core/rmem_max   - max receive buffer                  │   │
│   │   /proc/sys/net/core/wmem_max   - max send buffer                     │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   WHEN TO INCREASE:                                                            │
│   • High bandwidth-delay product networks (fast, long distance)                │
│   • Large file transfers                                                       │
│   • High-throughput streaming                                                  │
│                                                                                │
│   WHEN TO DECREASE:                                                            │
│   • Many concurrent connections (save memory)                                  │
│   • Low-latency requirements (smaller buffers = less bufferbloat)              │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### TCP_NODELAY and TCP_CORK

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    NAGLE'S ALGORITHM AND TCP_NODELAY                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   NAGLE'S ALGORITHM (enabled by default):                                      │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Problem it solves: "Small packet problem"                           │   │
│   │                                                                       │   │
│   │   Telnet example - typing one character at a time:                    │   │
│   │                                                                       │   │
│   │   User types 'a':                                                     │   │
│   │   ┌────────────────────────────────────────────────┐                  │   │
│   │   │ IP Header │ TCP Header │ Payload │             │                  │   │
│   │   │  20 bytes │  20 bytes  │ 1 byte  │             │                  │   │
│   │   └────────────────────────────────────────────────┘                  │   │
│   │                                                                       │   │
│   │   41 bytes sent to transmit 1 byte of data! (4000% overhead)          │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   NAGLE'S SOLUTION:                                                            │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   if (data_to_send < MSS && unacknowledged_data_in_flight)            │   │
│   │       WAIT until:                                                     │   │
│   │         - We have MSS bytes (full segment), OR                        │   │
│   │         - All outstanding data has been ACKed                         │   │
│   │   else                                                                │   │
│   │       SEND immediately                                                │   │
│   │                                                                       │   │
│   │   Effect: Small writes are coalesced into larger packets              │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   THE PROBLEM - DELAYED ACK INTERACTION:                                       │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Nagle: "Wait for ACK before sending small packet"                   │   │
│   │   Delayed ACK: "Wait 40ms before sending ACK, hoping to piggyback"    │   │
│   │                                                                       │   │
│   │   Client                              Server                          │   │
│   │      │                                   │                            │   │
│   │      │ ── HTTP headers (small) ───────> │                            │   │
│   │      │    Nagle: "Wait for ACK for body"│                            │   │
│   │      │                                   │ Delayed ACK:               │   │
│   │      │                                   │ "Wait 40ms..."             │   │
│   │      │                                   │                            │   │
│   │      │    ~~~~ 40ms delay ~~~~           │                            │   │
│   │      │                                   │                            │   │
│   │      │ <─────────────────── ACK ──────── │                            │   │
│   │      │ ── HTTP body ──────────────────> │                            │   │
│   │      │                                   │                            │   │
│   │                                                                       │   │
│   │   Result: 40ms artificial latency on every request!                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   SOLUTION - TCP_NODELAY:                                                      │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   int opt = 1;                                                        │   │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt));    │   │
│   │                                                                       │   │
│   │   DISABLES Nagle's algorithm - send immediately, always               │   │
│   │                                                                       │   │
│   │   USE WHEN:                                                           │   │
│   │   • Interactive applications (SSH, gaming)                            │   │
│   │   • Request-response protocols (HTTP)                                 │   │
│   │   • When you're already doing your own buffering                      │   │
│   │                                                                       │   │
│   │   DON'T USE WHEN:                                                     │   │
│   │   • Bulk data transfer (let the kernel optimize)                      │   │
│   │   • Many tiny writes without your own buffering                       │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                    TCP_CORK (Linux only)                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   "Cork" the socket - NOTHING goes out until you "uncork"             │   │
│   │                                                                       │   │
│   │   // Put cork in                                                      │   │
│   │   int opt = 1;                                                        │   │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_CORK, &opt, sizeof(opt));       │   │
│   │                                                                       │   │
│   │   write(sockfd, header, header_len);    // Buffered                   │   │
│   │   sendfile(sockfd, file_fd, ...);       // Buffered                   │   │
│   │   write(sockfd, trailer, trailer_len);  // Buffered                   │   │
│   │                                                                       │   │
│   │   // Remove cork - all data sent as efficiently as possible           │   │
│   │   opt = 0;                                                            │   │
│   │   setsockopt(sockfd, IPPROTO_TCP, TCP_CORK, &opt, sizeof(opt));       │   │
│   │                                                                       │   │
│   │   USE CASE: sendfile() with headers/trailers                          │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   COMPARISON:                                                                  │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Option       │ Effect                                               │   │
│   │   ─────────────┼───────────────────────────────────────────────       │   │
│   │   Default      │ Nagle on: coalesce small, send when ACKed            │   │
│   │   TCP_NODELAY  │ Nagle off: send immediately, always                  │   │
│   │   TCP_CORK     │ Full stop: don't send until uncorked                 │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### SO_LINGER

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SO_LINGER - CONTROLLING close() BEHAVIOR                    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   WHAT HAPPENS ON close()?                                                     │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   DEFAULT (SO_LINGER disabled):                                       │   │
│   │                                                                       │   │
│   │   close(sockfd)                                                       │   │
│   │       │                                                               │   │
│   │       ├─ Returns immediately                                          │   │
│   │       │                                                               │   │
│   │       └─ Kernel handles remaining data in background:                 │   │
│   │          - Tries to send buffered data                                │   │
│   │          - Sends FIN                                                  │   │
│   │          - Waits for peer's FIN                                       │   │
│   │          - Enters TIME_WAIT                                           │   │
│   │                                                                       │   │
│   │   PROBLEM: No way to know if data was actually delivered!             │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   SO_LINGER SETTINGS:                                                          │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   struct linger {                                                     │   │
│   │       int l_onoff;   /* 0 = disabled, non-0 = enabled */              │   │
│   │       int l_linger;  /* timeout in seconds */                         │   │
│   │   };                                                                  │   │
│   │                                                                       │   │
│   │   THREE MODES:                                                        │   │
│   │                                                                       │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐ │   │
│   │   │ l_onoff │ l_linger │ Behavior                                  │ │   │
│   │   ├─────────┼──────────┼───────────────────────────────────────────┤ │   │
│   │   │    0    │  (any)   │ DEFAULT: close returns immediately       │ │   │
│   │   │         │          │ kernel sends data in background          │ │   │
│   │   ├─────────┼──────────┼───────────────────────────────────────────┤ │   │
│   │   │   ≠0    │    0     │ HARD CLOSE: close returns immediately    │ │   │
│   │   │         │          │ RST sent, data discarded! (no TIME_WAIT) │ │   │
│   │   ├─────────┼──────────┼───────────────────────────────────────────┤ │   │
│   │   │   ≠0    │   >0     │ GRACEFUL: close BLOCKS up to l_linger    │ │   │
│   │   │         │          │ seconds waiting for data to be sent      │ │   │
│   │   └─────────┴──────────┴───────────────────────────────────────────┘ │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   EXAMPLES:                                                                    │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   // Hard close - RST, no TIME_WAIT                                   │   │
│   │   struct linger ling = { .l_onoff = 1, .l_linger = 0 };               │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_LINGER, &ling, sizeof(ling));     │   │
│   │   close(sockfd);  // Sends RST immediately                            │   │
│   │                                                                       │   │
│   │   // Graceful - wait up to 30 seconds for data to be sent             │   │
│   │   struct linger ling = { .l_onoff = 1, .l_linger = 30 };              │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_LINGER, &ling, sizeof(ling));     │   │
│   │   close(sockfd);  // Blocks up to 30 seconds                          │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   WARNING:                                                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Using l_linger = 0 (RST) is usually a BAD IDEA because:             │   │
│   │   • Violates TCP spec (abortive close)                                │   │
│   │   • Data may be lost                                                  │   │
│   │   • Peer gets ECONNRESET instead of clean EOF                         │   │
│   │                                                                       │   │
│   │   Legitimate uses:                                                    │   │
│   │   • Deliberately aborting connection                                  │   │
│   │   • Avoiding TIME_WAIT on servers with many short connections         │   │
│   │   • Testing error handling                                            │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Socket Buffers and Kernel Internals

This section explores how data flows through the kernel's network stack.

### The sk_buff Structure

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    sk_buff - THE NETWORK PACKET                                │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   Every network packet in Linux is represented by struct sk_buff ("socket     │
│   buffer" or "skb"). It's the fundamental data structure of the network       │
│   stack.                                                                       │
│                                                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   struct sk_buff (simplified):                                        │   │
│   │                                                                       │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐ │   │
│   │   │ struct sk_buff {                                                │ │   │
│   │   │     struct sk_buff *next, *prev;  /* Queue linkage */           │ │   │
│   │   │     struct sock *sk;              /* Owning socket */           │ │   │
│   │   │     struct net_device *dev;       /* Network device */          │ │   │
│   │   │                                                                 │ │   │
│   │   │     /* Packet data pointers */                                  │ │   │
│   │   │     unsigned char *head;          /* Start of buffer */         │ │   │
│   │   │     unsigned char *data;          /* Start of actual data */    │ │   │
│   │   │     unsigned char *tail;          /* End of actual data */      │ │   │
│   │   │     unsigned char *end;           /* End of buffer */           │ │   │
│   │   │                                                                 │ │   │
│   │   │     /* Layer pointers */                                        │ │   │
│   │   │     union { struct tcphdr *th; struct udphdr *uh; ... };        │ │   │
│   │   │     union { struct iphdr *iph; struct ipv6hdr *ipv6h; ... };    │ │   │
│   │   │                                                                 │ │   │
│   │   │     unsigned int len;             /* Packet length */           │ │   │
│   │   │     unsigned int data_len;        /* Paged data length */       │ │   │
│   │   │ };                                                              │ │   │
│   │   └─────────────────────────────────────────────────────────────────┘ │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   MEMORY LAYOUT:                                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   head                data                tail               end      │   │
│   │     │                  │                   │                  │       │   │
│   │     ▼                  ▼                   ▼                  ▼       │   │
│   │     ┌──────────────────┬───────────────────┬──────────────────┐       │   │
│   │     │    headroom      │   actual data     │    tailroom      │       │   │
│   │     │   (for headers)  │                   │  (for trailers)  │       │   │
│   │     └──────────────────┴───────────────────┴──────────────────┘       │   │
│   │                                                                       │   │
│   │   WHY HEADROOM/TAILROOM?                                              │   │
│   │   • Prepend headers without copying (Ethernet, IP, TCP headers)       │   │
│   │   • Append trailers without copying                                   │   │
│   │   • skb_push() adds to front, skb_put() adds to back                  │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: send() to Wire

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SEND PATH - APPLICATION TO NETWORK                          │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐ │
│   │                                                                         │ │
│   │   Application:   send(sockfd, buffer, len, 0);                          │ │
│   │                           │                                             │ │
│   │                           ▼                                             │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ SYSTEM CALL LAYER                                               │   │ │
│   │   │ sys_sendto() → sock_sendmsg()                                   │   │ │
│   │   │ • Copy data from user space                                     │   │ │
│   │   │ • Check socket state                                            │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ SOCKET LAYER                                                    │   │ │
│   │   │ inet_sendmsg()                                                  │   │ │
│   │   │ • Route to appropriate protocol                                 │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ TCP LAYER                                                       │   │ │
│   │   │ tcp_sendmsg()                                                   │   │ │
│   │   │ • Copy data to socket send buffer                               │   │ │
│   │   │ • Segment data into MSS-sized chunks                            │   │ │
│   │   │ • Apply Nagle's algorithm                                       │   │ │
│   │   │ • Create sk_buff for each segment                               │   │ │
│   │   │ • Add TCP header                                                │   │ │
│   │   │ • Queue to retransmit queue                                     │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ IP LAYER                                                        │   │ │
│   │   │ ip_queue_xmit()                                                 │   │ │
│   │   │ • Add IP header                                                 │   │ │
│   │   │ • Route lookup                                                  │   │ │
│   │   │ • Fragment if needed (usually avoided by path MTU discovery)    │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ DEVICE LAYER                                                    │   │ │
│   │   │ dev_queue_xmit()                                                │   │ │
│   │   │ • Add Ethernet header                                           │   │ │
│   │   │ • Queue to device's transmit queue                              │   │ │
│   │   │ • Qdisc (traffic control)                                       │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ DRIVER                                                          │   │ │
│   │   │ ndo_start_xmit()                                                │   │ │
│   │   │ • DMA to NIC ring buffer                                        │   │ │
│   │   │ • Signal NIC to transmit                                        │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │                         [ WIRE ]                                        │ │
│   │                                                                         │ │
│   └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Wire to recv()

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    RECEIVE PATH - NETWORK TO APPLICATION                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐ │
│   │                                                                         │ │
│   │                         [ WIRE ]                                        │ │
│   │                              │                                          │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ NIC HARDWARE                                                    │   │ │
│   │   │ • DMA packet to ring buffer                                     │   │ │
│   │   │ • Raise interrupt (or NAPI poll)                                │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ DRIVER / NAPI                                                   │   │ │
│   │   │ • Allocate sk_buff                                              │   │ │
│   │   │ • Copy packet to sk_buff (or use DMA mapping)                   │   │ │
│   │   │ • netif_receive_skb()                                           │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ DEVICE LAYER                                                    │   │ │
│   │   │ • Strip Ethernet header                                         │   │ │
│   │   │ • Determine protocol (ETH_P_IP, etc.)                           │   │ │
│   │   │ • Deliver to ip_rcv()                                           │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ IP LAYER                                                        │   │ │
│   │   │ ip_rcv() → ip_local_deliver()                                   │   │ │
│   │   │ • Validate IP header, checksum                                  │   │ │
│   │   │ • Defragment if needed                                          │   │ │
│   │   │ • Route to TCP/UDP based on protocol field                      │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ TCP LAYER                                                       │   │ │
│   │   │ tcp_v4_rcv()                                                    │   │ │
│   │   │ • Validate TCP checksum                                         │   │ │
│   │   │ • Find socket by 4-tuple (src_ip:src_port, dst_ip:dst_port)     │   │ │
│   │   │ • Handle state machine (SYN, ACK, FIN, etc.)                    │   │ │
│   │   │ • Queue data to socket receive buffer                           │   │ │
│   │   │ • Wake up waiting process                                       │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │   │ SOCKET LAYER                                                    │   │ │
│   │   │ sk->sk_data_ready() callback                                    │   │ │
│   │   │ • Wake process blocked in recv()/poll()/epoll()                 │   │ │
│   │   └──────────────────────────┬──────────────────────────────────────┘   │ │
│   │                              ▼                                          │ │
│   │   Application:   recv(sockfd, buffer, len, 0);                          │ │
│   │                   • Copy data from kernel to user buffer                │ │
│   │                   • Remove data from socket receive buffer              │ │
│   │                                                                         │ │
│   └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Advanced Topics

### Raw Sockets

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    RAW SOCKETS                                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   Raw sockets bypass the transport layer (TCP/UDP), giving direct access      │
│   to the IP layer (or lower).                                                 │
│                                                                                │
│   CREATING A RAW SOCKET:                                                       │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   // Raw IP socket - receive all IP packets of a protocol            │   │
│   │   int sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);               │   │
│   │                                                                       │   │
│   │   // Raw socket with IP header control                                │   │
│   │   int on = 1;                                                         │   │
│   │   setsockopt(sockfd, IPPROTO_IP, IP_HDRINCL, &on, sizeof(on));        │   │
│   │   // Now YOU must construct the IP header!                            │   │
│   │                                                                       │   │
│   │   REQUIRES: CAP_NET_RAW capability (or root)                          │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   USE CASES:                                                                   │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   • ping - Sends ICMP echo requests                                   │   │
│   │   • traceroute - Manipulates IP TTL                                   │   │
│   │   • Network scanners (nmap) - Custom packet crafting                  │   │
│   │   • Protocol implementations - Implementing new protocols             │   │
│   │   • Network debugging - Packet sniffing                               │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   PACKET SOCKET (even lower level):                                            │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   // Capture all packets at the link layer (like tcpdump)             │   │
│   │   int sockfd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));         │   │
│   │                                                                       │   │
│   │   // You receive ENTIRE frames, including Ethernet header!            │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Multicast and Broadcast

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    MULTICAST AND BROADCAST                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   COMPARISON:                                                                  │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Unicast:    One sender  →  One receiver                             │   │
│   │   Broadcast:  One sender  →  ALL on network                           │   │
│   │   Multicast:  One sender  →  Subscribed receivers                     │   │
│   │                                                                       │   │
│   │   ┌───────────┐      Unicast       ┌───────────┐                      │   │
│   │   │  Sender   │ ──────────────────>│ Receiver  │                      │   │
│   │   └───────────┘                    └───────────┘                      │   │
│   │                                                                       │   │
│   │   ┌───────────┐     Broadcast      ┌───────────┐                      │   │
│   │   │  Sender   │ ─────┬─────────────>│ Receiver 1│                      │   │
│   │   └───────────┘      ├─────────────>│ Receiver 2│                      │   │
│   │                      └─────────────>│ Receiver 3│                      │   │
│   │                   (all hosts)       └───────────┘                      │   │
│   │                                                                       │   │
│   │   ┌───────────┐     Multicast      ┌───────────┐                      │   │
│   │   │  Sender   │ ─────┬─────────────>│ Subscribed│                      │   │
│   │   └───────────┘      └─────────────>│ Subscribed│                      │   │
│   │                   (only members)          X       Not subscribed      │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   BROADCAST:                                                                   │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   // Enable broadcast on socket                                       │   │
│   │   int opt = 1;                                                        │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &opt, sizeof(opt));    │   │
│   │                                                                       │   │
│   │   // Send to broadcast address                                        │   │
│   │   struct sockaddr_in addr = {                                         │   │
│   │       .sin_family = AF_INET,                                          │   │
│   │       .sin_addr.s_addr = inet_addr("255.255.255.255"),  // or         │   │
│   │       .sin_addr.s_addr = inet_addr("192.168.1.255"),    // subnet     │   │
│   │       .sin_port = htons(12345)                                        │   │
│   │   };                                                                  │   │
│   │   sendto(sockfd, msg, len, 0, (struct sockaddr*)&addr, sizeof(addr)); │   │
│   │                                                                       │   │
│   │   NOTE: Broadcast only works on local network (not routed)            │   │
│   │         UDP only (no TCP broadcast)                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   MULTICAST:                                                                   │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   Multicast addresses: 224.0.0.0 - 239.255.255.255                    │   │
│   │                                                                       │   │
│   │   SENDING:                                                            │   │
│   │   // Just send to a multicast address - no special setup!             │   │
│   │   struct sockaddr_in addr = {                                         │   │
│   │       .sin_family = AF_INET,                                          │   │
│   │       .sin_addr.s_addr = inet_addr("239.1.2.3"),                      │   │
│   │       .sin_port = htons(12345)                                        │   │
│   │   };                                                                  │   │
│   │   sendto(sockfd, msg, len, 0, (struct sockaddr*)&addr, sizeof(addr)); │   │
│   │                                                                       │   │
│   │   RECEIVING (must join the group):                                    │   │
│   │   struct ip_mreq mreq = {                                             │   │
│   │       .imr_multiaddr.s_addr = inet_addr("239.1.2.3"),                 │   │
│   │       .imr_interface.s_addr = INADDR_ANY                              │   │
│   │   };                                                                  │   │
│   │   setsockopt(sockfd, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, ...);      │   │
│   │                                                                       │   │
│   │   // When done:                                                       │   │
│   │   setsockopt(sockfd, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq, ...);     │   │
│   │                                                                       │   │
│   │   USE CASES:                                                          │   │
│   │   • Service discovery (mDNS uses 224.0.0.251)                         │   │
│   │   • Streaming video/audio                                             │   │
│   │   • Stock market data feeds                                           │   │
│   │   • Multiplayer games                                                 │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Socket Timeouts

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SOCKET TIMEOUTS                                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   THREE WAYS TO SET TIMEOUTS:                                                  │
│                                                                                │
│   1. SO_RCVTIMEO / SO_SNDTIMEO:                                                │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };  // 5 seconds    │   │
│   │                                                                       │   │
│   │   // Receive timeout                                                  │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));       │   │
│   │                                                                       │   │
│   │   // Send timeout (for blocking writes)                               │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));       │   │
│   │                                                                       │   │
│   │   // Now recv() will return -1 with errno=EAGAIN after 5 seconds      │   │
│   │   n = recv(sockfd, buf, sizeof(buf), 0);                              │   │
│   │   if (n == -1 && (errno == EAGAIN || errno == EWOULDBLOCK)) {         │   │
│   │       // Timeout!                                                     │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   2. select()/poll() with timeout:                                             │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };                  │   │
│   │   fd_set readfds;                                                     │   │
│   │   FD_ZERO(&readfds);                                                  │   │
│   │   FD_SET(sockfd, &readfds);                                           │   │
│   │                                                                       │   │
│   │   int ret = select(sockfd + 1, &readfds, NULL, NULL, &tv);            │   │
│   │   if (ret == 0) {                                                     │   │
│   │       // Timeout!                                                     │   │
│   │   } else if (ret > 0) {                                               │   │
│   │       recv(sockfd, ...);  // Data available                           │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   3. Non-blocking + poll (recommended for complex apps):                       │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   fcntl(sockfd, F_SETFL, O_NONBLOCK);                                 │   │
│   │                                                                       │   │
│   │   struct pollfd pfd = { .fd = sockfd, .events = POLLIN };             │   │
│   │   int ret = poll(&pfd, 1, 5000);  // 5000ms timeout                   │   │
│   │                                                                       │   │
│   │   if (ret == 0) {                                                     │   │
│   │       // Timeout!                                                     │   │
│   │   } else if (pfd.revents & POLLIN) {                                  │   │
│   │       recv(sockfd, ...);                                              │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   CONNECT TIMEOUT (special case):                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   // SO_SNDTIMEO does NOT affect connect()!                           │   │
│   │   // Must use non-blocking connect:                                   │   │
│   │                                                                       │   │
│   │   fcntl(sockfd, F_SETFL, O_NONBLOCK);                                 │   │
│   │   int ret = connect(sockfd, ...);                                     │   │
│   │   // Returns immediately with -1, errno=EINPROGRESS                   │   │
│   │                                                                       │   │
│   │   struct pollfd pfd = { .fd = sockfd, .events = POLLOUT };            │   │
│   │   poll(&pfd, 1, 5000);  // Wait up to 5 seconds                       │   │
│   │                                                                       │   │
│   │   // Check if connected:                                              │   │
│   │   int error;                                                          │   │
│   │   socklen_t len = sizeof(error);                                      │   │
│   │   getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &error, &len);             │   │
│   │   if (error != 0) {                                                   │   │
│   │       // Connection failed                                            │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Practical Implementation

### Complete TCP Server

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE TCP SERVER EXAMPLE                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   #include <stdio.h>                                                           │
│   #include <stdlib.h>                                                          │
│   #include <string.h>                                                          │
│   #include <unistd.h>                                                          │
│   #include <errno.h>                                                           │
│   #include <sys/socket.h>                                                      │
│   #include <netinet/in.h>                                                      │
│   #include <arpa/inet.h>                                                       │
│                                                                                │
│   #define PORT 8080                                                            │
│   #define BACKLOG 128                                                          │
│   #define BUFFER_SIZE 4096                                                     │
│                                                                                │
│   int main(void) {                                                             │
│       int listenfd, connfd;                                                    │
│       struct sockaddr_in servaddr, cliaddr;                                    │
│       socklen_t clilen;                                                        │
│       char buffer[BUFFER_SIZE];                                                │
│       ssize_t n;                                                               │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 1: Create socket                                            */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       listenfd = socket(AF_INET, SOCK_STREAM, 0);                              │
│       if (listenfd < 0) {                                                      │
│           perror("socket");                                                    │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 2: Set SO_REUSEADDR (critical for restart)                  */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       int opt = 1;                                                             │
│       if (setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR,                       │
│                      &opt, sizeof(opt)) < 0) {                                 │
│           perror("setsockopt");                                                │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 3: Bind to address                                          */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       memset(&servaddr, 0, sizeof(servaddr));                                  │
│       servaddr.sin_family = AF_INET;                                           │
│       servaddr.sin_addr.s_addr = htonl(INADDR_ANY);  /* All interfaces */      │
│       servaddr.sin_port = htons(PORT);                                         │
│                                                                                │
│       if (bind(listenfd, (struct sockaddr *)&servaddr,                         │
│                sizeof(servaddr)) < 0) {                                        │
│           perror("bind");                                                      │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 4: Listen                                                   */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       if (listen(listenfd, BACKLOG) < 0) {                                     │
│           perror("listen");                                                    │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│       printf("Server listening on port %d\n", PORT);                           │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 5: Accept loop                                              */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       for (;;) {                                                               │
│           clilen = sizeof(cliaddr);                                            │
│           connfd = accept(listenfd, (struct sockaddr *)&cliaddr, &clilen);     │
│           if (connfd < 0) {                                                    │
│               if (errno == EINTR) continue;  /* Interrupted, retry */          │
│               perror("accept");                                                │
│               continue;                                                        │
│           }                                                                    │
│                                                                                │
│           printf("Connection from %s:%d\n",                                    │
│                  inet_ntoa(cliaddr.sin_addr), ntohs(cliaddr.sin_port));        │
│                                                                                │
│           /* Handle client (simple echo) */                                    │
│           while ((n = recv(connfd, buffer, sizeof(buffer), 0)) > 0) {          │
│               if (send(connfd, buffer, n, 0) != n) {                           │
│                   perror("send");                                              │
│                   break;                                                       │
│               }                                                                │
│           }                                                                    │
│                                                                                │
│           close(connfd);                                                       │
│           printf("Client disconnected\n");                                     │
│       }                                                                        │
│                                                                                │
│       return 0;                                                                │
│   }                                                                            │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Complete TCP Client

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE TCP CLIENT EXAMPLE                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   #include <stdio.h>                                                           │
│   #include <stdlib.h>                                                          │
│   #include <string.h>                                                          │
│   #include <unistd.h>                                                          │
│   #include <sys/socket.h>                                                      │
│   #include <netinet/in.h>                                                      │
│   #include <arpa/inet.h>                                                       │
│                                                                                │
│   #define SERVER_IP "127.0.0.1"                                                │
│   #define SERVER_PORT 8080                                                     │
│   #define BUFFER_SIZE 4096                                                     │
│                                                                                │
│   int main(void) {                                                             │
│       int sockfd;                                                              │
│       struct sockaddr_in servaddr;                                             │
│       char buffer[BUFFER_SIZE];                                                │
│       ssize_t n;                                                               │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 1: Create socket                                            */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       sockfd = socket(AF_INET, SOCK_STREAM, 0);                                │
│       if (sockfd < 0) {                                                        │
│           perror("socket");                                                    │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 2: Connect to server                                        */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       memset(&servaddr, 0, sizeof(servaddr));                                  │
│       servaddr.sin_family = AF_INET;                                           │
│       servaddr.sin_port = htons(SERVER_PORT);                                  │
│                                                                                │
│       if (inet_pton(AF_INET, SERVER_IP, &servaddr.sin_addr) <= 0) {            │
│           fprintf(stderr, "Invalid address: %s\n", SERVER_IP);                 │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│                                                                                │
│       if (connect(sockfd, (struct sockaddr *)&servaddr,                        │
│                   sizeof(servaddr)) < 0) {                                     │
│           perror("connect");                                                   │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│       printf("Connected to %s:%d\n", SERVER_IP, SERVER_PORT);                  │
│                                                                                │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       /* STEP 3: Send and receive data                                    */   │
│       /* ═══════════════════════════════════════════════════════════════ */   │
│       const char *msg = "Hello, Server!";                                      │
│       if (send(sockfd, msg, strlen(msg), 0) < 0) {                             │
│           perror("send");                                                      │
│           exit(EXIT_FAILURE);                                                  │
│       }                                                                        │
│                                                                                │
│       n = recv(sockfd, buffer, sizeof(buffer) - 1, 0);                         │
│       if (n > 0) {                                                             │
│           buffer[n] = '\0';                                                    │
│           printf("Received: %s\n", buffer);                                    │
│       }                                                                        │
│                                                                                │
│       close(sockfd);                                                           │
│       return 0;                                                                │
│   }                                                                            │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Error Handling Patterns

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING PATTERNS                                     │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ROBUST recv() LOOP:                                                          │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   ssize_t recv_all(int sockfd, void *buf, size_t len) {               │   │
│   │       size_t total = 0;                                               │   │
│   │       char *p = buf;                                                  │   │
│   │                                                                       │   │
│   │       while (total < len) {                                           │   │
│   │           ssize_t n = recv(sockfd, p + total, len - total, 0);        │   │
│   │                                                                       │   │
│   │           if (n == 0) {                                               │   │
│   │               /* Connection closed by peer */                         │   │
│   │               return total;  /* Return what we got */                 │   │
│   │           }                                                           │   │
│   │           if (n < 0) {                                                │   │
│   │               if (errno == EINTR) continue;  /* Interrupted */        │   │
│   │               if (errno == EAGAIN) continue; /* Non-blocking */       │   │
│   │               return -1;  /* Real error */                            │   │
│   │           }                                                           │   │
│   │           total += n;                                                 │   │
│   │       }                                                               │   │
│   │       return total;                                                   │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   ROBUST send() LOOP:                                                          │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   ssize_t send_all(int sockfd, const void *buf, size_t len) {         │   │
│   │       size_t total = 0;                                               │   │
│   │       const char *p = buf;                                            │   │
│   │                                                                       │   │
│   │       while (total < len) {                                           │   │
│   │           ssize_t n = send(sockfd, p + total, len - total, 0);        │   │
│   │                                                                       │   │
│   │           if (n < 0) {                                                │   │
│   │               if (errno == EINTR) continue;                           │   │
│   │               if (errno == EAGAIN) continue;                          │   │
│   │               return -1;                                              │   │
│   │           }                                                           │   │
│   │           total += n;                                                 │   │
│   │       }                                                               │   │
│   │       return total;                                                   │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   HANDLING SIGPIPE:                                                            │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   /* Problem: Writing to a closed connection sends SIGPIPE (crash!) */│   │
│   │                                                                       │   │
│   │   /* Solution 1: Ignore SIGPIPE globally */                           │   │
│   │   signal(SIGPIPE, SIG_IGN);                                           │   │
│   │   /* Now send() returns -1 with errno=EPIPE instead of killing us */  │   │
│   │                                                                       │   │
│   │   /* Solution 2: Use MSG_NOSIGNAL flag (Linux) */                     │   │
│   │   send(sockfd, buf, len, MSG_NOSIGNAL);                               │   │
│   │                                                                       │   │
│   │   /* Solution 3: Use SO_NOSIGPIPE option (macOS/BSD) */               │   │
│   │   int opt = 1;                                                        │   │
│   │   setsockopt(sockfd, SOL_SOCKET, SO_NOSIGPIPE, &opt, sizeof(opt));    │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Common Pitfalls

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    COMMON PITFALLS AND HOW TO AVOID THEM                       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   PITFALL 1: Assuming recv() returns exactly what was sent                     │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   WRONG:                                                              │   │
│   │   send(sock, "Hello World!", 12, 0);    /* Sender */                  │   │
│   │   recv(sock, buf, 12, 0);               /* Receiver: might get 5! */  │   │
│   │                                                                       │   │
│   │   WHY: TCP is a BYTE STREAM, not message-oriented.                    │   │
│   │        recv() may return partial data.                                │   │
│   │                                                                       │   │
│   │   FIX: Use a recv_all() loop, or implement message framing:           │   │
│   │        • Length prefix: send length first, then data                  │   │
│   │        • Delimiter: newline-separated messages                        │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   PITFALL 2: Forgetting SO_REUSEADDR                                           │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   SYMPTOM: "Address already in use" when restarting server            │   │
│   │                                                                       │   │
│   │   WHY: Previous socket is in TIME_WAIT state (up to 2-4 minutes)      │   │
│   │                                                                       │   │
│   │   FIX: Always set SO_REUSEADDR before bind():                         │   │
│   │        int opt = 1;                                                   │   │
│   │        setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)); │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   PITFALL 3: Not handling partial sends                                        │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   WRONG:                                                              │   │
│   │   send(sock, buffer, 100000, 0);  /* May only send 65536! */          │   │
│   │                                                                       │   │
│   │   WHY: Send buffer might be full, or kernel limits apply.             │   │
│   │        send() returns how many bytes were actually sent.              │   │
│   │                                                                       │   │
│   │   FIX: Use send_all() loop to ensure all data is sent.                │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   PITFALL 4: Blocking accept() preventing graceful shutdown                    │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   PROBLEM: accept() blocks forever, can't check shutdown flag         │   │
│   │                                                                       │   │
│   │   FIX 1: Use poll() with timeout before accept()                      │   │
│   │   struct pollfd pfd = { .fd = listenfd, .events = POLLIN };           │   │
│   │   while (!shutdown_flag) {                                            │   │
│   │       if (poll(&pfd, 1, 1000) > 0) {                                  │   │
│   │           connfd = accept(listenfd, ...);                             │   │
│   │       }                                                               │   │
│   │   }                                                                   │   │
│   │                                                                       │   │
│   │   FIX 2: Use self-pipe trick or eventfd                               │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   PITFALL 5: Not checking recv() return value                                  │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   WRONG:                                                              │   │
│   │   recv(sock, buf, len, 0);                                            │   │
│   │   process(buf);  /* buf might be garbage! */                          │   │
│   │                                                                       │   │
│   │   RETURN VALUES:                                                      │   │
│   │   • n > 0:  Success, n bytes received                                 │   │
│   │   • n == 0: Connection closed by peer (MUST handle!)                  │   │
│   │   • n < 0:  Error (check errno)                                       │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│   PITFALL 6: Byte order (endianness)                                           │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │                                                                       │   │
│   │   WRONG:                                                              │   │
│   │   addr.sin_port = 8080;       /* Might be wrong byte order! */        │   │
│   │                                                                       │   │
│   │   FIX: Always use conversion functions:                               │   │
│   │   • htons() - Host TO Network Short (16-bit)                          │   │
│   │   • htonl() - Host TO Network Long (32-bit)                           │   │
│   │   • ntohs() - Network TO Host Short                                   │   │
│   │   • ntohl() - Network TO Host Long                                    │   │
│   │                                                                       │   │
│   │   addr.sin_port = htons(8080);  /* Correct! */                        │   │
│   │                                                                       │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Summary and Appendix

### Socket System Call Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SOCKET SYSTEM CALL QUICK REFERENCE                          │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   CREATION AND SETUP:                                                          │
│   ┌────────────────────┬─────────────────────────────────────────────────────┐│
│   │ socket()           │ Create a new socket                                 ││
│   │ bind()             │ Assign local address to socket                      ││
│   │ listen()           │ Mark socket as passive (server)                     ││
│   │ accept()           │ Accept incoming connection, return new socket       ││
│   │ connect()          │ Establish connection to remote address              ││
│   └────────────────────┴─────────────────────────────────────────────────────┘│
│                                                                                │
│   DATA TRANSFER:                                                               │
│   ┌────────────────────┬─────────────────────────────────────────────────────┐│
│   │ send()             │ Send data on connected socket                       ││
│   │ recv()             │ Receive data from connected socket                  ││
│   │ sendto()           │ Send data to specific address (UDP)                 ││
│   │ recvfrom()         │ Receive data and get sender address (UDP)           ││
│   │ sendmsg()          │ Send with advanced options (scatter-gather, cmsg)   ││
│   │ recvmsg()          │ Receive with advanced options                       ││
│   │ write()            │ Alias for send() with flags=0                       ││
│   │ read()             │ Alias for recv() with flags=0                       ││
│   └────────────────────┴─────────────────────────────────────────────────────┘│
│                                                                                │
│   CLOSING:                                                                     │
│   ┌────────────────────┬─────────────────────────────────────────────────────┐│
│   │ close()            │ Close socket, release resources                     ││
│   │ shutdown()         │ Disable reads, writes, or both (graceful)           ││
│   └────────────────────┴─────────────────────────────────────────────────────┘│
│                                                                                │
│   OPTIONS AND INFO:                                                            │
│   ┌────────────────────┬─────────────────────────────────────────────────────┐│
│   │ setsockopt()       │ Set socket option                                   ││
│   │ getsockopt()       │ Get socket option                                   ││
│   │ getsockname()      │ Get local address of socket                         ││
│   │ getpeername()      │ Get remote address of connected socket              ││
│   │ fcntl()            │ Set O_NONBLOCK, O_ASYNC, etc.                       ││
│   │ ioctl()            │ Various socket I/O controls                         ││
│   └────────────────────┴─────────────────────────────────────────────────────┘│
│                                                                                │
│   I/O MULTIPLEXING:                                                            │
│   ┌────────────────────┬─────────────────────────────────────────────────────┐│
│   │ select()           │ Wait for events on multiple fds (oldest)            ││
│   │ poll()             │ Wait for events on multiple fds (portable)          ││
│   │ epoll_*()          │ Scalable I/O event notification (Linux)             ││
│   │ kqueue()           │ Scalable I/O event notification (BSD/macOS)         ││
│   └────────────────────┴─────────────────────────────────────────────────────┘│
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Socket Options Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    SOCKET OPTIONS QUICK REFERENCE                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   SOL_SOCKET LEVEL:                                                            │
│   ┌───────────────────┬───────────────────────────────────────────────────────┐│
│   │ SO_REUSEADDR      │ Allow bind to TIME_WAIT address                       ││
│   │ SO_REUSEPORT      │ Allow multiple sockets to bind same port             ││
│   │ SO_KEEPALIVE      │ Enable TCP keepalive probes                          ││
│   │ SO_RCVBUF         │ Set receive buffer size                              ││
│   │ SO_SNDBUF         │ Set send buffer size                                 ││
│   │ SO_RCVTIMEO       │ Set receive timeout                                  ││
│   │ SO_SNDTIMEO       │ Set send timeout                                     ││
│   │ SO_LINGER         │ Control close() behavior                             ││
│   │ SO_BROADCAST      │ Allow sending to broadcast addresses                 ││
│   │ SO_ERROR          │ Get and clear pending error                          ││
│   │ SO_TYPE           │ Get socket type (SOCK_STREAM, etc.)                  ││
│   │ SO_ACCEPTCONN     │ Is socket listening?                                 ││
│   └───────────────────┴───────────────────────────────────────────────────────┘│
│                                                                                │
│   IPPROTO_TCP LEVEL:                                                           │
│   ┌───────────────────┬───────────────────────────────────────────────────────┐│
│   │ TCP_NODELAY       │ Disable Nagle's algorithm                            ││
│   │ TCP_CORK          │ Cork output until uncorked (Linux)                   ││
│   │ TCP_KEEPIDLE      │ Seconds before first keepalive probe                 ││
│   │ TCP_KEEPINTVL     │ Seconds between keepalive probes                     ││
│   │ TCP_KEEPCNT       │ Number of keepalive probes before giving up          ││
│   │ TCP_QUICKACK      │ Disable delayed ACK (Linux)                          ││
│   │ TCP_FASTOPEN      │ Enable TCP Fast Open                                 ││
│   └───────────────────┴───────────────────────────────────────────────────────┘│
│                                                                                │
│   IPPROTO_IP LEVEL:                                                            │
│   ┌───────────────────┬───────────────────────────────────────────────────────┐│
│   │ IP_TTL            │ Set time-to-live                                     ││
│   │ IP_TOS            │ Set type of service                                  ││
│   │ IP_HDRINCL        │ Include IP header in raw socket                      ││
│   │ IP_ADD_MEMBERSHIP │ Join multicast group                                 ││
│   │ IP_DROP_MEMBERSHIP│ Leave multicast group                                ││
│   │ IP_MULTICAST_TTL  │ Multicast time-to-live                               ││
│   │ IP_MULTICAST_LOOP │ Receive own multicast packets                        ││
│   └───────────────────┴───────────────────────────────────────────────────────┘│
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Error Codes Reference

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    COMMON SOCKET ERROR CODES                                   │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   CONNECTION ERRORS:                                                           │
│   ┌────────────────────┬────────────────────────────────────────────────────┐ │
│   │ ECONNREFUSED       │ Connection refused - no server listening           │ │
│   │ ECONNRESET         │ Connection reset by peer                           │ │
│   │ ECONNABORTED       │ Connection aborted                                 │ │
│   │ ETIMEDOUT          │ Connection timed out                               │ │
│   │ ENETUNREACH        │ Network is unreachable                             │ │
│   │ EHOSTUNREACH       │ Host is unreachable                                │ │
│   │ ENOTCONN           │ Socket is not connected                            │ │
│   │ ESHUTDOWN          │ Socket has been shut down                          │ │
│   └────────────────────┴────────────────────────────────────────────────────┘ │
│                                                                                │
│   ADDRESS ERRORS:                                                              │
│   ┌────────────────────┬────────────────────────────────────────────────────┐ │
│   │ EADDRINUSE         │ Address already in use                             │ │
│   │ EADDRNOTAVAIL      │ Address not available                              │ │
│   │ EAFNOSUPPORT       │ Address family not supported                       │ │
│   │ EINVAL             │ Invalid argument                                   │ │
│   └────────────────────┴────────────────────────────────────────────────────┘ │
│                                                                                │
│   I/O ERRORS:                                                                  │
│   ┌────────────────────┬────────────────────────────────────────────────────┐ │
│   │ EAGAIN/EWOULDBLOCK │ Resource temporarily unavailable (non-blocking)    │ │
│   │ EINTR              │ Interrupted by signal                              │ │
│   │ EPIPE              │ Broken pipe (connection closed)                    │ │
│   │ EMSGSIZE           │ Message too large (UDP)                            │ │
│   │ ENOBUFS            │ No buffer space available                          │ │
│   └────────────────────┴────────────────────────────────────────────────────┘ │
│                                                                                │
│   SOCKET STATE ERRORS:                                                         │
│   ┌────────────────────┬────────────────────────────────────────────────────┐ │
│   │ EBADF              │ Bad file descriptor                                │ │
│   │ ENOTSOCK           │ Not a socket                                       │ │
│   │ EOPNOTSUPP         │ Operation not supported                            │ │
│   │ EISCONN            │ Socket is already connected                        │ │
│   │ EALREADY           │ Operation already in progress                      │ │
│   │ EINPROGRESS        │ Operation in progress (non-blocking connect)       │ │
│   └────────────────────┴────────────────────────────────────────────────────┘ │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Decision Tree: Choosing the Right Socket Type

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    CHOOSING THE RIGHT SOCKET TYPE                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐ │
│   │                                                                         │ │
│   │   START: What are you building?                                         │ │
│   │                │                                                        │ │
│   │                ▼                                                        │ │
│   │   ┌───────────────────────┐                                             │ │
│   │   │ Same machine only?    │                                             │ │
│   │   └───────────┬───────────┘                                             │ │
│   │               │                                                         │ │
│   │         ┌─────┴─────┐                                                   │ │
│   │         │           │                                                   │ │
│   │        YES          NO                                                  │ │
│   │         │           │                                                   │ │
│   │         ▼           ▼                                                   │ │
│   │   ┌───────────┐   ┌───────────────────┐                                 │ │
│   │   │ AF_UNIX   │   │ Need reliability? │                                 │ │
│   │   │ Unix      │   └─────────┬─────────┘                                 │ │
│   │   │ Domain    │       ┌─────┴─────┐                                     │ │
│   │   │ Sockets   │      YES          NO                                    │ │
│   │   │           │       │           │                                     │ │
│   │   │ • Fastest │       ▼           ▼                                     │ │
│   │   │ • No      │   ┌───────┐   ┌───────┐                                 │ │
│   │   │   network │   │ TCP   │   │ UDP   │                                 │ │
│   │   │   overhead│   │STREAM │   │DGRAM  │                                 │ │
│   │   └───────────┘   └───────┘   └───────┘                                 │ │
│   │                                                                         │ │
│   │   ────────────────────────────────────────────────────────────────────  │ │
│   │                                                                         │ │
│   │   SOCKET TYPE COMPARISON:                                               │ │
│   │                                                                         │ │
│   │   ┌─────────────┬──────────────┬──────────────┬──────────────────────┐  │ │
│   │   │             │   TCP        │   UDP        │   Unix Domain        │  │ │
│   │   ├─────────────┼──────────────┼──────────────┼──────────────────────┤  │ │
│   │   │ Reliable    │ Yes          │ No           │ Yes                  │  │ │
│   │   │ Ordered     │ Yes          │ No           │ Yes                  │  │ │
│   │   │ Boundaries  │ No (stream)  │ Yes (dgram)  │ Both available       │  │ │
│   │   │ Connection  │ Yes          │ No           │ Optional             │  │ │
│   │   │ Network     │ Yes          │ Yes          │ No (local only)      │  │ │
│   │   │ Performance │ Good         │ Best         │ Best (local)         │  │ │
│   │   │ FD passing  │ No           │ No           │ Yes                  │  │ │
│   │   └─────────────┴──────────────┴──────────────┴──────────────────────┘  │ │
│   │                                                                         │ │
│   │   USE WHEN:                                                             │ │
│   │                                                                         │ │
│   │   TCP:  • Web servers, databases, file transfer                         │ │
│   │         • Any app where data must arrive correctly                      │ │
│   │                                                                         │ │
│   │   UDP:  • DNS, gaming, video streaming, VoIP                            │ │
│   │         • Speed matters more than reliability                           │ │
│   │         • Application handles retransmission                            │ │
│   │                                                                         │ │
│   │   Unix: • Container/microservice communication                          │ │
│   │         • Database connections (PostgreSQL, MySQL)                      │ │
│   │         • Passing file descriptors between processes                    │ │
│   │                                                                         │ │
│   └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

### The Big Picture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    THE BIG PICTURE: SOCKET ECOSYSTEM                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐ │
│   │                                                                         │ │
│   │                        APPLICATION                                      │ │
│   │   ┌──────────────────────────────────────────────────────────────────┐  │ │
│   │   │  Web Server    Database    Container    Game Server    IoT       │  │ │
│   │   │    nginx       PostgreSQL    Docker       Custom      Sensor     │  │ │
│   │   └──────────────────────────────────────────────────────────────────┘  │ │
│   │                                │                                        │ │
│   │                    ┌───────────┴───────────┐                            │ │
│   │                    ▼                       ▼                            │ │
│   │   ┌────────────────────────┐  ┌────────────────────────┐               │ │
│   │   │    I/O Model Choice    │  │    Protocol Choice     │               │ │
│   │   │ • Blocking             │  │ • TCP (reliable)       │               │ │
│   │   │ • Non-blocking         │  │ • UDP (fast)           │               │ │
│   │   │ • I/O Multiplexing     │  │ • Unix (local IPC)     │               │ │
│   │   │ • Async (io_uring)     │  │ • Raw (custom)         │               │ │
│   │   └────────────────────────┘  └────────────────────────┘               │ │
│   │                                │                                        │ │
│   │                                ▼                                        │ │
│   │   ┌──────────────────────────────────────────────────────────────────┐  │ │
│   │   │                    SOCKET API                                    │  │ │
│   │   │   socket() bind() listen() accept() connect() send() recv()     │  │ │
│   │   └──────────────────────────────────────────────────────────────────┘  │ │
│   │                                │                                        │ │
│   │                                ▼                                        │ │
│   │   ┌──────────────────────────────────────────────────────────────────┐  │ │
│   │   │                    KERNEL                                        │  │ │
│   │   │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐      │  │ │
│   │   │  │  Socket   │  │   TCP     │  │   IP      │  │  Device   │      │  │ │
│   │   │  │  Layer    │->│  Layer    │->│  Layer    │->│  Driver   │      │  │ │
│   │   │  └───────────┘  └───────────┘  └───────────┘  └───────────┘      │  │ │
│   │   └──────────────────────────────────────────────────────────────────┘  │ │
│   │                                │                                        │ │
│   │                                ▼                                        │ │
│   │   ┌──────────────────────────────────────────────────────────────────┐  │ │
│   │   │                    NETWORK                                       │  │ │
│   │   │            ═══════════════════════════════════                   │  │ │
│   │   │              Ethernet / WiFi / Internet                          │  │ │
│   │   └──────────────────────────────────────────────────────────────────┘  │ │
│   │                                                                         │ │
│   └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│   EVOLUTION:                                                                   │
│   1983  BSD 4.2 introduces socket API                                         │
│   1988  POSIX standardizes sockets                                            │
│   1993  Linux supports sockets                                                │
│   2002  epoll() for scalable I/O (Linux 2.5.44)                              │
│   2019  io_uring for async I/O (Linux 5.1)                                    │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. References

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    REFERENCES                                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│   BOOKS:                                                                       │
│                                                                                │
│   • Stevens, W. Richard. "UNIX Network Programming, Volume 1:                  │
│     The Sockets Networking API" (3rd Edition, 2003)                            │
│     - The definitive guide to socket programming                               │
│                                                                                │
│   • Bach, Maurice J. "The Design of the UNIX Operating System" (1986)          │
│     - Classic reference for Unix kernel internals                              │
│                                                                                │
│   • Stevens, W. Richard. "TCP/IP Illustrated, Volume 1: The Protocols"         │
│     - Deep dive into TCP/IP protocol details                                   │
│                                                                                │
│   • Kerrisk, Michael. "The Linux Programming Interface" (2010)                 │
│     - Comprehensive Linux/Unix programming reference                           │
│                                                                                │
│   • Love, Robert. "Linux Kernel Development" (3rd Edition, 2010)               │
│     - Linux kernel internals including networking                              │
│                                                                                │
│   KERNEL SOURCE FILES:                                                         │
│                                                                                │
│   • net/socket.c           - Socket system calls                               │
│   • net/ipv4/tcp.c         - TCP implementation                                │
│   • net/ipv4/udp.c         - UDP implementation                                │
│   • net/unix/af_unix.c     - Unix domain sockets                               │
│   • include/linux/socket.h - Socket structures and constants                   │
│   • include/net/sock.h     - struct sock definition                            │
│   • include/linux/skbuff.h - sk_buff structure                                 │
│                                                                                │
│   MAN PAGES:                                                                   │
│                                                                                │
│   • socket(2)              - Create a socket                                   │
│   • socket(7)              - Socket concepts                                   │
│   • tcp(7)                 - TCP protocol                                      │
│   • udp(7)                 - UDP protocol                                      │
│   • unix(7)                - Unix domain sockets                               │
│   • ip(7)                  - IP protocol                                       │
│   • epoll(7)               - Scalable I/O event notification                   │
│                                                                                │
│   RFCs:                                                                        │
│                                                                                │
│   • RFC 793   - Transmission Control Protocol (TCP)                            │
│   • RFC 768   - User Datagram Protocol (UDP)                                   │
│   • RFC 791   - Internet Protocol (IP)                                         │
│   • RFC 1122  - Host Requirements (TCP clarifications)                         │
│   • RFC 7413  - TCP Fast Open                                                  │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

_Document generated in the style of Maurice Bach's "The Design of the UNIX Operating System"_
_Understanding sockets requires understanding the kernel's perspective_
