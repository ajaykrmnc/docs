# Chapter 9: Zero-Copy and Performance Optimization

Every byte copied between buffers consumes CPU cycles, pollutes caches, and wastes
memory bandwidth. At modern NIC speeds (10--100 Gbps), the kernel's networking
stack cannot afford gratuitous copies. This chapter dissects every zero-copy
mechanism available in Linux, from `MSG_ZEROCOPY` through XDP and AF_XDP, and
then surveys the broader set of performance primitives -- page pools, sk_buff
recycling, busy polling, and GRO/GSO -- that collectively allow the kernel to
saturate 100 Gbps links on commodity hardware.

---

## 1. The Cost of Copying

### 1.1 CPU Cycles per Byte

A naive `memcpy` on a modern x86-64 processor costs roughly 0.2--0.5 CPU cycles
per byte when the source and destination both reside in L1 cache.  When the
working set exceeds L1 (32--48 KiB per core), cost rises sharply:

```
┌───────────────────┬───────────────────┬────────────────────┐
│  Buffer Location  │  Cycles per Byte  │  Effective BW/core │
├───────────────────┼───────────────────┼────────────────────┤
│  L1 cache (hot)   │     ~0.25         │   ~50 GB/s         │
│  L2 cache         │     ~0.5          │   ~25 GB/s         │
│  L3 cache         │     ~1.5          │    ~8 GB/s         │
│  Main memory      │     ~4.0          │    ~3 GB/s         │
│  Cross-NUMA       │     ~8.0          │   ~1.5 GB/s        │
└───────────────────┴───────────────────┴────────────────────┘
```

At 100 Gbps line rate (12.5 GB/s), a single core doing `memcpy` from main memory
(~3 GB/s effective throughput) cannot even copy the data once, let alone process
headers, compute checksums, and manage state machines.

### 1.2 Cache Pollution

Copying a 1500-byte Ethernet frame through a 4 KiB staging buffer evicts two
cache lines (128 bytes) for the source *and* two for the destination.  A burst of
64 packets therefore touches 16 KiB of cache -- half of a typical L1d.

For jumbo frames (9000 bytes), a single copy pollutes ~18 cache lines, and a
64-packet burst flushes over 72 KiB, exceeding the entire L1 data cache on most
microarchitectures.

### 1.3 Memory Bandwidth Bottleneck at High Line Rates

The traditional kernel TX path for TCP involves at least two copies:

```
┌──────────────────────────────────────────────────────────────────┐
│  Application buffer  ──copy 1──►  Kernel socket buffer (sk_buff)│
│  Kernel socket buffer ──copy 2──► NIC TX ring (DMA)             │
└──────────────────────────────────────────────────────────────────┘
```

At 100 Gbps, these two copies alone consume 25 GB/s of memory bandwidth -- a
significant fraction of a modern dual-channel DDR5 system's total bandwidth
(~80 GB/s).  With the kernel also reading headers, computing checksums, and
walking data structures, the system saturates memory bandwidth long before the
CPU runs out of instruction throughput.

### 1.4 Measuring Copy Overhead with perf

```bash
# Record all memcpy activity in the network stack for 10 seconds
perf record -g -e cycles -a -- sleep 10

# Look for memcpy/copy_from_user in the flame graph
perf report --stdio | grep -E 'memcpy|copy_from_user|skb_copy'

# Count cache misses attributable to network copies
perf stat -e LLC-load-misses,LLC-store-misses \
         -p $(pgrep -x iperf3) -- sleep 5

# Trace specific copy functions with call stacks
perf probe --add 'skb_copy_bits'
perf record -e probe:skb_copy_bits -g -a -- sleep 5
```

The output typically reveals that `skb_copy_bits`, `copy_from_iter`,
`skb_copy_datagram_iter`, and `__memcpy` dominate the cycles spent in the
networking stack under high-throughput workloads.

---

## 2. MSG_ZEROCOPY (sendmsg)

### 2.1 Overview

`MSG_ZEROCOPY` eliminates the copy from user space to kernel socket buffer on the
transmit path.  Instead of copying application data into a freshly allocated
`sk_buff`, the kernel pins the user-space pages and instructs the NIC to DMA
directly from them.

### 2.2 Enabling SO_ZEROCOPY

```c
int one = 1;
/* Enable zero-copy on the socket */
setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));
```

Once enabled, the application passes `MSG_ZEROCOPY` in the `sendmsg()` flags:

```c
struct msghdr msg = { 0 };
struct iovec iov = {
    .iov_base = buf,       /* user-space buffer, page-aligned preferred */
    .iov_len  = len,
};
msg.msg_iov    = &iov;
msg.msg_iovlen = 1;

ssize_t sent = sendmsg(fd, &msg, MSG_ZEROCOPY);
if (sent < 0)
    perror("sendmsg");
```

### 2.3 How It Works Internally

The kernel path for `MSG_ZEROCOPY` proceeds as follows:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Traditional Copy TX Path                            │
│                                                                        │
│  User buf ──memcpy──► skb->data ──DMA──► NIC                          │
│             (CPU)       (kernel)                                       │
│                                                                        │
│  User buffer is FREE immediately after sendmsg() returns.              │
├─────────────────────────────────────────────────────────────────────────┤
│                    Zero-Copy TX Path                                   │
│                                                                        │
│  User buf ──pin pages──► skb->frags[] ──DMA──► NIC                    │
│              (no copy)    (page refs)                                   │
│                                                                        │
│  User buffer is NOT FREE until completion notification arrives.        │
└─────────────────────────────────────────────────────────────────────────┘
```

Step by step:

1. The kernel calls `get_user_pages_fast()` to pin the user-space pages.
2. Page references are stored in `skb_shared_info->frags[]` as `skb_frag_t`
   entries, each holding a `struct page *` and an offset/length.
3. The `sk_buff` header area (Ethernet, IP, TCP headers) is still allocated
   normally in `skb->data` -- only the *payload* is zero-copy.
4. The NIC's DMA engine reads directly from the pinned user pages.
5. After the NIC signals TX completion (via interrupt or polling), the kernel
   releases the page pins and posts a completion notification.

### 2.4 Completion Notification via MSG_ERRQUEUE

The application must poll the socket's error queue to learn when its buffers are
safe to reuse:

```c
struct sock_extended_err *serr;
struct msghdr            msg  = { 0 };
struct cmsghdr          *cm;
char                     cbuf[CMSG_SPACE(sizeof(struct sock_extended_err) +
                                         sizeof(uint32_t))];
uint32_t                 lo, hi;

msg.msg_control    = cbuf;
msg.msg_controllen = sizeof(cbuf);

/* Non-blocking poll for completion */
int ret = recvmsg(fd, &msg, MSG_ERRQUEUE | MSG_DONTWAIT);
if (ret < 0) {
    if (errno == EAGAIN)
        return;  /* no completions yet */
    perror("recvmsg errqueue");
    return;
}

for (cm = CMSG_FIRSTHDR(&msg); cm; cm = CMSG_NXTHDR(&msg, cm)) {
    if (cm->cmsg_level != SOL_IP || cm->cmsg_type != IP_RECVERR)
        continue;

    serr = (struct sock_extended_err *)CMSG_DATA(cm);
    if (serr->ee_origin != SO_EE_ORIGIN_ZEROCOPY)
        continue;

    /* Range of completed send IDs */
    lo = serr->ee_info;     /* first completed ID   */
    hi = serr->ee_data;     /* last completed ID    */

    /* Buffers [lo .. hi] are now safe to reuse or free */
    for (uint32_t id = lo; id <= hi; id++)
        mark_buffer_free(id);
}
```

Each `sendmsg()` call with `MSG_ZEROCOPY` is assigned a monotonically increasing
32-bit notification ID.  The completion notification reports ranges `[lo, hi]` of
IDs whose corresponding user buffers are now safe to reuse.

### 2.5 Key Kernel Functions

```c
/*
 * skb_zcopy_init() — initialize zero-copy state in skb_shared_info.
 * Called during sk_buff setup when MSG_ZEROCOPY is in effect.
 */
void skb_zcopy_init(struct sk_buff *skb, struct ubuf_info *uarg);

/*
 * skb_zcopy_set() — attach a ubuf_info (user buffer reference) to the skb.
 * The ubuf_info tracks the user-space pages and completion callback.
 */
void skb_zcopy_set(struct sk_buff *skb, struct ubuf_info *uarg, bool *have_ref);

/*
 * skb_zcopy_clear() — detach zero-copy state.
 * Called when the NIC has finished DMA and we can release the user pages.
 */
void skb_zcopy_clear(struct sk_buff *skb, bool zerocopy_success);
```

The `ubuf_info` structure is the core tracking object:

```c
struct ubuf_info {
    void (*callback)(struct sk_buff *, struct ubuf_info *, bool success);
    refcount_t refcnt;
    u8  flags;
    /* ... per-protocol fields ... */
};
```

When the last reference to a `ubuf_info` is dropped (all fragments DMA'd and
acknowledged), the callback fires, which posts the completion notification to the
socket's error queue.

### 2.6 When NOT to Use MSG_ZEROCOPY

Zero-copy is not universally beneficial.  The page-pinning and completion-
notification machinery introduces fixed overhead per `sendmsg()` call:

```
┌─────────────────────────────────────┬────────────┬─────────────┐
│  Scenario                           │  Copy TX   │  ZeroCopy   │
├─────────────────────────────────────┼────────────┼─────────────┤
│  Payload < ~4 KiB                   │  Faster    │  Slower     │
│  Payload 16 KiB - 64 KiB           │  Similar   │  Similar    │
│  Payload > 64 KiB                   │  Slower    │  Faster     │
│  Many small sends (< 1 KiB each)   │  Faster    │  Much Slower│
│  Bulk streaming (video, backup)     │  Slower    │  Much Faster│
└─────────────────────────────────────┴────────────┴─────────────┘
```

Avoid `MSG_ZEROCOPY` when:
- Writes are smaller than approximately 4 KiB (page-pinning overhead dominates).
- The application sends at very high frequency with small payloads (the
  completion-notification polling becomes a bottleneck).
- The NIC driver does not support scatter-gather DMA (the kernel falls back to
  copying silently, adding overhead with no benefit).

---

## 3. sendfile() and splice()

### 3.1 sendfile() -- File to Socket Without User-Space Copy

`sendfile()` transfers data directly from a file descriptor to a socket without
routing it through user space:

```c
#include <sys/sendfile.h>

/*
 * Transfer 'count' bytes from file fd 'in_fd' starting at *offset
 * directly into socket fd 'out_fd'.
 */
ssize_t sent = sendfile(out_fd,   /* destination socket     */
                        in_fd,    /* source file            */
                        &offset,  /* file offset (updated)  */
                        count);   /* bytes to transfer      */
```

Internally, `sendfile()` calls `do_sendfile()`, which uses `splice_direct_to_actor()`
to move page-cache pages into the socket's `sk_buff` fragments without copying.

### 3.2 Data Flow for sendfile()

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         sendfile() Data Flow                            │
│                                                                          │
│  ┌──────────┐    page ref    ┌──────────────┐    DMA     ┌─────────┐   │
│  │  Page     │──────────────►│  sk_buff      │──────────►│   NIC   │   │
│  │  Cache    │               │  frags[]      │           │   TX    │   │
│  │  (file)   │               │  (page refs)  │           │   Ring  │   │
│  └──────────┘               └──────────────┘           └─────────┘   │
│       ▲                                                                  │
│       │ read from disk                                                   │
│  ┌────┴─────┐                                                            │
│  │  Block   │    No user-space buffer is ever allocated or touched.      │
│  │  Device  │    The page cache pages are referenced directly by the     │
│  └──────────┘    sk_buff's fragment list.                                │
└──────────────────────────────────────────────────────────────────────────┘
```

The key insight: the same physical page that the page cache uses to hold file
data is referenced by the `sk_buff`'s `skb_shared_info->frags[]`.  No `memcpy`
occurs at any point.  The NIC's DMA engine reads directly from the page-cache
page.

### 3.3 splice() and vmsplice()

`splice()` is the generalized pipe-based zero-copy mechanism:

```c
#include <fcntl.h>

/*
 * splice() moves data between two file descriptors, where one
 * must be a pipe.  No data crosses the user/kernel boundary.
 */
ssize_t splice(int fd_in,  loff_t *off_in,
               int fd_out, loff_t *off_out,
               size_t len, unsigned int flags);

/*
 * vmsplice() moves data from user-space buffers into a pipe
 * without copying (if SPLICE_F_GIFT is set).
 */
ssize_t vmsplice(int fd, const struct iovec *iov,
                 unsigned long nr_segs, unsigned int flags);
```

A typical zero-copy file-to-socket path using `splice()`:

```c
int pipefd[2];
pipe(pipefd);

/* Move pages from file into pipe (zero-copy from page cache) */
ssize_t n = splice(file_fd, &offset, pipefd[1], NULL, len, SPLICE_F_MOVE);

/* Move pages from pipe into socket (zero-copy to sk_buff) */
ssize_t s = splice(pipefd[0], NULL, sock_fd, NULL, n, SPLICE_F_MOVE);
```

### 3.4 skb_splice_bits() and tcp_splice_read()

```c
/*
 * skb_splice_bits() — splice sk_buff data into a pipe.
 * Used by tcp_splice_read() to implement splice() from a TCP socket.
 * Moves sk_buff linear data and fragment pages into pipe buffers
 * without copying.
 */
int skb_splice_bits(struct sk_buff *skb, struct sock *sk,
                    unsigned int offset, struct pipe_inode_info *pipe,
                    unsigned int len, unsigned int flags);

/*
 * tcp_splice_read() — the splice_read file_operation for TCP sockets.
 * Called when the user does splice(tcp_socket, ..., pipe, ...).
 * Walks the socket's receive queue, calling skb_splice_bits() on
 * each sk_buff.
 */
ssize_t tcp_splice_read(struct socket *sock, loff_t *ppos,
                        struct pipe_inode_info *pipe,
                        size_t len, unsigned int flags);
```

The pages move through the pipe as `struct pipe_buffer` entries, each holding a
reference to the underlying page.  When the pipe drains into a socket (the
second `splice()` call), those page references become `skb_frag_t` entries in
the outgoing `sk_buff`.

---

## 4. XDP (eXpress Data Path)

### 4.1 What XDP Is

XDP is a programmable, high-performance packet-processing framework that runs
eBPF programs at the earliest possible point in the receive path -- inside the
NIC driver's NAPI poll function, *before* any `sk_buff` is allocated.

Because `sk_buff` allocation and initialization is one of the most expensive
per-packet operations in the Linux networking stack, bypassing it for packets
that will be dropped, redirected, or reflected yields dramatic throughput
improvements.

### 4.2 XDP Actions

An XDP program returns one of five action codes:

```
┌───────────────┬──────────────────────────────────────────────────────┐
│  Action       │  Behavior                                            │
├───────────────┼──────────────────────────────────────────────────────┤
│  XDP_PASS     │  Allocate sk_buff, pass packet to normal network     │
│               │  stack.  This is the "do nothing special" action.    │
├───────────────┼──────────────────────────────────────────────────────┤
│  XDP_DROP     │  Drop the packet immediately.  No sk_buff is ever   │
│               │  allocated.  The page/buffer is recycled instantly.  │
├───────────────┼──────────────────────────────────────────────────────┤
│  XDP_TX       │  Transmit the packet back out the same NIC it       │
│               │  arrived on.  Useful for load balancers, reflectors.│
├───────────────┼──────────────────────────────────────────────────────┤
│  XDP_REDIRECT │  Redirect the packet to another NIC, CPU, or AF_XDP │
│               │  socket.  Uses bpf_redirect() / bpf_redirect_map().│
├───────────────┼──────────────────────────────────────────────────────┤
│  XDP_ABORTED  │  Error path.  Like XDP_DROP but also triggers the   │
│               │  xdp:xdp_exception tracepoint for debugging.        │
└───────────────┴──────────────────────────────────────────────────────┘
```

### 4.3 xdp_buff vs sk_buff

XDP programs do not operate on `sk_buff`.  They receive an `xdp_buff`, which is
a lightweight descriptor pointing directly at the DMA-mapped receive buffer:

```c
struct xdp_buff {
    void *data;           /* start of packet data               */
    void *data_end;       /* end of packet data                 */
    void *data_meta;      /* metadata area before data          */
    void *data_hard_start;/* start of the headroom              */
    struct xdp_rxq_info *rxq; /* per-RX-queue info (ifindex etc.) */
    struct xdp_txq_info *txq; /* per-TX-queue info (for XDP_TX)   */
    u32 frame_sz;         /* total frame size including headroom */
    u32 flags;
};
```

Comparison with `sk_buff`:

```
┌──────────────────────┬───────────────────┬────────────────────────┐
│  Property            │  xdp_buff         │  sk_buff               │
├──────────────────────┼───────────────────┼────────────────────────┤
│  Size (struct)       │  ~48 bytes        │  ~232 bytes            │
│  Allocation          │  On stack / reused│  SLUB slab allocator   │
│  Header parsing      │  None by kernel   │  mac/net/transport set │
│  Protocol awareness  │  None             │  Full protocol state   │
│  Fragment support    │  Limited (multi-  │  Full (frags[], frag_  │
│                      │  buffer XDP)      │  list)                 │
│  Shared info         │  No               │  skb_shared_info       │
│  Queueing            │  Not possible     │  sk_buff_head queues   │
└──────────────────────┴───────────────────┴────────────────────────┘
```

### 4.4 Conversion: xdp_buff to sk_buff via XDP_PASS

When an XDP program returns `XDP_PASS`, the driver must convert the `xdp_buff`
into an `sk_buff` for the normal network stack:

```c
/*
 * Typical driver code after XDP_PASS:
 * 1. Allocate sk_buff with build_skb() or napi_build_skb()
 * 2. Set up data pointers from xdp_buff
 * 3. Pass to napi_gro_receive() or netif_receive_skb()
 */
struct sk_buff *skb = napi_build_skb(xdp->data_hard_start,
                                      xdp->frame_sz);
if (!skb) {
    /* Drop: could not allocate sk_buff */
    page_pool_put_page(rx_ring->page_pool, page, sync_len, true);
    return;
}

/* Adjust data pointer to skip headroom */
skb_reserve(skb, xdp->data - xdp->data_hard_start);

/* Set the packet length */
skb_put(skb, xdp->data_end - xdp->data);

/* Set protocol, checksum, hash, etc. */
skb->protocol = eth_type_trans(skb, netdev);
skb_record_rx_queue(skb, rx_ring->queue_index);

napi_gro_receive(&rx_ring->napi, skb);
```

### 4.5 XDP Program Attachment Modes

```
┌──────────────┬─────────────────────────────────────────────────────────┐
│  Mode        │  Description                                           │
├──────────────┼─────────────────────────────────────────────────────────┤
│  Native      │  XDP program runs inside the driver's NAPI poll.       │
│  (driver)    │  Requires driver support.  Best performance.           │
├──────────────┼─────────────────────────────────────────────────────────┤
│  Generic     │  XDP program runs in the generic receive path after    │
│  (SKB mode)  │  sk_buff allocation.  No driver support needed.        │
│              │  Lower performance (sk_buff already allocated).        │
├──────────────┼─────────────────────────────────────────────────────────┤
│  Offloaded   │  XDP program is compiled to run on the NIC hardware   │
│  (HW)        │  itself (e.g., Netronome SmartNICs).  Highest         │
│              │  performance but limited BPF instruction support.      │
└──────────────┴─────────────────────────────────────────────────────────┘
```

Attach an XDP program:

```bash
# Native mode (default if driver supports it)
ip link set dev eth0 xdpgeneric off
ip link set dev eth0 xdp obj xdp_prog.o sec xdp

# Generic/SKB mode (works on any NIC)
ip link set dev eth0 xdpgeneric obj xdp_prog.o sec xdp

# Offloaded mode (SmartNIC)
ip link set dev eth0 xdpoffload obj xdp_prog.o sec xdp
```

### 4.6 Performance

Native XDP achieves packet processing rates that are impossible with the
traditional `sk_buff`-based stack:

```
┌───────────────────────────┬───────────────────┬─────────────────────┐
│  Operation                │  sk_buff path     │  XDP native         │
├───────────────────────────┼───────────────────┼─────────────────────┤
│  Packet drop (per core)   │  ~5 Mpps          │  ~24 Mpps           │
│  Packet TX reflect        │  ~2 Mpps          │  ~14 Mpps           │
│  Packet redirect          │  ~2 Mpps          │  ~12 Mpps           │
│  L3 forwarding            │  ~3 Mpps          │  ~10 Mpps           │
└───────────────────────────┴───────────────────┴─────────────────────┘
```

(Approximate figures for a single core on a modern Xeon, 64-byte packets, with
a high-end 25/100 Gbps NIC supporting native XDP.)

### 4.7 XDP Decision Point in the Receive Path

```
                        ┌─────────┐
                        │   NIC   │
                        │   RX    │
                        └────┬────┘
                             │ DMA to ring buffer
                             ▼
                    ┌────────────────┐
                    │  Ring Buffer   │
                    │  (DMA-mapped   │
                    │   page/frag)   │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  XDP Program   │◄── eBPF bytecode, JIT-compiled
                    │  (xdp_buff)    │
                    └───┬──┬──┬──┬───┘
                        │  │  │  │
            ┌───────────┘  │  │  └──────────────┐
            │              │  │                  │
            ▼              ▼  ▼                  ▼
     ┌───────────┐  ┌─────┐  ┌──────────┐  ┌──────────┐
     │ XDP_DROP  │  │XDP  │  │  XDP     │  │ XDP_PASS │
     │           │  │_TX  │  │_REDIRECT │  │          │
     │ Recycle   │  │     │  │          │  │ Allocate │
     │ buffer,   │  │Send │  │ Forward  │  │ sk_buff, │
     │ no sk_buff│  │back │  │ to other │  │ enter    │
     │ allocated │  │out  │  │ NIC/CPU/ │  │ normal   │
     │           │  │same │  │ AF_XDP   │  │ stack    │
     └───────────┘  │NIC  │  └──────────┘  └──────────┘
                    └─────┘
```

---

## 5. AF_XDP

### 5.1 Overview

AF_XDP provides a mechanism for user-space applications to send and receive raw
packets with near-zero overhead, bypassing the entire kernel networking stack.
It builds on XDP: an XDP program running in the driver redirects selected
packets to an AF_XDP socket using `bpf_redirect_map()` with an `XSKMAP`.

### 5.2 UMEM -- Shared Memory Region

UMEM (User MEMory) is a contiguous, `mmap`'d region of memory shared between
the kernel and user space.  It is divided into fixed-size *frames* (typically
2 KiB or 4 KiB).  Both the kernel (NIC DMA) and user space read and write
directly to these frames -- no copies occur.

```c
struct xsk_umem_config cfg = {
    .fill_size      = XSK_RING_PROD__DEFAULT_NUM_DESCS,
    .comp_size      = XSK_RING_CONS__DEFAULT_NUM_DESCS,
    .frame_size     = XSK_UMEM__DEFAULT_FRAME_SIZE,  /* 4096 */
    .frame_headroom = XSK_UMEM__DEFAULT_FRAME_HEADROOM,
    .flags          = 0,
};

void *umem_area;
posix_memalign(&umem_area, getpagesize(),
               NUM_FRAMES * cfg.frame_size);

struct xsk_umem *umem;
xsk_umem__create(&umem, umem_area,
                 NUM_FRAMES * cfg.frame_size,
                 &fill_ring, &comp_ring, &cfg);
```

### 5.3 The Four Ring Queues

AF_XDP uses four lock-free, single-producer/single-consumer ring queues:

```
              Userspace                          Kernel
          ┌──────────────────┐              ┌──────────────────┐
          │                  │              │                  │
          │   Fill Ring      │─────────────►│                  │
          │   (producer:     │  "Here are   │   XDP Program    │
          │    userspace)    │   empty      │        +         │
          │                  │   frames"    │   NIC Driver     │
          ├──────────────────┤              │                  │
          │                  │              │                  │
          │   RX Ring        │◄─────────────│   Writes received│
          │   (consumer:     │  "Received   │   packet addrs   │
          │    userspace)    │   packets"   │   into RX ring   │
          │                  │              │                  │
          ├──────────────────┤              │                  │
          │                  │              │                  │
          │   TX Ring        │─────────────►│   Reads packet   │
          │   (producer:     │  "Send these │   addrs from TX  │
          │    userspace)    │   packets"   │   ring, DMAs out │
          │                  │              │                  │
          ├──────────────────┤              │                  │
          │                  │              │                  │
          │   Completion     │◄─────────────│   Returns addrs  │
          │   Ring           │  "TX done,   │   of completed   │
          │   (consumer:     │   reuse      │   TX frames      │
          │    userspace)    │   frames"    │                  │
          └──────────────────┘              └──────────────────┘
                  │    │
                  │    │  all frames live in
                  ▼    ▼
          ┌──────────────────┐
          │      UMEM        │
          │  (shared mmap'd  │
          │   memory region) │
          │                  │
          │  ┌─────┬─────┐  │
          │  │frame│frame│  │
          │  │  0  │  1  │  │
          │  ├─────┼─────┤  │
          │  │frame│frame│  │
          │  │  2  │  3  │  │
          │  ├─────┼─────┤  │
          │  │ ... │ ... │  │
          │  └─────┴─────┘  │
          └──────────────────┘
```

### 5.4 RX Path Walkthrough

```c
/*
 * 1. User fills the Fill Ring with addresses of empty UMEM frames.
 *    These frames are where the kernel will DMA incoming packets.
 */
uint32_t idx;
int n = xsk_ring_prod__reserve(&fill_ring, BATCH_SIZE, &idx);
for (int i = 0; i < n; i++) {
    *xsk_ring_prod__fill_addr(&fill_ring, idx + i) =
        get_free_frame() * FRAME_SIZE;   /* UMEM offset */
}
xsk_ring_prod__submit(&fill_ring, n);

/*
 * 2. Kernel/NIC DMAs packets into those frames.
 *    Kernel writes descriptors into the RX Ring.
 */

/*
 * 3. User polls and consumes the RX Ring.
 */
n = xsk_ring_cons__peek(&rx_ring, BATCH_SIZE, &idx);
for (int i = 0; i < n; i++) {
    const struct xdp_desc *desc = xsk_ring_cons__rx_desc(&rx_ring, idx + i);
    uint64_t addr = desc->addr;
    uint32_t len  = desc->len;

    /* Access packet data directly in UMEM — zero copy! */
    uint8_t *pkt = xsk_umem__get_data(umem_area, addr);
    process_packet(pkt, len);

    /* Return frame to free list for reuse */
    put_free_frame(addr / FRAME_SIZE);
}
xsk_ring_cons__release(&rx_ring, n);
```

### 5.5 Zero-Copy Mode vs Copy Mode

```
┌──────────────┬─────────────────────────────────────────────────────────┐
│  Mode        │  Description                                           │
├──────────────┼─────────────────────────────────────────────────────────┤
│  Zero-Copy   │  NIC DMA reads/writes directly to/from UMEM frames.   │
│              │  Requires driver support (e.g., i40e, ice, mlx5).     │
│              │  Best performance: ~20+ Mpps per core.                │
├──────────────┼─────────────────────────────────────────────────────────┤
│  Copy Mode   │  Kernel copies packet data between driver buffers and │
│              │  UMEM frames.  Works with any NIC.  Performance is    │
│              │  limited by the copy overhead (~5 Mpps per core).     │
└──────────────┴─────────────────────────────────────────────────────────┘
```

Specify copy mode at socket creation:

```c
struct xsk_socket_config cfg = {
    .rx_size      = XSK_RING_CONS__DEFAULT_NUM_DESCS,
    .tx_size      = XSK_RING_PROD__DEFAULT_NUM_DESCS,
    .bind_flags   = XDP_COPY,   /* force copy mode */
    /* .bind_flags = XDP_ZEROCOPY for zero-copy mode */
};
```

### 5.6 xsk_pool and Driver Integration

Drivers that support AF_XDP zero-copy mode register an `xsk_buff_pool` with the
AF_XDP subsystem.  The pool manages UMEM frame allocation and DMA mapping:

```c
/*
 * Key driver-side functions for AF_XDP zero-copy:
 */
struct xsk_buff_pool *xsk_get_pool_from_qid(struct net_device *dev,
                                             u16 queue_id);

/* Allocate a buffer from the pool (backed by a UMEM frame) */
struct xdp_buff *xsk_buff_alloc(struct xsk_buff_pool *pool);

/* Free a buffer back to the pool */
void xsk_buff_free(struct xdp_buff *xdp);

/* Complete a TX: return the UMEM frame to the Completion Ring */
void xsk_tx_completed(struct xsk_buff_pool *pool, u32 nb_entries);
```

---

## 6. Memory-Mapped Packet Sockets (AF_PACKET MMAP)

### 6.1 Overview

`PACKET_MMAP` provides a shared ring buffer between the kernel and user space
for high-speed packet capture and injection.  It predates AF_XDP and is the
mechanism used by `tcpdump`, `Wireshark`, and other capture tools.

### 6.2 Setup

```c
/* Create a raw packet socket */
int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

/* Configure the ring buffer */
struct tpacket_req3 req = {
    .tp_block_size   = 1 << 22,   /* 4 MiB per block          */
    .tp_block_nr     = 64,        /* 64 blocks = 256 MiB total*/
    .tp_frame_size   = 1 << 11,   /* 2048 bytes per frame     */
    .tp_frame_nr     = 64 * (1 << 22) / (1 << 11),
    .tp_retire_blk_tov = 60,      /* block timeout (ms)       */
    .tp_sizeof_priv  = 0,
    .tp_feature_req_word = TP_FT_REQ_FILL_RXHASH,
};

setsockopt(fd, SOL_PACKET, PACKET_RX_RING, &req, sizeof(req));

/* Memory-map the ring buffer */
void *ring = mmap(NULL, req.tp_block_size * req.tp_block_nr,
                  PROT_READ | PROT_WRITE,
                  MAP_SHARED | MAP_LOCKED, fd, 0);
```

### 6.3 TPACKET Versions

```
┌────────────┬──────────────────────────────────────────────────────────┐
│  Version   │  Features                                                │
├────────────┼──────────────────────────────────────────────────────────┤
│ TPACKET_V1 │  Original version.  Fixed frame size.  Per-frame status │
│            │  polling.  No VLAN metadata.                            │
├────────────┼──────────────────────────────────────────────────────────┤
│ TPACKET_V2 │  Adds VLAN tag support.  Supports 32-bit and 64-bit    │
│            │  with same structures.  Still per-frame polling.        │
├────────────┼──────────────────────────────────────────────────────────┤
│ TPACKET_V3 │  Variable-length frames packed into blocks.  Block-    │
│            │  level status polling (more efficient).  Timeout-based  │
│            │  block retirement.  Best for high-speed capture.        │
└────────────┴──────────────────────────────────────────────────────────┘
```

### 6.4 Frame Status Flags

The kernel and user space coordinate via status flags at the beginning of each
frame (V1/V2) or block header (V3):

```
┌──────────────────────┬─────────────────────────────────────────────┐
│  Flag                │  Meaning                                    │
├──────────────────────┼─────────────────────────────────────────────┤
│  TP_STATUS_KERNEL    │  Frame/block owned by kernel.  User must   │
│                      │  not touch it.  Kernel will fill it.       │
├──────────────────────┼─────────────────────────────────────────────┤
│  TP_STATUS_USER      │  Frame/block owned by user.  Kernel has    │
│                      │  written a packet; user may read it.       │
├──────────────────────┼─────────────────────────────────────────────┤
│  TP_STATUS_COPY      │  Packet was too large for the frame and    │
│                      │  was truncated.  Full copy in recvmsg().   │
├──────────────────────┼─────────────────────────────────────────────┤
│  TP_STATUS_LOSING    │  Packets were dropped (ring full).         │
├──────────────────────┼─────────────────────────────────────────────┤
│  TP_STATUS_CSUMNOTREADY │  Checksum not yet computed (offloaded). │
└──────────────────────┴─────────────────────────────────────────────┘
```

### 6.5 Ring Buffer Layout (TPACKET_V3)

```
┌────────────────────────────────────────────────────────────────┐
│                     mmap'd Ring Buffer                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Block 0                                                  │  │
│  │ ┌────────────┬─────────┬─────────┬─────────┬───────────┐│  │
│  │ │ Block Hdr  │ Frame 0 │ Frame 1 │ Frame 2 │    ...    ││  │
│  │ │ (status,   │ (pkt +  │ (pkt +  │ (pkt +  │           ││  │
│  │ │  num_pkts, │  hdr)   │  hdr)   │  hdr)   │           ││  │
│  │ │  offset)   │         │         │         │           ││  │
│  │ └────────────┴─────────┴─────────┴─────────┴───────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Block 1                                                  │  │
│  │ ┌────────────┬─────────┬─────────┬─────────┬───────────┐│  │
│  │ │ Block Hdr  │ Frame 0 │ Frame 1 │ Frame 2 │    ...    ││  │
│  │ └────────────┴─────────┴─────────┴─────────┴───────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ...                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Block N-1                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 6.6 Receive Loop (TPACKET_V3)

```c
struct tpacket_block_desc *block;
unsigned int block_idx = 0;

while (running) {
    block = (struct tpacket_block_desc *)
            (ring + block_idx * req.tp_block_size);

    /* Wait for block to become available */
    while (!(block->hdr.bh1.block_status & TP_STATUS_USER)) {
        struct pollfd pfd = { .fd = fd, .events = POLLIN };
        poll(&pfd, 1, -1);
    }

    /* Process all packets in this block */
    int num_pkts = block->hdr.bh1.num_pkts;
    struct tpacket3_hdr *hdr =
        (struct tpacket3_hdr *)((uint8_t *)block +
                                 block->hdr.bh1.offset_to_first_pkt);

    for (int i = 0; i < num_pkts; i++) {
        uint8_t *pkt = (uint8_t *)hdr + hdr->tp_mac;
        uint32_t len = hdr->tp_snaplen;

        process_packet(pkt, len);

        hdr = (struct tpacket3_hdr *)((uint8_t *)hdr + hdr->tp_next_offset);
    }

    /* Return block to kernel */
    block->hdr.bh1.block_status = TP_STATUS_KERNEL;
    block_idx = (block_idx + 1) % req.tp_block_nr;
}
```

---

## 7. Page Pool

### 7.1 The Problem: Page Allocator Overhead

Every received packet needs a page (or fragment thereof) to hold its data.
Without a page pool, the driver calls `alloc_page()` for every packet and
`put_page()` when the `sk_buff` is freed.  At high packet rates:

- The page allocator's zone-based locking becomes a contention point.
- Pages must be DMA-mapped and unmapped on every allocation/free cycle.
- TLB and cache pressure from constantly mapping new pages degrades performance.

### 7.2 page_pool_create()

The page pool provides per-NAPI page recycling with DMA mapping caches:

```c
struct page_pool_params pp_params = {
    .flags      = PP_FLAG_DMA_MAP | PP_FLAG_DMA_SYNC_DEV,
    .pool_size  = 256,          /* max pages in the pool              */
    .nid        = NUMA_NO_NODE, /* NUMA node (or dev_to_node(dev))    */
    .dev        = &pdev->dev,   /* device for DMA mapping             */
    .dma_dir    = DMA_FROM_DEVICE,
    .max_len    = PAGE_SIZE,    /* max data length per page           */
    .offset     = 0,            /* headroom offset                    */
};

struct page_pool *pool = page_pool_create(&pp_params);
if (IS_ERR(pool))
    return PTR_ERR(pool);
```

### 7.3 DMA Mapping Cache

A key optimization: when a page is allocated from the pool, its DMA address is
stored alongside the page metadata.  When the page is returned to the pool and
reallocated, the *same* DMA mapping is reused -- avoiding the expensive IOMMU
map/unmap cycle.

```
┌──────────────────────────────────────────────────────────────┐
│                Page Pool Operation                           │
│                                                              │
│  ┌────────────┐   page_pool_alloc_pages()   ┌────────────┐  │
│  │            │ ───────────────────────────► │  Recycled  │  │
│  │   Page     │                              │  Page +    │  │
│  │   Pool     │ ◄─────────────────────────── │  DMA addr  │  │
│  │            │   page_pool_put_page()       │  (cached)  │  │
│  └────────────┘                              └────────────┘  │
│       │                                           │          │
│       │ (pool empty)                              │          │
│       ▼                                           ▼          │
│  ┌────────────┐                              ┌────────────┐  │
│  │ alloc_page │                              │ NIC DMA    │  │
│  │ + dma_map  │   (slow path, only when      │ (reuses    │  │
│  │            │    pool is empty)             │  existing  │  │
│  └────────────┘                              │  mapping)  │  │
│                                              └────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 7.4 Core API

```c
/* Allocate a page from the pool (fast path: recycled page) */
struct page *page_pool_alloc_pages(struct page_pool *pool, gfp_t gfp);

/* Return a page to the pool for recycling */
void page_pool_put_page(struct page_pool *pool, struct page *page,
                        unsigned int dma_sync_size, bool allow_direct);

/* Bulk allocate pages (reduces per-call overhead) */
int page_pool_alloc_pages_bulk(struct page_pool *pool, gfp_t gfp,
                               int count, struct page **pages);

/* Get the cached DMA address of a pool-managed page */
dma_addr_t page_pool_get_dma_addr(struct page *page);

/* Destroy the pool (after all pages are returned) */
void page_pool_destroy(struct page_pool *pool);
```

### 7.5 Integration with build_skb() and napi_build_skb()

Drivers using page pools typically use `build_skb()` or `napi_build_skb()` to
construct an `sk_buff` around a page-pool-managed buffer:

```c
/* In the driver's NAPI poll function: */
struct page *page = page_pool_alloc_pages(rx_ring->page_pool, GFP_ATOMIC);
dma_addr_t dma = page_pool_get_dma_addr(page);

/* Program the NIC to DMA into this page */
rx_desc->addr = dma + rx_ring->rx_offset;
/* ... NIC receives packet ... */

/* After packet arrives, build sk_buff around the page */
void *buf = page_address(page) + rx_ring->rx_offset;
struct sk_buff *skb = napi_build_skb(buf, rx_ring->rx_buf_len);
if (!skb) {
    page_pool_put_page(rx_ring->page_pool, page, 0, true);
    return;
}

/* Mark the page for page-pool recycling when skb is freed */
skb_mark_for_recycle(skb);

skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN);
skb_put(skb, pkt_len);
skb->protocol = eth_type_trans(skb, netdev);

napi_gro_receive(&rx_ring->napi, skb);
/* When skb is eventually freed, page returns to the pool automatically */
```

### 7.6 Page Pool Statistics

Page pool effectiveness can be monitored via `ethtool`:

```bash
# Show page pool stats (kernel 5.18+)
ethtool -S eth0 | grep page_pool

# Typical output:
#   page_pool_alloc_fast: 1234567    (recycled, fast path)
#   page_pool_alloc_slow: 42         (had to call alloc_page)
#   page_pool_recycle_cached: 1234500
#   page_pool_recycle_ring: 67
```

---

## 8. sk_buff Recycling

### 8.1 The Cost of sk_buff Allocation

The `sk_buff` structure itself (separate from the data buffer) is allocated from
the `skbuff_head_cache` SLUB slab.  At high packet rates, the allocation and
freeing of `sk_buff` objects becomes a significant overhead:

- SLUB allocator per-CPU caches have limited depth.
- When the per-CPU cache is exhausted, the allocator falls back to the slab
  page, introducing locking overhead.
- `sk_buff` initialization zeroes multiple fields and sets up `skb_shared_info`.

### 8.2 napi_consume_skb() -- Budget-Aware Bulk Free

```c
/*
 * napi_consume_skb() — free an sk_buff within NAPI context.
 *
 * When 'budget' > 0 (inside NAPI poll), the sk_buff is added to a
 * per-CPU bulk-free list.  The list is flushed to the SLUB allocator
 * in batches, amortizing the per-object overhead.
 *
 * When 'budget' == 0 (outside NAPI, e.g., netpoll), falls back to
 * the normal dev_consume_skb() / __kfree_skb() path.
 */
void napi_consume_skb(struct sk_buff *skb, int budget);
```

Usage in a driver's TX completion handler:

```c
static int my_driver_tx_clean(struct my_tx_ring *ring, int budget)
{
    int cleaned = 0;

    while (cleaned < budget) {
        struct sk_buff *skb = ring->tx_buf[ring->clean_idx].skb;
        if (!skb)
            break;

        /* Unmap DMA buffers */
        dma_unmap_single(ring->dev,
                         ring->tx_buf[ring->clean_idx].dma,
                         skb->len, DMA_TO_DEVICE);

        /* Budget-aware bulk free */
        napi_consume_skb(skb, budget);

        ring->tx_buf[ring->clean_idx].skb = NULL;
        ring->clean_idx = (ring->clean_idx + 1) % ring->count;
        cleaned++;
    }

    return cleaned;
}
```

### 8.3 Per-CPU sk_buff Caches

The kernel maintains per-CPU caches at multiple levels:

```
┌─────────────────────────────────────────────────────────────────────┐
│  sk_buff Free Path (napi_consume_skb with budget > 0)              │
│                                                                     │
│  ┌──────────────┐                                                   │
│  │  sk_buff to  │                                                   │
│  │  free        │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────┐                                               │
│  │  NAPI bulk free  │ ── accumulate up to 64 sk_buffs               │
│  │  list (per-CPU)  │                                               │
│  └──────┬───────────┘                                               │
│         │ (flush when full or NAPI poll ends)                       │
│         ▼                                                           │
│  ┌──────────────────┐                                               │
│  │  SLUB per-CPU    │ ── per-CPU partial slab freelist               │
│  │  cache           │                                               │
│  └──────┬───────────┘                                               │
│         │ (overflow)                                                 │
│         ▼                                                           │
│  ┌──────────────────┐                                               │
│  │  SLUB slab page  │ ── shared, requires cmpxchg                   │
│  │  (node partial)  │                                               │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.4 Out-of-Tree skb_recycler Patches

Some high-throughput deployments (especially in the embedded/router space) use
out-of-tree `skb_recycler` patches.  These patches maintain a per-CPU free list
of fully initialized `sk_buff` objects.  When an `sk_buff` is freed, instead of
returning it to SLUB, it is placed on the recycler list.  The next allocation
pulls from this list, skipping SLUB entirely.

```c
/* Pseudocode for skb_recycler (out-of-tree concept) */
static DEFINE_PER_CPU(struct sk_buff_head, skb_recycle_list);

struct sk_buff *skb_recycler_alloc(struct net_device *dev, unsigned int len)
{
    struct sk_buff *skb;

    skb = __skb_dequeue(&per_cpu(skb_recycle_list, smp_processor_id()));
    if (skb) {
        /* Reset essential fields, reuse the sk_buff */
        skb_recycler_reset(skb);
        return skb;
    }

    /* Fallback to normal allocation */
    return __alloc_skb(len, GFP_ATOMIC, 0, NUMA_NO_NODE);
}
```

These patches are not upstream because:
- They can mask memory leaks (freed sk_buffs are never truly freed).
- Page pool + `napi_build_skb()` addresses the same problem in a cleaner way.
- Maintaining out-of-tree patches across kernel versions is burdensome.

---

## 9. Busy Polling

### 9.1 The Latency Problem

In the default interrupt-driven model, the receive path involves:

```
NIC interrupt → hardirq handler → raise softirq → softirq runs (NAPI poll)
    → sk_buff queued to socket → process woken up → process reads data
```

Each step adds latency.  The softirq may not run immediately if the CPU is busy;
the process may not be scheduled immediately after the softirq completes.  Total
latency from wire to application can be 20--50 microseconds.

### 9.2 SO_BUSY_POLL Socket Option

Busy polling allows a process to poll the NIC directly from process context,
bypassing the softirq path:

```c
int busy_poll_usec = 50;   /* poll for up to 50 microseconds */
setsockopt(fd, SOL_SOCKET, SO_BUSY_POLL,
           &busy_poll_usec, sizeof(busy_poll_usec));

int prefer_busy_poll = 1;
setsockopt(fd, SOL_SOCKET, SO_PREFER_BUSY_POLL,
           &prefer_busy_poll, sizeof(prefer_busy_poll));
```

Or system-wide:

```bash
# Enable busy polling globally (microseconds to busy-poll)
sysctl -w net.core.busy_poll=50
sysctl -w net.core.busy_read=50
```

### 9.3 How It Works: sk_busy_loop()

When the application calls `recv()` / `recvmsg()` / `poll()` / `epoll_wait()`
and no data is available, instead of sleeping immediately, the kernel enters
`sk_busy_loop()`:

```c
/*
 * sk_busy_loop() — poll NAPI from process context.
 *
 * Calls the driver's NAPI poll function directly, bypassing the
 * softirq mechanism.  Runs for up to 'busy_poll_usec' microseconds
 * or until data is available.
 */
void sk_busy_loop(struct sock *sk, int nonblock)
{
    unsigned long end_time = busy_loop_end_time(sk);
    struct napi_struct *napi;

    /* Find the NAPI structure associated with this socket's flow */
    napi = napi_by_id(READ_ONCE(sk->sk_napi_id));
    if (!napi)
        return;

    do {
        /* Call the driver's NAPI poll function directly */
        napi_busy_loop(napi, nonblock ? NULL : sk_busy_loop_end,
                       sk, prefer_busy_poll, budget);
    } while (!nonblock && skb_queue_empty(&sk->sk_receive_queue) &&
             !busy_loop_timeout(end_time));
}
```

### 9.4 Latency Comparison

```
┌──────────────────────┬───────────────────┬─────────────────────┐
│  Metric              │  Interrupt-driven │  Busy Polling       │
├──────────────────────┼───────────────────┼─────────────────────┤
│  Wire-to-app latency │  20-50 us         │  3-10 us            │
│  CPU usage (idle)    │  Low              │  100% on polling    │
│  Throughput          │  Moderate          │  Similar/higher     │
│  Jitter              │  Higher            │  Much lower         │
│  Power efficiency    │  Good              │  Poor               │
└──────────────────────┴───────────────────┴─────────────────────┘
```

### 9.5 Best Use Cases

Busy polling is most valuable for:
- Low-latency trading systems
- Real-time data processing
- In-memory databases (e.g., Redis, memcached)
- Any application where tail latency matters more than power efficiency

---

## 10. GRO/GSO Performance Impact

### 10.1 GRO -- Generic Receive Offload

GRO merges multiple related incoming packets into a single large `sk_buff`
before passing them up the stack.  This dramatically reduces per-packet overhead:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Without GRO (64 packets, 1500 bytes each):                           │
│                                                                        │
│  NIC → 64 sk_buffs → 64x protocol header parsing → 64x socket queue  │
│  Per-packet overhead: ~64 * 2 us = 128 us total                       │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│  With GRO (64 packets merged into 1 super-sk_buff, ~96 KiB):         │
│                                                                        │
│  NIC → 64 sk_buffs → GRO merges → 1 sk_buff → 1x protocol parsing   │
│  Per-packet overhead: ~1 * 5 us = 5 us total                          │
│                                                                        │
│  Effective reduction: ~25x fewer function calls through the stack      │
└────────────────────────────────────────────────────────────────────────┘
```

GRO merges packets by matching:
- Source and destination IP addresses
- Source and destination ports
- TCP sequence numbers (must be contiguous)
- Same flow hash

The merged `sk_buff` uses `skb_shared_info->frags[]` to hold the payload
fragments from each original packet while sharing a single set of headers.

### 10.2 GSO -- Generic Segmentation Offload

GSO is GRO's counterpart on the transmit side.  The application writes a large
buffer (e.g., 64 KiB), and the kernel creates a single `sk_buff` that travels
through most of the stack as one unit.  Segmentation into MSS-sized packets
is deferred until the last possible moment -- ideally to the NIC hardware (TSO),
or failing that, to the device driver layer.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Without GSO (application sends 64 KiB):                              │
│                                                                        │
│  sendmsg() → TCP segments immediately → 44 sk_buffs (1460 B each)    │
│  → 44x routing lookups → 44x netfilter traversals → NIC              │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│  With GSO (application sends 64 KiB):                                 │
│                                                                        │
│  sendmsg() → 1 sk_buff (64 KiB, gso_size=1460) → 1x routing         │
│  → 1x netfilter → segmentation at driver/NIC → 44 wire packets       │
│                                                                        │
│  Result: ~44x fewer function calls through the upper stack             │
└────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Measured Performance Improvements

Typical improvements from enabling GRO/GSO/TSO on a 25 Gbps NIC:

```
┌─────────────────────────┬────────────┬────────────┬────────────────┐
│  Feature                │  Off       │  On        │  Improvement   │
├─────────────────────────┼────────────┼────────────┼────────────────┤
│  GRO (RX throughput)    │  12 Gbps   │  24 Gbps   │  ~2x           │
│  GRO (CPU per Gbps)     │  8% CPU    │  2% CPU    │  ~4x           │
│  GSO (TX throughput)    │  14 Gbps   │  24 Gbps   │  ~1.7x         │
│  TSO (TX, HW offload)   │  14 Gbps   │  25 Gbps   │  ~1.8x         │
│  GRO+GSO+TSO combined   │  10 Gbps   │  25 Gbps   │  ~2.5x         │
└─────────────────────────┴────────────┴────────────┴────────────────┘
```

(Approximate numbers; actual results depend on CPU, NIC, packet size, and
workload characteristics.)

### 10.4 Tuning: ethtool GRO/GSO/TSO Toggle

```bash
# Check current offload status
ethtool -k eth0 | grep -E 'generic-receive-offload|generic-segmentation|tcp-segmentation'

# Enable GRO, GSO, and TSO
ethtool -K eth0 gro on
ethtool -K eth0 gso on
ethtool -K eth0 tso on

# Disable (for debugging or when offloads cause problems)
ethtool -K eth0 gro off
ethtool -K eth0 gso off
ethtool -K eth0 tso off
```

GRO can sometimes cause issues with:
- Packet captures (`tcpdump` sees merged packets, harder to analyze)
- Netfilter connection tracking (large merged packets counted as single)
- Applications that depend on per-packet timestamps

---

## 11. Performance Tuning Checklist

### 11.1 Ring Buffer Sizes

```bash
# Show current ring sizes
ethtool -g eth0

# Set RX and TX ring sizes to maximum
ethtool -G eth0 rx 4096 tx 4096

# Larger rings absorb traffic bursts but consume more memory
# Rule of thumb: set to max unless memory is constrained
```

### 11.2 Interrupt Coalescing

```bash
# Show current coalescing settings
ethtool -c eth0

# Optimize for throughput (more coalescing, higher latency)
ethtool -C eth0 rx-usecs 100 rx-frames 64 tx-usecs 100 tx-frames 64

# Optimize for latency (less coalescing)
ethtool -C eth0 rx-usecs 10 rx-frames 1 tx-usecs 10 tx-frames 1

# Adaptive coalescing (NIC adjusts automatically)
ethtool -C eth0 adaptive-rx on adaptive-tx on
```

### 11.3 RSS/RPS/RFS/XPS Configuration

```bash
# RSS (Receive Side Scaling) — hardware multi-queue
# Show number of queues
ethtool -l eth0
# Set to number of CPU cores
ethtool -L eth0 combined 16

# RPS (Receive Packet Steering) — software multi-queue
# Distribute RX processing across CPUs 0-7
echo "ff" > /sys/class/net/eth0/queues/rx-0/rps_cpus

# RFS (Receive Flow Steering) — steer to the CPU where the
# application is running
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 4096 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt

# XPS (Transmit Packet Steering) — map TX queues to CPUs
# CPU 0 uses TX queue 0, CPU 1 uses TX queue 1, etc.
echo 1 > /sys/class/net/eth0/queues/tx-0/xps_cpus
echo 2 > /sys/class/net/eth0/queues/tx-1/xps_cpus
echo 4 > /sys/class/net/eth0/queues/tx-2/xps_cpus
echo 8 > /sys/class/net/eth0/queues/tx-3/xps_cpus
```

### 11.4 NUMA Awareness and IRQ Affinity

```bash
# Show NUMA topology
numactl --hardware

# Show which NUMA node the NIC is on
cat /sys/class/net/eth0/device/numa_node

# Set IRQ affinity to match the NIC's NUMA node
# First, find the IRQ numbers
cat /proc/interrupts | grep eth0

# Set affinity (e.g., IRQ 42 to CPU 0)
echo 1 > /proc/irq/42/smp_affinity

# Automated script (many distros provide irqbalance, but for
# networking workloads, manual pinning is often better)
service irqbalance stop

# Pin NIC IRQs to the local NUMA node's CPUs
NUMA_NODE=$(cat /sys/class/net/eth0/device/numa_node)
CPULIST=$(numactl --hardware | grep "node $NUMA_NODE cpus:" | cut -d: -f2)
set_irq_affinity.sh eth0 $CPULIST
```

### 11.5 sysctl Tuning

```bash
# Maximum packets processed per softirq cycle
# Higher = better throughput, higher latency for other tasks
sysctl -w net.core.netdev_budget=600          # default: 300
sysctl -w net.core.netdev_budget_usecs=8000   # default: 2000

# Weight for NAPI polling (packets per poll)
sysctl -w net.core.dev_weight=128             # default: 64

# Socket buffer sizes
sysctl -w net.core.rmem_max=26214400          # 25 MiB max RX buffer
sysctl -w net.core.wmem_max=26214400          # 25 MiB max TX buffer
sysctl -w net.core.rmem_default=1048576       # 1 MiB default RX
sysctl -w net.core.wmem_default=1048576       # 1 MiB default TX

# TCP-specific buffer auto-tuning (min, default, max)
sysctl -w net.ipv4.tcp_rmem="4096 1048576 26214400"
sysctl -w net.ipv4.tcp_wmem="4096 1048576 26214400"

# Backlog queue size (packets queued when CPU is busy)
sysctl -w net.core.netdev_max_backlog=10000   # default: 1000

# Enable TCP window scaling
sysctl -w net.ipv4.tcp_window_scaling=1

# Enable TCP timestamps (needed for window scaling)
sysctl -w net.ipv4.tcp_timestamps=1
```

### 11.6 BQL (Byte Queue Limits) for TX

BQL prevents the TX ring from being overfilled, which would cause excessive
latency for packets waiting in the queue ("bufferbloat"):

```bash
# Show current BQL settings
cat /sys/class/net/eth0/queues/tx-0/byte_queue_limits/limit_max
cat /sys/class/net/eth0/queues/tx-0/byte_queue_limits/limit_min
cat /sys/class/net/eth0/queues/tx-0/byte_queue_limits/limit

# BQL is typically auto-tuned; manual overrides are rarely needed
# To force a maximum of 3000 bytes in the TX queue:
echo 3000 > /sys/class/net/eth0/queues/tx-0/byte_queue_limits/limit_max

# To disable BQL (not recommended):
echo 0 > /sys/class/net/eth0/queues/tx-0/byte_queue_limits/limit_max
```

### 11.7 Comprehensive Performance Diagnostic

```bash
#!/bin/bash
# Quick network performance diagnostic

DEV=${1:-eth0}

echo "=== Interface: $DEV ==="
echo ""

echo "--- Ring Buffer ---"
ethtool -g $DEV 2>/dev/null

echo "--- Offloads ---"
ethtool -k $DEV 2>/dev/null | grep -E 'offload|segmentation|scatter'

echo "--- Coalescing ---"
ethtool -c $DEV 2>/dev/null

echo "--- Queues ---"
ethtool -l $DEV 2>/dev/null

echo "--- NUMA Node ---"
cat /sys/class/net/$DEV/device/numa_node 2>/dev/null

echo "--- Softnet Stats (drops in column 2) ---"
cat /proc/net/softnet_stat

echo "--- Socket Buffer Sizes ---"
sysctl net.core.rmem_max net.core.wmem_max
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem

echo "--- NAPI Budget ---"
sysctl net.core.netdev_budget net.core.netdev_budget_usecs

echo "--- Backlog ---"
sysctl net.core.netdev_max_backlog
```

### 11.8 Performance Tuning Decision Flowchart

```
┌──────────────────────────────────────┐
│  Symptom: Low throughput / high CPU  │
└─────────────────┬────────────────────┘
                  │
                  ▼
         ┌────────────────┐     yes    ┌────────────────────────┐
         │ GRO/GSO/TSO    ├───────────►│ Enable: ethtool -K     │
         │ disabled?      │            │ eth0 gro/gso/tso on    │
         └───────┬────────┘            └────────────────────────┘
                 │ no
                 ▼
         ┌────────────────┐     yes    ┌────────────────────────┐
         │ Single RX/TX   ├───────────►│ Enable RSS: ethtool -L │
         │ queue?         │            │ eth0 combined <ncpus>  │
         └───────┬────────┘            └────────────────────────┘
                 │ no
                 ▼
         ┌────────────────┐     yes    ┌────────────────────────┐
         │ IRQs on wrong  ├───────────►│ Pin IRQs to local NUMA │
         │ NUMA node?     │            │ node CPUs              │
         └───────┬────────┘            └────────────────────────┘
                 │ no
                 ▼
         ┌────────────────┐     yes    ┌────────────────────────┐
         │ Ring buffer    ├───────────►│ Increase: ethtool -G   │
         │ too small?     │            │ eth0 rx 4096 tx 4096   │
         └───────┬────────┘            └────────────────────────┘
                 │ no
                 ▼
         ┌────────────────┐     yes    ┌────────────────────────┐
         │ softnet_stat   ├───────────►│ Increase netdev_budget │
         │ shows drops?   │            │ and netdev_max_backlog │
         └───────┬────────┘            └────────────────────────┘
                 │ no
                 ▼
         ┌────────────────┐     yes    ┌────────────────────────┐
         │ Application    ├───────────►│ Consider XDP, AF_XDP,  │
         │ needs > 10Mpps?│            │ or kernel bypass (DPDK)│
         └────────────────┘            └────────────────────────┘
```

---

## References

- `include/linux/skbuff.h` -- sk_buff and skb_shared_info definitions
- `include/net/xdp.h` -- xdp_buff, xdp_frame definitions
- `net/core/skbuff.c` -- sk_buff allocation, cloning, zero-copy support
- `net/core/page_pool.c` -- page pool implementation
- `net/xdp/xsk.c` -- AF_XDP socket implementation
- `net/packet/af_packet.c` -- PACKET_MMAP implementation
- `Documentation/networking/msg_zerocopy.rst` -- MSG_ZEROCOPY documentation
- `Documentation/networking/page_pool.rst` -- Page pool documentation
- `Documentation/networking/af_xdp.rst` -- AF_XDP documentation
- `tools/testing/selftests/bpf/` -- XDP and AF_XDP test programs
