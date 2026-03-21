# SKB Cloning and Queue Management - Comprehensive Guide

## Table of Contents
1. [Introduction to SKB Cloning](#introduction-to-skb-cloning)
2. [How SKB Cloning Works](#how-skb-cloning-works)
3. [Why SKB Cloning is Needed](#why-skb-cloning-is-needed)
4. [Clone vs Copy - Deep Dive](#clone-vs-copy-deep-dive)
5. [SKB List Management](#skb-list-management)
6. [SKB Queue Architecture](#skb-queue-architecture)
7. [Queue Operations and Use Cases](#queue-operations-and-use-cases)
8. [Performance Considerations](#performance-considerations)
9. [Common Patterns and Best Practices](#common-patterns-and-best-practices)

---

## Introduction to SKB Cloning

### What is an SKB?

`struct sk_buff` (Socket Buffer) is the fundamental Linux kernel data structure for network packet handling. Every network packet in the Linux kernel is represented by an `sk_buff` structure that contains:

- **Packet data**: The actual network payload
- **Metadata**: Headers, protocol information, routing data
- **Pointers**: Links to other buffers, queues, and network devices
- **Reference counts**: For memory management and sharing

### What is SKB Cloning?

SKB cloning is a **lightweight copy mechanism** that creates a new `sk_buff` structure that **shares the same packet data** with the original buffer. This is fundamentally different from copying, which duplicates both the structure and the data.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKB Clone Concept                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Original SKB                    Cloned SKB                     │
│  ┌──────────────┐               ┌──────────────┐               │
│  │  Metadata    │               │  Metadata    │               │
│  │  - headers   │               │  - headers   │               │
│  │  - pointers  │               │  - pointers  │               │
│  │  - flags     │               │  - flags     │               │
│  └──────┬───────┘               └──────┬───────┘               │
│         │                              │                        │
│         └──────────┬───────────────────┘                        │
│                    │                                            │
│                    ▼                                            │
│         ┌────────────────────┐                                  │
│         │   Shared Data      │                                  │
│         │   Buffer           │                                  │
│         │   (Packet Payload) │                                  │
│         └────────────────────┘                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Point**: Both SKBs point to the **same data buffer**, but each has its **own metadata**.

---

## How SKB Cloning Works

### The Cloning Process

SKB cloning in Linux involves two main functions:

1. **`skb_clone()`** - Public API that handles allocation
2. **`__skb_clone()`** - Internal worker that performs the actual cloning

### Step-by-Step Cloning Flow

```c
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask)
{
    struct sk_buff *n;
    
    // Step 1: Check if fclone optimization is available
    if (skb->fclone == SKB_FCLONE_ORIG &&
        refcount_read(&fclones->fclone_ref) == 1) {
        // Use pre-allocated clone buffer (fast path)
        n = &fclones->skb2;
        refcount_set(&fclones->fclone_ref, 2);
    } else {
        // Allocate new sk_buff from cache (slow path)
        n = kmem_cache_alloc(skbuff_head_cache, gfp_mask);
        if (!n)
            return NULL;
        n->fclone = SKB_FCLONE_UNAVAILABLE;
    }
    
    // Step 2: Perform the actual cloning
    return __skb_clone(n, skb);
}
```

### Internal Cloning Mechanism

```c
struct sk_buff *__skb_clone(struct sk_buff *n, struct sk_buff *skb)
{
    // Step 1: Copy the header region (metadata)
    __copy_skb_header(n, skb);
    
    // Step 2: Set up data pointers to SHARE the same buffer
    n->head = skb->head;
    n->data = skb->data;
    n->tail = skb->tail;
    n->end = skb->end;
    
    // Step 3: Increment reference count on shared data
    refcount_set(&n->users, 1);
    atomic_inc(&(skb_shinfo(skb)->dataref));
    
    // Step 4: Mark as cloned
    n->cloned = 1;
    skb->cloned = 1;
    
    // Step 5: Clear destructor (only original should free)
    n->destructor = NULL;
    
    return n;
}
```

### What Gets Copied vs Shared

| Component | Cloned? | Shared? | Notes |
|-----------|---------|---------|-------|
| `sk_buff` structure | ✅ Copied | ❌ | Each clone has its own metadata |
| Packet data buffer | ❌ | ✅ Shared | Points to same memory |
| `skb_shared_info` | ❌ | ✅ Shared | Fragment info, destructor |
| Header pointers | ✅ Copied | ❌ | But point to shared data |
| Protocol fields | ✅ Copied | ❌ | Can be modified independently |
| Reference count | ✅ New | ❌ | Each starts with refcount=1 |
| Data reference count | ❌ | ✅ Shared | Tracks how many SKBs share data |

### The Fclone Optimization

Linux uses a clever optimization called **fclone** (fast clone) to avoid memory allocation overhead:

```c
struct sk_buff_fclones {
    struct sk_buff  skb1;           // Original SKB
    struct sk_buff  skb2;           // Pre-allocated clone
    refcount_t      fclone_ref;     // Shared reference count
};
```

**How it works:**

1. When allocating an SKB with `__alloc_skb()`, you can request fclone support
2. The allocator allocates space for **two** `sk_buff` structures at once
3. When `skb_clone()` is called, it uses the pre-allocated `skb2` (no allocation needed!)
4. This is **much faster** than allocating from the slab cache

```
┌────────────────────────────────────────────────────────────────┐
│              Fclone Memory Layout                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  struct sk_buff_fclones                                  │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  skb1 (original)                                   │  │ │
│  │  │  - fclone = SKB_FCLONE_ORIG                        │  │ │
│  │  │  - all normal sk_buff fields                       │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │  skb2 (pre-allocated clone)                        │  │ │
│  │  │  - fclone = SKB_FCLONE_CLONE                       │  │ │
│  │  │  - ready to use when cloning                       │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │  fclone_ref (shared reference count)                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Memory Management During Cloning

The key to understanding cloning is the **dual reference counting** system:

1. **`skb->users`** - Counts references to the `sk_buff` structure itself
2. **`skb_shinfo(skb)->dataref`** - Counts how many SKBs share the data buffer

```c
// Example: Cloning increases dataref but not users
struct sk_buff *original = alloc_skb(1500, GFP_KERNEL);
// original->users = 1
// dataref = 1

struct sk_buff *clone = skb_clone(original, GFP_KERNEL);
// original->users = 1 (unchanged)
// clone->users = 1 (new)
// dataref = 2 (incremented!)

// When freeing:
kfree_skb(clone);
// clone->users = 0 → free sk_buff structure
// dataref = 1 (decremented)

kfree_skb(original);
// original->users = 0 → free sk_buff structure
// dataref = 0 → free data buffer!
```

**Critical Rule**: The data buffer is only freed when **both** conditions are met:
- All `sk_buff` structures referencing it have been freed
- `dataref` reaches zero

---

## Why SKB Cloning is Needed

SKB cloning is essential for many networking operations. Here are the primary use cases:

### 1. Packet Sniffing (tcpdump, Wireshark)

When you run `tcpdump`, the kernel needs to:
- Send the packet to the network interface (original path)
- Send a copy to the packet capture socket (for tcpdump)

**Without cloning**: Would need to copy entire packet data (expensive!)
**With cloning**: Clone the SKB, send both through different paths (cheap!)

```c
// Simplified packet capture flow
void packet_capture(struct sk_buff *skb)
{
    struct sk_buff *clone;

    // Clone for packet capture
    clone = skb_clone(skb, GFP_ATOMIC);
    if (clone) {
        // Send clone to capture socket
        deliver_to_capture_socket(clone);
    }

    // Original continues normal path
    netif_rx(skb);
}
```

### 2. TCP Retransmission

TCP must keep packets until they're acknowledged. If a packet is lost, it needs to be retransmitted.

**Problem**: Can't free the packet after sending (might need to retransmit)
**Solution**: Clone the packet, send the clone, keep the original

```c
// Simplified TCP transmission
int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb)
{
    struct sk_buff *clone;

    // Clone for transmission
    clone = skb_clone(skb, GFP_ATOMIC);
    if (!clone)
        return -ENOMEM;

    // Send the clone
    ip_queue_xmit(sk, clone, 1);

    // Keep original in retransmit queue
    tcp_add_to_retransmit_queue(sk, skb);

    return 0;
}
```

### 3. Multicast and Broadcast

When sending to multiple destinations, each needs its own copy of the packet.

**Scenario**: Sending a broadcast packet to 10 interfaces
**Without cloning**: Copy packet data 10 times (10x memory, 10x CPU)
**With cloning**: Clone SKB 10 times, share data (minimal overhead)

```c
// Simplified multicast delivery
void multicast_deliver(struct sk_buff *skb, struct net_device *dev)
{
    struct list_head *p;

    list_for_each(p, &multicast_list) {
        struct mc_member *member = list_entry(p, struct mc_member, list);
        struct sk_buff *clone;

        // Clone for each member
        clone = skb_clone(skb, GFP_ATOMIC);
        if (clone) {
            clone->dev = member->dev;
            dev_queue_xmit(clone);
        }
    }

    // Free original
    kfree_skb(skb);
}
```

### 4. Network Bridging

Bridges forward packets between interfaces. The packet needs to:
- Be processed by the bridge
- Be forwarded to destination interface(s)

```c
// Simplified bridge forwarding
void br_forward(struct net_bridge_port *to, struct sk_buff *skb)
{
    struct sk_buff *clone;

    // Clone for forwarding
    clone = skb_clone(skb, GFP_ATOMIC);
    if (clone) {
        clone->dev = to->dev;
        br_forward_finish(clone);
    }
}
```

### 5. QoS and Traffic Shaping

Quality of Service (QoS) systems may need to:
- Queue packets for later transmission
- Keep statistics on packet flows
- Mirror traffic for monitoring

All of these benefit from cloning rather than copying.

### 6. IPsec and VPN Tunneling

When encapsulating packets for VPN:
- Original packet may need to be kept for error handling
- Encapsulated version is sent
- Cloning allows both to exist efficiently

### Why Not Just Copy?

**Memory Efficiency**:
- Typical packet: 1500 bytes of data + ~200 bytes of sk_buff
- Clone: Allocate only ~200 bytes (sk_buff structure)
- Copy: Allocate ~1700 bytes (sk_buff + data)
- **Savings: ~88% less memory allocation**

**CPU Efficiency**:
- Clone: Copy ~200 bytes of metadata, increment counter
- Copy: Copy ~1700 bytes of data + metadata
- **Savings: ~88% less memory copying**

**Cache Efficiency**:
- Shared data stays in CPU cache
- Multiple SKBs can reference hot cache lines
- Better cache utilization = faster processing

---

## Clone vs Copy - Deep Dive

### The Two Operations

Linux provides two distinct operations for duplicating SKBs:

| Operation | Function | Data Sharing | Use Case |
|-----------|----------|--------------|----------|
| **Clone** | `skb_clone()` | ✅ Shares data | Read-only operations, forwarding |
| **Copy** | `skb_copy()` | ❌ Duplicates data | Modifications needed |

### Clone: skb_clone()

```c
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask);
```

**What it does:**
- Allocates new `sk_buff` structure
- Copies metadata (headers, pointers, flags)
- **Shares** the data buffer
- Increments data reference count

**When to use:**
- Packet forwarding
- Packet capture
- Multicast delivery
- Any read-only operation

**Restrictions:**
- **Cannot modify shared data** (will affect all clones)
- Must call `pskb_expand_head()` or `skb_unshare()` before modifying

### Copy: skb_copy()

```c
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t gfp_mask);
```

**What it does:**
- Allocates new `sk_buff` structure
- Copies metadata
- **Allocates new data buffer**
- **Copies all packet data**

**When to use:**
- Need to modify packet data
- Need independent copies
- Packet transformation (NAT, encryption)

**Cost:**
- Much more expensive than cloning
- Allocates and copies full packet size

### Visual Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLONE vs COPY                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CLONE (skb_clone):                                             │
│  ┌──────────┐         ┌──────────┐                             │
│  │ Original │         │  Clone   │                             │
│  │   SKB    │         │   SKB    │                             │
│  └────┬─────┘         └────┬─────┘                             │
│       │                    │                                    │
│       └────────┬───────────┘                                    │
│                ▼                                                │
│         ┌─────────────┐                                         │
│         │ Shared Data │  ← Only ONE data buffer                │
│         └─────────────┘                                         │
│                                                                 │
│  COPY (skb_copy):                                               │
│  ┌──────────┐         ┌──────────┐                             │
│  │ Original │         │   Copy   │                             │
│  │   SKB    │         │   SKB    │                             │
│  └────┬─────┘         └────┬─────┘                             │
│       │                    │                                    │
│       ▼                    ▼                                    │
│  ┌─────────┐         ┌─────────┐                               │
│  │ Data 1  │         │ Data 2  │  ← TWO separate buffers       │
│  └─────────┘         └─────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Making Clones Writable: skb_unshare()

If you have a clone but need to modify it, use `skb_unshare()`:

```c
struct sk_buff *skb_unshare(struct sk_buff *skb, gfp_t pri);
```

**What it does:**
- Checks if SKB is shared (`skb_shared(skb)`)
- If shared: creates a full copy and frees the clone
- If not shared: returns the original SKB unchanged

```c
// Example: Safely modifying an SKB
int modify_packet(struct sk_buff *skb)
{
    // Make sure we have exclusive access to data
    skb = skb_unshare(skb, GFP_ATOMIC);
    if (!skb)
        return -ENOMEM;

    // Now safe to modify
    struct iphdr *iph = ip_hdr(skb);
    iph->ttl--;

    return 0;
}
```

### Partial Copy: pskb_copy()

For packets with fragments (scatter-gather), there's a middle ground:

```c
struct sk_buff *pskb_copy(struct sk_buff *skb, gfp_t gfp_mask);
```

**What it does:**
- Copies the linear data (head to tail)
- **Shares** the fragments (paged data)
- Useful for modifying headers while keeping payload shared

---

## SKB List Management

SKBs are frequently organized into lists for various purposes. Linux provides multiple list structures:

### 1. Simple Linked Lists

The basic `sk_buff` structure contains `next` and `prev` pointers:

```c
struct sk_buff {
    struct sk_buff *next;
    struct sk_buff *prev;
    // ... other fields
};
```

**Operations:**

```c
// Add SKB to end of list
void skb_append(struct sk_buff *old, struct sk_buff *newsk)
{
    newsk->next = old->next;
    newsk->prev = old;
    old->next->prev = newsk;
    old->next = newsk;
}

// Remove SKB from list
void skb_unlink(struct sk_buff *skb)
{
    skb->next->prev = skb->prev;
    skb->prev->next = skb->next;
    skb->next = skb->prev = NULL;
}

// Iterate through list
struct sk_buff *skb;
for (skb = list_head; skb != NULL; skb = skb->next) {
    // Process skb
}
```

### 2. Fragment Lists (frag_list)

For large packets that need to be fragmented:

```c
struct sk_buff {
    struct sk_buff *next;
    struct sk_buff *prev;
    // ...
    struct sk_buff *frag_list;  // List of fragments
};
```

**Use case**: IP fragmentation, GSO (Generic Segmentation Offload)

```c
// Example: Building a fragmented packet
struct sk_buff *head = alloc_skb(1500, GFP_KERNEL);
struct sk_buff *frag1 = alloc_skb(1500, GFP_KERNEL);
struct sk_buff *frag2 = alloc_skb(500, GFP_KERNEL);

// Link fragments
skb_shinfo(head)->frag_list = frag1;
frag1->next = frag2;
frag2->next = NULL;

// Total length includes all fragments
head->len = head->data_len + frag1->len + frag2->len;
```

### 3. Scatter-Gather Lists (frags[])

For zero-copy operations with paged data:

```c
struct skb_shared_info {
    unsigned short nr_frags;
    skb_frag_t frags[MAX_SKB_FRAGS];
};

typedef struct skb_frag_struct {
    struct page *page;      // Page containing data
    __u32 page_offset;      // Offset within page
    __u32 size;             // Size of this fragment
} skb_frag_t;
```

**Use case**: Zero-copy networking, sendfile(), splice()

```c
// Example: Adding a page fragment
int skb_add_page_frag(struct sk_buff *skb, struct page *page,
                      int off, int size)
{
    struct skb_shared_info *shinfo = skb_shinfo(skb);

    if (shinfo->nr_frags >= MAX_SKB_FRAGS)
        return -EMSGSIZE;

    skb_frag_t *frag = &shinfo->frags[shinfo->nr_frags];
    frag->page = page;
    frag->page_offset = off;
    frag->size = size;

    shinfo->nr_frags++;
    skb->data_len += size;
    skb->len += size;

    return 0;
}
```

### SKB Data Layout with Fragments

```
┌────────────────────────────────────────────────────────────────┐
│              Complete SKB Data Layout                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  struct sk_buff                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Linear Data (head to tail)                              │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │ [Headers] [Payload Part 1]                         │  │ │
│  │  └────────────────────────────────────────────────────┘  │ │
│  │  skb->len = 1500                                         │ │
│  │  skb->data_len = 3000 (non-linear data)                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  skb_shared_info                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  frags[0] → Page 1 (1500 bytes)                          │ │
│  │  frags[1] → Page 2 (1500 bytes)                          │ │
│  │  nr_frags = 2                                            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Total packet size = skb->len + skb->data_len = 4500 bytes    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## SKB Queue Architecture

The most commonly used list structure for SKBs is the **queue** (`struct sk_buff_head`).

### Queue Structure

```c
struct sk_buff_head {
    struct sk_buff  *next;      // First SKB in queue
    struct sk_buff  *prev;      // Last SKB in queue
    __u32           qlen;       // Number of SKBs in queue
    spinlock_t      lock;       // Lock for concurrent access
};
```

**Key features:**
- **Doubly-linked circular list** with sentinel head
- **Thread-safe** with built-in spinlock
- **Length tracking** for quick size queries
- **FIFO or LIFO** operations supported

### Queue Visualization

```
┌────────────────────────────────────────────────────────────────┐
│                    SKB Queue Structure                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  struct sk_buff_head (queue head)                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  next ────────────────────────────┐                       │ │
│  │  prev ─────────────────────┐      │                       │ │
│  │  qlen = 3                  │      │                       │ │
│  │  lock                      │      │                       │ │
│  └────────────────────────────┼──────┼───────────────────────┘ │
│                               │      │                         │
│                               │      ▼                         │
│                               │  ┌────────────┐                │
│                               │  │   SKB 1    │                │
│                               │  │ next ───┐  │                │
│                               │  │ prev ◄──┼──┼─┐              │
│                               │  └─────────┼──┘ │              │
│                               │            ▼    │              │
│                               │        ┌────────┴───┐          │
│                               │        │   SKB 2    │          │
│                               │        │ next ───┐  │          │
│                               │        │ prev ◄──┼──┼─┐        │
│                               │        └─────────┼──┘ │        │
│                               │                  ▼    │        │
│                               │              ┌────────┴───┐    │
│                               │              │   SKB 3    │    │
│                               │              │ next ───┐  │    │
│                               └──────────────┤ prev ◄──┼──┼─┐  │
│                                              └─────────┼──┘ │  │
│                                                        │    │  │
│                                                        └────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Queue Initialization

```c
// Static initialization
struct sk_buff_head my_queue = {
    .next = (struct sk_buff *)&my_queue,
    .prev = (struct sk_buff *)&my_queue,
    .qlen = 0,
    .lock = __SPIN_LOCK_UNLOCKED(my_queue.lock)
};

// Or use macro
struct sk_buff_head my_queue = __SKB_QUEUE_HEAD_INIT(my_queue);

// Dynamic initialization
struct sk_buff_head my_queue;
skb_queue_head_init(&my_queue);
```

### Basic Queue Operations

#### 1. Enqueue (Add to Tail)

```c
void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_queue_tail(list, newsk);
    spin_unlock_irqrestore(&list->lock, flags);
}

// Unlocked version (caller must hold lock)
static inline void __skb_queue_tail(struct sk_buff_head *list,
                                    struct sk_buff *newsk)
{
    struct sk_buff *prev, *next;

    list->qlen++;
    next = (struct sk_buff *)list;
    prev = next->prev;
    newsk->next = next;
    newsk->prev = prev;
    next->prev = prev->next = newsk;
}
```

#### 2. Dequeue (Remove from Head)

```c
struct sk_buff *skb_dequeue(struct sk_buff_head *list)
{
    unsigned long flags;
    struct sk_buff *result;

    spin_lock_irqsave(&list->lock, flags);
    result = __skb_dequeue(list);
    spin_unlock_irqrestore(&list->lock, flags);

    return result;
}

// Unlocked version
static inline struct sk_buff *__skb_dequeue(struct sk_buff_head *list)
{
    struct sk_buff *skb = skb_peek(list);
    if (skb)
        __skb_unlink(skb, list);
    return skb;
}
```

#### 3. Peek (Look Without Removing)

```c
// Peek at head
static inline struct sk_buff *skb_peek(const struct sk_buff_head *list)
{
    struct sk_buff *skb = list->next;
    if (skb == (struct sk_buff *)list)
        skb = NULL;
    return skb;
}

// Peek at tail
static inline struct sk_buff *skb_peek_tail(const struct sk_buff_head *list)
{
    struct sk_buff *skb = list->prev;
    if (skb == (struct sk_buff *)list)
        skb = NULL;
    return skb;
}
```

#### 4. Queue Length

```c
static inline __u32 skb_queue_len(const struct sk_buff_head *list)
{
    return list->qlen;
}

static inline int skb_queue_empty(const struct sk_buff_head *list)
{
    return list->qlen == 0;
}
```

#### 5. Insert Operations

```c
// Insert after a specific SKB
void skb_insert(struct sk_buff *old, struct sk_buff *newsk,
                struct sk_buff_head *list)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_insert(newsk, old, old->next, list);
    spin_unlock_irqrestore(&list->lock, flags);
}

// Insert at head (LIFO)
void skb_queue_head(struct sk_buff_head *list, struct sk_buff *newsk)
{
    unsigned long flags;

    spin_lock_irqsave(&list->lock, flags);
    __skb_queue_head(list, newsk);
    spin_unlock_irqrestore(&list->lock, flags);
}
```

#### 6. Purge (Empty Queue)

```c
void skb_queue_purge(struct sk_buff_head *list)
{
    struct sk_buff *skb;

    while ((skb = skb_dequeue(list)) != NULL)
        kfree_skb(skb);
}
```

### Complete Queue Operation Example

```c
// Example: Packet buffering system
struct packet_buffer {
    struct sk_buff_head queue;
    unsigned int max_packets;
    unsigned int dropped;
};

// Initialize buffer
void packet_buffer_init(struct packet_buffer *buf, unsigned int max)
{
    skb_queue_head_init(&buf->queue);
    buf->max_packets = max;
    buf->dropped = 0;
}

// Add packet to buffer
int packet_buffer_add(struct packet_buffer *buf, struct sk_buff *skb)
{
    // Check if queue is full
    if (skb_queue_len(&buf->queue) >= buf->max_packets) {
        buf->dropped++;
        kfree_skb(skb);
        return -ENOSPC;
    }

    // Add to tail (FIFO)
    skb_queue_tail(&buf->queue, skb);
    return 0;
}

// Get next packet from buffer
struct sk_buff *packet_buffer_get(struct packet_buffer *buf)
{
    return skb_dequeue(&buf->queue);
}

// Cleanup buffer
void packet_buffer_cleanup(struct packet_buffer *buf)
{
    skb_queue_purge(&buf->queue);
}
```

---

## Queue Operations and Use Cases

### 1. Socket Receive Queue

Every socket has a receive queue where incoming packets wait to be read by the application:

```c
struct sock {
    struct sk_buff_head sk_receive_queue;
    // ... other fields
};

// Adding packet to socket receive queue
void sock_queue_rcv_skb(struct sock *sk, struct sk_buff *skb)
{
    skb_queue_tail(&sk->sk_receive_queue, skb);
    sk->sk_data_ready(sk);  // Wake up waiting process
}

// Application reading from socket
int sock_read(struct sock *sk, char __user *buf, size_t len)
{
    struct sk_buff *skb;

    // Get packet from queue
    skb = skb_dequeue(&sk->sk_receive_queue);
    if (!skb)
        return -EAGAIN;  // No data available

    // Copy to userspace
    if (copy_to_user(buf, skb->data, skb->len)) {
        kfree_skb(skb);
        return -EFAULT;
    }

    int ret = skb->len;
    kfree_skb(skb);
    return ret;
}
```

### 2. Network Device Transmit Queue

Network devices maintain transmit queues for outgoing packets:

```c
struct netdev_queue {
    struct sk_buff_head qdisc_queue;
    struct Qdisc *qdisc;
    // ... other fields
};

// Enqueue packet for transmission
int dev_queue_xmit(struct sk_buff *skb)
{
    struct net_device *dev = skb->dev;
    struct netdev_queue *txq = netdev_get_tx_queue(dev, 0);

    // Add to queue
    skb_queue_tail(&txq->qdisc_queue, skb);

    // Trigger transmission
    dev_hard_start_xmit(skb, dev);

    return 0;
}
```

### 3. Backlog Queue (Softirq Processing)

When packets arrive faster than they can be processed, they're queued in the backlog:

```c
struct softnet_data {
    struct sk_buff_head input_pkt_queue;
    struct sk_buff_head process_queue;
    // ... other fields
};

// Add to backlog
void enqueue_to_backlog(struct sk_buff *skb, int cpu)
{
    struct softnet_data *sd = &per_cpu(softnet_data, cpu);
    unsigned long flags;

    local_irq_save(flags);

    if (skb_queue_len(&sd->input_pkt_queue) <= netdev_max_backlog) {
        __skb_queue_tail(&sd->input_pkt_queue, skb);
        local_irq_restore(flags);
        return;
    }

    // Queue full, drop packet
    sd->dropped++;
    local_irq_restore(flags);
    kfree_skb(skb);
}
```

### 4. QoS Priority Queues

Quality of Service implementations use multiple queues with different priorities:

```c
#define NUM_PRIORITY_QUEUES 4

struct qos_scheduler {
    struct sk_buff_head queues[NUM_PRIORITY_QUEUES];
    unsigned int weights[NUM_PRIORITY_QUEUES];
};

// Initialize QoS scheduler
void qos_init(struct qos_scheduler *qos)
{
    int i;
    for (i = 0; i < NUM_PRIORITY_QUEUES; i++) {
        skb_queue_head_init(&qos->queues[i]);
        qos->weights[i] = (i + 1) * 10;  // Higher priority = higher weight
    }
}

// Enqueue with priority
void qos_enqueue(struct qos_scheduler *qos, struct sk_buff *skb, int priority)
{
    if (priority < 0 || priority >= NUM_PRIORITY_QUEUES)
        priority = 0;

    skb_queue_tail(&qos->queues[priority], skb);
}

// Dequeue using weighted round-robin
struct sk_buff *qos_dequeue(struct qos_scheduler *qos)
{
    int i;
    struct sk_buff *skb;

    // Try higher priority queues first
    for (i = NUM_PRIORITY_QUEUES - 1; i >= 0; i--) {
        if (!skb_queue_empty(&qos->queues[i])) {
            skb = skb_dequeue(&qos->queues[i]);
            return skb;
        }
    }

    return NULL;  // All queues empty
}
```

### 5. TCP Out-of-Order Queue

TCP uses queues to handle packets that arrive out of sequence:

```c
struct tcp_sock {
    struct sk_buff_head out_of_order_queue;
    // ... other fields
};

// Handle out-of-order packet
void tcp_data_queue(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);
    u32 seq = TCP_SKB_CB(skb)->seq;

    // Check if packet is in sequence
    if (seq == tp->rcv_nxt) {
        // In sequence, deliver immediately
        tcp_deliver_to_user(sk, skb);
        tp->rcv_nxt += skb->len;

        // Check if we can now deliver queued packets
        tcp_ofo_queue_process(sk);
    } else {
        // Out of order, queue it
        tcp_ofo_queue_insert(sk, skb);
    }
}

// Insert into out-of-order queue (sorted by sequence number)
void tcp_ofo_queue_insert(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);
    struct sk_buff *skb1;
    u32 seq = TCP_SKB_CB(skb)->seq;

    // Find insertion point
    skb_queue_walk(&tp->out_of_order_queue, skb1) {
        if (TCP_SKB_CB(skb1)->seq > seq)
            break;
    }

    // Insert before skb1
    __skb_queue_before(&tp->out_of_order_queue, skb1, skb);
}
```

### 6. Packet Scheduler Queues (Traffic Control)

Linux traffic control (tc) uses sophisticated queueing disciplines:

```c
// Token Bucket Filter (TBF) example
struct tbf_sched_data {
    struct sk_buff_head queue;
    u64 tokens;
    u64 rate;
    u64 burst;
    struct timer_list timer;
};

// Enqueue with rate limiting
int tbf_enqueue(struct sk_buff *skb, struct Qdisc *sch)
{
    struct tbf_sched_data *q = qdisc_priv(sch);

    // Check queue limit
    if (skb_queue_len(&q->queue) >= sch->limit) {
        qdisc_drop(skb, sch);
        return NET_XMIT_DROP;
    }

    // Add to queue
    skb_queue_tail(&q->queue, skb);

    // Schedule dequeue
    if (!timer_pending(&q->timer))
        mod_timer(&q->timer, jiffies + 1);

    return NET_XMIT_SUCCESS;
}

// Dequeue with token bucket
struct sk_buff *tbf_dequeue(struct Qdisc *sch)
{
    struct tbf_sched_data *q = qdisc_priv(sch);
    struct sk_buff *skb;

    skb = skb_peek(&q->queue);
    if (!skb)
        return NULL;

    // Check if we have enough tokens
    if (q->tokens >= skb->len) {
        skb = skb_dequeue(&q->queue);
        q->tokens -= skb->len;
        return skb;
    }

    // Not enough tokens, schedule for later
    mod_timer(&q->timer, jiffies + 1);
    return NULL;
}
```

---

## Performance Considerations

### Memory Allocation Overhead

**SKB Allocation Costs:**

| Operation | Allocations | Typical Size | Cost |
|-----------|-------------|--------------|------|
| `alloc_skb()` | 2 (skb + data) | ~200B + 1500B | High |
| `skb_clone()` | 1 (skb only) | ~200B | Low |
| `skb_copy()` | 2 (skb + data) | ~200B + 1500B | High |

**Optimization strategies:**

1. **Use cloning instead of copying** when possible
2. **Reuse SKBs** with recycling (some drivers implement this)
3. **Use fclone** for predictable clone patterns
4. **Batch allocations** to reduce allocator overhead

### Cache Effects

**Clone Benefits:**
- Shared data stays in CPU cache
- Multiple SKBs reference same cache lines
- Better cache hit rate for packet processing

**Example:**
```c
// Bad: Copying wastes cache
for (i = 0; i < 10; i++) {
    struct sk_buff *copy = skb_copy(original, GFP_ATOMIC);
    process_packet(copy);  // Each has different data in cache
}

// Good: Cloning shares cache
for (i = 0; i < 10; i++) {
    struct sk_buff *clone = skb_clone(original, GFP_ATOMIC);
    process_packet(clone);  // All share same data in cache
}
```

### Lock Contention

Queue operations use spinlocks, which can cause contention:

**Problem:**
```c
// Multiple CPUs contending for same queue
void high_contention_example(struct sk_buff_head *queue)
{
    // This lock is heavily contended
    skb_queue_tail(queue, skb);  // Acquires queue->lock
}
```

**Solutions:**

1. **Per-CPU queues:**
```c
struct per_cpu_queues {
    struct sk_buff_head queue;
} ____cacheline_aligned_in_smp;

DEFINE_PER_CPU(struct per_cpu_queues, cpu_queues);

void enqueue_percpu(struct sk_buff *skb)
{
    struct per_cpu_queues *pcq = this_cpu_ptr(&cpu_queues);
    skb_queue_tail(&pcq->queue, skb);  // No contention!
}
```

2. **Lockless queues (advanced):**
```c
// Use atomic operations for single producer/consumer
struct lockless_queue {
    struct sk_buff *head;
    struct sk_buff *tail;
};

void lockless_enqueue(struct lockless_queue *q, struct sk_buff *skb)
{
    skb->next = NULL;
    struct sk_buff *prev = xchg(&q->tail, skb);
    if (prev)
        prev->next = skb;
    else
        q->head = skb;
}
```

### Queue Depth Management

**Problem:** Unbounded queues can cause bufferbloat

**Solution:** Implement queue limits

```c
#define MAX_QUEUE_DEPTH 1000

int bounded_enqueue(struct sk_buff_head *queue, struct sk_buff *skb)
{
    if (skb_queue_len(queue) >= MAX_QUEUE_DEPTH) {
        // Queue full - drop packet
        kfree_skb(skb);
        return -ENOSPC;
    }

    skb_queue_tail(queue, skb);
    return 0;
}
```

**Advanced:** Use Active Queue Management (AQM) algorithms like CoDel or PIE

---

## Common Patterns and Best Practices

### Pattern 1: Safe SKB Modification

```c
// Always check if SKB is shared before modifying
int safe_modify_skb(struct sk_buff *skb)
{
    // Make sure we have exclusive access
    if (skb_shared(skb)) {
        struct sk_buff *nskb = skb_copy(skb, GFP_ATOMIC);
        if (!nskb)
            return -ENOMEM;
        kfree_skb(skb);
        skb = nskb;
    }

    // Or use skb_unshare()
    skb = skb_unshare(skb, GFP_ATOMIC);
    if (!skb)
        return -ENOMEM;

    // Now safe to modify
    struct iphdr *iph = ip_hdr(skb);
    iph->ttl--;

    return 0;
}
```

### Pattern 2: Efficient Multicast

```c
// Clone for all but last recipient
void efficient_multicast(struct sk_buff *skb, struct list_head *recipients)
{
    struct recipient *r;
    struct sk_buff *clone;
    int count = 0;

    list_for_each_entry(r, recipients, list) {
        count++;
    }

    list_for_each_entry(r, recipients, list) {
        if (--count > 0) {
            // Clone for all but last
            clone = skb_clone(skb, GFP_ATOMIC);
            if (clone)
                deliver_to_recipient(r, clone);
        } else {
            // Use original for last recipient
            deliver_to_recipient(r, skb);
            return;
        }
    }
}
```

### Pattern 3: Queue Draining with Timeout

```c
// Drain queue with timeout to prevent blocking
int drain_queue_with_timeout(struct sk_buff_head *queue,
                              unsigned long timeout_ms)
{
    unsigned long start = jiffies;
    unsigned long timeout = msecs_to_jiffies(timeout_ms);
    struct sk_buff *skb;
    int count = 0;

    while ((skb = skb_dequeue(queue)) != NULL) {
        process_skb(skb);
        kfree_skb(skb);
        count++;

        // Check timeout
        if (time_after(jiffies, start + timeout)) {
            // Timeout - purge remaining
            skb_queue_purge(queue);
            return -ETIMEDOUT;
        }

        // Yield CPU periodically
        if (count % 100 == 0)
            cond_resched();
    }

    return count;
}
```

### Pattern 4: Priority Queue with Starvation Prevention

```c
struct priority_queue {
    struct sk_buff_head high_prio;
    struct sk_buff_head low_prio;
    unsigned int low_prio_counter;
    unsigned int low_prio_threshold;
};

void prio_queue_init(struct priority_queue *pq)
{
    skb_queue_head_init(&pq->high_prio);
    skb_queue_head_init(&pq->low_prio);
    pq->low_prio_counter = 0;
    pq->low_prio_threshold = 10;  // Service low prio every 10 packets
}

struct sk_buff *prio_queue_dequeue(struct priority_queue *pq)
{
    struct sk_buff *skb;

    // Prevent starvation: periodically service low priority
    if (pq->low_prio_counter >= pq->low_prio_threshold) {
        skb = skb_dequeue(&pq->low_prio);
        if (skb) {
            pq->low_prio_counter = 0;
            return skb;
        }
    }

    // Try high priority first
    skb = skb_dequeue(&pq->high_prio);
    if (skb) {
        pq->low_prio_counter++;
        return skb;
    }

    // Fall back to low priority
    skb = skb_dequeue(&pq->low_prio);
    if (skb)
        pq->low_prio_counter = 0;

    return skb;
}
```

### Pattern 5: Batch Processing

```c
// Process packets in batches for better cache utilization
void batch_process_queue(struct sk_buff_head *queue)
{
    struct sk_buff *batch[32];
    int batch_size;
    int i;

    while (!skb_queue_empty(queue)) {
        // Dequeue a batch
        batch_size = 0;
        while (batch_size < 32) {
            batch[batch_size] = skb_dequeue(queue);
            if (!batch[batch_size])
                break;
            batch_size++;
        }

        // Process batch
        for (i = 0; i < batch_size; i++) {
            process_skb(batch[i]);
        }

        // Free batch
        for (i = 0; i < batch_size; i++) {
            kfree_skb(batch[i]);
        }
    }
}
```

### Pattern 6: Reference Counting Best Practices

```c
// Proper reference counting
void reference_counting_example(struct sk_buff *skb)
{
    // Increment reference count
    skb = skb_get(skb);  // Returns skb with incremented refcount

    // Pass to another subsystem
    other_subsystem_process(skb);

    // We still have our reference
    // ... do more work ...

    // Release our reference
    kfree_skb(skb);

    // Note: skb might still be valid if other_subsystem still holds a reference
}

// Clone vs Get
void clone_vs_get_example(struct sk_buff *original)
{
    // skb_get: Same SKB, shared everything
    struct sk_buff *ref = skb_get(original);
    // ref == original (same pointer)
    // ref->users = 2

    // skb_clone: New SKB, shared data
    struct sk_buff *clone = skb_clone(original, GFP_ATOMIC);
    // clone != original (different pointers)
    // clone->users = 1, original->users = 1
    // Both point to same data (dataref = 2)
}
```

### Pattern 7: Error Handling

```c
// Proper error handling with SKBs
int process_with_error_handling(struct sk_buff *skb)
{
    struct sk_buff *clone = NULL;
    int ret = 0;

    // Clone for processing
    clone = skb_clone(skb, GFP_ATOMIC);
    if (!clone) {
        ret = -ENOMEM;
        goto err_clone;
    }

    // Process clone
    ret = do_processing(clone);
    if (ret < 0)
        goto err_process;

    // Success
    kfree_skb(skb);  // Free original
    return 0;

err_process:
    kfree_skb(clone);
err_clone:
    kfree_skb(skb);
    return ret;
}
```

### Pattern 8: Queue Iteration

```c
// Safe iteration over queue
void iterate_queue_safe(struct sk_buff_head *queue)
{
    struct sk_buff *skb, *tmp;

    // Use skb_queue_walk_safe for safe iteration
    skb_queue_walk_safe(queue, skb, tmp) {
        // Can safely remove skb from queue
        if (should_remove(skb)) {
            __skb_unlink(skb, queue);
            kfree_skb(skb);
        }
    }
}

// Iteration without removal
void iterate_queue_readonly(struct sk_buff_head *queue)
{
    struct sk_buff *skb;

    skb_queue_walk(queue, skb) {
        // Read-only operations
        inspect_skb(skb);
        // Don't modify queue structure!
    }
}
```

---

## Advanced Topics

### SKB Recycling

Some high-performance drivers implement SKB recycling to avoid allocation overhead:

```c
struct skb_recycler {
    struct sk_buff_head pool;
    unsigned int pool_size;
    unsigned int max_pool_size;
};

void skb_recycler_init(struct skb_recycler *recycler, unsigned int max_size)
{
    skb_queue_head_init(&recycler->pool);
    recycler->pool_size = 0;
    recycler->max_pool_size = max_size;
}

struct sk_buff *skb_recycler_alloc(struct skb_recycler *recycler,
                                   unsigned int size, gfp_t gfp)
{
    struct sk_buff *skb;

    // Try to get from pool
    skb = skb_dequeue(&recycler->pool);
    if (skb) {
        recycler->pool_size--;
        // Reset SKB for reuse
        skb_reset(skb);
        return skb;
    }

    // Pool empty, allocate new
    return alloc_skb(size, gfp);
}

void skb_recycler_free(struct skb_recycler *recycler, struct sk_buff *skb)
{
    // Return to pool if not full
    if (recycler->pool_size < recycler->max_pool_size) {
        skb_queue_tail(&recycler->pool, skb);
        recycler->pool_size++;
    } else {
        // Pool full, actually free
        kfree_skb(skb);
    }
}
```

### Zero-Copy Techniques

Using page fragments for zero-copy operations:

```c
// Zero-copy transmission using sendpage
int zerocopy_send(struct sock *sk, struct page *page,
                  int offset, size_t size)
{
    struct sk_buff *skb;

    // Allocate SKB with minimal linear data
    skb = alloc_skb(MAX_TCP_HEADER, GFP_KERNEL);
    if (!skb)
        return -ENOMEM;

    // Reserve space for headers
    skb_reserve(skb, MAX_TCP_HEADER);

    // Add page as fragment (zero-copy!)
    get_page(page);  // Increment page refcount
    skb_fill_page_desc(skb, 0, page, offset, size);
    skb->len += size;
    skb->data_len += size;
    skb->truesize += size;

    // Send
    return tcp_sendmsg_locked(sk, skb);
}
```

### SKB Linearization

Converting fragmented SKB to linear (all data contiguous):

```c
// Linearize SKB (expensive operation!)
int linearize_if_needed(struct sk_buff *skb)
{
    // Check if already linear
    if (!skb_is_nonlinear(skb))
        return 0;

    // Linearize (copies all fragments to linear buffer)
    if (skb_linearize(skb) != 0)
        return -ENOMEM;

    // Now skb->data contains all data contiguously
    return 0;
}
```

---

## Debugging and Troubleshooting

### Common Issues and Solutions

#### Issue 1: Memory Leaks

**Symptom:** SKBs not being freed, memory usage grows

**Debugging:**
```c
// Enable SKB leak detection
echo 1 > /proc/sys/net/core/skb_debug

// Check SKB allocation statistics
cat /proc/net/skb_alloc

// Use kmemleak
echo scan > /sys/kernel/debug/kmemleak
cat /sys/kernel/debug/kmemleak
```

**Common causes:**
- Forgetting to call `kfree_skb()` after processing
- Reference count not decremented properly
- SKBs stuck in queues that are never drained

**Solution:**
```c
// Always pair allocations with frees
struct sk_buff *skb = alloc_skb(size, GFP_KERNEL);
if (!skb)
    return -ENOMEM;

// ... use skb ...

// Always free when done
kfree_skb(skb);

// Or use cleanup attribute (modern kernels)
struct sk_buff *skb __free(kfree_skb) = alloc_skb(size, GFP_KERNEL);
```

#### Issue 2: Use-After-Free

**Symptom:** Kernel crashes, corruption, unpredictable behavior

**Debugging:**
```c
// Enable KASAN (Kernel Address Sanitizer)
CONFIG_KASAN=y

// Enable SKB debugging
CONFIG_DEBUG_NET=y
```

**Common causes:**
- Using SKB after calling `kfree_skb()`
- Accessing SKB after it's been consumed by network stack
- Race conditions in multi-threaded code

**Solution:**
```c
// Bad: Use after free
kfree_skb(skb);
printk("len=%d\n", skb->len);  // CRASH!

// Good: Don't use after free
int len = skb->len;
kfree_skb(skb);
printk("len=%d\n", len);  // OK

// Good: Set to NULL after free
kfree_skb(skb);
skb = NULL;
```

#### Issue 3: Data Corruption in Clones

**Symptom:** Modifying one SKB affects others unexpectedly

**Cause:** Modifying shared data in a clone

**Solution:**
```c
// Bad: Modifying shared data
struct sk_buff *clone = skb_clone(original, GFP_ATOMIC);
memcpy(clone->data, new_data, len);  // Corrupts original too!

// Good: Unshare before modifying
struct sk_buff *clone = skb_clone(original, GFP_ATOMIC);
clone = skb_unshare(clone, GFP_ATOMIC);
if (!clone)
    return -ENOMEM;
memcpy(clone->data, new_data, len);  // Safe now
```

#### Issue 4: Queue Deadlocks

**Symptom:** System hangs, processes stuck in D state

**Cause:** Lock ordering issues, holding locks too long

**Solution:**
```c
// Bad: Potential deadlock
spin_lock(&queue1->lock);
spin_lock(&queue2->lock);  // Might deadlock if another thread locks in reverse order

// Good: Consistent lock ordering
if (queue1 < queue2) {
    spin_lock(&queue1->lock);
    spin_lock(&queue2->lock);
} else {
    spin_lock(&queue2->lock);
    spin_lock(&queue1->lock);
}

// Better: Use trylock
if (!spin_trylock(&queue2->lock)) {
    spin_unlock(&queue1->lock);
    // Retry or handle error
}
```

### Debugging Tools and Techniques

#### 1. SKB Tracing

```c
// Enable SKB tracepoints
echo 1 > /sys/kernel/debug/tracing/events/skb/enable

// View trace
cat /sys/kernel/debug/tracing/trace

// Custom tracepoint
trace_printk("SKB %p: len=%d, users=%d, dataref=%d\n",
             skb, skb->len, refcount_read(&skb->users),
             atomic_read(&skb_shinfo(skb)->dataref));
```

#### 2. Queue Statistics

```c
// Add statistics to your queue
struct instrumented_queue {
    struct sk_buff_head queue;
    atomic64_t enqueued;
    atomic64_t dequeued;
    atomic64_t dropped;
    unsigned int max_qlen;
};

void stats_enqueue(struct instrumented_queue *q, struct sk_buff *skb)
{
    if (skb_queue_len(&q->queue) >= q->max_qlen) {
        atomic64_inc(&q->dropped);
        kfree_skb(skb);
        return;
    }

    skb_queue_tail(&q->queue, skb);
    atomic64_inc(&q->enqueued);

    // Track max queue length
    unsigned int qlen = skb_queue_len(&q->queue);
    if (qlen > q->max_qlen)
        q->max_qlen = qlen;
}

// Export via debugfs
void show_queue_stats(struct seq_file *m, struct instrumented_queue *q)
{
    seq_printf(m, "Enqueued: %lld\n", atomic64_read(&q->enqueued));
    seq_printf(m, "Dequeued: %lld\n", atomic64_read(&q->dequeued));
    seq_printf(m, "Dropped: %lld\n", atomic64_read(&q->dropped));
    seq_printf(m, "Current: %u\n", skb_queue_len(&q->queue));
    seq_printf(m, "Max: %u\n", q->max_qlen);
}
```

#### 3. Memory Accounting

```c
// Track memory usage
struct skb_memory_tracker {
    atomic64_t total_allocated;
    atomic64_t total_freed;
    atomic64_t current_usage;
};

struct sk_buff *tracked_alloc_skb(struct skb_memory_tracker *tracker,
                                  unsigned int size, gfp_t gfp)
{
    struct sk_buff *skb = alloc_skb(size, gfp);
    if (skb) {
        atomic64_inc(&tracker->total_allocated);
        atomic64_add(skb->truesize, &tracker->current_usage);
    }
    return skb;
}

void tracked_free_skb(struct skb_memory_tracker *tracker,
                      struct sk_buff *skb)
{
    atomic64_inc(&tracker->total_freed);
    atomic64_sub(skb->truesize, &tracker->current_usage);
    kfree_skb(skb);
}
```

---

## Real-World Examples

### Example 1: Packet Capture Implementation

```c
// Simplified tcpdump-like packet capture
struct packet_capture {
    struct sk_buff_head capture_queue;
    wait_queue_head_t wait_queue;
    unsigned int max_packets;
    bool enabled;
};

void capture_init(struct packet_capture *cap, unsigned int max_packets)
{
    skb_queue_head_init(&cap->capture_queue);
    init_waitqueue_head(&cap->wait_queue);
    cap->max_packets = max_packets;
    cap->enabled = false;
}

// Called from network stack for each packet
void capture_packet(struct packet_capture *cap, struct sk_buff *skb)
{
    struct sk_buff *clone;

    if (!cap->enabled)
        return;

    // Clone packet for capture
    clone = skb_clone(skb, GFP_ATOMIC);
    if (!clone)
        return;

    // Add timestamp
    __net_timestamp(clone);

    // Check queue limit
    if (skb_queue_len(&cap->capture_queue) >= cap->max_packets) {
        // Drop oldest packet
        struct sk_buff *old = skb_dequeue(&cap->capture_queue);
        kfree_skb(old);
    }

    // Add to capture queue
    skb_queue_tail(&cap->capture_queue, clone);

    // Wake up readers
    wake_up_interruptible(&cap->wait_queue);
}

// User-space read interface
ssize_t capture_read(struct packet_capture *cap, char __user *buf, size_t len)
{
    struct sk_buff *skb;
    int ret;

    // Wait for packet
    ret = wait_event_interruptible(cap->wait_queue,
                                   !skb_queue_empty(&cap->capture_queue));
    if (ret)
        return ret;

    // Get packet from queue
    skb = skb_dequeue(&cap->capture_queue);
    if (!skb)
        return -EAGAIN;

    // Copy to userspace
    if (skb->len > len) {
        kfree_skb(skb);
        return -EMSGSIZE;
    }

    if (copy_to_user(buf, skb->data, skb->len)) {
        kfree_skb(skb);
        return -EFAULT;
    }

    ret = skb->len;
    kfree_skb(skb);
    return ret;
}
```

### Example 2: Load Balancer with Multiple Queues

```c
#define NUM_WORKER_QUEUES 4

struct load_balancer {
    struct sk_buff_head worker_queues[NUM_WORKER_QUEUES];
    atomic_t next_queue;
    struct task_struct *workers[NUM_WORKER_QUEUES];
};

void lb_init(struct load_balancer *lb)
{
    int i;

    atomic_set(&lb->next_queue, 0);

    for (i = 0; i < NUM_WORKER_QUEUES; i++) {
        skb_queue_head_init(&lb->worker_queues[i]);
        lb->workers[i] = kthread_run(worker_thread,
                                     &lb->worker_queues[i],
                                     "worker-%d", i);
    }
}

// Distribute packets using round-robin
void lb_enqueue(struct load_balancer *lb, struct sk_buff *skb)
{
    int queue_idx = atomic_inc_return(&lb->next_queue) % NUM_WORKER_QUEUES;
    skb_queue_tail(&lb->worker_queues[queue_idx], skb);
}

// Worker thread
int worker_thread(void *data)
{
    struct sk_buff_head *queue = data;
    struct sk_buff *skb;

    while (!kthread_should_stop()) {
        skb = skb_dequeue(queue);
        if (!skb) {
            schedule_timeout_interruptible(HZ / 100);
            continue;
        }

        // Process packet
        process_packet(skb);
        kfree_skb(skb);
    }

    return 0;
}
```

### Example 3: Rate-Limited Queue

```c
struct rate_limited_queue {
    struct sk_buff_head queue;
    unsigned long last_send;
    unsigned int rate_limit;  // packets per second
    unsigned int tokens;
    spinlock_t lock;
};

void rlq_init(struct rate_limited_queue *rlq, unsigned int rate)
{
    skb_queue_head_init(&rlq->queue);
    spin_lock_init(&rlq->lock);
    rlq->rate_limit = rate;
    rlq->tokens = rate;
    rlq->last_send = jiffies;
}

int rlq_enqueue(struct rate_limited_queue *rlq, struct sk_buff *skb)
{
    unsigned long flags;

    spin_lock_irqsave(&rlq->lock, flags);
    skb_queue_tail(&rlq->queue, skb);
    spin_unlock_irqrestore(&rlq->lock, flags);

    return 0;
}

struct sk_buff *rlq_dequeue(struct rate_limited_queue *rlq)
{
    unsigned long flags;
    unsigned long now = jiffies;
    unsigned long elapsed;
    struct sk_buff *skb = NULL;

    spin_lock_irqsave(&rlq->lock, flags);

    // Refill tokens based on elapsed time
    elapsed = now - rlq->last_send;
    if (elapsed > 0) {
        unsigned int new_tokens = (elapsed * rlq->rate_limit) / HZ;
        rlq->tokens = min(rlq->tokens + new_tokens, rlq->rate_limit);
        rlq->last_send = now;
    }

    // Dequeue if we have tokens
    if (rlq->tokens > 0 && !skb_queue_empty(&rlq->queue)) {
        skb = skb_dequeue(&rlq->queue);
        rlq->tokens--;
    }

    spin_unlock_irqrestore(&rlq->lock, flags);
    return skb;
}
```

---

## Summary and Key Takeaways

### SKB Cloning Summary

| Aspect | Key Points |
|--------|------------|
| **Purpose** | Efficient packet duplication without copying data |
| **Mechanism** | New `sk_buff` structure, shared data buffer |
| **Cost** | ~200 bytes allocation vs ~1700 bytes for full copy |
| **Use Cases** | Packet capture, multicast, TCP retransmission, bridging |
| **Optimization** | Fclone pre-allocation for fast cloning |
| **Limitation** | Cannot modify shared data without unsharing |

### Queue Management Summary

| Aspect | Key Points |
|--------|------------|
| **Structure** | `sk_buff_head` - doubly-linked circular list with lock |
| **Operations** | Enqueue, dequeue, peek, insert, purge |
| **Thread Safety** | Built-in spinlock for concurrent access |
| **Use Cases** | Socket buffers, device queues, QoS, traffic control |
| **Performance** | Per-CPU queues to reduce contention |
| **Best Practice** | Implement queue limits to prevent bufferbloat |

### Critical Rules

1. **Always free SKBs** - Every `alloc_skb()` must have a matching `kfree_skb()`
2. **Check before modifying** - Use `skb_unshare()` before modifying cloned SKBs
3. **Prefer cloning over copying** - Much more efficient when data doesn't need modification
4. **Use appropriate GFP flags** - `GFP_ATOMIC` in interrupt context, `GFP_KERNEL` otherwise
5. **Implement queue limits** - Prevent unbounded memory growth
6. **Handle errors properly** - Always check return values and clean up on failure
7. **Use per-CPU queues** - Reduce lock contention in high-performance scenarios
8. **Monitor queue depths** - Track statistics to identify bottlenecks

### Performance Tips

1. **Clone instead of copy** when possible (88% memory savings)
2. **Use fclone** for predictable clone patterns
3. **Batch process** packets for better cache utilization
4. **Implement recycling** for high-frequency allocation/free patterns
5. **Use zero-copy** techniques with page fragments
6. **Avoid linearization** unless absolutely necessary
7. **Per-CPU queues** to eliminate lock contention
8. **Lockless queues** for single producer/consumer scenarios

### Common Pitfalls to Avoid

1. ❌ Modifying shared data in clones
2. ❌ Forgetting to free SKBs
3. ❌ Using SKBs after freeing
4. ❌ Unbounded queue growth
5. ❌ Lock ordering violations
6. ❌ Using wrong GFP flags in interrupt context
7. ❌ Not checking allocation failures
8. ❌ Copying when cloning would suffice

---

## Reference Quick Guide

### Essential Functions

```c
// Allocation
struct sk_buff *alloc_skb(unsigned int size, gfp_t priority);
struct sk_buff *netdev_alloc_skb(struct net_device *dev, unsigned int length);

// Cloning and Copying
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t priority);
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t priority);
struct sk_buff *skb_unshare(struct sk_buff *skb, gfp_t pri);

// Reference Counting
struct sk_buff *skb_get(struct sk_buff *skb);
void kfree_skb(struct sk_buff *skb);
int skb_shared(const struct sk_buff *skb);

// Queue Operations
void skb_queue_head_init(struct sk_buff_head *list);
void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk);
struct sk_buff *skb_dequeue(struct sk_buff_head *list);
struct sk_buff *skb_peek(const struct sk_buff_head *list);
void skb_queue_purge(struct sk_buff_head *list);
__u32 skb_queue_len(const struct sk_buff_head *list);
int skb_queue_empty(const struct sk_buff_head *list);

// Data Manipulation
unsigned char *skb_put(struct sk_buff *skb, unsigned int len);
unsigned char *skb_push(struct sk_buff *skb, unsigned int len);
unsigned char *skb_pull(struct sk_buff *skb, unsigned int len);
void skb_reserve(struct sk_buff *skb, int len);
void skb_trim(struct sk_buff *skb, unsigned int len);
```

### Important Macros

```c
// Queue iteration
skb_queue_walk(queue, skb)
skb_queue_walk_safe(queue, skb, tmp)

// Data access
skb_headroom(skb)
skb_tailroom(skb)
skb_is_nonlinear(skb)

// Reference counting
refcount_read(&skb->users)
atomic_read(&skb_shinfo(skb)->dataref)
```

### Debugging

```c
// Enable debugging
CONFIG_DEBUG_NET=y
CONFIG_NET_SKB_DEBUG=y

// Runtime checks
echo 1 > /proc/sys/net/core/skb_debug

// Tracing
echo 1 > /sys/kernel/debug/tracing/events/skb/enable
cat /sys/kernel/debug/tracing/trace
```

---

## Further Reading

### Kernel Documentation
- `Documentation/networking/skbuff.txt` - Official SKB documentation
- `Documentation/networking/scaling.txt` - Network scaling techniques
- `include/linux/skbuff.h` - SKB structure definition and inline functions
- `net/core/skbuff.c` - SKB implementation

### Related Topics
- **Network Device Drivers** - How drivers allocate and manage SKBs
- **TCP/IP Stack** - How protocols use SKBs for packet processing
- **Traffic Control (tc)** - Advanced queueing disciplines
- **XDP (eXpress Data Path)** - High-performance packet processing
- **NAPI** - New API for network device drivers
- **Generic Segmentation Offload (GSO)** - Large packet handling
- **Scatter-Gather I/O** - Zero-copy techniques

### Performance Analysis Tools
- `perf` - CPU profiling and tracing
- `bpftrace` - Dynamic tracing with eBPF
- `tcpdump` - Packet capture and analysis
- `netstat`/`ss` - Socket and queue statistics
- `ethtool` - Network device statistics

---

## Conclusion

SKB cloning and queue management are fundamental to Linux network performance. Understanding these mechanisms enables:

- **Efficient packet processing** through cloning instead of copying
- **Proper memory management** with reference counting
- **Thread-safe operations** using queue primitives
- **Scalable architectures** with per-CPU queues
- **Quality of Service** through priority queues
- **Debugging capabilities** with proper instrumentation

The key to mastering SKB management is understanding the trade-offs between different approaches and choosing the right tool for each situation. Clone when you can, copy when you must, and always manage resources carefully.

This comprehensive guide provides the foundation for working with SKBs in the Linux kernel, from basic operations to advanced optimization techniques. Use it as a reference when implementing network functionality, debugging issues, or optimizing performance.

---

**Document Version:** 1.0
**Last Updated:** 2026-03-20
**Author:** Comprehensive SKB Documentation Project

