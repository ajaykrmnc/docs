# sk_buff vs qdf_nbuf: A Comprehensive Comparison

## Table of Contents
1. [Overview](#overview)
2. [What is sk_buff?](#what-is-sk_buff)
3. [What is qdf_nbuf?](#what-is-qdf_nbuf)
4. [Key Relationship](#key-relationship)
5. [sk_buff Structure Deep Dive](#sk_buff-structure-deep-dive)
6. [qdf_nbuf Abstraction Layer](#qdf_nbuf-abstraction-layer)
7. [Memory Layout Comparison](#memory-layout-comparison)
8. [Control Block (CB) Comparison](#control-block-cb-comparison)
9. [API Comparison](#api-comparison)
10. [Buffer Manipulation](#buffer-manipulation)
11. [DMA Operations](#dma-operations)
12. [Usage Patterns](#usage-patterns)
13. [Performance Considerations](#performance-considerations)
14. [Debugging](#debugging)
15. [Summary Table](#summary-table)
16. [Linux sk_buff Changes and qdf_nbuf Impact](#linux-sk_buff-changes-and-qdf_nbuf-impact)

---

## Overview

In Linux WLAN drivers, network packets are represented using buffer structures. Understanding the difference 
between `sk_buff` (Linux kernel's native buffer) and `qdf_nbuf` (QCA Driver Framework network buffer) is 
crucial for working with Qualcomm/Atheros wireless drivers.

**Key Insight**: `qdf_nbuf` is NOT a replacement for `sk_buff`. It's an **abstraction layer** (wrapper) around 
`sk_buff` that provides:
- OS-independent API
- Additional metadata for WLAN operations
- Enhanced debugging capabilities
- DMA mapping helpers

---

## What is sk_buff?

`sk_buff` (socket buffer) is the Linux kernel's fundamental data structure for network packet handling. It's 
defined in `<linux/skbuff.h>`.

### Purpose
- Represents network packets at all layers (L2-L7)
- Used by the entire Linux networking stack
- Handles packet data, metadata, and protocol headers
- Supports efficient header/trailer manipulation

### Key Characteristics
- **Native to Linux kernel**
- Used by all network drivers, protocols, and subsystems
- Highly optimized for performance
- Contains both packet data and extensive metadata

```
┌─────────────────────────────────────────────────────────────────────┐
│                        sk_buff Overview                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    struct sk_buff                           │   │
│   │  (Metadata - ~256 bytes depending on kernel version)        │   │
│   ├─────────────────────────────────────────────────────────────┤   │
│   │  • List pointers (next, prev)                               │   │
│   │  • Socket reference (sk)                                    │   │
│   │  • Network device (dev)                                     │   │
│   │  • Data pointers (head, data, tail, end)                    │   │
│   │  • Length fields (len, data_len, mac_len, etc.)             │   │
│   │  • Protocol info (protocol, pkt_type)                       │   │
│   │  • Control block (cb[48])                                   │   │
│   │  • Checksum info                                            │   │
│   │  • Priority, mark, timestamps                               │   │
│   │  • And many more...                                         │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              │ Points to                            │
│                              ▼                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    Data Buffer                              │   │
│   │            (Actual packet data region)                      │   │
│   │                                                             │   │
│   │  head ──▶ ┌──────────────────────────────────────────────┐  │   │
│   │           │           Headroom                            │  │   │
│   │  data ──▶ ├──────────────────────────────────────────────┤  │   │
│   │           │           Packet Data                         │  │   │
│   │  tail ──▶ ├──────────────────────────────────────────────┤  │   │
│   │           │           Tailroom                            │  │   │
│   │  end ───▶ └──────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What is qdf_nbuf?

`qdf_nbuf` (QDF Network Buffer) is Qualcomm's abstraction layer over `sk_buff`, part of the **QDF (QCA Driver 
Framework)**.

### Purpose
- Provide OS-independent network buffer API
- Enable code portability across different operating systems
- Add WLAN-specific metadata and operations
- Provide debugging and memory tracking capabilities

### Key Characteristics
- **Wrapper around sk_buff** (on Linux)
- Adds WLAN-specific control block data
- Provides DMA mapping helpers
- Includes memory debugging support

### Definition (Linux)

```c
// From i_qdf_nbuf.h
typedef struct sk_buff *__qdf_nbuf_t;

// From qdf_nbuf.h
typedef __qdf_nbuf_t qdf_nbuf_t;
```

**Critical Understanding**: On Linux, `qdf_nbuf_t` IS literally a `struct sk_buff *`. It's the same pointer!

---

## Key Relationship

```
┌─────────────────────────────────────────────────────────────────────┐
│                    qdf_nbuf ↔ sk_buff Relationship                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    qdf_nbuf_t  ════════════════════════════════════►  sk_buff *    │
│       │                    (Same pointer!)                 │        │
│       │                                                    │        │
│       │                                                    │        │
│    ┌──▼────────────────────────────────────────────────────▼──┐    │
│    │                    struct sk_buff                        │    │
│    │                                                          │    │
│    │  ┌──────────────────────────────────────────────────┐   │    │
│    │  │  Standard sk_buff fields                          │   │    │
│    │  │  (next, prev, dev, data, len, etc.)               │   │    │
│    │  └──────────────────────────────────────────────────┘   │    │
│    │                                                          │    │
│    │  ┌──────────────────────────────────────────────────┐   │    │
│    │  │  Control Block: cb[48]                            │   │    │
│    │  │  ┌──────────────────────────────────────────────┐│   │    │
│    │  │  │  struct qdf_nbuf_cb (QDF's view)             ││   │    │
│    │  │  │  - DMA address (paddr)                       ││   │    │
│    │  │  │  - RX metadata (peer_id, vdev_id, etc.)      ││   │    │
│    │  │  │  - TX metadata (ftype, trace, etc.)          ││   │    │
│    │  │  │  - Protocol tags, flow tags                  ││   │    │
│    │  │  │  - WLAN-specific flags                       ││   │    │
│    │  │  └──────────────────────────────────────────────┘│   │    │
│    │  └──────────────────────────────────────────────────┘   │    │
│    │                                                          │    │
│    └──────────────────────────────────────────────────────────┘    │
│                                                                     │
│  The "magic" is in how QDF interprets the sk_buff's cb[] array!    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## sk_buff Structure Deep Dive

### Core sk_buff Fields

```c
struct sk_buff {
  /* Linked list pointers */
  struct sk_buff      *next;
  struct sk_buff      *prev;
    
  /* Socket and device */
  struct sock         *sk;
  struct net_device   *dev;
    
  /* Timestamp */
  ktime_t             tstamp;
    
  /* Data pointers - THE MOST IMPORTANT FIELDS */
  unsigned char       *head;    // Start of allocated buffer
  unsigned char       *data;    // Start of actual data
  unsigned int        tail;     // End of actual data (offset from head)
  unsigned int        end;      // End of allocated buffer (offset from head)
    
  /* Length fields */
  unsigned int        len;      // Total data length (including fragments)
  unsigned int        data_len; // Length in fragments (paged data)
  __u16               mac_len;  // MAC header length
  __u16               hdr_len;  // Hardware header length
    
  /* Control block - 48 bytes for private use */
  char                cb[48] __aligned(8);
    
  /* Reference counting */
  refcount_t          users;
    
  /* Protocol and type */
  __be16              protocol;
  __u8                pkt_type;
    
  /* Checksum info */
  __u8                ip_summed;
  __wsum              csum;
    
  /* Priority and mark */
  __u32               priority;
  __u32               mark;

  /* ... many more fields ... */
};
```

### Data Pointers Explained

The four data pointers are fundamental to understanding sk_buff:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    sk_buff Data Pointers                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Allocated Buffer:                                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │◄─────────────────── skb->truesize ────────────────────────►│  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  head ──────►┌──────────────────────────────────────────────────┐  │
│              │              HEADROOM                            │  │
│              │    (Reserved space for adding headers)           │  │
│              │    headroom = skb->data - skb->head              │  │
│  data ──────►├──────────────────────────────────────────────────┤  │
│              │                                                  │  │
│              │              PACKET DATA                         │  │
│              │         skb->len = tail - data                   │  │
│              │                                                  │  │
│  tail ──────►├──────────────────────────────────────────────────┤  │
│              │              TAILROOM                            │  │
│              │    (Reserved space for adding trailers)          │  │
│              │    tailroom = skb->end - skb->tail               │  │
│  end ───────►└──────────────────────────────────────────────────┘  │
│                                                                     │
│  Key Relationships:                                                 │
│  • skb_headroom(skb) = skb->data - skb->head                       │
│  • skb_tailroom(skb) = skb->end - skb->tail                        │
│  • skb->len = amount of valid data (tail - data)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Headroom and Tailroom Purpose

```
Sending a packet through the stack:

Application Layer:
┌──────────────────────────────────────┐
│            "Hello World"             │  ← Application data
└──────────────────────────────────────┘

Transport Layer (TCP):
┌─────────────┬─────────────────────────────────┐
│  TCP Header │         "Hello World"           │  ← skb_push() adds TCP header
└─────────────┴─────────────────────────────────┘
Using HEADROOM ↑

Network Layer (IP):
┌───────────┬─────────────┬─────────────────────────────────┐
│ IP Header │  TCP Header │         "Hello World"           │  ← skb_push() adds IP header
└───────────┴─────────────┴─────────────────────────────────┘

Data Link Layer (Ethernet):
┌────────────────┬───────────┬─────────────┬───────────────────────────┬─────┐
│ Ethernet Header│ IP Header │  TCP Header │       "Hello World"       │ FCS │
└────────────────┴───────────┴─────────────┴───────────────────────────┴─────┘
Using TAILROOM ↑
```

---

## qdf_nbuf Abstraction Layer

### Why an Abstraction?

QDF (QCA Driver Framework) is designed for OS independence:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QDF Abstraction Purpose                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                    WLAN Driver Code                                 │
│                         │                                           │
│                         │ Uses                                      │
│                         ▼                                           │
│              ┌─────────────────────┐                               │
│              │   qdf_nbuf API      │  ← OS-Independent API         │
│              │   qdf_nbuf_alloc()  │                               │
│              │   qdf_nbuf_free()   │                               │
│              │   qdf_nbuf_data()   │                               │
│              │   qdf_nbuf_len()    │                               │
│              └─────────────────────┘                               │
│                         │                                           │
│         ┌───────────────┼───────────────┐                          │
│         │               │               │                          │
│         ▼               ▼               ▼                          │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐                   │
│   │  Linux    │   │  Windows  │   │   RTOS    │                   │
│   │  sk_buff  │   │    NBL    │   │  Custom   │                   │
│   └───────────┘   └───────────┘   └───────────┘                   │
│                                                                     │
│  Same driver code works on different operating systems!            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Linux Implementation

On Linux, qdf_nbuf is just a typedef to sk_buff:

```c
// i_qdf_nbuf.h (Internal, OS-specific)
typedef struct sk_buff *__qdf_nbuf_t;

// qdf_nbuf.h (Public, OS-independent)
typedef __qdf_nbuf_t qdf_nbuf_t;

// Therefore:
qdf_nbuf_t nbuf;   // Is the same as: struct sk_buff *nbuf;
```

### qdf_nbuf API Mapping to sk_buff

```c
// qdf_nbuf functions map to sk_buff functions:

// Allocation
qdf_nbuf_alloc()     →  alloc_skb() + additional setup
qdf_nbuf_free()      →  dev_kfree_skb_any()

// Data access
qdf_nbuf_data()      →  skb->data
qdf_nbuf_len()       →  skb->len

// Buffer manipulation
qdf_nbuf_push_head() →  skb_push()
qdf_nbuf_pull_head() →  skb_pull()
qdf_nbuf_put_tail()  →  skb_put()
qdf_nbuf_trim_tail() →  skb_trim()

// Queue operations
qdf_nbuf_queue_add() →  skb_queue_tail()
qdf_nbuf_queue_remove() → skb_dequeue()
```

---

## Memory Layout Comparison

### sk_buff Native Memory Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Native sk_buff Memory Layout                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   struct sk_buff                             │   │
│  │                    (~256 bytes)                              │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │ next, prev (list management)                          │  │   │
│  │  │ sk (socket), dev (netdevice)                          │  │   │
│  │  │ head, data, tail, end (data pointers)                 │  │   │
│  │  │ len, data_len, mac_len, hdr_len                       │  │   │
│  │  │ protocol, pkt_type                                    │  │   │
│  │  │ cb[48] - Control Block (private storage)              │  │   │
│  │  │ users (refcount)                                      │  │   │
│  │  │ ... (many other fields)                               │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                             │                                       │
│                             │ Separate allocation                   │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Data Buffer                               │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │ Headroom (for protocol headers)                       │  │   │
│  │  ├───────────────────────────────────────────────────────┤  │   │
│  │  │ Packet Data (Ethernet + IP + TCP + Payload)           │  │   │
│  │  ├───────────────────────────────────────────────────────┤  │   │
│  │  │ Tailroom (for FCS, etc.)                              │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │ skb_shared_info (at end of buffer)                    │  │   │
│  │  │ - Fragment info (frags[])                             │  │   │
│  │  │ - GSO info                                            │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### qdf_nbuf Memory Layout (Same sk_buff + QDF CB interpretation)

```
┌─────────────────────────────────────────────────────────────────────┐
│               qdf_nbuf Memory Layout (Linux)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   struct sk_buff                             │   │
│  │              (SAME structure as above!)                      │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │ ... standard fields ...                               │  │   │
│  │  │                                                       │  │   │
│  │  │ cb[48] ─────────────────────────────────────────────┐│  │   │
│  │  │ │  QDF interprets this as struct qdf_nbuf_cb:      ││  │   │
│  │  │ │  ┌─────────────────────────────────────────────┐ ││  │   │
│  │  │ │  │ paddr (DMA address of data)        8 bytes │ ││  │   │
│  │  │ │  ├─────────────────────────────────────────────┤ ││  │   │
│  │  │ │  │ union { rx, tx } - direction-specific:      │ ││  │   │
│  │  │ │  │                                    40 bytes │ ││  │   │
│  │  │ │  │   RX: peer_id, vdev_id, protocol_tag,      │ ││  │   │
│  │  │ │  │       flow_tag, msdu_len, flags...         │ ││  │   │
│  │  │ │  │   TX: ftype, data_attr, trace info,        │ ││  │   │
│  │  │ │  │       extra frag vaddr/paddr...            │ ││  │   │
│  │  │ │  └─────────────────────────────────────────────┘ ││  │   │
│  │  │ └──────────────────────────────────────────────────┘│  │   │
│  │  │                                                       │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  qdf_nbuf adds NO extra memory - just interprets cb[] differently! │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Control Block (CB) Comparison

The control block is the key differentiator. sk_buff provides 48 bytes (`cb[48]`) for private use by 
protocols/drivers.

### sk_buff Control Block Usage

Different protocols use cb[] differently:

```c
// TCP uses it for:
struct tcp_skb_cb {
  __u32       seq;        // Starting sequence number
  __u32       end_seq;    // Ending sequence number
  __u8        tcp_flags;
  // ... etc
};

// IP uses it for:
struct inet_skb_parm {
  int         iif;        // Input interface index
  // ... etc
};
```

### qdf_nbuf Control Block (struct qdf_nbuf_cb)

QDF defines its own structure to overlay on cb[]:

```c
struct qdf_nbuf_cb {
  /* Common: DMA address of skb->data */
  qdf_paddr_t paddr;          /* 8 bytes */

  /* Direction-specific union (40 bytes) */
  union {
    /* RX Control Block */
    struct {
      void *ext_cb_ptr;       /* Extension callback pointer */
      void *fctx;             /* Function context */
      uint16_t msdu_len;      /* MSDU length */
      uint16_t peer_id;       /* Peer ID */
      uint16_t protocol_tag;  /* Protocol tag */
      uint16_t flow_tag;      /* Flow tag */
      uint32_t flow_idx;      /* Flow index */
      uint8_t vdev_id;        /* VDEV ID */
      uint8_t tid_val;        /* TID value */
      uint8_t ftype;          /* Frame type */
      /* ... flags ... */
      uint8_t flag_chfrag_start:1,
      flag_chfrag_cont:1,
      flag_chfrag_end:1,
      flag_da_mcbc:1,
      flag_is_frag:1,
      fcs_err:1,
      is_raw_frame:1;
      /* ... more fields ... */
    } rx;

    /* TX Control Block */
    struct {
      uint8_t ftype;          /* Frame type */
      uint8_t reserved;
      uint16_t flags;
      struct {
        uint8_t packet_state;
        uint8_t dp_trace:1,
        is_bcast:1,
        is_mcast:1,
        packet_type:3;
      } trace;
      unsigned char *vaddr;   /* Extra fragment vaddr */
      qdf_paddr_t paddr;      /* Extra fragment paddr */
    } tx;
  } u;
}; /* MAX 48 bytes - must fit in sk_buff cb[] */
```

### CB Access Macros

```c
// QDF provides macros to access CB fields:

// DMA address
#define QDF_NBUF_CB_PADDR(skb) \
(((struct qdf_nbuf_cb *)((skb)->cb))->paddr.dma_addr)

// RX fields
#define QDF_NBUF_CB_RX_PEER_ID(skb) \
(((struct qdf_nbuf_cb *)((skb)->cb))->u.rx.peer_id)

#define QDF_NBUF_CB_RX_VDEV_ID(skb) \
(((struct qdf_nbuf_cb *)((skb)->cb))->u.rx.vdev_id)

#define QDF_NBUF_CB_RX_FCS_ERR(skb) \
(((struct qdf_nbuf_cb *)((skb)->cb))->u.rx.fcs_err)

// TX fields
#define QDF_NBUF_CB_TX_FTYPE(skb) \
(((struct qdf_nbuf_cb *)((skb)->cb))->u.tx.ftype)

#define QDF_NBUF_CB_GET_IS_BCAST(skb) \
(((struct qdf_nbuf_cb *)((skb)->cb))->u.tx.trace.is_bcast)
```

---

## API Comparison

### Allocation and Deallocation

| Operation | sk_buff API | qdf_nbuf API |
|-----------|-------------|--------------|
| Allocate buffer | `alloc_skb(size, gfp)` | `qdf_nbuf_alloc(osdev, size, reserve, align, prio)` |
| Allocate for RX | `netdev_alloc_skb(dev, size)` | `qdf_nbuf_alloc_no_recycler(size, reserve, align)` |
| Free buffer | `kfree_skb(skb)` | `qdf_nbuf_free(nbuf)` |
| Free (any context) | `dev_kfree_skb_any(skb)` | `qdf_nbuf_free(nbuf)` |
| Clone buffer | `skb_clone(skb, gfp)` | `qdf_nbuf_clone(nbuf)` |
| Copy buffer | `skb_copy(skb, gfp)` | `qdf_nbuf_copy(nbuf)` |

### Data Access

| Operation | sk_buff API | qdf_nbuf API |
|-----------|-------------|--------------|
| Get data pointer | `skb->data` | `qdf_nbuf_data(nbuf)` |
| Get data length | `skb->len` | `qdf_nbuf_len(nbuf)` |
| Get headroom | `skb_headroom(skb)` | `qdf_nbuf_headroom(nbuf)` |
| Get tailroom | `skb_tailroom(skb)` | `qdf_nbuf_tailroom(nbuf)` |
| Get head pointer | `skb->head` | `qdf_nbuf_head(nbuf)` |

### Buffer Manipulation

| Operation | sk_buff API | qdf_nbuf API |
|-----------|-------------|--------------|
| Add to head | `skb_push(skb, len)` | `qdf_nbuf_push_head(nbuf, len)` |
| Remove from head | `skb_pull(skb, len)` | `qdf_nbuf_pull_head(nbuf, len)` |
| Add to tail | `skb_put(skb, len)` | `qdf_nbuf_put_tail(nbuf, len)` |
| Trim from tail | `skb_trim(skb, len)` | `qdf_nbuf_trim_tail(nbuf, len)` |
| Reserve headroom | `skb_reserve(skb, len)` | `qdf_nbuf_reserve(nbuf, len)` |

### Queue Operations

| Operation | sk_buff API | qdf_nbuf API |
|-----------|-------------|--------------|
| Init queue | `skb_queue_head_init(q)` | `qdf_nbuf_queue_init(q)` |
| Add to tail | `skb_queue_tail(q, skb)` | `qdf_nbuf_queue_add(q, nbuf)` |
| Remove from head | `skb_dequeue(q)` | `qdf_nbuf_queue_remove(q)` |
| Check empty | `skb_queue_empty(q)` | `qdf_nbuf_is_queue_empty(q)` |
| Get length | `skb_queue_len(q)` | `qdf_nbuf_queue_len(q)` |

### Reference Counting

| Operation | sk_buff API | qdf_nbuf API |
|-----------|-------------|--------------|
| Get reference | `skb_get(skb)` | `qdf_nbuf_ref(nbuf)` |
| Check shared | `skb_shared(skb)` | `qdf_nbuf_shared(nbuf)` |
| Make private | `skb_unshare(skb, gfp)` | `qdf_nbuf_unshare(nbuf)` |

---

## Buffer Manipulation

### skb_push / qdf_nbuf_push_head

Adds data to the beginning of the buffer (uses headroom):

```c
// sk_buff way
unsigned char *new_data = skb_push(skb, sizeof(struct ethhdr));
memcpy(new_data, &eth_header, sizeof(struct ethhdr));

// qdf_nbuf way
uint8_t *new_data = qdf_nbuf_push_head(nbuf, sizeof(struct ethhdr));
qdf_mem_copy(new_data, &eth_header, sizeof(struct ethhdr));
```

```
Before skb_push(skb, 14):
┌────────────────────────────────────────────────────────────┐
│  Headroom (50 bytes)  │  IP + TCP + Data (100 bytes)       │
│                       │                                    │
│  head ────────────────│data ──────────────────────── tail  │
└────────────────────────────────────────────────────────────┘

After skb_push(skb, 14):
┌────────────────────────────────────────────────────────────┐
│  Headroom  │  Eth Hdr  │  IP + TCP + Data (100 bytes)      │
│  (36 bytes)│ (14 bytes)│                                   │
│  head ─────│data ──────│──────────────────────────── tail  │
└────────────────────────────────────────────────────────────┘
```

### skb_pull / qdf_nbuf_pull_head

Removes data from the beginning of the buffer:

```c
// sk_buff way
skb_pull(skb, sizeof(struct ethhdr));  // Skip Ethernet header

// qdf_nbuf way
qdf_nbuf_pull_head(nbuf, sizeof(struct ethhdr));
```

```
Before skb_pull(skb, 14):
┌────────────────────────────────────────────────────────────┐
│  Headroom  │  Eth Hdr  │  IP + TCP + Data (100 bytes)      │
│  (36 bytes)│ (14 bytes)│                                   │
│  head ─────│data ──────│──────────────────────────── tail  │
└────────────────────────────────────────────────────────────┘

After skb_pull(skb, 14):
┌────────────────────────────────────────────────────────────┐
│  Headroom (50 bytes)  │  IP + TCP + Data (100 bytes)       │
│                       │                                    │
│  head ────────────────│data ──────────────────────── tail  │
└────────────────────────────────────────────────────────────┘
```

### skb_put / qdf_nbuf_put_tail

Adds data to the end of the buffer (uses tailroom):

```c
// sk_buff way
unsigned char *tail = skb_put(skb, 4);  // Add 4 bytes for FCS
memcpy(tail, &fcs, 4);

// qdf_nbuf way
uint8_t *tail = qdf_nbuf_put_tail(nbuf, 4);
qdf_mem_copy(tail, &fcs, 4);
```

### skb_reserve / qdf_nbuf_reserve

Reserves headroom in an empty buffer (must be called before adding data):

```c
// sk_buff way
struct sk_buff *skb = alloc_skb(1500, GFP_KERNEL);
skb_reserve(skb, NET_IP_ALIGN + ETH_HLEN);  // Reserve for alignment + Ethernet

// qdf_nbuf way
qdf_nbuf_t nbuf = qdf_nbuf_alloc(osdev, 1500, 0, 4, false);
qdf_nbuf_reserve(nbuf, NET_IP_ALIGN + ETH_HLEN);
```

---

## DMA Operations

### sk_buff DMA Mapping

sk_buff doesn't have built-in DMA support. You must use the DMA API:

```c
// Map for DMA
dma_addr_t dma_addr = dma_map_single(dev, skb->data, skb->len, DMA_TO_DEVICE);
if (dma_mapping_error(dev, dma_addr)) {
  // Handle error
}

// After DMA completes
dma_unmap_single(dev, dma_addr, skb->len, DMA_TO_DEVICE);
```

### qdf_nbuf DMA Mapping

qdf_nbuf provides integrated DMA support with paddr stored in CB:

```c
// Map for DMA
QDF_STATUS status = qdf_nbuf_map_single(osdev, nbuf, QDF_DMA_TO_DEVICE);
if (status != QDF_STATUS_SUCCESS) {
  // Handle error
}

// Get DMA address (stored in CB)
qdf_dma_addr_t paddr = qdf_nbuf_get_frag_paddr(nbuf, 0);
// Or: qdf_dma_addr_t paddr = QDF_NBUF_CB_PADDR(nbuf);

// After DMA completes
qdf_nbuf_unmap_single(osdev, nbuf, QDF_DMA_TO_DEVICE);
```

### DMA Address Storage

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DMA Address Storage                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  sk_buff:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  No built-in DMA address storage                            │   │
│  │  Driver must track dma_addr separately                      │   │
│  │  Often stored in driver-specific structures                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  qdf_nbuf:                                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  cb[48] contains:                                           │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │  paddr (qdf_paddr_t) - 8 bytes                      │   │   │
│  │  │  DMA address stored directly in control block!      │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Advantage: No separate tracking needed, always with the buffer    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Usage Patterns

### Pattern 1: Receiving a Packet

```c
// sk_buff way (typical network driver)
static int my_driver_rx(struct net_device *dev)
{
  struct sk_buff *skb;
  int len = get_rx_length();

  skb = netdev_alloc_skb(dev, len + NET_IP_ALIGN);
  if (!skb)
    return -ENOMEM;

  skb_reserve(skb, NET_IP_ALIGN);

  // Copy data from hardware
  memcpy(skb_put(skb, len), hw_buffer, len);

  skb->protocol = eth_type_trans(skb, dev);
  skb->ip_summed = CHECKSUM_UNNECESSARY;

  netif_rx(skb);
  return 0;
}

// qdf_nbuf way (WLAN driver)
static QDF_STATUS wlan_rx_handler(qdf_nbuf_t nbuf)
{
  uint16_t peer_id = QDF_NBUF_CB_RX_PEER_ID(nbuf);
  uint8_t vdev_id = QDF_NBUF_CB_RX_VDEV_ID(nbuf);

  // Check for FCS error
  if (QDF_NBUF_CB_RX_FCS_ERR(nbuf)) {
    qdf_nbuf_free(nbuf);
    return QDF_STATUS_E_FAILURE;
  }

  // Process based on frame type
  uint8_t ftype = QDF_NBUF_CB_RX_FTYPE(nbuf);

  // Strip WLAN header
  qdf_nbuf_pull_head(nbuf, wlan_hdr_len);

  // Convert to Ethernet and send up
  // ...

  return QDF_STATUS_SUCCESS;
}
```

### Pattern 2: Transmitting a Packet

```c
// sk_buff way
static netdev_tx_t my_driver_tx(struct sk_buff *skb, struct net_device *dev)
{
  dma_addr_t dma_addr;

  // Map for DMA
  dma_addr = dma_map_single(&dev->dev, skb->data, skb->len, DMA_TO_DEVICE);
  if (dma_mapping_error(&dev->dev, dma_addr)) {
    dev_kfree_skb_any(skb);
    return NETDEV_TX_OK;
  }

  // Queue to hardware
  hw_queue_tx(dma_addr, skb->len, skb);

  return NETDEV_TX_OK;
}

// qdf_nbuf way
static QDF_STATUS wlan_tx_handler(qdf_nbuf_t nbuf, uint8_t vdev_id)
{
  // Set TX metadata in CB
  QDF_NBUF_CB_TX_FTYPE(nbuf) = CB_FTYPE_DATA;

  // Map for DMA (paddr stored in CB)
  if (qdf_nbuf_map_single(osdev, nbuf, QDF_DMA_TO_DEVICE) != QDF_STATUS_SUCCESS) {
    qdf_nbuf_free(nbuf);
    return QDF_STATUS_E_FAILURE;
  }

  // Get DMA address from CB
  qdf_dma_addr_t paddr = QDF_NBUF_CB_PADDR(nbuf);

  // Queue to hardware
  dp_tx_enqueue(paddr, qdf_nbuf_len(nbuf), nbuf);

  return QDF_STATUS_SUCCESS;
}
```

### Pattern 3: Buffer Cloning

```c
// sk_buff way
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC);
if (clone) {
  // clone shares data with original
  // Modifications to data affect both
  // But skb metadata is separate
}

// qdf_nbuf way
qdf_nbuf_t clone = qdf_nbuf_clone(nbuf);
if (clone) {
  // Same behavior - shares data
  // CB is copied, not shared
}
```

---

## Performance Considerations

### Memory Overhead

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Memory Overhead Comparison                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  sk_buff:                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  struct sk_buff:     ~256 bytes (varies by kernel config)   │   │
│  │  Data buffer:        Variable (MTU + headroom + tailroom)   │   │
│  │  skb_shared_info:    ~320 bytes (at end of data buffer)     │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  Total overhead:     ~576 bytes + data                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  qdf_nbuf:                                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Same as sk_buff (it IS sk_buff!)                           │   │
│  │  No additional memory allocation                            │   │
│  │  CB interpretation adds ZERO memory overhead                │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  Total overhead:     Same as sk_buff                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Function Call Overhead

```c
// qdf_nbuf functions are often inline wrappers:

// qdf_nbuf.h
static inline uint8_t *qdf_nbuf_data(qdf_nbuf_t buf)
{
  return __qdf_nbuf_data(buf);
}

// i_qdf_nbuf.h
static inline uint8_t *__qdf_nbuf_data(struct sk_buff *skb)
{
  return skb->data;  // Direct access!
}

// Compiler optimizes to: return skb->data;
// Zero overhead when inlined!
```

### When to Use Which

| Scenario | Recommendation |
|----------|----------------|
| Generic Linux network driver | Use sk_buff directly |
| QCA WLAN driver code | Use qdf_nbuf for portability |
| Performance-critical path | Either (both inline to same code) |
| Need WLAN metadata (peer_id, etc.) | Use qdf_nbuf CB macros |
| Interfacing with Linux stack | Use sk_buff (or cast qdf_nbuf) |
| Cross-platform driver code | Use qdf_nbuf |

---

## Debugging

### sk_buff Debugging

```c
// Print sk_buff info
void dump_skb(struct sk_buff *skb)
{
  printk("skb: %p\n", skb);
  printk("  head: %p, data: %p, tail: %u, end: %u\n",
         skb->head, skb->data, skb->tail, skb->end);
  printk("  len: %u, data_len: %u\n", skb->len, skb->data_len);
  printk("  headroom: %u, tailroom: %u\n",
         skb_headroom(skb), skb_tailroom(skb));
  printk("  users: %d\n", refcount_read(&skb->users));
  print_hex_dump(KERN_DEBUG, "data: ", DUMP_PREFIX_OFFSET,
                 16, 1, skb->data, min(skb->len, 64U), true);
}
```

### qdf_nbuf Debugging

```c
// QDF provides debug functions
void dump_nbuf(qdf_nbuf_t nbuf)
{
  qdf_print("nbuf: %pK\n", nbuf);
  qdf_print("  data: %pK, len: %u\n",
            qdf_nbuf_data(nbuf), qdf_nbuf_len(nbuf));
  qdf_print("  headroom: %u, tailroom: %u\n",
            qdf_nbuf_headroom(nbuf), qdf_nbuf_tailroom(nbuf));

  // WLAN-specific CB info
  qdf_print("  paddr: %llx\n", QDF_NBUF_CB_PADDR(nbuf));
  qdf_print("  RX peer_id: %u, vdev_id: %u\n",
            QDF_NBUF_CB_RX_PEER_ID(nbuf),
            QDF_NBUF_CB_RX_VDEV_ID(nbuf));

  // Hex dump
  qdf_trace_hex_dump(QDF_MODULE_ID_ANY, QDF_TRACE_LEVEL_DEBUG,
                     qdf_nbuf_data(nbuf),
                     QDF_MIN(qdf_nbuf_len(nbuf), 64));
}

// QDF also has nbuf tracking for memory leak detection
// Enable with: qdf_nbuf_map_tracking_config(true);
```

### Common Debugging Issues

| Issue | sk_buff Symptom | qdf_nbuf Symptom |
|-------|-----------------|------------------|
| Use after free | Kernel panic, corruption | Same + QDF tracking can detect |
| Double free | Kernel panic | Same + QDF tracking can detect |
| Buffer overflow | Data corruption | Same |
| Headroom exhausted | skb_push fails | qdf_nbuf_push_head fails |
| Tailroom exhausted | skb_put fails | qdf_nbuf_put_tail fails |
| DMA not unmapped | Memory leak, IOMMU errors | Same |

---

## Summary Table

| Aspect | sk_buff | qdf_nbuf |
|--------|---------|----------|
| **Definition** | Linux kernel structure | Typedef to sk_buff* |
| **Memory** | ~256 bytes + data | Same (no extra) |
| **Portability** | Linux only | Cross-platform API |
| **DMA Address** | External tracking | Stored in CB |
| **WLAN Metadata** | Not available | peer_id, vdev_id, etc. in CB |
| **Control Block** | 48 bytes, protocol-specific | 48 bytes, WLAN-specific |
| **API Style** | skb_* functions | qdf_nbuf_* functions |
| **Performance** | Native | Same (inline wrappers) |
| **Debugging** | Kernel tools | QDF tracking + kernel tools |
| **Use Case** | All Linux networking | QCA WLAN drivers |

---

## Quick Reference

### Converting Between Types

```c
// qdf_nbuf to sk_buff (they're the same!)
qdf_nbuf_t nbuf = ...;
  struct sk_buff *skb = (struct sk_buff *)nbuf;  // Direct cast

// sk_buff to qdf_nbuf
struct sk_buff *skb = ...;
qdf_nbuf_t nbuf = (qdf_nbuf_t)skb;  // Direct cast

// Both point to the same memory!
```

### Common Operations Cheat Sheet

```c
// Allocation
qdf_nbuf_t nbuf = qdf_nbuf_alloc(osdev, size, reserve, align, prio);

// Free
qdf_nbuf_free(nbuf);

// Get data pointer and length
uint8_t *data = qdf_nbuf_data(nbuf);
uint32_t len = qdf_nbuf_len(nbuf);

// Add header (uses headroom)
uint8_t *hdr = qdf_nbuf_push_head(nbuf, hdr_len);

// Remove header
qdf_nbuf_pull_head(nbuf, hdr_len);

// Add trailer (uses tailroom)
uint8_t *tail = qdf_nbuf_put_tail(nbuf, tail_len);

// DMA map
qdf_nbuf_map_single(osdev, nbuf, QDF_DMA_TO_DEVICE);
qdf_dma_addr_t paddr = QDF_NBUF_CB_PADDR(nbuf);

// DMA unmap
qdf_nbuf_unmap_single(osdev, nbuf, QDF_DMA_TO_DEVICE);

// Get WLAN metadata
uint16_t peer = QDF_NBUF_CB_RX_PEER_ID(nbuf);
uint8_t vdev = QDF_NBUF_CB_RX_VDEV_ID(nbuf);
```

---

## Glossary

| Term | Definition |
|------|------------|
| **sk_buff** | Socket buffer - Linux kernel's network packet structure |
| **qdf_nbuf** | QDF Network Buffer - QCA's abstraction over sk_buff |
| **QDF** | QCA Driver Framework - OS abstraction layer |
| **CB** | Control Block - 48-byte private storage in sk_buff |
| **paddr** | Physical/DMA address |
| **vaddr** | Virtual address |
| **headroom** | Space before data for adding headers |
| **tailroom** | Space after data for adding trailers |
| **skb_push** | Add data to beginning of buffer |
| **skb_pull** | Remove data from beginning of buffer |
| **skb_put** | Add data to end of buffer |
| **skb_reserve** | Reserve headroom in empty buffer |
| **peer_id** | Identifier for connected client/peer |
| **vdev_id** | Virtual device (VAP) identifier |
| **ftype** | Frame type (management, data, control) |
| **MSDU** | MAC Service Data Unit - payload |
| **DMA** | Direct Memory Access |

---

## Fragments and Scatter-Gather

### sk_buff Fragments (skb_shared_info)

sk_buff supports non-linear data through fragments stored in `skb_shared_info`:

```c
struct skb_shared_info {
  __u8        nr_frags;           // Number of fragments
  __u8        tx_flags;
  unsigned short gso_size;
  unsigned short gso_segs;
  struct sk_buff *frag_list;      // List of sk_buffs
  skb_frag_t  frags[MAX_SKB_FRAGS]; // Page fragments
  // ...
};

// skb_frag_t represents a page fragment
typedef struct skb_frag {
  struct {
    struct page *p;
  } bv_page;
  __u32 bv_len;
  __u32 bv_offset;
} skb_frag_t;
```

```
┌─────────────────────────────────────────────────────────────────────┐
│                    sk_buff with Fragments                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  struct sk_buff                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  len = 4096 (total)                                         │   │
│  │  data_len = 3072 (in fragments)                             │   │
│  │  Linear data = len - data_len = 1024 bytes                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│              ┌───────────────┴───────────────┐                     │
│              ▼                               ▼                     │
│  ┌─────────────────────┐      ┌─────────────────────────────────┐  │
│  │   Linear Data       │      │   skb_shared_info               │  │
│  │   (1024 bytes)      │      │   ┌─────────────────────────┐   │  │
│  │   head → data →     │      │   │ nr_frags = 3            │   │  │
│  │   tail → end        │      │   │ frags[0]: page, 1024B   │───┼──┼─► Page 1
│  └─────────────────────┘      │   │ frags[1]: page, 1024B   │───┼──┼─► Page 2
│                               │   │ frags[2]: page, 1024B   │───┼──┼─► Page 3
│                               │   └─────────────────────────┘   │  │
│                               └─────────────────────────────────┘  │
│                                                                     │
│  Total: 1024 (linear) + 3×1024 (frags) = 4096 bytes                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### qdf_nbuf Extra Fragments

QDF extends fragment support with "extra fragments" stored in the CB:

```c
// From qdf_nbuf CB (TX path)
struct {
  unsigned char *vaddr;   // Extra fragment virtual address
  qdf_paddr_t paddr;      // Extra fragment physical address
} tx;

// Access macros
#define QDF_NBUF_CB_TX_EXTRA_FRAG_VADDR(skb)  // Get extra frag vaddr
#define QDF_NBUF_CB_TX_EXTRA_FRAG_PADDR(skb)  // Get extra frag paddr
```

### Fragment Operations Comparison

| Operation | sk_buff API | qdf_nbuf API |
|-----------|-------------|--------------|
| Get fragment count | `skb_shinfo(skb)->nr_frags` | `qdf_nbuf_get_nr_frags(nbuf)` |
| Add fragment | `skb_add_rx_frag()` | `qdf_nbuf_add_rx_frag()` |
| Get fragment | `skb_frag_page()`, `skb_frag_size()` | `qdf_nbuf_get_frag_vaddr()` |
| Check if linear | `!skb_is_nonlinear(skb)` | `qdf_nbuf_is_nonlinear(nbuf)` |
| Linearize | `skb_linearize(skb)` | `qdf_nbuf_linearize(nbuf)` |

---

## Advanced Topics

### Reference Counting Deep Dive

```c
// sk_buff reference counting
struct sk_buff {
  refcount_t users;  // Reference count
  // ...
};

// Operations
skb_get(skb);           // Increment refcount
kfree_skb(skb);         // Decrement, free if zero
skb_shared(skb);        // Check if refcount > 1
skb_unshare(skb, gfp);  // Make private copy if shared

// qdf_nbuf equivalents
qdf_nbuf_ref(nbuf);
qdf_nbuf_free(nbuf);
qdf_nbuf_shared(nbuf);
qdf_nbuf_unshare(nbuf);
```

### Clone vs Copy

```
┌────────────────────────────────────────────────────────────────────┐
│                    Clone vs Copy                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  CLONE (skb_clone / qdf_nbuf_clone):                               │
│  ┌─────────────────┐     ┌─────────────────┐                       │
│  │  Original skb   │     │   Cloned skb    │                       │
│  │  (metadata)     │     │   (metadata)    │  ← Separate metadata  │
│  └────────┬────────┘     └────────┬────────┘                       │
│           │                       │                                │
│           └───────────┬───────────┘                                │
│                       ▼                                            │
│           ┌─────────────────────┐                                  │
│           │   Shared Data       │  ← Same data buffer!             │
│           │   (refcount = 2)    │                                  │
│           └─────────────────────┘                                  │
│                                                                    │
│  • Fast (no data copy)                                             │
│  • Data modifications affect both                                  │
│  • Metadata (headers, CB) is separate                              │
│                                                                    │
│  ───────────────────────────────────────────────────────────────── │
│                                                                    │
│  COPY (skb_copy / qdf_nbuf_copy):                                  │
│  ┌─────────────────┐     ┌─────────────────┐                       │
│  │  Original skb   │     │   Copied skb    │                       │
│  │  (metadata)     │     │   (metadata)    │  ← Separate metadata  │
│  └────────┬────────┘     └────────┬────────┘                       │
│           │                       │                                │
│           ▼                       ▼                                │
│  ┌─────────────────┐     ┌─────────────────┐                       │
│  │  Original Data  │     │   Copied Data   │  ← Separate data!     │
│  └─────────────────┘     └─────────────────┘                       │
│                                                                    │
│  • Slower (full data copy)                                         │
│  • Completely independent buffers                                  │
│  • Safe to modify either                                           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Checksum Offload

```c
// sk_buff checksum modes
enum {
  CHECKSUM_NONE,          // No checksum needed
  CHECKSUM_UNNECESSARY,   // Hardware verified checksum
  CHECKSUM_COMPLETE,      // Hardware computed checksum
  CHECKSUM_PARTIAL,       // Hardware should compute checksum
};

// Set checksum mode
skb->ip_summed = CHECKSUM_UNNECESSARY;  // RX: HW verified
skb->ip_summed = CHECKSUM_PARTIAL;      // TX: HW should compute

// qdf_nbuf checksum
qdf_nbuf_set_rx_cksum(nbuf, QDF_NBUF_RX_CKSUM_NONE);
qdf_nbuf_set_tx_cksum(nbuf, QDF_NBUF_TX_CKSUM_TCP_UDP);
```

### GSO/TSO (Segmentation Offload)

```c
// sk_buff GSO info in skb_shared_info
struct skb_shared_info {
  unsigned short gso_size;    // Segment size
  unsigned short gso_segs;    // Number of segments
  unsigned short gso_type;    // GSO type flags
};

// Check if GSO
if (skb_is_gso(skb)) {
  // Large packet that hardware will segment
}

// qdf_nbuf TSO
if (qdf_nbuf_is_tso(nbuf)) {
  qdf_nbuf_tso_info_t tso_info;
  qdf_nbuf_get_tso_info(nbuf, &tso_info);
}
```

---

## Memory Allocation Internals

### sk_buff Allocation

```c
// alloc_skb implementation (simplified)
struct sk_buff *alloc_skb(unsigned int size, gfp_t gfp_mask)
{
  struct sk_buff *skb;
  u8 *data;

  // Allocate sk_buff structure from slab cache
  skb = kmem_cache_alloc(skbuff_head_cache, gfp_mask);

  // Allocate data buffer (size + skb_shared_info)
  size = SKB_DATA_ALIGN(size);
  size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
  data = kmalloc(size, gfp_mask);

  // Initialize pointers
  skb->head = data;
  skb->data = data;
  skb->tail = data;
  skb->end = data + size - sizeof(struct skb_shared_info);

  // Initialize refcount
  refcount_set(&skb->users, 1);

  return skb;
}
```

### qdf_nbuf Allocation

```c
// __qdf_nbuf_alloc implementation (simplified)
struct sk_buff *__qdf_nbuf_alloc(qdf_device_t osdev, size_t size,
                                 int reserve, int align, int prio)
{
  struct sk_buff *skb;
  unsigned long offset;

  // Add alignment padding if needed
  if (align)
    size += (align - 1);

  // Allocate using kernel API
  if (in_interrupt())
    skb = alloc_skb(size, GFP_ATOMIC);
  else
    skb = alloc_skb(size, GFP_KERNEL);

  if (!skb)
    return NULL;

  // Align data pointer
  if (align) {
    offset = ((unsigned long)skb->data) % align;
    if (offset)
      skb_reserve(skb, align - offset);
  }

  // Reserve headroom
  if (reserve)
    skb_reserve(skb, reserve);

  // Initialize QDF CB fields
  memset(skb->cb, 0, sizeof(skb->cb));

  return skb;
}
```

### Memory Pools

```c
// sk_buff uses slab allocator
// skbuff_head_cache for sk_buff structures
// kmalloc for data buffers

// qdf_nbuf can use memory pools for performance
qdf_nbuf_t qdf_nbuf_alloc_no_recycler(size_t size, int reserve, int align)
{
  // Allocates without using recycler pool
  // Used when buffer won't be recycled
}

// Some implementations use buffer recycling
// Freed buffers go to pool instead of being freed
// Reduces allocation overhead in fast path
```

---

## WLAN-Specific Features

### Frame Type Handling

```c
// Frame types in qdf_nbuf CB
enum {
  CB_FTYPE_INVALID = 0,
  CB_FTYPE_MCAST2UCAST = 1,
  CB_FTYPE_TSO = 2,
  CB_FTYPE_TSO_SG = 3,
  CB_FTYPE_SG = 4,
  CB_FTYPE_INTRABSS_FWD = 5,
  CB_FTYPE_RX_INFO = 6,
  CB_FTYPE_MESH_RX_INFO = 7,
  CB_FTYPE_MESH_TX_INFO = 8,
  CB_FTYPE_DL_MU_MIMO = 9,
  CB_FTYPE_UL_MU_MIMO = 10,
};

// Set frame type
QDF_NBUF_CB_TX_FTYPE(nbuf) = CB_FTYPE_TSO;

// Check frame type
if (QDF_NBUF_CB_TX_FTYPE(nbuf) == CB_FTYPE_INTRABSS_FWD) {
  // Handle intra-BSS forwarding
}
```

### Protocol Tagging

```c
// Protocol tags for flow classification
#define QDF_NBUF_CB_RX_PROTOCOL_TAG(skb)  // Get protocol tag
#define QDF_NBUF_CB_RX_FLOW_TAG(skb)      // Get flow tag
#define QDF_NBUF_CB_RX_FLOW_IDX(skb)      // Get flow index

// Used for:
// - Traffic classification
// - QoS handling
// - Flow-based processing
```

### Peer and VDEV Tracking

```c
// Every RX packet has peer and vdev info
uint16_t peer_id = QDF_NBUF_CB_RX_PEER_ID(nbuf);
uint8_t vdev_id = QDF_NBUF_CB_RX_VDEV_ID(nbuf);
uint8_t tid = QDF_NBUF_CB_RX_TID_VAL(nbuf);

// Look up peer from ID
struct dp_peer *peer = dp_peer_get_ref_by_id(soc, peer_id);
if (peer) {
  // Process packet for this peer
  dp_peer_unref_del(peer);
}
```

---

## Error Handling

### sk_buff Error Patterns

```c
// Allocation failure
struct sk_buff *skb = alloc_skb(size, GFP_KERNEL);
if (!skb) {
  return -ENOMEM;
}

// Headroom check before push
if (skb_headroom(skb) < needed) {
  if (pskb_expand_head(skb, needed, 0, GFP_ATOMIC)) {
    kfree_skb(skb);
    return -ENOMEM;
  }
}

// Tailroom check before put
if (skb_tailroom(skb) < needed) {
  // Need to reallocate
}
```

### qdf_nbuf Error Patterns

```c
// Allocation failure
qdf_nbuf_t nbuf = qdf_nbuf_alloc(osdev, size, reserve, align, prio);
if (!nbuf) {
  return QDF_STATUS_E_NOMEM;
}

// DMA mapping failure
QDF_STATUS status = qdf_nbuf_map_single(osdev, nbuf, QDF_DMA_TO_DEVICE);
if (QDF_IS_STATUS_ERROR(status)) {
  qdf_nbuf_free(nbuf);
  return status;
}

// Always unmap before free if mapped
qdf_nbuf_unmap_single(osdev, nbuf, QDF_DMA_TO_DEVICE);
qdf_nbuf_free(nbuf);
```

---

## Best Practices

### Do's

1. **Always check allocation return values**
   ```c
   qdf_nbuf_t nbuf = qdf_nbuf_alloc(...);
   if (!nbuf) return QDF_STATUS_E_NOMEM;
   ```

2. **Unmap DMA before freeing**
   ```c
   qdf_nbuf_unmap_single(osdev, nbuf, direction);
   qdf_nbuf_free(nbuf);
   ```

3. **Check headroom/tailroom before push/put**
   ```c
   if (qdf_nbuf_headroom(nbuf) < hdr_len) {
     // Handle insufficient headroom
   }
   ```

4. **Use appropriate allocation context**
   ```c
   // In interrupt context
   nbuf = qdf_nbuf_alloc(..., GFP_ATOMIC, ...);
   // In process context
   nbuf = qdf_nbuf_alloc(..., GFP_KERNEL, ...);
   ```

### Don'ts

1. **Don't access freed buffers**
   ```c
   qdf_nbuf_free(nbuf);
   // nbuf is now invalid - don't use it!
   ```

2. **Don't modify shared buffer data**
   ```c
   if (qdf_nbuf_shared(nbuf)) {
     nbuf = qdf_nbuf_unshare(nbuf);  // Make private copy first
   }
   // Now safe to modify
   ```

3. **Don't assume CB is preserved across stack layers**
   ```c
   // CB may be overwritten by other layers
   // Save needed values before passing to other subsystems
   ```

4. **Don't mix sk_buff and qdf_nbuf APIs carelessly**
   ```c
   // While they're the same pointer, mixing APIs can cause confusion
   // Stick to one API style in each function
   ```

---

## Linux sk_buff Changes and qdf_nbuf Impact

Understanding how modifications to Linux's `sk_buff` structure affect QCA's `qdf_nbuf` operations is critical for driver development and maintenance. Since `qdf_nbuf` is a direct wrapper around `sk_buff`, **any kernel changes to sk_buff directly impact qdf_nbuf behavior**.

### The Tight Coupling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Linux sk_buff ←→ QCA qdf_nbuf Interaction                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Linux Kernel                          QCA WLAN Driver                     │
│   ┌───────────────────────┐            ┌───────────────────────┐           │
│   │   struct sk_buff      │◄──────────►│   qdf_nbuf_t          │           │
│   │   (Authoritative)     │   SAME     │   (Typedef/Wrapper)   │           │
│   │                       │  POINTER   │                       │           │
│   └───────────────────────┘            └───────────────────────┘           │
│            │                                      │                         │
│            │ Changes Here                         │ Affects Here            │
│            ▼                                      ▼                         │
│   ┌───────────────────────┐            ┌───────────────────────┐           │
│   │ • Field offsets       │            │ • CB overlay          │           │
│   │ • Structure size      │────────────│ • API behavior        │           │
│   │ • cb[] size           │  DIRECTLY  │ • Memory layout       │           │
│   │ • Function semantics  │  IMPACTS   │ • DMA operations      │           │
│   │ • Memory layout       │            │ • Driver compatibility│           │
│   └───────────────────────┘            └───────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Categories of sk_buff Changes and qdf_nbuf Impact

#### 1. Structure Layout Changes

When Linux kernel modifies `sk_buff` structure layout:

```c
// Example: Kernel adds new field or reorders fields
struct sk_buff {
  // ... existing fields ...
  __u32 new_kernel_field;  // NEW: Added in kernel 5.x
  char cb[48];             // Position may shift!
  // ...
};
```

**Impact on qdf_nbuf:**

| sk_buff Change | qdf_nbuf Impact | Required Action |
|----------------|-----------------|-----------------|
| New fields added | CB offset may change | Recompile driver against new headers |
| Field reordering | Structure alignment changes | Verify CB overlay still works |
| cb[] size change | qdf_nbuf_cb may not fit | CRITICAL: Resize CB structure |
| Data pointer changes | Buffer manipulation breaks | Update qdf_nbuf pointer macros |

```c
// qdf_nbuf CB MUST fit within sk_buff's cb[48]
// If kernel reduces cb[] size, QDF code breaks!

// Check at compile time:
BUILD_BUG_ON(sizeof(struct qdf_nbuf_cb) > sizeof(((struct sk_buff *)0)->cb));
```

#### 2. API Semantic Changes

When Linux kernel changes how `sk_buff` functions behave:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              sk_buff API Change → qdf_nbuf Wrapper Impact                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Kernel Change: skb_push() now validates headroom differently              │
│                                                                             │
│  ┌─────────────────────────────────┐                                       │
│  │ skb_push(skb, len)              │                                       │
│  │                                 │                                       │
│  │ OLD: BUG if no headroom        │  Changed                               │
│  │ NEW: Returns NULL if no room   │  Behavior!                             │
│  └────────────────┬────────────────┘                                       │
│                   │                                                         │
│                   ▼                                                         │
│  ┌─────────────────────────────────┐                                       │
│  │ qdf_nbuf_push_head(nbuf, len)   │                                       │
│  │                                 │                                       │
│  │ // Wrapper calls skb_push()    │                                       │
│  │ // Behavior change propagates! │  Driver must                           │
│  │ // Must now check return value │  be updated!                           │
│  └─────────────────────────────────┘                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Common API Changes and Impact:**

```c
// Example: Reference counting changes (kernel 4.13+)
// OLD: atomic_t users;
// NEW: refcount_t users;

// qdf_nbuf_ref() internally uses skb_get() which uses users field
// The wrapper works, but debugging tools may interpret refcount differently

// Example: skb_frag_t structure changes
// OLD: struct page *page + offset + size as separate fields
// NEW: biovec-style with struct bio_vec
// Impact: qdf_nbuf fragment iteration code needs updates
```

#### 3. Control Block (cb[]) Interaction

The cb[] array is the primary interaction point. Here's how changes affect both sides:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Control Block Ownership and Conflicts                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  sk_buff travels through multiple layers, each may use cb[]:                │
│                                                                             │
│   Layer              cb[] Usage               Conflict Risk                 │
│   ─────              ──────────               ─────────────                 │
│   │                                                                         │
│   │  WLAN Driver     struct qdf_nbuf_cb       ◄── QCA uses cb[]             │
│   │  (qdf_nbuf)      - paddr                                                │
│   │                  - peer_id, vdev_id                                     │
│   │                  - RX/TX metadata                                       │
│   ▼                                                                         │
│   │  mac80211        struct ieee80211_tx_info  ◄── Overwrites cb[]!         │
│   │  (if used)       - TX flags, rates                                      │
│   ▼                                                                         │
│   │  IP Layer        struct inet_skb_parm      ◄── Overwrites cb[]!         │
│   │                  - IP options                                           │
│   ▼                                                                         │
│   │  TCP Layer       struct tcp_skb_cb         ◄── Overwrites cb[]!         │
│   │                  - Sequence numbers                                     │
│   ▼                                                                         │
│                                                                             │
│  DANGER: Each layer assumes exclusive cb[] ownership!                       │
│                                                                             │
│  When qdf_nbuf passes packet to Linux stack:                                │
│  ┌─────────────────────────────────────────┐                               │
│  │ 1. qdf_nbuf sets peer_id, vdev_id in cb │                               │
│  │ 2. netif_rx(skb) called                  │                               │
│  │ 3. IP/TCP layers OVERWRITE cb[]         │  ← WLAN metadata LOST!        │
│  │ 4. Cannot access peer_id anymore         │                               │
│  └─────────────────────────────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Solutions for CB Preservation:**

```c
// Solution 1: Save metadata before passing to stack
void wlan_rx_to_stack(qdf_nbuf_t nbuf)
{
  // Save WLAN metadata we need later
  uint16_t saved_peer_id = QDF_NBUF_CB_RX_PEER_ID(nbuf);
  uint8_t saved_vdev_id = QDF_NBUF_CB_RX_VDEV_ID(nbuf);

  // Now safe to pass to stack (cb will be overwritten)
  struct sk_buff *skb = (struct sk_buff *)nbuf;
  netif_rx(skb);

  // peer_id/vdev_id in cb[] now contain garbage!
}

// Solution 2: Store in skb->sk or custom hash table
void wlan_rx_preserve_metadata(qdf_nbuf_t nbuf)
{
  struct wlan_pkt_info *info = lookup_or_create(nbuf);
  info->peer_id = QDF_NBUF_CB_RX_PEER_ID(nbuf);
  info->vdev_id = QDF_NBUF_CB_RX_VDEV_ID(nbuf);

  netif_rx((struct sk_buff *)nbuf);
}
```

### Kernel Version Compatibility Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    sk_buff Changes Across Kernel Versions                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Kernel    sk_buff Change                    qdf_nbuf Adaptation            │
│  ──────    ──────────────                    ──────────────────             │
│                                                                             │
│  3.x       cb[48] standard                   Base qdf_nbuf_cb design        │
│            head/data/tail/end pointers                                      │
│                                                                             │
│  4.0+      tail/end become offsets           qdf_nbuf macros updated        │
│            (not pointers on 64-bit)          to use skb_tail_pointer()      │
│                                                                             │
│  4.13+     refcount_t for users              No qdf_nbuf change needed      │
│            (was atomic_t)                    (uses skb_get/put APIs)        │
│                                                                             │
│  5.0+      skb_frag_t uses bio_vec           qdf_nbuf fragment APIs         │
│                                               need compatibility layer      │
│                                                                             │
│  5.4+      New GSO types added               qdf_nbuf TSO handling          │
│                                               may need updates              │
│                                                                             │
│  5.10+     XDP integration changes           Affects zero-copy paths        │
│                                                                             │
│  6.x       Ongoing structure optimizations   Continuous adaptation          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Handling sk_buff Changes in qdf_nbuf Code

#### Compile-Time Compatibility

```c
// i_qdf_nbuf.h - Linux-specific wrapper

// Handle different kernel versions
#if LINUX_VERSION_CODE >= KERNEL_VERSION(4, 0, 0)
  // tail is offset, not pointer
  #define __qdf_nbuf_tail(skb) skb_tail_pointer(skb)
#else
  // tail is pointer
  #define __qdf_nbuf_tail(skb) ((skb)->tail)
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 0, 0)
  // New fragment accessors
  #define __qdf_nbuf_frag_page(frag) skb_frag_page(frag)
#else
  // Old style
  #define __qdf_nbuf_frag_page(frag) ((frag)->page.p)
#endif
```

#### Runtime Adaptation

```c
// Some changes require runtime checks
QDF_STATUS qdf_nbuf_map_single(qdf_device_t osdev, qdf_nbuf_t buf,
                               qdf_dma_dir_t dir)
{
  struct sk_buff *skb = (struct sk_buff *)buf;
  dma_addr_t paddr;

  // DMA API may behave differently across kernels
  paddr = dma_map_single(osdev->dev, skb->data, skb->len,
                         __qdf_dma_dir_to_os(dir));

  if (dma_mapping_error(osdev->dev, paddr)) {
    // Error handling consistent across versions
    return QDF_STATUS_E_FAILURE;
  }

  // Store in CB (CB structure is version-independent)
  QDF_NBUF_CB_PADDR(skb) = paddr;

  return QDF_STATUS_SUCCESS;
}
```

### Data Flow: sk_buff Modification Propagation to qdf_nbuf

```
┌─────────────────────────────────────────────────────────────────────────────┐
│        How sk_buff Modifications Affect qdf_nbuf Operations                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Scenario: Driver modifies sk_buff, then uses qdf_nbuf API                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 1: Kernel/Driver modifies sk_buff                               │   │
│  │                                                                       │   │
│  │   struct sk_buff *skb = ...;                                          │   │
│  │   skb_pull(skb, 14);  // Remove Ethernet header                       │   │
│  │   // skb->data now points to IP header                                │   │
│  │   // skb->len reduced by 14                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                                                  │
│                          ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 2: qdf_nbuf sees the SAME modified state                        │   │
│  │                                                                       │   │
│  │   qdf_nbuf_t nbuf = (qdf_nbuf_t)skb;  // Same pointer                │   │
│  │                                                                       │   │
│  │   qdf_nbuf_data(nbuf);   // Returns IP header (not Ethernet!)        │   │
│  │   qdf_nbuf_len(nbuf);    // Returns reduced length                   │   │
│  │                                                                       │   │
│  │   // CB metadata is UNCHANGED - peer_id still valid                   │   │
│  │   QDF_NBUF_CB_RX_PEER_ID(nbuf);  // Still correct                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                                                  │
│                          ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 3: But DMA mapping may be stale!                                │   │
│  │                                                                       │   │
│  │   // DANGER: paddr in CB still points to Ethernet header!            │   │
│  │   qdf_dma_addr_t paddr = QDF_NBUF_CB_PADDR(nbuf);                    │   │
│  │   // paddr is NOW WRONG - doesn't match skb->data                    │   │
│  │                                                                       │   │
│  │   // Must remap after modifying data pointer!                         │   │
│  │   qdf_nbuf_unmap_single(osdev, nbuf, dir);                           │   │
│  │   qdf_nbuf_map_single(osdev, nbuf, dir);  // Get new paddr           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Critical Interaction Points

#### 1. RX Path: sk_buff Created by Kernel, Used by qdf_nbuf

```c
// NAPI RX callback - kernel creates skb, driver uses as qdf_nbuf
int wlan_napi_poll(struct napi_struct *napi, int budget)
{
  int processed = 0;

  while (processed < budget) {
    // Get sk_buff from hardware ring (kernel allocated)
    struct sk_buff *skb = hw_get_rx_buffer();
    if (!skb) break;

    // Cast to qdf_nbuf - MUST initialize CB first!
    qdf_nbuf_t nbuf = (qdf_nbuf_t)skb;

    // CB contains garbage from kernel allocation
    // MUST clear and populate CB before using qdf_nbuf macros
    memset(skb->cb, 0, sizeof(skb->cb));

    // Read metadata from hardware descriptor
    struct rx_desc *desc = hw_get_rx_desc();
    QDF_NBUF_CB_RX_PEER_ID(nbuf) = desc->peer_id;
    QDF_NBUF_CB_RX_VDEV_ID(nbuf) = desc->vdev_id;
    QDF_NBUF_CB_PADDR(nbuf) = desc->buf_paddr;

    // Now safe to use qdf_nbuf APIs
    process_rx_packet(nbuf);
    processed++;
  }

  return processed;
}
```

#### 2. TX Path: qdf_nbuf to sk_buff for Stack

```c
// TX completion - qdf_nbuf returns to kernel as sk_buff
void wlan_tx_complete(qdf_nbuf_t nbuf, bool success)
{
  // Unmap DMA (uses CB paddr)
  qdf_dma_addr_t paddr = QDF_NBUF_CB_PADDR(nbuf);
  qdf_nbuf_unmap_single(osdev, nbuf, QDF_DMA_TO_DEVICE);

  // Get original skb (same pointer)
  struct sk_buff *skb = (struct sk_buff *)nbuf;

  // CB is now invalid for qdf_nbuf use!
  // But skb still valid for kernel operations

  if (success) {
    // Return to stack for potential retransmit tracking
    dev_consume_skb_any(skb);
  } else {
    // Free on error
    dev_kfree_skb_any(skb);
  }
}
```

#### 3. Intra-BSS Forwarding: Mixed Usage

```c
// Packet received on one VAP, forwarded on another
QDF_STATUS wlan_intrabss_fwd(qdf_nbuf_t rx_nbuf, uint8_t dst_vdev_id)
{
  // RX metadata in CB
  uint16_t src_peer = QDF_NBUF_CB_RX_PEER_ID(rx_nbuf);
  uint8_t src_vdev = QDF_NBUF_CB_RX_VDEV_ID(rx_nbuf);

  // Clone for forwarding (sk_buff clone, but used as qdf_nbuf)
  qdf_nbuf_t fwd_nbuf = qdf_nbuf_clone(rx_nbuf);
  if (!fwd_nbuf) {
    return QDF_STATUS_E_NOMEM;
  }

  // Clone shares data, but has SEPARATE CB!
  // Must initialize forwarding CB
  QDF_NBUF_CB_TX_FTYPE(fwd_nbuf) = CB_FTYPE_INTRABSS_FWD;

  // Map for TX DMA (RX paddr is for different direction!)
  qdf_nbuf_map_single(osdev, fwd_nbuf, QDF_DMA_TO_DEVICE);

  // Queue for TX
  wlan_tx_enqueue(fwd_nbuf, dst_vdev_id);

  // Original continues up RX path
  wlan_rx_deliver(rx_nbuf, src_vdev);

  return QDF_STATUS_SUCCESS;
}
```

### Debugging sk_buff/qdf_nbuf Interaction Issues

```c
// Debug helper to verify sk_buff and qdf_nbuf consistency
void debug_nbuf_skb_state(qdf_nbuf_t nbuf, const char *context)
{
  struct sk_buff *skb = (struct sk_buff *)nbuf;

  qdf_print("=== %s ===\n", context);
  qdf_print("Pointer: skb=%pK nbuf=%pK (same=%d)\n",
            skb, nbuf, (void*)skb == (void*)nbuf);

  // sk_buff fields
  qdf_print("sk_buff: head=%pK data=%pK tail=%u end=%u\n",
            skb->head, skb->data, skb->tail, skb->end);
  qdf_print("sk_buff: len=%u data_len=%u users=%d\n",
            skb->len, skb->data_len, refcount_read(&skb->users));

  // qdf_nbuf view (should match!)
  qdf_print("qdf_nbuf: data=%pK len=%u\n",
            qdf_nbuf_data(nbuf), qdf_nbuf_len(nbuf));
  qdf_print("qdf_nbuf: headroom=%u tailroom=%u\n",
            qdf_nbuf_headroom(nbuf), qdf_nbuf_tailroom(nbuf));

  // CB state
  qdf_print("CB: paddr=%llx peer_id=%u vdev_id=%u\n",
            QDF_NBUF_CB_PADDR(nbuf),
            QDF_NBUF_CB_RX_PEER_ID(nbuf),
            QDF_NBUF_CB_RX_VDEV_ID(nbuf));
}
```

### Summary: sk_buff Change Impact on qdf_nbuf

| sk_buff Aspect | How qdf_nbuf Interacts | Impact of Changes |
|----------------|------------------------|-------------------|
| Structure size | Direct typedef | Compilation compatibility |
| cb[48] array | Overlays qdf_nbuf_cb | Must fit; preserved within driver only |
| Data pointers | Wrapped by qdf_nbuf_data/len | Automatic propagation |
| Reference count | Wrapped by qdf_nbuf_ref/free | Semantic compatibility |
| DMA mapping | Stored in CB paddr | Must sync after data pointer changes |
| Fragments | Wrapped with version checks | Kernel version adaptation |
| Clone/Copy | Same semantics | CB separation on clone |
| Queue operations | Wrapped by qdf_nbuf_queue | Automatic compatibility |

---

## References

### Linux Kernel Documentation
- `Documentation/networking/skbuff.rst` - sk_buff documentation
- `include/linux/skbuff.h` - sk_buff structure definition

### QDF Source Files
- `qdf/inc/qdf_nbuf.h` - Public qdf_nbuf API
- `qdf/linux/src/i_qdf_nbuf.h` - Linux-specific implementation
- `qdf/linux/src/i_qdf_nbuf_m.h` - CB structure definition
- `qdf/linux/src/qdf_nbuf.c` - Implementation

### Related Documentation
- `docs/wlan_drivers_terminology.md` - WLAN driver concepts
- `docs/osi_layers_packet_flow.md` - Packet encapsulation
- `docs/c_language_for_systems_programming.md` - C concepts for drivers
```

