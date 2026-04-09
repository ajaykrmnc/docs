# Chapter 1: sk_buff Structure and Memory Layout

> **Kernel version reference:** Linux 6.x series. Field offsets and sizes may vary across
> versions; the conceptual layout has been stable since approximately 2.6.22.

---

## 1. Introduction

### 1.1 What sk_buff Is and Why It Exists

The `struct sk_buff` (socket buffer) is the single most important data structure in the
Linux networking stack. Every packet -- whether inbound from a NIC, outbound from a
socket, forwarded between interfaces, or synthesized internally -- is represented by
exactly one `sk_buff` instance throughout its lifetime in the kernel.

The structure serves three fundamental purposes:

1. **Packet metadata container.** It carries all bookkeeping information about a packet:
   which device received it, which socket owns it, what protocol it uses, its priority,
   its checksum state, timestamps, routing decisions, and dozens of other fields that
   various subsystems consult as the packet traverses the stack.

2. **Buffer management descriptor.** It describes where the actual packet data lives in
   memory -- both the contiguous "linear" portion and any additional paged fragments --
   without copying data between layers.

3. **Linked-list node.** Socket receive queues, device transmit queues, and internal
   staging queues all thread sk_buffs together via intrusive doubly-linked list pointers
   embedded in the structure itself.

The design goal is efficiency: a packet arriving on the wire should be touched as few
times as possible, allocated once, described precisely, and passed by pointer through
every layer of the stack until it is either delivered to userspace or freed.

### 1.2 Historical Context: BSD mbuf vs. Linux sk_buff

BSD-derived systems use the `mbuf` (memory buffer) architecture dating back to 4.2BSD.
An mbuf is a small, fixed-size buffer (historically 128 or 256 bytes) that chains together
to hold arbitrarily sized packets. This design prioritizes memory frugality on small
machines but introduces significant complexity:

```
BSD mbuf chain (conceptual):

  ┌────────┐     ┌────────┐     ┌────────┐
  │ m_next─┼────►│ m_next─┼────►│ m_next─┼──► NULL
  │ m_len  │     │ m_len  │     │ m_len  │
  │ m_data │     │ m_data │     │ m_data │
  │ [data] │     │ [data] │     │ [data] │
  └────────┘     └────────┘     └────────┘
     128 B          128 B          128 B

  Problem: a 1500-byte Ethernet frame requires chaining
  ~12 mbufs, or using an "mbuf cluster" (external page).
```

When Linus Torvalds and Alan Cox designed the Linux networking stack in the early 1990s,
they made a deliberate architectural departure:

- **One sk_buff per packet.** A single structure describes the entire packet.
- **Contiguous linear buffer.** The common case (small-to-medium packets) uses a single
  kmalloc'd buffer large enough for the entire frame, avoiding chains entirely.
- **Scatter-gather for large packets.** Only truly large packets (GSO, jumbo frames) use
  the paged-fragment mechanism in `skb_shared_info`, which is an array, not a linked list.

The trade-off is clear: Linux uses more memory per small packet (an sk_buff plus a
full-sized buffer versus a compact mbuf), but gains:

- **Zero-copy header parsing.** Headers are accessed via pointer arithmetic within a
  contiguous region; no "pullup" operations across chain boundaries.
- **Simpler buffer manipulation.** Pushing/pulling headers is just pointer movement.
- **Cache friendliness.** A single linear buffer is far more cache-friendly than a chain
  of small mbufs scattered across memory.
- **Predictable allocation.** One allocation for the descriptor, one for the data buffer.

### 1.3 The "One sk_buff Per Packet" Principle

The principle is simple to state and subtle in its implications:

> Every packet in the Linux networking stack is represented by exactly one `struct sk_buff`.
> The sk_buff is **not** reused for a different packet; once freed, it is gone. If a packet
> must be duplicated (e.g., for multicast delivery to multiple sockets), a new sk_buff is
> allocated that may share the underlying data buffer (via reference counting) but maintains
> its own metadata.

This means:

- The sk_buff is allocated when the packet enters the kernel (either from a NIC driver via
  `netdev_alloc_skb()` or from a socket via `sock_alloc_send_skb()`).
- It is freed when the packet is consumed (delivered to userspace, transmitted on the wire,
  or dropped).
- Every function along the packet's path receives a pointer to the same sk_buff and may
  modify its metadata fields, adjust its data pointers, or attach additional information.
- The sk_buff is **not** embedded inside the data buffer; it is a separate heap allocation.

This ownership model simplifies lifetime management: at any point, exactly one subsystem
"owns" the sk_buff, and ownership is transferred explicitly (by passing the pointer and
relinquishing the caller's reference).

---

## 2. The Complete struct sk_buff

The following is a commented definition of `struct sk_buff` reflecting the kernel 6.x
layout. Fields are grouped by purpose. Some fields are architecture-dependent or
conditionally compiled; the most universally present fields are shown.

```c
/*
 * struct sk_buff - the core network packet descriptor
 *
 * Defined in: include/linux/skbuff.h
 *
 * Note: the actual kernel definition uses extensive #ifdefs,
 * __attribute__((aligned)), and anonymous unions. This version
 * is simplified for clarity while preserving the conceptual
 * grouping and field semantics.
 */
struct sk_buff {
    /* ─── Linked-list pointers ─────────────────────────────── */
    union {
        struct {
            struct sk_buff      *next;      /* next buffer in list         */
            struct sk_buff      *prev;      /* previous buffer in list     */
        };
        struct rb_node          rbnode;     /* used in TCP retransmit tree */
        struct list_head        list;       /* alternative list linkage    */
    };

    union {
        struct sock             *sk;        /* owning socket (may be NULL) */
        int                     ip_defrag_offset; /* used during defrag   */
    };

    /* ─── Device reference ─────────────────────────────────── */
    struct net_device           *dev;       /* device that received/sends
                                              this packet. Changes as the
                                              packet moves through the
                                              stack (e.g., bridging)      */

    /* ─── Timestamp ────────────────────────────────────────── */
    ktime_t                     tstamp;     /* packet timestamp (rx or tx)
                                              Set by driver or SO_TIMESTAMP
                                              socket option               */

    /* ─── Routing/destination cache ────────────────────────── */
    unsigned long               _skb_refdst; /* dst_entry with low bit
                                               encoding refcount policy.
                                               Accessed via skb_dst()     */

    /* ─── Destructor callback ──────────────────────────────── */
    void                        (*destructor)(struct sk_buff *skb);
                                            /* called when skb is freed.
                                               Used by sockets to release
                                               wmem accounting           */

    /* ─── Netfilter conntrack ──────────────────────────────── */
#if IS_ENABLED(CONFIG_NF_CONNTRACK)
    unsigned long               _nfct;      /* nf_conntrack pointer +
                                               ctinfo in low bits        */
#endif

    /* ─── Control buffer (protocol scratch area) ───────────── */
    char                        cb[48]
        __aligned(8);                       /* per-protocol private data.
                                               Each layer casts this to
                                               its own struct. See sec. 6 */

    /* ─── Length fields ────────────────────────────────────── */
    unsigned int                len;        /* total bytes of packet data.
                                               Includes both linear data
                                               AND paged fragments       */
    unsigned int                data_len;   /* bytes in paged fragments
                                               only. Linear data length =
                                               len - data_len            */
    __u16                       mac_len;    /* length of MAC header       */
    __u16                       hdr_len;    /* length of writable clone
                                               header area               */

    /* ─── Checksum fields ──────────────────────────────────── */
    __u16                       queue_mapping; /* tx queue selected       */
    __u8                        cloned:1;   /* head may be shared         */
    __u8                        nohdr:1;    /* skb header is not cloned   */
    __u8                        fclone:2;   /* sk_buff clone status       */
    __u8                        peeked:1;   /* packet has been peeked     */
    __u8                        head_frag:1;/* head is a page fragment    */
    __u8                        pfmemalloc:1;/* allocated from PFMEMALLOC
                                               reserves                  */
    __u8                        pp_recycle:1;/* page pool recycling hint  */

    /* ─── Active type (data path union) ────────────────────── */
    __u8                        active_type; /* which member of data union
                                               is active (for KASAN)     */

#ifdef CONFIG_NET_SCHED
    __u16                       tc_index;   /* traffic control index      */
#endif

    union {
        __wsum                  csum;       /* partial checksum value     */
        struct {
            __u16               csum_start; /* offset from head where
                                               checksumming begins       */
            __u16               csum_offset;/* offset from csum_start
                                               where to store checksum   */
        };
    };

    /* ─── Priority and protocol ────────────────────────────── */
    __u32                       priority;   /* packet priority (SO_PRIORITY
                                               or TOS-derived). Drives
                                               queuing discipline        */
    __u16                       transport_header; /* offset from head to
                                                     transport (L4) hdr  */
    __u16                       network_header;   /* offset from head to
                                                     network (L3) hdr    */
    __u16                       mac_header;       /* offset from head to
                                                     MAC (L2) hdr        */
    __u16                       inner_transport_header; /* for encap     */
    __u16                       inner_network_header;   /* for encap     */
    __u16                       inner_mac_header;       /* for encap     */

    __be16                      protocol;   /* L3 protocol in network byte
                                               order: ETH_P_IP, ETH_P_IPV6,
                                               ETH_P_ARP, etc.           */
    __be16                      inner_protocol; /* inner protocol (encap) */

    /* ─── VLAN fields ──────────────────────────────────────── */
    __u16                       vlan_present:1; /* VLAN tag is valid      */
    __u16                       vlan_proto;     /* VLAN protocol (802.1Q
                                                   or 802.1ad)           */
    __u16                       vlan_tci;       /* VLAN tag control info:
                                                   PCP + DEI + VID       */

    /* ─── Bit fields block ─────────────────────────────────── */
    __u8                        pkt_type:3; /* PACKET_HOST, PACKET_BROADCAST,
                                               PACKET_MULTICAST, etc.    */
    __u8                        ignore_df:1;/* allow local fragmentation */
    __u8                        dst_pending_confirm:1; /* need dst confirm*/
    __u8                        ip_summed:2;/* checksum status:
                                               CHECKSUM_NONE
                                               CHECKSUM_UNNECESSARY
                                               CHECKSUM_COMPLETE
                                               CHECKSUM_PARTIAL         */
    __u8                        ooo_okay:1; /* out-of-order is ok        */

    __u8                        l4_hash:1;  /* hash includes L4 ports    */
    __u8                        sw_hash:1;  /* hash computed in software */
    __u8                        wifi_acked_valid:1;
    __u8                        wifi_acked:1;
    __u8                        no_fcs:1;   /* don't append FCS on tx    */
    __u8                        encapsulation:1; /* encapsulated packet  */
    __u8                        encap_hdr_csum:1;
    __u8                        csum_valid:1;/* checksum already verified */

    /* ─── Packet hash ──────────────────────────────────────── */
    __u32                       hash;       /* flow hash for RPS/RFS.
                                               Set by driver or software
                                               (Toeplitz or jhash)      */

    /* ─── Secmark (SELinux) ────────────────────────────────── */
    __u32                       secmark;    /* security marking          */

    /* ─── Mark (netfilter/iptables) ────────────────────────── */
    union {
        __u32                   mark;       /* generic packet mark.
                                               iptables -j MARK sets this.
                                               Used for policy routing,
                                               traffic classification   */
        __u32                   reserved_tailroom; /* in head_frag mode  */
    };

    /* ─── Sender CPU and allocation info ───────────────────── */
    __u16                       sender_cpu; /* CPU that sent the packet  */
    union {
        __u32                   skb_iif;    /* input interface index      */
    };

    /* ─── XDP and redirect ─────────────────────────────────── */
    __u32                       alloc_cpu;  /* CPU where skb was alloc'd */

    /* ─── Transmit hints ───────────────────────────────────── */
    __u8                        xmit_more:1;/* more packets follow in
                                               burst (batching hint)    */

    /* ─── The four critical data pointers ──────────────────── */
    /* See section 3 for a full explanation                     */
    sk_buff_data_t              tail;       /* end of actual data        */
    sk_buff_data_t              end;        /* end of allocated buffer
                                               (start of skb_shared_info)*/
    unsigned char               *head;      /* start of allocated buffer */
    unsigned char               *data;      /* start of actual data      */

    /* ─── Size and reference counting ──────────────────────── */
    unsigned int                truesize;   /* total memory charged to
                                               the owning socket.
                                               Includes sk_buff struct +
                                               data buffer + fragments  */
    refcount_t                  users;      /* reference count on the
                                               sk_buff descriptor itself.
                                               When this drops to 0, the
                                               sk_buff is freed         */

    /* ─── Extensions (optional, pointer to extended metadata)  */
#ifdef CONFIG_SKB_EXTENSIONS
    struct skb_ext              *extensions; /* additional metadata such
                                               as TC, bridge, IPsec     */
#endif
};
```

### 2.1 Field Grouping Summary

The fields above can be organized into logical groups:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      struct sk_buff (~232 bytes)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ LIST LINKAGE       next, prev / rbnode / list               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ OWNERSHIP           sk, dev, destructor                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ ROUTING / CONNTRACK  _skb_refdst, _nfct                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ PROTOCOL SCRATCH     cb[48]                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ LENGTHS              len, data_len, mac_len, hdr_len        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ HEADER OFFSETS       transport_header, network_header,      │    │
│  │                      mac_header, inner_* variants           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ PROTOCOL / VLAN      protocol, vlan_tci, vlan_proto         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ BIT FLAGS            pkt_type, ip_summed, cloned, fclone,   │    │
│  │                      encapsulation, csum_valid, ...         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ HASH / MARK          hash, mark, secmark, priority          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ DATA POINTERS        head, data, tail, end                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ ACCOUNTING           truesize, users                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Cache-Line Considerations

The kernel developers carefully arrange fields within `struct sk_buff` to minimize cache
misses on the hot path. The first cache line (64 bytes on x86-64) contains:

- `next`, `prev` (or `rbnode`) -- for queue traversal
- `sk` -- for socket ownership checks
- `dev` -- for device lookups
- `tstamp` -- commonly accessed for packet scheduling

The second cache line typically contains:

- `_skb_refdst` -- routing lookup result
- `destructor` -- checked on free
- `_nfct` -- conntrack, hot in firewall paths
- `cb[]` -- begins here; protocols read it immediately

This layout means that the most common receive-path operations (queue insertion,
protocol identification, routing lookup) touch at most two cache lines of the sk_buff
itself, with the actual packet data in a separate allocation that the CPU prefetches
independently.

---

## 3. The Four Critical Pointers: head, data, tail, end

### 3.1 Overview

Every `sk_buff` points to a contiguous memory region called the **linear data buffer**.
This buffer is described by four pointers (or, in the case of `tail` and `end`, offsets
from `head` on 64-bit systems to save space):

```
                        Linear Data Buffer
                        ══════════════════

head ──────────────►  ┌──────────────────────────────────┐  address low
                      │                                  │
                      │          Headroom                │  reserved space
                      │    (available for pushing        │  for prepending
                      │     headers as packet moves      │  headers
                      │     down the stack)               │
                      │                                  │
data ──────────────►  ├──────────────────────────────────┤
                      │                                  │
                      │        Packet Data               │  the actual
                      │   (headers + payload as          │  content that
                      │    currently visible to          │  the current
                      │    the protocol layer)           │  layer sees
                      │                                  │
tail ──────────────►  ├──────────────────────────────────┤
                      │                                  │
                      │         Tailroom                 │  available space
                      │    (available for appending      │  for appending
                      │     data at the end)             │  data
                      │                                  │
end  ──────────────►  ├──────────────────────────────────┤
                      │                                  │
                      │      skb_shared_info             │  scatter-gather
                      │   (always lives right after      │  fragment info,
                      │    the linear buffer)            │  GSO state, etc.
                      │                                  │
                      └──────────────────────────────────┘  address high
```

### 3.2 The Role of Each Pointer

**`head`** -- Points to the very first byte of the allocated buffer. This never changes
after allocation. It marks the absolute beginning of the memory region. Headroom extends
from `head` to `data`.

**`data`** -- Points to the first byte of the current packet data as seen by the present
protocol layer. This pointer **moves** as the packet traverses the stack:
- On receive, the driver sets `data` to point at the beginning of the Ethernet header.
  As the packet moves up, the Ethernet layer "pulls" the MAC header by advancing `data`
  past it, exposing the IP header. The IP layer then pulls the IP header, and so on.
- On transmit, the transport layer starts with `data` pointing at the payload. As the
  packet moves down, each layer "pushes" its header by moving `data` backward into the
  headroom.

**`tail`** -- Points one byte past the last byte of current packet data. The region from
`tail` to `end` is tailroom. `tail` moves when data is appended (via `skb_put()`).

**`end`** -- Points one byte past the last usable byte of the linear buffer. The
`skb_shared_info` structure is placed at this address. `end` never changes after
allocation.

### 3.3 Fundamental Length Relationships

```c
/*
 * The key invariants:
 *
 * headroom    = skb->data - skb->head
 * linear_len  = skb->tail - skb->data     (also: skb->len - skb->data_len)
 * tailroom    = skb->end  - skb->tail
 * total_buf   = skb->end  - skb->head     (usable buffer, excludes shinfo)
 *
 * skb->len    = linear_len + skb->data_len
 *               where data_len accounts for paged fragments
 *
 * skb->truesize = sizeof(struct sk_buff) + (skb->end - skb->head) +
 *                 sizeof(struct skb_shared_info) + paged fragment sizes
 */

static inline unsigned int skb_headroom(const struct sk_buff *skb)
{
    return skb->data - skb->head;
}

static inline int skb_tailroom(const struct sk_buff *skb)
{
    return skb->end - skb->tail;
}

/* Linear data length (excluding paged fragments) */
static inline unsigned int skb_headlen(const struct sk_buff *skb)
{
    return skb->len - skb->data_len;
}
```

### 3.4 How Pointers Move During Packet Processing

#### 3.4.1 Receive Path (Packet Moving Up the Stack)

```
Step 1: Driver allocates sk_buff and copies frame from NIC
═══════════════════════════════════════════════════════════

head ──► ┌─────────────────────┐
         │     Headroom        │  (NET_SKB_PAD, typically 64 bytes
         │                     │   for cache alignment + XDP)
data ──► ├─────────────────────┤
         │  Ethernet Header    │  14 bytes
         ├─────────────────────┤
         │  IP Header          │  20 bytes
         ├─────────────────────┤
         │  TCP Header         │  20 bytes
         ├─────────────────────┤
         │  Payload            │  variable
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘

  skb->protocol = htons(ETH_P_IP)
  skb->len      = 14 + 20 + 20 + payload_len


Step 2: eth_type_trans() processes Ethernet header
══════════════════════════════════════════════════

  Calls skb_pull(skb, ETH_HLEN) to advance data past Ethernet header.

head ──► ┌─────────────────────┐
         │     Headroom        │
         ├─────────────────────┤
         │  Ethernet Header    │  ◄── still in buffer, but before data
data ──► ├─────────────────────┤      (mac_header offset points here)
         │  IP Header          │
         ├─────────────────────┤
         │  TCP Header         │
         ├─────────────────────┤
         │  Payload            │
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘

  skb->len is reduced by 14
  skb->mac_header still references the Ethernet header


Step 3: ip_rcv() processes IP header
════════════════════════════════════

  Sets network_header, then may pull IP header:
  skb_pull(skb, ip_hdrlen)

head ──► ┌─────────────────────┐
         │     Headroom        │
         ├─────────────────────┤
         │  Ethernet Header    │
         ├─────────────────────┤
         │  IP Header          │  ◄── network_header points here
data ──► ├─────────────────────┤
         │  TCP Header         │
         ├─────────────────────┤
         │  Payload            │
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘


Step 4: tcp_v4_rcv() processes TCP header
═════════════════════════════════════════

  Sets transport_header, then pulls TCP header.

head ──► ┌─────────────────────┐
         │     Headroom        │
         ├─────────────────────┤
         │  Ethernet Header    │  ◄── mac_header
         ├─────────────────────┤
         │  IP Header          │  ◄── network_header
         ├─────────────────────┤
         │  TCP Header         │  ◄── transport_header
data ──► ├─────────────────────┤
         │  Payload            │  ◄── this is what the socket sees
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘

  skb->len = payload length only
  All three header offsets are set; the headers
  remain accessible via skb_mac_header(), etc.
```

#### 3.4.2 Transmit Path (Packet Moving Down the Stack)

```
Step 1: Application calls send(). TCP creates sk_buff with payload.
═══════════════════════════════════════════════════════════════════

head ──► ┌─────────────────────┐
         │                     │
         │     Headroom        │  (MAX_TCP_HEADER bytes reserved)
         │                     │
data ──► ├─────────────────────┤
         │  Payload            │
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘


Step 2: TCP prepends TCP header via skb_push()
═════════════════════════════════════════════

head ──► ┌─────────────────────┐
         │     Headroom        │  (reduced by 20+ bytes)
data ──► ├─────────────────────┤
         │  TCP Header         │  ◄── transport_header
         ├─────────────────────┤
         │  Payload            │
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘


Step 3: IP prepends IP header via skb_push()
═══════════════════════════════════════════

head ──► ┌─────────────────────┐
         │     Headroom        │  (reduced by another 20 bytes)
data ──► ├─────────────────────┤
         │  IP Header          │  ◄── network_header
         ├─────────────────────┤
         │  TCP Header         │  ◄── transport_header
         ├─────────────────────┤
         │  Payload            │
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘


Step 4: Ethernet/dev_hard_header() prepends MAC header
══════════════════════════════════════════════════════

head ──► ┌─────────────────────┐
         │  Headroom (small)   │
data ──► ├─────────────────────┤
         │  Ethernet Header    │  ◄── mac_header
         ├─────────────────────┤
         │  IP Header          │  ◄── network_header
         ├─────────────────────┤
         │  TCP Header         │  ◄── transport_header
         ├─────────────────────┤
         │  Payload            │
tail ──► ├─────────────────────┤
         │     Tailroom        │
end  ──► ├─────────────────────┤
         │  skb_shared_info    │
         └─────────────────────┘

  Packet is now ready for the NIC driver.
  data points to the first byte to transmit.
  len = ETH_HLEN + IP_HLEN + TCP_HLEN + payload.
```

### 3.5 Core Buffer Manipulation Functions

```c
/*
 * skb_reserve() - increase the headroom of an empty sk_buff
 *
 * Called immediately after allocation, before any data is placed.
 * Advances both data and tail forward by 'len' bytes.
 *
 *   Before:                      After skb_reserve(skb, N):
 *   head ──► data ──► tail       head ──► [N bytes] ──► data ──► tail
 */
static inline void skb_reserve(struct sk_buff *skb, int len)
{
    skb->data += len;
    skb->tail += len;
}

/*
 * skb_put() - add data to a buffer's tail
 *
 * Extends the used data area toward the end of the buffer.
 * Returns a pointer to the first byte of the newly added area.
 * Decreases tailroom by 'len'.
 *
 *   Before:                      After skb_put(skb, N):
 *   data ──► [...] ──► tail      data ──► [...][N bytes] ──► tail
 *                   tailroom                            tailroom-N
 */
void *skb_put(struct sk_buff *skb, unsigned int len)
{
    void *tmp = skb_tail_pointer(skb);
    SKB_LINEAR_ASSERT(skb);
    skb->tail += len;
    skb->len  += len;
    if (unlikely(skb->tail > skb->end))
        skb_over_panic(skb, len, __builtin_return_address(0));
    return tmp;
}

/*
 * skb_push() - add data to the start of a buffer (prepend a header)
 *
 * Moves data pointer backward into headroom. Increases len.
 * Returns the new data pointer.
 *
 *   Before:                      After skb_push(skb, N):
 *   headroom ──► data            headroom-N ──► data
 *                                             (old data is now data+N)
 */
void *skb_push(struct sk_buff *skb, unsigned int len)
{
    skb->data -= len;
    skb->len  += len;
    if (unlikely(skb->data < skb->head))
        skb_under_panic(skb, len, __builtin_return_address(0));
    return skb->data;
}

/*
 * skb_pull() - remove data from the start of a buffer (strip a header)
 *
 * Advances data pointer forward, shrinking the visible packet.
 * Returns the new data pointer, or NULL if len > skb->len.
 *
 *   Before:                      After skb_pull(skb, N):
 *   data ──► [hdr][payload]      data ──► [payload]
 *                                  (old header is now in headroom)
 */
void *skb_pull(struct sk_buff *skb, unsigned int len)
{
    skb->len -= len;
    if (unlikely(skb->len < skb->data_len))
        BUG();
    return skb->data += len;
}
```

### 3.6 sk_buff_data_t: Pointer vs. Offset

On 32-bit systems, `tail` and `end` are plain `unsigned char *` pointers. On 64-bit
systems, they are stored as `unsigned int` offsets from `head` to save 8 bytes of space
in the sk_buff structure (a pointer is 8 bytes; an offset is 4 bytes).

```c
/*
 * From include/linux/skbuff.h:
 */
#if BITS_PER_LONG > 32
    typedef unsigned int sk_buff_data_t;
    /* tail and end are offsets from head */
    /* Access: skb->head + skb->tail     */
#else
    typedef unsigned char *sk_buff_data_t;
    /* tail and end are direct pointers   */
#endif

/*
 * Helper to get the actual tail pointer:
 */
static inline unsigned char *skb_tail_pointer(const struct sk_buff *skb)
{
#if BITS_PER_LONG > 32
    return skb->head + skb->tail;   /* offset → pointer */
#else
    return skb->tail;               /* already a pointer */
#endif
}

static inline unsigned char *skb_end_pointer(const struct sk_buff *skb)
{
#if BITS_PER_LONG > 32
    return skb->head + skb->end;
#else
    return skb->end;
#endif
}
```

This optimization saves 8 bytes per sk_buff on 64-bit systems, which matters when
millions of sk_buffs may be in flight on a busy server.

---

## 4. skb_shared_info

### 4.1 Purpose and Location

`struct skb_shared_info` lives **immediately after the linear data buffer**, at the
address pointed to by `skb->end` (or equivalently, `skb_end_pointer(skb)`). It is
part of the same allocation as the data buffer, so no additional memory allocation is
needed to create it. Every sk_buff has an associated `skb_shared_info`, even if the
packet has no paged fragments.

```
                        Memory Layout
                        ═════════════

  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │         struct sk_buff (heap allocation #1)              │
  │         ~232 bytes on 64-bit                            │
  │                                                         │
  │    head ──────────┐    data ──────────┐                 │
  │    tail (offset)  │    end (offset)   │                 │
  │                   │                   │                 │
  └───────────────────┼───────────────────┼─────────────────┘
                      │                   │
                      ▼                   ▼
  ┌───────────────────┬───────────────────┬─────────────────┐
  │                   │                   │                 │
  │    Headroom       │   Packet Data     │   Tailroom      │
  │                   │                   │                 │
  │                   │                   │                 │
  │                   │                   │                 │
  ├───────────────────┴───────────────────┴─────────────────┤  ◄── end
  │                                                         │
  │              struct skb_shared_info                      │
  │              (~320 bytes on 64-bit)                      │
  │                                                         │
  │    ┌─────────────────────────────────────────────┐      │
  │    │  dataref                                    │      │
  │    │  nr_frags                                   │      │
  │    │  gso_size, gso_segs, gso_type               │      │
  │    │  frag_list ──────────────────► (sk_buff *)   │      │
  │    │  frags[MAX_SKB_FRAGS]  (up to 17 entries)   │      │
  │    │    ┌──────────────────────┐                  │      │
  │    │    │ frag[0]: page,offset,│                  │      │
  │    │    │          size        │                  │      │
  │    │    ├──────────────────────┤                  │      │
  │    │    │ frag[1]: page,offset,│                  │      │
  │    │    │          size        │                  │      │
  │    │    ├──────────────────────┤                  │      │
  │    │    │       ...            │                  │      │
  │    │    └──────────────────────┘                  │      │
  │    │  tx_flags                                   │      │
  │    │  tskey                                      │      │
  │    │  meta_len (XDP metadata)                    │      │
  │    └─────────────────────────────────────────────┘      │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
        ▲
        │
        This entire region (head → end of skb_shared_info)
        is a SINGLE allocation (heap allocation #2)
```

### 4.2 Full Structure Definition

```c
/*
 * struct skb_shared_info - data shared between sk_buff clones
 *
 * This structure sits at skb_end_pointer(skb), right after
 * the linear data buffer. It manages:
 *   - Reference counting for shared data buffers
 *   - Scatter-gather (paged) fragments
 *   - GSO (Generic Segmentation Offload) metadata
 *   - Hardware TX timestamping
 *
 * Defined in: include/linux/skbuff.h
 */
struct skb_shared_info {
    /* ─── Flags and reference count ────────────────────────── */
    __u8                flags;          /* SKBFL_* flags              */
    __u8                meta_len;       /* XDP metadata length        */
    __u8                nr_frags;       /* number of paged fragments
                                           in frags[] array. Range:
                                           0 to MAX_SKB_FRAGS (17)   */
    __u8                tx_flags;       /* transmit flags:
                                           SKBTX_HW_TSTAMP
                                           SKBTX_SW_TSTAMP
                                           SKBTX_IN_PROGRESS
                                           SKBTX_HW_TSTAMP_USE_CYCLES
                                           etc.                      */

    unsigned short      gso_size;       /* GSO: size of each segment.
                                           For TSO, this is the MSS.
                                           0 means no GSO            */
    unsigned short      gso_segs;       /* GSO: number of segments
                                           that this packet will be
                                           split into                */
    /* ─── Fragment list ────────────────────────────────────── */
    struct sk_buff      *frag_list;     /* list of sk_buffs forming
                                           a fragmented packet.
                                           Used by IP fragmentation
                                           reassembly. This is
                                           DIFFERENT from scatter-
                                           gather frags[]            */

    /* ─── Shared data reference count ──────────────────────── */
    struct skb_shared_hwtstamps hwtstamps; /* hardware timestamps    */

    unsigned int        gso_type;       /* GSO type flags:
                                           SKB_GSO_TCPV4
                                           SKB_GSO_TCPV6
                                           SKB_GSO_UDP_L4
                                           etc.                      */

    u32                 tskey;          /* timestamp key for
                                           SO_TIMESTAMPING            */

    atomic_t            dataref;        /* reference count on the
                                           data buffer. When > 1,
                                           the buffer is shared
                                           between multiple sk_buffs
                                           (clones). Must COW before
                                           modifying data            */

    unsigned int        xdp_frags_size; /* total size of XDP frags   */

    /* ─── Scatter-gather fragment array ────────────────────── */
    /*
     * Each fragment describes a region of a kernel page.
     * This is the scatter-gather mechanism: the packet data
     * is spread across the linear buffer PLUS these page
     * fragments. The NIC's DMA engine reads from all of them.
     *
     * MAX_SKB_FRAGS is typically 17 (65536/PAGE_SIZE + 1).
     */
    skb_frag_t          frags[MAX_SKB_FRAGS];
                                        /* array of page fragments    */

    /*
     * Each skb_frag_t contains:
     *   struct {
     *       struct page   *p;        // the kernel page
     *   } bv_page;
     *   __u32              bv_len;    // length of data in page
     *   __u32              bv_offset; // offset within the page
     */
};
```

### 4.3 The dataref Field

The `dataref` field in `skb_shared_info` is one of the most important fields for
understanding sk_buff cloning:

```c
/*
 * dataref encoding:
 *
 * Bits 0-15:  number of sk_buffs sharing this data buffer
 * Bit  16:    SKB_DATAREF_SHIFT flag (for header clones)
 *
 * When an sk_buff is cloned via skb_clone(), the new sk_buff gets
 * its own metadata (struct sk_buff) but shares the same data buffer.
 * dataref is incremented to track this sharing.
 *
 * Before modifying shared data, code must call skb_unclone() or
 * pskb_expand_head() to get an exclusive copy (copy-on-write).
 */

/* Check if the data buffer is shared */
static inline int skb_shared(const struct sk_buff *skb)
{
    return atomic_read(&skb_shinfo(skb)->dataref) != 1;
}

/* Check if this sk_buff is a clone */
static inline int skb_cloned(const struct sk_buff *skb)
{
    return skb->cloned &&
           (atomic_read(&skb_shinfo(skb)->dataref) & SKB_DATAREF_MASK) != 1;
}
```

### 4.4 Scatter-Gather Fragments (frags[])

When a packet is too large to fit in the linear buffer alone (or when zero-copy
transmission is used), additional data is stored in paged fragments:

```
                  Scatter-Gather Layout
                  ═════════════════════

  struct sk_buff
  ┌──────────────────┐
  │  len = 4500      │    Total packet length
  │  data_len = 4000 │    Bytes in paged frags
  │  head ─────────────────┐
  │  data ─────────────────┼──┐
  │  tail ─────────────────┼──┼──┐
  │  end  ─────────────────┼──┼──┼──┐
  └──────────────────┘     │  │  │  │
                           ▼  ▼  ▼  ▼
  Linear Buffer:     ┌────┬──────┬──┬──────────────────┐
                     │head│ 500B │  │ skb_shared_info   │
                     │room│linear│tl├──────────────────┤
                     │    │ data │rm│ dataref = 1       │
                     │    │      │  │ nr_frags = 3      │
                     │    │      │  │                    │
                     │    │      │  │ frags[0] ──────────┼──► Page A
                     │    │      │  │  .offset = 0       │    [2000 bytes]
                     │    │      │  │  .size   = 2000    │
                     │    │      │  │                    │
                     │    │      │  │ frags[1] ──────────┼──► Page B
                     │    │      │  │  .offset = 512     │    [1500 bytes]
                     │    │      │  │  .size   = 1500    │
                     │    │      │  │                    │
                     │    │      │  │ frags[2] ──────────┼──► Page C
                     │    │      │  │  .offset = 0       │    [500 bytes]
                     │    │      │  │  .size   = 500     │
                     └────┴──────┴──┴──────────────────┘

  Total data = 500 (linear) + 2000 + 1500 + 500 = 4500 = skb->len
  Paged data = 2000 + 1500 + 500                = 4000 = skb->data_len
```

### 4.5 frag_list vs. frags[]

These two mechanisms are often confused. They serve different purposes:

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  frags[] (Scatter-Gather)              frag_list (IP Fragments)      │
│  ════════════════════                  ═════════════════════════      │
│                                                                      │
│  Array of page references              Linked list of sk_buffs       │
│  in skb_shared_info.                   in skb_shared_info.           │
│                                                                      │
│  All fragments are part of             Each sk_buff is a separate    │
│  the SAME packet (logically            IP fragment that needs to     │
│  contiguous data).                     be reassembled.               │
│                                                                      │
│  Used for:                             Used for:                     │
│  - sendfile() zero-copy               - IP defragmentation          │
│  - TSO/GSO                            - GRO (Generic Receive        │
│  - Large receive offload                Offload)                     │
│  - Page pool recycling                                               │
│                                                                      │
│  The NIC's SG-DMA gathers them         The network stack processes   │
│  into a single frame on the wire.      them to reconstruct the       │
│                                        original datagram.            │
│                                                                      │
│  skb->data_len includes the            skb->len of the head skb      │
│  total size of all frags[].            includes all frag_list data.  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.6 GSO Fields

Generic Segmentation Offload (GSO) allows the kernel to defer segmentation of large
packets. The `skb_shared_info` carries the metadata for this:

```c
/*
 * When a socket sends a 64 KB chunk of data, the kernel creates
 * a single large sk_buff rather than many MSS-sized segments.
 *
 * If the NIC supports TSO, it segments in hardware.
 * If not, GSO segments in software just before the driver.
 *
 * Key fields:
 *   gso_size  = MSS (e.g., 1460 for standard Ethernet)
 *   gso_segs  = number of segments (e.g., 64000/1460 ≈ 44)
 *   gso_type  = SKB_GSO_TCPV4, SKB_GSO_TCPV6, SKB_GSO_UDP_L4, etc.
 */

/* Check if this sk_buff needs segmentation */
static inline bool skb_is_gso(const struct sk_buff *skb)
{
    return skb_shinfo(skb)->gso_size;
}

/* Perform software segmentation */
struct sk_buff *skb_gso_segment(struct sk_buff *skb,
                                 netdev_features_t features);
/*
 * Returns a list of MSS-sized sk_buffs linked via skb->next.
 * The original sk_buff is consumed.
 */
```

### 4.7 Accessing skb_shared_info

```c
/*
 * The standard macro to access skb_shared_info:
 */
#define skb_shinfo(SKB)  ((struct skb_shared_info *)(skb_end_pointer(SKB)))

/*
 * Usage examples:
 */

/* Get the number of paged fragments */
int nfrags = skb_shinfo(skb)->nr_frags;

/* Add a new paged fragment */
skb_frag_t *frag = &skb_shinfo(skb)->frags[skb_shinfo(skb)->nr_frags];
skb_frag_set_page(skb, nfrags, page);
skb_frag_size_set(frag, size);
skb_frag_off_set(frag, offset);
skb_shinfo(skb)->nr_frags++;

/* Check if packet is GSO */
if (skb_is_gso(skb)) {
    unsigned int mss = skb_shinfo(skb)->gso_size;
    unsigned int segs = skb_shinfo(skb)->gso_segs;
    pr_info("GSO packet: %u segments of %u bytes\n", segs, mss);
}
```

---

## 5. Header Pointers and Protocol Layers

### 5.1 The Three Header Offsets

Every `sk_buff` carries three header offsets that record where each protocol layer's
header begins within the linear data buffer:

| Field              | Type   | Points To                        |
|--------------------|--------|----------------------------------|
| `mac_header`       | `__u16`| Start of Layer 2 (Ethernet) header |
| `network_header`   | `__u16`| Start of Layer 3 (IP) header     |
| `transport_header` | `__u16`| Start of Layer 4 (TCP/UDP) header|

These are **offsets from `skb->head`**, not absolute pointers. This design was introduced
in kernel 2.6.22 (commit by Arnaldo Carvalho de Melo). Before that, they were direct
pointers (`unsigned char *`), which wasted 8 bytes each on 64-bit systems.

### 5.2 Inner Header Offsets (Encapsulation)

For encapsulated packets (VXLAN, GRE, Geneve, IPsec, etc.), there are additional offsets:

```
| Field                    | Points To                              |
|--------------------------|----------------------------------------|
| `inner_mac_header`       | Inner L2 header (inside the tunnel)    |
| `inner_network_header`   | Inner L3 header (inside the tunnel)    |
| `inner_transport_header` | Inner L4 header (inside the tunnel)    |
```

### 5.3 Complete Header Layout in Memory

```
             Full Header Layout (Ethernet + IPv4 + TCP)
             ══════════════════════════════════════════

head ──────────────►  ┌─────────────────────────────────────────────┐
                      │                                             │
                      │                 Headroom                    │
                      │           (NET_SKB_PAD bytes)               │
                      │                                             │
mac_header ────────►  ├─────────────────────────────────────────────┤
                      │  Dst MAC (6B) │ Src MAC (6B) │ EtherType(2)│  14 bytes
                      │   aa:bb:cc:   │   dd:ee:ff:  │  0x0800     │  Ethernet
                      │   dd:ee:ff    │   aa:bb:cc   │  (IPv4)     │  Header
network_header ────►  ├─────────────────────────────────────────────┤
                      │  Ver│IHL│DSCP │  Total Len   │  Ident      │
                      │  4  │ 5 │  0  │    1500      │  0x1234     │
                      │  Flags│FragOff│  TTL │Proto  │  Hdr Cksum  │  20 bytes
                      │  DF  │  0    │  64  │ TCP(6)│  0xABCD     │  IP Header
                      │  Src IP: 192.168.1.100                     │
                      │  Dst IP: 10.0.0.1                          │
transport_header ──►  ├─────────────────────────────────────────────┤
                      │  Src Port │ Dst Port │  Seq Number         │
                      │   12345   │    80    │  0x00001000         │
                      │  Ack Number          │ Offset│Flags│Window │  20+ bytes
                      │  0x00002000          │  5   │ ACK │ 65535 │  TCP Header
                      │  Checksum │ Urg Ptr  │  [Options if any]   │
                      ├─────────────────────────────────────────────┤
                      │                                             │
                      │              TCP Payload                    │
                      │          (application data)                 │
                      │                                             │
tail ──────────────►  ├─────────────────────────────────────────────┤
                      │              Tailroom                       │
end  ──────────────►  ├─────────────────────────────────────────────┤
                      │           skb_shared_info                   │
                      └─────────────────────────────────────────────┘
```

### 5.4 Encapsulated Packet Layout (VXLAN Example)

```
             VXLAN Encapsulated Packet
             ═════════════════════════

mac_header ────────►  ├─────────────────────────────────────────────┤
                      │         Outer Ethernet Header               │  14 B
network_header ────►  ├─────────────────────────────────────────────┤
                      │         Outer IP Header                     │  20 B
transport_header ──►  ├─────────────────────────────────────────────┤
                      │         Outer UDP Header                    │  8 B
                      ├─────────────────────────────────────────────┤
                      │         VXLAN Header                        │  8 B
inner_mac_header ──►  ├─────────────────────────────────────────────┤
                      │         Inner Ethernet Header               │  14 B
inner_network_hdr ─►  ├─────────────────────────────────────────────┤
                      │         Inner IP Header                     │  20 B
inner_transport ───►  ├─────────────────────────────────────────────┤
                      │         Inner TCP Header                    │  20 B
                      ├─────────────────────────────────────────────┤
                      │         Payload                             │
                      └─────────────────────────────────────────────┘

  skb->encapsulation = 1
  Outer headers:  mac_header, network_header, transport_header
  Inner headers:  inner_mac_header, inner_network_header,
                  inner_transport_header
```

### 5.5 Header Access Macros

```c
/*
 * These macros convert the stored offsets back to usable pointers.
 * They are the ONLY correct way to access header pointers.
 */

/* Layer 2: MAC header */
static inline unsigned char *skb_mac_header(const struct sk_buff *skb)
{
    return skb->head + skb->mac_header;
}

static inline void skb_reset_mac_header(struct sk_buff *skb)
{
    skb->mac_header = skb->data - skb->head;     /* set to current data */
}

static inline void skb_set_mac_header(struct sk_buff *skb, const int offset)
{
    skb->mac_header = (skb->data - skb->head) + offset;
}

/* Layer 3: Network header */
static inline unsigned char *skb_network_header(const struct sk_buff *skb)
{
    return skb->head + skb->network_header;
}

static inline void skb_reset_network_header(struct sk_buff *skb)
{
    skb->network_header = skb->data - skb->head;
}

static inline void skb_set_network_header(struct sk_buff *skb, const int offset)
{
    skb->network_header = (skb->data - skb->head) + offset;
}

/* Layer 4: Transport header */
static inline unsigned char *skb_transport_header(const struct sk_buff *skb)
{
    return skb->head + skb->transport_header;
}

static inline void skb_reset_transport_header(struct sk_buff *skb)
{
    skb->transport_header = skb->data - skb->head;
}

static inline void skb_set_transport_header(struct sk_buff *skb,
                                             const int offset)
{
    skb->transport_header = (skb->data - skb->head) + offset;
}

/*
 * Protocol-specific typed accessors built on top:
 */
static inline struct iphdr *ip_hdr(const struct sk_buff *skb)
{
    return (struct iphdr *)skb_network_header(skb);
}

static inline struct ipv6hdr *ipv6_hdr(const struct sk_buff *skb)
{
    return (struct ipv6hdr *)skb_network_header(skb);
}

static inline struct tcphdr *tcp_hdr(const struct sk_buff *skb)
{
    return (struct tcphdr *)skb_transport_header(skb);
}

static inline struct udphdr *udp_hdr(const struct sk_buff *skb)
{
    return (struct udphdr *)skb_transport_header(skb);
}

static inline struct ethhdr *eth_hdr(const struct sk_buff *skb)
{
    return (struct ethhdr *)skb_mac_header(skb);
}
```

### 5.6 Network Header Length Helpers

```c
/*
 * Compute the length of various headers:
 */

/* Length of the network (IP) header */
static inline u32 skb_network_header_len(const struct sk_buff *skb)
{
    return skb->transport_header - skb->network_header;
}

/* Length from network header to end of transport header */
static inline int skb_transport_offset(const struct sk_buff *skb)
{
    return skb_transport_header(skb) - skb->data;
}

/* Length from network header to start of data */
static inline int skb_network_offset(const struct sk_buff *skb)
{
    return skb_network_header(skb) - skb->data;
}

/*
 * Typical usage in receive path:
 *
 *   struct iphdr *iph = ip_hdr(skb);
 *   int hdr_len = iph->ihl * 4;                  // IP hdr with options
 *   skb_set_transport_header(skb, hdr_len);       // set L4 offset
 *   struct tcphdr *th = tcp_hdr(skb);             // access TCP header
 *   int tcp_hdr_len = th->doff * 4;               // TCP hdr with options
 */
```

### 5.7 Header Offset Diagram During Receive Processing

```
  ┌──────────────────────────────────────────────────────────────────┐
  │ Stage         │ mac_header │ network_header │ transport_header   │
  ├───────────────┼────────────┼────────────────┼────────────────────┤
  │ Driver RX     │ data+0     │ (not set)      │ (not set)          │
  │ eth_type_trans│ data+0     │ data+14        │ (not set)          │
  │ ip_rcv        │ data-14    │ data+0         │ data+20            │
  │ tcp_v4_rcv    │ data-34    │ data-20        │ data+0             │
  │ (payload vis.)│ data-54    │ data-40        │ data-20            │
  └──────────────────────────────────────────────────────────────────┘

  Note: "data+N" means the header is N bytes ahead of current skb->data.
  "data-N" means the header is N bytes behind current skb->data (in headroom).
  The actual stored values are offsets from skb->head, but this table
  illustrates the relative positioning as data moves.
```

---

## 6. The Control Buffer (cb[])

### 6.1 Design and Purpose

The `cb[]` field is a 48-byte array embedded directly in every `sk_buff`. It serves as a
**per-protocol scratch area**: each protocol layer can cast `cb[]` to its own private
structure and store layer-specific metadata without allocating any additional memory.

```c
char cb[48] __aligned(8);   /* 48 bytes, 8-byte aligned */
```

The key design insight is that as a packet traverses the networking stack, each protocol
layer needs its own bookkeeping -- but these needs do **not overlap in time**. The IP
layer's per-packet metadata is no longer needed by the time the TCP layer processes the
packet. Therefore, the same 48 bytes can be reused by overlaying different structures at
each stage.

This avoids:
- Allocating and freeing a separate protocol-specific structure for each packet.
- Adding protocol-specific pointers to `struct sk_buff` (which would bloat the structure).
- Maintaining linked lists of auxiliary structures.

### 6.2 Protocol-Specific cb[] Overlays

#### 6.2.1 TCP Control Buffer (TCP_SKB_CB)

```c
/*
 * TCP's view of cb[] -- defined in include/net/tcp.h
 *
 * This is the most complex user of cb[]; TCP stores critical
 * per-segment metadata here.
 */
struct tcp_skb_cb {
    __u32           seq;        /* Starting sequence number of this
                                   segment. For SYN, this is ISN.
                                   For data, first byte's seqnum    */
    __u32           end_seq;    /* seq + FIN + SYN + datalen.
                                   First sequence number AFTER this
                                   segment. Used for overlap detection */
    union {
        /* In transmit path: */
        struct {
            __u16   tcp_gso_segs;   /* GSO segment count            */
            __u16   tcp_gso_size;   /* GSO segment size              */
        };
    };
    __u8            tcp_flags;  /* TCP flags (SYN, ACK, FIN, RST,
                                   PSH, URG, ECE, CWR). Stored here
                                   rather than re-parsing the header
                                   every time                       */
    __u8            sacked;     /* SACK state flags:
                                   TCPCB_SACKED_ACKED
                                   TCPCB_SACKED_RETRANS
                                   TCPCB_LOST
                                   TCPCB_TAGBITS (mask)             */
    __u8            ip_dsfield; /* IPv4 DSCP+ECN (TOS byte)         */
    __u8            txstamp_ack:1, /* need TX ack timestamp          */
                    eor:1,      /* end of record                     */
                    has_rxtstamp:1, /* has RX timestamp              */
                    unused:5;
    __u32           ack_seq;    /* ACK sequence number from the
                                   received segment (receive path)  */
    union {
        struct {
            /* Transmit path: timestamp info */
            __u32   in_flight;  /* bytes in flight at send time     */
            /* ... additional rate sampling fields ... */
        } tx;
        union {
            struct inet_skb_parm h4;   /* IPv4 params               */
            struct inet6_skb_parm h6;  /* IPv6 params               */
        } header;
    };
};

/*
 * Access macro:
 */
#define TCP_SKB_CB(__skb) ((struct tcp_skb_cb *)&((__skb)->cb[0]))

/*
 * Usage example in TCP receive path:
 */
static void tcp_data_queue(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_skb_cb *tcb = TCP_SKB_CB(skb);

    u32 seq      = tcb->seq;         /* first byte seqnum  */
    u32 end_seq  = tcb->end_seq;     /* last+1 byte seqnum */
    u8  flags    = tcb->tcp_flags;   /* SYN/ACK/FIN/etc.   */

    if (flags & TCPHDR_SYN) {
        /* Handle SYN segment */
    }

    /* Check if segment is in-window */
    if (before(seq, tp->rcv_nxt)) {
        /* Overlaps with already-received data */
    }
    /* ... */
}
```

#### 6.2.2 IP Control Buffer (IPCB)

```c
/*
 * IPv4's view of cb[] -- defined in include/net/ip.h
 */
struct inet_skb_parm {
    int                 iif;        /* incoming interface index      */
    struct ip_options   opt;        /* IP options parsed from header */
    u16                 flags;      /* IPSKB_FORWARDED
                                       IPSKB_XFRM_TUNNEL_SIZE
                                       IPSKB_XFRM_TRANSFORMED
                                       IPSKB_FRAG_COMPLETE
                                       IPSKB_REROUTED
                                       IPSKB_DOREDIRECT
                                       IPSKB_FRAG_PMTU
                                       IPSKB_L3SLAVE              */
    u16                 frag_max_size; /* max fragment size          */
};

#define IPCB(skb)  ((struct inet_skb_parm *)((skb)->cb))

/*
 * Usage in IP forwarding:
 */
static int ip_forward(struct sk_buff *skb)
{
    struct inet_skb_parm *ipcb = IPCB(skb);

    ipcb->flags |= IPSKB_FORWARDED;

    /* Check if options need processing */
    if (unlikely(ipcb->opt.optlen)) {
        if (ip_forward_options(skb))
            goto drop;
    }
    /* ... */
}
```

#### 6.2.3 IPv6 Control Buffer

```c
/*
 * IPv6's view of cb[] -- defined in include/net/ipv6.h
 */
struct inet6_skb_parm {
    int                 iif;        /* incoming interface index      */
    __be16              ra;         /* router alert value            */
    __u16               dst0;       /* offset of Dst Opts (before rthdr) */
    __u16               dst1;       /* offset of Dst Opts (after rthdr)  */
    __u16               lastopt;    /* offset of last option         */
    __u16               nhoff;      /* offset of next header field   */
    __u16               flags;      /* IP6SKB_XFRM_TRANSFORMED, etc. */
    __u16               dsthao;     /* home address option offset    */
    __u16               frag_max_size; /* max fragment size           */
    __s16               srhoff;     /* SRv6 header offset            */
};

#define IP6CB(skb) ((struct inet6_skb_parm *)((skb)->cb))
```

#### 6.2.4 Netfilter Control Buffer

```c
/*
 * Netfilter's view of cb[] -- defined in include/linux/netfilter_bridge.h
 * (used when bridging interacts with netfilter)
 */
struct nf_bridge_info {
    enum {
        BRNF_PROTO_UNCHANGED,
        BRNF_PROTO_8021Q,
        BRNF_PROTO_PPPOE,
    } orig_proto:8;
    u8                  pkt_otherhost:1;
    u8                  in_prerouting:1;
    u8                  bridged_dnat:1;
    __u16               frag_max_size;
    struct net_device   *physindev;
    struct net_device   *physoutdev;
    /* ... */
};
```

### 6.3 cb[] Lifecycle Through the Stack

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  cb[48] usage as packet traverses the receive path:                   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ NIC Driver                                                     │   │
│  │ cb[] = uninitialized / driver-specific                         │   │
│  └────────────────────┬───────────────────────────────────────────┘   │
│                       │                                               │
│                       ▼                                               │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Netfilter PREROUTING                                           │   │
│  │ cb[] = struct nf_bridge_info (if bridging) or left alone       │   │
│  └────────────────────┬───────────────────────────────────────────┘   │
│                       │                                               │
│                       ▼                                               │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ ip_rcv() / ip_rcv_finish()                                     │   │
│  │ cb[] = struct inet_skb_parm (IPCB)                             │   │
│  │   - iif set to input interface                                 │   │
│  │   - IP options parsed into opt                                 │   │
│  │   - flags set (FORWARDED, etc.)                                │   │
│  └────────────────────┬───────────────────────────────────────────┘   │
│                       │                                               │
│                       ▼                                               │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ tcp_v4_rcv()                                                   │   │
│  │ cb[] = struct tcp_skb_cb (TCP_SKB_CB)                          │   │
│  │   - seq, end_seq computed from TCP header                      │   │
│  │   - tcp_flags extracted                                        │   │
│  │   - ack_seq set                                                │   │
│  │   - sacked initialized to 0                                    │   │
│  │   NOTE: IP's IPCB data is OVERWRITTEN here                     │   │
│  │         (but IP processing is complete, so this is safe)       │   │
│  └────────────────────┬───────────────────────────────────────────┘   │
│                       │                                               │
│                       ▼                                               │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ tcp_data_queue() / tcp_rcv_established()                       │   │
│  │ cb[] = still struct tcp_skb_cb                                 │   │
│  │   - SACK state updated in sacked field                         │   │
│  │   - seq/end_seq used for window comparisons                    │   │
│  │   - tcp_flags checked for FIN, RST, etc.                       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 6.4 Why 48 Bytes?

The size of 48 bytes was chosen as a pragmatic trade-off:

- **Large enough** to hold the biggest protocol-specific structure without external
  allocation. `struct tcp_skb_cb` is the primary consumer and is carefully designed to
  fit within this limit.
- **Small enough** to not bloat `struct sk_buff` excessively. Every sk_buff carries
  this 48-byte array whether or not the packet uses TCP.
- **8-byte aligned** (`__aligned(8)`) to allow efficient access to 64-bit fields within
  the overlaid structures.

The size has been increased over the years as protocols needed more metadata. It was 40
bytes in early kernels and was expanded to 48 in later versions. There is continuous
pressure from protocol developers who want more space and from performance engineers who
want to keep sk_buff small.

---

## 7. Metadata Fields Deep Dive

### 7.1 pkt_type -- Packet Addressability

The `pkt_type` field is a 3-bit value that records how the packet was addressed. It is
set by the Ethernet layer (specifically `eth_type_trans()`) based on comparing the
destination MAC address to the receiving interface's MAC address and known multicast
addresses.

```c
/*
 * Defined in include/uapi/linux/if_packet.h:
 */
#define PACKET_HOST         0   /* Addressed to this host's MAC         */
#define PACKET_BROADCAST    1   /* Layer 2 broadcast (ff:ff:ff:ff:ff:ff)*/
#define PACKET_MULTICAST    2   /* Layer 2 multicast (01:xx:xx:xx:xx:xx)*/
#define PACKET_OTHERHOST    3   /* Addressed to a different host (only
                                   received in promiscuous mode)        */
#define PACKET_OUTGOING     4   /* Originated from this host (loopback
                                   or packet socket observation)        */
#define PACKET_LOOPBACK     5   /* Sent to ourselves via loopback       */
#define PACKET_USER         6   /* To userspace (unused in practice)    */
#define PACKET_KERNEL       7   /* To kernel space (unused in practice) */

/*
 * How eth_type_trans() determines pkt_type:
 */
__be16 eth_type_trans(struct sk_buff *skb, struct net_device *dev)
{
    const struct ethhdr *eth = eth_hdr(skb);

    skb->dev = dev;

    if (unlikely(is_multicast_ether_addr(eth->h_dest))) {
        if (ether_addr_equal_64bits(eth->h_dest, dev->broadcast))
            skb->pkt_type = PACKET_BROADCAST;     /* ff:ff:ff:ff:ff:ff */
        else
            skb->pkt_type = PACKET_MULTICAST;     /* 01:xx:xx:xx:xx:xx */
    } else if (unlikely(!ether_addr_equal_64bits(eth->h_dest,
                                                   dev->dev_addr))) {
        skb->pkt_type = PACKET_OTHERHOST;         /* not our MAC       */
    }
    /* else: skb->pkt_type stays PACKET_HOST (0, the default) */

    /* ... determine and return the ethertype ... */
}
```

The `pkt_type` field affects packet delivery:
- `PACKET_OTHERHOST` packets are dropped by `ip_rcv()` unless the interface is in
  promiscuous mode and a packet socket is listening.
- `PACKET_BROADCAST` and `PACKET_MULTICAST` trigger broadcast/multicast delivery logic.
- `PACKET_HOST` is the fast path for unicast packets addressed to this machine.

### 7.2 ip_summed -- Checksum Offload State

The `ip_summed` field is a 2-bit value that communicates checksum status between the
driver, the protocol stack, and the hardware. This is one of the most commonly
misunderstood fields in sk_buff.

```c
/*
 * Checksum states (include/linux/skbuff.h):
 */
#define CHECKSUM_NONE        0   /* No checksum information available.
                                    Software must compute and verify
                                    the checksum.
                                    RX: driver did not verify checksum.
                                    TX: stack must compute checksum.     */

#define CHECKSUM_UNNECESSARY 1   /* Checksum is known to be correct.
                                    RX: hardware verified the checksum
                                    and it passed. No software check
                                    needed.
                                    TX: not used in this direction.      */

#define CHECKSUM_COMPLETE    2   /* Hardware computed the raw checksum
                                    over the entire packet and stored
                                    the result in skb->csum. Software
                                    must verify against the pseudo-header.
                                    RX only: used by some NICs that
                                    compute a raw sum rather than a
                                    protocol-aware check.                */

#define CHECKSUM_PARTIAL     3   /* Partial checksum already computed.
                                    TX: the transport layer has set up
                                    csum_start and csum_offset. The NIC
                                    hardware must compute the checksum
                                    from csum_start to end of packet
                                    and store at csum_offset.
                                    This is the TX offload mechanism.    */
```

State machine on the receive path:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Receive Checksum Flow                             │
│                                                                     │
│  NIC Hardware                                                       │
│  ┌───────────────────────────────────────┐                          │
│  │ Can verify L4 checksum?               │                          │
│  │                                       │                          │
│  │  YES ──► ip_summed = CHECKSUM_        │                          │
│  │          UNNECESSARY                  │                          │
│  │          (checksum known good)        │                          │
│  │                                       │                          │
│  │  PARTIAL ──► ip_summed = CHECKSUM_    │                          │
│  │              COMPLETE                 │                          │
│  │              skb->csum = raw_sum      │                          │
│  │                                       │                          │
│  │  NO ──► ip_summed = CHECKSUM_NONE     │                          │
│  └───────────────┬───────────────────────┘                          │
│                  │                                                   │
│                  ▼                                                   │
│  IP Layer (ip_rcv)                                                  │
│  ┌───────────────────────────────────────┐                          │
│  │ IP header checksum always verified    │                          │
│  │ in software (cheap: 20 bytes)         │                          │
│  └───────────────┬───────────────────────┘                          │
│                  │                                                   │
│                  ▼                                                   │
│  TCP Layer (tcp_v4_rcv)                                             │
│  ┌───────────────────────────────────────┐                          │
│  │ ip_summed == UNNECESSARY?             │                          │
│  │   YES ──► skip checksum verify ───────┼──► Fast path             │
│  │                                       │                          │
│  │ ip_summed == COMPLETE?                │                          │
│  │   YES ──► add pseudo-header to csum,  │                          │
│  │           verify result is 0xFFFF ────┼──► Accept or drop        │
│  │                                       │                          │
│  │ ip_summed == NONE?                    │                          │
│  │   YES ──► compute full checksum in    │                          │
│  │           software (expensive) ───────┼──► Accept or drop        │
│  └───────────────────────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

State machine on the transmit path:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Transmit Checksum Flow                            │
│                                                                     │
│  TCP/UDP Layer                                                      │
│  ┌───────────────────────────────────────┐                          │
│  │ NIC supports TX checksum offload?     │                          │
│  │                                       │                          │
│  │  YES ──► ip_summed = CHECKSUM_PARTIAL │                          │
│  │          csum_start = offset to L4 hdr│                          │
│  │          csum_offset = offset within  │                          │
│  │          L4 header to store checksum  │                          │
│  │          (16 for TCP, 6 for UDP)      │                          │
│  │          Pseudo-header checksum placed│                          │
│  │          in the checksum field.       │                          │
│  │                                       │                          │
│  │  NO ──►  ip_summed = CHECKSUM_NONE    │                          │
│  │          Full checksum computed in    │                          │
│  │          software and placed in header│                          │
│  └───────────────┬───────────────────────┘                          │
│                  │                                                   │
│                  ▼                                                   │
│  NIC Driver / Hardware                                              │
│  ┌───────────────────────────────────────┐                          │
│  │ CHECKSUM_PARTIAL?                     │                          │
│  │   YES ──► DMA packet; hardware reads  │                          │
│  │           csum_start/csum_offset from │                          │
│  │           descriptor and computes     │                          │
│  │           remaining checksum on-chip  │                          │
│  │                                       │                          │
│  │ CHECKSUM_NONE?                        │                          │
│  │   YES ──► DMA packet as-is; checksum  │                          │
│  │           already in the header       │                          │
│  └───────────────────────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Protocol Field and Byte Order

```c
/*
 * skb->protocol identifies the Layer 3 protocol.
 * It is stored in NETWORK BYTE ORDER (big-endian).
 *
 * Set by eth_type_trans() based on the EtherType field.
 */
skb->protocol = htons(ETH_P_IP);     /* 0x0800 */
skb->protocol = htons(ETH_P_IPV6);   /* 0x86DD */
skb->protocol = htons(ETH_P_ARP);    /* 0x0806 */
skb->protocol = htons(ETH_P_8021Q);  /* 0x8100 (VLAN) */

/*
 * Common EtherType values (include/uapi/linux/if_ether.h):
 *
 *  ┌──────────────┬────────┬──────────────────────────────────┐
 *  │ Constant     │ Value  │ Description                      │
 *  ├──────────────┼────────┼──────────────────────────────────┤
 *  │ ETH_P_IP     │ 0x0800 │ IPv4                             │
 *  │ ETH_P_ARP    │ 0x0806 │ ARP                              │
 *  │ ETH_P_8021Q  │ 0x8100 │ 802.1Q VLAN                      │
 *  │ ETH_P_IPV6   │ 0x86DD │ IPv6                             │
 *  │ ETH_P_8021AD │ 0x88A8 │ 802.1ad QinQ                     │
 *  │ ETH_P_MPLS_UC│ 0x8847 │ MPLS Unicast                     │
 *  │ ETH_P_LLDP   │ 0x88CC │ LLDP                             │
 *  │ ETH_P_ALL    │ 0x0003 │ Match all protocols (raw socket) │
 *  └──────────────┴────────┴──────────────────────────────────┘
 *
 * Comparison must use network byte order:
 */
if (skb->protocol == htons(ETH_P_IP)) {
    /* Process IPv4 packet */
}
```

### 7.4 Priority and QoS Mapping

```c
/*
 * skb->priority controls queuing and scheduling decisions.
 *
 * Sources of priority:
 *   1. SO_PRIORITY socket option (set by application)
 *   2. IPv4 TOS field (mapped automatically)
 *   3. VLAN PCP bits
 *   4. tc(8) classifiers and actions
 *
 * Priority values 0-15 map to Linux traffic classes (TC_PRIO_*):
 *
 *  ┌────────┬────────────────────┬────────────────────────────┐
 *  │ Value  │ Constant           │ Description                │
 *  ├────────┼────────────────────┼────────────────────────────┤
 *  │   0    │ TC_PRIO_BESTEFFORT │ Best effort (default)      │
 *  │   1    │ TC_PRIO_FILLER     │ Filler / background        │
 *  │   2    │ TC_PRIO_BULK       │ Bulk data transfer         │
 *  │   4    │ TC_PRIO_INTERACTIVE│ Interactive (SSH, etc.)     │
 *  │   6    │ TC_PRIO_INTERACTIVE│ Interactive bulk            │
 *  │        │ _BULK              │                            │
 *  │   7    │ TC_PRIO_CONTROL    │ Network control            │
 *  └────────┴────────────────────┴────────────────────────────┘
 *
 * The DSCP-to-priority mapping for IPv4:
 */
static inline __u8 ip_tos2prio[16] = {
    TC_PRIO_BESTEFFORT,       /* TOS 0x00 */
    ECN_OR_COST(FILLER),      /* TOS 0x02 */
    TC_PRIO_BESTEFFORT,       /* TOS 0x04 */
    ECN_OR_COST(BESTEFFORT),  /* TOS 0x06 */
    TC_PRIO_BULK,             /* TOS 0x08 */
    ECN_OR_COST(BULK),        /* TOS 0x0A */
    TC_PRIO_BULK,             /* TOS 0x0C */
    ECN_OR_COST(BULK),        /* TOS 0x0E */
    TC_PRIO_INTERACTIVE,      /* TOS 0x10 */
    /* ... remaining entries ... */
};

/*
 * How priority flows to the queuing discipline:
 *
 *   Application sets SO_PRIORITY=6
 *       │
 *       ▼
 *   skb->priority = 6
 *       │
 *       ▼
 *   pfifo_fast qdisc maps priority to one of 3 bands:
 *     Band 0 (highest): priorities 0-3
 *     Band 1:           priorities 4-5
 *     Band 2 (lowest):  priorities 6-7
 *
 *   (But with mqprio or other qdiscs, the mapping is configurable)
 */
```

### 7.5 Mark Field (Netfilter/iptables)

```c
/*
 * skb->mark is a generic 32-bit tag that travels with the packet.
 * It is NOT transmitted on the wire; it is purely kernel-internal.
 *
 * Primary users:
 *   - iptables/nftables: -j MARK --set-mark VALUE
 *   - Policy routing:    ip rule fwmark VALUE table TABLE
 *   - Traffic shaping:   tc filter fw flowid X:Y
 *   - Connection tracking: CONNMARK save/restore
 *   - SO_MARK socket option
 *
 * Example: route traffic from a specific application through a VPN:
 *
 *   # Mark packets from UID 1000
 *   iptables -t mangle -A OUTPUT -m owner --uid-owner 1000 \
 *       -j MARK --set-mark 0x100
 *
 *   # Route marked packets through table 100
 *   ip rule add fwmark 0x100 table 100
 *   ip route add default via 10.8.0.1 table 100
 *
 *   # In kernel: the packet's skb->mark is 0x100, and the
 *   #            routing subsystem checks this via fib_rule_match()
 */

/*
 * Setting mark from a socket (SO_MARK, requires CAP_NET_ADMIN):
 */
int mark = 0x100;
setsockopt(fd, SOL_SOCKET, SO_MARK, &mark, sizeof(mark));
/* All packets from this socket will have skb->mark = 0x100 */
```

### 7.6 Timestamp (tstamp)

```c
/*
 * skb->tstamp records the packet's timestamp as a ktime_t
 * (nanosecond-resolution monotonic clock value).
 *
 * When it is set depends on the path:
 *
 * Receive path:
 *   - If the NIC supports hardware timestamping, the driver sets
 *     tstamp from the hardware clock (via skb_hwtstamps()).
 *   - Otherwise, netif_receive_skb() sets it via net_timestamp_set()
 *     if enabled via sysctl net.core.netdev_tstamp_prequeue.
 *   - Used by SO_TIMESTAMP, SO_TIMESTAMPNS, SO_TIMESTAMPING socket
 *     options to deliver timestamps to userspace.
 *
 * Transmit path:
 *   - If SO_TXTIME is used (EDT - Earliest Departure Time), tstamp
 *     holds the intended transmission time.
 *   - Used by fq (Fair Queueing) qdisc for pacing.
 *   - skb->tstamp is repurposed: on TX it is EDT, on RX it is the
 *     arrival time. The stack must be careful about this duality.
 *
 * Internal format:
 *   ktime_t is a 64-bit signed integer of nanoseconds since boot.
 */

/* Reading the timestamp */
ktime_t arrival = skb->tstamp;
u64 ns = ktime_to_ns(arrival);

/* Setting a TX departure time (EDT) */
skb->tstamp = ktime_add_ns(ktime_get(), delay_ns);

/*
 * Hardware timestamps live in skb_shared_info->hwtstamps
 * (a separate field from skb->tstamp):
 */
struct skb_shared_hwtstamps {
    union {
        ktime_t hwtstamp;      /* hardware timestamp value  */
        void    *netdev_data;  /* driver-specific data      */
    };
};
```

### 7.7 Hash and Receive Steering

```c
/*
 * skb->hash is a 32-bit flow hash used for:
 *   - RPS (Receive Packet Steering): distributing softirq
 *     processing across CPUs
 *   - RFS (Receive Flow Steering): steering packets to the
 *     CPU where the application is running
 *   - Multiqueue device TX queue selection
 *
 * The hash can be:
 *   1. Computed by the NIC hardware (RSS - Receive Side Scaling)
 *      and stored by the driver: skb->hash = rss_hash, sw_hash=0, l4_hash=1
 *   2. Computed in software by skb_get_hash():
 *      uses a jhash over (src_ip, dst_ip, src_port, dst_port, proto)
 *      and sets sw_hash=1, l4_hash=1
 *
 * Associated flags:
 *   skb->l4_hash:  1 if hash includes L4 (port) information
 *   skb->sw_hash:  1 if hash was computed in software
 *
 * Flow dissection:
 *   skb_get_hash() calls flow_dissector to extract the flow key
 *   (IP addresses, ports, protocol) and then hashes it.
 */

/* How RPS uses the hash (simplified from net/core/dev.c): */
static int get_rps_cpu(struct net_device *dev,
                       struct sk_buff *skb,
                       struct rps_dev_flow **rflowp)
{
    u32 hash = skb_get_hash(skb);          /* get or compute hash   */
    u32 cpu_index = hash % num_online_cpus(); /* select target CPU  */
    /* ... RFS logic to prefer the CPU running the application ... */
    return cpu_index;
}
```

### 7.8 VLAN Fields

```c
/*
 * VLAN tag handling in sk_buff:
 *
 * When the NIC strips a VLAN tag (hardware VLAN offload),
 * the driver stores the tag in the sk_buff rather than leaving
 * it in the packet data:
 *
 *   skb->vlan_proto   = htons(ETH_P_8021Q)  or  htons(ETH_P_8021AD)
 *   skb->vlan_tci     = the 16-bit TCI field:
 *                        ┌───────┬─────┬──────────────┐
 *                        │  PCP  │ DEI │     VID      │
 *                        │ 3 bit │1 bit│   12 bit     │
 *                        └───────┴─────┴──────────────┘
 *   skb->vlan_present = 1  (indicates the above fields are valid)
 *
 * If the NIC does NOT strip the tag, the VLAN header remains
 * inline in the packet data between the Ethernet header and
 * the IP header.
 *
 * Manipulation functions:
 */

/* Add a VLAN tag to an sk_buff (does not modify packet data) */
static inline void __vlan_hwaccel_put_tag(struct sk_buff *skb,
                                           __be16 vlan_proto,
                                           u16 vlan_tci)
{
    skb->vlan_proto   = vlan_proto;
    skb->vlan_tci     = vlan_tci;
    skb->vlan_present = 1;
}

/* Check if a VLAN tag is present */
static inline bool skb_vlan_tag_present(const struct sk_buff *skb)
{
    return skb->vlan_present;
}

/* Get the VLAN TCI */
static inline u16 skb_vlan_tag_get(const struct sk_buff *skb)
{
    return skb->vlan_tci;
}

/* Get just the VLAN ID (lower 12 bits) */
static inline u16 skb_vlan_tag_get_id(const struct sk_buff *skb)
{
    return skb->vlan_tci & VLAN_VID_MASK;    /* & 0x0FFF */
}

/* Get the priority (PCP, upper 3 bits of TCI) */
static inline u16 skb_vlan_tag_get_prio(const struct sk_buff *skb)
{
    return (skb->vlan_tci & VLAN_PRIO_MASK) >> VLAN_PRIO_SHIFT;
}
```

### 7.9 Cloning and Reference Count Flags

```c
/*
 * Several bit fields control sk_buff sharing and cloning:
 *
 * cloned (1 bit):
 *   Set to 1 when this sk_buff's data buffer may be shared with
 *   another sk_buff (created via skb_clone()). When cloned=1,
 *   the code must check skb_shared_info->dataref before modifying
 *   the data buffer.
 *
 * fclone (2 bits):
 *   Fast-clone status. The kernel can pre-allocate pairs of sk_buffs
 *   from a special slab cache ("skbuff_fclone_cache") to avoid a
 *   second kmalloc when cloning is expected (common for TCP).
 *
 *   SKB_FCLONE_UNAVAILABLE (0): Not from fclone cache, or already used.
 *   SKB_FCLONE_ORIG        (1): Original sk_buff from fclone pair.
 *   SKB_FCLONE_CLONE       (2): The clone partner of an fclone pair.
 *
 * users (refcount_t):
 *   Reference count on the sk_buff DESCRIPTOR (not the data buffer).
 *   Incremented by skb_get(), decremented by kfree_skb() / consume_skb().
 *   When it reaches 0, the sk_buff is freed.
 *
 * dataref (in skb_shared_info):
 *   Reference count on the DATA BUFFER.
 *   Incremented when the buffer is shared via skb_clone().
 *   The buffer is freed only when dataref reaches 0.
 */

/*
 * Cloning diagram:
 *
 *   skb_clone(original, GFP_ATOMIC) creates:
 *
 *   Original sk_buff              Clone sk_buff
 *   ┌──────────────┐             ┌──────────────┐
 *   │ next, prev   │             │ next, prev   │
 *   │ sk, dev      │             │ sk, dev      │  (copied)
 *   │ cloned = 1   │             │ cloned = 1   │
 *   │ head ────────┼──┐   ┌─────┼── head       │
 *   │ data ────────┼──┼───┼─────┼── data       │
 *   │ tail, end    │  │   │     │ tail, end    │  (same offsets)
 *   │ users = 1    │  │   │     │ users = 1    │
 *   └──────────────┘  │   │     └──────────────┘
 *                     │   │
 *                     ▼   ▼
 *            ┌──────────────────────────┐
 *            │    Shared Data Buffer    │
 *            │                          │
 *            │  ┌────────────────────┐  │
 *            │  │  skb_shared_info   │  │
 *            │  │  dataref = 2      │  │  ◄── two sk_buffs share
 *            │  └────────────────────┘  │      this buffer
 *            └──────────────────────────┘
 *
 *   The clone has its own metadata but shares the data buffer.
 *   Either sk_buff can modify its own pointers (data, tail)
 *   independently, but neither can modify the buffer contents
 *   without first calling pskb_expand_head() to get a private copy.
 */
```

### 7.10 Queue Mapping and Multiqueue

```c
/*
 * skb->queue_mapping selects which hardware TX queue to use
 * on multiqueue NICs.
 *
 * Set by:
 *   - netdev_pick_tx() during transmit
 *   - XPS (Transmit Packet Steering) configuration
 *   - Traffic control (tc) classifiers
 *   - Driver-specific logic
 *
 * Valid range: 0 to dev->num_tx_queues - 1
 *
 * The xmit_more flag (1 bit) is a batching hint:
 *   When xmit_more=1, the driver knows that more packets will
 *   follow immediately for the same queue. The driver can defer
 *   the doorbell write (PCI MMIO) to batch multiple packets,
 *   reducing PCI overhead.
 */
static inline void skb_set_queue_mapping(struct sk_buff *skb,
                                          u16 queue_mapping)
{
    skb->queue_mapping = queue_mapping;
}

static inline u16 skb_get_queue_mapping(const struct sk_buff *skb)
{
    return skb->queue_mapping;
}
```

### 7.11 The ooo_okay Flag

```c
/*
 * skb->ooo_okay (1 bit): "Out-of-order is okay"
 *
 * This flag is used in the TCP transmit path. When set, it tells
 * the queuing discipline and NIC driver that this packet can be
 * transmitted out of order relative to other packets from the
 * same flow without causing issues.
 *
 * This is relevant for multiqueue NICs where packets from the
 * same flow might be spread across queues. If ooo_okay=0, the
 * stack tries harder to keep packets in order.
 *
 * Set by TCP when it detects that the connection can tolerate
 * reordering (e.g., when using RACK loss detection).
 */
```

---

## 8. Size and Memory Overhead

### 8.1 sizeof(struct sk_buff)

On a 64-bit x86 system with a typical kernel configuration:

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Component                           │  Approximate Size             │
│  ════════════════════════════════════ │  ════════════════             │
│                                      │                               │
│  struct sk_buff                      │  ~232 bytes (v6.x)            │
│    (varies with CONFIG options:      │                               │
│     +8 if CONFIG_NF_CONNTRACK        │  Often 240-256 bytes with     │
│     +8 if CONFIG_NET_SCHED           │  common configurations        │
│     +8 if CONFIG_SKB_EXTENSIONS      │                               │
│     +8 if CONFIG_NET_CLS_ACT         │                               │
│     alignment padding)               │                               │
│                                      │                               │
│  struct skb_shared_info              │  ~320 bytes                   │
│    (sizeof base struct               │                               │
│     + MAX_SKB_FRAGS * sizeof(        │  17 * 20 = 340 for frags     │
│       skb_frag_t))                   │  alone on some configs)       │
│                                      │                               │
│  Linear data buffer                  │  varies:                      │
│    - Small packet (TCP ACK)          │  ~256 bytes (MTU + headroom)  │
│    - Standard Ethernet MTU           │  ~1792 bytes (1500 + 256 +    │
│                                      │   headroom + alignment)       │
│    - Jumbo frame (9000 MTU)          │  ~9728 bytes                  │
│                                      │                               │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.2 Memory Layout of a Complete Packet

```
                Complete Memory Layout for One Packet
                ═════════════════════════════════════

  Heap Allocation #1: struct sk_buff (from kmem_cache "skbuff_head_cache")
  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │    struct sk_buff                                                │
  │    ~232 bytes                                                    │
  │                                                                  │
  │    ┌──────────────────────────────────────────────────────────┐  │
  │    │  next, prev, sk, dev, tstamp, _skb_refdst, destructor   │  │
  │    │  _nfct, cb[48], len, data_len, mac_len, hdr_len         │  │
  │    │  queue_mapping, cloned, nohdr, fclone, pkt_type          │  │
  │    │  ip_summed, priority, protocol, vlan_tci                 │  │
  │    │  transport_header, network_header, mac_header            │  │
  │    │  hash, mark, secmark                                     │  │
  │    │  head ─┐  data ─┐  tail (offset)  end (offset)          │  │
  │    │        │        │  truesize, users                       │  │
  │    └────────┼────────┼────────────────────────────────────────┘  │
  │             │        │                                           │
  └─────────────┼────────┼───────────────────────────────────────────┘
                │        │
                │        │
  Heap Allocation #2: Data buffer (from kmalloc / page allocator)
  ┌─────────────┼────────┼───────────────────────────────────────────┐
  │             ▼        ▼                                           │
  │  ┌──────────┬────────┬───────────────────────┬─────────────┐    │
  │  │ Headroom │ Packet │      Tailroom         │skb_shared_  │    │
  │  │          │  Data  │                       │info (~320B) │    │
  │  │(64-256B) │(varies)│  (remaining space)    │             │    │
  │  └──────────┴────────┴───────────────────────┴─────────────┘    │
  │  ▲                                            ▲                  │
  │  head                                         end                │
  │                                                                  │
  │  Total allocation = headroom + MTU + tailroom + sizeof(shinfo)   │
  │  Typical for 1500 MTU: ~2048 bytes (power-of-2 from kmalloc)    │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

  Optional: Paged fragments (zero or more kernel pages)
  ┌──────────────────────────────────────────────────────────────────┐
  │  Page A (4096 bytes)  ──► referenced by shinfo->frags[0]        │
  │  Page B (4096 bytes)  ──► referenced by shinfo->frags[1]        │
  │  ...                                                             │
  └──────────────────────────────────────────────────────────────────┘
```

### 8.3 Total Memory Per Packet

```c
/*
 * skb->truesize tracks the total memory charged to the owning socket.
 * This is used for socket buffer accounting (sk->sk_wmem_alloc,
 * sk->sk_rmem_alloc) and flow control (tcp_mem, udp_mem).
 *
 * truesize = sizeof(struct sk_buff)          (~232 bytes)
 *          + data buffer size                 (end - head + shinfo)
 *          + paged fragment sizes             (sum of all frag sizes)
 *
 * For a typical TCP segment on Ethernet:
 *
 *   truesize ≈ 232 + 2048 = 2280 bytes
 *
 * But the actual payload might only be 1448 bytes (MSS).
 * The "waste" is headroom, tailroom, shinfo overhead, and sk_buff
 * metadata. This overhead ratio (~57%) is the price of zero-copy
 * efficiency and O(1) header manipulation.
 *
 * For a tiny TCP ACK (40 bytes on the wire):
 *
 *   truesize ≈ 232 + 256 = 488 bytes
 *
 * The overhead ratio for small packets is much worse (~92%).
 * This is why the kernel uses TCP ACK compression and GRO
 * (Generic Receive Offload) to reduce the number of sk_buffs.
 */

/*
 * truesize is computed at allocation:
 */
struct sk_buff *__alloc_skb(unsigned int size,
                             gfp_t gfp_mask,
                             int flags,
                             int node)
{
    struct sk_buff *skb;
    unsigned int osize;

    /* Allocate the sk_buff descriptor */
    skb = kmem_cache_alloc(skbuff_head_cache, gfp_mask);

    /* Round up the data buffer size */
    size = SKB_DATA_ALIGN(size);              /* align to cache line   */
    size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info)); /* room for shinfo */

    /* Allocate the data buffer */
    osize = kmalloc_size_roundup(size);       /* next kmalloc bucket   */
    data = kmalloc_reserve(osize, gfp_mask, node, &pfmemalloc);

    /* Set up the four pointers */
    skb->head = data;
    skb->data = data;
    skb_reset_tail_pointer(skb);              /* tail = data           */
    skb->end  = skb->tail + (osize - SKB_DATA_ALIGN(sizeof(struct skb_shared_info)));

    /* Set truesize */
    skb->truesize = SKB_TRUESIZE(osize);
    /* where SKB_TRUESIZE(X) = sizeof(struct sk_buff) + X */

    /* Initialize skb_shared_info */
    shinfo = skb_shinfo(skb);
    memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
    atomic_set(&shinfo->dataref, 1);

    return skb;
}
```

### 8.4 Memory Pool and Slab Cache Architecture

```
                    sk_buff Allocation Caches
                    ═════════════════════════

  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  skbuff_head_cache (kmem_cache)                                 │
  │  ══════════════════════════════                                  │
  │  Slab cache for struct sk_buff allocations.                     │
  │  Object size: sizeof(struct sk_buff) ≈ 232 bytes               │
  │  Allocated via: kmem_cache_alloc(skbuff_head_cache, flags)      │
  │  Freed via:     kmem_cache_free(skbuff_head_cache, skb)         │
  │                                                                 │
  │  This is a dedicated slab cache (not generic kmalloc)           │
  │  because sk_buffs are allocated/freed at extremely high         │
  │  rates and benefit from per-CPU caching.                        │
  │                                                                 │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  skbuff_fclone_cache (kmem_cache)                               │
  │  ═══════════════════════════════                                 │
  │  Slab cache for "fast clone" pairs.                             │
  │  Object size: 2 * sizeof(struct sk_buff) + sizeof(refcount_t)   │
  │  ≈ 472 bytes                                                    │
  │                                                                 │
  │  When a clone is expected (e.g., TCP retransmit queue),         │
  │  alloc_skb_fclone() allocates a pair. Cloning the first         │
  │  sk_buff reuses the pre-allocated partner instead of doing      │
  │  a fresh kmem_cache_alloc().                                    │
  │                                                                 │
  │  Layout in memory:                                              │
  │  ┌────────────────────┬────────────────────┬────────────┐       │
  │  │  sk_buff (original)│  sk_buff (clone)   │ fclone_ref │       │
  │  │  fclone=ORIG       │  fclone=CLONE      │ refcount   │       │
  │  └────────────────────┴────────────────────┴────────────┘       │
  │                                                                 │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  Data buffer allocation                                         │
  │  ══════════════════════                                          │
  │  The data buffer is allocated separately from the sk_buff:      │
  │                                                                 │
  │  Small buffers (≤ PAGE_SIZE):                                   │
  │    Allocated via kmalloc() from generic slab caches.            │
  │    Typical sizes: 256, 512, 1024, 2048, 4096 bytes.             │
  │    kmalloc rounds up to the next power-of-2 bucket.             │
  │                                                                 │
  │  Large buffers (> PAGE_SIZE, e.g., jumbo frames):               │
  │    Allocated via the page allocator (alloc_pages()).             │
  │    skb->head_frag = 1 indicates a page-based allocation.        │
  │                                                                 │
  │  NAPI / driver pools:                                           │
  │    Many drivers use napi_alloc_skb() or netdev_alloc_skb()      │
  │    which use per-CPU page fragment caches for efficiency.        │
  │    The page_frag allocator carves small buffers from a          │
  │    larger page without individual kmalloc overhead.             │
  │                                                                 │
  │  Page Pool (since kernel 5.x):                                  │
  │    Drivers can use the page_pool API for high-performance       │
  │    recycling of pages used for paged fragments.                 │
  │    skb->pp_recycle = 1 indicates page pool recycling.           │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

### 8.5 Memory Overhead Comparison Table

```
┌────────────────────────────┬────────────┬─────────────┬──────────────┐
│ Packet Type                │ Wire Bytes │ Total Memory│ Overhead     │
│                            │            │ (truesize)  │ Ratio        │
├────────────────────────────┼────────────┼─────────────┼──────────────┤
│ TCP ACK (no data)          │     54     │   ~768      │  ~14x        │
│ TCP small (100B payload)   │    154     │   ~768      │  ~5x         │
│ TCP full MSS (1448B)       │   1502     │  ~2560      │  ~1.7x       │
│ UDP DNS query (50B)        │     92     │   ~768      │  ~8x         │
│ Jumbo frame (9000B MTU)    │   9014     │  ~10240     │  ~1.1x       │
│ TSO/GSO super-packet (64K) │  65536     │  ~66816     │  ~1.02x      │
│ (uses paged fragments)     │            │             │              │
└────────────────────────────┴────────────┴─────────────┴──────────────┘

Notes:
- "Wire Bytes" = Ethernet header + IP header + L4 header + payload
- "Total Memory" = sizeof(sk_buff) + data buffer (rounded to kmalloc bucket)
  + skb_shared_info overhead
- "Overhead Ratio" = Total Memory / Wire Bytes
- The overhead is worst for small packets and nearly negligible for large ones.
- GSO/TSO amortizes the sk_buff overhead across many segments.
```

### 8.6 Reducing Per-Packet Overhead

The kernel employs several strategies to reduce per-packet memory overhead:

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  Strategy                │ Mechanism                                  │
│  ════════════════════════│════════════════════════════════════════     │
│                          │                                            │
│  GRO (Generic Receive    │ Coalesces multiple small rx packets into   │
│  Offload)                │ a single large sk_buff, reducing the       │
│                          │ number of sk_buffs created.                │
│                          │                                            │
│  GSO/TSO (Segmentation   │ Creates one large sk_buff for many         │
│  Offload)                │ segments. Segmentation deferred to NIC     │
│                          │ or done lazily in software.                │
│                          │                                            │
│  TCP ACK compression     │ Replaces queued ACKs with the latest one,  │
│                          │ dropping intermediate pure-ACK sk_buffs.   │
│                          │                                            │
│  Bulk alloc / free       │ napi_alloc_skb() and napi_consume_skb()    │
│                          │ batch allocations per NAPI poll cycle,      │
│                          │ amortizing slab cache lock overhead.       │
│                          │                                            │
│  Page fragment recycling │ netdev_alloc_frag() carves small buffers   │
│                          │ from a compound page, reducing page alloc  │
│                          │ pressure.                                  │
│                          │                                            │
│  Fast clones (fclone)    │ Pre-allocated clone pairs avoid kmalloc    │
│                          │ for the common TCP clone-for-retransmit    │
│                          │ pattern.                                   │
│                          │                                            │
│  Page pool               │ Recycling framework for DMA-mapped pages,  │
│                          │ avoiding repeated DMA map/unmap cycles.    │
│                          │                                            │
│  XDP (eXpress Data Path) │ Processes packets at the driver level      │
│                          │ before sk_buff allocation. For forwarding  │
│                          │ or dropping, no sk_buff is created at all. │
│                          │                                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.7 Allocation and Deallocation Hot Path

```c
/*
 * Fast path allocation for receive (drivers):
 */
static inline struct sk_buff *netdev_alloc_skb(struct net_device *dev,
                                                unsigned int length)
{
    /*
     * Allocates an sk_buff with 'length' bytes of data space.
     * Uses a per-CPU page fragment cache for the data buffer
     * to minimize allocator overhead.
     *
     * Typical driver usage:
     *
     *   skb = netdev_alloc_skb_ip_align(dev, pkt_len);
     *   // This calls netdev_alloc_skb(dev, pkt_len + NET_IP_ALIGN)
     *   // and then skb_reserve(skb, NET_IP_ALIGN) to align IP header
     *   // to a 4-byte boundary for efficient access.
     */
    return __netdev_alloc_skb(dev, length, GFP_ATOMIC);
}

/*
 * NAPI-optimized allocation (preferred in modern drivers):
 */
static inline struct sk_buff *napi_alloc_skb(struct napi_struct *napi,
                                              unsigned int length)
{
    /*
     * Like netdev_alloc_skb() but uses NAPI-local page fragment
     * cache. This is faster because NAPI guarantees single-threaded
     * execution, so no locking is needed.
     */
    return __napi_alloc_skb(napi, length, GFP_ATOMIC);
}

/*
 * Deallocation:
 *
 *   kfree_skb(skb)    - decrements users; frees if it reaches 0.
 *                        Counts as a "drop" in drop monitoring.
 *
 *   consume_skb(skb)  - same, but counts as "consumed" (normal completion).
 *
 *   dev_kfree_skb(skb) - wrapper for use in driver context.
 *
 *   napi_consume_skb() - batched free, deferred to end of NAPI poll.
 *
 * The actual free path:
 *   1. Call skb->destructor(skb) if set (releases socket wmem/rmem).
 *   2. Release dst_entry (via skb_dst_drop()).
 *   3. Release nf_conntrack entry.
 *   4. Release extensions (skb_ext_put()).
 *   5. Release paged fragments (put_page() on each frag).
 *   6. Release data buffer (kfree(skb->head) or page_frag_free()).
 *   7. Free the sk_buff descriptor (kmem_cache_free()).
 */
```

### 8.8 Memory Accounting in the Socket Layer

```c
/*
 * The kernel limits how much memory each socket (and each protocol
 * globally) can consume via sk_buff allocations:
 *
 * Per-socket limits:
 *   sk->sk_sndbuf    - max send buffer (SO_SNDBUF)
 *   sk->sk_rcvbuf    - max receive buffer (SO_RCVBUF)
 *   sk->sk_wmem_alloc - current TX memory usage
 *   sk->sk_rmem_alloc - current RX memory usage
 *
 * The skb->truesize field is what gets charged:
 */

/* When an sk_buff is queued for transmission: */
static inline void skb_set_owner_w(struct sk_buff *skb, struct sock *sk)
{
    skb->sk = sk;                        /* remember owning socket     */
    skb->destructor = sock_wfree;        /* callback to release wmem   */
    refcount_add(skb->truesize, &sk->sk_wmem_alloc); /* charge memory */
}

/* The destructor releases the charge when the sk_buff is freed: */
void sock_wfree(struct sk_buff *skb)
{
    struct sock *sk = skb->sk;

    /* Release the memory charge */
    if (refcount_sub_and_test(skb->truesize, &sk->sk_wmem_alloc)) {
        /* If socket is waiting for more wmem, wake it up */
        sk->sk_write_space(sk);
    }
    sock_put(sk);   /* release socket reference */
}

/*
 * Flow control interaction:
 *
 *   When sk->sk_wmem_alloc >= sk->sk_sndbuf, the socket is
 *   "write-blocked". send()/write() will either block (blocking I/O)
 *   or return EAGAIN (non-blocking I/O).
 *
 *   When sk_buffs are freed after successful transmission, wmem
 *   decreases and the socket becomes writable again, waking any
 *   blocked writers and generating EPOLLOUT events.
 *
 *   This is how TCP flow control interacts with the sk_buff
 *   memory management: the amount of data "in flight" is bounded
 *   by both the TCP window AND the socket buffer limit, whichever
 *   is smaller.
 *
 *   ┌──────────────┐
 *   │ Application  │
 *   │  send(data)  │
 *   └──────┬───────┘
 *          │
 *          ▼
 *   ┌──────────────────────────────────────────────────┐
 *   │ sk->sk_wmem_alloc + skb->truesize > sk_sndbuf ? │
 *   │                                                  │
 *   │  YES ──► Block / EAGAIN                          │
 *   │  NO  ──► Allocate sk_buff, queue for TX          │
 *   └──────────────────────────────────────────────────┘
 *          │
 *          ▼
 *   ┌──────────────────────────────────────────────────┐
 *   │ NIC driver transmits packet                      │
 *   │ TX completion interrupt fires                    │
 *   │ kfree_skb() → sock_wfree() → decrement wmem     │
 *   │ Wake blocked writers                             │
 *   └──────────────────────────────────────────────────┘
 */
```

### 8.9 Summary Diagram: Full sk_buff Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               Lifecycle of an sk_buff (Receive Path)                        │
│                                                                             │
│  NIC receives frame                                                         │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Driver: napi_alloc_skb(napi, frame_size)                           │    │
│  │   - kmem_cache_alloc(skbuff_head_cache) → sk_buff descriptor       │    │
│  │   - page_frag_alloc() → data buffer + skb_shared_info              │    │
│  │   - DMA map the buffer, copy or map the received frame             │    │
│  │   - Set: skb->dev, skb->protocol (via eth_type_trans)              │    │
│  │   - Set: skb->ip_summed (based on HW checksum result)              │    │
│  │   - Set: skb->hash (from RSS if available)                         │    │
│  │   - Set: skb->len, skb->data, skb->tail                           │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ napi_gro_receive() → GRO attempts to merge with previous packets   │    │
│  │   If merged: original sk_buff is freed, data appended as fragment   │    │
│  │   If not:    sk_buff proceeds to netif_receive_skb()               │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ netif_receive_skb() / __netif_receive_skb_core()                   │    │
│  │   - Packet taps (tcpdump via AF_PACKET)                            │    │
│  │   - RPS steering (may enqueue to another CPU's backlog)            │    │
│  │   - VLAN processing                                                │    │
│  │   - Deliver to protocol handler based on skb->protocol             │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ip_rcv() → NF_HOOK(PREROUTING) → ip_rcv_finish()                  │    │
│  │   - Validate IP header                                             │    │
│  │   - Routing decision (skb->_skb_refdst set)                       │    │
│  │   - IPCB(skb) populated in cb[]                                    │    │
│  │   - Defragmentation if needed (may consume sk_buff, produce new)   │    │
│  │   - Forward to ip_local_deliver() or ip_forward()                  │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ tcp_v4_rcv()                                                       │    │
│  │   - Lookup socket (sk = __inet_lookup_skb())                       │    │
│  │   - TCP_SKB_CB(skb) populated in cb[] (overwrites IPCB)            │    │
│  │   - skb->sk = sk (ownership assigned)                              │    │
│  │   - tcp_rcv_established() or tcp_rcv_state_process()               │    │
│  │   - sk_buff queued on sk->sk_receive_queue                         │    │
│  │   - sk->sk_rmem_alloc += skb->truesize                            │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Application: recv(fd, buf, len, 0)                                 │    │
│  │   - tcp_recvmsg() copies data from sk_buff to userspace            │    │
│  │   - sk_buff is removed from receive queue                          │    │
│  │   - consume_skb(skb) called                                        │    │
│  │     → destructor releases rmem accounting                          │    │
│  │     → paged fragments freed (put_page)                             │    │
│  │     → data buffer freed (kfree / page_frag_free)                   │    │
│  │     → sk_buff descriptor freed (kmem_cache_free)                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Quick Reference -- Key Functions

```
┌──────────────────────────┬───────────────────────────────────────────────┐
│ Function                 │ Purpose                                       │
├──────────────────────────┼───────────────────────────────────────────────┤
│ alloc_skb(size, flags)   │ Allocate sk_buff + data buffer of 'size'     │
│ netdev_alloc_skb(dev,sz) │ Allocate for receive (driver context)        │
│ napi_alloc_skb(napi,sz)  │ Allocate for receive (NAPI context)          │
│ alloc_skb_fclone(sz,fl)  │ Allocate fast-clone pair                     │
│ skb_clone(skb, flags)    │ Clone: new metadata, shared data buffer      │
│ skb_copy(skb, flags)     │ Deep copy: new metadata AND new data buffer  │
│ pskb_copy(skb, flags)    │ Copy linear data, share paged fragments      │
├──────────────────────────┼───────────────────────────────────────────────┤
│ skb_reserve(skb, len)    │ Increase headroom (before data is added)     │
│ skb_put(skb, len)        │ Append len bytes at tail                     │
│ skb_push(skb, len)       │ Prepend len bytes (move data backward)       │
│ skb_pull(skb, len)       │ Remove len bytes from head (move data fwd)   │
│ skb_trim(skb, len)       │ Trim packet to 'len' bytes total             │
├──────────────────────────┼───────────────────────────────────────────────┤
│ skb_headroom(skb)        │ Bytes available before data                  │
│ skb_tailroom(skb)        │ Bytes available after tail                   │
│ skb_headlen(skb)         │ Linear data length (len - data_len)          │
│ skb_is_nonlinear(skb)    │ True if packet has paged fragments           │
│ skb_linearize(skb)       │ Pull all paged frags into linear buffer      │
├──────────────────────────┼───────────────────────────────────────────────┤
│ skb_mac_header(skb)      │ Pointer to L2 header                        │
│ skb_network_header(skb)  │ Pointer to L3 header                        │
│ skb_transport_header(skb)│ Pointer to L4 header                        │
│ ip_hdr(skb)              │ Cast network_header to struct iphdr *        │
│ tcp_hdr(skb)             │ Cast transport_header to struct tcphdr *     │
│ udp_hdr(skb)             │ Cast transport_header to struct udphdr *     │
│ eth_hdr(skb)             │ Cast mac_header to struct ethhdr *           │
├──────────────────────────┼───────────────────────────────────────────────┤
│ kfree_skb(skb)           │ Free sk_buff (counted as drop)               │
│ consume_skb(skb)         │ Free sk_buff (counted as consume)            │
│ dev_kfree_skb(skb)       │ Free in driver context                       │
│ dev_consume_skb(skb)     │ Consume in driver context                    │
│ napi_consume_skb(skb,b)  │ Batched free in NAPI context                 │
├──────────────────────────┼───────────────────────────────────────────────┤
│ skb_shinfo(skb)          │ Access skb_shared_info at skb->end           │
│ skb_is_gso(skb)          │ True if packet needs segmentation            │
│ skb_shared(skb)          │ True if data buffer is shared                │
│ skb_cloned(skb)          │ True if sk_buff is a clone                   │
│ skb_get_hash(skb)        │ Get or compute flow hash                     │
│ skb_set_owner_w(skb,sk)  │ Set TX ownership and charge wmem             │
│ skb_set_owner_r(skb,sk)  │ Set RX ownership and charge rmem             │
└──────────────────────────┴───────────────────────────────────────────────┘
```

## Appendix B: Configuration Options Affecting sk_buff Size

```
┌────────────────────────────────┬─────────────────────────────────────────┐
│ Config Option                  │ Effect on struct sk_buff                │
├────────────────────────────────┼─────────────────────────────────────────┤
│ CONFIG_NF_CONNTRACK            │ Adds _nfct field (~8 bytes)             │
│ CONFIG_NET_SCHED               │ Adds tc_index field (~2 bytes)          │
│ CONFIG_SKB_EXTENSIONS          │ Adds *extensions pointer (~8 bytes)     │
│ CONFIG_NET_CLS_ACT             │ Adds tc_at field for tc actions         │
│ CONFIG_XFRM                    │ Adds sp field for IPsec                 │
│ CONFIG_NET_SWITCHDEV           │ Adds offload fields                     │
│ CONFIG_NET_REDIRECT            │ Adds redirect info                      │
│ CONFIG_TLS_DEVICE              │ Adds TLS offload fields                 │
│ CONFIG_SOCK_VALIDATE_XMIT      │ Adds validation hooks                   │
│ CONFIG_WIRELESS                │ Adds IEEE80211 fields                   │
└────────────────────────────────┴─────────────────────────────────────────┘

Typical sk_buff sizes by configuration:
  - Minimal (embedded): ~200 bytes
  - Server (most options enabled): ~248 bytes
  - Full debug + all features: ~280+ bytes
```

## Appendix C: Historical Evolution

```
┌───────────┬───────────────────────────────────────────────────────────────┐
│ Version   │ Notable Changes to sk_buff                                   │
├───────────┼───────────────────────────────────────────────────────────────┤
│ 2.2.x     │ Original design. Header pointers are direct (unsigned char *)│
│           │ cb[] is 40 bytes. No scatter-gather support.                 │
│           │                                                              │
│ 2.4.x     │ Scatter-gather support added (frags[] in skb_shared_info).   │
│           │ Zero-copy sendfile() support. TSO introduced.                │
│           │                                                              │
│ 2.6.22    │ Header pointers changed to offsets from head (saves 24 bytes │
│           │ on 64-bit). tail/end become sk_buff_data_t.                  │
│           │                                                              │
│ 2.6.35    │ cb[] expanded from 40 to 48 bytes.                           │
│           │ RPS/RFS hash fields added.                                   │
│           │                                                              │
│ 3.x       │ Fast clone (fclone) mechanism refined.                       │
│           │ skb_shared_info GSO fields expanded.                         │
│           │ Inner header offsets added for tunneling.                     │
│           │                                                              │
│ 4.x       │ skb_ext (extensions) introduced to avoid further growth.     │
│           │ XDP metadata integration.                                    │
│           │ Page pool support in skb_shared_info.                        │
│           │                                                              │
│ 5.x       │ pp_recycle flag for page pool.                               │
│           │ alloc_cpu tracking.                                          │
│           │ Further cache-line optimization.                             │
│           │ active_type for KASAN (memory sanitizer) support.            │
│           │                                                              │
│ 6.x       │ Continued refinement. skb_ext used for TC, bridge, IPsec    │
│           │ metadata. Structure size stabilized around 232-256 bytes.    │
│           │ Emphasis on keeping the hot path within two cache lines.     │
│           │                                                              │
└───────────┴───────────────────────────────────────────────────────────────┘
```

---

**End of Chapter 1.**

*Next: Chapter 2 covers sk_buff allocation, cloning, and lifecycle management in detail.*
