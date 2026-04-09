# Chapter 4: Cloning, Copying, and Expanding

The Linux networking stack frequently encounters situations where a single packet
must be delivered to multiple consumers, where headers must be modified without
disturbing the original payload, or where buffer space must be enlarged to
accommodate encapsulation. This chapter provides an exhaustive treatment of the
kernel APIs that address these requirements: `skb_clone()`, `skb_copy()`,
`pskb_copy()`, `skb_cow()`, and the family of expansion functions. Understanding
these operations is essential for anyone writing network drivers, protocol
handlers, or packet-processing modules.

---

## 1. Why Clone and Copy?

### 1.1 The Fundamental Problem

A packet traversing the Linux network stack is represented by a single `sk_buff`
structure and its associated data buffer. However, the stack frequently needs
to present the same packet data to multiple independent consumers, each of which
may have different requirements regarding mutability and lifetime.

Consider the following scenarios:

1. **Packet sniffing (AF_PACKET / tcpdump):** When a raw socket is listening
   on an interface, every incoming packet must be delivered both to the normal
   protocol stack and to the raw socket. The raw socket needs its own reference
   to the packet, but copying 1500 bytes of payload for every packet would be
   prohibitively expensive on a 10 Gbps link.

2. **Multicast forwarding:** A single multicast packet arriving on one interface
   may need to be forwarded out of N interfaces simultaneously. Each egress path
   may modify L2 headers independently.

3. **Netfilter and connection tracking:** The NAT subsystem must rewrite IP
   addresses and port numbers in packet headers, but it receives the same
   `sk_buff` that other subsystems (logging, accounting) may still reference.

4. **TCP retransmission:** The TCP stack keeps `sk_buff` structures in the
   retransmit queue. When retransmitting, it must send a copy without removing
   the original from the queue.

5. **Tunnel encapsulation (VXLAN, GRE, GENEVE):** Encapsulating a packet
   requires prepending new headers, which demands additional headroom that the
   original buffer may not possess.

### 1.2 The Cost Spectrum

Different operations occupy different points on the performance spectrum:

```
  Cost Spectrum of sk_buff Duplication
  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   Cheapest                                              Most        │
  │   ◄────────────────────────────────────────────────────► Expensive  │
  │                                                                     │
  │   skb_clone    skb_cow    pskb_copy    skb_copy_expand   skb_copy  │
  │   (~232 B)     (conditional) (head only)  (head+tail)    (full)    │
  │                                                                     │
  │   Share all    Unshare    Copy head,   Full copy with    Full copy  │
  │   data         head if    share frags  new head/tail     + linearize│
  │                needed                                               │
  └─────────────────────────────────────────────────────────────────────┘
```

### 1.3 The Guiding Principle

The kernel follows a strict principle: **share as much as possible, copy only
what must be modified.** This is a form of copy-on-write applied to network
buffers. The APIs are designed so that:

- If you only need to read the data, use `skb_clone()`.
- If you need to modify headers but not payload, use `pskb_copy()` or
  `skb_cow()`.
- If you need to modify everything, use `skb_copy()`.
- If you need more buffer space, use the expansion functions.

### 1.4 Shared State vs. Independent State

When an `sk_buff` is cloned, the following state is shared versus independent:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    State Ownership Table                         │
  ├──────────────────────┬────────────────┬─────────────────────────┤
  │  Field               │  Clone         │  Full Copy              │
  ├──────────────────────┼────────────────┼─────────────────────────┤
  │  sk_buff struct      │  Independent   │  Independent            │
  │  sk (socket pointer) │  Independent   │  Independent            │
  │  dev (net_device)    │  Independent   │  Independent            │
  │  cb[] (control buf)  │  Independent   │  Independent            │
  │  head/data/tail/end  │  SHARED        │  Independent            │
  │  Linear data area    │  SHARED        │  Independent (copied)   │
  │  Paged fragments     │  SHARED        │  Independent (copied)   │
  │  skb_shared_info     │  SHARED        │  Independent            │
  │  dataref count       │  Incremented   │  Fresh (= 1)            │
  │  destructor          │  NULL on clone │  NULL on copy           │
  └──────────────────────┴────────────────┴─────────────────────────┘
```

---

## 2. skb_clone(skb, gfp_mask)

### 2.1 Overview

`skb_clone()` is the fastest way to create a second reference to a packet. It
allocates only a new `sk_buff` structure (approximately 232 bytes on a 64-bit
kernel) and points it at the same data buffer as the original. The data buffer's
reference count (`dataref` in `skb_shared_info`) is incremented atomically to
track the sharing.

```c
/**
 * skb_clone - duplicate an sk_buff
 * @skb: buffer to clone
 * @gfp_mask: allocation priority
 *
 * Duplicate an &sk_buff. The new one is not owned by any socket.
 * Both copies share the same packet data but the clone has its
 * own sk_buff structure. The new buffer's reference count is set
 * to 1. The clone's destructor is set to NULL.
 *
 * If there is room at the end of the buffer, the skb_shared_info
 * structure is shared (dataref is incremented). Neither the
 * original nor the clone may modify the data until they unshare it.
 */
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask)
{
    struct sk_buff *n;

    /* Fast path: try to allocate from the sk_buff cache */
    n = skb + 1;  /* simplified — actual code uses kmem_cache_alloc() */
    if (skb->fclone == SKB_FCLONE_ORIG &&
        refcount_read(&fclone->fclone_ref) == 1) {
        /* Use the pre-allocated fclone companion */
        n = skb + 1;
        n->fclone = SKB_FCLONE_CLONE;
        refcount_set(&fclone->fclone_ref, 2);
    } else {
        /* Allocate a fresh sk_buff from the slab cache */
        n = kmem_cache_alloc(skbuff_cache, gfp_mask);
        if (!n)
            return NULL;
        n->fclone = SKB_FCLONE_UNAVAILABLE;
    }

    return __skb_clone(n, skb);  /* Copy metadata, share data */
}
```

### 2.2 The __skb_clone() Helper

The actual metadata copying happens in `__skb_clone()`:

```c
static struct sk_buff *__skb_clone(struct sk_buff *n, struct sk_buff *skb)
{
    /* Copy the sk_buff structure fields */
    n->next = n->prev = NULL;
    n->sk = NULL;               /* clone has no socket ownership */

    /* Share the data pointers */
    n->head     = skb->head;    /* same buffer start               */
    n->data     = skb->data;    /* same data start                 */
    n->tail     = skb->tail;    /* same data end                   */
    n->end      = skb->end;     /* same buffer end                 */

    /* Copy transport/network/mac header offsets */
    n->transport_header = skb->transport_header;
    n->network_header   = skb->network_header;
    n->mac_header       = skb->mac_header;

    /* Mark both as cloned */
    n->cloned = 1;
    skb->cloned = 1;

    /* Increment the data reference count */
    atomic_inc(&(skb_shinfo(skb)->dataref));

    /* Copy control buffer (independent per-clone) */
    memcpy(n->cb, skb->cb, sizeof(skb->cb));

    /* Copy protocol, priority, queue mapping, etc. */
    n->protocol = skb->protocol;
    n->priority = skb->priority;
    n->queue_mapping = skb->queue_mapping;

    /* The clone does NOT inherit the destructor */
    n->destructor = NULL;

    /* Set own reference count to 1 */
    refcount_set(&n->users, 1);

    return n;
}
```

### 2.3 Memory Layout After Cloning

The following diagram illustrates the memory relationships after
`clone = skb_clone(original, GFP_ATOMIC)`:

```
  Original sk_buff                       Clone sk_buff
  ┌──────────────────┐                   ┌──────────────────┐
  │ users    = 1     │                   │ users    = 1     │
  │ cloned   = 1     │                   │ cloned   = 1     │
  │ fclone   = ORIG  │                   │ fclone   = CLONE │
  │ sk       = sock* │                   │ sk       = NULL  │
  │ destructor = fn  │                   │ destructor= NULL │
  │                  │                   │                  │
  │ head ────────────┼───┐         ┌─────┼──────── head     │
  │ data ────────────┼───┼────┐    │┌────┼──────── data     │
  │ tail ────────────┼───┼────┼────┼┼────┼──────── tail     │
  │ end  ────────────┼───┼────┼────┼┼────┼──────── end      │
  │                  │   │    │    ││    │                  │
  │ transport_header │   │    │    ││    │ transport_header │
  │ network_header   │   │    │    ││    │ network_header   │
  │ mac_header       │   │    │    ││    │ mac_header       │
  │ cb[48] (indep.)  │   │    │    ││    │ cb[48] (indep.)  │
  └──────────────────┘   │    │    ││    └──────────────────┘
                         │    │    ││
                         ▼    ▼    ▼▼
                   ┌─────────────────────────┐
                   │  head                   │  ◄── buffer start
                   │  ┌─ ─ ─ ─ ─ ─ ─ ─ ─┐  │
                   │    headroom (unused)    │
                   │  └─ ─ ─ ─ ─ ─ ─ ─ ─┘  │
                   │  data                   │  ◄── packet data start
                   │  ┌─────────────────────┐│
                   │  │ L2 Header           ││
                   │  ├─────────────────────┤│
                   │  │ L3 Header (IP)      ││
                   │  ├─────────────────────┤│
                   │  │ L4 Header (TCP/UDP) ││
                   │  ├─────────────────────┤│
                   │  │ Payload             ││
                   │  └─────────────────────┘│
                   │  tail                   │  ◄── packet data end
                   │  ┌─ ─ ─ ─ ─ ─ ─ ─ ─┐  │
                   │    tailroom (unused)    │
                   │  └─ ─ ─ ─ ─ ─ ─ ─ ─┘  │
                   │  end                    │  ◄── buffer end
                   ├─────────────────────────┤
                   │  skb_shared_info        │
                   │  ┌─────────────────────┐│
                   │  │ dataref = 2         ││  ◄── shared by both
                   │  │ nr_frags            ││
                   │  │ frag_list           ││
                   │  │ frags[]             ││
                   │  └─────────────────────┘│
                   └─────────────────────────┘
```

### 2.4 The fclone Optimization

The kernel provides an optimization for the common clone pattern. When a
subsystem knows that a packet will very likely be cloned exactly once (the
common case for packet capture), it can allocate a "fast clone" pair:

```c
/* Three fclone states */
enum {
    SKB_FCLONE_UNAVAILABLE, /* Normal sk_buff, no companion     */
    SKB_FCLONE_ORIG,        /* Original of an fclone pair       */
    SKB_FCLONE_CLONE,       /* Clone companion of an fclone pair*/
};
```

When `__alloc_skb()` is called with `SKB_ALLOC_FCLONE`, it allocates space for
**two** `sk_buff` structures contiguously. The second one sits dormant until
`skb_clone()` is called, at which point it is activated without any
`kmem_cache_alloc()` call:

```
  fclone allocation layout
  ┌──────────────────────────────────┐
  │  sk_buff #1 (ORIG)               │  ◄── returned to caller
  │  fclone = SKB_FCLONE_ORIG        │
  ├──────────────────────────────────┤
  │  sk_buff #2 (dormant CLONE)      │  ◄── used by skb_clone()
  │  fclone = SKB_FCLONE_CLONE       │
  ├──────────────────────────────────┤
  │  struct sk_buff_fclones          │
  │  ┌──────────────────────────────┐│
  │  │  fclone_ref = 1 (→ 2)       ││
  │  └──────────────────────────────┘│
  └──────────────────────────────────┘
```

This saves one slab allocation per clone, which is significant under load.

### 2.5 Constraints on Cloned Buffers

After cloning, **neither** the original nor the clone may modify the shared
data buffer. Any attempt to write to the data area may corrupt the view of the
other user. The kernel enforces this discipline through the `skb_cloned()` check:

```c
static inline int skb_cloned(const struct sk_buff *skb)
{
    return skb->cloned &&
           (atomic_read(&skb_shinfo(skb)->dataref) & SKB_DATAREF_MASK) != 1;
}
```

Before modifying data, code must check `skb_cloned()` and, if true, must
unshare the data by calling one of the copy or cow functions described in the
following sections.

### 2.6 Lifecycle of a Cloned sk_buff

```
  Timeline of a clone lifecycle
  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  1. skb_clone(original)                                          │
  │     ├── Allocate clone sk_buff                                   │
  │     ├── Copy metadata (head, data, tail, end, headers, cb)       │
  │     ├── Set original->cloned = 1                                 │
  │     ├── Set clone->cloned = 1                                    │
  │     ├── atomic_inc(dataref)  →  dataref becomes 2                │
  │     └── Return clone                                             │
  │                                                                  │
  │  2. Both can READ the shared data freely                         │
  │     ├── original: read head..tail  ✓                             │
  │     └── clone:    read head..tail  ✓                             │
  │                                                                  │
  │  3. Before WRITING, must unshare:                                │
  │     ├── pskb_copy() or skb_copy() or pskb_expand_head()         │
  │     └── After unshare: dataref decremented for old, new = 1     │
  │                                                                  │
  │  4. kfree_skb(clone)                                             │
  │     ├── decrement clone->users  →  0                             │
  │     ├── __kfree_skb(clone)                                       │
  │     │   ├── skb_release_data()                                   │
  │     │   │   └── atomic_dec(dataref)  →  dataref becomes 1       │
  │     │   │       (data NOT freed: still in use by original)       │
  │     │   └── Free the clone sk_buff struct                        │
  │     └── original->cloned can now be 0  (if dataref == 1)        │
  │                                                                  │
  │  5. kfree_skb(original)                                          │
  │     ├── decrement original->users  →  0                          │
  │     ├── __kfree_skb(original)                                    │
  │     │   ├── skb_release_data()                                   │
  │     │   │   └── atomic_dec(dataref)  →  0                       │
  │     │   │       Data buffer is FREED                             │
  │     │   └── Free the original sk_buff struct                     │
  │     └── All memory released                                      │
  └──────────────────────────────────────────────────────────────────┘
```

### 2.7 Performance Characteristics

| Metric                      | Value (approximate)        |
|-----------------------------|----------------------------|
| Allocation size             | ~232 bytes (sk_buff only)  |
| Time complexity             | O(1)                       |
| Data buffer copy            | None                       |
| Fragment handling            | None (shared)              |
| Cache impact                | Minimal (single alloc)     |
| Safe for parallel readers   | Yes                        |
| Safe for parallel writers   | No (must unshare first)    |
| Atomic operations           | 1 (dataref increment)      |

---

## 3. skb_copy(skb, gfp_mask)

### 3.1 Overview

`skb_copy()` produces a completely independent copy of an `sk_buff`. It
allocates a new `sk_buff` structure **and** a new data buffer, then copies all
data -- including paged fragments and the frag_list chain -- into a single
contiguous (linear) buffer. The result is a fully self-contained sk_buff with
no shared state.

```c
/**
 * skb_copy - create a private copy of an sk_buff
 * @skb: buffer to copy
 * @gfp_mask: allocation priority
 *
 * Make a copy of both an &sk_buff and its data. This is used when
 * the caller wishes to modify data and needs a completely private
 * copy of the buffer to work with. The returned sk_buff is fully
 * linear — all fragments have been pulled into the linear area.
 */
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t gfp_mask)
{
    struct sk_buff *n;
    int headerlen = skb_headroom(skb);
    int total_len  = skb->len;  /* includes fragments */

    /*
     * Allocate new sk_buff with enough linear room for ALL data
     * (linear + paged + frag_list), plus the original headroom.
     */
    n = __alloc_skb(total_len + headerlen, gfp_mask,
                    skb_alloc_rx_flag(skb), NUMA_NO_NODE);
    if (!n)
        return NULL;

    /* Reserve the same headroom as the original */
    skb_reserve(n, headerlen);

    /* Set the data length (will be 0 — all linear) */
    skb_put(n, total_len);

    /*
     * Copy ALL data: linear area, paged fragments, and frag_list
     * into the new linear buffer. This linearizes the packet.
     */
    if (skb_copy_bits(skb, 0, n->data, total_len)) {
        kfree_skb(n);
        return NULL;
    }

    /* Copy metadata: headers, protocol, priority, marks, etc. */
    copy_skb_header(n, skb);

    return n;
}
```

### 3.2 Linearization During Copy

A key property of `skb_copy()` is that it **linearizes** the data. If the
original sk_buff had paged fragments or a frag_list, all of that data is pulled
into a single contiguous linear buffer. This makes the copy easier to work with
but potentially requires a very large allocation.

```
  Before skb_copy():

  Original sk_buff
  ┌──────────────────┐
  │ len = 2800       │
  │ data_len = 2048  │   ◄── 2048 bytes in fragments
  │ head ─────────┐  │
  │ data ─────────┤  │
  │ tail ─────────┤  │
  │ end  ─────────┤  │
  └───────────────┼──┘
                  │
                  ▼
    ┌──────────────────┐
    │ Linear: 752 B    │   ◄── headers + partial payload
    ├──────────────────┤
    │ skb_shared_info   │
    │  nr_frags = 2     │
    │  frags[0] ────────┼───► Page A (1024 B)
    │  frags[1] ────────┼───► Page B (1024 B)
    └──────────────────┘

  After skb_copy():

  New sk_buff (copy)
  ┌──────────────────┐
  │ len = 2800       │
  │ data_len = 0     │   ◄── fully linear now
  │ head ─────────┐  │
  │ data ─────────┤  │
  │ tail ─────────┤  │
  │ end  ─────────┤  │
  └───────────────┼──┘
                  │
                  ▼
    ┌──────────────────┐
    │ Linear: 2800 B   │   ◄── ALL data contiguous
    │ ┌──────────────┐ │
    │ │ Headers      │ │   ◄── copied from linear area
    │ ├──────────────┤ │
    │ │ Payload (A)  │ │   ◄── copied from frags[0]
    │ ├──────────────┤ │
    │ │ Payload (B)  │ │   ◄── copied from frags[1]
    │ └──────────────┘ │
    ├──────────────────┤
    │ skb_shared_info   │
    │  nr_frags = 0     │   ◄── no fragments
    │  dataref  = 1     │   ◄── independent
    └──────────────────┘
```

### 3.3 The skb_copy_bits() Workhorse

`skb_copy_bits()` is the function that handles copying data from a potentially
fragmented sk_buff into a flat buffer. It walks the linear area, then paged
fragments, then the frag_list:

```c
int skb_copy_bits(const struct sk_buff *skb, int offset,
                  void *to, int len)
{
    int start = skb_headlen(skb);  /* linear data length */
    int i, copy;

    /* 1. Copy from the linear area */
    if ((copy = start - offset) > 0) {
        if (copy > len)
            copy = len;
        memcpy(to, skb->data + offset, copy);
        if ((len -= copy) == 0)
            return 0;
        offset += copy;
        to     += copy;
    }

    /* 2. Copy from paged fragments (frags[]) */
    for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
        skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
        int end = start + skb_frag_size(frag);

        if ((copy = end - offset) > 0) {
            u8 *vaddr;
            if (copy > len)
                copy = len;
            vaddr = kmap_atomic(skb_frag_page(frag));
            memcpy(to, vaddr + skb_frag_off(frag) + offset - start, copy);
            kunmap_atomic(vaddr);
            if ((len -= copy) == 0)
                return 0;
            offset += copy;
            to     += copy;
        }
        start = end;
    }

    /* 3. Copy from frag_list (chained sk_buffs) */
    skb_walk_frags(skb, frag_iter) {
        /* Recursive: each frag_list entry is itself an sk_buff */
        int end = start + frag_iter->len;
        if ((copy = end - offset) > 0) {
            if (copy > len)
                copy = len;
            if (skb_copy_bits(frag_iter, offset - start, to, copy))
                return -EFAULT;
            if ((len -= copy) == 0)
                return 0;
            offset += copy;
            to     += copy;
        }
        start = end;
    }

    if (len)
        return -EFAULT;  /* should not happen */
    return 0;
}
```

### 3.4 The copy_skb_header() Helper

After the data is copied, `copy_skb_header()` transfers all the metadata from
the original to the new sk_buff:

```c
static void copy_skb_header(struct sk_buff *new, const struct sk_buff *old)
{
    /* Copy header offsets — adjusted for the new buffer */
    new->transport_header = old->transport_header;
    new->network_header   = old->network_header;
    new->mac_header       = old->mac_header;

    /* Copy protocol stack metadata */
    new->protocol      = old->protocol;
    new->priority      = old->priority;
    new->mark          = old->mark;
    new->vlan_proto    = old->vlan_proto;
    new->vlan_tci      = old->vlan_tci;
    new->queue_mapping = old->queue_mapping;
    new->nf_trace      = old->nf_trace;
    new->pkt_type      = old->pkt_type;
    new->ip_summed     = old->ip_summed;
    new->csum          = old->csum;

    /* The new sk_buff is NOT cloned */
    new->cloned = 0;

    /* Independent reference count */
    refcount_set(&new->users, 1);

    /* Copy the control buffer (cb) */
    memcpy(new->cb, old->cb, sizeof(old->cb));

    /* Timestamp */
    new->tstamp = old->tstamp;

    /* NOTE: destructor is NOT copied */
    new->destructor = NULL;

    /* NOTE: sk (socket) pointer is NOT transferred */
    new->sk = NULL;
}
```

### 3.5 When to Use skb_copy()

Use `skb_copy()` when:

- You need a fully independent packet that can be modified freely.
- The data will be modified at arbitrary offsets (not just headers).
- You need a linear buffer for a protocol parser that cannot handle fragments.
- The copy will outlive the original significantly.

**Do not** use `skb_copy()` when:
- Only header modifications are needed (use `pskb_copy()` or `skb_cow()`).
- You only need a second reference for reading (use `skb_clone()`).
- The packet is very large and copying is wasteful.

### 3.6 Performance Characteristics

| Metric                    | Value                            |
|---------------------------|----------------------------------|
| Allocation size           | sk_buff + full data length       |
| Time complexity           | O(n) where n = total data length |
| Data buffer copy          | Complete (linear + frags + list) |
| Fragment handling          | Linearized into copy             |
| Resulting nr_frags        | 0                                |
| Resulting data_len        | 0                                |
| Cache impact              | High (touches all data pages)    |
| Safe for modification     | Yes (fully independent)          |

---

## 4. pskb_copy(skb, gfp_mask)

### 4.1 Overview

`pskb_copy()` stands for "partial sk_buff copy." It occupies the middle ground
between `skb_clone()` (share everything) and `skb_copy()` (copy everything).
Specifically, it:

1. Allocates a new `sk_buff` structure.
2. Allocates a new linear data buffer and copies the linear data (headers).
3. **Shares** the paged fragment pages via page reference counting.

This allows the caller to modify headers independently while still sharing the
(usually much larger) payload pages.

```c
/**
 * pskb_copy - create a partial copy of an sk_buff
 * @skb: buffer to copy
 * @gfp_mask: allocation priority
 *
 * Creates a copy of an &sk_buff with a new linear buffer.
 * The linear data is copied but paged fragments are shared
 * (their reference counts are incremented). This is useful
 * when you need to modify headers but not payload.
 */
struct sk_buff *pskb_copy(struct sk_buff *skb, gfp_t gfp_mask)
{
    struct sk_buff *n;
    int headerlen = skb_headroom(skb);
    int size      = skb_end_offset(skb);  /* linear buffer size */

    /* Allocate sk_buff + linear buffer (same size as original) */
    n = __alloc_skb(size, gfp_mask,
                    skb_alloc_rx_flag(skb), NUMA_NO_NODE);
    if (!n)
        return NULL;

    /* Reserve the same headroom */
    skb_reserve(n, headerlen);

    /* Copy the linear data */
    skb_put(n, skb_headlen(skb));
    memcpy(n->data, skb->data, skb_headlen(skb));

    /* data_len remains the same: still referencing paged data */
    n->data_len = skb->data_len;
    n->len      = skb->len;

    /* Share the paged fragments: increment page references */
    if (skb_shinfo(skb)->nr_frags) {
        int i;
        for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
            skb_shinfo(n)->frags[i] = skb_shinfo(skb)->frags[i];
            skb_frag_ref(skb, i);   /* get_page() on the frag page */
        }
        skb_shinfo(n)->nr_frags = skb_shinfo(skb)->nr_frags;
    }

    /* Share or copy the frag_list */
    if (skb_has_frag_list(skb)) {
        skb_shinfo(n)->frag_list = skb_shinfo(skb)->frag_list;
        skb_clone_fraglist(skb);  /* increment refcounts */
    }

    /* Copy metadata */
    copy_skb_header(n, skb);

    return n;
}
```

### 4.2 Memory Layout After pskb_copy()

```
  Original sk_buff                       Copy (pskb_copy)
  ┌──────────────────┐                   ┌──────────────────┐
  │ len = 2800       │                   │ len = 2800       │
  │ data_len = 2048  │                   │ data_len = 2048  │
  │ cloned = 1       │                   │ cloned = 0       │
  └──────┬───────────┘                   └──────┬───────────┘
         │                                      │
         ▼                                      ▼
  ┌──────────────┐                       ┌──────────────┐
  │ Linear: 752B │ ◄── ORIGINAL          │ Linear: 752B │ ◄── COPIED
  │ ┌──────────┐ │     buffer            │ ┌──────────┐ │    (independent)
  │ │ Headers  │ │                       │ │ Headers  │ │
  │ │ (can't   │ │                       │ │ (CAN     │ │
  │ │  modify) │ │                       │ │  modify) │ │
  │ └──────────┘ │                       │ └──────────┘ │
  ├──────────────┤                       ├──────────────┤
  │shared_info   │                       │shared_info   │
  │ dataref = 2  │                       │ dataref = 1  │  ◄── own buffer
  │ nr_frags = 2 │                       │ nr_frags = 2 │
  │ frags[0] ────┼───┐              ┌────┼── frags[0]   │
  │ frags[1] ────┼─┐ │              │ ┌──┼── frags[1]   │
  └──────────────┘ │ │              │ │  └──────────────┘
                   │ │              │ │
                   │ └──────┬───────┘ │
                   │        ▼         │
                   │  ┌───────────┐   │
                   │  │  Page A   │   │    SHARED (page refcount
                   │  │  1024 B   │   │    incremented)
                   │  │  refcnt=2 │   │
                   │  └───────────┘   │
                   │                  │
                   └──────┬───────────┘
                          ▼
                    ┌───────────┐
                    │  Page B   │          SHARED (page refcount
                    │  1024 B   │          incremented)
                    │  refcnt=2 │
                    └───────────┘
```

### 4.3 Key Properties

1. **Linear area is independent:** The copy can freely modify any data in the
   linear area (typically containing L2/L3/L4 headers).

2. **Fragments are shared:** Paged fragment pages have their reference counts
   incremented. Neither the original nor the copy should modify fragment data
   without first taking their own copy of the relevant pages.

3. **The new sk_buff is NOT cloned:** Since it has its own linear buffer with
   `dataref = 1`, `skb_cloned()` returns false for the copy.

4. **The original remains as before:** If it was already cloned (shared), it
   stays cloned. The `pskb_copy()` operation does not alter the original's
   cloned state.

### 4.4 Comparison: skb_clone vs. pskb_copy vs. skb_copy

```
  ┌─────────────────┬───────────────────┬───────────────────┬───────────────────┐
  │  Property        │  skb_clone()      │  pskb_copy()      │  skb_copy()       │
  ├─────────────────┼───────────────────┼───────────────────┼───────────────────┤
  │  sk_buff struct  │  New (independent)│  New (independent)│  New (independent)│
  │  Linear buffer   │  SHARED           │  COPIED           │  COPIED           │
  │  Paged frags     │  SHARED           │  SHARED (ref'd)   │  COPIED (linear.) │
  │  frag_list       │  SHARED           │  SHARED (ref'd)   │  COPIED (linear.) │
  │  Can modify head │  NO               │  YES              │  YES              │
  │  Can modify data │  NO               │  NO (frags)       │  YES (all)        │
  │  Allocation cost │  ~232 B           │  ~232 B + headlen │  ~232 B + totallen│
  │  Copy cost       │  O(1)             │  O(headlen)       │  O(totallen)      │
  │  Result linear?  │  Same as orig     │  Same as orig     │  Fully linear     │
  └─────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

### 4.5 When to Use pskb_copy()

The primary use case for `pskb_copy()` is when a subsystem needs to modify
packet headers while preserving the payload. Common scenarios include:

- **NAT:** Rewriting IP addresses and ports requires modifying the IP and
  TCP/UDP headers (in the linear area) but not the payload.
- **TTL decrement:** Forwarding code must decrement the IP TTL, which is in
  the linear area.
- **VLAN tag insertion/removal:** VLAN tags are in the linear header area.
- **Checksum recalculation:** After header modification, checksums must be
  updated, but the payload data used for checksum calculation can still be
  read from shared pages.

---

## 5. skb_cow(skb, headroom)

### 5.1 Overview

`skb_cow()` implements copy-on-write semantics for sk_buff headers. The name
stands for "Copy On Write." Its contract is:

> Ensure that the sk_buff has at least `headroom` bytes of writable space
> before `skb->data`. If the buffer is shared (cloned) or lacks sufficient
> headroom, make a private copy of the head area.

This is the function most commonly used by protocol handlers before they
modify headers on a packet that might be shared.

```c
/**
 * skb_cow - copy header of an sk_buff when it is cloned
 * @skb: buffer to cow
 * @headroom: needed headroom
 *
 * If the sk_buff is cloned, or if there is not enough headroom,
 * the linear buffer is replaced with a private copy that has
 * at least @headroom bytes of space before skb->data.
 *
 * Returns 0 on success, -ENOMEM on allocation failure.
 *
 * NOTE: This may reallocate the buffer. Pointers derived from
 * skb->head, skb->data, etc. are INVALIDATED after this call.
 */
static inline int skb_cow(struct sk_buff *skb, unsigned int headroom)
{
    /* Calculate the delta between desired and available headroom */
    int delta = headroom - skb_headroom(skb);

    if (delta < 0)
        delta = 0;

    /*
     * If the buffer is shared (cloned) OR we need more headroom,
     * reallocate. pskb_expand_head() will unshare and/or expand.
     */
    if (delta || skb_cloned(skb))
        return pskb_expand_head(skb, ALIGN(delta, NET_SKB_PAD), 0,
                                GFP_ATOMIC);
    return 0;
}
```

### 5.2 Decision Flow

```
  skb_cow(skb, headroom)
  ┌───────────────────────────┐
  │  Is skb_cloned(skb)?      │
  │  OR headroom insufficient?│
  └─────────┬─────────────────┘
            │
       ┌────┴────┐
       │         │
      YES        NO
       │         │
       ▼         ▼
  ┌────────────┐ ┌──────────────────┐
  │ Call        │ │ Do nothing.      │
  │ pskb_expand │ │ Buffer is already│
  │ _head()     │ │ writable with    │
  │             │ │ enough headroom. │
  │ - Allocate  │ │                  │
  │   new buffer│ │ Return 0.        │
  │ - Copy head │ └──────────────────┘
  │ - Unshare   │
  │   (dataref  │
  │    drops)   │
  │ - Update    │
  │   pointers  │
  │ Return 0    │
  │ or -ENOMEM  │
  └─────────────┘
```

### 5.3 Typical Usage Pattern

```c
/*
 * Example: Decrementing TTL during IP forwarding.
 * The sk_buff may be cloned (e.g., for packet capture),
 * so we must ensure we have a writable copy of the IP header.
 */
int ip_forward(struct sk_buff *skb)
{
    struct iphdr *iph;

    /*
     * Ensure writable headers. We need at least LL_RESERVED_SPACE(dev)
     * bytes of headroom for the output device's link-layer header.
     */
    if (skb_cow(skb, LL_RESERVED_SPACE(skb->dev))) {
        kfree_skb(skb);
        return NET_RX_DROP;
    }

    /*
     * NOW it is safe to get a pointer to the IP header and modify it.
     * skb->data may have moved due to reallocation, so we must
     * re-derive all pointers AFTER skb_cow().
     */
    iph = ip_hdr(skb);
    ip_decrease_ttl(iph);       /* safe: header is now private */

    /* Recalculate IP checksum */
    ip_send_check(iph);

    /* Forward the packet */
    return ip_forward_finish(skb);
}
```

### 5.4 Pointer Invalidation Warning

A critical subtlety: after `skb_cow()` (or any call that may reallocate the
buffer), **all cached pointers into the data buffer are invalidated.** The
`head`, `data`, `tail`, and `end` pointers in the sk_buff are updated, but
any local variables holding addresses derived from the old buffer are now
dangling.

```c
/* WRONG — dangling pointer after skb_cow() */
struct iphdr *iph = ip_hdr(skb);   /* pointer into old buffer */
skb_cow(skb, headroom);            /* buffer may be reallocated */
iph->ttl--;                        /* BUG: iph may point to freed memory */

/* CORRECT — re-derive pointer after skb_cow() */
skb_cow(skb, headroom);            /* buffer may be reallocated */
struct iphdr *iph = ip_hdr(skb);   /* pointer into new buffer */
iph->ttl--;                        /* safe */
```

### 5.5 Before and After skb_cow() on a Cloned Buffer

```
  BEFORE: skb is a clone sharing data with the original

  Clone sk_buff                    Original sk_buff
  ┌──────────────┐                ┌──────────────┐
  │ cloned = 1   │                │ cloned = 1   │
  │ head ────────┼───┐       ┌────┼── head       │
  │ data ────────┼───┼───┐   │┌───┼── data       │
  └──────────────┘   │   │   ││   └──────────────┘
                     ▼   ▼   ▼▼
               ┌───────────────────┐
               │  Shared Buffer     │
               │  dataref = 2       │
               └───────────────────┘

  AFTER: skb_cow(clone, headroom) succeeds

  Clone sk_buff                    Original sk_buff
  ┌──────────────┐                ┌──────────────┐
  │ cloned = 0   │  ◄── unshared │ cloned = 0   │ ◄── if no other clones
  │ head ────────┼───┐            │ head ────────┼───┐
  │ data ────────┼───┤            │ data ────────┼───┤
  └──────────────┘   │            └──────────────┘   │
                     ▼                               ▼
         ┌──────────────────┐             ┌───────────────────┐
         │  NEW Private Buf  │             │  Original Buffer   │
         │  dataref = 1      │             │  dataref = 1       │
         │  (headers copied) │             │  (unchanged)       │
         └──────────────────┘             └───────────────────┘
```

---

## 6. skb_cow_head(skb, headroom)

### 6.1 Overview

`skb_cow_head()` is a more targeted variant of `skb_cow()`. It ensures that
the sk_buff has at least `headroom` bytes of writable headroom, but unlike
`skb_cow()`, it focuses exclusively on the headroom requirement and uses
`__pskb_pull_tail()` semantics when only the head area needs to be unshared.

```c
/**
 * skb_cow_head - ensure writable headroom
 * @skb: buffer to modify
 * @headroom: bytes of headroom required
 *
 * Ensures that @skb has at least @headroom bytes of writable
 * space before skb->data. More efficient than skb_cow() when
 * the caller only needs to prepend headers and does not need
 * to modify existing data in the tail area.
 *
 * Returns 0 on success, negative errno on failure.
 */
static inline int skb_cow_head(struct sk_buff *skb, unsigned int headroom)
{
    int delta = headroom - skb_headroom(skb);

    if (delta < 0)
        delta = 0;

    if (delta || skb_header_cloned(skb))
        return pskb_expand_head(skb, ALIGN(delta, NET_SKB_PAD), 0,
                                GFP_ATOMIC);
    return 0;
}
```

### 6.2 skb_header_cloned() vs. skb_cloned()

The key difference between `skb_cow_head()` and `skb_cow()` lies in the check:

- `skb_cow()` uses `skb_cloned()` — checks if the **data** is shared.
- `skb_cow_head()` uses `skb_header_cloned()` — checks if the **header area**
  specifically is shared.

```c
static inline int skb_header_cloned(const struct sk_buff *skb)
{
    int dataref;

    if (!skb->cloned)
        return 0;

    dataref = atomic_read(&skb_shinfo(skb)->dataref);
    dataref = (dataref & SKB_DATAREF_MASK) - (dataref >> SKB_DATAREF_SHIFT);
    return dataref != 1;
}
```

The `dataref` field is split into two halves:
- Lower bits: total references to the header (linear) area.
- Upper bits: references to only the payload (via `skb_header_release()`).

This allows the kernel to distinguish between "data is shared for reading the
whole buffer" and "only the payload pages are shared."

### 6.3 When to Use skb_cow_head()

`skb_cow_head()` is preferred over `skb_cow()` when:

- The caller only needs to prepend new headers (e.g., pushing a VLAN tag,
  pushing a tunnel outer header).
- The caller does not need to modify existing data in the linear area beyond
  adjusting pointers.
- Performance is critical and the caller wants to avoid unnecessary copies
  when only headroom is insufficient but the buffer is not actually cloned.

Example usage in VLAN processing:

```c
int vlan_insert_tag(struct sk_buff *skb, __be16 vlan_proto, u16 vlan_tci)
{
    /* Ensure we have room for the 4-byte VLAN header */
    if (skb_cow_head(skb, VLAN_HLEN) < 0) {
        kfree_skb(skb);
        return -ENOMEM;
    }

    /* Push the data pointer back by 4 bytes */
    skb_push(skb, VLAN_HLEN);

    /* Move the MAC header to make room */
    memmove(skb->data, skb->data + VLAN_HLEN, 2 * ETH_ALEN);

    /* Insert the VLAN tag */
    struct vlan_ethhdr *veth = (struct vlan_ethhdr *)skb->data;
    veth->h_vlan_proto       = vlan_proto;
    veth->h_vlan_TCI         = htons(vlan_tci);

    return 0;
}
```

---

## 7. pskb_expand_head(skb, nhead, ntail, gfp_mask)

### 7.1 Overview

`pskb_expand_head()` is the core reallocation function used by `skb_cow()`,
`skb_cow_head()`, and other expansion APIs. It allocates a new linear data
buffer that is larger than the current one (with additional headroom and/or
tailroom), copies the existing linear data into it, and updates all pointers
in the `sk_buff` structure.

If the buffer was shared (due to cloning), the new buffer is private to this
sk_buff, effectively "unsharing" the data.

```c
/**
 * pskb_expand_head - reallocate header of &sk_buff
 * @skb: buffer to reallocate
 * @nhead: room to add at the head (before data)
 * @ntail: room to add at the tail (after tail, before end)
 * @gfp_mask: allocation priority
 *
 * Expands (or just copies) the data area of a sk_buff. After
 * this call, at least @nhead bytes are available before skb->data
 * and @ntail bytes between skb->tail and skb->end. Fragment
 * pages are unaffected. Returns 0 on success, -ENOMEM on failure.
 *
 * WARNING: All pointers derived from skb->head are invalidated.
 */
int pskb_expand_head(struct sk_buff *skb, int nhead, int ntail,
                     gfp_t gfp_mask)
{
    int old_headlen = skb_headlen(skb);
    int old_headroom = skb_headroom(skb);

    /* Calculate the new buffer size */
    int size = SKB_DATA_ALIGN(nhead + old_headlen + ntail) +
               SKB_DATA_ALIGN(sizeof(struct skb_shared_info));

    /* Allocate the new data buffer */
    void *data = kmalloc_reserve(size, gfp_mask, NUMA_NO_NODE, NULL);
    if (!data)
        goto nodata;

    /* Compute the new skb_shared_info location */
    size = SKB_WITH_OVERHEAD(ksize(data));

    /*
     * Copy the linear data from the old buffer to the new one.
     * The data is placed at offset nhead (new headroom) in the
     * new buffer.
     */
    memcpy(data + nhead, skb->data, old_headlen);

    /* Initialize skb_shared_info in the new buffer */
    struct skb_shared_info *new_shinfo =
        (struct skb_shared_info *)(data + size);
    memcpy(new_shinfo, skb_shinfo(skb), offsetof(struct skb_shared_info, frags));

    /*
     * If there are paged fragments, copy the frag array and
     * increment page reference counts (fragments are still shared).
     */
    if (skb_shinfo(skb)->nr_frags) {
        int i;
        for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
            new_shinfo->frags[i] = skb_shinfo(skb)->frags[i];
            skb_frag_ref(skb, i);
        }
    }

    /*
     * The new buffer has its own independent dataref.
     * Start at 1 (or potentially split for header_release).
     */
    atomic_set(&new_shinfo->dataref, 1);

    /*
     * Release the old data buffer. If it was shared, this
     * decrements dataref. If dataref reaches 0, the old
     * buffer is freed.
     */
    skb_release_data(skb);

    /* Update the sk_buff pointers to the new buffer */
    int off = nhead - old_headroom;  /* pointer adjustment delta */

    skb->head     = data;
    skb->data    += off;
    skb->end      = size;

    /* Offsets stored as offsets from head are adjusted */
#ifdef NET_SKBUFF_DATA_USES_OFFSET
    /* tail is an offset from head */
    skb->tail    += nhead - old_headroom;
#else
    /* tail is an absolute pointer */
    skb->tail    += off;
#endif

    /* Adjust header offsets */
    skb->transport_header += off;
    skb->network_header   += off;
    skb->mac_header       += off;
    skb->inner_transport_header += off;
    skb->inner_network_header   += off;
    skb->inner_mac_header       += off;

    /* The buffer is no longer cloned */
    skb->cloned = 0;
    skb->hdr_len = 0;

    /* Recalculate nohdr status */
    skb->nohdr = 0;

    return 0;

nodata:
    return -ENOMEM;
}
```

### 7.2 Expansion Diagram

The following diagram illustrates what happens when `pskb_expand_head(skb, 64,
128, GFP_ATOMIC)` is called to add 64 bytes of headroom and 128 bytes of
tailroom:

```
  BEFORE pskb_expand_head():

  sk_buff                Old Buffer
  ┌────────────┐        ┌──────────────────────────────────┐
  │ head ──────┼───────►│ head                             │
  │ data ──────┼───────►│ ├─ headroom: 32 B ─┤             │
  │ tail ──────┼───────►│ data ─── linear data ── tail     │
  │ end  ──────┼───────►│ ├─ tailroom: 16 B ──┤            │
  └────────────┘        │ end                              │
                        ├──────────────────────────────────┤
                        │ skb_shared_info  dataref = 2     │
                        │  frags[0] ──────► Page X          │
                        └──────────────────────────────────┘

  AFTER pskb_expand_head(skb, 64, 128, GFP_ATOMIC):

  sk_buff                New Buffer (larger)
  ┌────────────┐        ┌──────────────────────────────────────────────────┐
  │ head ──────┼───────►│ head                                             │
  │            │        │ ├──── new headroom: 64 B ────┤                   │
  │ data ──────┼───────►│ data ─── linear data (copied) ── tail            │
  │ tail ──────┼───────►│ ├──── new tailroom: 128 B ──────────┤            │
  │ end  ──────┼───────►│ end                                              │
  └────────────┘        ├──────────────────────────────────────────────────┤
                        │ skb_shared_info  dataref = 1  ◄── UNSHARED      │
                        │  frags[0] ──────► Page X (still shared via ref)  │
                        └──────────────────────────────────────────────────┘

                         Old Buffer
                        ┌──────────────────────────────────┐
                        │ (dataref decremented → 1)        │
                        │  Still in use by the original    │
                        │  sk_buff that was sharing it     │
                        └──────────────────────────────────┘
```

### 7.3 Key Properties

1. **Linear data is copied:** The content between `data` and `tail` in the
   old buffer is faithfully reproduced in the new buffer.

2. **Fragment pages are still shared:** Paged fragment references are copied
   to the new `skb_shared_info`, and page reference counts are incremented.
   The actual fragment data is not duplicated.

3. **The old buffer is released:** `skb_release_data()` is called on the old
   buffer. If the old buffer's `dataref` drops to zero, it is freed. If other
   clones still reference it, it survives with a decremented `dataref`.

4. **All pointers must be re-derived:** After `pskb_expand_head()`, any cached
   pointers to locations within the old buffer (e.g., `ip_hdr(skb)`,
   `tcp_hdr(skb)`) are dangling. Callers must re-derive them.

5. **The sk_buff struct is reused:** Unlike `pskb_copy()`, which allocates a
   new `sk_buff`, `pskb_expand_head()` modifies the existing one in place.
   This is an important distinction: the sk_buff's position in queues and
   its pointer identity are preserved.

### 7.4 Alignment Considerations

The new headroom is aligned to `NET_SKB_PAD`, which is typically 64 bytes on
most architectures. This alignment is important for:

- **Cache line alignment:** Ensuring that the start of packet data aligns with
  a cache line boundary improves DMA performance.
- **Hardware requirements:** Some network adapters require specific alignment
  for DMA descriptors.

```c
#ifndef NET_SKB_PAD
#define NET_SKB_PAD max(32, L1_CACHE_BYTES)
#endif
```

---

## 8. skb_realloc_headroom(skb, headroom)

### 8.1 Overview

`skb_realloc_headroom()` creates a **new** sk_buff with the specified amount of
headroom, copying data from the old sk_buff. Unlike `pskb_expand_head()` (which
modifies the sk_buff in place), this function returns a new sk_buff; the caller
must explicitly free the old one.

```c
/**
 * skb_realloc_headroom - reallocate headroom of an sk_buff
 * @skb: buffer to reallocate
 * @headroom: new headroom size
 *
 * Allocate a new &sk_buff with the specified headroom. The content
 * of the old sk_buff is copied to the new one. The caller is
 * responsible for freeing the old sk_buff.
 *
 * Returns NULL on allocation failure.
 */
struct sk_buff *skb_realloc_headroom(struct sk_buff *skb,
                                     unsigned int headroom)
{
    struct sk_buff *skb2;
    int delta = headroom - skb_headroom(skb);

    if (delta <= 0)
        /* Already have enough headroom — just clone */
        skb2 = pskb_copy(skb, GFP_ATOMIC);
    else {
        /* Need more headroom — use skb_copy_expand */
        skb2 = skb_copy_expand(skb, headroom,
                               skb_tailroom(skb), GFP_ATOMIC);
    }
    return skb2;
}
```

### 8.2 Usage Pattern

```c
/*
 * Example: A tunnel device needs to add an outer IP header
 * but the current sk_buff does not have enough headroom.
 */
int tunnel_xmit(struct sk_buff *skb, struct net_device *dev)
{
    int needed_headroom = sizeof(struct iphdr) +
                          sizeof(struct udphdr) +
                          LL_RESERVED_SPACE(dev);

    if (skb_headroom(skb) < needed_headroom) {
        struct sk_buff *new_skb;

        new_skb = skb_realloc_headroom(skb, needed_headroom);
        if (!new_skb) {
            dev->stats.tx_dropped++;
            kfree_skb(skb);
            return NETDEV_TX_OK;
        }

        /* Consume the old sk_buff */
        consume_skb(skb);
        skb = new_skb;
    }

    /* Now we have enough headroom to push the outer headers */
    skb_push(skb, sizeof(struct iphdr));
    /* ... build outer IP header ... */

    return dev_queue_xmit(skb);
}
```

### 8.3 Comparison with pskb_expand_head()

```
  ┌───────────────────────┬────────────────────────┬─────────────────────────┐
  │  Property              │  pskb_expand_head()    │  skb_realloc_headroom() │
  ├───────────────────────┼────────────────────────┼─────────────────────────┤
  │  Modifies in-place?    │  Yes                   │  No (returns new skb)   │
  │  Returns               │  0 / -ENOMEM           │  new skb / NULL         │
  │  Old sk_buff           │  Modified (same ptr)   │  Unchanged (must free)  │
  │  Queue position        │  Preserved             │  Lost (new sk_buff)     │
  │  Socket association    │  Preserved             │  Lost (sk = NULL)       │
  │  Use case              │  In-place header mods  │  Creating a new packet  │
  └───────────────────────┴────────────────────────┴─────────────────────────┘
```

---

## 9. skb_copy_expand(skb, newheadroom, newtailroom, gfp_mask)

### 9.1 Overview

`skb_copy_expand()` combines a full data copy with expansion. It creates a
completely independent sk_buff with a new linear buffer sized to accommodate
the original data plus the requested additional headroom and tailroom. All
data (linear + fragments + frag_list) is linearized into the new buffer.

```c
/**
 * skb_copy_expand - copy and expand an sk_buff
 * @skb: buffer to copy
 * @newheadroom: new free bytes before the current data
 * @newtailroom: new free bytes after the current data
 * @gfp_mask: allocation priority
 *
 * Make a copy of both an &sk_buff and its data, with the new
 * buffer having at least @newheadroom bytes before the data
 * and @newtailroom bytes after it. In addition, the data is
 * linearized (all fragments pulled into the linear area).
 */
struct sk_buff *skb_copy_expand(const struct sk_buff *skb,
                                int newheadroom, int newtailroom,
                                gfp_t gfp_mask)
{
    struct sk_buff *n;
    int total_len = skb->len;  /* total data length (linear + frags) */

    /*
     * Allocate new sk_buff with room for:
     *   newheadroom + total_data_len + newtailroom
     */
    n = __alloc_skb(newheadroom + total_len + newtailroom,
                    gfp_mask, skb_alloc_rx_flag(skb), NUMA_NO_NODE);
    if (!n)
        return NULL;

    /* Reserve the new headroom */
    skb_reserve(n, newheadroom);

    /* Set the data length */
    skb_put(n, total_len);

    /* Copy ALL data (linear + frags + frag_list) into linear area */
    if (skb_copy_bits(skb, 0, n->data, total_len)) {
        kfree_skb(n);
        return NULL;
    }

    /* Copy metadata */
    copy_skb_header(n, skb);

    return n;
}
```

### 9.2 Memory Layout

```
  Original sk_buff with limited headroom
  ┌────────────┐
  │ headroom:  │
  │   16 bytes │        ┌──────────────────────────────┐
  │ head ──────┼───────►│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│            │
  │ data ──────┼───────►│ packet data (1500 B)          │
  │ tail ──────┼───────►│                │              │
  │ end  ──────┼───────►│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│            │
  │ tailroom:  │        │ shared_info                   │
  │   32 bytes │        └──────────────────────────────┘
  └────────────┘

  After skb_copy_expand(skb, 128, 256, GFP_ATOMIC):

  New sk_buff with expanded headroom and tailroom
  ┌────────────┐
  │ headroom:  │
  │   128 bytes│        ┌─────────────────────────────────────────────┐
  │ head ──────┼───────►│                                             │
  │            │        │ ◄─── 128 B headroom ──►                     │
  │ data ──────┼───────►│ packet data (1500 B, COPIED)                │
  │ tail ──────┼───────►│                                             │
  │            │        │ ◄─── 256 B tailroom ──────────►             │
  │ end  ──────┼───────►│                                             │
  │ tailroom:  │        ├─────────────────────────────────────────────┤
  │   256 bytes│        │ skb_shared_info  dataref = 1                │
  └────────────┘        │ nr_frags = 0  (linearized)                  │
                        └─────────────────────────────────────────────┘
```

### 9.3 Primary Use Cases

#### 9.3.1 Tunnel Encapsulation

The most common use case is when a packet must be encapsulated inside a new
protocol layer. For example, VXLAN encapsulation adds:

- Outer Ethernet header: 14 bytes
- Outer IP header: 20 bytes
- Outer UDP header: 8 bytes
- VXLAN header: 8 bytes
- Total: 50 bytes of additional headroom needed

```c
/*
 * VXLAN encapsulation example — simplified from drivers/net/vxlan.c
 */
int vxlan_xmit_skb(struct sk_buff *skb, struct net_device *dev,
                   struct vxlan_config *cfg)
{
    int headroom = sizeof(struct iphdr) +     /* outer IP: 20 B    */
                   sizeof(struct udphdr) +    /* outer UDP: 8 B    */
                   sizeof(struct vxlanhdr) +  /* VXLAN: 8 B        */
                   LL_RESERVED_SPACE(dev);    /* L2 header room    */

    int tailroom = 0;

    if (skb_headroom(skb) < headroom || skb_cloned(skb)) {
        struct sk_buff *new_skb;

        new_skb = skb_copy_expand(skb, headroom, tailroom, GFP_ATOMIC);
        if (!new_skb) {
            kfree_skb(skb);
            return -ENOMEM;
        }
        consume_skb(skb);
        skb = new_skb;
    }

    /* Build VXLAN header */
    struct vxlanhdr *vxh;
    vxh = __skb_push(skb, sizeof(*vxh));
    vxh->vx_flags = htonl(VXLAN_HF_VNI);
    vxh->vx_vni = vxlan_vni_field(cfg->vni);

    /* Build outer UDP header */
    struct udphdr *uh;
    uh = __skb_push(skb, sizeof(*uh));
    uh->dest   = cfg->dst_port;
    uh->source = udp_flow_src_port(dev_net(dev), skb, 0, 0, false);
    uh->len    = htons(skb->len);
    uh->check  = 0;

    /* Build outer IP header */
    /* ... */

    return 0;
}
```

#### 9.3.2 GRE Encapsulation

```c
int gre_build_header(struct sk_buff *skb, int hdr_len)
{
    int headroom = hdr_len + sizeof(struct iphdr) +
                   LL_RESERVED_SPACE(skb->dev);

    if (skb_cow_head(skb, headroom) < 0) {
        /*
         * skb_cow_head failed — fall back to full copy+expand.
         * This is less efficient but handles edge cases.
         */
        struct sk_buff *new_skb;
        new_skb = skb_copy_expand(skb, headroom, 0, GFP_ATOMIC);
        if (!new_skb)
            return -ENOMEM;
        consume_skb(skb);
        skb = new_skb;
    }

    /* Push and build the GRE header */
    __skb_push(skb, hdr_len);
    /* ... fill in GRE fields ... */

    return 0;
}
```

### 9.4 Performance Characteristics

| Metric                    | Value                                     |
|---------------------------|-------------------------------------------|
| Allocation size           | sk_buff + headroom + data + tailroom       |
| Time complexity           | O(n) where n = total data length           |
| Data copy                 | Full (linear + frags + frag_list)           |
| Fragments                 | Linearized                                 |
| Headroom                  | Exactly as requested (after alignment)     |
| Tailroom                  | Exactly as requested (after alignment)     |
| Result                    | Fully independent, fully linear             |

---

## 10. Linearization

### 10.1 What Is a Non-Linear sk_buff?

An sk_buff is "non-linear" when its data is not entirely contained in the
contiguous linear buffer between `data` and `tail`. Instead, some data resides
in:

1. **Paged fragments** (`skb_shinfo(skb)->frags[]`): References to pages in
   memory, typically populated by hardware scatter-gather DMA.
2. **frag_list** (`skb_shinfo(skb)->frag_list`): A linked list of other
   sk_buff structures, used for GSO (Generic Segmentation Offload) and
   IP fragmentation reassembly.

```
  Non-linear sk_buff structure
  ┌──────────────────┐
  │ len = 4096       │   ◄── total data length
  │ data_len = 3072  │   ◄── data NOT in linear area
  │ headlen = 1024   │   ◄── len - data_len = linear data
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ Linear area      │
  │ ┌──────────────┐ │
  │ │ 1024 bytes   │ │   ◄── headers + some payload
  │ └──────────────┘ │
  ├──────────────────┤
  │ skb_shared_info   │
  │ ┌──────────────┐ │
  │ │ nr_frags = 2 │ │
  │ │ frags[0] ────┼─┼──► Page P1: 1024 bytes
  │ │ frags[1] ────┼─┼──► Page P2: 1024 bytes
  │ │ frag_list ───┼─┼──► sk_buff chain: 1024 bytes
  │ └──────────────┘ │
  └──────────────────┘

  Total: 1024 (linear) + 1024 (P1) + 1024 (P2) + 1024 (frag_list) = 4096
  data_len = 3072 (everything not in the linear area)
```

### 10.2 skb_linearize(skb)

`skb_linearize()` converts a non-linear sk_buff into a fully linear one by
allocating a new buffer large enough for all data and copying everything into
it.

```c
/**
 * skb_linearize - convert non-linear sk_buff to linear
 * @skb: buffer to linearize
 *
 * If there is no data in the paged area (data_len == 0),
 * this function does nothing. Otherwise, it allocates a new
 * buffer and copies all data into the linear area.
 *
 * Returns 0 on success, -ENOMEM on failure.
 */
static inline int skb_linearize(struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) ? __skb_linearize(skb) : 0;
}

int __skb_linearize(struct sk_buff *skb)
{
    return __pskb_pull_tail(skb, skb->data_len) ? 0 : -ENOMEM;
}
```

The heavy lifting is done by `__pskb_pull_tail()`, which pulls data from the
paged area into the linear area.

### 10.3 __pskb_pull_tail(skb, delta)

This function pulls `delta` bytes of data from the non-linear area (paged
fragments and frag_list) into the linear area. When called by `skb_linearize()`,
`delta` equals `data_len`, pulling ALL non-linear data into the linear area.

```c
/**
 * __pskb_pull_tail - pull data from non-linear to linear area
 * @skb: buffer to modify
 * @delta: number of bytes to pull
 *
 * Pull @delta bytes from the paged data area into the linear
 * area. This may require reallocating the linear buffer if
 * there is not enough tailroom.
 */
void *__pskb_pull_tail(struct sk_buff *skb, int delta)
{
    int headlen  = skb_headlen(skb);
    int tailroom = skb_tailroom(skb);

    /* Do we need a bigger linear buffer? */
    if (delta > tailroom) {
        /*
         * Not enough tailroom — must reallocate.
         * pskb_expand_head() will allocate a new buffer with
         * enough room and copy existing linear data.
         */
        if (pskb_expand_head(skb, 0, delta - tailroom, GFP_ATOMIC))
            return NULL;
    }

    /*
     * Now copy 'delta' bytes from the paged area into the
     * linear area, starting right after the current tail.
     */
    if (skb_copy_bits(skb, headlen, skb_tail_pointer(skb), delta)) {
        /* Should not happen */
        return NULL;
    }

    /* Release the fragment pages that were fully consumed */
    /* (complex bookkeeping of frags[] and frag_list omitted for clarity) */

    /* Advance tail by delta bytes */
    skb->tail += delta;

    /* Reduce data_len by delta (less data in paged area) */
    skb->data_len -= delta;

    return skb_tail_pointer(skb);
}
```

### 10.4 Linearization Diagram

```
  BEFORE skb_linearize():

  ┌──────────────────┐
  │ len = 4096       │
  │ data_len = 3072  │
  │ headlen = 1024   │
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────────────┐
  │ head                     │
  │ ├── headroom ──┤         │
  │ data                     │
  │ ┌──────────────────────┐ │
  │ │ Linear: 1024 bytes   │ │
  │ └──────────────────────┘ │
  │ tail                     │
  │ ├── tailroom: 64 B ──┤  │   ◄── NOT enough for 3072 B
  │ end                      │
  ├──────────────────────────┤
  │ shared_info               │
  │  frags[0] → Page P1 1024 │
  │  frags[1] → Page P2 1024 │
  │  frag_list → skb  1024   │
  └──────────────────────────┘

  STEP 1: pskb_expand_head(skb, 0, 3072 - 64, ...) to get tailroom
  STEP 2: Copy 3072 bytes from frags/frag_list into linear area
  STEP 3: Release consumed fragment pages

  AFTER skb_linearize():

  ┌──────────────────┐
  │ len = 4096       │
  │ data_len = 0     │   ◄── fully linear
  │ headlen = 4096   │
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────────────────────────────┐
  │ head                                     │
  │ ├── headroom ──┤                         │
  │ data                                     │
  │ ┌──────────────────────────────────────┐ │
  │ │ Linear: 4096 bytes                   │ │
  │ │ ┌──────────────────┐                 │ │
  │ │ │ Original 1024 B  │ (was linear)    │ │
  │ │ ├──────────────────┤                 │ │
  │ │ │ From P1: 1024 B  │ (was frag[0])   │ │
  │ │ ├──────────────────┤                 │ │
  │ │ │ From P2: 1024 B  │ (was frag[1])   │ │
  │ │ ├──────────────────┤                 │ │
  │ │ │ From list: 1024 B│ (was frag_list) │ │
  │ │ └──────────────────┘                 │ │
  │ └──────────────────────────────────────┘ │
  │ tail                                     │
  │ end                                      │
  ├──────────────────────────────────────────┤
  │ shared_info                               │
  │  nr_frags = 0                             │
  │  frag_list = NULL                         │
  │  dataref = 1                              │
  └──────────────────────────────────────────┘
```

### 10.5 Cost of Linearization

Linearization is expensive:

1. **Memory allocation:** A buffer large enough for ALL data must be allocated
   contiguously. For jumbo frames (9000+ bytes), this may require order-2 or
   higher page allocations, which are increasingly likely to fail under memory
   pressure.

2. **Data copying:** All paged data must be copied into the new buffer.
   For a 64 KB GSO packet, this means copying 64 KB of data.

3. **Page unmapping:** `kmap_atomic()` / `kunmap_atomic()` calls for each
   paged fragment add overhead.

4. **Cache pollution:** Touching all the data pages pollutes the CPU cache.

### 10.6 When Linearization Is Required

Despite its cost, linearization is sometimes unavoidable:

- **Legacy protocol parsers:** Some older protocol implementations expect
  contiguous data and use direct pointer arithmetic rather than
  `skb_header_pointer()`.

- **Crypto operations:** Some cryptographic algorithms require contiguous input
  buffers.

- **Netfilter string matching:** Pattern matching across the payload may
  require a contiguous view.

- **BPF programs:** While modern eBPF programs use helpers to access
  non-linear data, classic BPF programs may need linearized access.

### 10.7 Avoiding Linearization

The kernel provides several helpers to access non-linear data without
linearizing:

```c
/*
 * skb_header_pointer() — access potentially non-linear header data
 * without linearizing. If the header is in the linear area, returns
 * a direct pointer. Otherwise, copies it to a caller-provided buffer.
 */
static inline void *skb_header_pointer(const struct sk_buff *skb,
                                        int offset, int len, void *buffer)
{
    int hlen = skb_headlen(skb);

    if (hlen - offset >= len)
        return skb->data + offset;  /* Fast path: already linear */

    /* Slow path: copy from non-linear area to buffer */
    if (skb_copy_bits(skb, offset, buffer, len) < 0)
        return NULL;

    return buffer;
}

/* Usage example: reading a TCP header that might be in fragments */
struct tcphdr _tcph;
struct tcphdr *th;

th = skb_header_pointer(skb, transport_offset, sizeof(_tcph), &_tcph);
if (!th) {
    /* Packet too short */
    return -EINVAL;
}
/* th now points to valid TCP header data (either in-buffer or _tcph) */
```

---

## 11. Reference Count Management During Clone/Copy

### 11.1 The dataref Anatomy

The `dataref` field in `skb_shared_info` is an `atomic_t` that tracks how many
`sk_buff` structures reference the same data buffer. Its structure is more
nuanced than a simple counter:

```c
/*
 * The dataref field is logically split into two halves:
 *
 *  ┌─────────────────────────────────────┐
 *  │ 31            16 │ 15             0 │
 *  ├─────────────────────────────────────┤
 *  │  SKB_DATAREF_SHIFT │ SKB_DATAREF_MASK│
 *  │  (header-released  │ (total refs to  │
 *  │   references)      │  buffer)        │
 *  └─────────────────────────────────────┘
 *
 *  Total users = lower half
 *  Header-only users = upper half
 *  Users who need the header = lower - upper
 */

#define SKB_DATAREF_SHIFT 16
#define SKB_DATAREF_MASK  ((1 << SKB_DATAREF_SHIFT) - 1)
```

### 11.2 The dataref Lifecycle

```
  1. Allocation:
     __alloc_skb()
     └── atomic_set(&shinfo->dataref, 1)     dataref = 1

  2. Clone:
     skb_clone()
     └── atomic_inc(&shinfo->dataref)         dataref = 2
         ┌──────────────┐ ┌──────────────┐
         │ original     │ │ clone        │
         │ cloned = 1   │ │ cloned = 1   │
         └──────┬───────┘ └──────┬───────┘
                │                │
                └───────┬────────┘
                        ▼
                   dataref = 2

  3. Second clone:
     skb_clone()
     └── atomic_inc(&shinfo->dataref)         dataref = 3

  4. Free one clone:
     kfree_skb(clone1)
     └── skb_release_data()
         └── atomic_dec_and_test(&dataref)    dataref = 2
             → returns false → buffer NOT freed

  5. Free another clone:
     kfree_skb(clone2)
     └── skb_release_data()
         └── atomic_dec_and_test(&dataref)    dataref = 1
             → returns false → buffer NOT freed
             → but now only 1 user: cloned flag can be cleared

  6. Free original:
     kfree_skb(original)
     └── skb_release_data()
         └── atomic_dec_and_test(&dataref)    dataref = 0
             → returns true → buffer IS freed
             → kfree(head)
             → put_page() for each fragment page
```

### 11.3 Atomic Operations and Memory Ordering

The `dataref` manipulations use atomic operations to ensure correctness under
concurrent access:

```c
/* Incrementing (during clone) */
atomic_inc(&skb_shinfo(skb)->dataref);
/*
 * This uses a full atomic increment with memory barriers.
 * It ensures that the increment is visible to all CPUs before
 * the clone is returned to the caller.
 */

/* Decrementing (during free) */
if (atomic_dec_and_test(&skb_shinfo(skb)->dataref)) {
    /* We were the last user — free the buffer */
    /*
     * atomic_dec_and_test provides acquire-release semantics:
     * all previous writes to the buffer are visible before
     * we proceed to free it.
     */
}
```

### 11.4 The users Reference Count

In addition to `dataref` (which tracks data buffer sharing), each `sk_buff`
has its own `users` reference count that tracks how many entities hold a
reference to the `sk_buff` structure itself:

```c
/*
 * sk_buff reference counting:
 *
 *  sk_buff.users   → references to the sk_buff STRUCTURE
 *  shinfo.dataref  → references to the DATA BUFFER
 *
 * These are independent. An sk_buff can have users > 1
 * without being cloned (e.g., when queued in multiple places),
 * and vice versa.
 */

/* Increment sk_buff reference */
static inline struct sk_buff *skb_get(struct sk_buff *skb)
{
    refcount_inc(&skb->users);
    return skb;
}

/* Decrement and potentially free */
void kfree_skb(struct sk_buff *skb)
{
    if (!refcount_dec_and_test(&skb->users))
        return;         /* Other users remain */
    __kfree_skb(skb);   /* Last user — free everything */
}
```

### 11.5 The Clone/Unshare/Free Lifecycle — Complete Example

```c
/*
 * Complete lifecycle demonstrating clone, unshare, and free.
 */
void example_lifecycle(struct sk_buff *skb)
{
    /*
     * State: skb->users = 1, dataref = 1, cloned = 0
     */

    /* 1. Clone for packet capture */
    struct sk_buff *capture_skb = skb_clone(skb, GFP_ATOMIC);
    /*
     * State:
     *   skb->users = 1, skb->cloned = 1
     *   capture_skb->users = 1, capture_skb->cloned = 1
     *   dataref = 2  (shared buffer)
     */

    /* 2. Try to modify the original's IP header — MUST cow first */
    if (skb_cow(skb, 0)) {
        /* Allocation failure */
        kfree_skb(capture_skb);
        kfree_skb(skb);
        return;
    }
    /*
     * State:
     *   skb now has a PRIVATE buffer (dataref = 1)
     *   skb->cloned = 0
     *   capture_skb still points to OLD buffer (dataref = 1)
     *   capture_skb->cloned = 0  (it's now the sole user)
     */

    /* 3. Modify the header safely */
    struct iphdr *iph = ip_hdr(skb);
    iph->ttl--;
    ip_send_check(iph);

    /* 4. Deliver capture_skb to userspace (e.g., AF_PACKET) */
    deliver_to_packet_socket(capture_skb);
    /* capture_skb will be freed by the packet socket layer */

    /* 5. Forward the modified skb */
    ip_forward_finish(skb);
    /* skb will be freed after transmission */
}
```

### 11.6 Decision Flowchart: Clone vs. Copy

```
  Need a second reference to this packet?
  ┌───────────────────────────────┐
  │  Will the second reference    │
  │  MODIFY any data?             │
  └─────────────┬─────────────────┘
                │
         ┌──────┴──────┐
         │             │
        NO            YES
         │             │
         ▼             ▼
  ┌────────────┐  ┌──────────────────────────┐
  │ skb_clone()│  │ Will it modify ONLY       │
  │            │  │ headers (linear area)?    │
  │ Share all  │  └────────────┬──────────────┘
  │ data.      │               │
  │ Cheapest.  │        ┌──────┴──────┐
  └────────────┘        │             │
                       YES            NO
                        │             │
                        ▼             ▼
                 ┌────────────┐  ┌─────────────────┐
                 │ pskb_copy()│  │ Does it need     │
                 │ or         │  │ different        │
                 │ skb_cow()  │  │ headroom/tailroom│
                 │            │  │ than original?   │
                 │ Copy head, │  └──────┬───────────┘
                 │ share frags│         │
                 └────────────┘  ┌──────┴──────┐
                                 │             │
                                YES            NO
                                 │             │
                                 ▼             ▼
                          ┌──────────────┐ ┌──────────┐
                          │skb_copy_     │ │ skb_copy()│
                          │  expand()    │ │           │
                          │              │ │ Full copy │
                          │ Full copy    │ │ Same room │
                          │ + new room   │ └──────────┘
                          └──────────────┘
```

### 11.7 Avoiding Double-Free and Use-After-Free

The kernel's reference counting scheme prevents double-free, but developers must
still be careful:

```c
/* WRONG: double free of the same sk_buff */
kfree_skb(skb);
kfree_skb(skb);  /* BUG: users is already 0 */

/* WRONG: use after free */
kfree_skb(skb);
printk("protocol: %x\n", skb->protocol);  /* BUG: freed memory */

/* WRONG: freeing a cloned sk_buff and then using the data */
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC);
kfree_skb(skb);  /* original freed */
/*
 * clone is still valid, but if both clone and skb are freed,
 * the data buffer is also freed. The clone must be freed
 * through kfree_skb(clone) separately.
 */

/* CORRECT: use consume_skb() when the sk_buff was used successfully */
consume_skb(skb);  /* Marks as consumed (not dropped) for tracing */
```

---

## 12. Real-World Use Cases

### 12.1 Packet Capture (tcpdump / AF_PACKET)

When a raw packet socket (AF_PACKET) is active on an interface, the kernel
delivers a copy of every matching packet to the socket. This is implemented
using `skb_clone()`:

```c
/*
 * Simplified from net/packet/af_packet.c: packet_rcv()
 *
 * Called for each incoming packet when a packet socket is active.
 */
static int packet_rcv(struct sk_buff *skb, struct net_device *dev,
                      struct packet_type *pt, struct net_device *orig_dev)
{
    struct sock *sk;
    struct sk_buff *nskb;

    sk = pt->af_packet_priv;

    /*
     * Clone the sk_buff. We must NOT consume the original because
     * it still needs to be delivered to the normal protocol stack.
     *
     * skb_clone is ideal here:
     * - We only need to READ the packet data (for delivery to userspace)
     * - The clone is independent for metadata (sk, timestamp, etc.)
     * - The actual packet bytes are shared — no 1500-byte copy
     */
    nskb = skb_clone(skb, GFP_ATOMIC);
    if (!nskb)
        return 0;  /* Drop the capture, don't affect normal path */

    /* Adjust the clone's metadata for the packet socket */
    nskb->sk = sk;
    nskb->pkt_type = PACKET_HOST;

    /* Record the timestamp for the capture */
    __net_timestamp(nskb);

    /*
     * Queue the clone to the packet socket's receive queue.
     * The original skb continues through the normal stack.
     */
    if (sock_queue_rcv_skb(sk, nskb) < 0) {
        kfree_skb(nskb);
    }

    return 0;  /* Let the original continue */
}

/*
 * The flow:
 *
 *  NIC driver receives packet → allocates sk_buff
 *       │
 *       ▼
 *  netif_receive_skb(skb)
 *       │
 *       ├──► deliver_skb() → packet_rcv()
 *       │         │
 *       │         └── skb_clone() → clone queued to AF_PACKET socket
 *       │
 *       └──► ip_rcv(skb) → normal IP processing
 *                │
 *                └── skb continues (original, unmodified)
 */
```

### 12.2 Multicast Forwarding

When a multicast packet arrives and must be forwarded to multiple output
interfaces, the kernel clones the sk_buff for each output interface except the
last (which reuses the original):

```c
/*
 * Simplified from net/ipv4/ipmr.c: ipmr_queue_xmit()
 *
 * Forward a multicast packet to a single output interface.
 */
static int ipmr_queue_xmit(struct net *net, struct mr_table *mrt,
                           struct sk_buff *skb, int vifi)
{
    struct sk_buff *skb2;
    struct vif_device *vif = &mrt->vif_table[vifi];
    struct net_device *dev = vif->dev;

    /*
     * Clone the sk_buff for this output interface.
     * Each output gets its own clone because:
     * 1. Each may need different L2 headers (different next-hop MACs)
     * 2. Each travels through independent egress queueing
     * 3. Freeing one must not affect others
     */
    skb2 = skb_clone(skb, GFP_ATOMIC);
    if (!skb2)
        return -ENOMEM;

    /*
     * Before modifying the IP header (TTL decrement), we must
     * ensure the data is writable. The clone shares data with
     * the original, so we need skb_cow().
     */
    if (skb_cow(skb2, LL_RESERVED_SPACE(dev) + sizeof(struct iphdr))) {
        kfree_skb(skb2);
        return -ENOMEM;
    }

    /* Now safe to modify the IP header */
    struct iphdr *iph = ip_hdr(skb2);
    ip_decrease_ttl(iph);
    ip_send_check(iph);

    /* Set the output device */
    skb2->dev = dev;

    /* Send it out */
    ip_local_out(net, skb2->sk, skb2);

    return 0;
}

/*
 * The multicast routing daemon calls this for each output vif:
 *
 *  Incoming multicast packet
 *       │
 *       ▼
 *  ip_mr_forward()
 *       │
 *       ├── vif[0]: skb_clone → skb_cow → TTL-- → ip_local_out
 *       │
 *       ├── vif[1]: skb_clone → skb_cow → TTL-- → ip_local_out
 *       │
 *       ├── vif[2]: skb_clone → skb_cow → TTL-- → ip_local_out
 *       │
 *       └── vif[last]: use original → skb_cow → TTL-- → ip_local_out
 *                      (no clone needed for last output)
 */
```

### 12.3 Netfilter NAT — Copy-on-Write Before Header Modification

The NAT subsystem in Netfilter must rewrite IP addresses and transport-layer
ports. Since the sk_buff may be shared (e.g., with a packet socket or the
conntrack entry), NAT uses `skb_cow()` before modifying:

```c
/*
 * Simplified from net/netfilter/nf_nat_proto.c
 *
 * Mangle the source IP address of a packet (SNAT).
 */
static void nf_nat_manip_pkt(struct sk_buff *skb,
                              const struct nf_conntrack_tuple *target)
{
    struct iphdr *iph;
    struct tcphdr *th;

    /*
     * Ensure we have a writable copy of the IP and TCP headers.
     * The sk_buff might be cloned by packet capture or connection
     * tracking, so we must cow before modifying.
     *
     * We need writable access to at least:
     *   IP header (20 bytes) + TCP header (20-60 bytes)
     */
    if (skb_cow(skb, 0)) {
        /* skb_cow failed — drop the packet */
        return;
    }

    /*
     * IMPORTANT: Re-derive all header pointers after skb_cow().
     * The buffer may have been reallocated.
     */
    iph = ip_hdr(skb);

    /* Rewrite the source IP address */
    __be32 old_saddr = iph->saddr;
    iph->saddr = target->src.u3.ip;

    /* Incrementally update the IP checksum */
    csum_replace4(&iph->check, old_saddr, iph->saddr);

    /* Rewrite the TCP source port */
    th = tcp_hdr(skb);
    __be16 old_sport = th->source;
    th->source = target->src.u.tcp.port;

    /* Incrementally update the TCP checksum */
    inet_proto_csum_replace4(&th->check, skb,
                             old_saddr, iph->saddr, true);
    inet_proto_csum_replace2(&th->check, skb,
                             old_sport, th->source, false);
}
```

### 12.4 Tunnel Encapsulation (VXLAN)

VXLAN encapsulation requires adding 50+ bytes of outer headers. The original
sk_buff typically lacks sufficient headroom, so `skb_cow_head()` or
`skb_copy_expand()` is used:

```c
/*
 * Simplified from drivers/net/vxlan/vxlan_core.c
 *
 * Encapsulate a packet in a VXLAN tunnel.
 */
static int vxlan_build_skb(struct sk_buff *skb,
                           struct net_device *dev,
                           struct vxlan_rdst *rdst)
{
    struct vxlan_dev *vxlan = netdev_priv(dev);
    int headroom;

    /*
     * Calculate required headroom for the outer headers:
     *   Outer Ethernet   = 14 bytes
     *   Outer IP         = 20 bytes (IPv4) or 40 bytes (IPv6)
     *   Outer UDP        = 8 bytes
     *   VXLAN header     = 8 bytes
     *   Total (IPv4)     = 50 bytes
     *
     * Plus LL_RESERVED_SPACE for the output device's L2 header.
     */
    headroom = LL_RESERVED_SPACE(vxlan->dev) +
               sizeof(struct iphdr) +
               sizeof(struct udphdr) +
               sizeof(struct vxlanhdr);

    /*
     * Use skb_cow_head to ensure writable headroom.
     * This is more efficient than skb_copy_expand because:
     * 1. If headroom is already sufficient and not cloned, no-op
     * 2. If headroom is insufficient, only reallocates the head
     * 3. Paged fragment payload remains shared (not copied)
     */
    if (skb_cow_head(skb, headroom)) {
        kfree_skb(skb);
        return -ENOMEM;
    }

    /*
     * Now build the tunnel headers from inside out:
     */

    /* 1. VXLAN header */
    struct vxlanhdr *vxh;
    vxh = __skb_push(skb, sizeof(*vxh));
    vxh->vx_flags = htonl(VXLAN_HF_VNI);
    vxh->vx_vni   = vxlan_vni_field(rdst->remote_vni);

    /* 2. Outer UDP header */
    struct udphdr *uh;
    uh = __skb_push(skb, sizeof(*uh));
    uh->dest   = vxlan->cfg.dst_port;
    uh->source = udp_flow_src_port(dev_net(dev), skb, 0, 0, false);
    uh->len    = htons(skb->len);
    uh->check  = 0;

    /* 3. Set up for outer IP header (handled by ip_tunnel_xmit) */
    skb_reset_inner_headers(skb);
    skb->encapsulation = 1;

    return 0;
}
```

### 12.5 TCP Retransmission — Cloning from the Retransmit Queue

When TCP retransmits a segment, it does not remove the sk_buff from the
retransmit queue. Instead, it clones the sk_buff and sends the clone:

```c
/*
 * Simplified from net/ipv4/tcp_output.c: __tcp_retransmit_skb()
 *
 * Retransmit a TCP segment.
 */
int __tcp_retransmit_skb(struct sock *sk, struct sk_buff *skb, int segs)
{
    struct sk_buff *nskb;
    struct tcp_sock *tp = tcp_sk(sk);

    /*
     * We cannot send the original sk_buff because it must remain
     * in the retransmit queue (sk->tcp_rtx_queue) in case we
     * need to retransmit again, or until it is acknowledged.
     *
     * Clone the sk_buff. The clone will be sent to the IP layer
     * for transmission, while the original stays in the queue.
     */
    if (skb_cloned(skb)) {
        /*
         * The skb is already cloned (maybe from a previous
         * retransmit attempt). We need a writable copy because
         * we may need to update TCP header fields (sequence
         * number, window, timestamp options).
         */
        nskb = pskb_copy(skb, GFP_ATOMIC);
    } else {
        /*
         * Not cloned yet — clone it. This shares the data
         * buffer (cheap) and allows us to keep the original.
         */
        nskb = skb_clone(skb, GFP_ATOMIC);
    }

    if (!nskb)
        return -ENOBUFS;

    /*
     * Now we may need to modify TCP header fields on the clone.
     * Since the clone shares data with the original, we must
     * ensure the header area is writable.
     */
    if (skb_cow(nskb, 0)) {
        kfree_skb(nskb);
        return -ENOBUFS;
    }

    /* Update TCP header fields */
    struct tcphdr *th = tcp_hdr(nskb);
    th->ack_seq = htonl(tp->rcv_nxt);       /* current ACK number */
    th->window  = htons(tcp_select_window(sk)); /* current window */

    /* Update TCP timestamp option if present */
    tcp_replace_ts_recent(tp, TCP_SKB_CB(skb)->seq);

    /* Recalculate TCP checksum */
    tcp_send_check(sk, nskb);

    /*
     * Queue the clone for transmission.
     * The original remains in the retransmit queue.
     */
    tcp_transmit_skb(sk, nskb, 0, GFP_ATOMIC);

    /* Update retransmission statistics */
    TCP_INC_STATS(sock_net(sk), TCP_MIB_RETRANSSEGS);

    return 0;
}

/*
 * Retransmission flow:
 *
 *  tcp_rtx_queue (doubly-linked list in the socket):
 *  ┌──────┐    ┌──────┐    ┌──────┐
 *  │ skb1 │───►│ skb2 │───►│ skb3 │───► NULL
 *  └──┬───┘    └──┬───┘    └──┬───┘
 *     │           │           │
 *     │    retransmit skb2:   │
 *     │           │           │
 *     │     skb_clone(skb2)   │
 *     │           │           │
 *     │           ▼           │
 *     │     ┌──────────┐     │
 *     │     │ clone    │     │
 *     │     │ (sent to │     │
 *     │     │  IP layer│     │
 *     │     │  for tx) │     │
 *     │     └──────────┘     │
 *     │                      │
 *     │  skb2 remains in     │
 *     │  the rtx queue       │
 *     │  until ACK received  │
 */
```

### 12.6 Bridge Forwarding — Clone per Port

The Linux bridge forwards frames to multiple ports. Each port gets its own
clone:

```c
/*
 * Simplified from net/bridge/br_forward.c
 *
 * Deliver a frame to a single bridge port.
 */
static void __br_deliver(const struct net_bridge_port *to,
                         struct sk_buff *skb)
{
    /* Set the output device to the bridge port's device */
    skb->dev = to->dev;

    /* Modify the L2 header if needed */
    if (skb_cow_head(skb, LL_RESERVED_SPACE(to->dev))) {
        kfree_skb(skb);
        return;
    }

    /* Forward the frame */
    dev_queue_xmit(skb);
}

/*
 * Flood a frame to all ports except the source.
 */
void br_flood(struct net_bridge *br, struct sk_buff *skb,
              enum br_pkt_type pkt_type,
              bool local_rcv, bool local_orig)
{
    struct net_bridge_port *p;
    struct sk_buff *skb2;
    struct net_bridge_port *prev = NULL;

    list_for_each_entry_rcu(p, &br->port_list, list) {
        if (should_deliver(p, skb)) {
            if (prev) {
                /*
                 * Clone for the previous port.
                 * We defer delivery so that the LAST port
                 * can reuse the original sk_buff (no clone).
                 */
                skb2 = skb_clone(skb, GFP_ATOMIC);
                if (skb2)
                    __br_deliver(prev, skb2);
            }
            prev = p;
        }
    }

    if (prev) {
        /*
         * Last port: deliver the original sk_buff.
         * No clone needed — this is an optimization.
         */
        __br_deliver(prev, skb);
    } else {
        kfree_skb(skb);  /* No ports to deliver to */
    }
}
```

### 12.7 IPsec Encapsulation — Expanding for ESP Headers

IPsec ESP (Encapsulating Security Payload) requires adding an ESP header, IV
(Initialization Vector), padding, and an ESP trailer. This requires both
headroom and tailroom expansion:

```c
/*
 * Simplified from net/ipv4/esp4.c
 *
 * Encapsulate a packet with ESP.
 */
static int esp_output(struct xfrm_state *x, struct sk_buff *skb)
{
    struct esp_info esp;
    int nfrags;

    /* Calculate space needed */
    int blksize = ALIGN(crypto_aead_blocksize(aead), 4);
    int clen = ALIGN(skb->len + 2, blksize);        /* padded length */
    int alen = crypto_aead_authsize(aead);           /* auth tag size */
    int plen = clen - skb->len;                      /* padding length */
    int tfclen = 0;
    int tailen = plen + alen;                        /* tail expansion */
    int headlen = sizeof(struct ip_esp_hdr) + crypto_aead_ivsize(aead);

    /*
     * Ensure we have enough headroom for the ESP header + IV
     * and enough tailroom for padding + authentication tag.
     *
     * Use skb_cow_data() which is similar to skb_cow() but
     * also handles the tail and fragment pages for crypto.
     */
    nfrags = skb_cow_data(skb, tailen, &trailer);
    if (nfrags < 0)
        return nfrags;

    /* Ensure headroom */
    if (skb_headroom(skb) < headlen) {
        if (pskb_expand_head(skb, headlen, 0, GFP_ATOMIC))
            return -ENOMEM;
    }

    /* Push ESP header */
    struct ip_esp_hdr *esph;
    esph = __skb_push(skb, headlen);
    esph->spi = x->id.spi;
    esph->seq_no = htonl(XFRM_SKB_CB(skb)->seq.output.low);

    /* ... perform encryption, add padding and auth tag ... */

    return 0;
}
```

### 12.8 Network Taps and Traffic Mirroring

The `tc` (traffic control) subsystem supports packet mirroring via the `mirred`
action, which clones packets and redirects them to another interface:

```c
/*
 * Simplified from net/sched/act_mirred.c
 *
 * Mirror or redirect a packet to another device.
 */
static int tcf_mirred_act(struct sk_buff *skb, const struct tc_action *a,
                          struct tcf_result *res)
{
    struct tcf_mirred *m = to_mirred(a);
    struct net_device *dev = rcu_dereference(m->tcfm_dev);
    struct sk_buff *skb2;
    int retval;

    if (m->tcfm_eaction == TCA_EGRESS_MIRROR) {
        /*
         * MIRROR: Send a copy to the target device,
         * but let the original continue through the pipeline.
         *
         * skb_clone is used because:
         * 1. The original must continue unmodified
         * 2. The mirror only needs to READ the data
         * 3. Cloning is O(1) — critical for high-speed mirroring
         */
        skb2 = skb_clone(skb, GFP_ATOMIC);
        if (!skb2)
            goto out;

        skb2->dev = dev;

        /* May need to adjust headroom for the new device's L2 */
        if (skb_cow_head(skb2, LL_RESERVED_SPACE(dev))) {
            kfree_skb(skb2);
            goto out;
        }

        dev_queue_xmit(skb2);
        retval = TC_ACT_PIPE;  /* original continues */

    } else {
        /*
         * REDIRECT: Send the original to the target device.
         * No clone needed — the original is consumed.
         */
        skb->dev = dev;
        dev_queue_xmit(skb);
        retval = TC_ACT_CONSUMED;
    }

out:
    return retval;
}
```

### 12.9 XDP and Clone Interactions

XDP (eXpress Data Path) processes packets at the driver level before sk_buff
allocation. However, when XDP passes a packet up to the normal stack via
`XDP_PASS`, an sk_buff is created. If the system has packet sockets active, the
freshly created sk_buff may be immediately cloned:

```c
/*
 * Flow when XDP_PASS is combined with packet capture:
 *
 *  ┌───────────┐
 *  │ NIC RX    │
 *  │ ring buf  │
 *  └─────┬─────┘
 *        │
 *        ▼
 *  ┌───────────┐
 *  │ XDP prog  │──── XDP_DROP ──► packet dropped (no sk_buff)
 *  │ (eBPF)    │──── XDP_TX ───► loopback to TX ring
 *  │           │──── XDP_REDIRECT► redirect to other dev/CPU
 *  └─────┬─────┘
 *        │ XDP_PASS
 *        ▼
 *  ┌───────────────┐
 *  │ Allocate       │
 *  │ sk_buff        │  (fclone variant if packet sockets active)
 *  │ (SKB_ALLOC_    │
 *  │  FCLONE)       │
 *  └─────┬──────────┘
 *        │
 *        ▼
 *  ┌───────────────────┐
 *  │ netif_receive_skb │
 *  │                   │
 *  │ ├── packet_rcv()  │──► skb_clone() for AF_PACKET
 *  │ │                 │     (uses fclone companion — fast!)
 *  │ └── ip_rcv()      │──► normal protocol processing
 *  └───────────────────┘
 */
```

### 12.10 Summary of Use Cases

```
  ┌──────────────────────────┬────────────────────┬───────────────────────┐
  │  Use Case                 │  Primary API        │  Reason               │
  ├──────────────────────────┼────────────────────┼───────────────────────┤
  │  Packet capture           │  skb_clone()        │  Read-only; fast      │
  │  Multicast forwarding     │  skb_clone + cow    │  Clone per port,      │
  │                           │                     │  cow before TTL--     │
  │  NAT (Netfilter)          │  skb_cow()          │  Unshare headers      │
  │  VXLAN encapsulation      │  skb_cow_head()     │  Add outer headers    │
  │  GRE encapsulation        │  skb_cow_head()     │  Add outer headers    │
  │  IPsec ESP                │  skb_cow_data()     │  Head + tail for      │
  │                           │  + pskb_expand_head │  crypto overhead      │
  │  TCP retransmit           │  skb_clone() or     │  Keep in rtx queue,   │
  │                           │  pskb_copy()        │  send clone           │
  │  Bridge flooding          │  skb_clone()        │  Clone per port       │
  │  TC mirroring             │  skb_clone()        │  Mirror is read-only  │
  │  Fragmentation            │  skb_copy() or      │  Each fragment is     │
  │                           │  alloc + copy_bits  │  independent          │
  │  Socket buffer coalesce   │  skb_copy_bits()    │  Merge into existing  │
  │  Protocol conversion      │  skb_copy_expand()  │  Need different room  │
  └──────────────────────────┴────────────────────┴───────────────────────┘
```

---

## 13. Advanced Topics

### 13.1 skb_cow_data(skb, tailbits, trailer)

`skb_cow_data()` is used by cryptographic subsystems (IPsec, SCTP
authentication) that need to ensure ALL data in the sk_buff is writable --
including paged fragments. This is more aggressive than `skb_cow()`, which only
ensures the linear (header) area is writable:

```c
/**
 * skb_cow_data - ensure all data in sk_buff is writable
 * @skb: buffer to make writable
 * @tailbits: additional tailroom needed
 * @trailer: output parameter — pointer to the last sk_buff in frag_list
 *
 * Ensures that the entire data area of @skb (including all paged
 * fragments and frag_list entries) can be modified. This may require
 * linearizing parts of the data or cloning fragment pages.
 *
 * Returns the number of fragments on success, or negative errno.
 */
int skb_cow_data(struct sk_buff *skb, int tailbits,
                 struct sk_buff **trailer)
{
    int copyflag;
    int elt;
    struct sk_buff *skb1, **skb_p;

    /* Check if the linear area needs to be unshared */
    if ((skb_cloned(skb) || skb_shinfo(skb)->nr_frags) &&
        __pskb_pull_tail(skb, skb_pagelen(skb) - skb_headlen(skb)) == NULL)
        return -ENOMEM;

    /* Ensure tailroom */
    if (skb_tailroom(skb) < tailbits &&
        pskb_expand_head(skb, 0, tailbits - skb_tailroom(skb) + 128,
                         GFP_ATOMIC))
        return -ENOMEM;

    /* Walk the frag_list and ensure each entry is also writable */
    elt = 1;
    skb_p = &skb_shinfo(skb)->frag_list;
    skb1 = *skb_p;

    while (skb1) {
        if (skb_cloned(skb1) || skb_shinfo(skb1)->nr_frags) {
            struct sk_buff *skb2 = skb_copy(skb1, GFP_ATOMIC);
            if (!skb2)
                return -ENOMEM;
            skb2->next = skb1->next;
            *skb_p = skb2;
            kfree_skb(skb1);
            skb1 = skb2;
        }
        elt++;
        skb_p = &skb1->next;
        skb1 = skb1->next;
    }

    *trailer = skb;  /* or last frag_list entry */
    return elt;
}
```

### 13.2 skb_unshare(skb, pri)

`skb_unshare()` ensures that the sk_buff is not shared with anyone. If it is
cloned, a full copy is made and the original is freed:

```c
/**
 * skb_unshare - make a copy of a shared buffer
 * @skb: buffer to check
 * @pri: priority for memory allocation
 *
 * If the buffer is shared (refcount > 1 or cloned), make a copy
 * and free the original. The caller must use the returned sk_buff.
 *
 * Returns the (possibly new) sk_buff, or NULL on failure.
 * NOTE: The input skb is consumed on success (caller must not
 * reference it after this call).
 */
static inline struct sk_buff *skb_unshare(struct sk_buff *skb,
                                           gfp_t pri)
{
    might_sleep_if(gfpflags_allow_blocking(pri));

    if (skb_cloned(skb)) {
        struct sk_buff *nskb = skb_copy(skb, pri);
        kfree_skb(skb);  /* free the original (or decrement ref) */
        skb = nskb;
    }
    return skb;
}
```

### 13.3 skb_share_check(skb, pri)

Similar to `skb_unshare()`, but only checks the `users` reference count (not
`cloned`/`dataref`). Used when you need exclusive ownership of the sk_buff
structure but don't necessarily need to modify the data:

```c
static inline struct sk_buff *skb_share_check(struct sk_buff *skb,
                                               gfp_t pri)
{
    might_sleep_if(gfpflags_allow_blocking(pri));

    if (skb_shared(skb)) {
        struct sk_buff *nskb = skb_clone(skb, pri);
        if (likely(nskb))
            consume_skb(skb);
        return nskb;
    }
    return skb;
}

static inline int skb_shared(const struct sk_buff *skb)
{
    return refcount_read(&skb->users) != 1;
}
```

### 13.4 Memory Allocation Context and GFP Flags

The GFP (Get Free Pages) flags passed to clone/copy functions determine the
memory allocation behavior:

```
  ┌──────────────────┬──────────────────────────────────────────────────┐
  │  GFP Flag         │  Context and Behavior                           │
  ├──────────────────┼──────────────────────────────────────────────────┤
  │  GFP_ATOMIC       │  Used in interrupt context, softirq, and       │
  │                   │  anywhere that cannot sleep. Tries to allocate  │
  │                   │  from pre-allocated reserves. May fail.         │
  │                   │  Most common in networking hot paths.           │
  ├──────────────────┼──────────────────────────────────────────────────┤
  │  GFP_KERNEL       │  Used in process context (syscall handlers,    │
  │                   │  workqueues). Can sleep and trigger reclaim.    │
  │                   │  Higher chance of success. Used in socket ops.  │
  ├──────────────────┼──────────────────────────────────────────────────┤
  │  GFP_NOIO         │  Process context but cannot initiate I/O.      │
  │                   │  Used when the allocation is on the I/O path   │
  │                   │  to avoid deadlocks.                            │
  └──────────────────┴──────────────────────────────────────────────────┘
```

Usage patterns in clone/copy:

```c
/* In the receive path (softirq context) — must use GFP_ATOMIC */
struct sk_buff *clone = skb_clone(skb, GFP_ATOMIC);

/* In a socket sendmsg handler (process context) — can use GFP_KERNEL */
struct sk_buff *copy = skb_copy(skb, GFP_KERNEL);

/* In a workqueue processing deferred packets */
struct sk_buff *expanded = skb_copy_expand(skb, extra_head, 0, GFP_KERNEL);
```

### 13.5 NUMA Awareness

On NUMA (Non-Uniform Memory Access) systems, the kernel tries to allocate
sk_buff structures and data buffers on the NUMA node closest to the CPU that
will process them. This is controlled by the `node` parameter in allocation
functions:

```c
/* Allocate sk_buff on the NUMA node of the receiving CPU */
struct sk_buff *skb = __alloc_skb(size, GFP_ATOMIC, 0,
                                  cpu_to_node(smp_processor_id()));

/*
 * When cloning, the clone is allocated from the slab cache
 * associated with the current NUMA node by default.
 */
```

---

## 14. Debugging and Tracing

### 14.1 Tracepoints for Clone/Copy Operations

The kernel provides tracepoints that can be used to observe clone and copy
operations in real time:

```
  Available tracepoints (examples):

  skb:skb_clone          — fires when skb_clone() is called
  skb:skb_copy           — fires when skb_copy() is called
  skb:kfree_skb          — fires when an sk_buff is freed
  skb:consume_skb        — fires when an sk_buff is consumed (not dropped)

  Usage with perf:
  $ perf trace -e 'skb:*' -- sleep 10

  Usage with ftrace:
  # echo 1 > /sys/kernel/debug/tracing/events/skb/skb_clone/enable
  # cat /sys/kernel/debug/tracing/trace_pipe
```

### 14.2 Common Bugs Related to Cloning/Copying

```
  ┌──────────────────────────────────────────────────────────────────┐
  │  Bug Pattern                │  Symptom              │  Fix       │
  ├─────────────────────────────┼───────────────────────┼────────────┤
  │  Modifying cloned data      │  Corrupted packets    │  skb_cow() │
  │  without cow                │  in other consumers   │  before    │
  │                             │                       │  modify    │
  ├─────────────────────────────┼───────────────────────┼────────────┤
  │  Using stale pointer after  │  Use-after-free,      │  Re-derive │
  │  skb_cow/expand             │  kernel oops          │  pointers  │
  │                             │                       │  after cow │
  ├─────────────────────────────┼───────────────────────┼────────────┤
  │  Forgetting to free old skb │  Memory leak          │  kfree_skb │
  │  after skb_realloc_headroom │                       │  or consume│
  ├─────────────────────────────┼───────────────────────┼────────────┤
  │  Cloning in a loop without  │  OOM under load       │  Check     │
  │  checking return value      │                       │  for NULL  │
  ├─────────────────────────────┼───────────────────────┼────────────┤
  │  Calling skb_linearize on   │  Huge allocation,     │  Use       │
  │  jumbo/GSO frames           │  likely failure       │  helpers   │
  │                             │                       │  instead   │
  └──────────────────────────────────────────────────────────────────┘
```

### 14.3 Inspecting sk_buff State with crash/gdb

When debugging kernel crashes involving sk_buff cloning, the following fields
are most informative:

```
  (crash) struct sk_buff <address>
  Key fields to examine:
    users.refs.counter    — reference count of the sk_buff struct
    cloned                — 1 if data is shared via clone
    fclone                — 0 (unavailable), 1 (orig), 2 (clone)
    head                  — start of the data buffer
    data                  — start of the packet data
    tail                  — end of the packet data
    end                   — end of the data buffer (start of shared_info)

  (crash) struct skb_shared_info <skb->end address>
  Key fields:
    dataref.counter       — number of sk_buffs sharing this buffer
    nr_frags              — number of paged fragments
    frag_list             — pointer to chained sk_buffs
```

---

## 15. API Quick Reference

### 15.1 Complete Function Signatures

```c
/* ─── Cloning ─────────────────────────────────────────────────── */

struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask);
    /* Share data buffer. New sk_buff only. O(1). */

/* ─── Copying ─────────────────────────────────────────────────── */

struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t gfp_mask);
    /* Full independent copy. Linearizes. O(n). */

struct sk_buff *pskb_copy(struct sk_buff *skb, gfp_t gfp_mask);
    /* Copy linear area, share fragments. O(headlen). */

struct sk_buff *skb_copy_expand(const struct sk_buff *skb,
                                int newheadroom, int newtailroom,
                                gfp_t gfp_mask);
    /* Full copy with new headroom/tailroom. Linearizes. O(n). */

/* ─── Copy-on-Write ───────────────────────────────────────────── */

int skb_cow(struct sk_buff *skb, unsigned int headroom);
    /* Ensure writable data + headroom. In-place. */

int skb_cow_head(struct sk_buff *skb, unsigned int headroom);
    /* Ensure writable headroom only. In-place. */

int skb_cow_data(struct sk_buff *skb, int tailbits,
                 struct sk_buff **trailer);
    /* Ensure ALL data (including frags) writable. */

/* ─── Expansion ───────────────────────────────────────────────── */

int pskb_expand_head(struct sk_buff *skb, int nhead, int ntail,
                     gfp_t gfp_mask);
    /* Expand linear buffer in-place. Core reallocation function. */

struct sk_buff *skb_realloc_headroom(struct sk_buff *skb,
                                     unsigned int headroom);
    /* Returns NEW sk_buff with specified headroom. */

/* ─── Linearization ───────────────────────────────────────────── */

int skb_linearize(struct sk_buff *skb);
    /* Pull all paged data into linear area. */

void *__pskb_pull_tail(struct sk_buff *skb, int delta);
    /* Pull delta bytes from non-linear to linear area. */

/* ─── Sharing Checks ──────────────────────────────────────────── */

int skb_cloned(const struct sk_buff *skb);
    /* True if data buffer is shared. */

int skb_shared(const struct sk_buff *skb);
    /* True if sk_buff struct has users > 1. */

int skb_header_cloned(const struct sk_buff *skb);
    /* True if header area specifically is shared. */

struct sk_buff *skb_unshare(struct sk_buff *skb, gfp_t pri);
    /* Make an unshared copy if cloned. Consumes input. */

struct sk_buff *skb_share_check(struct sk_buff *skb, gfp_t pri);
    /* Clone if shared (users > 1). Consumes input. */
```

### 15.2 Decision Matrix

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                                                                      │
  │  I need to...              Use this              Returns             │
  │  ────────────────────────  ───────────────────── ──────────────────  │
  │  Read-only second ref      skb_clone()           new sk_buff         │
  │  Modify headers only       skb_cow() / pskb_copy in-place / new skb │
  │  Modify all data           skb_copy()            new sk_buff         │
  │  Add headroom              pskb_expand_head()    0 / -ENOMEM        │
  │  Add head+tail room        skb_copy_expand()     new sk_buff         │
  │  Make everything writable  skb_cow_data()        nfrags / -ENOMEM   │
  │  Flatten fragments         skb_linearize()       0 / -ENOMEM        │
  │  Get new skb with room     skb_realloc_headroom  new sk_buff         │
  │  Ensure exclusive struct   skb_share_check()     same or new skb     │
  │  Ensure exclusive data     skb_unshare()         same or new skb     │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘
```

---

## 16. Summary

The Linux kernel's sk_buff cloning and copying infrastructure embodies a
carefully designed trade-off between performance and correctness. The key
insights are:

1. **Clone first, copy only when necessary.** `skb_clone()` is O(1) and
   allocates only ~232 bytes. It should be the default choice when a second
   reference to a packet is needed.

2. **Copy-on-write for headers.** `skb_cow()` and `skb_cow_head()` defer the
   cost of copying until a modification is actually needed, and even then, they
   copy only the linear (header) area while sharing the payload.

3. **Full copy as last resort.** `skb_copy()` and `skb_copy_expand()` produce
   fully independent, linearized buffers. They are expensive but sometimes
   unavoidable.

4. **Reference counting is the backbone.** The `dataref` field in
   `skb_shared_info` and the `users` field in `sk_buff` work together to ensure
   that buffers are freed at the right time, that shared data is not modified
   unsafely, and that the system does not leak memory.

5. **Pointer invalidation is the primary source of bugs.** After any operation
   that may reallocate the buffer (`skb_cow`, `pskb_expand_head`, etc.), all
   cached pointers into the data area must be re-derived from the updated
   sk_buff fields.

Understanding these APIs and their interactions is essential for writing correct
and performant networking code in the Linux kernel. The next chapter will build
on this foundation to examine how these operations interact with the DMA
subsystem and hardware offload features.
