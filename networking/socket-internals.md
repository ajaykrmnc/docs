# Socket Internals: Connections, Ports, and Browser Multiplexin

> For readers familiar with Stevens' *Unix Network Programming* and Bach's *The Design of the UNIX Operating System*

---

## Table of Contents

1. [The Socket Abstraction Revisited](#1-the-socket-abstraction-revisited)
2. [The 5-Tuple: How Connections Are Uniquely Identified](#2-the-5-tuple-how-connections-are-uniquely-identified)
3. [Port Mechanics: The Kernel's Perspective](#3-port-mechanics-the-kernels-perspective)
4. [Chrome's Connection Architecture](#4-chromes-connection-architecture)
5. [HTTP/2 Multiplexing](#5-http2-multiplexing-the-key-to-modern-efficiency)
6. [Chrome's Socket Management: Kernel Interaction](#6-chromes-socket-management-kernel-interaction)
7. [Connection Reuse: Keep-Alive and Pooling](#7-connection-reuse-keep-alive-and-pooling)
8. [SO_REUSEPORT: Modern Load Balancing](#8-so_reuseport-modern-load-balancing)
9. [Summary: The Complete Picture](#9-summary-the-complete-picture)
10. [Deep Dive: Kernel Socket Data Structures](#10-deep-dive-kernel-socket-data-structures)
11. [The sk_buff: Kernel's Packet Representation](#11-the-sk_buff-kernels-packet-representation)
12. [TCP State Machine: Complete Implementation](#12-tcp-state-machine-complete-implementation)
13. [TCP Congestion Control Algorithms](#13-tcp-congestion-control-algorithms)
14. [Buffer Management and Memory Pressure](#14-buffer-management-and-memory-pressure)
15. [TLS Integration with Sockets](#15-tls-integration-with-sockets)
16. [QUIC and HTTP/3: The UDP Revolution](#16-quic-and-http3-the-udp-revolution)
17. [Zero-Copy Techniques](#17-zero-copy-techniques)
18. [Advanced: Connection Tracking and NAT](#18-advanced-connection-tracking-and-nat)
19. [Chrome Network Stack Deep Dive](#19-chrome-network-stack-deep-dive)
20. [Debugging and Observability](#20-debugging-and-observability)
21. [Performance Tuning](#21-performance-tuning)
22. [Security Considerations](#22-security-considerations)

---

## 1. The Socket Abstraction Revisited

A socket is a **file descriptor** bound to a protocol-specific data structure in the kernel. When you call `socket()`, the kernel allocates:

- A `struct socket` (BSD) or equivalent (`struct sock` in Linux)
- Protocol control blocks (TCP: `tcp_sock`, UDP: `udp_sock`)
- Send/receive buffer queues (sk_buff chains)

The key insight from Bach: sockets extend the file abstraction. The VFS layer routes `read()`/`write()` calls through `sock_read()`/`sock_write()`, which invoke protocol-specific handlers.

```
Process File Descriptor Table
        │
        ▼
   struct file
        │
        ▼
   struct socket ──────► struct sock (protocol layer)
        │                      │
        ▼                      ▼
   socket operations      TCP/UDP state machine
   (accept, bind, etc)    sk_buff queues
```

---

## 2. The 5-Tuple: How Connections Are Uniquely Identified

A TCP connection is **not** identified by port alone. The kernel demultiplexes packets using the **5-tuple**:

```
{protocol, local_ip, local_port, remote_ip, remote_port}
```

This is critical: **thousands of connections can share the same local port** as long as the remote endpoint differs.

### Example: Web Server on Port 443

| Connection | Local IP:Port | Remote IP:Port |
|------------|---------------|----------------|
| Conn 1     | 10.0.0.1:443  | 192.168.1.5:52341 |
| Conn 2     | 10.0.0.1:443  | 192.168.1.5:52342 |
| Conn 3     | 10.0.0.1:443  | 203.0.113.7:49823 |

All three connections use port 443, but they're distinct because the remote side differs.

---

## 3. Port Mechanics: The Kernel's Perspective

### 3.1 Port Binding and the Listening Socket

When a server calls `bind()` + `listen()`:

1. Kernel marks socket as `TCP_LISTEN` state
2. Socket is inserted into a **listening hash table** keyed by `(local_ip, local_port)`
3. Incoming SYN packets are matched against this table

### 3.2 The Accept Queue (Two-Queue Model)

Stevens covers this, but the modern implementation:

```
                     SYN received
                          │
                          ▼
              ┌───────────────────────┐
              │   SYN Queue (half-open)│  ← tcp_max_syn_backlog
              │   Incomplete connections│
              └───────────┬───────────┘
                          │ 3-way handshake complete
                          ▼
              ┌───────────────────────┐
              │  Accept Queue (ESTABLISHED)│  ← listen() backlog
              │  Complete connections      │
              └───────────┬───────────┘
                          │ accept() called
                          ▼
                   New socket FD returned
```

### 3.3 Ephemeral Port Allocation

Client-side ports come from the **ephemeral range** (Linux default: 32768-60999):

```c
// Simplified: net/ipv4/inet_hashtables.c
int inet_csk_get_port(struct sock *sk, unsigned short snum) {
    // If snum == 0, kernel picks from ip_local_port_range
    // Uses bitmap or sequential scan depending on config
    // Checks against established connections to avoid collision
}
```

---

## 4. Chrome's Connection Architecture

Chrome's network stack is sophisticated, handling multiple tabs with connection pooling, HTTP/2 multiplexing, and socket limits.

### 4.1 The Connection Pool

Chrome maintains a **per-origin connection pool**:

```
┌──────────────────────────────────────────────────────────┐
│                    Chrome Network Service                 │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Tab 1           │  │ Tab 2           │               │
│  │ example.com     │  │ example.com     │               │
│  └────────┬────────┘  └────────┬────────┘               │
│           │                    │                         │
│           ▼                    ▼                         │
│  ┌─────────────────────────────────────────────┐        │
│  │        HttpNetworkSession                    │        │
│  │  ┌───────────────────────────────────────┐  │        │
│  │  │  Connection Pool (per-origin)          │  │        │
│  │  │  example.com:443 ─► [Conn1, Conn2, ...│  │        │
│  │  │  cdn.example.com:443 ─► [Conn3]       │  │        │
│  │  └───────────────────────────────────────┘  │        │
│  └─────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Connection Limits (Chromium defaults)

| Limit | Value | Reason |
|-------|-------|--------|
| Max connections per origin | 6 | HTTP/1.1 spec recommendation |
| Max total connections | 256 | OS socket limits |
| Max connections per proxy | 32 | Proxy overload prevention |

### 4.3 How Multiple Tabs Share Connections

**Scenario**: Tab 1 and Tab 2 both load `https://example.com`

1. Tab 1 requests `example.com/page1`
2. Network service checks pool: no connection exists
3. Creates TCP connection → TLS handshake → HTTP/2 negotiation
4. Tab 2 requests `example.com/page2` (while Tab 1 still loading)
5. **Same connection is reused** via HTTP/2 stream multiplexing

```
Single TCP Connection (port 443)
        │
        ├── Stream 1: GET /page1  (Tab 1)
        ├── Stream 3: GET /style.css (Tab 1)
        ├── Stream 5: GET /page2  (Tab 2)
        └── Stream 7: GET /app.js (Tab 2)
```

All streams share **one TCP socket**, one local ephemeral port.

---

## 5. HTTP/2 Multiplexing: The Key to Modern Efficiency

HTTP/1.1 problem: **head-of-line blocking**. One slow response blocks the entire connection.

HTTP/2 solution: **stream multiplexing** over a single TCP connection.

```
HTTP/1.1 (6 connections needed):
├── Conn 1: Request A ──────────► Response A
├── Conn 2: Request B ──────────► Response B
├── Conn 3: Request C ──────────► Response C
├── Conn 4: Request D ──────────► Response D
├── Conn 5: Request E ──────────► Response E
└── Conn 6: Request F ──────────► Response F

HTTP/2 (1 connection):
└── Conn 1: ┌─ Stream 1: Request A ◄─► Response A
            ├─ Stream 3: Request B ◄─► Response B
            ├─ Stream 5: Request C ◄─► Response C
            ├─ Stream 7: Request D ◄─► Response D  (interleaved frames)
            ├─ Stream 9: Request E ◄─► Response E
            └─ Stream 11: Request F ◄─► Response F
```

### 5.1 Frame Interleaving

HTTP/2 breaks responses into **frames** (16KB default). The server can interleave frames:

```
Time ─────────────────────────────────────────────►

[DATA:Stream1][DATA:Stream3][DATA:Stream1][DATA:Stream5][DATA:Stream3]...
```

This prevents a large response from blocking smaller ones.

---

## 6. Chrome's Socket Management: Kernel Interaction

### 6.1 The Network Service Process

Chrome isolates networking in a separate process (`network_service`):

```
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│   Renderer     │      │   Renderer     │      │   Browser      │
│   (Tab 1)      │      │   (Tab 2)      │      │   Process      │
└───────┬────────┘      └───────┬────────┘      └───────┬────────┘
        │                       │                       │
        │ Mojo IPC              │ Mojo IPC              │
        ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Network Service Process                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  URLLoaderFactory → HttpNetworkTransaction →            │    │
│  │  HttpStreamFactory → ClientSocketPool →                 │    │
│  │  TCPClientSocket (wraps OS socket)                      │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┬────┘
                                                              │
                         System Calls                         │
                              ▼                               │
┌─────────────────────────────────────────────────────────────────┐
│                           Kernel                                 │
│   socket() → connect() → send()/recv() → close()                │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Non-Blocking I/O and Event Loops

Chrome uses non-blocking sockets with event notification:

- **Linux**: `epoll_wait()` in a dedicated I/O thread
- **macOS**: `kqueue()`
- **Windows**: `IOCP` (I/O Completion Ports)

```cpp
// Simplified: Chrome's socket implementation
void TCPClientSocket::Connect() {
    int rv = connect(socket_fd_, addr, len);  // Returns immediately
    if (rv == -1 && errno == EINPROGRESS) {
        // Register with event loop for write-ready notification
        watcher_.WatchFileDescriptor(socket_fd_, WATCH_WRITE);
    }
}
```

---

## 7. Connection Reuse: Keep-Alive and Pooling

### 7.1 Keep-Alive Mechanics

TCP connections are expensive (3-way handshake + TLS). Keep-alive reuses them:

```
Without Keep-Alive:
Request 1: [SYN][SYN-ACK][ACK][GET...][Response][FIN]
Request 2: [SYN][SYN-ACK][ACK][GET...][Response][FIN]  ← Full overhead again

With Keep-Alive:
Request 1: [SYN][SYN-ACK][ACK][GET...][Response]
Request 2: [GET...][Response]  ← Same connection
Request 3: [GET...][Response]
...
[FIN]  ← Close after idle timeout
```

### 7.2 Chrome's Idle Socket Timeout

- Idle sockets kept for **60 seconds** (configurable)
- Pool proactively warms connections for predicted navigations

---

## 8. SO_REUSEPORT: Modern Load Balancing

Linux 3.9+ introduced `SO_REUSEPORT`, allowing **multiple sockets to bind to the same port**:

```c
int optval = 1;
setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &optval, sizeof(optval));
bind(fd, addr, len);  // Multiple processes can do this
```

The kernel distributes incoming connections across all listening sockets (hash-based).

```
                     Incoming Connections
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Kernel: SO_REUSEPORT distribution   │
        │   Hash(src_ip, src_port, dst_port)    │
        └───────┬───────────┬───────────┬───────┘
                │           │           │
                ▼           ▼           ▼
           Worker 1    Worker 2    Worker 3
           (port 80)   (port 80)   (port 80)
```

This eliminates the accept() thundering herd problem from older kernels.

---

## 9. Summary: The Complete Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Browser (e.g., Chrome with 10 tabs)                                    │
│                                                                          │
│  Tab1 Tab2 Tab3 Tab4 Tab5 Tab6 Tab7 Tab8 Tab9 Tab10                     │
│   │    │    │    │    │    │    │    │    │    │                        │
│   └────┴────┴────┴────┴────┴────┴────┴────┴────┘                        │
│                           │                                              │
│                   Network Service                                        │
│                           │                                              │
│            Connection Pool (per-origin)                                  │
│   ┌─────────────────────────────────────────────┐                       │
│   │ example.com:443 → [Conn1, Conn2]            │ ← 2 sockets           │
│   │ cdn.site.com:443 → [Conn3]                  │ ← 1 socket            │
│   │ api.service.io:443 → [Conn4, Conn5, Conn6]  │ ← 3 sockets           │
│   └─────────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                        6 TCP connections total
                        6 local ephemeral ports
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel                                                                  │
│                                                                          │
│  Connection Tracking (5-tuple hash table):                              │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ {TCP, 10.0.0.5:52341, 93.184.216.34:443} → Conn1 (sk_buff)     │     │
│  │ {TCP, 10.0.0.5:52342, 93.184.216.34:443} → Conn2               │     │
│  │ {TCP, 10.0.0.5:52343, 104.18.2.1:443}    → Conn3               │     │
│  │ ...                                                             │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  Ephemeral Port Bitmap: [32768...52341✓...52343✓...60999]               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Takeaways**:

1. **Port is not the bottleneck** — the 5-tuple allows 65k+ connections per remote IP
2. **Chrome pools connections** — tabs don't get dedicated sockets
3. **HTTP/2 multiplexes** — one connection serves multiple requests concurrently
4. **Kernel demultiplexes** — incoming packets matched via hash lookup in O(1)
5. **Ephemeral ports are per-connection** — browser needs one per TCP connection, not per tab

---

## 10. Deep Dive: Kernel Socket Data Structures

Understanding sockets requires understanding the kernel's layered data structure hierarchy. This section explores the Linux implementation in depth.

### 10.1 The Three-Layer Socket Model

Linux implements sockets through three interconnected structures:

```
User Space
─────────────────────────────────────────────────────────────────────────────
Kernel Space

┌─────────────────────────────────────────────────────────────────────────────┐
│                         struct socket (BSD layer)                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  state          : SS_UNCONNECTED, SS_CONNECTED, SS_CONNECTING, etc.   │  │
│  │  type           : SOCK_STREAM, SOCK_DGRAM, SOCK_RAW                   │  │
│  │  flags          : SOCK_NONBLOCK, SOCK_CLOEXEC                         │  │
│  │  *ops           : pointer to protocol operations (proto_ops)          │  │
│  │  *sk            : pointer to struct sock (network layer)              │  │
│  │  *file          : back-pointer to struct file                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ sk pointer
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         struct sock (INET layer)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Common fields (struct sock_common):                                   │  │
│  │    skc_family      : AF_INET, AF_INET6, AF_UNIX                       │  │
│  │    skc_state       : TCP_ESTABLISHED, TCP_SYN_SENT, etc.              │  │
│  │    skc_bound_dev_if: bound network interface index                    │  │
│  │    skc_hash        : hash value for lookup tables                     │  │
│  │    skc_daddr       : destination IP address                           │  │
│  │    skc_dport       : destination port                                 │  │
│  │    skc_rcv_saddr   : source IP address                                │  │
│  │    skc_num         : source port (host byte order)                    │  │
│  │                                                                        │  │
│  │  Socket buffers:                                                       │  │
│  │    sk_receive_queue : incoming packet queue (sk_buff list)            │  │
│  │    sk_write_queue   : outgoing packet queue                           │  │
│  │    sk_error_queue   : ICMP errors, timestamps                         │  │
│  │                                                                        │  │
│  │  Buffer limits:                                                        │  │
│  │    sk_rcvbuf        : receive buffer size limit                       │  │
│  │    sk_sndbuf        : send buffer size limit                          │  │
│  │    sk_wmem_queued   : bytes queued for transmission                   │  │
│  │    sk_rmem_alloc    : bytes in receive queue                          │  │
│  │                                                                        │  │
│  │  Callbacks:                                                            │  │
│  │    sk_data_ready    : called when data arrives                        │  │
│  │    sk_write_space   : called when send buffer has space               │  │
│  │    sk_state_change  : called on state transitions                     │  │
│  │    sk_error_report  : called on errors                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ embedded/container_of
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    struct tcp_sock (Protocol layer)                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  struct inet_connection_sock (connection-oriented base):               │  │
│  │    icsk_accept_queue  : pending connections for accept()              │  │
│  │    icsk_retransmit_timer : retransmission timer                       │  │
│  │    icsk_delack_timer  : delayed ACK timer                             │  │
│  │    icsk_ca_ops        : congestion control operations                 │  │
│  │                                                                        │  │
│  │  TCP-specific fields:                                                  │  │
│  │    snd_una        : oldest unacknowledged sequence number             │  │
│  │    snd_nxt        : next sequence number to send                      │  │
│  │    snd_wnd        : send window (advertised by peer)                  │  │
│  │    rcv_nxt        : next expected sequence number                     │  │
│  │    rcv_wnd        : receive window (advertised to peer)               │  │
│  │                                                                        │  │
│  │  Congestion control:                                                   │  │
│  │    snd_cwnd       : congestion window (packets)                       │  │
│  │    snd_ssthresh   : slow start threshold                              │  │
│  │    srtt_us        : smoothed RTT (microseconds)                       │  │
│  │    mdev_us        : RTT mean deviation                                │  │
│  │    rto            : retransmission timeout (jiffies)                  │  │
│  │                                                                        │  │
│  │  Out-of-order handling:                                                │  │
│  │    ooo_queue      : out-of-order segment queue (rb_tree)              │  │
│  │    sacked_out     : SACK'd packets count                              │  │
│  │    lost_out       : lost packets count                                │  │
│  │                                                                        │  │
│  │  Window scaling:                                                       │  │
│  │    rx_opt.snd_wscale : send window scale factor                       │  │
│  │    rx_opt.rcv_wscale : receive window scale factor                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 The Protocol Operations Table

Each protocol family registers its operations via `struct proto_ops`:

```c
// From net/ipv4/af_inet.c
const struct proto_ops inet_stream_ops = {
    .family        = PF_INET,
    .owner         = THIS_MODULE,
    .release       = inet_release,
    .bind          = inet_bind,
    .connect       = inet_stream_connect,
    .accept        = inet_accept,
    .getname       = inet_getname,
    .poll          = tcp_poll,
    .ioctl         = inet_ioctl,
    .listen        = inet_listen,
    .shutdown      = inet_shutdown,
    .setsockopt    = sock_common_setsockopt,
    .getsockopt    = sock_common_getsockopt,
    .sendmsg       = inet_sendmsg,
    .recvmsg       = inet_recvmsg,
    .mmap          = sock_no_mmap,
    .sendpage      = inet_sendpage,
    .splice_read   = tcp_splice_read,
};
```

### 10.3 Socket Creation Path

When `socket(AF_INET, SOCK_STREAM, 0)` is called:

```
User: socket(AF_INET, SOCK_STREAM, 0)
        │
        ▼
sys_socket()
        │
        ├── sock_create()
        │       │
        │       ├── Allocate struct socket
        │       │
        │       ├── Find protocol family: net_families[AF_INET]
        │       │       └── inet_family_ops
        │       │
        │       └── inet_create()
        │               │
        │               ├── Find protocol: inetsw[SOCK_STREAM]
        │               │       └── tcp_prot
        │               │
        │               ├── sk_alloc()
        │               │       └── Allocate struct tcp_sock (includes sock)
        │               │
        │               ├── sock_init_data()
        │               │       ├── Initialize queues
        │               │       ├── Set buffer limits
        │               │       └── Install callbacks
        │               │
        │               └── tcp_v4_init_sock()
        │                       ├── Initialize TCP timers
        │                       ├── Set initial congestion window
        │                       └── Set default congestion control (CUBIC)
        │
        └── sock_map_fd()
                │
                ├── get_unused_fd_flags()
                │
                ├── sock_alloc_file()
                │       └── Create struct file with socket_file_ops
                │
                └── fd_install()
                        └── Link fd → file → socket → sock
```

### 10.4 File Descriptor to Socket Resolution

```c
// How the kernel finds socket from fd
struct socket *sockfd_lookup(int fd, int *err) {
    struct file *file = fget(fd);           // Get file from fd table
    if (!file)
        return NULL;

    struct socket *sock = sock_from_file(file);  // Extract socket
    return sock;
}

// sock_from_file:
static inline struct socket *sock_from_file(struct file *file) {
    if (file->f_op != &socket_file_ops)
        return NULL;
    return file->private_data;  // socket stored here
}
```

### 10.5 The INET Hash Tables

TCP uses multiple hash tables for efficient connection lookup:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        inet_hashinfo structure                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ehash (Established Hash Table)                                      │    │
│  │  ─────────────────────────────                                       │    │
│  │  Key: hash(local_ip, local_port, remote_ip, remote_port)            │    │
│  │  Used for: ESTABLISHED and TIME_WAIT connections                    │    │
│  │  Size: tcp_hashinfo.ehash_mask + 1 buckets                          │    │
│  │                                                                      │    │
│  │  Bucket 0: [sock1] ──► [sock2] ──► NULL                             │    │
│  │  Bucket 1: [sock3] ──► NULL                                         │    │
│  │  Bucket 2: NULL                                                      │    │
│  │  ...                                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  bhash (Bind Hash Table)                                             │    │
│  │  ──────────────────────                                              │    │
│  │  Key: hash(local_port)                                               │    │
│  │  Used for: bind() conflict detection                                 │    │
│  │  Value: inet_bind_bucket with list of sockets on that port          │    │
│  │                                                                      │    │
│  │  Bucket for port 80:                                                 │    │
│  │    inet_bind_bucket {                                                │    │
│  │      port: 80                                                        │    │
│  │      fastreuse: 1 (SO_REUSEADDR allowed)                            │    │
│  │      owners: [sock_A, sock_B]  // sockets bound to port 80          │    │
│  │    }                                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  listening_hash (Listening Socket Hash Table)                        │    │
│  │  ────────────────────────────────────────────                        │    │
│  │  Key: hash(local_port)                                               │    │
│  │  Used for: finding listening socket for incoming SYN                │    │
│  │                                                                      │    │
│  │  Bucket for port 443:                                                │    │
│  │    [listen_sock1 (0.0.0.0:443)] ──► [listen_sock2 (10.0.0.1:443)]   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.6 Connection Lookup Algorithm

```c
// Simplified from inet_hashtables.c
struct sock *__inet_lookup(struct net *net,
                           struct inet_hashinfo *hashinfo,
                           const __be32 saddr, const __be16 sport,
                           const __be32 daddr, const __be16 dport,
                           const int dif) {

    // Step 1: Try established hash (most common case)
    unsigned int hash = inet_ehashfn(net, daddr, dport, saddr, sport);
    struct sock *sk = __inet_lookup_established(
        net, hashinfo, saddr, sport, daddr, dport, dif);

    if (sk)
        return sk;  // Found established connection

    // Step 2: Try listening hash (for incoming SYN)
    return __inet_lookup_listener(
        net, hashinfo, saddr, sport, daddr, dport, dif);
}

// Hash function for established connections
static inline unsigned int inet_ehashfn(struct net *net,
                                         __be32 laddr, __u16 lport,
                                         __be32 faddr, __u16 fport) {
    return jhash_3words(
        (__force __u32)laddr,
        (__force __u32)faddr,
        ((__u32)lport) << 16 | (__force __u32)fport,
        net->hash_mix
    );
}
```

---

## 11. The sk_buff: Kernel's Packet Representation

The `sk_buff` (socket buffer) is the fundamental data structure for all network packets in Linux. Understanding it is essential for grasping kernel networking.

### 11.1 sk_buff Structure Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            struct sk_buff                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Packet ownership and linkage:                                       │    │
│  │    *next, *prev     : doubly-linked list pointers                   │    │
│  │    *sk              : owning socket (NULL for forwarded packets)    │    │
│  │    *dev             : network device                                 │    │
│  │  ──────────────────────────────────────────────────────────────────  │    │
│  │  Timing:                                                             │    │
│  │    tstamp           : packet timestamp (for latency measurement)    │    │
│  │  ──────────────────────────────────────────────────────────────────  │    │
│  │  Buffer pointers (the critical four):                                │    │
│  │    *head            : start of allocated buffer                      │    │
│  │    *data            : start of actual packet data                    │    │
│  │    *tail            : end of actual packet data                      │    │
│  │    *end             : end of allocated buffer                        │    │
│  │  ──────────────────────────────────────────────────────────────────  │    │
│  │  Protocol headers (unions for memory efficiency):                    │    │
│  │    transport_header : offset to L4 (TCP/UDP) header                 │    │
│  │    network_header   : offset to L3 (IP) header                      │    │
│  │    mac_header       : offset to L2 (Ethernet) header                │    │
│  │  ──────────────────────────────────────────────────────────────────  │    │
│  │  Packet metadata:                                                    │    │
│  │    len              : actual data length                             │    │
│  │    data_len         : length in fragments (for scatter-gather)      │    │
│  │    protocol         : L3 protocol (ETH_P_IP, etc.)                  │    │
│  │    pkt_type         : PACKET_HOST, PACKET_BROADCAST, etc.           │    │
│  │    ip_summed        : checksum status                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 The Four Critical Pointers

```
Allocated Buffer Memory:

        head                    data                   tail                end
         │                       │                      │                   │
         ▼                       ▼                      ▼                   ▼
         ┌───────────────────────────────────────────────────────────────────┐
         │ HEADROOM │  Ethernet │   IP    │   TCP    │  Payload  │ TAILROOM │
         │          │  Header   │  Header │  Header  │   Data    │          │
         └───────────────────────────────────────────────────────────────────┘
         │◄─────────►│                                             │◄────────►│
          headroom    ◄────────── skb->len ──────────►               tailroom
                     │◄─────────────── data area ─────────────────►│

Headroom: Reserved space for prepending headers (e.g., tunneling)
Tailroom: Reserved space for appending data or trailers
```

### 11.3 sk_buff Operations

```c
// Reserve headroom at allocation time
struct sk_buff *skb = alloc_skb(size, GFP_KERNEL);
skb_reserve(skb, headroom);  // Move data pointer forward

// Prepend data (e.g., adding IP header)
unsigned char *ptr = skb_push(skb, header_len);
// data pointer moves backward, len increases

// Append data (e.g., payload)
unsigned char *ptr = skb_put(skb, data_len);
// tail pointer moves forward, len increases

// Remove from front (e.g., stripping Ethernet header)
skb_pull(skb, eth_header_len);
// data pointer moves forward, len decreases
```

```
skb_reserve(skb, 64):
         head     data/tail                                            end
         │        │                                                     │
         ▼        ▼                                                     ▼
         ┌────────────────────────────────────────────────────────────────┐
         │ Reserved │                     Empty                           │
         │ headroom │                                                     │
         └────────────────────────────────────────────────────────────────┘

skb_put(skb, 1460) - Add TCP payload:
         head     data                                    tail         end
         │        │                                        │            │
         ▼        ▼                                        ▼            ▼
         ┌────────────────────────────────────────────────────────────────┐
         │ Reserved │            1460 bytes payload         │ Tailroom   │
         └────────────────────────────────────────────────────────────────┘

skb_push(skb, 20) - Prepend TCP header:
         head  data                                        tail         end
         │     │                                            │            │
         ▼     ▼                                            ▼            ▼
         ┌────────────────────────────────────────────────────────────────┐
         │ Rsv │ TCP hdr │         1460 bytes payload        │ Tailroom   │
         │     │  20B    │                                   │            │
         └────────────────────────────────────────────────────────────────┘

skb_push(skb, 20) - Prepend IP header:
         head data                                          tail        end
         │    │                                              │           │
         ▼    ▼                                              ▼           ▼
         ┌────────────────────────────────────────────────────────────────┐
         │Rsv│ IP │ TCP │         1460 bytes payload          │Tailroom  │
         │   │20B │ 20B │                                     │          │
         └────────────────────────────────────────────────────────────────┘
```

### 11.4 sk_buff Cloning and Sharing

sk_buffs can be cloned for zero-copy operations:

```c
// Clone: creates new sk_buff metadata, shares data buffer
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC);

// After cloning:
┌────────────────┐         ┌────────────────┐
│ Original skb   │         │ Cloned skb     │
│  *data ────────┼────┐    │  *data ────────┼────┐
│  len = 1500    │    │    │  len = 1500    │    │
│  users = 2     │    │    │  users = 2     │    │
└────────────────┘    │    └────────────────┘    │
                      │                          │
                      ▼                          ▼
              ┌───────────────────────────────────────┐
              │  Shared Data Buffer (refcounted)      │
              │  dataref = 2                          │
              └───────────────────────────────────────┘

// Copy: creates entirely new sk_buff with copied data
struct sk_buff *copy = skb_copy(skb, GFP_ATOMIC);
```

### 11.5 Scatter-Gather and Fragmented sk_buffs

For large packets, data can span multiple memory regions:

```
Linear sk_buff (small packet):
┌──────────────────────────────────────────┐
│ sk_buff                                   │
│   len = 1500                             │
│   data_len = 0  (all data in linear buf) │
│   *data ─────────────────────────────────┼──► [1500 bytes]
└──────────────────────────────────────────┘

Fragmented sk_buff (large packet, e.g., 64KB):
┌──────────────────────────────────────────┐
│ sk_buff                                   │
│   len = 65536                            │
│   data_len = 64000  (in fragments)       │
│   *data ─────────────────────────────────┼──► [1536 bytes linear]
│                                           │
│   skb_shinfo(skb)->frags[]:              │
│     [0]: page=0xffff..., offset=0, size=16384  ──► Page 1
│     [1]: page=0xffff..., offset=0, size=16384  ──► Page 2
│     [2]: page=0xffff..., offset=0, size=16384  ──► Page 3
│     [3]: page=0xffff..., offset=0, size=14848  ──► Page 4
└──────────────────────────────────────────┘
```

### 11.6 sk_buff Queues

Sockets maintain multiple sk_buff queues:

```c
// Socket receive queue
struct sk_buff_head sk_receive_queue;

// Adding to queue (tail)
skb_queue_tail(&sk->sk_receive_queue, skb);

// Removing from queue (head)
struct sk_buff *skb = skb_dequeue(&sk->sk_receive_queue);

// Queue iteration
skb_queue_walk(&sk->sk_receive_queue, skb) {
    // Process each skb
}
```

```
sk_buff_head structure:
┌─────────────────────────────────────────────────────────────────────┐
│  struct sk_buff_head                                                 │
│    qlen = 3                                                          │
│    lock (spinlock)                                                   │
│    next ──► skb1 ──► skb2 ──► skb3 ──► (back to head)               │
│    prev ◄── skb1 ◄── skb2 ◄── skb3 ◄── (circular list)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. TCP State Machine: Complete Implementation

### 12.1 TCP States (Stevens Chapter 2, Expanded)

```
                              ┌───────────────────┐
                              │      CLOSED       │
                              └─────────┬─────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              │ Passive open            │ Active open             │
              │ (listen)                │ (connect)               │
              ▼                         ▼                         │
     ┌─────────────────┐       ┌─────────────────┐               │
     │     LISTEN      │       │   SYN_SENT      │               │
     └────────┬────────┘       └────────┬────────┘               │
              │                         │                         │
              │ Receive SYN             │ Receive SYN+ACK         │
              │ Send SYN+ACK            │ Send ACK                │
              ▼                         ▼                         │
     ┌─────────────────┐       ┌─────────────────┐               │
     │   SYN_RECEIVED  │       │   ESTABLISHED   │◄──────────────┤
     └────────┬────────┘       └────────┬────────┘               │
              │                         │                         │
              │ Receive ACK             │                         │
              │                         │                         │
              └─────────────────────────┘                         │
                                        │                         │
                                        │ Close (active)          │
                                        │ Send FIN                │
                                        ▼                         │
                               ┌─────────────────┐               │
                               │    FIN_WAIT_1   │               │
                               └────────┬────────┘               │
                                        │                         │
              ┌─────────────────────────┼─────────────────────────┤
              │                         │                         │
              │ Receive ACK only        │ Receive FIN+ACK         │
              ▼                         │ Send ACK                │
     ┌─────────────────┐               │                         │
     │    FIN_WAIT_2   │               │                         │
     └────────┬────────┘               │                         │
              │                         │                         │
              │ Receive FIN             │                         │
              │ Send ACK                │                         │
              ▼                         ▼                         │
     ┌─────────────────┐       ┌─────────────────┐               │
     │    TIME_WAIT    │◄──────│   CLOSING       │               │
     └────────┬────────┘       └─────────────────┘               │
              │                                                   │
              │ 2MSL timeout                                      │
              ▼                                                   │
     ┌─────────────────┐                                         │
     │     CLOSED      │◄────────────────────────────────────────┘
     └─────────────────┘


Simultaneous Close (both sides send FIN):
┌─────────────────┐                     ┌─────────────────┐
│  ESTABLISHED    │                     │  ESTABLISHED    │
└────────┬────────┘                     └────────┬────────┘
         │ Send FIN                              │ Send FIN
         ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│   FIN_WAIT_1    │      FIN (cross)    │   FIN_WAIT_1    │
└────────┬────────┘ ──────────────────► └────────┬────────┘
         │ Receive FIN                           │ Receive FIN
         │ Send ACK                              │ Send ACK
         ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│    CLOSING      │                     │    CLOSING      │
└────────┬────────┘                     └────────┬────────┘
         │ Receive ACK                           │ Receive ACK
         ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│   TIME_WAIT     │                     │   TIME_WAIT     │
└─────────────────┘                     └─────────────────┘


Passive Close (receive FIN first):
┌─────────────────┐
│   ESTABLISHED   │
└────────┬────────┘
         │ Receive FIN
         │ Send ACK
         ▼
┌─────────────────┐
│   CLOSE_WAIT    │   ← Application notified, may continue sending
└────────┬────────┘
         │ Application closes
         │ Send FIN
         ▼
┌─────────────────┐
│    LAST_ACK     │
└────────┬────────┘
         │ Receive ACK
         ▼
┌─────────────────┐
│     CLOSED      │
└─────────────────┘
```

### 12.2 Kernel State Machine Implementation

```c
// From net/ipv4/tcp_input.c (simplified)
int tcp_rcv_state_process(struct sock *sk, struct sk_buff *skb) {
    struct tcphdr *th = tcp_hdr(skb);

    switch (sk->sk_state) {
    case TCP_CLOSE:
        goto discard;

    case TCP_LISTEN:
        if (th->syn) {
            // Create request socket for 3-way handshake
            return tcp_v4_conn_request(sk, skb);
        }
        goto discard;

    case TCP_SYN_SENT:
        // Expecting SYN+ACK
        return tcp_rcv_synsent_state_process(sk, skb, th);

    case TCP_SYN_RECV:
        if (th->ack) {
            // 3-way handshake complete
            tcp_set_state(sk, TCP_ESTABLISHED);
            sk->sk_state_change(sk);  // Wake up accept()
        }
        break;

    case TCP_ESTABLISHED:
        if (th->fin) {
            tcp_set_state(sk, TCP_CLOSE_WAIT);
            // Queue FIN for application
        }
        // Normal data processing
        tcp_data_queue(sk, skb);
        break;

    case TCP_FIN_WAIT_1:
        if (th->ack && !th->fin) {
            tcp_set_state(sk, TCP_FIN_WAIT_2);
        } else if (th->fin) {
            tcp_send_ack(sk);
            tcp_set_state(sk, th->ack ? TCP_TIME_WAIT : TCP_CLOSING);
        }
        break;

    // ... other states
    }
    return 0;
}
```

### 12.3 TIME_WAIT Handling

TIME_WAIT is critical but expensive. The kernel optimizes it:

```c
// inet_timewait_sock: Lightweight socket for TIME_WAIT
struct inet_timewait_sock {
    struct sock_common  __tw_common;
    volatile unsigned char tw_substate;
    unsigned char       tw_rcv_wscale;
    __be16              tw_sport;
    __be32              tw_daddr;
    __be32              tw_rcv_saddr;
    __be16              tw_dport;
    __u16               tw_num;
    // ... much smaller than full tcp_sock
};
```

```
TIME_WAIT Optimization:

┌────────────────────────────────────────────────────────────────────────┐
│  Full tcp_sock (~2KB)                                                   │
│                                                                          │
│  After entering TIME_WAIT:                                              │
│  ───────────────────────────                                            │
│                                     ┌────────────────────────────────┐  │
│  Replace with:                      │ inet_timewait_sock (~200B)     │  │
│                                     │  - Minimal state only          │  │
│                                     │  - Stored in separate hash     │  │
│                                     │  - Recycled after 2MSL         │  │
│                                     └────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘

2MSL (Maximum Segment Lifetime):
- Linux default: 60 seconds (2 * 30s)
- Configurable via net.ipv4.tcp_fin_timeout (single MSL)
- Can hold tens of thousands of TIME_WAIT sockets

TIME_WAIT bucket recycling:
┌─────────────────────────────────────────────────────────────────────┐
│  tcp_death_row structure                                             │
│                                                                       │
│  tw_timer ──────► Timer wheel for expiration                        │
│                                                                       │
│  tw_count = 5000  (current TIME_WAIT sockets)                       │
│  sysctl_max_tw_buckets = 65536  (maximum allowed)                   │
│                                                                       │
│  If tw_count > max: new connections recycle oldest TIME_WAIT        │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.4 SYN Cookies: DoS Mitigation

When the SYN queue fills, the kernel can use SYN cookies to avoid storing state:

```
Normal 3-Way Handshake (stores state):

Client                    Server
   │                         │
   │──── SYN (seq=x) ───────►│  Server allocates request_sock
   │                         │  (consumes memory)
   │◄─── SYN+ACK (seq=y) ────│
   │                         │
   │──── ACK (ack=y+1) ─────►│  Server creates full socket
   │                         │


SYN Cookie Mode (stateless until ACK):

Client                    Server
   │                         │
   │──── SYN (seq=x) ───────►│  Server computes cookie:
   │                         │    seq = hash(src_ip, src_port,
   │                         │              dst_ip, dst_port,
   │                         │              secret_key, time)
   │                         │  NO STATE STORED
   │◄─── SYN+ACK (seq=y) ────│  y = cookie value
   │                         │
   │──── ACK (ack=y+1) ─────►│  Server validates:
   │                         │    if (ack-1 == computed_cookie)
   │                         │      create socket (legitimate)
   │                         │    else
   │                         │      drop (attack/stale)
```

```c
// Enabling SYN cookies (automatic when queue full)
sysctl net.ipv4.tcp_syncookies = 1   // Enable
sysctl net.ipv4.tcp_syncookies = 2   // Always use

// Cookie computation (simplified)
__u32 cookie_v4_init_sequence(struct sk_buff *skb, __u16 *mssp) {
    const struct iphdr *iph = ip_hdr(skb);
    const struct tcphdr *th = tcp_hdr(skb);

    // Cookie encodes: timestamp (5 bits), MSS index (3 bits)
    // + cryptographic hash of 5-tuple

    return __cookie_v4_init_sequence(iph->saddr, iph->daddr,
                                      th->source, th->dest,
                                      ntohl(th->seq), mssp);
}
```

---

## 13. TCP Congestion Control Algorithms

### 13.1 Congestion Control Framework

Linux supports pluggable congestion control via the `tcp_congestion_ops` structure:

```c
struct tcp_congestion_ops {
    // List management
    struct list_head list;

    // Name and flags
    char name[TCP_CA_NAME_MAX];
    u32 key;
    u32 flags;

    // Required callbacks
    void (*init)(struct sock *sk);
    void (*release)(struct sock *sk);

    // Congestion events
    void (*cwnd_event)(struct sock *sk, enum tcp_ca_event ev);
    void (*cong_avoid)(struct sock *sk, u32 ack, u32 acked);
    void (*cong_control)(struct sock *sk, const struct rate_sample *rs);

    // Loss/recovery
    u32 (*ssthresh)(struct sock *sk);
    u32 (*undo_cwnd)(struct sock *sk);

    // RTT measurement
    void (*pkts_acked)(struct sock *sk, const struct ack_sample *sample);

    // ECN handling
    void (*cwnd_reduction)(struct sock *sk, int newly_acked);
};
```

### 13.2 CUBIC: The Linux Default

CUBIC is optimized for high-bandwidth, high-latency networks:

```
CUBIC Window Growth:

Cwnd
  │                                            ┌──────────
  │                                       ┌────┘
  │                                  ┌────┘
  │                             ┌────┘
  │    Wmax ─────────────────  ┌┘
  │            ╲              /│
  │             ╲            / │
  │              ╲          /  │
  │               ╲        /   │
  │                ╲      /    │
  │                 ╲    /     │
  │                  ╲  /      │
  │                   ╲/       │
  │                 Wlast      │
  │                   │        │
  └────────────────────────────┼───────────────────► Time
                            Loss event

W(t) = C * (t - K)^3 + Wmax

Where:
  C = scaling constant (0.4)
  K = ∛(Wmax * β / C)  (time to reach Wmax)
  β = multiplicative decrease factor (0.7)
  Wmax = window size before last reduction
```

```c
// From net/ipv4/tcp_cubic.c
static void bictcp_cong_avoid(struct sock *sk, u32 ack, u32 acked) {
    struct tcp_sock *tp = tcp_sk(sk);
    struct bictcp *ca = inet_csk_ca(sk);

    if (!tcp_is_cwnd_limited(sk))
        return;

    if (tcp_in_slow_start(tp)) {
        // Slow start: exponential growth
        tcp_slow_start(tp, acked);
        return;
    }

    // Congestion avoidance: cubic function
    bictcp_update(ca, tcp_snd_cwnd(tp), acked);
    tcp_cong_avoid_ai(tp, ca->cnt, acked);
}

static void bictcp_update(struct bictcp *ca, u32 cwnd, u32 acked) {
    u32 delta, bic_target, max_cnt;
    u64 offs, t;

    // Calculate time since last window reduction
    t = (s32)(tcp_jiffies32 - ca->epoch_start);
    t += usecs_to_jiffies(ca->delay_min);

    // Calculate target cwnd using cubic function
    offs = ca->bic_K - t;  // Distance from K

    if (offs > 0) {
        // Left side of curve: below Wmax
        bic_target = ca->last_max_cwnd - (cube_factor * offs * offs * offs);
    } else {
        // Right side of curve: above Wmax
        bic_target = ca->last_max_cwnd + (cube_factor * offs * offs * offs);
    }

    // Calculate cnt: how many ACKs before incrementing cwnd
    if (bic_target > cwnd) {
        ca->cnt = cwnd / (bic_target - cwnd);
    } else {
        ca->cnt = 100 * cwnd;  // Very slow growth
    }
}
```

### 13.3 BBR: Bottleneck Bandwidth and RTT

BBR (developed by Google) uses a different approach: model the network path:

```
BBR Model:

                    ┌─────────────────────────────────────────────┐
                    │                Network Path                  │
                    │                                              │
   Sender ──────────┤  BtlBw (bottleneck bandwidth)               ├────── Receiver
                    │  RTprop (minimum RTT)                       │
                    │                                              │
                    │  Optimal point: BDP = BtlBw × RTprop        │
                    └─────────────────────────────────────────────┘

BBR's goal: send at exactly BtlBw rate, with BDP bytes in flight

States:
┌──────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  STARTUP ──────► DRAIN ──────► PROBE_BW ◄──────► PROBE_RTT           │
│                                    │                                  │
│  (Exponential     (Clear excess    (Steady state,   (Drain queue     │
│   growth to        queue from       cycle through    periodically    │
│   find BtlBw)      startup)         pacing gains)    to measure      │
│                                                       RTprop)         │
└──────────────────────────────────────────────────────────────────────┘
```

```c
// BBR state machine (simplified)
static void bbr_update_model(struct sock *sk, const struct rate_sample *rs) {
    struct bbr *bbr = inet_csk_ca(sk);

    // Update bottleneck bandwidth estimate
    bbr_update_bw(sk, rs);

    // Update RTT estimate
    bbr_update_min_rtt(sk, rs);

    // Update target cwnd
    bbr->target_cwnd = bbr_bdp(sk);  // BtlBw × RTprop

    // State machine transitions
    switch (bbr->mode) {
    case BBR_STARTUP:
        if (!bbr_full_bw_reached(sk))
            break;
        bbr->mode = BBR_DRAIN;
        bbr->pacing_gain = BBR_DRAIN_GAIN;  // 0.35
        break;

    case BBR_DRAIN:
        if (tcp_packets_in_flight(tp) <= bbr->target_cwnd) {
            bbr->mode = BBR_PROBE_BW;
        }
        break;

    case BBR_PROBE_BW:
        // Cycle through gains: 1.25, 0.75, 1, 1, 1, 1, 1, 1
        bbr_advance_cycle_phase(sk);
        // Occasionally enter PROBE_RTT
        if (bbr_should_probe_rtt(sk))
            bbr->mode = BBR_PROBE_RTT;
        break;

    case BBR_PROBE_RTT:
        // Reduce cwnd to 4 packets to drain queue
        // Measure true RTprop
        if (bbr_probe_rtt_done(sk))
            bbr->mode = BBR_PROBE_BW;
        break;
    }
}
```

### 13.4 Algorithm Comparison

```
Throughput vs Latency (High BDP Network: 1Gbps, 100ms RTT):

Algorithm │ Throughput │ Latency  │ Fairness │ Notes
──────────┼────────────┼──────────┼──────────┼────────────────────────────
Reno      │ 30%        │ Low      │ Good     │ Loss-based, poor in high BDP
CUBIC     │ 95%        │ High     │ Good     │ Fills buffers, causes bloat
BBR       │ 98%        │ Low      │ Poor*    │ Rate-based, queue-aware
BBRv2     │ 98%        │ Low      │ Better   │ Improved fairness, ECN-aware

* BBRv1 known to be unfair to loss-based algorithms in some conditions


RTT Fairness Problem:

Flow 1: RTT = 10ms   ┌─────────────────────────────────────────────┐
Flow 2: RTT = 100ms  │  With loss-based CC (CUBIC):                │
                     │    Flow 1 gets ~10x more bandwidth          │
                     │    (faster RTT = faster cwnd growth)         │
                     │                                              │
                     │  With BBR:                                   │
                     │    Both flows get similar bandwidth          │
                     │    (rate-based, not window-based)            │
                     └─────────────────────────────────────────────┘
```

### 13.5 Selecting Congestion Control

```bash
# View available algorithms
$ sysctl net.ipv4.tcp_available_congestion_control
net.ipv4.tcp_available_congestion_control = reno cubic bbr

# Change system default
$ sysctl -w net.ipv4.tcp_congestion_control=bbr

# Per-socket selection (in application)
setsockopt(fd, IPPROTO_TCP, TCP_CONGESTION, "bbr", 3);
```

---

## 14. Buffer Management and Memory Pressure

### 14.1 Socket Buffer Sizing

```
TCP Buffer Architecture:

Application
     │
     │ write(fd, data, len)
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Send Buffer (sk->sk_sndbuf)                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Unsent data │ Sent but unacked │ (sk_wmem_queued)                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
     │
     │ TCP segmentation + transmission
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Network                                                                 │
└─────────────────────────────────────────────────────────────────────────┘
     │
     │ Incoming packets
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Receive Buffer (sk->sk_rcvbuf)                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ In-order data │ Out-of-order data │ (sk_rmem_alloc)                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
     │
     │ read(fd, buf, len)
     ▼
Application
```

### 14.2 Automatic Buffer Sizing

Linux automatically tunes buffer sizes based on available memory and connection characteristics:

```c
// Buffer limits (from sysctl)
// net.ipv4.tcp_rmem = min default max
// net.ipv4.tcp_wmem = min default max

// Default values (bytes):
tcp_rmem: 4096  131072  6291456   // 4KB, 128KB, 6MB
tcp_wmem: 4096  16384   4194304   // 4KB, 16KB, 4MB

// Auto-tuning algorithm (simplified)
static void tcp_rcv_space_adjust(struct sock *sk) {
    struct tcp_sock *tp = tcp_sk(sk);

    // Calculate "goodput" - useful bytes per RTT
    u32 copied = tp->rcv_nxt - tp->copied_seq;
    u32 time = tcp_stamp_us_delta(tp->tcp_mstamp, tp->rcvq_space.time);

    // Estimate required buffer: 2 × BDP
    u32 space = 2 * (copied * tp->rcv_rtt_est.rtt_us / time);

    // Clamp to limits
    space = clamp(space, sysctl_tcp_rmem[0], sysctl_tcp_rmem[2]);

    if (space > sk->sk_rcvbuf) {
        sk->sk_rcvbuf = space;
        tcp_set_window_clamp(sk, space);
    }
}
```

### 14.3 Memory Pressure Handling

```
System Memory Pressure Levels:

                    ┌─────────────────────────────────────────────────────┐
                    │  tcp_memory_allocated (atomic counter)              │
                    └─────────────────────────────────────────────────────┘
                                          │
       ┌──────────────────────────────────┼──────────────────────────────────┐
       │                                  │                                  │
       ▼                                  ▼                                  ▼
┌─────────────────┐            ┌─────────────────────┐           ┌──────────────────┐
│    LOW          │            │     MODERATE        │           │     HIGH         │
│                 │            │                     │           │                  │
│ < tcp_mem[0]    │            │ tcp_mem[0]-[1]      │           │ > tcp_mem[1]     │
│                 │            │                     │           │                  │
│ Normal          │            │ Enter "memory       │           │ Severe pressure: │
│ operation       │            │ pressure" mode      │           │ - Collapse queues│
│                 │            │ - Reduce buffers    │           │ - Drop segments  │
│                 │            │ - Slower growth     │           │ - Prune OOO queue│
└─────────────────┘            └─────────────────────┘           └──────────────────┘

                    tcp_mem[2]: Hard limit - fail allocations
```

```c
// Memory pressure check
bool tcp_under_memory_pressure(const struct sock *sk) {
    if (mem_cgroup_sockets_enabled && sk->sk_memcg)
        return mem_cgroup_under_socket_pressure(sk->sk_memcg);

    return READ_ONCE(tcp_memory_pressure);
}

// Entering memory pressure
static void tcp_enter_memory_pressure(struct sock *sk) {
    if (!READ_ONCE(tcp_memory_pressure)) {
        WRITE_ONCE(tcp_memory_pressure, 1);
        // Trigger memory reclaim
        tcp_mem_reclaim(sk);
    }
}

// Actions under pressure
static bool tcp_prune_ofo_queue(struct sock *sk) {
    struct tcp_sock *tp = tcp_sk(sk);
    struct sk_buff *skb;

    // Drop out-of-order segments to free memory
    while ((skb = skb_rb_first(&tp->out_of_order_queue)) != NULL) {
        tcp_drop(sk, skb);
        if (!tcp_under_memory_pressure(sk))
            return true;  // Pressure relieved
    }
    return false;
}
```

### 14.4 Receive Window and Flow Control

```
Window Scaling and Receive Window:

Without window scaling (16-bit window):
  Max window = 65,535 bytes
  Max throughput on 100ms RTT = 655 KB/s = 5.2 Mbps  (unacceptable!)

With window scaling (RFC 7323):
  Window field shifted left by scale factor (0-14)
  Max window = 65,535 × 2^14 = 1,073,725,440 bytes ≈ 1GB

┌─────────────────────────────────────────────────────────────────────────┐
│  Window Calculation                                                      │
│                                                                          │
│  Advertised Window = min(                                                │
│      sk->sk_rcvbuf - sk->sk_rmem_alloc,  // Available buffer space      │
│      tp->rcv_ssthresh,                    // Slow-start threshold       │
│      tp->window_clamp                     // Maximum window             │
│  ) >> tp->rx_opt.rcv_wscale                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Zero Window Situation:

Receiver buffer full:
┌────────────────────────────────────────────────────────────────────────┐
│ ████████████████████████████████████████████████████████████████████  │
│ (Application not reading)                              Available: 0    │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                │ Advertise window = 0
                                ▼
                         Sender stops

Sender probes with Zero Window Probes:
  - Persist timer fires
  - Send 1-byte probe
  - Receiver responds with current window
  - When window opens, transmission resumes
```

---

## 15. TLS Integration with Sockets

### 15.1 TLS Architectural Options

```
Option 1: User-Space TLS (Traditional - OpenSSL, etc.)

Application
     │
     │ SSL_write(ssl, data, len)
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OpenSSL / BoringSSL / etc. (User Space)                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Encrypt data                                                    │    │
│  │  Build TLS record:                                               │    │
│  │    [Type][Version][Length][Encrypted Payload][MAC/Tag]          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
     │
     │ write(fd, encrypted_record, len)  (syscall)
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel TCP Stack                                                        │
│  (Sees opaque byte stream)                                               │
└─────────────────────────────────────────────────────────────────────────┘


Option 2: Kernel TLS (kTLS - Linux 4.13+)

Application
     │
     │ send(fd, plaintext, len, 0)  (after TLS handshake)
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel (TLS ULP - Upper Layer Protocol)                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  tls_sw_sendmsg() or tls_device_sendmsg()                       │    │
│  │  - Encrypt in kernel (SW) or offload to NIC (HW)                │    │
│  │  - Build TLS records                                             │    │
│  │  - Zero-copy possible with sendfile()                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  TCP Stack                                                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15.2 Kernel TLS (kTLS) Setup

```c
// Step 1: Normal TCP connection
int fd = socket(AF_INET, SOCK_STREAM, 0);
connect(fd, &addr, sizeof(addr));

// Step 2: Complete TLS handshake in user space (OpenSSL)
SSL *ssl = SSL_new(ctx);
SSL_set_fd(ssl, fd);
SSL_connect(ssl);  // TLS handshake

// Step 3: Extract crypto parameters
struct tls12_crypto_info_aes_gcm_128 crypto_info = {
    .info = {
        .version = TLS_1_2_VERSION,
        .cipher_type = TLS_CIPHER_AES_GCM_128,
    },
};
// Copy key, IV, sequence number from SSL session
SSL_export_keying_material(...);  // Or internal extraction

// Step 4: Enable kernel TLS
setsockopt(fd, SOL_TCP, TCP_ULP, "tls", sizeof("tls"));

// Step 5: Install TX crypto parameters
setsockopt(fd, SOL_TLS, TLS_TX, &crypto_info, sizeof(crypto_info));

// Step 6: Install RX crypto parameters (for receive-side kTLS)
setsockopt(fd, SOL_TLS, TLS_RX, &crypto_info_rx, sizeof(crypto_info_rx));

// Now: send(fd, plaintext) automatically encrypts in kernel
send(fd, "Hello, TLS!", 11, 0);
```

### 15.3 TLS Hardware Offload

Modern NICs (Mellanox, Intel) support TLS offload:

```
TLS Hardware Offload Architecture:

Application
     │ send(fd, plaintext, len)
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel TLS (tls_device_sendmsg)                                        │
│    - Mark sk_buff for hardware encryption                               │
│    - Attach crypto context to skb                                       │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NIC Driver                                                              │
│    - Pass plaintext + crypto context to hardware                        │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NIC Hardware (TLS Crypto Engine)                                        │
│    ┌───────────────────────────────────────────────────────────────┐    │
│    │  Encryption Engine (AES-GCM)                                   │    │
│    │    - Encrypt payload                                           │    │
│    │    - Compute authentication tag                                │    │
│    │    - Build TLS record                                          │    │
│    └───────────────────────────────────────────────────────────────┘    │
│    ┌───────────────────────────────────────────────────────────────┐    │
│    │  Transmit Engine                                               │    │
│    │    - Send encrypted packets on wire                            │    │
│    └───────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

Benefits:
  - Zero CPU usage for encryption
  - True zero-copy (DMA from user buffer, encrypt in NIC)
  - Lower latency
  - Higher throughput (40-100Gbps achievable)
```

### 15.4 TLS Record Structure

```
TLS 1.2 Record (AES-GCM):

┌─────────┬─────────┬─────────┬───────────────────────────────────┬────────┐
│  Type   │ Version │ Length  │          Encrypted Data           │  Tag   │
│  1 byte │ 2 bytes │ 2 bytes │         Variable length           │ 16 B   │
├─────────┼─────────┼─────────┼───────────────────────────────────┼────────┤
│   23    │ 03 03   │ 00 35   │ [Nonce 8B][Ciphertext][Padding]   │ [Auth] │
│ (App)   │ (TLS1.2)│ (53 B)  │                                   │        │
└─────────┴─────────┴─────────┴───────────────────────────────────┴────────┘
          │◄────────────── Authenticated ─────────────────────────►│


TLS 1.3 Record (simplified):

┌─────────┬─────────┬─────────┬───────────────────────────────────────────┐
│  Type   │ Version │ Length  │              Encrypted                    │
│  1 byte │ 2 bytes │ 2 bytes │  [Inner Type + Data + Padding + Tag]     │
├─────────┼─────────┼─────────┼───────────────────────────────────────────┤
│   23    │ 03 03   │ 00 XX   │  All content encrypted (including type)  │
│ (App)   │ (compat)│         │  Real type hidden inside                 │
└─────────┴─────────┴─────────┴───────────────────────────────────────────┘
```

### 15.5 TLS and TCP Interaction

```
TLS Record vs TCP Segment Boundaries:

TLS Record (16KB max recommended):
┌──────────────────────────────────────────────────────────────────────────┐
│  TLS Record (e.g., 16384 bytes)                                          │
└──────────────────────────────────────────────────────────────────────────┘

TCP segments (MSS ~1460):
┌───────────┬───────────┬───────────┬───────────┬ ... ┬───────────┐
│  Seg 1    │  Seg 2    │  Seg 3    │  Seg 4    │     │  Seg 12   │
│ 1460 B    │ 1460 B    │ 1460 B    │ 1460 B    │     │  724 B    │
└───────────┴───────────┴───────────┴───────────┴─────┴───────────┘

Head-of-Line Blocking Problem:
  - Cannot decrypt TLS record until ALL TCP segments received
  - Single lost segment blocks entire record
  - Solution: QUIC (see Section 16)


TLS False Start and 0-RTT:

Traditional TLS 1.2 (2-RTT):
┌────────┐                              ┌────────┐
│ Client │                              │ Server │
└───┬────┘                              └───┬────┘
    │───── ClientHello ─────────────────────►│  RTT 1
    │◄──── ServerHello, Cert, Done ──────────│
    │───── Key, ChangeCipher, Finished ─────►│  RTT 2
    │◄──── ChangeCipher, Finished ───────────│
    │═══════ Application Data ══════════════►│

TLS 1.3 (1-RTT, with 0-RTT resumption):
┌────────┐                              ┌────────┐
│ Client │                              │ Server │
└───┬────┘                              └───┬────┘
    │───── ClientHello + KeyShare ──────────►│  RTT 1
    │◄──── ServerHello + KeyShare + EE + Fin─│
    │───── Finished ═══ Application Data ═══►│  Data sent with RTT 1!
    │◄════ Application Data ═════════════════│

0-RTT Resumption (replay risk):
    │═══ ClientHello + 0-RTT Data ══════════►│  0 RTT!
    │◄════ Response ═════════════════════════│
```

---

## 16. QUIC and HTTP/3: The UDP Revolution

### 16.1 Why QUIC?

```
TCP+TLS Problems:

1. Head-of-Line Blocking (TCP level):
   ┌────────┬────────┬────────┬────────┬────────┐
   │ Pkt 1  │ Pkt 2  │ Pkt 3  │ Pkt 4  │ Pkt 5  │
   │  ✓     │  ✗     │  ✓     │  ✓     │  ✓     │  (Pkt 2 lost)
   └────────┴────────┴────────┴────────┴────────┘
                │
                └──► Pkts 3,4,5 buffered, waiting for Pkt 2 retransmit
                     Even if they belong to different HTTP streams!

2. Connection Setup Latency:
   TCP handshake: 1 RTT
   TLS handshake: 1-2 RTT
   Total: 2-3 RTT before first byte of data

3. Connection Migration:
   IP changes (WiFi → Cellular) → Connection dies
   Must complete new TCP+TLS handshake

4. Ossification:
   Middleboxes (firewalls, NATs) inspect TCP headers
   Prevents protocol evolution
```

### 16.2 QUIC Architecture

```
QUIC Stack vs TCP Stack:

TCP/TLS Stack:                    QUIC Stack:
┌─────────────────┐               ┌─────────────────┐
│   HTTP/2        │               │    HTTP/3       │
├─────────────────┤               ├─────────────────┤
│   TLS 1.2/1.3   │               │    QUIC         │
├─────────────────┤               │  (Crypto built  │
│   TCP           │               │   in, based on  │
├─────────────────┤               │   TLS 1.3)      │
│   IP            │               ├─────────────────┤
└─────────────────┘               │   UDP           │
                                  ├─────────────────┤
                                  │   IP            │
                                  └─────────────────┘

Why UDP?
  - Middleboxes pass UDP through unchanged
  - QUIC implemented in user space (can update without kernel)
  - Protocol details encrypted (prevents ossification)
```

### 16.3 QUIC Stream Multiplexing

```
QUIC eliminates head-of-line blocking:

Stream 1: ─────[Frame 1.1]────[Frame 1.2]────[Frame 1.3]────►
Stream 2: ─────────[Frame 2.1]────────[Frame 2.2]────────────►
Stream 3: ───────────────[Frame 3.1]─────────────────────────►

UDP Packets:
┌────────────────────────────────────────────────────────────────────────┐
│ Packet 1: [Header][Frame 1.1][Frame 2.1]                               │
│ Packet 2: [Header][Frame 1.2][Frame 3.1]  ◄── Lost, but...            │
│ Packet 3: [Header][Frame 2.2]             ◄── Delivered immediately!   │
│ Packet 4: [Header][Frame 1.3]             ◄── Delivered immediately!   │
└────────────────────────────────────────────────────────────────────────┘

With TCP:
  Packet 2 lost → Packets 3,4 blocked until retransmit received
  Streams 2 and 3 stalled even though their data was received

With QUIC:
  Packet 2 lost → Only Stream 1's Frame 1.2 waits
  Streams 2 and 3 continue immediately with received frames
  No cross-stream head-of-line blocking!
```

### 16.4 QUIC Connection IDs

```
Connection Migration with QUIC:

                Initial Connection (WiFi)
┌────────┐     src=192.168.1.10:52341      ┌────────┐
│ Client │ ◄───────────────────────────────► │ Server │
│        │     Connection ID: 0xABCD1234    │ :443   │
└────────┘                                  └────────┘

                Phone moves to cellular...

                Continued Connection (Cellular)
┌────────┐     src=10.0.0.5:49321  (NEW!)  ┌────────┐
│ Client │ ◄───────────────────────────────► │ Server │
│        │     Connection ID: 0xABCD1234    │ :443   │
└────────┘     (SAME!)                      └────────┘

Server recognizes connection by Connection ID, not by 4-tuple!
No handshake needed, connection continues seamlessly.

TCP would require:
  - New TCP connection
  - New TLS handshake
  - Restart any in-progress downloads
```

### 16.5 QUIC Packet Structure

```
QUIC Long Header (handshake):
┌─────────┬────────┬────────────┬────────────┬───────────────────────────┐
│ Header  │ Version│ DCID Len   │ SCID Len   │                           │
│ Byte    │ 4 B    │ + DCID     │ + SCID     │  Payload (encrypted)      │
└─────────┴────────┴────────────┴────────────┴───────────────────────────┘

QUIC Short Header (post-handshake):
┌─────────┬────────────────────┬──────────────┬─────────────────────────┐
│ Header  │ Destination        │ Packet       │                         │
│ Byte    │ Connection ID      │ Number       │  Payload (encrypted)    │
│ 1 B     │ Variable           │ 1-4 B        │                         │
└─────────┴────────────────────┴──────────────┴─────────────────────────┘

Payload contains QUIC Frames:
┌────────────┬────────────┬────────────┬────────────┐
│ STREAM     │ ACK        │ STREAM     │ CRYPTO     │
│ Frame      │ Frame      │ Frame      │ Frame      │
│ (Data)     │ (Acks)     │ (Data)     │ (Handshake)│
└────────────┴────────────┴────────────┴────────────┘
```

### 16.6 Chrome's QUIC Implementation

```
Chrome QUIC Architecture:

┌─────────────────────────────────────────────────────────────────────────┐
│  Chrome Network Service                                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  QuicStreamFactory                                               │    │
│  │    - Manages QUIC sessions                                       │    │
│  │    - Connection pooling (like HTTP/2)                           │    │
│  │    - Session resumption with 0-RTT                              │    │
│  └───────────────────────────────┬─────────────────────────────────┘    │
│                                  │                                       │
│  ┌───────────────────────────────▼─────────────────────────────────┐    │
│  │  QuicChromiumClientSession                                       │    │
│  │    - Per-origin QUIC session                                     │    │
│  │    - Multiple streams (HTTP requests) per session               │    │
│  │    - Handles connection migration                                │    │
│  └───────────────────────────────┬─────────────────────────────────┘    │
│                                  │                                       │
│  ┌───────────────────────────────▼─────────────────────────────────┐    │
│  │  QuicConnection                                                  │    │
│  │    - Packet assembly/parsing                                     │    │
│  │    - Congestion control (CUBIC or BBR)                          │    │
│  │    - Loss detection and recovery                                 │    │
│  └───────────────────────────────┬─────────────────────────────────┘    │
│                                  │                                       │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │
                                   │ UDP socket
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel UDP Stack                                                        │
│    - Simple datagram delivery                                            │
│    - No connection state (stateless from kernel's perspective)          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 16.7 QUIC vs TCP Performance

```
Connection Establishment:

                    Cold Start       Resumed
TCP + TLS 1.2       3 RTT            2 RTT
TCP + TLS 1.3       2 RTT            1 RTT (0-RTT data)
QUIC                1 RTT            0 RTT (data in first packet!)


Packet Loss Impact (multiple streams):

Scenario: 10 concurrent requests, 2% packet loss

TCP/HTTP/2:
  - All streams share one TCP connection
  - Loss blocks all streams until retransmit
  - Effective throughput significantly degraded

QUIC/HTTP/3:
  - Each stream independent at transport layer
  - Loss only blocks affected stream
  - Other streams continue at full speed
  - Better effective throughput under loss


Measured Improvements (Google data):
┌─────────────────────────────────────────────────────────────────────────┐
│  Metric                          │ Improvement vs TCP                   │
├──────────────────────────────────┼──────────────────────────────────────┤
│  Search page load time           │ 3.6% faster (desktop)               │
│                                  │ 15% faster (mobile, poor network)   │
├──────────────────────────────────┼──────────────────────────────────────┤
│  YouTube rebuffer rate           │ 18% reduction                        │
├──────────────────────────────────┼──────────────────────────────────────┤
│  Connection setup (0-RTT)        │ 100ms+ savings per connection       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 17. Zero-Copy Techniques

### 17.1 The Copy Problem

```
Traditional send() path (4 copies):

┌─────────────────────────────────────────────────────────────────────────┐
│  Application Buffer                                                      │
│  [User data.............................................]                │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Copy 1: user→kernel (write syscall)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel Socket Buffer                                                    │
│  [User data.............................................]                │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Copy 2: socket buf→skb (TCP segmentation)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  sk_buff (with headers)                                                  │
│  [ETH][IP][TCP][User data segment........................]               │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Copy 3: skb→DMA buffer (NIC driver)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NIC TX Ring Buffer (DMA)                                                │
│  [Full frame with data segment..............................]            │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Copy 4: DMA→wire (NIC hardware)
                                  ▼
                              [Network]

For file serving: add file→application copy = 5 copies total!
```

### 17.2 sendfile() - Kernel-to-Kernel Transfer

```c
// Traditional file serving:
char buf[65536];
int n = read(file_fd, buf, sizeof(buf));   // Copy 1: file → user
write(sock_fd, buf, n);                     // Copy 2: user → kernel

// With sendfile():
sendfile(sock_fd, file_fd, &offset, count);  // No user-space copy!

// sendfile path:
┌─────────────────────────────────────────────────────────────────────────┐
│  Page Cache (file data)                                                  │
│  [File content in kernel memory...............................]          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Direct reference (no copy)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  sk_buff (fragmented)                                                    │
│  Linear: [ETH][IP][TCP]                                                  │
│  Fragment: points to page cache page (refcount++)                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ DMA from original pages
                                  ▼
                              [Network]

Savings:
  - Eliminated user-space copy
  - Data stays in page cache, referenced by skb
  - NIC DMAs directly from page cache (with scatter-gather)
```

### 17.3 splice() and Pipes

```c
// splice: move data between file descriptors via pipe
// Great for proxying (socket→socket)

int pipefd[2];
pipe(pipefd);

// Move data from socket to pipe (no copy)
splice(sock_in, NULL, pipefd[1], NULL, len, SPLICE_F_MOVE);

// Move data from pipe to socket (no copy)
splice(pipefd[0], NULL, sock_out, NULL, len, SPLICE_F_MOVE);

// Total: 0 copies between user and kernel

┌────────────┐                     ┌────────────┐
│ sock_in    │                     │ sock_out   │
│ (client)   │                     │ (upstream) │
└─────┬──────┘                     └─────▲──────┘
      │                                  │
      │ splice                           │ splice
      ▼                                  │
┌─────────────────────────────────────────────────┐
│  Kernel Pipe Buffer                              │
│  [References to skb pages, no data copy]        │
└─────────────────────────────────────────────────┘

Used by: Nginx, HAProxy, and other high-performance proxies
```

### 17.4 TCP Zero-Copy Send (MSG_ZEROCOPY)

```c
// Enable zero-copy on socket
int one = 1;
setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));

// Send with zero-copy flag
send(fd, buf, len, MSG_ZEROCOPY);

// CRITICAL: Must wait for completion notification!
// Buffer must remain valid until kernel signals completion

struct msghdr msg = {0};
struct sock_extended_err *serr;
char control[100];
msg.msg_control = control;
msg.msg_controllen = sizeof(control);

// Poll for error queue notification
poll(fd, POLLERR);

// Receive completion notification
recvmsg(fd, &msg, MSG_ERRQUEUE);
for (struct cmsghdr *cm = CMSG_FIRSTHDR(&msg); cm; cm = CMSG_NXTHDR(&msg, cm)) {
    if (cm->cmsg_type == SO_EE_ORIGIN_ZEROCOPY) {
        serr = (struct sock_extended_err *)CMSG_DATA(cm);
        // serr->ee_data contains completion counter
        // Now safe to reuse/free buffer
    }
}
```

```
MSG_ZEROCOPY Flow:

┌─────────────────────────────────────────────────────────────────────────┐
│  Application Buffer (pinned in memory)                                   │
│  [User data...............................................]               │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Page pinned, reference passed
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  sk_buff (references user pages)                                         │
│  Linear: [Headers]                                                       │
│  Fragment: → User buffer pages (reference, not copy)                     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ DMA directly from user pages
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NIC (DMA engine)                                                        │
│  Reads directly from user-space buffer via IOMMU                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Transmission complete
                                  ▼
                          Completion notification via errqueue
                          (Application can now reuse buffer)

When to use:
  - Large buffers (>10KB typically)
  - High-throughput scenarios
  - Buffer reuse pattern works with async completion

When NOT to use:
  - Small messages (notification overhead > copy cost)
  - Cannot handle async buffer lifecycle
```

### 17.5 io_uring for Network I/O

```c
// io_uring: Async I/O with shared memory submission/completion queues
// Eliminates syscall overhead for high-throughput scenarios

struct io_uring ring;
io_uring_queue_init(256, &ring, 0);

// Submit send operation
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_send(sqe, sock_fd, buf, len, 0);
sqe->user_data = request_id;
io_uring_submit(&ring);

// Reap completions (can batch multiple)
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
int result = cqe->res;      // Bytes sent or error
uint64_t id = cqe->user_data;  // Our request ID
io_uring_cqe_seen(&ring, cqe);

// io_uring with fixed buffers (true zero-copy)
struct iovec iovs[16];
// ... fill iovs ...
io_uring_register_buffers(&ring, iovs, 16);

// Send using pre-registered buffer (kernel already knows the pages)
sqe = io_uring_get_sqe(&ring);
io_uring_prep_send_fixed(sqe, sock_fd, buf_index, len, 0);
```

```
io_uring Architecture:

┌─────────────────────────────────────────────────────────────────────────┐
│  User Space                                                              │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Submission Queue (SQ)                                            │   │
│  │  [sqe][sqe][sqe][sqe]...  ← Application writes requests          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Completion Queue (CQ)                                            │   │
│  │  [cqe][cqe][cqe][cqe]...  ← Application reads completions        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
         │                              ▲
         │ Shared memory (mmap)         │
         ▼                              │
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel                                                                  │
│                                                                          │
│  io_uring worker threads process SQEs, post CQEs                        │
│  Can run polling mode (no syscalls needed for submit!)                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Benefits:
  - Batched submission (one syscall for many ops)
  - Batched completion (one syscall to reap many results)
  - SQ polling mode: kernel polls SQ, no submit syscall needed
  - Fixed buffers: pre-register pages, eliminate per-I/O page pinning
```

---

## 18. Advanced: Connection Tracking and NAT

### 18.1 Netfilter Connection Tracking (conntrack)

```
Connection Tracking Architecture:

                       Incoming Packet
                            │
                            ▼
                    ┌───────────────┐
                    │  PRE_ROUTING  │  ← First hook
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────────────────────────────────────────┐
                    │  nf_conntrack_in()                                │
                    │                                                    │
                    │  1. Extract tuple from packet:                    │
                    │     {src_ip, src_port, dst_ip, dst_port, proto}   │
                    │                                                    │
                    │  2. Look up in conntrack hash table:              │
                    │     - Found: Update connection state              │
                    │     - Not found: Create new entry                 │
                    │                                                    │
                    │  3. Attach nf_conn to skb                         │
                    └───────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Routing     │
                    └───────┬───────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
        Local delivery            Forwarding
               │                         │
               ▼                         ▼
        ┌──────────────┐         ┌──────────────┐
        │ LOCAL_IN     │         │ FORWARD      │
        └──────────────┘         └──────────────┘
```

### 18.2 Connection Tracking States

```
TCP Connection Tracking States (nf_conntrack):

                        ┌─────────────────────────────┐
                        │           NEW               │
                        │  (First packet of flow)     │
                        └──────────────┬──────────────┘
                                       │
                                       │ SYN seen
                                       ▼
                        ┌─────────────────────────────┐
                        │       SYN_SENT              │
                        │  (Waiting for SYN+ACK)      │
                        └──────────────┬──────────────┘
                                       │
                                       │ SYN+ACK seen
                                       ▼
                        ┌─────────────────────────────┐
                        │       SYN_RECV              │
                        │  (Waiting for final ACK)    │
                        └──────────────┬──────────────┘
                                       │
                                       │ ACK seen
                                       ▼
                        ┌─────────────────────────────┐
                        │       ESTABLISHED           │
                        │  (Connection active)        │
                        │  Timeout: 5 days default    │
                        └──────────────┬──────────────┘
                                       │
                                       │ FIN seen
                                       ▼
                        ┌─────────────────────────────┐
                        │       FIN_WAIT              │
                        │  (Closing)                  │
                        └──────────────┬──────────────┘
                                       │
                                       │ FIN+ACK complete
                                       ▼
                        ┌─────────────────────────────┐
                        │       TIME_WAIT             │
                        │  Timeout: 120s              │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
                                   [Removed]


Conntrack Entry Structure:

┌─────────────────────────────────────────────────────────────────────────┐
│  struct nf_conn                                                          │
│                                                                          │
│  Original direction tuple:                                               │
│    {src: 192.168.1.10:52341, dst: 93.184.216.34:443, proto: TCP}       │
│                                                                          │
│  Reply direction tuple:                                                  │
│    {src: 93.184.216.34:443, dst: 192.168.1.10:52341, proto: TCP}       │
│                                                                          │
│  Status flags:                                                           │
│    IPS_CONFIRMED     - Seen packets in both directions                  │
│    IPS_ASSURED       - Seen "real" traffic (not just SYN)               │
│    IPS_EXPECTED      - Created from expectation (FTP, SIP)              │
│    IPS_NAT_MASK      - NAT applied                                       │
│    IPS_SEQ_ADJUST    - Sequence adjustment needed                       │
│                                                                          │
│  Timeout: when to expire this entry                                      │
│  Mark: user-defined mark (for routing decisions)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 18.3 NAT Implementation

```
SNAT (Source NAT) - Outgoing:

Internal host                  NAT Gateway                  External Server
192.168.1.10                   203.0.113.5                  93.184.216.34

    │                               │                               │
    │ src=192.168.1.10:52341       │                               │
    │ dst=93.184.216.34:443        │                               │
    │──────────────────────────────►│                               │
    │                               │                               │
    │                               │ POSTROUTING hook:             │
    │                               │ SNAT 192.168.1.10 → 203.0.113.5
    │                               │ Update conntrack:             │
    │                               │   orig: 192.168.1.10:52341    │
    │                               │   reply: 93.184.216.34:443    │
    │                               │   nat.src: 203.0.113.5:52341  │
    │                               │                               │
    │                               │ src=203.0.113.5:52341         │
    │                               │ dst=93.184.216.34:443         │
    │                               │──────────────────────────────►│
    │                               │                               │
    │                               │ src=93.184.216.34:443         │
    │                               │ dst=203.0.113.5:52341         │
    │                               │◄──────────────────────────────│
    │                               │                               │
    │                               │ PREROUTING hook:              │
    │                               │ Lookup conntrack, find NAT    │
    │                               │ DNAT 203.0.113.5 → 192.168.1.10
    │                               │                               │
    │ src=93.184.216.34:443        │                               │
    │ dst=192.168.1.10:52341       │                               │
    │◄──────────────────────────────│                               │


Port Allocation for Many-to-One NAT:

Many internal hosts sharing one external IP:

┌──────────────────┐
│ 192.168.1.10     │───┐
│   :52341         │   │
├──────────────────┤   │     ┌────────────────────────────────────┐
│ 192.168.1.11     │───┼────►│  NAT Gateway (203.0.113.5)         │
│   :52341         │   │     │                                     │
├──────────────────┤   │     │  Must use different external ports: │
│ 192.168.1.12     │───┘     │    192.168.1.10:52341 → :52341      │
│   :52341         │         │    192.168.1.11:52341 → :52342      │
└──────────────────┘         │    192.168.1.12:52341 → :52343      │
                             │                                     │
All using same internal      │  Conntrack table tracks mappings    │
port number!                 └────────────────────────────────────┘

Port exhaustion:
  - 65535 ports per external IP
  - Minus reserved ports (1-1023)
  - ~64000 concurrent connections per external IP per destination
  - More destinations = more connections possible (5-tuple uniqueness)
```

### 18.4 Conntrack Scaling

```
Conntrack Hash Table:

Default: 65536 buckets (tunable via hashsize parameter)
Each bucket: linked list of nf_conn entries

Performance considerations:
  - Lookup is O(bucket_size), ideally O(1) with good hashing
  - Lock per bucket (RCU for reads)
  - Large tables = more memory but better distribution

Tuning:
  # Maximum tracked connections
  sysctl net.netfilter.nf_conntrack_max = 1000000

  # Hash table size (buckets)
  echo 262144 > /sys/module/nf_conntrack/parameters/hashsize

  # Ideal: max / buckets ≈ 4-8 entries per bucket

Memory usage:
  Each nf_conn ≈ 300-400 bytes
  1M connections ≈ 300-400 MB just for conntrack
```

---

## 19. Chrome Network Stack Deep Dive

### 19.1 Architecture Overview

```
Chrome Multi-Process Architecture for Networking:

┌─────────────────────────────────────────────────────────────────────────┐
│                         Browser Process                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  UI, tabs management, navigation decisions                      │    │
│  │  ProfileNetworkContextService (manages contexts)                │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │ Mojo IPC
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Network Service Process                             │
│                      (Since Chrome 67+)                                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  NetworkContext (per-profile)                                     │   │
│  │    - Cookie store                                                 │   │
│  │    - HTTP cache                                                   │   │
│  │    - Certificate verifier                                         │   │
│  │    - Proxy resolver                                               │   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────────┐│   │
│  │  │  URLLoaderFactory                                            ││   │
│  │  │    - Creates URLLoader per request                           ││   │
│  │  │    - Policy enforcement (CORS, etc.)                         ││   │
│  │  └──────────────────────────────────────────────────────────────┘│   │
│  │                                                                   │   │
│  │  ┌──────────────────────────────────────────────────────────────┐│   │
│  │  │  HttpNetworkSession                                          ││   │
│  │  │    - Connection pooling                                       ││   │
│  │  │    - SPDY/HTTP2 session pool                                 ││   │
│  │  │    - QUIC session pool                                        ││   │
│  │  │    - Socket pool groups (per-origin)                         ││   │
│  │  └──────────────────────────────────────────────────────────────┘│   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
         │                                   │
         │ TCP/QUIC                          │ DNS
         ▼                                   ▼
┌─────────────────────────────┐     ┌────────────────────────────────────┐
│  OS Socket Layer            │     │  DNS Resolver                       │
│  (Kernel TCP/UDP)           │     │  (DoH, system resolver)            │
└─────────────────────────────┘     └────────────────────────────────────┘
```

### 19.2 Connection Pool Implementation

```cpp
// Simplified from net/socket/client_socket_pool_manager.h

// Pool hierarchy:
//   ClientSocketPoolManager
//     └── TransportClientSocketPool (TCP connections)
//           └── Groups (per-destination)
//                 └── Sockets (idle, connecting, assigned)

class ClientSocketPoolManager {
    // Limits
    static const int kMaxSocketsPerGroup = 6;       // Per origin
    static const int kMaxSockets = 256;              // Total
    static const int kMaxSocketsPerProxy = 32;

    // Pool lookup
    TransportClientSocketPool* GetSocketPool(
        const GroupId& group_id);  // GroupId = scheme://host:port
};

// Group represents one origin's connection pool
class Group {
    // Sockets in this group
    std::list<IdleSocket> idle_sockets_;       // Available for reuse
    std::set<ConnectingSocket*> connecting_;    // Handshake in progress
    std::set<AssignedSocket*> assigned_;        // In use by requests

    // Pending requests waiting for socket
    RequestQueue pending_requests_;

    // Connection timing
    base::TimeDelta connect_timeout_;
    base::TimeDelta idle_timeout_ = base::Minutes(5);
};
```

```
Socket Group States:

Group for "https://example.com":
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Idle Sockets (ready for immediate use):                                │
│  ┌────────┐ ┌────────┐                                                  │
│  │ Sock 1 │ │ Sock 2 │    Idle timeout: 5 minutes                      │
│  │ (idle) │ │ (idle) │    If not used, closed and removed              │
│  └────────┘ └────────┘                                                  │
│                                                                          │
│  Connecting Sockets (handshake in progress):                            │
│  ┌────────┐                                                              │
│  │ Sock 3 │    TCP connect + TLS handshake ongoing                      │
│  │ (conn) │    Will move to idle or assigned when complete             │
│  └────────┘                                                              │
│                                                                          │
│  Assigned Sockets (actively serving request):                           │
│  ┌────────┐ ┌────────┐ ┌────────┐                                       │
│  │ Sock 4 │ │ Sock 5 │ │ Sock 6 │    Serving HTTP transactions         │
│  │(assign)│ │(assign)│ │(assign)│    Return to idle when done          │
│  └────────┘ └────────┘ └────────┘                                       │
│                                                                          │
│  Count: 6/6 (at limit for this group)                                   │
│                                                                          │
│  Pending Requests (waiting for socket):                                 │
│  [Request 7] → [Request 8] → [Request 9]                                │
│  Will be served when sockets become available                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 19.3 HTTP/2 Session Multiplexing

```
HTTP/2 Session Pool:

┌─────────────────────────────────────────────────────────────────────────┐
│  SpdySessionPool                                                         │
│                                                                          │
│  Key: SpdySessionKey (host, port, proxy, privacy mode, network anonymization key)
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Session for "https://example.com:443"                             │ │
│  │                                                                     │ │
│  │  TCP Socket → TLS → HTTP/2                                         │ │
│  │                                                                     │ │
│  │  Active Streams:                                                    │ │
│  │    Stream 1:  GET /page.html      (Tab 1)                          │ │
│  │    Stream 3:  GET /style.css      (Tab 1)                          │ │
│  │    Stream 5:  GET /api/data       (Tab 2)                          │ │
│  │    Stream 7:  POST /submit        (Tab 3)                          │ │
│  │                                                                     │ │
│  │  Max concurrent streams: 100 (server-configured)                   │ │
│  │  Flow control: per-stream and per-connection                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Why multiple tabs can share one TCP connection:

Tab 1: Loads https://example.com/page1
  │
  ├── Request: GET /page1 → Stream 1
  ├── Request: GET /style.css → Stream 3
  └── Request: GET /script.js → Stream 5

Tab 2: Loads https://example.com/page2  (same origin!)
  │
  ├── Reuses existing HTTP/2 session
  ├── Request: GET /page2 → Stream 7
  └── Request: GET /data.json → Stream 9

Single TCP connection serves both tabs!
Streams interleaved for optimal performance.
```

### 19.4 Request Lifecycle

```
URL Request Flow:

┌─────────────────────────────────────────────────────────────────────────┐
│  Renderer Process (Tab)                                                  │
│                                                                          │
│  JavaScript: fetch('https://api.example.com/data')                      │
│                    │                                                     │
│                    ▼                                                     │
│  Blink: ResourceFetcher → ResourceLoader                                │
│                    │                                                     │
└────────────────────┼────────────────────────────────────────────────────┘
                     │ Mojo IPC (URLLoader interface)
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Network Service Process                                                 │
│                                                                          │
│  URLLoaderFactory::CreateLoaderAndStart()                               │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  URLLoader                                                        │   │
│  │    │                                                              │   │
│  │    ├── CORS check                                                 │   │
│  │    ├── Cookie policy                                              │   │
│  │    ├── Check HTTP cache                                           │   │
│  │    │     │                                                        │   │
│  │    │     ├── Cache hit? → Return cached response                  │   │
│  │    │     └── Cache miss? → Continue to network                    │   │
│  │    │                                                              │   │
│  │    └── HttpNetworkTransaction                                     │   │
│  └──────────────┬───────────────────────────────────────────────────┘   │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  HttpNetworkTransaction                                           │   │
│  │    │                                                              │   │
│  │    ├── Resolve proxy (PAC script if configured)                   │   │
│  │    │                                                              │   │
│  │    ├── DNS resolution (may be cached)                             │   │
│  │    │                                                              │   │
│  │    └── HttpStreamFactory::RequestStream()                         │   │
│  │          │                                                        │   │
│  │          ├── Check for existing HTTP/2 session → Reuse           │   │
│  │          ├── Check for existing QUIC session → Reuse             │   │
│  │          └── No session? → Get socket from pool                  │   │
│  └──────────────┬───────────────────────────────────────────────────┘   │
│                 │                                                        │
│                 ▼                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Socket Pool                                                      │   │
│  │    │                                                              │   │
│  │    ├── Idle socket available? → Assign it                         │   │
│  │    └── No idle socket?                                            │   │
│  │          ├── Under limit? → Create new connection                 │   │
│  │          └── At limit? → Queue request                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 19.5 Preconnect and Prefetch

```
Chrome's Proactive Connection Warming:

1. Navigation Predictor:
   - Observes user behavior (hovering over links, etc.)
   - Predicts likely navigation targets
   - Triggers preconnect

2. Preconnect (establish connection before click):
   ┌─────────────────────────────────────────────────────────────────────┐
   │  User hovers over link to "https://example.com/page2"              │
   │                          │                                          │
   │                          ▼                                          │
   │  Predictor: "User likely to click"                                  │
   │                          │                                          │
   │                          ▼                                          │
   │  network::mojom::NetworkContext::PreconnectSockets(                │
   │      url = "https://example.com",                                   │
   │      num_sockets = 2,                                               │
   │      allow_credentials = true                                       │
   │  )                                                                  │
   │                          │                                          │
   │                          ▼                                          │
   │  Socket Pool: Start TCP + TLS handshake                            │
   │                          │                                          │
   │                          ▼                                          │
   │  When user clicks: connection already established!                 │
   │  Page load latency reduced by ~100-300ms                           │
   └─────────────────────────────────────────────────────────────────────┘

3. DNS Prefetch (resolve domain before needed):
   <link rel="dns-prefetch" href="//cdn.example.com">

   Chrome resolves cdn.example.com in background
   Cache warm when actual request made

4. Prerender (full page load in hidden tab):
   <link rel="prerender" href="/next-page">

   Entire page loaded invisibly
   When user navigates: instant display
```

### 19.6 Connection Coalescing

```
HTTP/2 Connection Coalescing (RFC 7540):

Same certificate can serve multiple hostnames:

Certificate Subject Alternative Names:
  - example.com
  - www.example.com
  - api.example.com
  - cdn.example.com

IP address resolution:
  example.com     → 93.184.216.34
  www.example.com → 93.184.216.34  (same IP)
  api.example.com → 93.184.216.34  (same IP)
  cdn.example.com → 104.18.32.68   (different IP!)

Connection coalescing decision:

┌─────────────────────────────────────────────────────────────────────────┐
│  Existing HTTP/2 connection to example.com (93.184.216.34:443)         │
│                                                                          │
│  New request to www.example.com:                                        │
│    1. Certificate covers www.example.com? ✓                            │
│    2. DNS resolves to same IP? ✓                                       │
│    → COALESCE: Use existing connection                                  │
│                                                                          │
│  New request to api.example.com:                                        │
│    1. Certificate covers api.example.com? ✓                            │
│    2. DNS resolves to same IP? ✓                                       │
│    → COALESCE: Use existing connection                                  │
│                                                                          │
│  New request to cdn.example.com:                                        │
│    1. Certificate covers cdn.example.com? ✓                            │
│    2. DNS resolves to same IP? ✗ (104.18.32.68 ≠ 93.184.216.34)       │
│    → NO COALESCING: Open new connection                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Result: 3 origins served by 1 connection + 1 separate connection
Instead of 4 separate connections
```

---

## 20. Debugging and Observability

### 20.1 ss and netstat Commands

```bash
# ss (socket statistics) - modern replacement for netstat
# Much faster for large connection counts

# All TCP connections with process info
ss -tnp

# Listening sockets
ss -tlnp

# All sockets with extended info
ss -tnpe

# Filter by state
ss -t state established
ss -t state time-wait
ss -t state syn-sent

# Filter by port
ss -tn 'sport = :443'
ss -tn 'dport = :443'

# Filter by address
ss -tn 'src 192.168.1.0/24'
ss -tn 'dst 93.184.216.34'

# Combined filters
ss -tn 'sport = :443 and dst 10.0.0.0/8'

# Show timer information
ss -tno
# Output: timer:(keepalive,25sec,0)

# Show memory usage
ss -tnm
# Output: skmem:(r0,rb131072,t0,tb46080,f0,w0,o0,bl0,d0)
#   r: receive queue bytes
#   rb: receive buffer size
#   t: transmit queue bytes
#   tb: transmit buffer size
#   f: forward allocated memory
#   w: write queue bytes
#   o: option memory
#   bl: backlog queue bytes
#   d: drop count

# Show internal TCP info
ss -ti
# Output includes:
#   cubic                    # Congestion control algorithm
#   wscale:7,7              # Window scale factors
#   rto:204                 # Retransmission timeout (ms)
#   rtt:1.234/0.567         # RTT/RTT variance (ms)
#   ato:40                  # ACK timeout
#   mss:1448                # Maximum segment size
#   pmtu:1500               # Path MTU
#   rcvmss:1448             # Received MSS
#   advmss:1448             # Advertised MSS
#   cwnd:10                 # Congestion window (segments)
#   ssthresh:7              # Slow start threshold
#   bytes_sent:12345        # Total bytes sent
#   bytes_acked:12340       # Bytes acknowledged
#   bytes_received:67890    # Bytes received
#   segs_out:100            # Segments sent
#   segs_in:95              # Segments received
#   data_segs_out:80        # Data segments sent
#   data_segs_in:75         # Data segments received
#   send 1234567bps         # Send bandwidth estimate
#   lastsnd:100             # Time since last send (ms)
#   lastrcv:50              # Time since last receive (ms)
#   lastack:50              # Time since last ACK (ms)
#   pacing_rate 2345678bps  # Pacing rate
#   delivery_rate 1234567bps # Delivery rate
#   delivered:80            # Packets delivered
#   busy:5000ms             # Time socket was busy
#   rcv_rtt:1.5             # Receiver RTT estimate
#   rcv_space:29200         # Receive window space
#   rcv_ssthresh:64088      # Receiver slow start threshold
#   minrtt:0.5              # Minimum RTT observed
```

### 20.2 /proc/net Files

```bash
# /proc/net/tcp - Raw TCP socket table
cat /proc/net/tcp

# Columns:
#   sl: slot number
#   local_address: hex IP:port
#   rem_address: hex IP:port
#   st: state (0A=LISTEN, 01=ESTABLISHED, etc.)
#   tx_queue:rx_queue: transmit/receive queue sizes
#   tr:tm->when: timer type and value
#   retrnsmt: retransmit count
#   uid: owner user ID
#   timeout: timeout value
#   inode: socket inode number

# Decode hex address: 0100007F:0050 = 127.0.0.1:80
# (bytes reversed due to little-endian)

# TCP states in hex:
#   01 = ESTABLISHED
#   02 = SYN_SENT
#   03 = SYN_RECV
#   04 = FIN_WAIT1
#   05 = FIN_WAIT2
#   06 = TIME_WAIT
#   07 = CLOSE
#   08 = CLOSE_WAIT
#   09 = LAST_ACK
#   0A = LISTEN
#   0B = CLOSING

# /proc/net/sockstat - Socket statistics summary
cat /proc/net/sockstat
# sockets: used 1234
# TCP: inuse 100 orphan 5 tw 50 alloc 200 mem 1000
# UDP: inuse 20 mem 100
# UDPLITE: inuse 0
# RAW: inuse 0
# FRAG: inuse 0 memory 0

# /proc/net/netstat - Extended network statistics
cat /proc/net/netstat
# TcpExt: SyncookiesSent SyncookiesRecv SyncookiesFailed ...
# IpExt: InNoRoutes InTruncatedPkts ...

# Key TcpExt counters:
#   SyncookiesSent: SYN cookies sent (SYN flood defense)
#   TCPBacklogDrop: Drops due to full backlog
#   TCPTimeWaitOverflow: TIME_WAIT bucket overflow
#   TCPFastRetrans: Fast retransmissions
#   TCPSlowStartRetrans: Slow start retransmissions
#   TCPLossProbes: Tail loss probes sent
#   TCPLossProbeRecovery: Recovered via TLP
#   TCPSackRecovery: Recovered via SACK
#   TCPOFOQueue: Out-of-order packets queued
#   TCPOFODrop: Out-of-order packets dropped
#   TCPOFOMerge: Out-of-order packets merged
#   TCPChallengeACK: Challenge ACKs sent
#   TCPSYNChallenge: SYN challenges received
#   TCPSpuriousRtxHostQueues: Spurious retransmits
#   TCPAutoCorking: Auto-corking events
#   TCPOrigDataSent: Original data segments sent
#   TCPHystartTrainDetect: Hystart train detection
#   TCPHystartTrainCwnd: Hystart cwnd at train detection
#   TCPHystartDelayDetect: Hystart delay detection
#   TCPHystartDelayCwnd: Hystart cwnd at delay detection
```

### 20.3 eBPF Tracing

```c
// BPF program to trace TCP connection establishment
// Using bpftrace syntax

// Trace connect() calls
tracepoint:syscalls:sys_enter_connect
{
    @connect_start[tid] = nsecs;
}

tracepoint:syscalls:sys_exit_connect
/args->ret == 0/
{
    $latency = (nsecs - @connect_start[tid]) / 1000000;
    printf("connect latency: %d ms\n", $latency);
    @connect_latency = hist($latency);
    delete(@connect_start[tid]);
}

// Trace TCP state changes
tracepoint:tcp:tcp_set_state
{
    $sk = (struct sock *)args->skaddr;
    $newstate = args->newstate;
    $oldstate = args->oldstate;

    printf("TCP state: %d -> %d, sport=%d dport=%d\n",
           $oldstate, $newstate,
           $sk->__sk_common.skc_num,
           $sk->__sk_common.skc_dport);
}

// Trace TCP retransmissions
tracepoint:tcp:tcp_retransmit_skb
{
    $sk = (struct sock *)args->skaddr;
    printf("Retransmit: %s:%d -> %s:%d, segs=%d\n",
           ntop($sk->__sk_common.skc_rcv_saddr),
           $sk->__sk_common.skc_num,
           ntop($sk->__sk_common.skc_daddr),
           ntohs($sk->__sk_common.skc_dport),
           args->segs);
    @retransmits = count();
}

// Trace socket buffer allocation
kprobe:__alloc_skb
{
    @skb_alloc = count();
    @skb_size = hist(arg1);  // size argument
}
```

```bash
# Using bpftrace one-liners:

# Count TCP connections by state
bpftrace -e 'tracepoint:tcp:tcp_set_state { @[args->newstate] = count(); }'

# Histogram of TCP RTT
bpftrace -e 'kprobe:tcp_rcv_established {
    $sk = (struct sock *)arg0;
    $tp = (struct tcp_sock *)$sk;
    @rtt = hist($tp->srtt_us >> 3);
}'

# Track socket memory usage
bpftrace -e 'kprobe:sk_mem_charge { @mem[comm] = sum(arg1); }'

# Trace DNS lookups
bpftrace -e 'uprobe:/lib/x86_64-linux-gnu/libc.so.6:getaddrinfo {
    printf("DNS lookup: %s\n", str(arg0));
}'
```

### 20.4 Wireshark and tcpdump

```bash
# tcpdump basics
tcpdump -i eth0 -n port 443

# Capture to file for Wireshark analysis
tcpdump -i eth0 -w capture.pcap -s 0 port 443

# Filter expressions
tcpdump 'tcp port 443 and host 93.184.216.34'
tcpdump 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0'  # SYN or FIN
tcpdump 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0'  # SYN only

# Show TCP sequence numbers
tcpdump -S -n port 443

# Verbose output with hex dump
tcpdump -X -n port 443

# Capture ring buffer (rotate files)
tcpdump -i eth0 -w capture-%H%M.pcap -G 3600 -W 24 port 443
# Creates hourly files, keeps 24 hours

# Wireshark display filters (different syntax):
# tcp.port == 443
# tcp.flags.syn == 1 && tcp.flags.ack == 0
# tcp.analysis.retransmission
# tcp.analysis.duplicate_ack
# tcp.analysis.zero_window
# http2
# tls.handshake.type == 1  # Client Hello
# tls.handshake.type == 2  # Server Hello
```

### 20.5 Chrome Network Internals

```
chrome://net-internals/ - Chrome's network debugging tool

Key sections:

1. Events (chrome://net-internals/#events)
   - Real-time log of all network events
   - Filter by type: URL_REQUEST, SOCKET, HTTP2_SESSION, QUIC_SESSION
   - Shows timing, errors, connection reuse

2. Sockets (chrome://net-internals/#sockets)
   - Active socket pools
   - Idle sockets per group
   - Connection limits and usage

3. HTTP/2 (chrome://net-internals/#http2)
   - Active SPDY/HTTP2 sessions
   - Stream counts
   - Settings negotiated

4. QUIC (chrome://net-internals/#quic)
   - Active QUIC sessions
   - Connection IDs
   - Stream statistics

5. DNS (chrome://net-internals/#dns)
   - DNS cache contents
   - Resolution times
   - DoH status

6. Export (chrome://net-internals/#export)
   - Export logs for offline analysis
   - JSON format with all events

Example event log for a request:

t=12345 [st=0] +URL_REQUEST_START
                --> url = "https://example.com/page"
                --> method = "GET"
t=12346 [st=1] +HTTP_CACHE_GET_BACKEND
t=12347 [st=2] -HTTP_CACHE_GET_BACKEND
                --> net_error = -2 (ERR_FAILED)
t=12348 [st=3] +HTTP_STREAM_REQUEST
t=12349 [st=4]   HTTP_STREAM_REQUEST_BOUND_TO_JOB
                 --> source_dependency = 54321 (HTTP_STREAM_JOB)
t=12400 [st=55] -HTTP_STREAM_REQUEST
t=12401 [st=56] +HTTP_TRANSACTION_SEND_REQUEST
t=12402 [st=57]   HTTP_TRANSACTION_SEND_REQUEST_HEADERS
                  --> GET /page HTTP/1.1
                      Host: example.com
t=12403 [st=58] -HTTP_TRANSACTION_SEND_REQUEST
t=12450 [st=105] +HTTP_TRANSACTION_READ_HEADERS
t=12500 [st=155] -HTTP_TRANSACTION_READ_HEADERS
                  --> HTTP/1.1 200 OK
t=12501 [st=156] +HTTP_TRANSACTION_READ_BODY
t=12600 [st=255] -HTTP_TRANSACTION_READ_BODY
t=12601 [st=256] -URL_REQUEST_START
```

---

## 21. Performance Tuning

### 21.1 Kernel Sysctl Parameters

```bash
# ============================================================
# TCP Buffer Sizes
# ============================================================

# Receive buffer: min, default, max (bytes)
net.ipv4.tcp_rmem = 4096 131072 6291456
#   4KB minimum (small connections)
#   128KB default (most connections)
#   6MB maximum (high-bandwidth connections)

# Send buffer: min, default, max (bytes)
net.ipv4.tcp_wmem = 4096 16384 4194304
#   4KB minimum
#   16KB default
#   4MB maximum

# Total TCP memory: min, pressure, max (pages, not bytes!)
net.ipv4.tcp_mem = 94500 126000 188000
#   At 'pressure' threshold, kernel starts reclaiming
#   At 'max', new allocations fail

# Enable auto-tuning (default: on)
net.ipv4.tcp_moderate_rcvbuf = 1

# ============================================================
# Connection Handling
# ============================================================

# Maximum SYN backlog (half-open connections)
net.ipv4.tcp_max_syn_backlog = 65535

# Maximum listen backlog (completed connections waiting accept)
net.core.somaxconn = 65535

# Enable SYN cookies (SYN flood protection)
net.ipv4.tcp_syncookies = 1

# SYN retries (initial connection)
net.ipv4.tcp_syn_retries = 3
#   Default 6 = ~127 seconds total
#   3 = ~15 seconds total

# SYN-ACK retries (server side)
net.ipv4.tcp_synack_retries = 3

# ============================================================
# TIME_WAIT Handling
# ============================================================

# TIME_WAIT bucket count
net.ipv4.tcp_max_tw_buckets = 262144

# Enable TIME_WAIT reuse (for outgoing connections)
net.ipv4.tcp_tw_reuse = 1
#   Allows reusing TIME_WAIT sockets for new outgoing connections
#   Safe because timestamps prevent old packet confusion

# ============================================================
# Keepalive
# ============================================================

# Time before sending first keepalive probe
net.ipv4.tcp_keepalive_time = 600
#   Default 7200 (2 hours) - too long for most uses

# Interval between keepalive probes
net.ipv4.tcp_keepalive_intvl = 60

# Number of probes before declaring dead
net.ipv4.tcp_keepalive_probes = 5

# ============================================================
# Congestion Control
# ============================================================

# Available algorithms
net.ipv4.tcp_available_congestion_control = reno cubic bbr

# Default algorithm
net.ipv4.tcp_congestion_control = bbr

# Enable ECN (Explicit Congestion Notification)
net.ipv4.tcp_ecn = 1

# ============================================================
# Fast Open
# ============================================================

# Enable TCP Fast Open
net.ipv4.tcp_fastopen = 3
#   1 = client only
#   2 = server only
#   3 = both

# ============================================================
# Port Range
# ============================================================

# Ephemeral port range
net.ipv4.ip_local_port_range = 1024 65535
#   Default: 32768 60999 (~28000 ports)
#   Expanded: 1024 65535 (~64000 ports)

# ============================================================
# Timestamps and SACK
# ============================================================

# Enable timestamps (for RTT measurement, PAWS)
net.ipv4.tcp_timestamps = 1

# Enable SACK (Selective Acknowledgment)
net.ipv4.tcp_sack = 1

# Enable DSACK (Duplicate SACK)
net.ipv4.tcp_dsack = 1

# Enable FACK (Forward Acknowledgment)
net.ipv4.tcp_fack = 1

# ============================================================
# Window Scaling
# ============================================================

# Enable window scaling (for windows > 64KB)
net.ipv4.tcp_window_scaling = 1

# ============================================================
# Orphan Sockets
# ============================================================

# Maximum orphaned sockets (closed but not yet freed)
net.ipv4.tcp_max_orphans = 262144

# FIN timeout (how long to wait for FIN-ACK)
net.ipv4.tcp_fin_timeout = 30
#   Default 60 - reduce for faster cleanup
```

### 21.2 Socket Options

```c
// ============================================================
// Buffer Sizes
// ============================================================

// Set receive buffer size
int rcvbuf = 1048576;  // 1MB
setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf));
// Note: kernel doubles this value (for bookkeeping overhead)
// Actual buffer = 2 * rcvbuf

// Set send buffer size
int sndbuf = 1048576;
setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

// Force buffer size (bypass rmem_max/wmem_max limits)
// Requires CAP_NET_ADMIN
setsockopt(fd, SOL_SOCKET, SO_RCVBUFFORCE, &rcvbuf, sizeof(rcvbuf));
setsockopt(fd, SOL_SOCKET, SO_SNDBUFFORCE, &sndbuf, sizeof(sndbuf));

// ============================================================
// TCP-Specific Options
// ============================================================

// Disable Nagle's algorithm (send immediately)
int nodelay = 1;
setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &nodelay, sizeof(nodelay));
// Use for latency-sensitive applications
// Trade-off: more small packets, higher overhead

// Enable TCP keepalive
int keepalive = 1;
setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &keepalive, sizeof(keepalive));

// Keepalive parameters (per-socket override of sysctl)
int keepidle = 60;   // Seconds before first probe
int keepintvl = 10;  // Seconds between probes
int keepcnt = 5;     // Number of probes
setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE, &keepidle, sizeof(keepidle));
setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL, &keepintvl, sizeof(keepintvl));
setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT, &keepcnt, sizeof(keepcnt));

// Set congestion control algorithm (per-socket)
char algo[] = "bbr";
setsockopt(fd, IPPROTO_TCP, TCP_CONGESTION, algo, sizeof(algo));

// Enable TCP Fast Open (client side)
// Data sent with SYN
sendto(fd, data, len, MSG_FASTOPEN, addr, addrlen);

// Enable TCP Fast Open (server side)
int qlen = 5;  // Queue length for pending TFO requests
setsockopt(listen_fd, IPPROTO_TCP, TCP_FASTOPEN, &qlen, sizeof(qlen));

// Cork: accumulate data before sending
int cork = 1;
setsockopt(fd, IPPROTO_TCP, TCP_CORK, &cork, sizeof(cork));
// Write multiple small pieces
write(fd, header, header_len);
write(fd, body, body_len);
// Uncork to send
cork = 0;
setsockopt(fd, IPPROTO_TCP, TCP_CORK, &cork, sizeof(cork));

// User timeout: abort connection if no ACK received
unsigned int timeout_ms = 30000;  // 30 seconds
setsockopt(fd, IPPROTO_TCP, TCP_USER_TIMEOUT, &timeout_ms, sizeof(timeout_ms));

// ============================================================
// Address Reuse
// ============================================================

// Allow binding to address in TIME_WAIT
int reuse = 1;
setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

// Allow multiple sockets to bind to same port (load balancing)
setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse));

// ============================================================
// Timestamping
// ============================================================

// Enable hardware/software timestamps
int flags = SOF_TIMESTAMPING_RX_HARDWARE |
            SOF_TIMESTAMPING_TX_HARDWARE |
            SOF_TIMESTAMPING_RAW_HARDWARE;
setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &flags, sizeof(flags));
// Timestamps received via recvmsg() ancillary data
```

### 21.3 Hardware Offloading

```
NIC Offload Features:

┌─────────────────────────────────────────────────────────────────────────┐
│  Feature                    │ Description                              │
├─────────────────────────────┼──────────────────────────────────────────┤
│  TSO (TCP Segmentation      │ NIC segments large buffers into MSS-     │
│       Offload)              │ sized packets. CPU sends 64KB, NIC       │
│                             │ creates ~44 packets.                      │
├─────────────────────────────┼──────────────────────────────────────────┤
│  GSO (Generic Segmentation  │ Software fallback for TSO. Kernel        │
│       Offload)              │ delays segmentation until last moment.   │
├─────────────────────────────┼──────────────────────────────────────────┤
│  GRO (Generic Receive       │ Coalesce multiple packets into one       │
│       Offload)              │ large buffer before passing to stack.    │
├─────────────────────────────┼──────────────────────────────────────────┤
│  LRO (Large Receive         │ Hardware version of GRO. NIC coalesces   │
│       Offload)              │ packets.                                  │
├─────────────────────────────┼──────────────────────────────────────────┤
│  Checksum Offload           │ NIC calculates/verifies TCP/UDP/IP       │
│                             │ checksums.                                │
├─────────────────────────────┼──────────────────────────────────────────┤
│  RSS (Receive Side          │ Distribute incoming packets across       │
│       Scaling)              │ multiple RX queues/CPUs based on         │
│                             │ flow hash.                                │
├─────────────────────────────┼──────────────────────────────────────────┤
│  RPS (Receive Packet        │ Software RSS. Kernel distributes         │
│       Steering)             │ packets to CPUs.                          │
├─────────────────────────────┼──────────────────────────────────────────┤
│  XPS (Transmit Packet       │ Map TX queues to CPUs for cache          │
│       Steering)             │ locality.                                 │
├─────────────────────────────┼──────────────────────────────────────────┤
│  TLS Offload (kTLS)         │ NIC handles TLS encryption/decryption.   │
│                             │ Kernel sends plaintext, wire sees        │
│                             │ ciphertext.                               │
└─────────────────────────────┴──────────────────────────────────────────┘
```

```bash
# Check current offload settings
ethtool -k eth0

# Enable/disable offloads
ethtool -K eth0 tso on
ethtool -K eth0 gro on
ethtool -K eth0 lro off  # Often disabled (breaks routing)
ethtool -K eth0 tx-checksum-ipv4 on
ethtool -K eth0 rx-checksum on

# Check ring buffer sizes
ethtool -g eth0

# Increase ring buffers (reduce packet drops under load)
ethtool -G eth0 rx 4096 tx 4096

# Check interrupt coalescing
ethtool -c eth0

# Tune interrupt coalescing (trade latency for throughput)
ethtool -C eth0 rx-usecs 50 tx-usecs 50

# Check RSS configuration
ethtool -x eth0

# Configure RSS indirection table
ethtool -X eth0 equal 4  # Distribute across 4 queues

# Check queue count
ethtool -l eth0

# Set queue count
ethtool -L eth0 combined 8
```

### 21.4 Interrupt Affinity and CPU Pinning

```bash
# View current IRQ affinity
cat /proc/interrupts | grep eth0
# Shows which CPUs handle each interrupt

# Set IRQ affinity (pin to specific CPU)
echo 2 > /proc/irq/123/smp_affinity
# Bitmask: 2 = CPU 1, 4 = CPU 2, 6 = CPUs 1+2

# Automatic IRQ balancing
# irqbalance daemon distributes IRQs across CPUs
systemctl status irqbalance

# For high-performance: disable irqbalance, manually pin
systemctl stop irqbalance

# Pin each NIC queue to dedicated CPU
# Queue 0 → CPU 0, Queue 1 → CPU 1, etc.
for i in $(seq 0 7); do
    irq=$(grep "eth0-TxRx-$i" /proc/interrupts | awk '{print $1}' | tr -d ':')
    echo $((1 << i)) > /proc/irq/$irq/smp_affinity
done

# RPS (Receive Packet Steering) - software RSS
# Distribute to CPUs 0-3
echo f > /sys/class/net/eth0/queues/rx-0/rps_cpus

# XPS (Transmit Packet Steering)
# TX queue 0 handled by CPU 0
echo 1 > /sys/class/net/eth0/queues/tx-0/xps_cpus
```

---

## 22. Security Considerations

### 22.1 SYN Flood Mitigation

```
SYN Flood Attack:

Attacker sends massive SYN packets with spoofed source IPs:

┌─────────────────────────────────────────────────────────────────────────┐
│  Attacker                                                                │
│                                                                          │
│  SYN (src=1.1.1.1) ──────────────────────────────────────────┐          │
│  SYN (src=2.2.2.2) ──────────────────────────────────────────┤          │
│  SYN (src=3.3.3.3) ──────────────────────────────────────────┤          │
│  SYN (src=4.4.4.4) ──────────────────────────────────────────┤          │
│  ... millions more ...                                        │          │
│                                                               ▼          │
│                                                    ┌─────────────────┐  │
│                                                    │  Target Server  │  │
│                                                    │                 │  │
│                                                    │  SYN Queue:     │  │
│                                                    │  [full][full]   │  │
│                                                    │  [full][full]   │  │
│                                                    │                 │  │
│                                                    │  Legitimate     │  │
│                                                    │  connections    │  │
│                                                    │  DROPPED!       │  │
│                                                    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Defense: SYN Cookies

Instead of storing state for half-open connections:

1. Server receives SYN
2. Server computes cookie:
   cookie = hash(src_ip, src_port, dst_ip, dst_port, secret, timestamp)
3. Server sends SYN-ACK with seq = cookie
4. Server stores NOTHING

5. Client sends ACK with ack = cookie + 1
6. Server recomputes cookie, verifies ACK
7. Only now: allocate connection state

┌─────────────────────────────────────────────────────────────────────────┐
│  With SYN Cookies:                                                       │
│                                                                          │
│  Attacker SYNs → Server sends SYN-ACKs (no state stored)                │
│                  SYN-ACKs go to spoofed IPs (no response)               │
│                  No state exhaustion!                                    │
│                                                                          │
│  Legitimate client → SYN → SYN-ACK → ACK (with valid cookie)            │
│                      Connection established normally                     │
└─────────────────────────────────────────────────────────────────────────┘

Limitations of SYN cookies:
  - Cannot encode all TCP options (MSS limited to 8 values)
  - No window scaling in initial handshake
  - No SACK negotiation
  - Slight CPU overhead for crypto

Enable:
  sysctl net.ipv4.tcp_syncookies = 1
```

### 22.2 Connection Hijacking

```
TCP Session Hijacking (historical):

Attacker needs to guess:
  1. Source IP (known if on same network)
  2. Source port (predictable if sequential)
  3. Sequence number (was predictable!)

Old vulnerability (pre-RFC 6528):
  - Initial Sequence Numbers (ISN) were predictable
  - Attacker could guess next ISN
  - Inject packets into existing connection

Modern defenses:

1. Randomized ISN (RFC 6528):
   ISN = hash(src_ip, src_port, dst_ip, dst_port, secret_key) + time_based_counter

   Unpredictable without knowing secret_key

2. Randomized ephemeral ports:
   Source port chosen randomly from range
   Not sequential

3. TCP timestamps:
   PAWS (Protection Against Wrapped Sequences)
   Rejects packets with old timestamps

4. Challenge ACK (RFC 5961):
   When receiving unexpected RST/SYN:
   - Don't immediately reset connection
   - Send Challenge ACK
   - Require valid response before action

Kernel implementation:
  net.ipv4.tcp_challenge_ack_limit = 1000
  # Limits challenge ACKs per second (prevents amplification)
```

### 22.3 TLS Security

```
TLS Vulnerabilities and Mitigations:

┌─────────────────────────────────────────────────────────────────────────┐
│  Vulnerability          │ Mitigation                                    │
├─────────────────────────┼───────────────────────────────────────────────┤
│  BEAST (CBC IV)         │ Use TLS 1.1+ or AES-GCM                       │
├─────────────────────────┼───────────────────────────────────────────────┤
│  CRIME (compression)    │ Disable TLS compression                       │
├─────────────────────────┼───────────────────────────────────────────────┤
│  BREACH (HTTP compress) │ Disable HTTP compression for sensitive data  │
├─────────────────────────┼───────────────────────────────────────────────┤
│  POODLE (SSLv3)         │ Disable SSLv3                                 │
├─────────────────────────┼───────────────────────────────────────────────┤
│  Heartbleed (OpenSSL)   │ Patch OpenSSL, rotate keys                    │
├─────────────────────────┼───────────────────────────────────────────────┤
│  DROWN (SSLv2)          │ Disable SSLv2 on all servers                  │
├─────────────────────────┼───────────────────────────────────────────────┤
│  ROBOT (RSA PKCS#1)     │ Disable RSA key exchange                      │
├─────────────────────────┼───────────────────────────────────────────────┤
│  Downgrade attacks      │ TLS_FALLBACK_SCSV, require TLS 1.2+          │
└─────────────────────────┴───────────────────────────────────────────────┘

Recommended TLS Configuration (2024+):

Protocol versions:
  - TLS 1.3 preferred
  - TLS 1.2 minimum
  - Disable TLS 1.1, 1.0, SSLv3, SSLv2

Cipher suites (TLS 1.3):
  - TLS_AES_256_GCM_SHA384
  - TLS_CHACHA20_POLY1305_SHA256
  - TLS_AES_128_GCM_SHA256

Cipher suites (TLS 1.2):
  - ECDHE-ECDSA-AES256-GCM-SHA384
  - ECDHE-RSA-AES256-GCM-SHA384
  - ECDHE-ECDSA-CHACHA20-POLY1305
  - ECDHE-RSA-CHACHA20-POLY1305

Key exchange:
  - ECDHE with P-256, P-384, or X25519
  - No RSA key exchange (forward secrecy!)
  - No DHE with small groups

Certificate:
  - RSA 2048+ or ECDSA P-256+
  - SHA-256 signature
  - Valid chain to trusted root
  - OCSP stapling enabled
```

### 22.4 Socket Security Options

```c
// ============================================================
// Credential Passing (Unix sockets)
// ============================================================

// Enable credential passing
int passcred = 1;
setsockopt(fd, SOL_SOCKET, SO_PASSCRED, &passcred, sizeof(passcred));

// Receive credentials via ancillary data
struct msghdr msg = {0};
struct cmsghdr *cmsg;
char control[CMSG_SPACE(sizeof(struct ucred))];
msg.msg_control = control;
msg.msg_controllen = sizeof(control);

recvmsg(fd, &msg, 0);

for (cmsg = CMSG_FIRSTHDR(&msg); cmsg; cmsg = CMSG_NXTHDR(&msg, cmsg)) {
    if (cmsg->cmsg_level == SOL_SOCKET && cmsg->cmsg_type == SCM_CREDENTIALS) {
        struct ucred *cred = (struct ucred *)CMSG_DATA(cmsg);
        printf("PID: %d, UID: %d, GID: %d\n", cred->pid, cred->uid, cred->gid);
    }
}

// ============================================================
// Binding to Device
// ============================================================

// Bind socket to specific interface (requires CAP_NET_RAW)
char ifname[] = "eth0";
setsockopt(fd, SOL_SOCKET, SO_BINDTODEVICE, ifname, strlen(ifname));
// Packets only sent/received on this interface

// ============================================================
// Mark for Policy Routing
// ============================================================

// Set socket mark (for iptables/routing decisions)
int mark = 100;
setsockopt(fd, SOL_SOCKET, SO_MARK, &mark, sizeof(mark));
// Use with: ip rule add fwmark 100 table custom

// ============================================================
// Transparent Proxy
// ============================================================

// Allow binding to non-local address (for transparent proxy)
int transparent = 1;
setsockopt(fd, SOL_IP, IP_TRANSPARENT, &transparent, sizeof(transparent));
// Requires CAP_NET_ADMIN

// ============================================================
// Receive Original Destination
// ============================================================

// For intercepted connections, get original destination
int origdst = 1;
setsockopt(fd, SOL_IP, IP_RECVORIGDSTADDR, &origdst, sizeof(origdst));
// Original destination in ancillary data
```

### 22.5 Firewall Integration

```
Netfilter Hooks and Socket Interaction:

                    Incoming Packet
                          │
                          ▼
                  ┌───────────────┐
                  │  PREROUTING   │ ← DNAT, connection tracking
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │   Routing     │
                  └───────┬───────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
     ┌───────────────┐         ┌───────────────┐
     │    INPUT      │         │   FORWARD     │
     │ (local dest)  │         │ (routing)     │
     └───────┬───────┘         └───────┬───────┘
             │                         │
             ▼                         ▼
     ┌───────────────┐         ┌───────────────┐
     │ Local Process │         │  POSTROUTING  │
     │   (socket)    │         │    (SNAT)     │
     └───────┬───────┘         └───────────────┘
             │
             ▼
     ┌───────────────┐
     │    OUTPUT     │ ← Locally generated packets
     └───────┬───────┘
             │
             ▼
     ┌───────────────┐
     │  POSTROUTING  │ ← SNAT, masquerade
     └───────────────┘


iptables/nftables Rules for Socket Security:

# Limit new connections per source IP
iptables -A INPUT -p tcp --syn -m connlimit --connlimit-above 100 -j DROP

# Rate limit SYN packets
iptables -A INPUT -p tcp --syn -m limit --limit 100/s --limit-burst 200 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Protect against port scanning
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP
iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
```

---

## 23. Conclusion: The Complete Picture

```
From Application to Wire - Complete Data Path:

┌─────────────────────────────────────────────────────────────────────────┐
│  Chrome Tab (Renderer Process)                                           │
│                                                                          │
│  fetch('https://example.com/api/data')                                  │
│         │                                                                │
│         ▼                                                                │
│  Blink ResourceFetcher → URLLoader (Mojo IPC)                           │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Network Service Process                                                 │
│                                                                          │
│  URLLoaderFactory → HttpNetworkTransaction                              │
│         │                                                                │
│         ├── Check HTTP cache (miss)                                      │
│         ├── DNS resolution (cached or DoH query)                        │
│         ├── Check HTTP/2 session pool → Found existing session!         │
│         │                                                                │
│         ▼                                                                │
│  HTTP/2 Stream created on existing TCP connection                       │
│  HEADERS frame: GET /api/data                                           │
│         │                                                                │
│         ▼                                                                │
│  TLS encryption (kTLS or user-space)                                    │
│  Plaintext → Ciphertext                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Kernel TCP Stack                                                        │
│                                                                          │
│  Socket send buffer ← Application data                                  │
│         │                                                                │
│         ▼                                                                │
│  TCP segmentation (or TSO offload)                                      │
│  Add TCP header (seq, ack, window, checksum)                            │
│         │                                                                │
│         ▼                                                                │
│  IP layer: Add IP header (src, dst, TTL, checksum)                      │
│         │                                                                │
│         ▼                                                                │
│  Routing decision → Output interface                                    │
│         │                                                                │
│         ▼                                                                │
│  Netfilter OUTPUT chain (firewall rules)                                │
│         │                                                                │
│         ▼                                                                │
│  Neighbor subsystem: ARP lookup → MAC address                           │
│         │                                                                │
│         ▼                                                                │
│  Add Ethernet header                                                     │
│         │                                                                │
│         ▼                                                                │
│  Queue to NIC driver (qdisc)                                            │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  NIC Driver                                                              │
│                                                                          │
│  sk_buff → DMA descriptor                                               │
│  NIC reads packet via DMA                                               │
│  Hardware offloads: checksum, TSO, TLS                                  │
│         │                                                                │
│         ▼                                                                │
│  Transmit to wire                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
              [Physical Network]
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Remote Server                                                           │
│                                                                          │
│  NIC receives → DMA to memory → Driver → NAPI polling                   │
│         │                                                                │
│         ▼                                                                │
│  GRO coalescing → Netfilter INPUT → IP layer → TCP layer               │
│         │                                                                │
│         ▼                                                                │
│  Socket receive buffer → Application read()                             │
└─────────────────────────────────────────────────────────────────────────┘


Key Insights for the Stevens/Bach Reader:

1. SOCKET ABSTRACTION
   The VFS-based socket abstraction (struct socket → struct sock) provides
   the same file descriptor interface you know from Bach, but with protocol-
   specific operations via function pointer tables.

2. 5-TUPLE DEMULTIPLEXING
   Port numbers alone don't identify connections. The kernel's hash tables
   use the full 5-tuple, enabling massive connection scaling on a single port.

3. BUFFER MANAGEMENT
   sk_buff is the kernel's packet representation, with careful attention to
   avoiding copies (cloning, page references, scatter-gather).

4. CHROME'S EFFICIENCY
   Multiple tabs share connections via HTTP/2 multiplexing. The 6-connection
   limit per origin is rarely hit because streams multiplex on single TCP
   connections.

5. MODERN OPTIMIZATIONS
   Zero-copy (sendfile, MSG_ZEROCOPY, io_uring), hardware offload (TSO, GRO,
   kTLS), and kernel bypass (DPDK, XDP) push performance beyond what was
   possible in the Stevens era.

6. SECURITY LAYERS
   SYN cookies, randomized ISN, TLS 1.3, and connection tracking provide
   defense in depth against the attacks that plagued early TCP/IP.

The fundamentals from Stevens and Bach remain true: sockets are file
descriptors, the kernel manages buffers and state machines, and the
protocol stack is layered. But the implementation has evolved dramatically
to handle millions of connections, gigabit speeds, and sophisticated attacks.
```

