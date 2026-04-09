# Chapter 2: sk_buff Lifecycle and Allocation

The lifecycle of an `sk_buff` -- from allocation through manipulation to eventual
release -- is one of the most performance-critical paths in the Linux networking
stack. Every packet that traverses the kernel requires at least one `sk_buff`
allocation and one free operation, making these routines among the most heavily
optimized in the entire kernel. This chapter provides an exhaustive treatment of
every allocation variant, reference counting mechanism, memory accounting system,
and deallocation path.

---

## 1. Allocation Functions

The kernel provides a family of allocation functions tailored to different
contexts: process context, interrupt context, NAPI polling, and driver
initialization. All ultimately converge on `__alloc_skb()`, the low-level
workhorse.

### 1.1 `alloc_skb(size, gfp_mask)` -- The Primary Allocator

`alloc_skb()` is the most commonly used allocation function in protocol-layer
code. It is a thin wrapper around `__alloc_skb()`:

```c
/* include/linux/skbuff.h */
static inline struct sk_buff *alloc_skb(unsigned int size, gfp_t priority)
{
    return __alloc_skb(size, priority, 0, NUMA_NO_NODE);
    /*                                 ^-- flags=0: no fclone, no recycling */
}
```

When `alloc_skb(size, GFP_KERNEL)` is called, the following sequence occurs:

**Step 1: Allocate the sk_buff structure from `skbuff_head_cache`**

The kernel maintains a dedicated SLAB/SLUB cache named `skbuff_head_cache`
exclusively for `struct sk_buff` objects. This cache is created at boot time
in `skb_init()`:

```c
/* net/core/skbuff.c — boot-time initialization */
void __init skb_init(void)
{
    skbuff_head_cache = kmem_cache_create("skbuff_head_cache",
                                          sizeof(struct sk_buff),
                                          0,                        /* align */
                                          SLAB_HWCACHE_ALIGN |      /* cache-line aligned */
                                          SLAB_PANIC,               /* panic on failure */
                                          NULL);                    /* no ctor */
    /* ... fclone cache creation follows ... */
}
```

The allocation from this cache proceeds through the SLUB fast path: check the
per-CPU freelist, then the per-CPU partial list, then fall back to the page
allocator. Because `sk_buff` structs are allocated and freed millions of times
per second on a busy system, the per-CPU freelist almost always satisfies the
request without any locking.

```c
/* Inside __alloc_skb(): */
skb = kmem_cache_alloc_node(cache,       /* skbuff_head_cache */
                            gfp_mask & ~GFP_DMA,
                            node);
if (unlikely(!skb))
    return NULL;
```

**Step 2: Allocate the data buffer via `kmalloc`**

The data buffer must hold both the packet data and a `struct skb_shared_info`
at the end. The kernel rounds up the requested size and adds the shared info:

```c
/* Inside __alloc_skb(): */
size = SKB_DATA_ALIGN(size);                 /* round up to alignment boundary */
size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
data = kmalloc_reserve(size, gfp_mask, node, &pfmemalloc);
if (unlikely(!data)) {
    kmem_cache_free(cache, skb);             /* release the sk_buff struct */
    return NULL;
}
size = SKB_WITH_OVERHEAD(ksize(data));       /* actual usable size after kmalloc */
```

The `SKB_DATA_ALIGN()` macro ensures proper alignment (typically to
`sizeof(long)`, i.e., 8 bytes on 64-bit). The `ksize()` call retrieves the
actual allocation size from the SLAB allocator, which may be larger than
requested due to SLAB size classes.

**Step 3: Initialize head, data, tail, end pointers**

```c
skb->head = data;                /* start of allocated data buffer          */
skb->data = data;                /* start of packet data (will advance)     */
skb_reset_tail_pointer(skb);     /* tail = data (no data written yet)       */
skb->end  = skb->tail + size;   /* end of usable data area                 */
```

At this point, the entire data region between `head` and `end` is available.
The `data` and `tail` pointers both point to `head`, meaning zero bytes of
packet data exist:

```
    head ──► ┌─────────────────────────────────────┐
    data ──► │                                     │
    tail ──► │    (empty — available headroom and   │
             │     tailroom for protocol headers)   │
             │                                     │
     end ──► ├─────────────────────────────────────┤
             │         skb_shared_info              │
             └─────────────────────────────────────┘
```

**Step 4: Initialize `skb_shared_info` at the end of the data buffer**

The `skb_shared_info` structure occupies the space between `end` and the true
end of the allocated buffer. It is initialized via `skb_set_end_offset()` and
then explicitly zeroed/set:

```c
shinfo = skb_shinfo(skb);          /* (struct skb_shared_info *)(skb->end) */
memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
atomic_set(&shinfo->dataref, 1);   /* one reference to this data buffer   */
shinfo->nr_frags  = 0;
shinfo->gso_size  = 0;
shinfo->gso_segs  = 0;
shinfo->gso_type  = 0;
shinfo->frag_list = NULL;
```

**Step 5: Set reference counts**

```c
refcount_set(&skb->users, 1);      /* one reference to this sk_buff struct */
/* dataref already set to 1 in step 4 */
```

The dual reference counting scheme is fundamental: `skb->users` tracks
references to the `sk_buff` structure itself, while `shinfo->dataref` tracks
references to the data buffer. This distinction enables efficient cloning.

**Complete allocation result:**

```
    sk_buff (from skbuff_head_cache)       Data Buffer (from kmalloc)
    ┌───────────────────────┐              ┌──────────────────────────┐
    │ next       = NULL     │   head ─────►│                          │
    │ prev       = NULL     │   data ─────►│  (head == data == tail   │
    │ sk         = NULL     │   tail ─────►│   initially)             │
    │ dev        = NULL     │              │                          │
    │ len        = 0        │              │  (available for packet   │
    │ data_len   = 0        │              │   data and headers)      │
    │ mac_len    = 0        │              │                          │
    │ queue_mapping = 0     │   end  ─────►├──────────────────────────┤
    │ users      = 1        │              │ skb_shared_info          │
    │ truesize   = size +   │              │   nr_frags  = 0          │
    │   sizeof(sk_buff)     │              │   frag_list = NULL       │
    │ ...                   │              │   dataref   = 1          │
    └───────────────────────┘              └──────────────────────────┘
```

### 1.2 `__alloc_skb()` -- The Low-Level Implementation

All `sk_buff` allocation paths ultimately call `__alloc_skb()`. Its full
signature exposes every available option:

```c
/* net/core/skbuff.c */
struct sk_buff *__alloc_skb(unsigned int size,    /* data buffer size       */
                            gfp_t gfp_mask,       /* allocation flags       */
                            int flags,            /* SKB_ALLOC_FCLONE, etc. */
                            int node)             /* NUMA node, or -1       */
```

The `flags` parameter accepts the following values:

| Flag                 | Value | Effect                                          |
|----------------------|-------|-------------------------------------------------|
| `SKB_ALLOC_FCLONE`  | 0x01  | Allocate from `skbuff_fclone_cache` (see S3)    |
| `SKB_ALLOC_RX`      | 0x02  | Allocation is for receive path                  |
| `SKB_ALLOC_NAPI`    | 0x04  | Use NAPI per-CPU cache for sk_buff allocation   |

The implementation, annotated:

```c
struct sk_buff *__alloc_skb(unsigned int size, gfp_t gfp_mask,
                            int flags, int node)
{
    struct kmem_cache *cache;
    struct sk_buff *skb;
    u8 *data;
    bool pfmemalloc;

    /*
     * 1. Select the cache: fclone cache if requested,
     *    otherwise the standard head cache.
     */
    cache = (flags & SKB_ALLOC_FCLONE)
            ? skbuff_fclone_cache
            : skbuff_head_cache;

    /*
     * 2. Allocate the sk_buff struct from the selected cache.
     *    If NAPI context, use the NAPI bulk-alloc cache.
     */
    if (flags & SKB_ALLOC_NAPI)
        skb = kmem_cache_alloc_bulk(cache, gfp_mask, 1, ...);
    else
        skb = kmem_cache_alloc_node(cache, gfp_mask & ~GFP_DMA, node);

    if (unlikely(!skb))
        return NULL;

    prefetchw(skb);         /* prefetch for write — we will initialize it */

    /*
     * 3. Calculate aligned data buffer size including skb_shared_info.
     */
    size = SKB_DATA_ALIGN(size);
    size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));

    /*
     * 4. Allocate the data buffer. kmalloc_reserve uses __GFP_NOMEMALLOC
     *    unless we are in a softirq/NAPI context allowed to tap reserves.
     */
    data = kmalloc_reserve(size, gfp_mask, node, &pfmemalloc);
    if (unlikely(!data)) {
        kmem_cache_free(cache, skb);
        return NULL;
    }

    /*
     * 5. Adjust size to actual allocated size from SLAB.
     */
    size = SKB_WITH_OVERHEAD(ksize(data));
    prefetchw(data + size);  /* prefetch skb_shared_info location */

    /*
     * 6. Zero-initialize selected sk_buff fields (not the entire struct
     *    for performance — only the critical fields).
     */
    memset(skb, 0, offsetof(struct sk_buff, tail));

    /*
     * 7. Setup data pointers.
     */
    skb->truesize = SKB_TRUESIZE(size);
    skb->pfmemalloc = pfmemalloc;
    refcount_set(&skb->users, 1);
    skb->head = data;
    skb->data = data;
    skb_reset_tail_pointer(skb);
    skb_set_end_offset(skb, size);

    /*
     * 8. Initialize skb_shared_info at the end of the data buffer.
     */
    skb_set_kcov_handle(skb, kcov_common_handle());
    shinfo = skb_shinfo(skb);
    memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
    atomic_set(&shinfo->dataref, 1);

    /*
     * 9. For fclone: initialize the companion sk_buff and fclone refcount.
     */
    if (flags & SKB_ALLOC_FCLONE) {
        struct sk_buff_fclones *fclones;
        fclones = container_of(skb, struct sk_buff_fclones, skb1);
        skb->fclone = SKB_FCLONE_ORIG;
        refcount_set(&fclones->fclone_ref, 1);
        fclones->skb2.fclone = SKB_FCLONE_CLONE;
    }

    return skb;
}
EXPORT_SYMBOL(__alloc_skb);
```

### 1.3 `dev_alloc_skb(length)` -- For Network Drivers (Legacy)

`dev_alloc_skb()` is the traditional allocation function used in network device
drivers. It adds `NET_SKB_PAD` bytes of headroom before the packet data so that
protocol headers can be pushed without reallocating:

```c
/* include/linux/skbuff.h */
static inline struct sk_buff *dev_alloc_skb(unsigned int length)
{
    return netdev_alloc_skb(NULL, length);
}
```

`NET_SKB_PAD` is defined as:

```c
/*
 * NET_SKB_PAD is typically 64 bytes on most architectures.
 * On architectures with DMA cache-line alignment requirements
 * (e.g., ARM), it may be larger (e.g., 128).
 */
#ifdef CONFIG_64BIT
#define NET_SKB_PAD     max(64, L1_CACHE_BYTES)
#else
#define NET_SKB_PAD     max(32, L1_CACHE_BYTES)
#endif
```

The effect of `dev_alloc_skb(length)`:

```
    head ──► ┌──────────────────────────────────────┐
             │     NET_SKB_PAD bytes headroom       │
    data ──► ├──────────────────────────────────────┤
    tail ──► │                                      │
             │     length bytes available           │
             │                                      │
     end ──► ├──────────────────────────────────────┤
             │         skb_shared_info              │
             └──────────────────────────────────────┘
```

This headroom is essential because Ethernet drivers receive raw frames that
need L2/L3/L4 header parsing. The headroom allows the networking stack to
`skb_push()` additional headers without triggering `pskb_expand_head()`.

### 1.4 `netdev_alloc_skb()` and `netdev_alloc_skb_ip_align()` -- Modern Driver Variants

`netdev_alloc_skb()` supersedes `dev_alloc_skb()` and associates the allocated
sk_buff with a specific network device:

```c
/* net/core/skbuff.c */
struct sk_buff *__netdev_alloc_skb(struct net_device *dev,
                                   unsigned int len, gfp_t gfp_mask)
{
    struct page_frag_cache *nc;
    struct sk_buff *skb;
    bool pfmemalloc;
    void *data;

    len += NET_SKB_PAD;        /* add headroom */

    /*
     * For small allocations (< PAGE_SIZE), use the per-CPU
     * page fragment cache for the data buffer. This avoids
     * calling kmalloc and improves cache locality.
     */
    if (len <= SKB_WITH_OVERHEAD(1024) ||
        len > SKB_WITH_OVERHEAD(PAGE_SIZE) ||
        (gfp_mask & (__GFP_DIRECT_RECLAIM | GFP_DMA))) {
        /* Fall back to standard __alloc_skb path */
        skb = __alloc_skb(len, gfp_mask, SKB_ALLOC_RX, NUMA_NO_NODE);
        if (!skb)
            goto skb_fail;
        goto skb_success;
    }

    /* Use per-CPU page fragment allocator for the data buffer */
    len = SKB_DATA_ALIGN(len);
    len += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));

    nc = this_cpu_ptr(&netdev_alloc_cache);
    data = page_frag_alloc(nc, len, gfp_mask);
    if (unlikely(!data))
        return NULL;

    pfmemalloc = nc->pfmemalloc;

    /* Build an sk_buff around the pre-allocated data buffer */
    skb = __build_skb(data, len);
    if (unlikely(!skb)) {
        skb_free_frag(data);
        return NULL;
    }

skb_success:
    skb_reserve(skb, NET_SKB_PAD);   /* reserve headroom */
    skb->dev = dev;                   /* associate with device */
    return skb;

skb_fail:
    return NULL;
}
EXPORT_SYMBOL(__netdev_alloc_skb);
```

**`netdev_alloc_skb_ip_align()`** adds an additional 2-byte offset so that the
IP header (which follows the 14-byte Ethernet header) lands on a 4-byte aligned
boundary. This is critical on architectures that fault on unaligned access:

```c
/* include/linux/skbuff.h */
static inline struct sk_buff *netdev_alloc_skb_ip_align(struct net_device *dev,
                                                        unsigned int length)
{
    struct sk_buff *skb = netdev_alloc_skb(dev, length + NET_IP_ALIGN);
    if (NET_IP_ALIGN && skb)
        skb_reserve(skb, NET_IP_ALIGN);   /* typically 2 bytes */
    return skb;
}
```

The resulting layout:

```
    head ──► ┌──────────────────────────────────────┐
             │     NET_SKB_PAD bytes (e.g., 64)     │
             ├──────────────────────────────────────┤
             │     NET_IP_ALIGN (2 bytes)           │
    data ──► ├──────────────────────────────────────┤
    tail ──► │                                      │
             │     length bytes available           │
             │     (IP header at 4-byte boundary    │
             │      after 14-byte Ethernet header)  │
             │                                      │
     end ──► ├──────────────────────────────────────┤
             │         skb_shared_info              │
             └──────────────────────────────────────┘
```

Alignment arithmetic: Ethernet header = 14 bytes. With a 2-byte pre-offset,
the IP header starts at offset 14 + 2 = 16, which is 4-byte aligned.

### 1.5 `napi_alloc_skb()` -- NAPI-Context Allocation

`napi_alloc_skb()` is optimized for the NAPI (New API) polling context. Since
NAPI poll runs in softirq context on a specific CPU, this function exploits
per-CPU caches more aggressively:

```c
/* net/core/skbuff.c */
struct sk_buff *napi_alloc_skb(struct napi_struct *napi, unsigned int len)
{
    struct napi_alloc_cache *nc;
    struct sk_buff *skb;
    void *data;
    bool pfmemalloc;

    len += NET_SKB_PAD + NET_IP_ALIGN;

    nc = this_cpu_ptr(&napi_alloc_cache);

    if (len <= SKB_WITH_OVERHEAD(SKB_SMALL_HEAD_CACHE_SIZE)) {
        /* Use small head cache for data buffer */
        data = kmem_cache_alloc_node(skb_small_head_cache,
                                     GFP_ATOMIC | __GFP_NOWARN,
                                     NUMA_NO_NODE);
        if (unlikely(!data))
            return NULL;
        /* ... build skb from data ... */
    } else {
        /* Use per-CPU page fragment cache */
        len = SKB_DATA_ALIGN(len);
        len += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));

        data = page_frag_alloc(&nc->page, len, GFP_ATOMIC);
        if (unlikely(!data))
            return NULL;
    }

    pfmemalloc = nc->page.pfmemalloc;
    skb = __napi_build_skb(data, len);
    if (unlikely(!skb)) {
        skb_free_frag(data);
        return NULL;
    }

    skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN);
    skb->dev = napi->dev;

    return skb;
}
EXPORT_SYMBOL(napi_alloc_skb);
```

**Key optimization: NAPI sk_buff bulk cache.** The `napi_alloc_cache` maintains
a per-CPU cache of pre-freed `sk_buff` structures that can be recycled without
going through the SLAB allocator:

```c
/* net/core/skbuff.c */
struct napi_alloc_cache {
    struct page_frag_cache page;        /* per-CPU page frag allocator   */
    unsigned int skb_count;             /* number of cached sk_buff ptrs */
    void *skb_cache[NAPI_SKB_CACHE_SIZE]; /* cache of freed sk_buffs    */
};

#define NAPI_SKB_CACHE_SIZE    64       /* typical cache size */
```

This structure enables the following fast path:

```
    ┌─────────────────────────────────────────────────────────┐
    │               NAPI Allocation Fast Path                 │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │   napi_alloc_skb()                                      │
    │        │                                                │
    │        ▼                                                │
    │   ┌────────────────────────┐                            │
    │   │ NAPI sk_buff cache     │  skb_count > 0?            │
    │   │ (per-CPU, no locking)  │──── YES ──► return cached  │
    │   └────────────────────────┘              sk_buff        │
    │        │ NO                                              │
    │        ▼                                                │
    │   ┌────────────────────────┐                            │
    │   │ kmem_cache_alloc()     │  SLUB fast path            │
    │   │ skbuff_head_cache      │                            │
    │   └────────────────────────┘                            │
    │        │                                                │
    │        ▼                                                │
    │   ┌────────────────────────┐                            │
    │   │ page_frag_alloc()      │  per-CPU page fragment     │
    │   │ (data buffer)          │  cache                     │
    │   └────────────────────────┘                            │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

### 1.6 `build_skb()` -- Wrapping an Existing Buffer

`build_skb()` creates an `sk_buff` around a pre-allocated data buffer. This is
used when the driver or subsystem has already allocated memory (e.g., from a
page pool) and simply needs to wrap it in the `sk_buff` metadata structure:

```c
/* net/core/skbuff.c */
struct sk_buff *build_skb(void *data, unsigned int frag_size)
{
    struct sk_buff *skb = kmem_cache_alloc(skbuff_head_cache,
                                           GFP_ATOMIC);
    if (unlikely(!skb))
        return NULL;

    skb->head = data;
    skb->data = data;
    skb_reset_tail_pointer(skb);

    if (frag_size) {
        /* Data came from page fragment allocator */
        skb->head_frag = 1;
        skb_set_end_offset(skb,
            frag_size - SKB_DATA_ALIGN(sizeof(struct skb_shared_info)));
    } else {
        /* Data came from kmalloc — query actual size */
        skb_set_end_offset(skb,
            SKB_WITH_OVERHEAD(ksize(data)));
    }

    /* Initialize shared info */
    struct skb_shared_info *shinfo = skb_shinfo(skb);
    memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
    atomic_set(&shinfo->dataref, 1);

    refcount_set(&skb->users, 1);
    skb->truesize = SKB_TRUESIZE(skb_end_offset(skb));

    return skb;
}
EXPORT_SYMBOL(build_skb);
```

**`__build_skb()`** is the no-fail variant that assumes the caller handles
allocation failure of the data buffer, and never allocates a new sk_buff from
the SLAB cache; instead, it can use a pre-allocated or NAPI-cached sk_buff.

Typical use in a modern driver:

```c
/* Example: driver receive path using page pool + build_skb */
static struct sk_buff *my_driver_build_rx_skb(struct my_ring *ring,
                                              struct page *page,
                                              unsigned int offset,
                                              unsigned int len)
{
    void *data = page_address(page) + offset;
    struct sk_buff *skb;

    skb = build_skb(data, ring->rx_buf_size);
    if (unlikely(!skb))
        return NULL;

    skb_reserve(skb, ring->rx_headroom);  /* reserve headroom    */
    __skb_put(skb, len);                  /* set data length     */
    return skb;
}
```

### 1.7 Comparison of Allocation Functions

```
    ┌─────────────────────────┬──────────┬──────────┬────────────┬────────────┐
    │ Function                │ Context  │ Headroom │ Device     │ Cache      │
    │                         │          │          │ Assoc.     │ Friendly   │
    ├─────────────────────────┼──────────┼──────────┼────────────┼────────────┤
    │ alloc_skb()             │ Any      │ None     │ No         │ Standard   │
    │ dev_alloc_skb()         │ IRQ/BH   │ PAD      │ No         │ Standard   │
    │ netdev_alloc_skb()      │ IRQ/BH   │ PAD      │ Yes        │ Page frag  │
    │ netdev_alloc_skb_       │ IRQ/BH   │ PAD+2    │ Yes        │ Page frag  │
    │   ip_align()            │          │          │            │            │
    │ napi_alloc_skb()        │ NAPI     │ PAD+2    │ Yes        │ NAPI cache │
    │ build_skb()             │ Any      │ None     │ No         │ Ext. buf   │
    └─────────────────────────┴──────────┴──────────┴────────────┴────────────┘
```

---

## 2. SLAB/SLUB Allocator Integration

The `sk_buff` allocation system is tightly integrated with the kernel's slab
allocator (SLAB, SLUB, or SLOB, depending on kernel configuration; modern
kernels overwhelmingly use SLUB). Two dedicated caches are created at boot.

### 2.1 `skbuff_head_cache` -- The Standard sk_buff Cache

```c
/* net/core/skbuff.c */
static struct kmem_cache *skbuff_head_cache __ro_after_init;

void __init skb_init(void)
{
    skbuff_head_cache = kmem_cache_create(
        "skbuff_head_cache",
        sizeof(struct sk_buff),       /* object size (~232 bytes on x86-64) */
        0,                            /* no special alignment beyond default */
        SLAB_HWCACHE_ALIGN | SLAB_PANIC,
        NULL                          /* no constructor */
    );
    /* ... */
}
```

On x86-64, `sizeof(struct sk_buff)` is typically 232-240 bytes, which the SLUB
allocator rounds up to a 256-byte slab object (fitting into the 256-byte size
class). With `SLAB_HWCACHE_ALIGN`, objects are aligned to the L1 cache line
size (typically 64 bytes).

Objects per slab page (4KB page):

```
    4096 / 256 = 16 sk_buff objects per slab page
```

### 2.2 `skbuff_fclone_cache` -- For Fast Cloning

```c
/* net/core/skbuff.c */
static struct kmem_cache *skbuff_fclone_cache __ro_after_init;

void __init skb_init(void)
{
    /* ... skbuff_head_cache creation ... */

    skbuff_fclone_cache = kmem_cache_create(
        "skbuff_fclone_cache",
        sizeof(struct sk_buff_fclones),  /* contains TWO sk_buffs + refcount */
        0,
        SLAB_HWCACHE_ALIGN | SLAB_PANIC,
        NULL
    );
}
```

The `sk_buff_fclones` structure:

```c
struct sk_buff_fclones {
    struct sk_buff  skb1;           /* the "original" sk_buff              */
    struct sk_buff  skb2;           /* the "clone" sk_buff (pre-allocated) */
    refcount_t      fclone_ref;     /* shared reference count for the pair */
};
```

Size: `2 * sizeof(struct sk_buff) + sizeof(refcount_t)` ~ 472 bytes on x86-64,
rounded up to a 512-byte SLUB object.

### 2.3 SLUB Fast Path for sk_buff Allocation

The SLUB allocator provides three levels of caching for `sk_buff` allocations,
all designed to minimize lock contention and cache-line bouncing:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                  SLUB Allocator Layers                      │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  Level 1: Per-CPU Freelist (lockless, fastest)              │
    │  ┌────────────────────────────────────────────────┐         │
    │  │  cpu_slab->freelist ──► obj ──► obj ──► obj    │         │
    │  │  (single pointer CAS — no spinlock)            │         │
    │  └────────────────────────────────────────────────┘         │
    │       │ empty                                               │
    │       ▼                                                     │
    │  Level 2: Per-CPU Partial List (local_lock)                 │
    │  ┌────────────────────────────────────────────────┐         │
    │  │  cpu_slab->partial ──► slab ──► slab ──► slab  │         │
    │  │  (move a partially-free slab to cpu_slab)      │         │
    │  └────────────────────────────────────────────────┘         │
    │       │ empty                                               │
    │       ▼                                                     │
    │  Level 3: Per-Node Partial List (spinlock)                  │
    │  ┌────────────────────────────────────────────────┐         │
    │  │  kmem_cache_node->partial ──► slab ──► slab    │         │
    │  │  (requires node-level spinlock)                │         │
    │  └────────────────────────────────────────────────┘         │
    │       │ empty                                               │
    │       ▼                                                     │
    │  Level 4: Page Allocator                                    │
    │  ┌────────────────────────────────────────────────┐         │
    │  │  alloc_pages(gfp, order)                       │         │
    │  │  (slow path — allocate fresh slab pages)       │         │
    │  └────────────────────────────────────────────────┘         │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

**Performance characteristics:**

| Level | Latency      | Lock Required | Cache Lines Touched |
|-------|-------------|---------------|---------------------|
| 1     | ~20 ns      | None (CAS)    | 1                   |
| 2     | ~50 ns      | local_lock    | 2-3                 |
| 3     | ~100-200 ns | spinlock      | 4+                  |
| 4     | ~500+ ns    | multiple      | many                |

On a busy system processing millions of packets per second, the vast majority
of allocations (>99%) are satisfied from Level 1, making `sk_buff` allocation
nearly as fast as a simple pointer increment.

### 2.4 Per-CPU Caches and Magazine Layers

Beyond the SLUB allocator's own per-CPU caches, the networking stack adds
additional caching layers:

```c
/* Per-CPU page fragment cache for data buffers */
static DEFINE_PER_CPU(struct page_frag_cache, netdev_alloc_cache);

/* Per-CPU NAPI allocation cache */
static DEFINE_PER_CPU(struct napi_alloc_cache, napi_alloc_cache);
```

The page fragment cache (`page_frag_cache`) allocates a full page and then
carves it into smaller fragments for data buffers. This amortizes the cost
of `alloc_pages()` across multiple packet allocations:

```
    ┌─────────────────────────────────────────────────────┐
    │         Page Fragment Cache (per-CPU)                │
    ├─────────────────────────────────────────────────────┤
    │                                                     │
    │  Single 4KB (or 32KB compound) page:                │
    │  ┌────────┬────────┬────────┬────────┬─────────┐    │
    │  │ frag 1 │ frag 2 │ frag 3 │ frag 4 │ (free)  │    │
    │  │ (used) │ (used) │ (used) │ (used) │         │    │
    │  └────────┴────────┴────────┴────────┴─────────┘    │
    │                                      ▲              │
    │                                      │              │
    │                               nc->offset            │
    │                               (next allocation      │
    │                                starts here)         │
    │                                                     │
    └─────────────────────────────────────────────────────┘
```

### 2.5 `__alloc_skb()` with `SKB_ALLOC_FCLONE` Flag

When the `SKB_ALLOC_FCLONE` flag is passed, `__alloc_skb()` allocates from the
`skbuff_fclone_cache` instead of `skbuff_head_cache`. This yields a pair of
`sk_buff` structures that share a single SLAB object:

```c
/* Inside __alloc_skb(), when SKB_ALLOC_FCLONE is set: */
struct sk_buff_fclones *fclones;

skb = kmem_cache_alloc_node(skbuff_fclone_cache, gfp_mask, node);
fclones = container_of(skb, struct sk_buff_fclones, skb1);

/* Mark the original and the clone */
skb->fclone = SKB_FCLONE_ORIG;           /* "I am the original"  */
fclones->skb2.fclone = SKB_FCLONE_CLONE; /* "I am the clone"     */
refcount_set(&fclones->fclone_ref, 1);   /* one user of the pair */
```

This optimization is primarily used by TCP, which frequently needs to clone
sk_buffs in the retransmit queue.

---

## 3. Fast Cloning (fclone)

### 3.1 The fclone Pair

Traditional cloning (`skb_clone()`) requires allocating a new `sk_buff`
structure from the SLAB allocator for every clone. For TCP, which clones every
outgoing packet for retransmission, this cost is prohibitive. The fclone
mechanism pre-allocates a pair of `sk_buff` structures together, so the clone
is essentially free.

The fclone lifecycle:

```
    Phase 1: Allocation (SKB_ALLOC_FCLONE)
    ┌──────────────────────────────────────────────┐
    │  sk_buff_fclones (from skbuff_fclone_cache)  │
    ├──────────────────────────────────────────────┤
    │  ┌──────────────┐  ┌──────────────┐          │
    │  │    skb1       │  │    skb2       │          │
    │  │ fclone=ORIG   │  │ fclone=CLONE  │          │
    │  │ users=1       │  │ users=0       │          │
    │  │ (IN USE)      │  │ (DORMANT)     │          │
    │  └──────────────┘  └──────────────┘          │
    │  fclone_ref = 1                               │
    └──────────────────────────────────────────────┘
                                                    
    Phase 2: Clone (skb_clone() detects fclone)     
    ┌──────────────────────────────────────────────┐
    │  ┌──────────────┐  ┌──────────────┐          │
    │  │    skb1       │  │    skb2       │          │
    │  │ fclone=ORIG   │  │ fclone=CLONE  │          │
    │  │ users=1       │  │ users=1       │          │
    │  │ (IN USE)      │  │ (IN USE)      │          │
    │  └──────────────┘  └──────────────┘          │
    │  fclone_ref = 2                               │
    │  (both sk_buffs share the same data buffer)   │
    └──────────────────────────────────────────────┘
                                                    
    Phase 3: Free original (kfree_skb(skb1))        
    ┌──────────────────────────────────────────────┐
    │  ┌──────────────┐  ┌──────────────┐          │
    │  │    skb1       │  │    skb2       │          │
    │  │ (FREED)       │  │ fclone=CLONE  │          │
    │  │               │  │ users=1       │          │
    │  │               │  │ (IN USE)      │          │
    │  └──────────────┘  └──────────────┘          │
    │  fclone_ref = 1                               │
    │  (slab object NOT freed — skb2 still in use)  │
    └──────────────────────────────────────────────┘
                                                    
    Phase 4: Free clone (kfree_skb(skb2))           
    ┌──────────────────────────────────────────────┐
    │  ┌──────────────┐  ┌──────────────┐          │
    │  │    skb1       │  │    skb2       │          │
    │  │ (FREED)       │  │ (FREED)       │          │
    │  │               │  │               │          │
    │  └──────────────┘  └──────────────┘          │
    │  fclone_ref = 0                               │
    │  kmem_cache_free(skbuff_fclone_cache, fclones)│
    └──────────────────────────────────────────────┘
```

### 3.2 Clone Detection in `skb_clone()`

When `skb_clone()` is called, it checks whether the original was allocated
with fclone support:

```c
/* net/core/skbuff.c */
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask)
{
    struct sk_buff_fclones *fclones =
        container_of(skb, struct sk_buff_fclones, skb1);
    struct sk_buff *n;

    if (skb_orphan_frags(skb, gfp_mask))
        return NULL;

    /*
     * Check if this sk_buff was allocated from fclone cache
     * and the clone slot is still available.
     */
    if (skb->fclone == SKB_FCLONE_ORIG &&
        refcount_read(&fclones->fclone_ref) == 1) {
        /* Fast path: use the pre-allocated clone */
        n = &fclones->skb2;
        refcount_set(&n->users, 1);
        refcount_set(&fclones->fclone_ref, 2);  /* both halves in use */
    } else {
        /* Slow path: allocate a new sk_buff from skbuff_head_cache */
        if (skb->fclone == SKB_FCLONE_ORIG &&
            refcount_read(&fclones->fclone_ref) != 1) {
            /* fclone already consumed — fall through to kmem_cache_alloc */
        }
        n = kmem_cache_alloc(skbuff_head_cache, gfp_mask);
        if (!n)
            return NULL;
        n->fclone = SKB_FCLONE_UNAVAILABLE;
    }

    return __skb_clone(n, skb);     /* copy metadata, share data buffer */
}
```

### 3.3 `skb_fclone_busy()` -- Checking Clone Availability

```c
/* include/linux/skbuff.h */
static inline bool skb_fclone_busy(const struct sock *sk,
                                   const struct sk_buff *skb)
{
    const struct sk_buff_fclones *fclones;

    fclones = container_of(skb, struct sk_buff_fclones, skb1);

    return skb->fclone == SKB_FCLONE_ORIG &&
           refcount_read(&fclones->fclone_ref) > 1 &&
           READ_ONCE(fclones->skb2.sk) == sk;
}
```

TCP uses this function in `tcp_write_queue_purge()` and `tcp_trim_head()` to
determine whether an sk_buff's fclone is currently in use (e.g., by a
retransmission in progress).

### 3.4 fclone Memory Layout

```
    skbuff_fclone_cache SLUB object (~512 bytes)
    ┌────────────────────────────────────────────────┐ offset 0
    │                                                │
    │  skb1 (struct sk_buff, ~232 bytes)             │
    │  ┌──────────────────────────────────────────┐  │
    │  │ fclone = SKB_FCLONE_ORIG                 │  │
    │  │ head ──► (shared data buffer)            │  │
    │  │ users = 1                                │  │
    │  │ ...                                      │  │
    │  └──────────────────────────────────────────┘  │
    │                                                │ offset ~232
    │  skb2 (struct sk_buff, ~232 bytes)             │
    │  ┌──────────────────────────────────────────┐  │
    │  │ fclone = SKB_FCLONE_CLONE                │  │
    │  │ head ──► (same shared data buffer)       │  │
    │  │ users = 0 (dormant until cloned)         │  │
    │  │ ...                                      │  │
    │  └──────────────────────────────────────────┘  │
    │                                                │ offset ~464
    │  fclone_ref (refcount_t, 4 bytes)              │
    │  ┌──────────────────────────────────────────┐  │
    │  │ refcount = 1  (becomes 2 after clone)    │  │
    │  └──────────────────────────────────────────┘  │
    │                                                │
    └────────────────────────────────────────────────┘
```

---

## 4. Reference Counting

The `sk_buff` system uses a dual reference counting scheme that enables
efficient data sharing between clones while maintaining independent control
of `sk_buff` structure lifetimes.

### 4.1 `skb->users` (atomic_t) -- Structure Refcount

The `users` field is an atomic reference count on the `sk_buff` structure
itself. When it reaches zero, the `sk_buff` structure is freed (returned to
the SLAB cache).

```c
/* include/linux/skbuff.h */
struct sk_buff {
    /* ... */
    refcount_t  users;      /* structure reference count */
    /* ... */
};
```

Rules governing `skb->users`:

1. Set to 1 at allocation time.
2. Incremented by `skb_get()` when another subsystem needs a reference.
3. Decremented by `kfree_skb()` or `consume_skb()`.
4. When it reaches 0, `__kfree_skb()` is called to actually free the sk_buff.

### 4.2 `skb_shared_info->dataref` -- Data Buffer Refcount

The `dataref` field, stored in `struct skb_shared_info` at the end of the data
buffer, tracks how many `sk_buff` structures reference this particular data
buffer. When multiple sk_buffs share the same data (via cloning), `dataref`
is greater than 1.

```c
/* include/linux/skbuff.h */
struct skb_shared_info {
    /* ... */
    atomic_t    dataref;     /* data buffer reference count  */
    /* ... */
    unsigned int nr_frags;
    struct skb_frag_struct frags[MAX_SKB_FRAGS];
    /* ... */
};
```

The upper 16 bits of `dataref` encode a separate "no-clone" counter that
prevents certain zero-copy optimizations. The lower 16 bits are the actual
reference count:

```c
/* Actual data references = dataref & SKB_DATAREF_MASK */
#define SKB_DATAREF_SHIFT  16
#define SKB_DATAREF_MASK   ((1 << SKB_DATAREF_SHIFT) - 1)  /* 0xFFFF */
```

### 4.3 `skb_get(skb)` -- Increment Users

```c
/* include/linux/skbuff.h */
static inline struct sk_buff *skb_get(struct sk_buff *skb)
{
    refcount_inc(&skb->users);
    return skb;
}
```

Common use cases for `skb_get()`:

- A protocol handler wants to retain a reference after returning from the
  receive path (e.g., for reassembly queues).
- A timer or workqueue needs to defer processing of an sk_buff.
- The socket layer holds a reference while the sk_buff is queued in a
  socket's receive buffer.

**Warning:** `skb_get()` does NOT clone the data. The caller must not modify
the data buffer unless it first calls `pskb_copy()` or `skb_copy()`.

### 4.4 `skb_shared(skb)` -- Check if Data is Shared

```c
/* include/linux/skbuff.h */
static inline int skb_shared(const struct sk_buff *skb)
{
    return refcount_read(&skb->users) != 1;
}
```

Note that `skb_shared()` checks whether the `sk_buff structure` is shared
(multiple users), not whether the data buffer is shared. To check data sharing:

```c
/* Check if the data buffer is shared (cloned) */
static inline int skb_cloned(const struct sk_buff *skb)
{
    return skb->cloned &&
           (atomic_read(&skb_shinfo(skb)->dataref) & SKB_DATAREF_MASK) != 1;
}
```

### 4.5 Reference Count State Diagrams

**State 1: Fresh allocation -- single owner**

```
    ┌───────────────┐         ┌───────────────────────────┐
    │   sk_buff A    │         │     Data Buffer           │
    │   users = 1    │ ───────►│                           │
    │   cloned = 0   │         │     skb_shared_info       │
    │                │         │       dataref = 1         │
    └───────────────┘         └───────────────────────────┘
```

**State 2: After `skb_clone()` -- two sk_buffs sharing data**

```
    ┌───────────────┐
    │   sk_buff A    │ ──┐
    │   users = 1    │   │     ┌───────────────────────────┐
    │   cloned = 1   │   ├────►│     Data Buffer           │
    └───────────────┘   │     │                           │
                         │     │     skb_shared_info       │
    ┌───────────────┐   │     │       dataref = 2         │
    │   sk_buff B    │ ──┘     └───────────────────────────┘
    │   users = 1    │              (shared, read-only)
    │   cloned = 1   │
    └───────────────┘
```

**State 3: After `skb_get()` -- multiple references to same sk_buff**

```
    Subsystem X ──┐
                   ├──► ┌───────────────┐       ┌────────────────────┐
    Subsystem Y ──┘    │   sk_buff A    │──────►│    Data Buffer     │
                        │   users = 2    │       │  dataref = 1       │
                        │   cloned = 0   │       └────────────────────┘
                        └───────────────┘
```

**State 4: Complex scenario -- clone + get**

```
    tcp_retransmit ──┐
                      ├──► ┌───────────────┐
    tcp_write_queue ─┘    │   sk_buff A    │ ──┐
                           │   users = 2    │   │  ┌────────────────────┐
                           │   cloned = 1   │   ├─►│    Data Buffer     │
                           └───────────────┘   │  │  dataref = 2       │
                                                │  └────────────────────┘
                           ┌───────────────┐   │
                           │   sk_buff B    │ ──┘
    qdisc_enqueue ────────►│   users = 1    │
                           │   cloned = 1   │
                           └───────────────┘
```

### 4.6 Copy-on-Write Semantics

When a subsystem needs to modify the data buffer of a cloned sk_buff, it must
first ensure exclusive access. The kernel provides several functions:

```c
/*
 * skb_unclone() — make the data buffer exclusively owned.
 * If dataref > 1, copies the entire linear data region into a new buffer.
 */
static inline int skb_unclone(struct sk_buff *skb, gfp_t pri)
{
    might_sleep_if(gfpflags_allow_blocking(pri));
    if (skb_cloned(skb))
        return pskb_expand_head(skb, 0, 0, pri);
    return 0;
}

/*
 * skb_copy() — deep copy: new sk_buff + new data buffer.
 * skb_clone() — shallow copy: new sk_buff, shared data buffer.
 * pskb_copy() — partial copy: new sk_buff + new linear data,
 *               shared fragments (paged data).
 */
```

Copy hierarchy:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                    Copy Functions                           │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  skb_clone()     ──► New sk_buff, SHARED data               │
    │                      dataref incremented                    │
    │                      O(1), no data copy                     │
    │                                                             │
    │  pskb_copy()     ──► New sk_buff, NEW linear data           │
    │                      Fragments still shared                 │
    │                      O(n) where n = linear data size        │
    │                                                             │
    │  skb_copy()      ──► New sk_buff, NEW data (all regions)    │
    │                      Completely independent copy            │
    │                      O(n) where n = total packet size       │
    │                                                             │
    │  __pskb_copy()   ──► Like pskb_copy() with headroom ctrl   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## 5. Freeing sk_buffs

The `sk_buff` free path is carefully layered to handle different contexts
(process, softirq, hardirq), provide tracing hooks, and ensure all associated
resources are properly released.

### 5.1 `kfree_skb(skb)` -- Standard Free (Dropped Packets)

`kfree_skb()` decrements the reference count and, if it reaches zero, frees
the sk_buff. It generates a `kfree_skb` tracepoint that includes the drop
reason, making it the appropriate function for packets that are being
**dropped** (not successfully consumed):

```c
/* net/core/skbuff.c */
void kfree_skb_reason(struct sk_buff *skb, enum skb_drop_reason reason)
{
    if (!skb_unref(skb))         /* decrement users; return false if not 0 */
        return;

    trace_kfree_skb(skb, __builtin_return_address(0), reason);
    __kfree_skb(skb);
}
EXPORT_SYMBOL(kfree_skb_reason);

/* Convenience macro */
#define kfree_skb(skb)  kfree_skb_reason(skb, SKB_DROP_REASON_NOT_SPECIFIED)
```

The `skb_unref()` function is a critical optimization:

```c
static inline bool skb_unref(struct sk_buff *skb)
{
    if (unlikely(!skb))
        return false;
    if (likely(refcount_read(&skb->users) == 1))
        /* Fast path: we are the only user, no atomic needed */
        smp_rmb();
    else if (likely(!refcount_dec_and_test(&skb->users)))
        /* Slow path: other users exist, decrement atomically */
        return false;
    return true;
}
```

### 5.2 `consume_skb(skb)` -- Standard Free (Consumed Packets)

`consume_skb()` is functionally identical to `kfree_skb()` but generates a
different tracepoint (`consume_skb` instead of `kfree_skb`). This distinction
is important for debugging and monitoring:

```c
void consume_skb(struct sk_buff *skb)
{
    if (!skb_unref(skb))
        return;

    trace_consume_skb(skb);      /* different tracepoint than kfree_skb */
    __kfree_skb(skb);
}
EXPORT_SYMBOL(consume_skb);
```

**Usage convention:**

- `kfree_skb()` -- the packet was **dropped** (error, filter, congestion).
  Tools like `dropwatch` and `perf trace` monitor this tracepoint.
- `consume_skb()` -- the packet was **successfully consumed** (delivered to
  a socket, forwarded, etc.). This is the normal, non-error path.

```
    ┌─────────────────────────────────────────────────────┐
    │             Free Function Selection Guide           │
    ├─────────────────────────────────────────────────────┤
    │                                                     │
    │   Packet dropped (error/filter)?                    │
    │       ──► kfree_skb(skb)                            │
    │           ──► trace_kfree_skb (monitored by         │
    │               dropwatch, perf)                      │
    │                                                     │
    │   Packet consumed successfully?                     │
    │       ──► consume_skb(skb)                          │
    │           ──► trace_consume_skb (informational)     │
    │                                                     │
    │   In device driver TX completion?                   │
    │       ──► dev_kfree_skb(skb)     (process ctx)      │
    │       ──► dev_kfree_skb_irq(skb) (hardirq ctx)     │
    │       ──► dev_kfree_skb_any(skb) (unknown ctx)     │
    │                                                     │
    │   NAPI context, bulk free?                          │
    │       ──► napi_consume_skb(skb, budget)             │
    │                                                     │
    │   Freeing a list/chain?                             │
    │       ──► kfree_skb_list(skb)                       │
    │                                                     │
    └─────────────────────────────────────────────────────┘
```

### 5.3 `dev_kfree_skb(skb)` -- Device Driver Context

`dev_kfree_skb()` is for device drivers freeing transmitted sk_buffs in
process context (e.g., in the ndo_start_xmit path when recycling old buffers):

```c
/* include/linux/skbuff.h */
#define dev_kfree_skb(a)    consume_skb(a)
```

It is simply an alias for `consume_skb()`, as a successfully transmitted
packet is considered "consumed."

### 5.4 `dev_kfree_skb_irq(skb)` and `dev_kfree_skb_any(skb)` -- IRQ-Safe Variants

When a driver's TX completion interrupt fires, the driver may need to free
sk_buffs. Since `kfree_skb()` can call `skb->destructor`, which may attempt
to wake a process (e.g., `sock_wfree` calling `sk_write_space`), it is not
safe to call from hard IRQ context.

`dev_kfree_skb_irq()` defers the actual free to softirq context:

```c
/* net/core/dev.c */
void dev_kfree_skb_irq_reason(struct sk_buff *skb,
                               enum skb_drop_reason reason)
{
    unsigned long flags;

    local_irq_save(flags);
    /* Queue the sk_buff on a per-CPU completion queue */
    skb->next = __this_cpu_read(softnet_data.completion_queue);
    __this_cpu_write(softnet_data.completion_queue, skb);
    raise_softirq_irqoff(NET_TX_SOFTIRQ);  /* schedule softirq */
    local_irq_restore(flags);
}
```

The `NET_TX_SOFTIRQ` handler then drains the completion queue:

```c
/* net/core/dev.c — net_tx_action() softirq handler */
static void net_tx_action(struct softirq_action *h)
{
    struct softnet_data *sd = this_cpu_ptr(&softnet_data);

    if (sd->completion_queue) {
        struct sk_buff *clist;

        local_irq_disable();
        clist = sd->completion_queue;
        sd->completion_queue = NULL;
        local_irq_enable();

        while (clist) {
            struct sk_buff *skb = clist;
            clist = clist->next;
            WARN_ON(refcount_read(&skb->users));
            trace_consume_skb(skb);
            __kfree_skb(skb);        /* safe in softirq context */
        }
    }
    /* ... TX queue processing ... */
}
```

`dev_kfree_skb_any()` detects the context and chooses the appropriate path:

```c
/* include/linux/skbuff.h */
static inline void dev_kfree_skb_any(struct sk_buff *skb)
{
    if (in_hardirq() || irqs_disabled())
        dev_kfree_skb_irq(skb);
    else
        dev_kfree_skb(skb);          /* == consume_skb() */
}
```

### 5.5 `__kfree_skb(skb)` -- Unconditional Free (Internal)

`__kfree_skb()` is the internal function that performs the actual deallocation.
It does NOT check the reference count -- the caller must ensure `users == 0`.

```c
/* net/core/skbuff.c */
void __kfree_skb(struct sk_buff *skb)
{
    skb_release_all(skb);        /* release all associated resources */
    kfree_skbmem(skb);           /* free the sk_buff struct itself   */
}
```

### 5.6 The Full Free Path

The complete deallocation sequence involves releasing all resources associated
with the sk_buff before returning memory to the allocators:

```
    kfree_skb(skb) / consume_skb(skb)
        │
        ▼
    skb_unref(skb)           ──► decrement users, check if zero
        │  (users == 0)
        ▼
    __kfree_skb(skb)
        │
        ├──► skb_release_all(skb)
        │        │
        │        ├──► skb_release_head_state(skb)
        │        │        │
        │        │        ├──► skb->destructor(skb)    [if set]
        │        │        │        (e.g., sock_wfree, sock_rfree)
        │        │        │
        │        │        ├──► nf_conntrack_put()      [if netfilter]
        │        │        │
        │        │        ├──► skb_ext_put()            [if extensions]
        │        │        │
        │        │        └──► secpath_put()            [if IPsec]
        │        │
        │        └──► skb_release_data(skb)
        │                 │
        │                 ├──► decrement dataref
        │                 │    (if dataref > 0, stop — data is shared)
        │                 │
        │                 ├──► skb_zcopy_clear(skb)    [zero-copy cleanup]
        │                 │
        │                 ├──► for each frag in nr_frags:
        │                 │        skb_frag_unref(skb, i)
        │                 │        (put_page on fragment pages)
        │                 │
        │                 ├──► if frag_list:
        │                 │        kfree_skb_list(frag_list)
        │                 │        (recursively free chained sk_buffs)
        │                 │
        │                 └──► skb_free_head(skb)
        │                          │
        │                          ├──► if head_frag:
        │                          │        skb_free_frag(skb->head)
        │                          │        (page fragment free)
        │                          │
        │                          └──► else:
        │                                   kfree(skb->head)
        │                                   (kmalloc free)
        │
        └──► kfree_skbmem(skb)
                 │
                 ├──► if fclone == SKB_FCLONE_UNAVAILABLE:
                 │        kmem_cache_free(skbuff_head_cache, skb)
                 │
                 ├──► if fclone == SKB_FCLONE_ORIG:
                 │        if refcount_dec_and_test(fclone_ref):
                 │            kmem_cache_free(skbuff_fclone_cache, fclones)
                 │        else:
                 │            (clone still alive — defer to clone's free)
                 │
                 └──► if fclone == SKB_FCLONE_CLONE:
                          if refcount_dec_and_test(fclone_ref):
                              kmem_cache_free(skbuff_fclone_cache, fclones)
                          else:
                              (original still alive — defer to original's free)
```

### 5.7 `skb->destructor` Callback -- Socket Layer Notification

The `destructor` function pointer allows the socket layer to be notified when
an sk_buff is freed. This is the primary mechanism for socket memory accounting:

```c
struct sk_buff {
    /* ... */
    void (*destructor)(struct sk_buff *skb);
    /* ... */
};
```

Common destructors:

```c
/*
 * sock_wfree() — called when a TX sk_buff is freed.
 * Decrements sk->sk_wmem_alloc and may wake writers.
 */
void sock_wfree(struct sk_buff *skb)
{
    struct sock *sk = skb->sk;
    unsigned int len = skb->truesize;

    if (!sock_flag(sk, SOCK_USE_WRITE_QUEUE)) {
        if (sock_flag(sk, SOCK_RCU_FREE) &&
            sk->sk_write_space)
            /* Schedule callback under RCU */
            call_rcu(&skb->sp_destructed, ...);
        else {
            atomic_sub(len, &sk->sk_wmem_alloc);
            sk->sk_write_space(sk);     /* wake up blocked writers */
            sock_put(sk);               /* release socket reference */
        }
    } else {
        atomic_sub(len, &sk->sk_wmem_alloc);
    }
}

/*
 * sock_rfree() — called when an RX sk_buff is freed.
 * Decrements sk->sk_rmem_alloc.
 */
void sock_rfree(struct sk_buff *skb)
{
    struct sock *sk = skb->sk;
    unsigned int len = skb->truesize;

    atomic_sub(len, &sk->sk_rmem_alloc);
    sk_mem_uncharge(sk, len);            /* release socket memory charge */
}
```

The destructor lifecycle:

```
    ┌────────────────────────────────────────────────────────────┐
    │              Destructor Lifecycle                          │
    ├────────────────────────────────────────────────────────────┤
    │                                                            │
    │  1. Socket sends data:                                     │
    │     ┌──────────────────────────────────────────────────┐   │
    │     │ skb = alloc_skb(...)                              │   │
    │     │ skb_set_owner_w(skb, sk)                          │   │
    │     │   ──► skb->sk = sk                                │   │
    │     │   ──► skb->destructor = sock_wfree                │   │
    │     │   ──► atomic_add(truesize, &sk->sk_wmem_alloc)   │   │
    │     │   ──► sock_hold(sk)  /* keep socket alive */      │   │
    │     └──────────────────────────────────────────────────┘   │
    │                                                            │
    │  2. Packet travels through the stack, is transmitted...    │
    │                                                            │
    │  3. Driver TX completion frees the sk_buff:                │
    │     ┌──────────────────────────────────────────────────┐   │
    │     │ consume_skb(skb)                                  │   │
    │     │   ──► skb->destructor(skb)  /* sock_wfree */      │   │
    │     │   ──► atomic_sub(truesize, &sk->sk_wmem_alloc)   │   │
    │     │   ──► sk->sk_write_space(sk)                      │   │
    │     │       ──► wake_up(sk->sk_wq)  /* wake writers */  │   │
    │     │   ──► sock_put(sk)  /* release socket ref */      │   │
    │     └──────────────────────────────────────────────────┘   │
    │                                                            │
    └────────────────────────────────────────────────────────────┘
```

---

## 6. Memory Accounting

Memory accounting ensures that no single socket can monopolize kernel memory
for network buffers. The accounting system tracks per-socket memory usage and
enforces configurable limits.

### 6.1 Socket Memory Limits

Each socket maintains atomic counters for send and receive buffer usage:

```c
struct sock {
    /* ... */
    atomic_t        sk_wmem_alloc;     /* TX bytes committed (including overhead) */
    atomic_t        sk_rmem_alloc;     /* RX bytes queued in receive buffer       */
    int             sk_sndbuf;         /* send buffer size limit                  */
    int             sk_rcvbuf;         /* receive buffer size limit               */
    int             sk_wmem_queued;    /* bytes queued by transport layer (TCP)   */
    int             sk_forward_alloc;  /* pre-charged memory (optimization)       */
    /* ... */
};
```

The relationship between these fields:

```
    ┌───────────────────────────────────────────────────────────────┐
    │                 Socket Memory Accounting                     │
    ├───────────────────────────────────────────────────────────────┤
    │                                                               │
    │  Send Side:                                                   │
    │  ┌─────────────────────────────────────────────────────┐      │
    │  │                                                     │      │
    │  │  sk_wmem_alloc  ≤  sk_sndbuf                        │      │
    │  │  (sum of truesize  (setsockopt SO_SNDBUF or         │      │
    │  │   for all TX skbs)  /proc/sys/net/core/wmem_default)│      │
    │  │                                                     │      │
    │  │  When sk_wmem_alloc ≥ sk_sndbuf:                    │      │
    │  │    ──► send() blocks (or returns EAGAIN)            │      │
    │  │                                                     │      │
    │  │  When sk_buff freed (sock_wfree):                   │      │
    │  │    ──► sk_wmem_alloc decremented                    │      │
    │  │    ──► sk_write_space() wakes blocked writers       │      │
    │  │                                                     │      │
    │  └─────────────────────────────────────────────────────┘      │
    │                                                               │
    │  Receive Side:                                                │
    │  ┌─────────────────────────────────────────────────────┐      │
    │  │                                                     │      │
    │  │  sk_rmem_alloc  ≤  sk_rcvbuf                        │      │
    │  │  (sum of truesize  (setsockopt SO_RCVBUF or         │      │
    │  │   for all RX skbs)  /proc/sys/net/core/rmem_default)│      │
    │  │                                                     │      │
    │  │  When sk_rmem_alloc ≥ sk_rcvbuf:                    │      │
    │  │    ──► incoming packets dropped                     │      │
    │  │                                                     │      │
    │  │  When application reads (recvmsg/read):             │      │
    │  │    ──► sk_buff freed, sock_rfree called             │      │
    │  │    ──► sk_rmem_alloc decremented                    │      │
    │  │                                                     │      │
    │  └─────────────────────────────────────────────────────┘      │
    │                                                               │
    └───────────────────────────────────────────────────────────────┘
```

### 6.2 `skb_set_owner_w()` / `skb_set_owner_r()` -- Associating with a Socket

These functions charge an sk_buff's memory to a socket:

```c
/* include/net/sock.h */
static inline void skb_set_owner_w(struct sk_buff *skb, struct sock *sk)
{
    skb_orphan(skb);                          /* detach from any previous owner */
    skb->sk = sk;                             /* associate with this socket     */
#ifdef CONFIG_INET
    if (unlikely(!sk_fullsock(sk))) {
        skb->destructor = sock_edemux;
        sock_hold(sk);
        return;
    }
#endif
    skb->destructor = sock_wfree;             /* set TX destructor              */
    skb_set_hash_from_sk(skb, sk);
    /*
     * Charge the sk_buff's truesize to the socket's write memory.
     * We add 1 to sk_wmem_alloc to prevent it from reaching 0
     * while sk_buffs are still in flight (the final decrement
     * in sock_wfree would race with socket teardown).
     */
    refcount_add(skb->truesize, &sk->sk_wmem_alloc);
}

static inline void skb_set_owner_r(struct sk_buff *skb, struct sock *sk)
{
    skb_orphan(skb);                          /* detach from previous owner     */
    skb->sk = sk;                             /* associate with this socket     */
    skb->destructor = sock_rfree;             /* set RX destructor              */
    atomic_add(skb->truesize, &sk->sk_rmem_alloc);
    sk_mem_charge(sk, skb->truesize);         /* charge against memory pressure */
}
```

### 6.3 `skb_orphan()` -- Detaching from a Socket

```c
static inline void skb_orphan(struct sk_buff *skb)
{
    if (skb->destructor) {
        skb->destructor(skb);   /* call current destructor (accounting) */
        skb->destructor = NULL;
        skb->sk = NULL;
    } else {
        BUG_ON(skb->sk);
    }
}
```

`skb_orphan()` is called when an sk_buff is transferred between subsystems
that have different ownership semantics. For example, when the TCP layer hands
a packet to the IP layer, or when a packet is forwarded.

### 6.4 TCP Memory Accounting for Flow Control

TCP uses memory accounting as a flow control mechanism. The `sk_wmem_queued`
counter tracks bytes in the write queue, and TCP adjusts its behavior based
on memory pressure:

```c
/* TCP send path (simplified) */
int tcp_sendmsg_locked(struct sock *sk, struct msghdr *msg, size_t size)
{
    /* ... */
    while (msg_data_left(msg)) {
        /* Check if we can allocate more send buffer */
        if (sk_stream_memory_free(sk)) {
            /* Allocate sk_buff and copy data */
            skb = sk_stream_alloc_skb(sk, select_size(sk, sg, firstfrag),
                                       sk->sk_allocation, firstfrag);
            if (!skb)
                goto wait_for_memory;

            skb_entail(sk, skb);    /* add to write queue */
            /* ... copy data ... */
        } else {
wait_for_memory:
            /* Block until memory is available */
            err = sk_stream_wait_memory(sk, &timeo);
            if (err)
                goto out_err;
        }
    }
}

/* Check if send buffer space is available */
static inline bool sk_stream_memory_free(const struct sock *sk)
{
    return sk->sk_wmem_queued < READ_ONCE(sk->sk_sndbuf);
}
```

Memory pressure states for TCP:

```
    ┌─────────────────────────────────────────────────────────┐
    │              TCP Memory Pressure States                 │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │  Normal (under pressure = 0):                           │
    │  ┌───────────────────────────────────────────────┐      │
    │  │  tcp_memory_allocated < sysctl_tcp_mem[0]     │      │
    │  │  ──► Full allocation allowed                  │      │
    │  │  ──► Autotuning active                        │      │
    │  └───────────────────────────────────────────────┘      │
    │                                                         │
    │  Warning (under pressure = 1):                          │
    │  ┌───────────────────────────────────────────────┐      │
    │  │  sysctl_tcp_mem[1] ≤ allocated < tcp_mem[2]   │      │
    │  │  ──► Reduce buffer sizes                      │      │
    │  │  ──► Disable autotuning                       │      │
    │  │  ──► More aggressive pruning of OOO queue     │      │
    │  └───────────────────────────────────────────────┘      │
    │                                                         │
    │  Critical (under pressure = 2):                         │
    │  ┌───────────────────────────────────────────────┐      │
    │  │  tcp_memory_allocated ≥ sysctl_tcp_mem[2]     │      │
    │  │  ──► Fail new allocations                     │      │
    │  │  ──► Drop incoming data                       │      │
    │  │  ──► Prune receive queues aggressively        │      │
    │  └───────────────────────────────────────────────┘      │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

### 6.5 Sysctl Tunables

The following sysctl parameters control default buffer sizes and limits:

```
    ┌──────────────────────────────────────────────────────────────────┐
    │              /proc/sys/net/core/ Parameters                     │
    ├──────────────────────────────┬───────────────────────────────────┤
    │ Parameter                    │ Description                      │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ wmem_default                 │ Default SO_SNDBUF for new        │
    │ (default: 212992 = 208 KB)   │ sockets (bytes)                  │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ rmem_default                 │ Default SO_RCVBUF for new        │
    │ (default: 212992 = 208 KB)   │ sockets (bytes)                  │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ wmem_max                     │ Maximum SO_SNDBUF settable by    │
    │ (default: 212992)            │ setsockopt (bytes)               │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ rmem_max                     │ Maximum SO_RCVBUF settable by    │
    │ (default: 212992)            │ setsockopt (bytes)               │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ optmem_max                   │ Maximum ancillary buffer size    │
    │ (default: 20480)             │ for socket options (bytes)       │
    └──────────────────────────────┴───────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │              /proc/sys/net/ipv4/ Parameters (TCP)               │
    ├──────────────────────────────┬───────────────────────────────────┤
    │ tcp_wmem (3 values)          │ min / default / max TCP send     │
    │ (default: 4096 16384 4194304)│ buffer (per-socket, bytes)       │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ tcp_rmem (3 values)          │ min / default / max TCP recv     │
    │ (default: 4096 131072        │ buffer (per-socket, bytes)       │
    │           6291456)           │                                  │
    ├──────────────────────────────┼───────────────────────────────────┤
    │ tcp_mem (3 values, in pages) │ low / pressure / high threshold  │
    │ (auto-calculated at boot)    │ for global TCP memory pressure   │
    └──────────────────────────────┴───────────────────────────────────┘
```

### 6.6 `truesize` -- The Real Memory Cost

The `truesize` field of an sk_buff represents the total memory consumed by
the sk_buff, including the structure itself and the data buffer. It is the
value charged to socket memory accounting:

```c
/* Set during allocation: */
skb->truesize = SKB_TRUESIZE(size);

/* SKB_TRUESIZE macro: */
#define SKB_TRUESIZE(X) ((X) +                          \
                          SKB_DATA_ALIGN(sizeof(struct sk_buff)) + \
                          SKB_DATA_ALIGN(sizeof(struct skb_shared_info)))
```

For a 1500-byte Ethernet frame:

```
    truesize = 1500 (data)
             + 256  (sk_buff struct, aligned)
             + 320  (skb_shared_info, aligned)
             = 2076 bytes  (approximately)
```

This means that a socket holding 100 queued packets of 1500 bytes consumes
roughly 200 KB of `sk_rmem_alloc`, not just 150 KB of raw packet data. This
overhead is significant for memory accounting accuracy.

---

## 7. Recycling and Bulk Operations

Modern high-performance networking requires minimizing allocation overhead.
The kernel provides several recycling and bulk operation mechanisms.

### 7.1 Page Pool Recycling

The page pool API (`page_pool`) provides efficient page allocation and
recycling for network drivers. Instead of returning pages to the page
allocator after each packet, the page pool maintains a cache of recycled pages:

```c
/* include/net/page_pool.h */
struct page_pool_params {
    unsigned int    flags;         /* PP_FLAG_* options               */
    unsigned int    order;         /* page order (0 = 4KB)            */
    unsigned int    pool_size;     /* number of pages in the pool     */
    int             nid;           /* NUMA node                       */
    struct device  *dev;           /* for DMA mapping                 */
    enum dma_data_direction dma_dir;
    unsigned int    max_len;       /* max data length per page        */
    unsigned int    offset;        /* headroom offset                 */
};

struct page_pool {
    struct pp_alloc_cache alloc;   /* per-CPU fast alloc cache        */
    /* ... */
    struct ptr_ring ring;          /* lock-free return ring           */
    /* ... */
};
```

The page pool operates as a circular buffer:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                    Page Pool Lifecycle                      │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌──────────┐     Driver RX    ┌──────────────┐            │
    │  │          │ ───────────────► │  sk_buff +    │            │
    │  │  Page    │    page_pool     │  page (DMA    │            │
    │  │  Pool    │    _alloc()      │  mapped)      │            │
    │  │          │                  └──────┬───────┘            │
    │  │  ┌────┐  │                         │                    │
    │  │  │page│  │                         │ Network stack      │
    │  │  │page│  │                         │ processes packet   │
    │  │  │page│  │                         │                    │
    │  │  │... │  │                         ▼                    │
    │  │  └────┘  │                  ┌──────────────┐            │
    │  │          │ ◄─────────────── │  consume_skb │            │
    │  │          │    page_pool     │  page_pool   │            │
    │  │          │    _put_page()   │  _put_page() │            │
    │  └──────────┘    (recycle)     └──────────────┘            │
    │                                                             │
    │  Fast path: page returned to pool's alloc.cache (per-CPU)  │
    │  Slow path: page returned to pool's ring (ptr_ring)        │
    │  Slowest:   page returned to page allocator                │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

Driver usage example:

```c
/* Driver initialization */
struct page_pool_params pp_params = {
    .flags      = PP_FLAG_DMA_MAP | PP_FLAG_DMA_SYNC_DEV,
    .order      = 0,                /* 4KB pages                  */
    .pool_size  = 256,              /* 256 pages in the pool      */
    .nid        = dev_to_node(&pdev->dev),
    .dev        = &pdev->dev,
    .dma_dir    = DMA_FROM_DEVICE,
    .offset     = NET_SKB_PAD + NET_IP_ALIGN,
    .max_len    = ETH_FRAME_LEN,
};

ring->page_pool = page_pool_create(&pp_params);

/* Driver receive path */
struct page *page = page_pool_dev_alloc_pages(ring->page_pool);
if (!page)
    return -ENOMEM;

/* ... DMA completion, build sk_buff ... */
skb = build_skb(page_address(page), PAGE_SIZE);
skb_mark_for_recycle(skb);   /* mark for page pool recycling */
```

### 7.2 `napi_consume_skb()` -- Bulk Free in NAPI Context

`napi_consume_skb()` batches sk_buff frees for efficiency. Instead of returning
each sk_buff structure to the SLAB allocator individually, it caches them in a
per-CPU NAPI cache and flushes them in bulk:

```c
/* net/core/skbuff.c */
void napi_consume_skb(struct sk_buff *skb, int budget)
{
    /* Non-NAPI context (budget <= 0): normal free path */
    if (unlikely(!budget)) {
        dev_consume_skb_any(skb);
        return;
    }

    lockdep_assert_in_softirq();

    if (!skb_unref(skb))
        return;

    /* Release everything except the sk_buff struct itself */
    skb_release_all(skb);

    /* Cache the sk_buff struct for reuse instead of freeing it */
    napi_skb_cache_put(skb);
}

static void napi_skb_cache_put(struct sk_buff *skb)
{
    struct napi_alloc_cache *nc = this_cpu_ptr(&napi_alloc_cache);

    /* Only cache non-fclone, non-special sk_buffs */
    if (!skb->fclone) {
        nc->skb_cache[nc->skb_count++] = skb;

        /* Flush the cache when it is full */
        if (unlikely(nc->skb_count == NAPI_SKB_CACHE_SIZE)) {
            /* Bulk-free half the cache back to SLAB */
            kmem_cache_free_bulk(skbuff_head_cache,
                                 NAPI_SKB_CACHE_BULK,
                                 nc->skb_cache);
            nc->skb_count -= NAPI_SKB_CACHE_BULK;

            /* Shift remaining entries to the front */
            memmove(nc->skb_cache,
                    nc->skb_cache + NAPI_SKB_CACHE_BULK,
                    nc->skb_count * sizeof(void *));
        }
    } else {
        /* fclone sk_buffs cannot be cached — free normally */
        kfree_skbmem(skb);
    }
}
```

Performance impact: bulk free via `kmem_cache_free_bulk()` amortizes the SLAB
allocator overhead across multiple objects, reducing per-object cost from
~20 ns to ~5 ns.

### 7.3 `kfree_skb_list()` -- Free a List of sk_buffs

When multiple sk_buffs are chained via the `next` pointer (e.g., a GSO
segment list or a frag_list), `kfree_skb_list()` frees the entire chain:

```c
/* net/core/skbuff.c */
void kfree_skb_list_reason(struct sk_buff *segs,
                            enum skb_drop_reason reason)
{
    while (segs) {
        struct sk_buff *next = segs->next;
        kfree_skb_reason(segs, reason);
        segs = next;
    }
}
EXPORT_SYMBOL(kfree_skb_list_reason);
```

Optimized variant for NAPI context:

```c
void napi_free_frags(struct napi_struct *napi)
{
    struct sk_buff *skb = napi->skb;
    if (skb) {
        napi->skb = NULL;
        kfree_skb(skb);
    }
}
```

### 7.4 Recycling for XDP and AF_XDP

XDP (eXpress Data Path) bypasses the standard `sk_buff` allocation path
entirely for maximum performance. However, when XDP_PASS is returned (routing
the packet to the normal stack), an sk_buff must be created:

```c
/* XDP to sk_buff conversion */
struct sk_buff *xdp_build_skb_from_frame(struct xdp_frame *xdpf,
                                          struct net_device *dev)
{
    struct skb_shared_info *sinfo = xdp_get_shared_info_from_frame(xdpf);
    unsigned int headroom, frame_size;
    struct sk_buff *skb;
    void *hard_start;

    headroom = xdpf->headroom;
    frame_size = headroom + xdpf->len + xdpf->metasize;

    skb = build_skb_around(skb_cache, xdpf->data - headroom, frame_size);
    if (unlikely(!skb))
        return NULL;

    skb_reserve(skb, headroom - xdpf->metasize);
    __skb_put(skb, xdpf->len + xdpf->metasize);

    if (xdpf->metasize)
        skb_metadata_set(skb, xdpf->metasize);

    skb->dev = dev;
    skb_mark_for_recycle(skb);    /* enable page pool recycling */

    return skb;
}
```

AF_XDP uses a shared UMEM (user-space memory) region. Frames are returned to
the UMEM fill ring rather than freed:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                  AF_XDP Frame Lifecycle                     │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  User Space                          Kernel                 │
    │  ┌──────────┐                        ┌──────────┐           │
    │  │ Fill Ring │ ──── descriptors ────► │ RX Ring  │           │
    │  │ (produce) │                        │ (NIC DMA │           │
    │  └──────────┘                        │  target) │           │
    │                                      └────┬─────┘           │
    │                                           │                 │
    │                                      NIC receives           │
    │                                      packet into            │
    │                                      UMEM frame             │
    │                                           │                 │
    │  ┌──────────┐                        ┌────▼─────┐           │
    │  │ RX Ring  │ ◄──── completion ───── │ XDP prog │           │
    │  │ (consume)│                        │ XDP_PASS │           │
    │  └──────────┘                        └──────────┘           │
    │       │                                                     │
    │  App reads frame                                            │
    │  from UMEM                                                  │
    │       │                                                     │
    │  Returns descriptor                                         │
    │  to Fill Ring                                               │
    │  (recycling)                                                │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

### 7.5 Performance Impact of Allocation Strategies

Measured allocation costs on a modern x86-64 system (Intel Xeon, 2.5 GHz):

```
    ┌─────────────────────────────────────────────────────────────┐
    │          Allocation Strategy Performance Comparison         │
    ├─────────────────────────────────┬───────────────────────────┤
    │ Strategy                        │ Cost per packet (approx.) │
    ├─────────────────────────────────┼───────────────────────────┤
    │ alloc_skb + kfree_skb           │ 150-250 ns                │
    │ (standard path)                 │                           │
    ├─────────────────────────────────┼───────────────────────────┤
    │ napi_alloc_skb + napi_consume   │ 50-100 ns                 │
    │ (NAPI cached path)              │                           │
    ├─────────────────────────────────┼───────────────────────────┤
    │ build_skb + page pool           │ 30-60 ns                  │
    │ (page pool recycling)           │                           │
    ├─────────────────────────────────┼───────────────────────────┤
    │ XDP (no sk_buff)                │ 5-15 ns                   │
    │ (frame-based, zero-copy)        │                           │
    ├─────────────────────────────────┼───────────────────────────┤
    │ AF_XDP (user-space)             │ 2-10 ns                   │
    │ (UMEM, zero-copy)               │                           │
    └─────────────────────────────────┴───────────────────────────┘
```

The cost difference between the standard path and XDP/AF_XDP represents
more than an order of magnitude improvement, which is why high-performance
networking applications increasingly bypass the `sk_buff` layer entirely.

---

## 8. GFP Flags and Context

The choice of GFP (Get Free Pages) flags for `sk_buff` allocation is critical
and depends entirely on the execution context. Using the wrong flags leads to
either kernel crashes (sleeping in atomic context) or unnecessary allocation
failures (using `GFP_ATOMIC` when sleeping is acceptable).

### 8.1 `GFP_KERNEL` -- Process Context Allocation

```c
/*
 * GFP_KERNEL = __GFP_RECLAIM | __GFP_IO | __GFP_FS
 *
 * Can sleep, can trigger direct reclaim, can invoke the OOM killer.
 * This is the most permissive allocation mode.
 */

/* Example: TCP send path (process context, can sleep) */
struct sk_buff *skb = alloc_skb(size, GFP_KERNEL);
if (!skb) {
    /* True allocation failure — system is critically low on memory */
    return -ENOMEM;
}
```

When to use `GFP_KERNEL`:

- System call handlers (sendmsg, recvmsg, connect, bind, etc.)
- Socket option processing (setsockopt)
- Kernel threads
- Workqueue handlers
- Any context where `might_sleep()` would not trigger a warning

### 8.2 `GFP_ATOMIC` -- Interrupt and Atomic Context

```c
/*
 * GFP_ATOMIC = __GFP_HIGH | __GFP_KSWAPD_RECLAIM
 *
 * Cannot sleep, cannot trigger direct reclaim.
 * Uses emergency memory reserves if necessary.
 */

/* Example: packet receive in softirq (NAPI poll) */
struct sk_buff *skb = alloc_skb(size, GFP_ATOMIC);
if (!skb) {
    /* Allocation failed — drop the packet */
    dev->stats.rx_dropped++;
    return;
}
```

When to use `GFP_ATOMIC`:

- Hardware interrupt handlers (hardirq)
- Software interrupt handlers (softirq / tasklet)
- While holding a spinlock
- While holding a read/write lock
- Timer callbacks
- Any context where `in_atomic()` or `in_interrupt()` returns true

### 8.3 `GFP_DMA` -- DMA-Accessible Memory

```c
/*
 * GFP_DMA = __GFP_DMA
 *
 * Allocate from the DMA zone (first 16 MB on x86).
 * Required for legacy ISA devices that cannot address
 * memory above 16 MB.
 *
 * Modern PCI/PCIe devices do NOT need this — use GFP_KERNEL
 * or GFP_ATOMIC with proper DMA mapping instead.
 */

/* Legacy ISA network card (extremely rare today) */
struct sk_buff *skb = alloc_skb(size, GFP_ATOMIC | GFP_DMA);
```

Note: `GFP_DMA` is almost never needed in modern drivers. PCI/PCIe devices
use the DMA mapping API (`dma_map_single()`, `dma_map_page()`) which handles
address translation via IOMMU/SWIOTLB, and do not require memory from the
DMA zone.

### 8.4 Context Decision Matrix

```
    ┌────────────────────────────────────────────────────────────────┐
    │              GFP Flag Selection by Context                    │
    ├────────────────────────────────────────────────────────────────┤
    │                                                                │
    │  Where am I?                       Which GFP flag?             │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │                                                         │   │
    │  │  System call / process context                          │   │
    │  │  (no locks held that disable preemption)                │   │
    │  │       ──► GFP_KERNEL                                    │   │
    │  │                                                         │   │
    │  │  Process context, holding a mutex                       │   │
    │  │       ──► GFP_KERNEL (mutexes allow sleeping)           │   │
    │  │                                                         │   │
    │  │  Process context, holding a spinlock                    │   │
    │  │       ──► GFP_ATOMIC                                    │   │
    │  │                                                         │   │
    │  │  softirq / NAPI poll                                    │   │
    │  │       ──► GFP_ATOMIC                                    │   │
    │  │       (or use napi_alloc_skb which handles this)        │   │
    │  │                                                         │   │
    │  │  Hard IRQ handler                                       │   │
    │  │       ──► GFP_ATOMIC                                    │   │
    │  │                                                         │   │
    │  │  Timer / tasklet                                        │   │
    │  │       ──► GFP_ATOMIC                                    │   │
    │  │                                                         │   │
    │  │  Workqueue                                              │   │
    │  │       ──► GFP_KERNEL (workqueues run in process ctx)    │   │
    │  │                                                         │   │
    │  │  Socket allocation (sk->sk_allocation)                  │   │
    │  │       ──► Use sk->sk_allocation                         │   │
    │  │           (GFP_KERNEL for TCP, GFP_ATOMIC for some      │   │
    │  │            protocols in special states)                  │   │
    │  │                                                         │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                                                                │
    └────────────────────────────────────────────────────────────────┘
```

### 8.5 Advanced GFP Modifiers

Several modifier flags fine-tune allocation behavior:

```c
/* __GFP_NOWARN — suppress allocation failure warnings */
skb = alloc_skb(size, GFP_ATOMIC | __GFP_NOWARN);
/* Use when failure is expected and handled gracefully */

/* __GFP_ZERO — zero-fill the allocated memory */
/* Not commonly used for sk_buffs (wastes cycles) */

/* __GFP_NOMEMALLOC — do not use emergency reserves */
/* Used internally by kmalloc_reserve() to prevent
   non-critical allocations from depleting reserves */

/* __GFP_MEMALLOC — access ALL memory reserves */
/* Used when the allocation is required to free memory
   (e.g., swapping over network — NBD/iSCSI) */
skb->pfmemalloc = 1;   /* set when allocated with __GFP_MEMALLOC */

/* sk->sk_allocation — per-socket GFP flags */
struct sock {
    gfp_t sk_allocation;   /* GFP_KERNEL by default */
    /* Set to GFP_ATOMIC in certain protocol states */
};
```

### 8.6 Allocation Failure Handling

Proper handling of allocation failures is essential for kernel stability.
The strategy depends on the context:

```c
/* Pattern 1: Drop the packet (receive path) */
static int my_driver_rx(struct my_ring *ring)
{
    struct sk_buff *skb = napi_alloc_skb(&ring->napi, pkt_len);
    if (unlikely(!skb)) {
        ring->rx_stats.alloc_failures++;
        ring->netdev->stats.rx_dropped++;
        /* Recycle the DMA buffer for future use */
        my_driver_recycle_buffer(ring, buf);
        return 0;   /* continue polling — don't crash */
    }
    /* ... process packet ... */
}

/* Pattern 2: Return error to user space (send path) */
static int my_proto_sendmsg(struct sock *sk, struct msghdr *msg, size_t len)
{
    struct sk_buff *skb = alloc_skb(len + headroom, sk->sk_allocation);
    if (!skb)
        return -ENOBUFS;    /* propagate to sendmsg() caller */
    /* ... */
}

/* Pattern 3: Wait for memory (TCP send path) */
static int tcp_sendmsg_locked(struct sock *sk, ...)
{
    /* ... */
    skb = sk_stream_alloc_skb(sk, size, sk->sk_allocation, first);
    if (!skb) {
        /* Wait with timeout for memory to become available */
        set_bit(SOCK_NOSPACE, &sk->sk_socket->flags);
        err = sk_stream_wait_memory(sk, &timeo);
        if (err)
            goto out_err;
        /* Retry allocation after waiting */
        continue;
    }
    /* ... */
}

/* Pattern 4: Use pre-allocated reserve (critical path) */
static struct sk_buff *my_critical_alloc(struct sock *sk)
{
    struct sk_buff *skb;

    /* Try normal allocation first */
    skb = alloc_skb(size, GFP_ATOMIC | __GFP_NOWARN);
    if (skb)
        return skb;

    /* Fall back to pre-allocated emergency buffer */
    skb = my_get_emergency_skb(sk);
    if (skb)
        return skb;

    /* Last resort: fail */
    return NULL;
}
```

### 8.7 `pfmemalloc` -- Emergency Reserve Access

When the system is under extreme memory pressure, the networking stack may
need to process packets to free memory (e.g., receiving swap pages over NFS
or iSCSI). The `pfmemalloc` mechanism allows critical sk_buffs to be allocated
from the emergency memory reserves:

```c
/* In __alloc_skb(): */
data = kmalloc_reserve(size, gfp_mask, node, &pfmemalloc);
skb->pfmemalloc = pfmemalloc;

/* In the receive path: */
static int __netif_receive_skb_core(struct sk_buff **pskb, ...)
{
    struct sk_buff *skb = *pskb;

    if (skb->pfmemalloc) {
        /*
         * This sk_buff was allocated from emergency reserves.
         * Only deliver to sockets that are marked as SOCK_MEMALLOC
         * (i.e., sockets that are being used for memory reclaim,
         * such as swap-over-NFS).
         */
        if (!sock_flag(sk, SOCK_MEMALLOC)) {
            kfree_skb(skb);   /* drop — not allowed to use reserves */
            return NET_RX_DROP;
        }
    }
    /* ... normal processing ... */
}
```

The pfmemalloc flow:

```
    ┌─────────────────────────────────────────────────────────────┐
    │               pfmemalloc Decision Flow                     │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  System memory low ──► NIC receives packet                  │
    │       │                                                     │
    │       ▼                                                     │
    │  napi_alloc_skb(GFP_ATOMIC)                                 │
    │       │                                                     │
    │       ├── Normal free pages available?                       │
    │       │     YES ──► allocate normally, pfmemalloc=0          │
    │       │     NO  ──► tap emergency reserves, pfmemalloc=1    │
    │       │                                                     │
    │       ▼                                                     │
    │  __netif_receive_skb()                                      │
    │       │                                                     │
    │       ├── skb->pfmemalloc?                                  │
    │       │     NO  ──► deliver to all matching sockets          │
    │       │     YES ──► only deliver to SOCK_MEMALLOC sockets   │
    │       │             (NFS/iSCSI/NBD swap targets)            │
    │       │             all others: kfree_skb (drop)            │
    │       │                                                     │
    │       ▼                                                     │
    │  Swap-over-NFS socket processes the data                    │
    │       ──► frees swap pages ──► system recovers memory       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

---

## 9. Complete Lifecycle Example

To illustrate the full lifecycle, consider a TCP packet being sent from
user space to the wire and back:

```
    ┌──────────────────────────────────────────────────────────────────┐
    │              Complete sk_buff Lifecycle: TCP Send                │
    ├──────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  1. User calls send(fd, buf, len, 0)                             │
    │     ┌──────────────────────────────────────────────────────────┐  │
    │     │ tcp_sendmsg()                                            │  │
    │     │   skb = alloc_skb(size, GFP_KERNEL | SKB_ALLOC_FCLONE)  │  │
    │     │   skb_set_owner_w(skb, sk)                               │  │
    │     │     ──► sk_wmem_alloc += truesize                        │  │
    │     │     ──► skb->destructor = sock_wfree                     │  │
    │     │   skb_copy_from_iter(skb, ...)  /* copy user data */     │  │
    │     │   tcp_push(sk, ...)             /* enqueue for sending */ │  │
    │     └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  2. TCP segments and clones for retransmit                       │
    │     ┌──────────────────────────────────────────────────────────┐  │
    │     │ tcp_transmit_skb()                                       │  │
    │     │   clone = skb_clone(skb)  /* fclone fast path! */        │  │
    │     │     ──► fclone_ref = 2                                   │  │
    │     │     ──► dataref = 2                                      │  │
    │     │   Original stays in sk->sk_write_queue (retransmit)      │  │
    │     │   Clone descends through the stack                       │  │
    │     └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  3. IP layer adds headers                                        │
    │     ┌──────────────────────────────────────────────────────────┐  │
    │     │ ip_queue_xmit(clone)                                     │  │
    │     │   skb_push(clone, sizeof(struct iphdr))                  │  │
    │     │   /* data pointer moves back — headroom consumed */      │  │
    │     └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  4. Device driver transmits                                      │
    │     ┌──────────────────────────────────────────────────────────┐  │
    │     │ dev_hard_start_xmit(clone)                               │  │
    │     │   ndo_start_xmit(clone)   /* DMA map + ring enqueue */   │  │
    │     └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  5. TX completion interrupt                                      │
    │     ┌──────────────────────────────────────────────────────────┐  │
    │     │ my_driver_tx_complete()                                   │  │
    │     │   dev_consume_skb_any(clone)                              │  │
    │     │     ──► clone users: 1 → 0                                │  │
    │     │     ──► clone freed                                       │  │
    │     │     ──► dataref: 2 → 1                                    │  │
    │     │     ──► fclone_ref: 2 → 1                                 │  │
    │     │     ──► data buffer NOT freed (original still refs it)    │  │
    │     │     ──► fclone slab NOT freed (original still refs it)    │  │
    │     └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  6. ACK received — original freed                                │
    │     ┌──────────────────────────────────────────────────────────┐  │
    │     │ tcp_clean_rtx_queue()                                    │  │
    │     │   tcp_rtx_queue_unlink_and_free(skb)                     │  │
    │     │     ──► kfree_skb(skb)                                   │  │
    │     │     ──► skb->destructor (sock_wfree)                     │  │
    │     │         ──► sk_wmem_alloc -= truesize                    │  │
    │     │         ──► sk->sk_write_space(sk)  /* wake writers */   │  │
    │     │     ──► dataref: 1 → 0, free data buffer                 │  │
    │     │     ──► fclone_ref: 1 → 0, free fclone slab object      │  │
    │     └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

## 10. Debugging and Tracing

### 10.1 Tracepoints

The kernel provides several tracepoints for monitoring sk_buff lifecycle events:

```
    ┌────────────────────────────────────────────────────────────┐
    │                  sk_buff Tracepoints                       │
    ├────────────────────────────┬───────────────────────────────┤
    │ Tracepoint                 │ When Fired                    │
    ├────────────────────────────┼───────────────────────────────┤
    │ skb:kfree_skb              │ Packet dropped (kfree_skb)    │
    │ skb:consume_skb            │ Packet consumed (consume_skb) │
    │ skb:skb_copy_datagram_     │ Data copied to user space     │
    │   iovec                    │                               │
    │ net:netif_receive_skb      │ Packet received by stack      │
    │ net:net_dev_xmit           │ Packet transmitted by driver  │
    │ net:net_dev_queue          │ Packet enqueued to qdisc      │
    └────────────────────────────┴───────────────────────────────┘
```

Using `perf` to trace sk_buff drops:

```bash
# Trace all kfree_skb events with stack traces
perf trace -e skb:kfree_skb --call-graph dwarf

# Count drops by location
perf stat -e skb:kfree_skb -a sleep 10

# Use dropwatch for aggregated drop monitoring
dropwatch -l kas
```

### 10.2 `/proc/slabinfo` -- Monitoring SLAB Caches

```bash
# View sk_buff cache statistics
cat /proc/slabinfo | grep skbuff
# skbuff_head_cache   12456  12544    256   16    1 : tunables ...
# skbuff_fclone_cache  1024   1056    512    8    1 : tunables ...
```

Fields:

```
    ┌──────────┬───────┬────────┬────────────────────────────────────┐
    │ Cache    │ Active│ Total  │ Interpretation                     │
    │ Name     │ Objs  │ Objs   │                                    │
    ├──────────┼───────┼────────┼────────────────────────────────────┤
    │ head     │ 12456 │ 12544  │ 12456 sk_buffs in use              │
    │ cache    │       │        │ 88 free in partial slabs            │
    ├──────────┼───────┼────────┼────────────────────────────────────┤
    │ fclone   │ 1024  │ 1056   │ 1024 fclone pairs in use           │
    │ cache    │       │        │ 32 free in partial slabs            │
    └──────────┴───────┴────────┴────────────────────────────────────┘
```

### 10.3 Common Lifecycle Bugs

**Bug 1: Use-after-free**

```c
/* WRONG: using skb after kfree_skb */
kfree_skb(skb);
printk("packet len was %d\n", skb->len);  /* BUG: use-after-free */

/* CORRECT: save needed values before freeing */
unsigned int len = skb->len;
kfree_skb(skb);
printk("packet len was %d\n", len);
```

**Bug 2: Double free**

```c
/* WRONG: freeing twice without skb_get */
kfree_skb(skb);
/* ... later ... */
kfree_skb(skb);   /* BUG: double free */

/* CORRECT: use reference counting */
skb_get(skb);      /* users = 2 */
kfree_skb(skb);    /* users = 1 */
/* ... later ... */
kfree_skb(skb);    /* users = 0, freed */
```

**Bug 3: Wrong GFP flags**

```c
/* WRONG: sleeping allocation in IRQ context */
irqreturn_t my_handler(int irq, void *dev_id) {
    struct sk_buff *skb = alloc_skb(1500, GFP_KERNEL);  /* BUG: can sleep */
    /* ... */
}

/* CORRECT: use GFP_ATOMIC in IRQ context */
irqreturn_t my_handler(int irq, void *dev_id) {
    struct sk_buff *skb = alloc_skb(1500, GFP_ATOMIC);
    if (!skb)
        return IRQ_HANDLED;   /* handle failure gracefully */
    /* ... */
}
```

**Bug 4: Memory leak (missing destructor call)**

```c
/* WRONG: replacing destructor without calling the old one */
skb->destructor = my_destructor;
/* The original sock_wfree will never be called
   ──► sk_wmem_alloc leaks ──► socket memory exhaustion */

/* CORRECT: use skb_orphan() first */
skb_orphan(skb);                 /* calls old destructor, clears sk */
skb->destructor = my_destructor; /* now safe to set new one */
```

**Bug 5: Writing to shared data buffer**

```c
/* WRONG: modifying data of a cloned sk_buff */
clone = skb_clone(skb, GFP_ATOMIC);
memcpy(skb_put(clone, 10), "extra data", 10);  /* BUG: shared buffer */

/* CORRECT: unclone before modifying */
if (skb_cloned(clone)) {
    if (pskb_expand_head(clone, 0, 10, GFP_ATOMIC)) {
        kfree_skb(clone);
        return -ENOMEM;
    }
}
memcpy(skb_put(clone, 10), "extra data", 10);  /* safe: exclusive buffer */
```

---

## 11. Summary: Quick Reference

### Allocation Functions

| Function | Context | Data Source | Headroom | Use Case |
|---|---|---|---|---|
| `alloc_skb()` | Any | kmalloc | None | Protocol layer |
| `__alloc_skb()` | Any | kmalloc | None | Internal / custom flags |
| `dev_alloc_skb()` | IRQ | kmalloc | PAD | Legacy drivers |
| `netdev_alloc_skb()` | IRQ | page frag | PAD | Modern drivers |
| `netdev_alloc_skb_ip_align()` | IRQ | page frag | PAD+2 | Drivers (aligned) |
| `napi_alloc_skb()` | NAPI | NAPI cache | PAD+2 | NAPI polling |
| `build_skb()` | Any | External | None | Page pool drivers |

### Free Functions

| Function | Tracepoint | Context | Use Case |
|---|---|---|---|
| `kfree_skb()` | kfree_skb | Any | Dropped packets |
| `consume_skb()` | consume_skb | Any | Consumed packets |
| `dev_kfree_skb()` | consume_skb | Process | Driver TX done |
| `dev_kfree_skb_irq()` | consume_skb | IRQ | Driver TX IRQ |
| `dev_kfree_skb_any()` | consume_skb | Any | Driver (unknown ctx) |
| `napi_consume_skb()` | consume_skb | NAPI | Bulk NAPI free |
| `kfree_skb_list()` | kfree_skb | Any | Free chain |
| `__kfree_skb()` | None | Internal | Unconditional free |

### Reference Count Operations

| Function | Affects | Operation |
|---|---|---|
| `skb_get(skb)` | users | Increment |
| `kfree_skb(skb)` | users | Decrement (free if 0) |
| `skb_clone(skb)` | dataref, users (new) | Increment dataref, new users=1 |
| `skb_shared(skb)` | users | Check if > 1 |
| `skb_cloned(skb)` | dataref | Check if > 1 |
| `skb_unclone(skb)` | dataref | Copy data if shared |

---

*This chapter is part of an in-depth treatment of the Linux kernel networking
data structures. The next chapter covers sk_buff data manipulation operations:
`skb_put()`, `skb_push()`, `skb_pull()`, `skb_reserve()`, and the non-linear
data model (paged fragments, frag_list, and scatter-gather I/O).*
